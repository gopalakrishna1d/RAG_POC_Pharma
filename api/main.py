from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from query_pipeline import process_question


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="FDC RAG Chatbot API",
    description="RAG chatbot API for FDC",
    version="1.0.0"
)


# ---------------------------------------------------------
# Request Model
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    question: str


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "fdc-rag-chatbot"
    }


# ---------------------------------------------------------
# Chat Endpoint
# ---------------------------------------------------------

@app.post("/api/chat")
def chat(request: ChatRequest):

    try:

        result = process_question(
            request.question
        )

        return {
            "success": True,
            "question": result["question"],
            "answer": result["answer"],
            "intent": result["intent"],
            "query_plan": result["query_plan"],
            "sql": result["sql"],
            "rows": [
                list(row)
                for row in result["rows"]
            ]
        }

    except Exception as error:

        print("\nAPI ERROR:")
        print(error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )