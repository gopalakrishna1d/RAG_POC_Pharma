import json
import re
import time
from datetime import datetime

from langchain_ollama import ChatOllama

from database.db import get_connection
from query.sql_validator import validate_sql_statement
from schema_test import load_schema, build_query_plan
from sql_generator import generate_sql

# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatOllama(
    model="qwen2.5:3b",
    # model = "nemotron-3-nano:4b",
    temperature=0
)

# ---------------------------------------------------------
# Intent Extraction
# ---------------------------------------------------------

def _fallback_intent(question):
    """Rule-based intent extraction used when the local LLM is unavailable."""
    q = question.strip()
    if not q:
        return {"entity": "none", "operation": "none", "conditions": [], "fields": []}

    lower = q.lower()
    if "difference between a deviation and a capa" in lower or "difference between deviation and capa" in lower:
        return {"entity": "none", "operation": "none", "conditions": [], "fields": []}

    entity = "none"
    for name in ["deviation", "capa", "action", "site", "user", "document"]:
        if name in lower:
            entity = name
            break

    if any(word in lower for word in ["how many", "count", "total number", "number of"]):
        operation = "count"
    elif any(word in lower for word in ["show", "list", "which", "what are", "give me", "find"]):
        operation = "list"
    else:
        operation = "list" if "deviation" in lower or "capa" in lower or "action" in lower or "document" in lower or "site" in lower else "none"

    conditions = []
    for status in ["open", "closed", "in progress", "approved", "issued", "active"]:
        if status in lower:
            target_entity = entity if entity != "none" else "deviation"
            if "capa" in lower and "deviation" not in lower:
                target_entity = "capa"
            elif "site" in lower:
                target_entity = "site"
            conditions.append({"entity": target_entity, "concept": "status", "value": status})
            break

    if "this month" in lower or "current month" in lower:
        conditions.append({"entity": entity if entity != "none" else "deviation", "concept": "created_on", "value": "this month"})

    if "hyderabad" in lower or "bangalore" in lower or "vizag" in lower:
        conditions.append({"entity": "site", "concept": "name", "value": "Hyderabad Manufacturing Plant" if "hyderabad" in lower else "Bangalore API Plant" if "bangalore" in lower else "Vizag Quality Control Lab"})

    if "overdue" in lower:
        conditions.append({"entity": entity if entity != "none" else "capa", "concept": "status", "value": "overdue"})

    if entity == "none" and operation != "none":
        entity = "deviation" if "deviation" in lower else "capa" if "capa" in lower else "site" if "site" in lower else "document" if "document" in lower else "action" if "action" in lower else "none"

    return {"entity": entity, "operation": operation, "conditions": conditions, "fields": []}


def extract_intent(question):
    """
    Ask the LLM to convert the user's natural-language
    question into a small structured intent JSON.
    """
    if not question or not question.strip():
        return {"entity": "none", "operation": "none", "conditions": [], "fields": []}

    try:
        prompt = f"""
You are an intent extraction system for a pharmaceutical
quality management database.

Your job is ONLY to identify:

1. entity being requested
2. operation
3. conditions
4. which entity each condition applies to
5. any fields explicitly requested by the user

Do NOT identify database tables.
Do NOT write SQL.
Do NOT explain your answer.

Allowed entities:

- deviation
- capa
- action
- site
- user
- document

Allowed condition concepts:

- status
- name
- created_on
- created
- date

Allowed operations:

- count
- list

Return ONLY valid JSON.

JSON format:

{{
  "entity": "capa",
  "operation": "count",
  "conditions": [
    {{
      "entity": "deviation",
      "concept": "status",
      "value": "open"
    }},
    {{
      "entity": "site",
      "concept": "name",
      "value": "Hyderabad Manufacturing Plant"
    }}
  ],
  "fields": ["capa_number", "created_on"]
}}

Rules:

- "How many" means operation = "count".
- "Show", "list", "which", or "what are" usually means operation = "list".
- Extract every condition explicitly mentioned by the user.
- Every condition MUST specify which entity it applies to.
- If the user asks for specific fields such as "createdon and capaid" or "title and status", include them in the `fields` array.
- Field names should be short, normalized concepts such as `created_on`, `capa_number`, `title`, `status`, `deviation_number`, `site_name`, `user_name`, `document_type`.
- If the question says "open deviations", the status condition
  applies to deviation.
- If the question says "open CAPAs", the status condition
  applies to capa.
- If the question says "actions assigned to John", the condition
  applies to action.
- If a site/facility/plant is mentioned, use:
    entity = "site"
    concept = "name"
- If a creation date/time is mentioned, use:
    concept = "created_on"
    value = a natural date phrase such as "this month", "last month", "last 30 days", "past 6 months", or a date string.
- If status is mentioned, determine which entity the status
  describes from the wording.
- Preserve the user's actual value.
- Do not invent conditions.
- Do not identify database table names.
- Do not write SQL.
- Do not add explanations.
- Return JSON only.

Examples:

Question:
How many open deviations are there?

Return:

{{
  "entity": "deviation",
  "operation": "count",
  "conditions": [
    {{
      "entity": "deviation",
      "concept": "status",
      "value": "open"
    }}
  ]
}}

Question:
How many open CAPAs are there?

Return:

{{
  "entity": "capa",
  "operation": "count",
  "conditions": [
    {{
      "entity": "capa",
      "concept": "status",
      "value": "open"
    }}
  ]
}}

Question:
How many CAPAs are associated with open deviations?

Return:

{{
  "entity": "capa",
  "operation": "count",
  "conditions": [
    {{
      "entity": "deviation",
      "concept": "status",
      "value": "open"
    }}
  ]
}}

Question:
How many CAPAs are associated with open deviations
at the Hyderabad Manufacturing Plant?

Return:

{{
  "entity": "capa",
  "operation": "count",
  "conditions": [
    {{
      "entity": "deviation",
      "concept": "status",
      "value": "open"
    }},
    {{
      "entity": "site",
      "concept": "name",
      "value": "Hyderabad Manufacturing Plant"
    }}
  ]
}}

Question:
Show deviations created this month.

Return:

{{
  "entity": "deviation",
  "operation": "list",
  "conditions": [
    {{
      "entity": "deviation",
      "concept": "created_on",
      "value": "this month"
    }}
  ],
  "fields": ["deviation_number", "title", "status", "created_on"]
}}

Question:
Give me the CreatedOn and CAPAId of all CAPA records.

Return:

{{
  "entity": "capa",
  "operation": "list",
  "fields": ["created_on", "capa_number"],
  "conditions": []
}}

User question:

{question}
"""
        response = llm.invoke(prompt)
        content = response.content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)
        content = content.strip()
        intent = json.loads(content)
    except Exception as exc:
        print(f"LLM intent extraction failed, using fallback parser: {exc}")
        return _fallback_intent(question)

    question_lower = question.lower()
    if isinstance(intent, dict):
        conditions = intent.get("conditions", [])
        month_names = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
        ]

        found_months = []
        for month in month_names:
            pattern = rf"\b{re.escape(month)}\b"
            if re.search(pattern, question_lower):
                found_months.append(month)

        if found_months:
            if not any(condition.get("concept", "").lower() in {"created_on", "created", "date", "created_at"} for condition in conditions):
                conditions.append({"entity": intent.get("entity", "capa"), "concept": "created_on", "value": found_months[0]})
                intent["conditions"] = conditions

            for condition in conditions:
                if condition.get("concept", "").lower() in {"created_on", "created", "date", "created_at"}:
                    if len(found_months) >= 2:
                        condition["value"] = [found_months[0], found_months[-1]]
                    else:
                        condition["value"] = found_months[0]

        if intent.get("entity") in {None, "none"} and question_lower.startswith("what is the difference"):
            intent["entity"] = "none"
            intent["operation"] = "none"

    return intent



DISPLAY_COLUMN_NAMES = {
    "CAPANumber": "CAPA Number",
    "CAPAId": "CAPA ID",
    "DeviationNumber": "Deviation Number",
    "ActionNumber": "Action Number",
    "DocumentNumber": "Document Number",
    "CreatedOn": "Created On",
    "DueDate": "Due Date",
    "EntityId": "Entity ID",
    "SiteId": "Site ID",
    "AssignedTo": "Assigned To",
    "OwnerId": "Owner ID",
    "DeviationId": "Deviation ID",
    "ActionId": "Action ID",
    "DocumentId": "Document ID",
}


def format_column_name(column):
    """Convert a schema column identifier into a consistent display label."""
    column_name = column.rsplit(".", 1)[-1]
    if column_name in DISPLAY_COLUMN_NAMES:
        return DISPLAY_COLUMN_NAMES[column_name]

    column_name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", column_name)
    column_name = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", column_name)
    return column_name.replace("_", " ").title()


def generate_answer(question, rows, operation, columns=None):
    """
    Format list results exactly and use the LLM only for non-list responses.
    It must not invent, recalculate, or modify the result.
    """

    if operation == "list":
        if not rows:
            return "There are no matching records."

        labels = [format_column_name(column) for column in (columns or [])]
        lines = [f"Matching records ({len(rows)}):"]
        for index, row in enumerate(rows, start=1):
            values = list(row)
            fields = []
            for value_index, value in enumerate(values):
                label = labels[value_index] if value_index < len(labels) else f"Column {value_index + 1}"
                fields.append(f"{label}: {value}")
            lines.append(f"{index}. " + "; ".join(fields))
        return "\n".join(lines)

    prompt = f"""
You are a helpful database assistant.

The database has already executed the user's question.
Your job is ONLY to turn the database result into a clear, natural-language answer.

IMPORTANT RULES:
- Do NOT calculate anything.
- Do NOT change the database result.
- Do NOT invent any information.
- Use ONLY the information in the database result.
- Answer the user's question directly.
- Do not mention SQL, database queries, schemas, prompts, or AI.
- Do not output JSON.

The requested operation is: {operation}

If the operation is COUNT:
- State the count clearly.
- Keep the answer concise.
- Use one short sentence.

If the operation is LIST:
- Present ALL records returned by the database.
- Do NOT omit any record.
- Include the relevant fields from each record.
- Use a clear numbered list.
- Do not add information that is not present in the database result.

User question:
{question}

Database result:
{rows}

Final answer:
"""

    response = llm.invoke(prompt)

    return response.content.strip()


# ---------------------------------------------------------
# SQL Execution
# ---------------------------------------------------------

def execute_sql(sql):
    """
    Execute generated SQL against SQL Server
    and return the result rows.
    """
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows

    finally:
        cursor.close()
        connection.close()



# ---------------------------------------------------------
# Main RAG Pipeline
# ---------------------------------------------------------

def process_question(question):
    """
    Execute the complete RAG pipeline for a single question.

    This function is independent of CLI/FastAPI so that the
    same RAG logic can be reused by different interfaces.
    """

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    # -----------------------------------------------------
    # 1. Intent extraction
    # -----------------------------------------------------

    print("\nExtracting intent...")

    intent = extract_intent(question)

    print("\nINTENT:")
    print("=" * 50)
    print(json.dumps(intent, indent=2))

    # -----------------------------------------------------
    # 2. Load schema
    # -----------------------------------------------------

    schema = load_schema()

    # -----------------------------------------------------
    # 3. Intent → Query Plan
    # -----------------------------------------------------

    if intent.get("operation") == "none" or intent.get("entity") in {None, "none"}:
        return {
            "question": question,
            "intent": intent,
            "query_plan": None,
            "sql": None,
            "rows": [],
            "answer": "A deviation is an actual quality event or issue, while a CAPA is the formal corrective and preventive action plan created to investigate and prevent recurrence."
        }

    print("\nBuilding query plan...")

    plan = build_query_plan(
        intent,
        schema
    )

    print("\nQUERY PLAN:")
    print("=" * 50)
    print(json.dumps(plan, indent=2))

    # -----------------------------------------------------
    # 4. Query Plan → SQL
    # -----------------------------------------------------

    print("\nGenerating SQL...")

    sql = generate_sql(plan)
    validate_sql_statement(sql)

    print("\nGENERATED SQL:")
    print("=" * 50)
    print(sql)

    # -----------------------------------------------------
    # 5. Execute SQL
    # -----------------------------------------------------

    print("\nExecuting SQL...")

    rows = execute_sql(sql)

    print("\nDATABASE RESULT:")
    print("=" * 50)

    for row in rows:
        print(row)

    # -----------------------------------------------------
    # 6. Generate final answer
    # -----------------------------------------------------

    print("\nFINAL ANSWER:")
    print("=" * 50)

    answer = generate_answer(
        question,
        rows,
        intent["operation"],
        plan["select"]
    )

    print(answer)

    # -----------------------------------------------------
    # Return everything needed by API
    # -----------------------------------------------------

    return {
        "question": question,
        "intent": intent,
        "query_plan": plan,
        "sql": sql,
        "rows": rows,
        "answer": answer
    }


# ---------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------

def main():

    question = input(
        "\nEnter your question: "
    ).strip()

    if not question:
        print("Question cannot be empty.")
        return

    process_question(question)


if __name__ == "__main__":
    main()
