import os
import sqlite3
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

from database.init_sqlite import ensure_sqlite_database

load_dotenv()

SERVER = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_DATABASE")
USERNAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")
DB_TYPE = (os.getenv("DB_TYPE") or "sqlite").lower()
DB_PATH = os.getenv("DB_PATH") or str(Path(__file__).resolve().parent / "fdc_rag_demo.db")


def get_connection():
    if DB_TYPE == "sqlite":
        ensure_sqlite_database(DB_PATH, reset=False)
        return sqlite3.connect(DB_PATH)

    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)


