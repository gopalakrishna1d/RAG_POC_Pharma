import pyodbc


SERVER = r"ALTESTSERVER10\SQLSTD19"
DATABASE = "FDCRAGDemo"
USERNAME = "sa"
PASSWORD = "ALlogic@25"


def get_connection():
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)


