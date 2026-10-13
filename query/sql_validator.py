import re

FORBIDDEN_KEYWORDS = (
    "ALTER",
    "ATTACH",
    "BEGIN",
    "COMMIT",
    "CREATE",
    "DELETE",
    "DETACH",
    "DROP",
    "EXEC",
    "EXECUTE",
    "GRANT",
    "INSERT",
    "MERGE",
    "PRAGMA",
    "REPLACE",
    "REVOKE",
    "ROLLBACK",
    "SAVEPOINT",
    "SET",
    "TRUNCATE",
    "UPDATE",
)


def validate_sql_statement(sql: str) -> bool:
    """Allow only read-only SELECT statements for the demo QMS chatbot."""
    if sql is None or not str(sql).strip():
        raise ValueError("SQL statement is empty.")

    statement = str(sql).strip()

    if not re.match(r"^SELECT\b", statement, flags=re.IGNORECASE):
        raise ValueError("Only SELECT statements are allowed.")

    if ";" in statement[:-1]:
        raise ValueError("Multiple SQL statements are not allowed.")

    if re.search(r"--|/\*|\*/", statement):
        raise ValueError("SQL comments are not allowed.")

    if re.search(r"\b(?:" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", statement, flags=re.IGNORECASE):
        raise ValueError("Only read-only SELECT statements are allowed.")

    if re.search(r"\b(INTO|VALUES|RETURNING|FROM\s+\w+\s+VALUES)\b", statement, flags=re.IGNORECASE):
        raise ValueError("Data-changing SQL is not allowed.")

    return True
