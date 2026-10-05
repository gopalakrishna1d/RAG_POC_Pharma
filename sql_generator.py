import json


def quote_identifier(identifier):
    """
    Convert Table.Column into SQL Server-safe [Table].[Column].
    """

    parts = identifier.split(".")

    return ".".join(f"[{part}]" for part in parts)


def escape_sql_value(value):
    """
    Escape a string value for SQL Server.
    """

    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"

    if value is None:
        return "NULL"

    return str(value)


def generate_sql(plan):
    """
    Convert a structured query plan into SQL Server SQL.
    """

    tables = plan["tables"]
    joins = plan.get("joins", [])
    filters = plan.get("filters", [])
    aggregation = plan.get("aggregation")

    if not tables:
        raise ValueError("Query plan contains no tables.")

    base_table = tables[0]

    # ---------------------------------------------------------
    # TABLE ALIASES
    # ---------------------------------------------------------

    aliases = {}
    used_aliases = {}

    for table in tables:

        first_letter = table[0].lower()

        if first_letter in used_aliases:
            used_aliases[first_letter] += 1

            aliases[table] = (
                first_letter +
                str(used_aliases[first_letter])
            )

        else:
            used_aliases[first_letter] = 1
            aliases[table] = first_letter

    # ---------------------------------------------------------
    # SELECT
    # ---------------------------------------------------------

    if aggregation:

        function = aggregation["function"]
        aggregation_table, aggregation_column = (
            aggregation["column"].split(".", 1)
        )
        aggregation_alias = aliases[aggregation_table]
        column = (
            f"{aggregation_alias}.[{aggregation_column}]"
        )

        if aggregation.get("distinct", False):
            select_clause = (
                f"{function}(DISTINCT {column})"
            )
        else:
            select_clause = (
                f"{function}({column})"
            )

        select_clause += " AS Result"

    else:

        select_columns = plan.get("select", [])

        if not select_columns:
            raise ValueError(
                "No SELECT columns found."
            )

        select_parts = []
        for column in select_columns:
            table_name, column_name = (
                column.split(".", 1)
            )
            alias = aliases[table_name]
            select_parts.append(
                f"{alias}.[{column_name}]"
            )
        select_clause = ", ".join(select_parts)

    # ---------------------------------------------------------
    # FROM
    # ---------------------------------------------------------

    base_alias = aliases[base_table]

    sql = (
        f"SELECT {select_clause}\n"
        f"FROM [{base_table}] AS {base_alias}\n"
    )

    # ---------------------------------------------------------
    # JOIN
    # ---------------------------------------------------------

    joined_tables = {base_table}

    for join in joins:
        left = join["left"]
        right = join["right"]
        left_table, left_column = (
            left.split(".", 1)
        )
        right_table, right_column = (
            right.split(".", 1)
        )

        if left_table in joined_tables:
            new_table = right_table

        elif right_table in joined_tables:
            new_table = left_table

        else:
            raise ValueError(
                f"Cannot determine JOIN order for: "
                f"{left} = {right}"
            )

        sql += (
            f"INNER JOIN [{new_table}] AS "
            f"{aliases[new_table]}\n"
        )

        sql += (
            f"    ON "
            f"{aliases[left_table]}.[{left_column}] = "
            f"{aliases[right_table]}.[{right_column}]\n"
        )

        joined_tables.add(new_table)
    # ---------------------------------------------------------
    # WHERE
    # ---------------------------------------------------------

    if filters:

        conditions = [] 

        for filter_item in filters:

            column = filter_item["column"]
            operator = filter_item["operator"]
            value = filter_item["value"]

            table_name, column_name = column.split(".", 1)

            alias = aliases[table_name]

            quoted_column = (
                f"{alias}.[{column_name}]"
            )

            if value is None:

                if operator == "=":
                    condition = (
                        f"{quoted_column} IS NULL"
                    )

                elif operator in ("!=", "<>"):
                    condition = (
                        f"{quoted_column} IS NOT NULL"
                    )

                else:
                    raise ValueError(
                        f"Invalid NULL operator: {operator}"
                    )

            else:

                condition = (
                    f"{quoted_column} "
                    f"{operator} "
                    f"{escape_sql_value(value)}"
                )

            conditions.append(condition)

        sql += "WHERE\n"
        sql += "  " + "\n  AND ".join(conditions)
        sql += "\n"

    sql += ";"

    return sql


if __name__ == "__main__":

    plan = {
        "tables": [
            "Deviations",
            "Sites"
        ],
        "joins": [
            {
                "left": "Deviations.SiteId",
                "right": "Sites.EntityId"
            }
        ],
        "filters": [
            {
                "column": "Deviations.Status",
                "operator": "=",
                "value": "Open"
            },
            {
                "column": "Sites.SiteName",
                "operator": "=",
                "value": "Hyderabad Manufacturing Plant"
            }
        ],
        "select": [
            "Deviations.EntityId"
        ],
        "aggregation": {
            "function": "COUNT",
            "column": "Deviations.EntityId",
            "distinct": False
        }
    }

    sql = generate_sql(plan)

    print("\nGENERATED SQL:")
    print("=" * 50)
    print(sql)