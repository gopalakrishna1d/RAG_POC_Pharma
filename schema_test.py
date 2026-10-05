import json
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
    ("user", "name"): "Users.UserName"
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

        if key not in FILTER_MAP:
            raise ValueError(
                f"No filter mapping found for: {key}"
            )

        filter_column = FILTER_MAP[key]

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
        select = LIST_COLUMNS.get(
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