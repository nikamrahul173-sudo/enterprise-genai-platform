# Enterprise AI IT Operations Copilot

**AI-powered IT support and incident management — Local Ollama + Cloud Groq Demo**

[Live Demo](https://huggingface.co/spaces/nikamrahul/enterprise-ai-it-copilot) | [GitHub Repository](https://github.com/nikamrahul173-sudo/enterprise-genai-platform) | [Backend Health](https://enterprise-genai-platform-6xrg.onrender.com/healthz)

## Cloud Deployment (Public Demo)

The project includes a publicly accessible AI IT Operations Copilot deployed using Hugging Face Spaces and Render.

### Cloud Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript — Hugging Face Spaces |
| Backend | Python, FastAPI — Render |
| Cloud AI | Groq API |
| Demo Database | SQLite |
| Local AI | Ollama |
| Local RAG | ChromaDB + Ollama Embeddings |

### Public Demo Features

- Groq-powered IT troubleshooting assistant.
- Five synthetic IT support tickets.
- Dashboard showing ticket statistics.
- Read-only public ticket interface.
- Knowledge Base page with document listing and disabled public uploads.

### Current Limitations

- Cloud PDF RAG is not yet verified as a working public demo feature.
- No documents are currently indexed in the cloud Knowledge Base.
- Render Free storage is not persistent across all restarts or redeployments.
- Public ticket changes and document uploads require administrator authorization.
- Full enterprise authentication, role-based access control, and comprehensive audit logging are not implemented.
- AI recommendations require human verification.

**Project status:** Working portfolio demonstration, not a production-ready enterprise platform.

---









# Enterprise AI IT Operations Copilot

An AI-powered IT operations copilot featuring local Ollama-based RAG workflows and a deployed Groq-powered cloud demonstration.

## Overview

Enterprise AI IT Operations Copilot is a portfolio project designed to demonstrate how Generative AI can assist IT support engineers with troubleshooting, knowledge retrieval, incident analysis, and human-reviewed ticket management.

The local application uses Ollama; the public cloud demo uses Groq for AI inference.

## Key Features

- **AI Knowledge Assistant:** Answer IT support questions using a local language model and retrieval-augmented generation (RAG).
- **PDF Knowledge Base:** Upload PDF documents, extract content, generate embeddings, and store searchable chunks in ChromaDB.
- **IT Incident Management:** Create, view, and manage IT support tickets.
- **AI Incident Analysis:** Generate suggested categories, priorities, troubleshooting steps, and escalation recommendations.
- **Basic Safety Guardrails:** Identify potentially risky AI-generated troubleshooting actions for human review.
- **Engineer Review Workflow:** Record approval or rejection decisions with reviewer names and notes.
- **Ticket Lifecycle:** Move tickets between Open, In Progress, Resolved, and Closed.
- **Dashboard Analytics:** View ticket and review statistics retrieved from SQLite.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend API | Python, FastAPI |
| Local LLM | Ollama, Qwen 2.5 1.5B |
| Embeddings | Ollama, nomic-embed-text |
| Vector Database | ChromaDB |
| Relational Database | SQLite |
| PDF Processing | PyMuPDF |
| Frontend | HTML, CSS, JavaScript |
| API Testing | Swagger UI |
| Development Environment | VS Code, Windows |

 ## Architecture

### Local Development Architecture

```text
User
  |
  v
HTML / CSS / JavaScript Frontend
  |
  v
FastAPI Backend
  |
  +----> Ollama LLM
  |         |
  |         +----> AI Chat and Incident Analysis
  |
  +----> RAG Service
  |         |
  |         +----> Ollama Embeddings
  |         |
  |         +----> ChromaDB Knowledge Base
  |
  +----> SQLite Database
            |
            +----> Tickets
            +----> AI Analysis
            +----> Engineer Reviews
            +----> Ticket Status
```


### Deployed Cloud Architecture

```mermaid
flowchart TD
    U[User] --> F[Hugging Face Frontend]
    F --> API[FastAPI on Render]
    API --> CHAT[AI Chat]
    CHAT --> G[Groq LLM]
    API --> RAG[Cloud RAG]
    RAG --> S[SQLite Keyword Search]
    S --> KB[(Knowledge Chunks)]
    RAG --> G
    MD[Markdown IT Runbooks] --> SEED[Startup Indexing]
    SEED --> KB
    API --> T[Ticket APIs]
    T --> DB[(SQLite Tickets)]
```

The deployed frontend runs on Hugging Face Spaces and connects to a FastAPI backend hosted on Render. AI responses are generated using Groq. Cloud RAG retrieves relevant knowledge chunks through SQLite keyword matching and provides source references.

**Note:** Cloud RAG does not currently use vector embeddings. Render Free storage is ephemeral, and the public demo is not a production authentication system.


## Local Installation

### Prerequisites

- Python 3.13
- Ollama installed and running
- Git
- A modern web browser

### 1. Clone the repository

```powershell
git clone https://github.com/nikamrahul173-sudo/enterprise-genai-platform.git
cd enterprise-genai-platform
```



### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Download Ollama models

```powershell
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

Ensure Ollama is running before starting the backend.

### 5. Start the backend

```powershell
python -m uvicorn backend.app.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

Swagger API documentation:

`http://127.0.0.1:8000/docs`

### 6. Open the frontend

Open `frontend/index.html` in your browser.

## Example Workflow

1. Create an IT incident ticket describing a VPN or Windows Server issue.
2. Run AI analysis to generate troubleshooting recommendations.
3. Review AI-suggested category, priority, and potentially risky actions.
4. Submit an engineer approval or rejection with notes.
5. Update the ticket status as the simulated incident progresses.
6. View updated metrics in the dashboard.

## Testing

The following workflows have been manually tested in the local development environment:

- FastAPI health endpoint
- AI assistant responses
- Knowledge Base document listing and PDF upload
- Ticket creation and retrieval
- AI incident analysis
- Engineer approval
- Ticket status updates
- Dashboard statistics

Automated test coverage and deployment testing are planned improvements.

## Security and Limitations

This is a local portfolio demonstration, not a production-ready enterprise incident management system.

- Engineer identity is entered manually; authentication and role-based access control are not implemented.
- Review records currently store the latest decision rather than a complete audit history.
- Safety detection uses basic rules and does not guarantee identification of every dangerous action.
- AI-generated troubleshooting instructions must be verified by qualified engineers.
- Ticket approval and status changes do not execute infrastructure commands or verify that an incident was actually resolved.
- Local databases, vector stores, credentials, and private documents should not be committed to the repository.

## Future Improvements

- User authentication and role-based access control
- Full audit logging for ticket reviews and status changes
- Automated backend and frontend tests
- Improved retrieval evaluation and source citations
- Docker-based local deployment
- Enhanced AI safety validation

## Project Purpose

This project demonstrates practical experience with local LLM integration, retrieval-augmented generation, REST API development, vector databases, structured AI output, SQLite persistence, and human-in-the-loop workflows.





## Application Screenshots

### AI Assistant
Local AI-powered IT troubleshooting assistant.

![AI Assistant](screenshots/ai-assistant.png)

### Ticket Management
AI-powered incident analysis, engineer review, and ticket lifecycle management.

![Ticket Management](screenshots/ticket-management.png)

### Knowledge Base
PDF document management and retrieval-augmented generation.

![Knowledge Base](screenshots/knowledge-base.png)

### Dashboard
IT incident statistics and review tracking.

![Dashboard](screenshots/dashboard.png)


### Cloud RAG Knowledge Base

![Cloud RAG Knowledge Base](screenshots/cloud-rag-knowledge-base.png)




## Manual API Testing Results

Core application workflows were manually tested using FastAPI Swagger UI (`http://127.0.0.1:8000/docs`).

| Feature | Test Result |
|---|---|
| AI Chat using Ollama | Passed |
| RAG-based Knowledge Base Chat | Passed |
| Document Upload and Retrieval | Passed |
| IT Ticket Creation | Passed |
| AI Incident Analysis | Passed |
| Engineer Review and Approval | Passed |
| Ticket Status Lifecycle | Passed |
| Dashboard Statistics | Passed |

### Ticket Lifecycle Validation

Test Ticket #6 (`VPN Disconnecting Frequently`) was used to validate the incident management workflow:

1. Created a new IT support ticket.
2. Generated AI-based incident analysis and troubleshooting recommendations.
3. Saved engineer approval with review notes.
4. Updated the ticket through Open → In Progress → Resolved → Closed.
5. Verified the final ticket counts using the dashboard statistics API.

### Final Dashboard Verification

| Metric | Verified Value |
|---|---:|
| Total Tickets | 6 |
| Open Tickets | 3 |
| In Progress Tickets | 0 |
| Resolved Tickets | 1 |
| Closed Tickets | 2 |
| Pending Reviews | 3 |
| Approved Reviews | 3 |
| Rejected Reviews | 0 |

### Current Limitations

- The application has a deployed public demo, but it is not a production-ready enterprise system.
- Local workflows were manually tested; a limited pytest suite exists, but comprehensive regression testing is pending.
- Authentication and role-based access control are not yet implemented.
- AI-generated recommendations require human verification before real-world execution.
- AI-suggested incident priority is not automatically applied to the ticket record.