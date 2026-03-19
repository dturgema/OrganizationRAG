# MFS RAG System Troubleshooting Guide

## 🚨 Common Issues and Fixes

### ❌ "Invalid Model ID" Error

**Symptoms:**
- RAG queries return no results
- Error: `Error code: 400 - {'error': {'message': 'invalid model ID'}}`
- Both simple and complex queries fail

**Root Cause:**
Inline comments in `.env` file break environment variables.

**❌ Problematic `.env` format:**
```bash
EMBEDDING_MODEL=text-embedding-ada-002   # Most compatible model
INFERENCE_MODEL=gpt-4o-mini              # Cheap and fast for chat
```

**✅ Correct `.env` format:**
```bash
EMBEDDING_MODEL=text-embedding-ada-002
INFERENCE_MODEL=gpt-4o-mini
```

**Fix:**
1. Edit your `.env` file
2. Remove all inline comments (everything after `#` on the same line)
3. Restart your RAG services: `docker-compose -f docker-compose-openai-working.yml restart`

---

### ❌ Queries Only Work with Exact Terminology

**Symptoms:**
- `"explain the product configurator flow"` returns no results
- `"explain the product configurator flow of events"` works fine
- Similar semantic queries have very different results

**Root Cause:**
Usually the "Invalid Model ID" issue above (environment variables broken).

**Diagnosis:**
Run the diagnostic script:
```bash
docker run --rm --env-file .env --network rag_rag-network python:3.12-slim sh -c "
pip install --quiet openai psycopg2-binary requests &&
python -c 'import os; import openai; print(f\"Model: {os.getenv(\"EMBEDDING_MODEL\")}\"); openai.OpenAI(api_key=os.getenv(\"OPENAI_API_KEY\")).embeddings.create(model=os.getenv(\"EMBEDDING_MODEL\"), input=\"test\")'
"
```

---

### ❌ RAG Returns "No Context Found"

**Symptoms:**
- RAG UI loads but queries return generic "no information found" responses
- Database connection works but search returns empty

**Common Causes:**
1. **No documents ingested**: Run `python master_ingest.py`
2. **Embedding model mismatch**: Check `EMBEDDING_MODEL` in `.env`
3. **Database connection issues**: Verify PostgreSQL container is running

**Diagnosis:**
```bash
# Check if documents exist
docker run --rm --env-file .env --network rag_rag-network python:3.12-slim sh -c "
pip install --quiet psycopg2-binary &&
python -c 'import psycopg2; conn=psycopg2.connect(host=\"rag-pgvector-openai\", port=5432, database=\"ragdb\", user=\"raguser\", password=\"ragpassword\"); cursor=conn.cursor(); cursor.execute(\"SELECT COUNT(*) FROM documents\"); print(f\"Documents in database: {cursor.fetchone()[0]}\"); conn.close()'
"
```

---

### ❌ Docker Services Won't Start

**Symptoms:**
- `dependency failed to start: container ... is unhealthy`
- PostgreSQL connection refused
- RAG UI shows "connection failed"

**Fix:**
```bash
# Stop everything
docker-compose -f docker-compose-openai-working.yml down

# Clean up
docker system prune -f

# Restart fresh
docker-compose -f docker-compose-openai-working.yml up -d

# Check status
docker-compose -f docker-compose-openai-working.yml ps
```

---

## 🔧 Diagnostic Tools

### Quick Environment Test
```bash
# Test OpenAI connection
export $(grep -v '^#' .env | xargs) && python -c "
import openai
client = openai.OpenAI()
result = client.embeddings.create(model='text-embedding-ada-002', input='test')
print('✅ OpenAI connection works!')
"
```

### Database Connection Test
```bash
# Test PostgreSQL connection  
export $(grep -v '^#' .env | xargs) && python -c "
import psycopg2
conn = psycopg2.connect(host='rag-pgvector-openai', port=5432, database='ragdb', user='raguser', password='ragpassword')
print('✅ Database connection works!')
conn.close()
"
```

### Full RAG System Test
```bash
# Run comprehensive test
python debug_rag_search.py
```

---

## 🆘 Still Having Issues?

1. **Check Docker logs**: `docker logs rag-ui-openai`
2. **Verify environment**: `cat .env | grep -v "API_KEY"`
3. **Test with diagnostic scripts**: `python debug_rag_search.py`
4. **Restart everything**: `docker-compose -f docker-compose-openai-working.yml restart`

## ✅ Working System Checklist

- [ ] `.env` file has no inline comments
- [ ] OpenAI API key is valid
- [ ] PostgreSQL container is running and healthy
- [ ] Documents are ingested (run `master_ingest.py`)
- [ ] Both `"flow"` and `"flow of events"` queries return results
- [ ] RAG UI accessible at http://localhost:8501