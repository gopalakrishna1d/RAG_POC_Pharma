import json
import re
from datetime import datetime, timedelta
from pathlib import Path

SCHEMA_PATH = Path("schema/database_schema.json")


ENTITY_MAP = {
    "deviation": "Deviations",
    "capa": "CAPA",
    "action": "Actions",
    "site": "Sites",
    "user": "Users",
    "document": "Documents"
}

FILTER_MAP = {
    ("deviation", "status"): "Deviations.Status",
    ("site", "name"): "Sites.SiteName",
    ("capa", "status"): "CAPA.Status",
    ("action", "status"): "Actions.Status",
    ("document", "status"): "Documents.Status",
    ("user", "name"): "Users.UserName",
    ("deviation", "created_on"): "Deviations.CreatedOn",
    ("deviation", "created"): "Deviations.CreatedOn",
    ("capa", "created_on"): "CAPA.CreatedOn",
    ("capa", "created"): "CAPA.CreatedOn",
    ("document", "created_on"): "Documents.CreatedOn",
    ("document", "created"): "Documents.CreatedOn"
}

LIST_COLUMNS = {
    "deviation": [
        "Deviations.DeviationNumber",
        "Deviations.Title",
        "Deviations.Status",
        "Deviations.Severity"
    ],

    "capa": [
        "CAPA.CAPANumber",
        "CAPA.Title",
        "CAPA.Status"
    ],

    "action": [
        "Actions.ActionNumber",
        "Actions.Description",
        "Actions.Status"
    ],

    "site": [
        "Sites.SiteCode",
        "Sites.SiteName",
        "Sites.Location"
    ],

    "user": [
        "Users.UserName",
        "Users.Email"
    ],

    "document": [
        "Documents.DocumentNumber",
        "Documents.Title",
        "Documents.DocumentType",
        "Documents.Status"
    ]
}

FIELD_MAP = {
    "deviation": {
        "deviation_number": "Deviations.DeviationNumber",
        "number": "Deviations.DeviationNumber",
        "title": "Deviations.Title",
        "status": "Deviations.Status",
        "severity": "Deviations.Severity",
        "created_on": "Deviations.CreatedOn",
        "created": "Deviations.CreatedOn",
        "site_id": "Deviations.SiteId",
        "assigned_to": "Deviations.AssignedTo"
    },
    "capa": {
        "capa_number": "CAPA.CAPANumber",
        "number": "CAPA.CAPANumber",
        "capaid": "CAPA.CAPANumber",
        "capa_id": "CAPA.CAPANumber",
        "title": "CAPA.Title",
        "status": "CAPA.Status",
        "created_on": "CAPA.CreatedOn",
        "created": "CAPA.CreatedOn",
        "due_date": "CAPA.DueDate",
        "owner_id": "CAPA.OwnerId",
        "deviation_id": "CAPA.DeviationId"
    },
    "action": {
        "action_number": "Actions.ActionNumber",
        "number": "Actions.ActionNumber",
        "actionid": "Actions.ActionNumber",
        "description": "Actions.Description",
        "status": "Actions.Status",
        "due_date": "Actions.DueDate",
        "assigned_to": "Actions.AssignedTo",
        "capa_id": "Actions.CAPAId"
    },
    "site": {
        "site_code": "Sites.SiteCode",
        "code": "Sites.SiteCode",
        "site_name": "Sites.SiteName",
        "name": "Sites.SiteName",
        "location": "Sites.Location",
        "is_active": "Sites.IsActive"
    },
    "user": {
        "user_name": "Users.UserName",
        "name": "Users.UserName",
        "email": "Users.Email",
        "site_id": "Users.SiteId",
        "is_active": "Users.IsActive"
    },
    "document": {
        "document_number": "Documents.DocumentNumber",
        "number": "Documents.DocumentNumber",
        "title": "Documents.Title",
        "document_type": "Documents.DocumentType",
        "status": "Documents.Status",
        "created_on": "Documents.CreatedOn",
        "created": "Documents.CreatedOn",
        "site_id": "Documents.SiteId"
    }
}

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def find_relationship_path(schema, start_table, target_table):
    """
    Find a relationship path between two tables.

    Relationships are treated as an undirected graph for traversal,
    while preserving the actual FK -> PK join condition.
    """

    if start_table == target_table:
        return []

    relationships = []

    for table_name, table_info in schema["tables"].items():

        for relationship in table_info.get("relationships", []):

            column = relationship["column"]
            reference = relationship["references"]

            referenced_table, referenced_column = reference.split(".")

            relationships.append({
                "from_table": table_name,
                "from_column": column,
                "to_table": referenced_table,
                "to_column": referenced_column
            })

    # BFS
    queue = [(start_table, [])]
    visited = {start_table}

    while queue:

        current_table, path = queue.pop(0)

        for rel in relationships:

            # Forward direction
            if rel["from_table"] == current_table:
                next_table = rel["to_table"]

                join = {
                    "left": f"{rel['from_table']}.{rel['from_column']}",
                    "right": f"{rel['to_table']}.{rel['to_column']}"
                }

                if next_table == target_table:
                    return path + [join]

                if next_table not in visited:
                    visited.add(next_table)
                    queue.append(
                        (next_table, path + [join])
                    )

            # Reverse direction
            elif rel["to_table"] == current_table:
                next_table = rel["from_table"]

                join = {
                    "left": f"{rel['from_table']}.{rel['from_column']}",
                    "right": f"{rel['to_table']}.{rel['to_column']}"
                }

                if next_table == target_table:
                    return path + [join]

                if next_table not in visited:
                    visited.add(next_table)
                    queue.append(
                        (next_table, path + [join])
                    )

    return None


MONTH_NAMES = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def resolve_relative_date_range(value):
    """
    Convert natural language date phrases such as "this month"
    or "past 6 months" into a SQLite-compatible date range.
    """
    if not isinstance(value, str):
        return None

    text = value.strip().lower()
    now = datetime.now()

    def iso(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Normalize common phrases
    text = text.replace("created ", "")
    text = re.sub(r"\s+", " ", text).strip()

    month_match = re.search(r"\b(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\b", text)
    if month_match:
        month_name = month_match.group(1).lower()
        month_num = MONTH_NAMES[month_name]
        year = now.year
        start = datetime(year, month_num, 1, 0, 0, 0)
        if month_num == 12:
            end = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            end = datetime(year, month_num + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        return [iso(start), iso(end)]

    if text in {"today"}:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return [iso(start), iso(now)]

    if text in {"yesterday"}:
        day = now - timedelta(days=1)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=0)
        return [iso(start), iso(end)]

    if text in {"this month", "current month"}:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        else:
            end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        return [iso(start), iso(end)]

    if text in {"last month", "previous month"}:
        year = now.year
        month = now.month - 1 if now.month > 1 else 12
        if now.month == 1:
            year -= 1
        start = now.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        if month == 12:
            end = start.replace(year=year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        else:
            end = start.replace(month=month + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        return [iso(start), iso(end)]

    if text in {"this year", "current year"}:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        return [iso(start), iso(end)]

    if text in {"last 7 days", "past 7 days", "last seven days"}:
        start = now - timedelta(days=7)
        return [iso(start), iso(now)]

    if text in {"last 30 days", "past 30 days", "last thirty days"}:
        start = now - timedelta(days=30)
        return [iso(start), iso(now)]

    if text in {"last 6 months", "past 6 months", "last six months"}:
        start = now - timedelta(days=182)
        return [iso(start), iso(now)]

    if text.startswith("last ") and " days" in text:
        match = re.search(r"last\s+(\d+)\s+days?", text)
        if match:
            days = int(match.group(1))
            start = now - timedelta(days=days)
            return [iso(start), iso(now)]

    if text.startswith("past ") and " days" in text:
        match = re.search(r"past\s+(\d+)\s+days?", text)
        if match:
            days = int(match.group(1))
            start = now - timedelta(days=days)
            return [iso(start), iso(now)]

    if text.startswith("last ") and " months" in text:
        match = re.search(r"last\s+(\d+)\s+months?", text)
        if match:
            months = int(match.group(1))
            start = now - timedelta(days=30 * months)
            return [iso(start), iso(now)]

    if text.startswith("past ") and " months" in text:
        match = re.search(r"past\s+(\d+)\s+months?", text)
        if match:
            months = int(match.group(1))
            start = now - timedelta(days=30 * months)
            return [iso(start), iso(now)]

    if "month" in text and "last" in text:
        try:
            months = int(re.search(r"(\d+)", text).group(1))
            start = now - timedelta(days=30 * months)
            return [iso(start), iso(now)]
        except Exception:
            pass

    return None


def normalize_requested_fields(entity, requested_fields):
    """
    Convert user-requested field names into actual schema columns.
    """
    if not requested_fields:
        return LIST_COLUMNS.get(entity, [f"{ENTITY_MAP[entity]}.EntityId"])

    valid_fields = []
    for field in requested_fields:
        if not isinstance(field, str):
            continue

        normalized = field.strip().lower().replace(" ", "_").replace("-", "_")
        normalized = normalized.replace("createdon", "created_on")
        normalized = normalized.replace("capaid", "capa_id")
        normalized = normalized.replace("actionid", "action_id")
        normalized = normalized.replace("documentid", "document_id")
        normalized = normalized.replace("deviationid", "deviation_id")

        mapped = FIELD_MAP.get(entity, {}).get(normalized)
        if mapped is None:
            # Accept direct database-column-like names when already provided.
            for candidate in [
                f"{ENTITY_MAP[entity]}.{field.strip()}",
                f"{ENTITY_MAP[entity]}.{field.strip().replace(' ', '')}",
                field.strip()
            ]:
                if candidate in [
                    col for col in LIST_COLUMNS.get(entity, [])
                ] + [f"{ENTITY_MAP[entity]}.EntityId"]:
                    mapped = candidate
                    break

        if mapped is not None and mapped not in valid_fields:
            valid_fields.append(mapped)

    if valid_fields:
        return valid_fields

    return LIST_COLUMNS.get(entity, [f"{ENTITY_MAP[entity]}.EntityId"])


def build_query_plan(intent, schema):

    entity = intent["entity"]
    operation = intent["operation"]

    if entity not in ENTITY_MAP:
        raise ValueError(f"Unknown entity: {entity}")

    base_table = ENTITY_MAP[entity]

    # Entity ID column
    entity_id_column = f"{base_table}.EntityId"

    tables = [base_table]
    joins = []
    filters = []

    for condition in intent.get("conditions", []):
        condition_entity = condition["entity"]
        concept = condition["concept"]
        value = condition["value"]

        key = (
            condition_entity,
            concept
        )

        normalized_key = key
        if concept in {"created_on", "created", "created_at", "date"}:
            normalized_key = (condition_entity, "created_on")

        if normalized_key not in FILTER_MAP:
            raise ValueError(
                f"No filter mapping found for: {key}"
            )

        filter_column = FILTER_MAP[normalized_key]

        filter_table = filter_column.split(".")[0]

        # Add required table
        if filter_table not in tables:
            tables.append(filter_table)

        # Find relationship between base table and filter table
        if filter_table != base_table:

            relationship_path = find_relationship_path(
                schema,
                base_table,
                filter_table
            )

            if relationship_path is None:
                raise ValueError(
                    f"No relationship path found between "
                    f"{base_table} and {filter_table}"
                )
            for join in relationship_path:

                if join not in joins:
                    joins.append(join)

                left_table = join["left"].split(".", 1)[0]
                right_table = join["right"].split(".", 1)[0]

                if left_table not in tables:
                    tables.append(left_table)

                if right_table not in tables:
                    tables.append(right_table)

        # Normalize common values
        normalized_value = value

        if isinstance(value, str):
            if value.lower() == "open":
                normalized_value = "Open"
            elif value.lower() == "closed":
                normalized_value = "Closed"

        date_range = None
        if concept in {"created_on", "created", "created_at", "date"}:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                start_range = resolve_relative_date_range(str(value[0]))
                end_range = resolve_relative_date_range(str(value[1]))
                if start_range is not None and end_range is not None:
                    date_range = [start_range[0], end_range[1]]
                else:
                    date_range = [str(value[0]), str(value[1])]
            else:
                date_range = resolve_relative_date_range(str(value)) if value is not None else None

        if date_range is not None:
            filters.append({
                "column": filter_column,
                "operator": "BETWEEN",
                "value": date_range
            })
        else:
            filters.append({
                "column": filter_column,
                "operator": "=",
                "value": normalized_value
            })

    # ---------------------------------------------------------
    # SELECT + AGGREGATION
    # ---------------------------------------------------------

    if operation == "count":
        select = [entity_id_column]
        aggregation = {
            "function": "COUNT",
            "column": entity_id_column,
            "distinct": False
        }

    elif operation == "list":
        requested_fields = intent.get("fields")
        select = normalize_requested_fields(
            entity,
            requested_fields
        ) if requested_fields else LIST_COLUMNS.get(
            entity,
            [entity_id_column]
        )
        aggregation = None

    else:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )

    plan = {
        "tables": tables,
        "joins": joins,
        "filters": filters,
        "select": select,
        "aggregation": aggregation
    }

    return plan


def main():

    schema = load_schema()

    # This represents the output from the LLM.

    intent = {
        "entity": "deviation",
        "operation": "count",
        "conditions": [
            {
                "entity": "deviation",
                "concept": "status",
                "value": "open"
            },
            {
                "entity": "site",
                "concept": "name",
                "value": "Hyderabad Manufacturing Plant"
            }
        ]
    }

    plan = build_query_plan(intent, schema)

    print("\nQUERY PLAN:")
    print("=" * 50)

    plan_json = json.dumps(plan, indent=2)

    print(plan_json)

if __name__ == "__main__":
    main()