
# Enterprise AI IT Support Copilot â€” Interview Preparation

## 1. Explain your project architecture.

**Answer:**

I developed an Enterprise AI IT Support Copilot with a JavaScript frontend and a Python FastAPI backend.

The local development architecture uses Ollama for LLM inference and embeddings, with ChromaDB for vector-based knowledge retrieval.

The deployed cloud version runs on Render with a static frontend hosted on Hugging Face Spaces. It uses Groq for AI answer generation, SQLite for ticket data and keyword-based knowledge retrieval, and bundled Markdown IT runbooks for document-grounded troubleshooting.

The system supports AI troubleshooting, ticket workflows, a dashboard, and knowledge-based question answering with source references.

**Key distinction:** The deployed cloud RAG uses keyword retrieval, not vector embeddings.

## 2. What is Retrieval-Augmented Generation (RAG), and why did you use it?

**Answer:**

RAG is a technique that retrieves relevant information from a knowledge source and supplies it to a language model before generating an answer.

I used RAG to make IT troubleshooting responses more relevant to documented procedures instead of relying only on the language model's general knowledge. The application also displays source references so users can identify which knowledge article was used.

## 3. How does your cloud RAG pipeline work?

**Answer:**

When a user submits a Knowledge Base question, the frontend sends it to the FastAPI `/rag/chat` endpoint.

The backend searches indexed knowledge chunks in SQLite using keyword matching. Relevant excerpts are provided to the Groq-hosted language model as context. The backend returns the generated answer and source references, which the frontend displays.

The cloud implementation does not currently use vector embeddings.

## 4. Why did you use Groq instead of Ollama in the cloud?

**Answer:**

Ollama is useful for running language models locally, but it requires local model execution and sufficient computing resources.

For the free cloud demo, I used Groq-hosted inference to avoid hosting a large language model on Render. This keeps the deployed FastAPI application lightweight.

## 5. What is the role of FastAPI in your project?

**Answer:**

FastAPI provides the backend API layer. It receives requests from the frontend, handles AI chat and knowledge-based questions, manages ticket operations, and returns structured responses.

It also provides endpoints for health checks and applies public-demo access restrictions.

## 6. Why did you use SQLite?

**Answer:**

SQLite is lightweight, requires no separate database server, and is suitable for a small portfolio demonstration.

In the cloud implementation, it stores ticket data and indexed knowledge chunks. The knowledge retrieval workflow uses keyword matching.

For production, I would consider a managed persistent database because the Render Free filesystem is ephemeral.

## 7. What is ChromaDB, and where is it used?

**Answer:**

ChromaDB is a vector database that stores embeddings and supports similarity-based retrieval.

My local RAG architecture uses Ollama embeddings and ChromaDB. The deployed cloud RAG uses SQLite keyword retrieval instead.

This distinction is important because the cloud implementation should not be described as vector-based RAG.

## 8. How are knowledge documents indexed?

**Answer:**

The deployed backend includes a version-controlled Markdown IT troubleshooting runbook.

When FastAPI starts, the knowledge-seeding process loads the bundled document, splits it into searchable chunks, and stores them in SQLite.

The indexing logic is designed to avoid duplicating unchanged content and replace outdated versions when the bundled document changes.

## 9. How does the application provide source references?

**Answer:**

The cloud RAG API returns source metadata with the answer, including the document filename and page reference.

The frontend displays these references in the Knowledge Base interface and removes duplicate references from the displayed source list.

Source references improve traceability, although they do not guarantee that every generated statement is correct.

## 10. How are IT tickets managed?

**Answer:**

The application provides ticket-related backend APIs and a frontend interface for working with IT support tickets.

Ticket information is stored in SQLite, and the dashboard presents ticket-related information.

The public cloud demo restricts ticket mutations, so visitors cannot freely modify the demonstration data.

## 11. What security controls have you implemented?

**Answer:**

The cloud application includes a public-demo mode that restricts administrative operations, including document uploads and ticket mutations.

AI chat endpoints are rate-limited to reduce abuse. The Groq API key is configured on the backend rather than exposed in frontend JavaScript.

These controls are appropriate for a portfolio demonstration, but they are not a substitute for production authentication, authorization, and security monitoring.

## 12. How did you test the backend?

**Answer:**

I used automated backend tests to validate important application behavior.

The verified test suite has nine passing tests, including checks for cloud knowledge seeding, document version handling, and public-demo access restrictions.

I also manually verified the deployed API and the frontend Knowledge Base question-answering workflow.

## 13. How did you deploy the project?

**Answer:**

I deployed the FastAPI backend on Render Free and the static HTML, CSS, and JavaScript frontend on Hugging Face Spaces.

The frontend sends API requests to the Render backend. The backend communicates with Groq for language-model inference.

Bundled Markdown knowledge is indexed at startup so the cloud RAG workflow can operate after a service restart.

## 14. What are the current limitations?

**Answer:**

The main limitations are:

- Cloud RAG uses keyword matching rather than semantic vector search.
- Render Free storage is ephemeral, so SQLite data is not guaranteed to persist across redeployments.
- The public demo does not implement production-grade authentication or role-based access control.
- Generated AI responses can still contain errors and should be reviewed for accuracy.
- The deployment is designed for portfolio demonstration rather than enterprise-scale traffic.

## 15. How would you scale this system for production?

**Answer:**

I would replace ephemeral SQLite storage with a managed persistent database such as PostgreSQL.

I would add enterprise authentication, role-based authorization, audit logging, and stronger monitoring.

For knowledge retrieval, I would evaluate embeddings, a vector database, hybrid
