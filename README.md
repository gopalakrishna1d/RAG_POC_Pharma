# Pharma Quality Management AI Assistant

A conversational AI assistant for pharmaceutical Quality Management Systems (QMS), designed to help users retrieve and understand quality records through natural language.

Built with Python, FastAPI, LangChain, Ollama, and SQLite, the application combines schema-aware database querying, role-based access control, division-level data isolation, and conversational memory to provide a chatbot experience tailored to pharmaceutical quality operations.

Unlike a conventional database query tool, the assistant supports both structured data retrieval and general pharmaceutical quality-related conversations. Users can ask questions about deviations, CAPAs, and change controls, request record summaries, ask follow-up questions, or have a normal conversation about basic pharmaceutical quality concepts.

The project uses a local LLM and a locally seeded SQLite database, making it suitable for experimentation, demonstrations, and AI engineering development without requiring a paid LLM API.

## Key Features

* **Natural Language Database Querying:** Convert user questions into structured query plans and SQL queries.
* **Pharmaceutical QMS Support:** Retrieve and summarize records from Deviation, CAPA, and Change Control modules.
* **Role-Based Access Control (RBAC):** Restrict access according to the authenticated user's role and permissions.
* **Division-Level Data Isolation:** Limit users to records belonging to their assigned division unless their authorized role permits broader access.
* **Conversational Memory:** Maintain conversation context so users can ask follow-up questions without repeating previously supplied information.
* **General Chat Capabilities:** Answer greetings, basic questions, and general pharmaceutical quality-related queries.
* **Schema-Aware Query Planning:** Use database schema metadata to identify relevant tables, columns, relationships, and filters.
* **SQL Execution and Validation:** Execute generated read-only queries against the configured database.
* **Natural Language Responses:** Convert database results into understandable answers rather than returning raw SQL alone.
* **FastAPI Backend:** Expose the assistant through a REST API.
* **Local LLM Inference:** Use Ollama to run the language model locally.
* **Debugging and Traceability:** Return structured query information and execution results for development and testing.

## Supported QMS Modules

### 1. Deviation Management

Retrieve and understand deviation records, including their status, severity, description, assigned personnel, site or division, and related quality records.

Example questions:

* How many open deviations are there?
* Show critical deviations in my division.
* List deviations currently under investigation.
* Summarize deviation DEV-2026-0001.
* Which deviations have remained open the longest?

### 2. Corrective and Preventive Action (CAPA)

Retrieve CAPA records, review their progress, and identify related deviations and actions.

Example questions:

* How many open CAPAs are there?
* Show CAPAs created this month.
* Which CAPAs are overdue?
* List CAPAs associated with a particular deviation.
* Summarize the current status of a CAPA.

### 3. Change Control

Retrieve change control records and their associated status, classification, ownership, and approval information, where available in the database.

Example questions:

* List all open change controls.
* Show change controls awaiting approval.
* How many changes were initiated this month?
* Summarize change control CC-2026-0001.
* Show change controls associated with my division.

The exact fields and supported questions depend on the schema and seeded data included in the project.

## Technology Stack

| Component             | Technology                          | Purpose                                                    |
| --------------------- | ----------------------------------- | ---------------------------------------------------------- |
| Programming language  | Python 3.11+                        | Application logic                                          |
| API framework         | FastAPI                             | REST API and request handling                              |
| LLM orchestration     | LangChain                           | Prompt management and model integration                    |
| Local inference       | Ollama                              | Running the LLM locally                                    |
| Language model        | Qwen 2.5 3B                         | Intent extraction, query planning, and response generation |
| Database              | SQLite                              | Local storage for QMS records and access-control data      |
| Database connectivity | Python SQLite driver                | SQL execution                                              |
| Schema metadata       | JSON                                | Entity mapping and relationship definitions                |
| Conversational memory | Application-managed session history | Follow-up questions and contextual responses               |
| Testing               | pytest and FastAPI TestClient       | Unit and API testing                                       |

The application is designed to work locally using SQLite and Ollama. SQL Server connectivity can be retained as an optional extension.

## System Architecture

The application follows a modular pipeline that separates conversation handling, query planning, authorization, SQL execution, and response generation.

```text
                  User
                   |
                   v
          FastAPI Chat Endpoint
                   |
                   v
       User Authentication / Identity
                   |
                   v
         Role and Division Context
                   |
                   v
          Conversation Manager
                   |
                   v
            Intent Routing
              /         \
             /           \
            v             v
     General Chat     QMS Data Query
            |             |
            |             v
            |       Schema Mapping
            |             |
            |             v
            |       Query Planning
            |             |
            |             v
            |    Authorization Filters
            |             |
            |             v
            |        SQL Generation
            |             |
            |             v
            |       SQL Validation
            |             |
            |             v
            |      SQLite Execution
            |             |
            +-------> Response Generation
                          |
                          v
                 Conversation Memory
                          |
                          v
                    Chat Response
```

**Important design principle:** Authorization is enforced by the application and database-query layer, not by relying on the LLM to decide which records a user may access.

## User Access and Data Isolation

The application includes a demonstration identity and authorization model to simulate how an AI assistant would operate inside a multi-user pharmaceutical QMS.

### User and role management

The database contains user accounts, roles, and role assignments. Each user is associated with a division, and access is determined by the user's assigned role and applicable permissions.

The demonstration dataset includes users from multiple divisions and roles with different access scopes.

Example access model:

| Role                  | Access scope                                                                         |
| --------------------- | ------------------------------------------------------------------------------------ |
| System Administrator  | All records across divisions                                                         |
| Quality Administrator | Organization-wide quality records, subject to assigned permissions                   |
| Quality Manager       | Records within the authorized division, with additional permissions where configured |
| Quality User          | Permitted records within the assigned division                                       |
| Read-Only User        | Authorized records with retrieval-only access                                        |

These are illustrative roles; the actual access rules are defined by the application's authorization configuration.

### Division-level filtering

A user assigned to the Hyderabad division should only retrieve records authorized for that division.

For example:

* A Hyderabad user asks, "Show all open deviations."
* The application identifies the authenticated user's division.
* The query layer applies the division restriction.
* Only authorized Hyderabad deviation records are returned.
* A user with the required organization-wide permissions can retrieve records across divisions.

The LLM does not determine the user's identity, role, or division. These are obtained from the trusted application context.

### Database tables

The SQLite database includes QMS entities and access-control entities.

**QMS data tables**

* `Deviations`
* `CAPA`
* `Actions`
* `ChangeControls`
* `Sites`
* `Documents`

**Access-control tables**

* `Users`
* `Roles`
* `UserRoles` or an equivalent role-assignment structure
* `Divisions`
* `RolePermissions` or an equivalent permission structure, if permissions are modeled separately

The exact table names and relationships follow the implemented schema.

The database initialization script creates the required tables and populates them with deterministic demonstration data covering multiple users, roles, divisions, and QMS records.

**Security note:** The seeded identity model is intended for demonstration and testing. A production deployment should use a trusted authentication provider, secure password handling or single sign-on, server-side authorization, audit logging, and appropriate database and application security controls.

## Conversational Capabilities

The assistant supports two main interaction paths.

### 1. QMS data retrieval

Questions that require actual database records are routed through the schema-aware SQL pipeline.

Example:

**User:** How many open CAPAs are there in my division?

**Assistant:** There are 4 open CAPAs in your division.

The response is based on the records returned by the database, subject to the user's access permissions. The number above is illustrative.

### 2. General conversation

Questions that do not require database retrieval are handled as normal chatbot interactions.

Examples include:

* Hi, how are you?
* What is a CAPA in pharmaceutical quality management?
* What is the difference between a deviation and a change control?
* Why is root cause analysis important?
* Explain corrective and preventive actions in simple terms.

The assistant uses the LLM to generate conversational responses grounded in general pharmaceutical quality knowledge. It does not need to generate SQL for every message.

General answers are educational and do not replace approved SOPs, validated procedures, or formal quality decisions.

### 3. Context-aware follow-up questions

The conversation manager maintains relevant context within a conversation.

Example:

**User:** Show open deviations in my division.

**Assistant:** There are 5 open deviations in your division.

**User:** Which of them are critical?

**Assistant:** Of those open deviations, 2 are classified as critical.

The assistant interprets "them" using the previous conversation while applying the current user's authorization restrictions to the follow-up query.

Conversation memory is managed separately from authorization. Previous conversation history must never override the user's current identity, role, or division permissions.

## Natural Language to SQL Pipeline

The database-query workflow consists of the following stages.

1. **Question intake:** Receive the user's message through the chat API.
2. **Identity resolution:** Obtain the authenticated user's identity and access context.
3. **Conversation resolution:** Retrieve relevant prior messages for the active conversation.
4. **Intent classification:** Determine whether the question requires QMS data retrieval or general conversation.
5. **Entity identification:** Identify the relevant QMS module, entities, attributes, filters, and requested operation.
6. **Schema mapping:** Match the identified entities and attributes against `database_schema.json`.
7. **Query planning:** Build a structured query plan containing the intended tables, joins, filters, and aggregation.
8. **Authorization enforcement:** Apply the user's role-based permissions and division restrictions.
9. **SQL generation:** Generate SQL compatible with the configured database.
10. **SQL validation:** Check the query against application-defined safety rules.
11. **Database execution:** Execute the validated read-only query against SQLite.
12. **Answer generation:** Convert the query results into a concise, human-readable response.
13. **Context update:** Save the relevant interaction to the active conversation history.
14. **API response:** Return the answer and the appropriate diagnostic information.

Schema metadata helps the model understand the database structure without requiring the complete database schema to be embedded in every prompt.

## Repository Structure

The following structure represents the intended organization of the completed project. File names can be adjusted to match the final implementation.

```text
RAG_POC_Pharma/
│
├── api/
│   ├── main.py                 # FastAPI application and chat endpoints
│   ├── routes.py               # API route definitions, if separated
│   └── models.py               # Request and response models
│
├── auth/
│   ├── authentication.py       # User identity and authentication
│   ├── authorization.py        # Role and division access enforcement
│   └── permissions.py          # Permission checks
│
├── conversation/
│   ├── manager.py              # Conversation lifecycle and context
│   └── memory.py               # Conversation history management
│
├── database/
│   ├── db.py                   # Database connection and execution
│   ├── init_sqlite.py          # Schema creation and seed data
│   ├── fdc_rag_demo.db         # Local demonstration database
│   └── repositories/            # Data access functions, if separated
│
├── llm/
│   ├── model.py                # Ollama and LangChain configuration
│   ├── prompts.py              # Intent and response prompts
│   └── intent_router.py        # General-chat and QMS-query routing
│
├── query/
│   ├── query_pipeline.py       # End-to-end query workflow
│   ├── schema_mapper.py        # Schema-aware entity mapping
│   ├── query_planner.py        # Structured query plan generation
│   ├── sql_generator.py        # SQL generation
│   └── sql_validator.py        # Read-only query validation
│
├── schema/
│   └── database_schema.json    # Entities, fields, and relationships
│
├── tests/
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_query_pipeline.py
│   ├── test_sql_validator.py
│   ├── test_conversation.py
│   └── test_api.py
│
├── .env.example                # Example environment configuration
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

Install the following before running the project:

* Python 3.11 or newer
* Git
* Ollama
* The Qwen model used by the application
* A terminal such as PowerShell on Windows

The project is designed to run locally and does not require a cloud-hosted LLM API.

## End-to-End Setup and Initialization

### Step 1: Clone the repository

```bash
git clone https://github.com/gopalakrishna1d/RAG_POC_Pharma.git
cd RAG_POC_Pharma
```

If the repository is already available locally, open a terminal in the project root instead.

### Step 2: Create a Python virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If script execution is restricted, use the appropriate PowerShell execution policy for your environment or activate the environment through Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Confirm the active Python version:

```bash
python --version
```

### Step 3: Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The dependencies include the packages required for FastAPI, LangChain, Ollama integration, database access, configuration, and testing.

### Step 4: Install and start Ollama

Install Ollama from its official website:

https://ollama.com/

Download the configured model:

```bash
ollama pull qwen2.5:3b
```

Check that the model is available:

```bash
ollama list
```

If Ollama is not already running, start the Ollama application or run:

```bash
ollama serve
```

Keep the Ollama service running while using the chatbot.

The model name and endpoint should match the application's configuration.

### Step 5: Configure environment variables

Create a local `.env` file in the project root using `.env.example` as a reference.

Example:

```env
DB_TYPE=sqlite
DB_PATH=database/fdc_rag_demo.db

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

APP_ENV=development
```

Additional authentication or session configuration should be included if required by the implementation.

Do not commit `.env`, production credentials, API keys, session secrets, or user-specific sensitive data to Git.

### Step 6: Initialize the SQLite database

Run the initialization script from the project root:

```bash
python database/init_sqlite.py
```

The initialization process creates the database schema and inserts demonstration data for the supported QMS modules.

Depending on the implementation, initialization includes:

* Users and divisions
* Roles and role assignments
* Role permissions
* Sites
* Deviations
* CAPAs
* Actions
* Change controls
* Documents and relevant relationships

The script should create a consistent set of sample records so that queries and access-control scenarios can be tested reproducibly.

**Important:** If the initialization script recreates existing tables or clears data, running it again may reset the local database. Back up any data you want to preserve.

### Step 7: Verify the database

Run the database connectivity check if provided:

```bash
python database/test_connection.py
```

Verify that:

* The SQLite file exists at the configured path.
* All expected tables have been created.
* Seed data is present.
* Foreign-key relationships are valid.
* User, role, and division mappings are correct.

### Step 8: Validate the schema metadata

Inspect:

```text
schema/database_schema.json
```

Confirm that the schema metadata matches the initialized database.

It should describe the supported entities, relevant columns, relationships, and join keys needed by the query planner.

Test the schema mapping or query-planning module if a dedicated test script is provided.

### Step 9: Start the FastAPI server

From the project root:

```bash
uvicorn api.main:app --reload
```

The application should start at:

http://127.0.0.1:8000

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

The API documentation allows you to inspect the available endpoints and send test requests.

### Step 10: Check the application health

Run:

```bash
curl http://127.0.0.1:8000/health
```

The health endpoint should confirm that the API is running. If database or LLM readiness is exposed separately, verify those dependencies as well.

### Step 11: Authenticate a demonstration user

Use the authentication mechanism implemented by the project to establish a session or obtain an access token.

For local testing, use only the documented demonstration accounts and credentials, if supplied.

The API should resolve the user's role and division from trusted server-side data rather than accepting arbitrary role or division values from a chat request.

### Step 12: Send a chat request

The chat endpoint is:

```text
POST /api/chat
```

Example request:

```json
{
  "question": "How many open deviations are there?",
  "conversation_id": "demo-conversation-001"
}
```

The exact request fields depend on the API contract. If authentication is enabled, send the required session cookie or authorization header.

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d "{\"question\":\"How many open deviations are there?\",\"conversation_id\":\"demo-conversation-001\"}"
```

Replace the placeholder token with a valid token only if bearer-token authentication is implemented. Otherwise, use the application's actual authentication mechanism.

### Step 13: Test follow-up questions

Within the same conversation, ask a follow-up question:

```json
{
  "question": "Which of them are critical?",
  "conversation_id": "demo-conversation-001"
}
```

The application should use relevant conversation history to interpret the reference to previously retrieved deviations.

Verify that the follow-up query also enforces the current user's permissions and division restrictions.

### Step 14: Test general conversation

Ask a non-database question:

```json
{
  "question": "What is the difference between a deviation and a CAPA?",
  "conversation_id": "demo-conversation-001"
}
```

The application should route this to general response generation rather than unnecessarily generating and executing SQL.

### Step 15: Run the automated tests

If the test suite is included:

```bash
pytest -v
```

The test suite should cover query planning, SQL validation, API behavior, conversation handling, and authorization.

Before considering the project complete, verify that a user cannot retrieve another division's records by changing the question, asking for all records, or referring to previously retrieved data.

## API Response Format

A successful QMS query may return a structured response similar to the following:

```json
{
  "success": true,
  "question": "How many open deviations are there?",
  "answer": "There are 5 open deviations in your division.",
  "intent": "qms_query",
  "query_plan": {
    "entity": "Deviation",
    "operation": "count",
    "filters": {
      "status": "Open"
    }
  },
  "sql": "SELECT COUNT(*) FROM Deviations WHERE Status = ?",
  "rows": [
    {
      "count": 5
    }
  ],
  "conversation_id": "demo-conversation-001"
}
```

This is an illustrative response, not a guarantee of the exact implemented response schema or seeded record count.

The generated SQL shown here omits the division filter for readability. The actual executed query must enforce all applicable authorization constraints.

Diagnostic fields such as SQL, query plans, and raw rows should be restricted to authorized development or administrative contexts. Normal end users should receive only the information they are permitted to access.

## Security and Reliability Considerations

Although the project uses a local database and model, access control and query safety remain important.

The application should enforce the following safeguards:

* **Trusted identity:** Resolve the current user through the configured authentication mechanism.
* **Server-side authorization:** Derive role permissions and division restrictions from trusted database records.
* **Division isolation:** Apply access restrictions to every applicable query, including counts, aggregations, joins, and follow-up questions.
* **Read-only execution:** Restrict the assistant to approved read operations.
* **SQL validation:** Reject multiple statements, data modification, schema modification, and other disallowed operations.
* **Parameterized values:** Use SQL parameters for user-derived filter values rather than interpolating them directly into SQL.
* **Controlled schema access:** Allow queries only against approved tables and columns.
* **Error handling:** Avoid exposing database credentials, internal exceptions, or sensitive query details to ordinary users.
* **Conversation isolation:** Separate conversation history between users and sessions.
* **Memory expiration:** Apply appropriate retention and expiration policies to stored conversation history.
* **Auditability:** Record appropriate query and access events without unnecessarily storing sensitive information.

A local LLM does not by itself guarantee that data is secure or that generated SQL is correct. The application must enforce permissions and validate queries independently of model output.

The demonstration is not a validated pharmaceutical GxP system. Production use would require a separate assessment of applicable regulatory requirements, validation, audit trails, electronic records, change management, and data integrity controls.

## Limitations

* The included database contains synthetic demonstration data rather than live pharmaceutical records.
* Query accuracy depends on the schema metadata, prompts, model capabilities, and supported relationships.
* Complex multi-table questions may require additional query-planning and validation logic.
* A small local model may occasionally misinterpret ambiguous questions or generate incomplete answers.
* Conversational memory depends on the configured history-management strategy and available context window.
* General pharmaceutical answers may be incomplete and should not be treated as approved procedural guidance.
* Performance depends on the local machine, database size, and model configuration.

## Future Enhancements

Potential improvements include:

* Persistent user authentication and integration with enterprise identity providers.
* More granular permission management and comprehensive audit logging.
* Improved schema linking and complex relationship handling.
* Query evaluation datasets and automated SQL accuracy tests.
* Conversation summarization and persistent conversation storage.
* Streaming responses and a dedicated chat interface.
* Retrieval from approved SOPs and controlled pharmaceutical documentation.
* More robust evaluation of answer correctness, authorization boundaries, and prompt-injection resistance.
* Optional SQL Server integration for enterprise database environments.
* Deployment, monitoring, and performance testing.

## License

This repository is a demonstration project. Unless a license file is included, no specific open-source license is granted. Add an appropriate license before permitting reuse or redistribution.
