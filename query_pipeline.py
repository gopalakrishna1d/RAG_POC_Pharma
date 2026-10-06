import json
import re

from langchain_ollama import ChatOllama

from database.db import get_connection
from schema_test import load_schema, build_query_plan
from sql_generator import generate_sql

# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0
)

# ---------------------------------------------------------
# Intent Extraction
# ---------------------------------------------------------

def extract_intent(question):
    """
    Ask the LLM to convert the user's natural-language
    question into a small structured intent JSON.
    """

    prompt = f"""
You are an intent extraction system for a pharmaceutical
quality management database.

Your job is ONLY to identify:

1. entity being requested
2. operation
3. conditions
4. which entity each condition applies to

Do NOT identify database tables.
Do NOT identify database columns.
Do NOT write SQL.
Do NOT explain your answer.

Allowed entities:

- deviation
- capa
- action
- site
- user
- document

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
  ]
}}

Rules:

- "How many" means operation = "count".
- "Show", "list", "which", or "what are" usually means operation = "list".
- Extract every condition explicitly mentioned by the user.
- Every condition MUST specify which entity it applies to.
- If the question says "open deviations", the status condition
  applies to deviation.
- If the question says "open CAPAs", the status condition
  applies to capa.
- If the question says "actions assigned to John", the condition
  applies to action.
- If a site/facility/plant is mentioned, use:
    entity = "site"
    concept = "name"
- If status is mentioned, determine which entity the status
  describes from the wording.
- Preserve the user's actual value.
- Do not invent conditions.
- Do not identify database table names.
- Do not identify database column names.
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

User question:

{question}
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    # -----------------------------------------------------
    # Remove Markdown code fences if the model adds them
    # -----------------------------------------------------

    content = re.sub(
        r"^```(?:json)?\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"\s*```$",
        "",
        content
    )

    content = content.strip()

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:

        intent = json.loads(content)

    except json.JSONDecodeError as error:

        print("\nLLM returned invalid JSON:")
        print(content)

        raise ValueError(
            f"Could not parse LLM intent as JSON: {error}"
        )

    return intent



def generate_answer(question, rows, operation):
    """
    Convert the database result into a natural-language answer.

    The LLM is only responsible for explaining the supplied database result.
    It must not invent, recalculate, or modify the result.
    """

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
# Main Pipeline
# ---------------------------------------------------------

def main():
    # -----------------------------------------------------
    # 1. Get user question
    # -----------------------------------------------------

    question = input(
        "\nEnter your question: "
    ).strip()

    if not question:
        print("Question cannot be empty.")
        return

    # ---------------------------------------------------------
    # 2. Intent extracted by the LLM
    # ---------------------------------------------------------

    print("\nExtracting intent...")

    intent = extract_intent(question)

    print("\nINTENT:")
    print("=" * 50)
    print(json.dumps(intent, indent=2))

    # -----------------------------------------------------
    # 3. Load schema
    # -----------------------------------------------------

    schema = load_schema()

    # -----------------------------------------------------
    # 4. Intent → Query Plan
    # -----------------------------------------------------

    print("\nBuilding query plan...")
    plan = build_query_plan(
        intent,
        schema
    )

    print("\nQUERY PLAN:")
    print("=" * 50)
    print(json.dumps(plan, indent=2))

    # -----------------------------------------------------
    # 5. Query Plan → SQL
    # -----------------------------------------------------

    print("\nGenerating SQL...")

    sql = generate_sql(plan)

    print("\nGENERATED SQL:")
    print("=" * 50)
    print(sql)

    # -----------------------------------------------------
    # 6. Execute SQL
    # -----------------------------------------------------

    print("\nExecuting SQL...")
    rows = execute_sql(sql)

    # -----------------------------------------------------
    # 7. Display result
    # -----------------------------------------------------

    print("\nDATABASE RESULT:")
    print("=" * 50)

    for row in rows:
        print(row)

    print()
    print("FINAL ANSWER:")
    print("=" * 50)

    answer = generate_answer(question, rows, intent["operation"])

    print(answer)

if __name__ == "__main__":
    main()