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
    conversation_id: str | None = None
    user_id: str | None = None


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

        response = {
            "success": True,
            "question": result["question"],
            "answer": result["answer"],
            "intent": result["intent"],
            "query_plan": result.get("query_plan"),
            "sql": result.get("sql"),
            "rows": [
                list(row)
                for row in result.get("rows", [])
            ],
        }
        if request.conversation_id is not None:
            response["conversation_id"] = request.conversation_id
        if request.user_id is not None:
            response["user_id"] = request.user_id
        return response

    except Exception as error:

        print("\nAPI ERROR:")
        print(error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )