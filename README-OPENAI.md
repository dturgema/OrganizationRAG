# 🚀 Run RAG on Your PC with OpenAI

This guide shows you how to run the RAG system on your PC using OpenAI instead of local models. No GPU required!

## ✨ Benefits of Using OpenAI

- **💻 PC-Friendly**: No GPU or high-end hardware required
- **⚡ Fast Setup**: No model downloads, instant startup  
- **🧠 Smart Models**: GPT-4o-mini for chat, latest embedding models
- **💰 Cost-Effective**: ~$1-5/month for typical personal use
- **🔄 Always Updated**: Latest OpenAI models automatically

## 🎯 Quick Start (2 Minutes!)

### **1. Get OpenAI API Key**
- Go to https://platform.openai.com/api-keys
- Create new API key
- Copy the key (starts with `sk-...`)

### **2. Run the Setup Script**
```bash
./start-rag-openai.sh
```

The script will:
- ✅ Set up environment file  
- ✅ Guide you through API key setup
- ✅ Start all services with Docker
- ✅ Open the RAG UI in your browser

### **3. Use Your RAG System**
- 🌐 Open http://localhost:8501
- 📄 Upload documents or configure URLs
- 💬 Start asking questions!

## 📋 Manual Setup (Alternative)

If you prefer manual setup:

### **1. Configure Environment**
```bash
# Copy environment template
cp .env.openai .env

# Edit with your API key
nano .env
# Replace: OPENAI_API_KEY=sk-your-openai-api-key-here
```

### **2. Start Services**
```bash
# Start the RAG system
docker-compose -f docker-compose-openai.yml up -d

# Wait for startup (~30 seconds)
```

### **3. Add Documents**
```bash
# Option A: Use web UI at http://localhost:8501

# Option B: Configure URLs and run ingestion
docker-compose -f docker-compose-openai.yml run --rm rag-ingestion
```

## 🔧 Configuration Options

### **OpenAI Models**

Edit `.env` file:

```bash
# Fast & Cheap (Recommended)
INFERENCE_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Higher Quality (More Expensive)  
INFERENCE_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large

# Budget Option
INFERENCE_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small
```

### **Document Sources**

Edit `ingestion-config-pc-openai.yaml`:

```yaml
pipelines:
  web-docs:
    config:
      urls:
        - "https://your-docs-site.com"
        - "https://another-site.com/docs"
      crawl:
        max_pages: 100  # Adjust based on site size
        
  confluence-docs:
    config:
      urls:
        - "https://company.atlassian.net/wiki/spaces/TEAM/overview"
```

## 💰 Cost Estimates

Based on OpenAI pricing (as of 2024):

### **Typical Monthly Usage**
- **Small Personal Docs** (~1000 pages): $1-2/month
- **Company Documentation** (~5000 pages): $3-5/month  
- **Large Knowledge Base** (~10000 pages): $8-12/month

### **Per Operation**
- **Document Ingestion**: ~$0.02 per 1000 pages
- **Chat Queries**: ~$0.001-0.005 per question
- **Embeddings**: ~$0.02 per million tokens

### **Model Comparison**
| Model | Input Cost | Output Cost | Use Case |
|-------|------------|-------------|----------|
| gpt-4o-mini | $0.15/1M | $0.60/1M | Recommended (fast + cheap) |
| gpt-4o | $5.00/1M | $15.00/1M | High-quality responses |
| gpt-3.5-turbo | $0.50/1M | $1.50/1M | Budget option |

## 🧪 Testing Your Setup

### **Check Services**
```bash
# Check if services are running
docker-compose -f docker-compose-openai.yml ps

# View logs
docker-compose -f docker-compose-openai.yml logs llamastack

# Test API connection
curl http://localhost:8321/health
```

### **Test with Sample Data**
```bash
# Enable web docs pipeline
# Edit ingestion-config-pc-openai.yaml, set web-docs enabled: true

# Run ingestion
docker-compose -f docker-compose-openai.yml run --rm rag-ingestion

# Check UI at http://localhost:8501
```

## 🏢 Advanced Features

### **Confluence Integration**
1. Get Confluence API token: https://id.atlassian.com/manage-profile/security/api-tokens
2. Add to `.env`:
   ```bash
   CONFLUENCE_BASE_URL=https://company.atlassian.net
   CONFLUENCE_USERNAME=your-email@company.com
   CONFLUENCE_API_TOKEN=your-token
   ```
3. Enable confluence pipelines in config
4. Run ingestion

### **GitHub Integration**
```yaml
pipelines:
  github-docs:
    enabled: true
    source: GITHUB
    config:
      GITHUB:
        url: "https://github.com/username/repo.git"
        path: "docs"
        token: "${GITHUB_TOKEN}"  # For private repos
```

### **Custom Web Crawling**
```yaml
config:
  urls:
    - "https://your-site.com"
  crawl:
    enabled: true
    max_depth: 3
    max_pages: 500
    delay: 1.0
```

## 🛟 Troubleshooting

### **Common Issues**

**"OpenAI API Error"**
- Check API key is correct in `.env`
- Verify you have credits in your OpenAI account
- Check API key permissions

**"Services not starting"**
- Ensure Docker Desktop is running
- Check ports 8321, 8501, 5432 aren't in use
- Try: `docker-compose -f docker-compose-openai.yml down && docker-compose -f docker-compose-openai.yml up`

**"No documents found"**
- Check ingestion configuration is enabled
- Verify URLs are accessible
- Check logs: `docker-compose -f docker-compose-openai.yml logs rag-ingestion`

**"High OpenAI costs"**
- Use `gpt-4o-mini` instead of `gpt-4o`
- Reduce `max_pages` in crawling config
- Use `text-embedding-3-small` for embeddings

### **Performance Tuning**

**For Large Document Sets**
```yaml
# In ingestion config
vector_db:
  chunk_size_in_tokens: 256  # Smaller chunks = more embeddings cost
  
crawl:
  max_pages: 100        # Limit pages per site
  delay: 2.0           # Slower crawling
```

**For Cost Optimization**
```bash
# In .env
INFERENCE_MODEL=gpt-4o-mini          # Cheaper chat model
EMBEDDING_MODEL=text-embedding-3-small  # Cheaper embeddings
```

## 🎛️ Management Commands

```bash
# Start services
./start-rag-openai.sh

# Stop services  
docker-compose -f docker-compose-openai.yml down

# View logs
docker-compose -f docker-compose-openai.yml logs -f

# Run ingestion
docker-compose -f docker-compose-openai.yml run --rm rag-ingestion

# Update ingestion config
docker-compose -f docker-compose-openai.yml restart rag-ingestion

# Clean up everything
docker-compose -f docker-compose-openai.yml down -v
docker system prune -f
```

## ✨ Why This is Great for PC Use

### **✅ Advantages Over Local Setup**
- **No GPU Required**: Runs on any modern PC
- **Instant Startup**: No model downloads (GBs)
- **Latest Models**: Always uses newest OpenAI models
- **Consistent Performance**: No hardware limitations
- **Easy Updates**: Just restart containers

### **🎯 Perfect For**
- **Personal Knowledge Base**: Organize your documents
- **Small Teams**: Share company documentation  
- **Learning**: Experiment with RAG without hardware costs
- **Development**: Build RAG applications quickly

### **📊 Resource Usage**
- **RAM**: ~1-2GB (vs 8GB+ for local models)
- **CPU**: Minimal (just Docker containers)
- **Storage**: ~5GB (vs 20GB+ for local models)
- **Network**: API calls only (no model downloads)

---

🚀 **Ready to start?** Run `./start-rag-openai.sh` and you'll have a powerful RAG system running in minutes!

💬 **Questions?** Check the troubleshooting section above or the main README.md for more details.

✨ **Enjoy your AI-powered document chat system!** 🤖📚