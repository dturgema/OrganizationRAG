# MFS RAG System - Complete Implementation

## 🎯 Overview

This is a production-ready RAG (Retrieval-Augmented Generation) system specifically designed for MFS (Manufacturing & Configuration System) documentation. The system provides intelligent question-answering capabilities for:

- Order validation and status management
- Configuration workflows and business rules  
- Inventory management and item validation
- System architecture and integrations

## 🚀 Quick Start

### 1. Environment Setup

Create/update your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
INFERENCE_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-ada-002

# Confluence Authentication (optional but recommended)
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# Database (automatically configured in Docker)
POSTGRES_HOST=rag-pgvector-openai
POSTGRES_PORT=5432
POSTGRES_DB=ragdb
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpassword
```

### 2. Start the System

```bash
# Start RAG system with PostgreSQL and Streamlit UI
docker-compose -f docker-compose-openai-working.yml up -d

# Check status
docker-compose -f docker-compose-openai-working.yml ps
```

### 3. Ingest Your MFS Content

Choose one of these ingestion methods:

**Option A: Docling-Enhanced (Recommended)**
```bash
# Advanced document structure analysis
docker run --rm \
  -v $(pwd)/ingest_docling_simple.py:/app/ingest_docling_simple.py:ro \
  --env-file .env \
  --network rag_rag-network \
  python:3.12-slim \
  sh -c "
  pip install --quiet psycopg2-binary requests beautifulsoup4 lxml docling &&
  python /app/ingest_docling_simple.py
  "
```

**Option B: Standard Ingestion**  
```bash
# Basic but reliable ingestion
export $(grep -v '^#' .env | xargs) && python3 ingest_standalone_fixed.py
```

### 4. Use the RAG System

Open your browser to: **http://localhost:8501**

## 📋 Core Components

### 🔬 Document Processing
- **`ingest_docling_simple.py`** - Docling-enhanced ingestion with structured table extraction
- **`ingest_standalone_fixed.py`** - Reliable standalone ingestion with direct API calls
- **`ingest_standalone.py`** - Basic ingestion for MFS pages and whiteboards

### 🖥️ User Interface  
- **`rag_app.py`** - Production Streamlit UI with OpenAI integration
- **`docker-compose-openai-working.yml`** - Complete Docker setup

## 🎯 System Capabilities

### ✅ What the System Can Do:
- **Intelligent Q&A** about MFS configuration processes
- **Order validation** rules and status checking
- **Business logic** extraction from Confluence whiteboards  
- **Structured data** processing (tables, workflows, diagrams)
- **Multi-document search** with similarity scoring
- **Confluence integration** with authentication support

### 💬 Example Questions:
- "What are the valid order status values?"
- "Does the retrieve configuration options whiteboard check if an order exists?"
- "How does the MFS configuration validation work?"
- "What business rules exist for inventory management?"
- "Show me the order processing workflow"

## 🔧 Advanced Features

### Docling Integration
The system uses IBM's Docling for advanced document analysis:
- **Table extraction** - Converts HTML tables to structured markdown
- **Layout preservation** - Maintains document hierarchy and formatting  
- **Content enhancement** - Improves raw text with proper structure

### Confluence Authentication
Supports private Confluence spaces:
- Uses Confluence username/API token authentication
- Handles modern Confluence pages with JavaScript content
- Fallback to web scraping when API access is limited

### Vector Search
Powered by PostgreSQL + PGVector:
- **Semantic search** using OpenAI embeddings
- **Similarity scoring** for result ranking
- **Efficient indexing** for fast retrieval

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Streamlit UI   │    │  PostgreSQL +    │    │  OpenAI API     │
│  (rag_app.py)   │◄──►│  PGVector        │◄──►│  GPT-4o-mini    │
│  Port: 8501     │    │  Port: 5432      │    │  Embeddings     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                       ▲
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│               Docker Network (rag_rag-network)                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Check container status
docker-compose -f docker-compose-openai-working.yml ps

# View logs
docker-compose -f docker-compose-openai-working.yml logs pgvector
docker-compose -f docker-compose-openai-working.yml logs rag-ui
```

### Ingestion Problems
```bash
# Test database connectivity
docker run --rm --env-file .env --network rag_rag-network python:3.12-slim \
  sh -c "pip install psycopg2-binary && python -c 'import psycopg2; print(\"DB OK\")"

# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models | jq '.data[0].id'
```

### Confluence Access Issues  
- Verify your API token is active: https://id.atlassian.com/manage-profile/security/api-tokens
- Check if your pages are publicly accessible
- Ensure correct base URL format

## 📊 System Status

Check the Streamlit sidebar for real-time status:
- ✅ Database connection and document count
- ✅ OpenAI API connectivity  
- 📋 Sample questions for testing

## 🎉 Success Indicators

When working correctly, you should see:
- Streamlit UI accessible at localhost:8501
- Database with 30+ comprehensive MFS documents
- Specific, detailed answers to MFS configuration questions
- No "context does not contain" generic responses

---

**Your MFS RAG system is production-ready and optimized for comprehensive MFS knowledge assistance!**