import os
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
from collections import Counter

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.services.llm_service import generate_answer
from backend.app.services.rag_service import generate_rag_answer
from backend.app.services.pdf_upload_service import (
    upload_pdf_to_chromadb,
)
from backend.app.services.vector_store import collection
from backend.app.services.ticket_ai_service import analyze_ticket

from backend.app.database.ticket_db import (
    initialize_database,
    create_ticket,
    get_ticket,
    list_tickets,
    save_ticket_analysis,
    initialize_review_columns,
    save_engineer_review,
    update_ticket_status,
)


# =====================================
# FastAPI Application
# =====================================

app = FastAPI(
    title="Enterprise AI IT Operations Copilot",
    description=(
        "AI-powered IT Support, Server Operations, "
        "Azure and AWS Incident Management Platform"
    ),
    version="1.0.0",
)


# =====================================
# Public Demo Security
# =====================================

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

class PublicDemoGuard(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if DEMO_MODE:
            path = request.url.path
            method = request.method

            # Block API operations that change stored data
            blocked = (
                method in {"POST", "PATCH", "PUT", "DELETE"}
                and (
                    path.startswith("/tickets")
                    or path.startswith("/documents")
                )
            )

            if blocked:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "This action is disabled in public demo mode."
                    },
                )

        return await call_next(request)


app.add_middleware(PublicDemoGuard)


# =====================================
# Initialize Database
# =====================================

initialize_database()


# =====================================
# CORS Configuration
# =====================================

# Local frontend is opened through file://
# Production deployments need restricted origins
# and proper authentication.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "null",
    "https://nikamrahul-enterprise-ai-it-copilot.hf.space",
],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "DELETE",
    ],
    allow_headers=["Content-Type"],
)


# =====================================
# Request Models
# =====================================

class ChatRequest(BaseModel):
    question: str


class TicketCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class EngineerReviewRequest(BaseModel):
    decision: str
    reviewed_by: str = Field(min_length=1)
    notes: str = Field(min_length=1)


class TicketStatusRequest(BaseModel):
    status: str


# =====================================
# Home API
# =====================================

@app.get("/")
def home():
    return {
        "message": (
            "Enterprise AI IT Operations Copilot "
            "is running!"
        )
    }


# =====================================
# General AI Chat
# =====================================

@app.post("/chat")
def ask_ai(request: ChatRequest):
    answer = generate_answer(request.question)

    return {
        "answer": answer
    }


# =====================================
# RAG Knowledge Assistant
# =====================================

@app.post("/rag/chat")
def ask_company_ai(request: ChatRequest):
    result = generate_rag_answer(
        request.question
    )

    return result


# =====================================
# PDF Upload API
# =====================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    try:
        result = await upload_pdf_to_chromadb(
            file
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print(
            f"PDF upload error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process PDF.",
        )


# =====================================
# List Knowledge Base Documents
# =====================================

@app.get("/documents")
def list_documents():
    data = collection.get(
        include=["metadatas"]
    )

    counts = Counter(
        (metadata or {}).get(
            "source",
            "unknown"
        )
        for metadata in data["metadatas"]
    )

    return {
        "total_documents": len(counts),
        "total_chunks": len(data["ids"]),
        "documents": [
            {
                "filename": filename,
                "chunks": count,
            }
            for filename, count in counts.items()
        ],
    }


# =====================================
# Delete Uploaded PDF
# =====================================

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    confirm: bool = False,
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail=(
                "Deletion not confirmed. "
                "Set confirm=true to delete."
            ),
        )

    # Validate 32-character document ID
    if (
        len(document_id) != 32
        or any(
            character not in "0123456789abcdef"
            for character in document_id
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        )

    # Find document chunks
    data = collection.get(
        where={
            "document_id": document_id
        },
        include=["metadatas"],
    )

    if not data["ids"]:
        raise HTTPException(
            status_code=404,
            detail="Uploaded document not found.",
        )

    # Protect non-PDF knowledge documents
    if not all(
        (metadata or {})
        .get("source", "")
        .lower()
        .endswith(".pdf")
        for metadata in data["metadatas"]
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "This document cannot be deleted."
            ),
        )

    # Delete indexed chunks
    collection.delete(
        ids=data["ids"]
    )

    # Delete stored PDF file
    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    saved_pdf = (
        project_root
        / "data"
        / "uploads"
        / f"{document_id}.pdf"
    )

    saved_pdf.unlink(
        missing_ok=True
    )

    return {
        "message": (
            "Document deleted successfully!"
        ),
        "document_id": document_id,
        "deleted_chunks": len(data["ids"]),
    }


# =====================================
# Create IT Incident Ticket
# =====================================

@app.post(
    "/tickets",
    status_code=201
)
def create_new_ticket(
    request: TicketCreateRequest
):
    try:
        ticket = create_ticket(
            title=request.title,
            description=request.description,
        )

        return {
            "message": (
                "Ticket created successfully"
            ),
            "ticket": ticket,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# =====================================
# List All IT Tickets
# =====================================

@app.get("/tickets")
def get_all_tickets():
    tickets = list_tickets()

    return {
        "total_tickets": len(tickets),
        "tickets": tickets,
    }


# =====================================
# Get Ticket By ID
# =====================================

@app.get("/tickets/{ticket_id}")
def get_ticket_by_id(
    ticket_id: int
):
    ticket = get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return ticket


# =====================================
# AI Ticket Analysis + SQLite Saving
# =====================================

@app.post("/tickets/{ticket_id}/analyze")
def analyze_existing_ticket(
    ticket_id: int
):
    # Step 1: Find existing ticket
    ticket = get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    # Step 2: Generate AI analysis
    try:
        analysis = analyze_ticket(
            title=ticket["title"],
            description=ticket["description"],
        )

    except Exception as error:
        print(
            f"Ticket AI analysis failed: {error}"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "AI analysis unavailable. "
                "Check Ollama and model output."
            ),
        )

    # Step 3: Save analysis in SQLite
    try:
        saved = save_ticket_analysis(
            ticket_id=ticket_id,
            analysis=analysis,
        )

        if not saved:
            raise HTTPException(
                status_code=404,
                detail="Ticket not found",
            )

    except HTTPException:
        raise

    except Exception as error:
        print(
            f"Database saving failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save AI analysis."
            ),
        )

    # Step 4: Return analysis
    return {
        "message": (
            "AI analysis completed and saved"
        ),
        "ticket_id": ticket_id,
        "title": ticket["title"],
        "current_status": ticket["status"],
        "ai_analysis": analysis,
    }


# =====================================
# Engineer Review API
# =====================================

@app.post("/tickets/{ticket_id}/review")
def review_ticket(
    ticket_id: int,
    review: EngineerReviewRequest,
):
    if review.decision not in (
        "Approved",
        "Rejected",
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Decision must be "
                "Approved or Rejected."
            ),
        )

    try:
        initialize_review_columns()

        updated_ticket = save_engineer_review(
            ticket_id=ticket_id,
            decision=review.decision,
            reviewed_by=review.reviewed_by,
            notes=review.notes,
        )

        return {
            "message": (
                "Engineer review saved successfully"
            ),
            "ticket_id": ticket_id,
            "review_status": review.decision,
            "ticket": updated_ticket,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# =====================================
# Ticket Status Update API
# =====================================

@app.patch("/tickets/{ticket_id}/status")
def change_ticket_status(
    ticket_id: int,
    request: TicketStatusRequest,
):
    allowed_statuses = (
        "Open",
        "In Progress",
        "Resolved",
        "Closed",
    )

    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail=(
                "Status must be Open, "
                "In Progress, Resolved, "
                "or Closed."
            ),
        )

    try:
        updated_ticket = update_ticket_status(
            ticket_id=ticket_id,
            new_status=request.status,
        )

        return {
            "message": (
                "Ticket status updated successfully"
            ),
            "ticket_id": ticket_id,
            "new_status": request.status,
            "ticket": updated_ticket,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )




# =====================================
# Dashboard Analytics API
# =====================================

@app.get("/dashboard/stats")
def get_dashboard_stats():

    # Fetch all existing tickets from SQLite
    tickets = list_tickets()

    # Ticket status counters
    total_tickets = len(tickets)

    open_tickets = sum(
        1 for ticket in tickets
        if ticket.get("status") == "Open"
    )

    in_progress_tickets = sum(
        1 for ticket in tickets
        if ticket.get("status") == "In Progress"
    )

    resolved_tickets = sum(
        1 for ticket in tickets
        if ticket.get("status") == "Resolved"
    )

    closed_tickets = sum(
        1 for ticket in tickets
        if ticket.get("status") == "Closed"
    )

    # Engineer review counters
    pending_reviews = sum(
        1 for ticket in tickets
        if ticket.get("review_status", "Pending") == "Pending"
    )

    approved_reviews = sum(
        1 for ticket in tickets
        if ticket.get("review_status") == "Approved"
    )

    rejected_reviews = sum(
        1 for ticket in tickets
        if ticket.get("review_status") == "Rejected"
    )

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "in_progress_tickets": in_progress_tickets,
        "resolved_tickets": resolved_tickets,
        "closed_tickets": closed_tickets,
        "pending_reviews": pending_reviews,
        "approved_reviews": approved_reviews,
        "rejected_reviews": rejected_reviews,
    }
