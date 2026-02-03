# Agentic RAG Chatbot

An advanced Retrieval-Augmented Generation (RAG) system built with an Agentic Architecture. This project uses the **Model Context Protocol (MCP)** to orchestrate multiple AI agents for document ingestion, retrieval, and response generation.

## 📂 Project Structure

```bash
RAG-PROJECT/
├── backend/                  # Python FastAPI Backend
│   ├── agents/               # AI Agents (Ingestion, Retrieval, Response, Coordinator)
│   ├── mcp/                  # Model Context Protocol implementation
│   ├── main.py               # API Entry point
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment keys (GROQ_API_KEY)
├── frontend/                 # Static Frontend
│   ├── index.html            # Premium UI Layout
│   ├── app.js                # Chat logic & File Uploads
│   └── style.css             # Animations & Tailwind config
├── chroma_db/                # Local Vector Store (Auto-generated/Deleted on restart)
├── Agentic_RAG_Architecture.pptx # Architecture Presentation Slides
├── verify_rag.py             # Automated System Verification Script
└── create_ppt.py             # Script to regenerate the presentation
```

## 🚀 Key Features

-   **Multi-Agent System**:
    -   `IngestionAgent`: Parses PDF, DOCX, PPTX, CSV, TXT.
    -   `RetrievalAgent`: Manages Vector DB (ChromaDB) and Semantic Search.
    -   `LLMResponseAgent`: Generates answers using Groq (Llama3-70b).
    -   `CoordinatorAgent`: Orchestrates the workflow via MCP.
-   **Premium UI**: Glassmorphism design, real-time typing indicators, and drag-and-drop uploads.
-   **Model Context Protocol (MCP)**: Standardized message passing for robust agent communication.
-   **Auto-Cleanup**: Automatically resets the knowledge base (DB) on every server restart.

## 🛠️ Setup & Installation

1.  **Prerequisites**: Python 3.10 or higher.
2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    venv\Scripts\activate   # Windows
    # source venv/bin/activate # Mac/Linux
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  **Environment Variables**:
    Ensure `backend/.env` exists and contains your API key:
    ```
    GROQ_API_KEY=your_key_here
    ```

## ▶️ How to Run

1.  **Start the Server**:
    ```bash
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
    ```
    *Note: The server will automatically clear the old database on startup.*

2.  **Access the Application**:
    Open your browser and go to: `http://localhost:8000`

3.  **Verify System**:
    Run the included test script to verify backend connectivity and RAG flow:
    ```bash
    python verify_rag.py
    ```

## 🧠 Architecture Overview

The system follows a strictly agentic flow:

1.  **User** uploads a file -> **Coordinator** sends to **IngestionAgent**.
2.  **IngestionAgent** chunks text -> **RetrievalAgent** embeds & stores in ChromaDB.
3.  **User** asks a question -> **Coordinator** requests context from **RetrievalAgent**.
4.  **RetrievalAgent** returns semantic matches -> **Coordinator** sends context + query to **LLMResponseAgent**.
5.  **LLMResponseAgent** generates a cited answer -> Returned to User.

## 📄 Deliverables

-   **Source Code**: Full backend/frontend implementation.
-   **Presentation**: `Agentic_RAG_Architecture.pptx` (Included in root).
-   **Documentation**: This README.md.
