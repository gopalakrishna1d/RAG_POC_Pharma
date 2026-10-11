# RAG POC Pharma

A lightweight RAG-style chatbot for querying a pharmaceutical quality management database using natural language. The application extracts intent from a user question, maps it to the relevant schema, generates SQL, executes it, and returns a human-readable answer.

## What this project does

- Accepts natural-language questions such as:
  - "How many open deviations are there?"
  - "Show CAPAs created this month."
  - "List actions assigned to Aisha Rao."
- Uses a schema-driven pipeline to convert the question into a query plan and SQL.
- Executes the query against an SQLite database by default.
- Exposes the logic through a FastAPI API.
- Returns both the generated SQL and the raw rows for easy debugging and validation.

## Supported entities

The demo focuses on pharmaceutical quality data across these entities:

- Deviation
- CAPA
- Action
- Site
- User
- Document

## Tech stack

- Python
- FastAPI
- SQLite (default)
- SQL Server support is included via ODBC but is optional
- LangChain + Ollama for intent extraction and answer generation

## Repository structure

```text
RAG_POC_Pharma/
├── api/
│   └── main.py              # FastAPI application and chat endpoint
├── database/
│   ├── db.py                # Database connection logic
│   ├── fdc_rag_demo.db     # SQLite database
│   └── init_sqlite.py      # SQLite schema and seed data creation
├── schema/
│   └── database_schema.json # Database schema metadata used by query planning
├── query_pipeline.py        # End-to-end RAG workflow
├── schema_test.py           # Schema mapping and SQL builder logic
├── sql_generator.py         # SQL generation from query plan
├── test_connection.py       # Simple DB connectivity check
├── requirements.txt         # Python dependencies
├── .env                     # Local environment settings
├── .gitignore              # Git exclusions
└── README.md               # Project overview and usage
```

## Prerequisites

- Python 3.11+
- Ollama installed and running locally
- Access to the model used in the project (`qwen2.5:3b` by default)

If the model is not available locally, pull it before running the app:

```bash
ollama pull qwen2.5:3b
```

## Setup

1. Open a terminal in the project root.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Confirm the default database is present and ready:

```bash
python database\init_sqlite.py
```

The project defaults to SQLite and uses the database at:

```text
database/fdc_rag_demo.db
```

## Running the API

Start the FastAPI server from the project root:

```bash
uvicorn api.main:app --reload
```

The app will be available at:

- http://127.0.0.1:8000

Health check endpoint:

```bash
curl http://127.0.0.1:8000/health
```

## Chat API

Send a POST request to:

```text
POST /api/chat
```

Example JSON payload:

```json
{
  "question": "How many open CAPAs are there?"
}
```

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"How many open CAPAs are there?"}'
```

The response includes:

- `success`
- `question`
- `answer`
- `intent`
- `query_plan`
- `sql`
- `rows`

## Database configuration

The project reads DB settings from `.env`.

Default SQLite configuration:

```env
DB_TYPE = "sqlite"
DB_PATH = "database/fdc_rag_demo.db"
```

If you want to switch to SQL Server instead, update `.env` with the appropriate values:

```env
DB_TYPE = "mssql"
DB_SERVER = "your-server"
DB_DATABASE = "your-database"
DB_USERNAME = "your-user"
DB_PASSWORD = "your-password"
```

## Running the pipeline directly

You can also invoke the query pipeline from Python:

```python
from query_pipeline import process_question

result = process_question("Show open deviations for Hyderabad Manufacturing Plant")
print(result["answer"])
```

## Notes

- This project is intended as a demo/prototype for RAG-driven database querying in a pharmaceutical quality context.
- The default dataset is small and seeded locally for demonstration purposes.
- The generated SQL and natural-language answer are useful for testing and validation, especially when tuning the schema mappings or LLM prompts.

## License

This project does not include a custom license file. Use it as a demonstration project and adapt it to your organization’s internal standards and compliance requirements.
