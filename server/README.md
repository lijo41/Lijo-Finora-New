# Finora Backend

Agentic backend for document processing and GSTR-1 filing using Google ADK, Docling, and AI APIs.

## Features

- **Document Processing**: Upload documents via file or URL, parsed with Docling
- **Semantic Search**: Find relevant document chunks using vector embeddings
- **AI Chat**: Chat with documents using Google Gemini or Groq APIs
- **GSTR-1 Filing**: Extract structured GST data and generate filing reports

## Setup

1. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -e .
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run server:
```bash
uvicorn main:app --reload
```

## API Endpoints

- `POST /api/upload_document` - Upload document file
- `POST /api/upload_document_url` - Upload document from URL
- `POST /api/search_documents` - Search documents
- `POST /api/chat_with_documents` - Chat with documents
- `GET /api/get_document_chunks` - Get document chunks
- `POST /api/process_gstr1_chunks` - Process chunks for GSTR-1
- `POST /api/generate_gstr1_summary` - Generate GSTR-1 summary
- `GET /api/get_server_status` - Get server status
- `POST /api/clear_database` - Clear database

## Architecture

The backend uses an agentic architecture with specialized agents:

- **DocumentAgent**: Handles document parsing and chunking with Docling
- **SearchAgent**: Provides semantic search functionality
- **ChatAgent**: Enables AI-powered chat with documents
- **GSTR1Agent**: Extracts and processes GSTR-1 data
- **OrchestratorAgent**: Coordinates all agents and tasks
