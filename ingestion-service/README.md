# RAG Ingestion Service for Local Deployment

This ingestion service automatically creates and populates vector databases from various sources (GitHub, S3/MinIO, URLs) for local RAG deployments.

## Features

- 🔄 **Automatic Ingestion**: Runs during stack startup to populate vector databases
- 📁 **Multiple Sources**: Support for GitHub repositories, S3/MinIO buckets, and direct URLs
- 📄 **Smart Processing**: Uses Docling for advanced PDF parsing and chunking
- 🔧 **Configuration-Based**: Easy YAML configuration for defining pipelines
- 🚀 **Production Ready**: Proper error handling, logging, and health checks

## Architecture

```
┌─────────────────────┐
│  GitHub / S3 / URL  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Ingestion Service   │
│  • Fetch documents  │
│  • Process with     │
│    Docling          │
│  • Chunk & Embed    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Llama Stack API   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PGVector Database  │
└─────────────────────┘
```

## Configuration

The ingestion service is configured via `ingestion-config.yaml`. Each pipeline defines:

- **name**: Unique identifier for the vector database
- **vector_store_name**: The ID used by Llama Stack
- **source**: Type of source (GITHUB, S3, URL)
- **config**: Source-specific configuration

### Example Configurations

#### GitHub Source

```yaml
hr-pipeline:
  enabled: true
  name: "hr-vector-db"
  version: "1.0"
  vector_store_name: "hr-vector-db-v1-0"
  source: GITHUB
  config:
    url: "https://github.com/rh-ai-quickstart/RAG.git"
    path: "notebooks/hr"
    branch: "main"
    # token: ""  # Optional for private repos
```

#### S3/MinIO Source

```yaml
minio-pipeline:
  enabled: true
  name: "minio-vector-db"
  version: "1.0"
  vector_store_name: "minio-vector-db-v1-0"
  source: S3
  config:
    endpoint: "http://minio:9000"
    bucket: "documents"
    access_key: "minio_rag_user"
    secret_key: "minio_rag_password"
    # prefix: "folder/"  # Optional
```

#### URL Source

**Basic URL Processing:**
```yaml
url-pipeline:
  enabled: true
  name: "url-vector-db"
  version: "1.0"
  vector_store_name: "url-vector-db-v1-0"
  source: URL
  config:
    urls:
      - "https://example.com/document1.pdf"
      - "https://example.com/page.html"
      - "https://example.com/document.docx"
```

**Recursive Web Crawling:**
```yaml
web-crawler-pipeline:
  enabled: true
  name: "crawled-docs-vector-db"
  version: "1.0"
  vector_store_name: "crawled-docs-vector-db-v1-0"
  source: URL
  config:
    urls:
      - "https://docs.company.com/knowledge-base/"  # Root page
    
    # Recursive crawling configuration
    crawl:
      enabled: true              # Enable web crawling
      max_depth: 3               # Crawl 3 levels deep
      same_domain_only: true     # Stay within same domain
      max_pages: 100             # Maximum pages to process
      delay: 1.0                 # Delay between requests (seconds)
```

**Supported Formats:** PDF, HTML, DOCX, PPTX

### Web Crawling Features

The ingestion service includes intelligent web crawling capabilities for comprehensive HTML content extraction:

#### Crawling Configuration Options

- **`enabled`**: Enable/disable recursive crawling (default: false)
- **`max_depth`**: Maximum crawling depth from root URLs (default: 2)
- **`same_domain_only`**: Restrict crawling to same domain (default: true)
- **`max_pages`**: Maximum number of pages to process (default: 50)
- **`delay`**: Delay between requests in seconds (default: 1.0)

#### Crawling Behavior

- **Link Discovery**: Automatically finds and follows `<a>` tags in HTML pages
- **Domain Filtering**: Can restrict crawling to same domain for focused extraction
- **Duplicate Detection**: Prevents processing the same URL multiple times
- **Content Filtering**: Skips non-content files (images, CSS, JavaScript, etc.)
- **Rate Limiting**: Configurable delays to be respectful to target servers

#### Best Practices

1. **Start Small**: Begin with `max_depth: 2` and `max_pages: 25` for testing
2. **Be Respectful**: Use appropriate delays (1-3 seconds) for external sites
3. **Stay Focused**: Use `same_domain_only: true` to avoid crawling the entire web
4. **Monitor Progress**: Watch logs to understand crawling behavior
5. **Internal vs External**: Use faster settings for internal sites, slower for external

#### Example Use Cases

- **Documentation Sites**: Crawl entire product documentation
- **Company Wikis**: Extract all knowledge base articles  
- **Learning Resources**: Process tutorial series and guides
- **Policy Collections**: Gather all company policies and procedures

## Usage

### Quick Start

1. **Edit Configuration**:
   ```bash
   cd deploy/local
   vim ingestion-config.yaml
   ```

2. **Start the Stack**:
   ```bash
   podman-compose up -d
   ```

3. **Watch Ingestion Progress**:
   ```bash
   podman logs -f rag-ingestion
   ```

### Manual Run

If you need to re-run ingestion:

```bash
# Rebuild and run the ingestion service
podman-compose up --build rag-ingestion

# Or run with podman directly
podman run --rm \
  --network rag-network \
  -v $(pwd)/ingestion-config.yaml:/config/ingestion-config.yaml:ro \
  rag-ingestion
```

### Disable Ingestion

To skip automatic ingestion, comment out the service in `podman-compose.yml`:

```yaml
# rag-ingestion:
#   ...
```

## Monitoring

### Check Service Status

```bash
# Check if ingestion completed successfully
podman ps -a | grep rag-ingestion

# View logs
podman logs rag-ingestion
```

### Expected Output

Successful ingestion will show:

```
INFO - Starting RAG Ingestion Service
INFO - Waiting for Llama Stack...
INFO - Llama Stack is ready!
============================================================
Processing pipeline: hr-pipeline
============================================================
INFO - Cloning from GitHub: https://github.com/...
INFO - Found 1 PDF files
INFO - Processing 1 documents with docling...
INFO - Creating vector database: hr-vector-db-v1-0
INFO - ✓ Successfully inserted documents into 'hr-vector-db-v1-0'
============================================================
Ingestion Summary
============================================================
Total pipelines: 5
Successful: 5
Failed: 0
Skipped: 0
============================================================
```

## Troubleshooting

### Service Fails to Start

**Issue**: Ingestion service exits immediately

**Solution**: Check that Llama Stack and PGVector are running:
```bash
podman ps | grep -E "llamastack|pgvector"
```

### GitHub Clone Fails

**Issue**: `fatal: could not read Username`

**Solution**: For private repos, add a GitHub token:
```yaml
config:
  url: "https://github.com/myorg/private-repo.git"
  token: "ghp_yourPersonalAccessToken"
```

### No Documents Found

**Issue**: `No PDF files found for pipeline`

**Solution**: 
- Verify the path exists in the repository
- Ensure documents are in PDF format
- Check branch name is correct

### Vector DB Already Exists

**Issue**: `Vector DB 'xxx' already exists`

**Solution**: This is normal and expected. The service will continue with insertion.

To start fresh:
```bash
# Remove existing vector DBs
podman volume rm pgvector_data
podman-compose up -d
```

### Memory Issues

**Issue**: `Killed` or out of memory errors

**Solution**: 
- Increase container memory limits
- Process fewer documents per pipeline
- Use smaller embedding models

## Advanced Configuration

### Custom Embedding Model

Edit `ingestion-config.yaml`:

```yaml
vector_db:
  embedding_model: "sentence-transformers/all-mpnet-base-v2"
  embedding_dimension: 768
```

### Chunk Size Tuning

Adjust chunk size for different document types:

```yaml
vector_db:
  chunk_size_in_tokens: 256  # Smaller chunks
  # or
  chunk_size_in_tokens: 1024  # Larger chunks
```

### Retry Configuration

For unreliable networks, adjust wait times in the code:

```python
def wait_for_llamastack(self, max_retries: int = 60, retry_delay: int = 10):
```

## Development

### Building the Image

```bash
cd ingestion-service
podman build -t rag-ingestion -f Containerfile .
```

### Running Locally

For development without containers:

```bash
cd ingestion-service

# Install dependencies
pip install -r requirements.txt

# Set environment
export INGESTION_CONFIG="../deploy/local/ingestion-config.yaml"

# Run
python ingest.py
```

### Testing with Mock Data

Create a test configuration with URL sources:

```yaml
test-pipeline:
  enabled: true
  name: "test-db"
  vector_store_name: "test-db-v1-0"
  source: URL
  config:
    urls:
      - "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
```

## Integration with UI

The ingested vector databases will automatically appear in the RAG UI's database selector. Make sure the `vector_store_name` in `ingestion-config.yaml` matches the keys in your suggested questions configuration.

### Synchronizing Suggestions

In `ingestion-config.yaml`:
```yaml
vector_store_name: "hr-vector-db-v1-0"
```

In `podman-compose.yml` (rag-ui environment):
```yaml
RAG_QUESTION_SUGGESTIONS: |
  {
    "hr-vector-db-v1-0": [
      "What are the health benefits?",
      ...
    ]
  }
```

## Performance

### Ingestion Times

Typical ingestion times (single pipeline):

- **Small** (1-5 PDFs, <10MB): 1-2 minutes
- **Medium** (5-20 PDFs, 10-50MB): 3-5 minutes
- **Large** (20+ PDFs, >50MB): 5-15 minutes

Times depend on:
- Document size and complexity
- Network speed (for downloads)
- Available CPU/Memory
- Embedding model complexity

### Optimization Tips

1. **Parallel Pipelines**: Enable only needed pipelines
2. **Network**: Use local sources when possible
3. **Caching**: Keep source files in volumes for re-ingestion
4. **Resources**: Allocate adequate memory to containers

## Security Considerations

### Secrets Management

Never commit tokens or credentials. Use environment variables:

```yaml
config:
  token: "${GITHUB_TOKEN}"
  secret_key: "${MINIO_SECRET_KEY}"
```

Set in shell before running:
```bash
export GITHUB_TOKEN="ghp_xxx"
export MINIO_SECRET_KEY="xxx"
podman-compose up
```

### Private Repositories

For GitHub private repos:
1. Generate a Personal Access Token with `repo` scope
2. Add to configuration or environment
3. Use HTTPS URLs (not SSH)

## FAQ

**Q: Can I add documents after initial ingestion?**

A: Yes, re-run the ingestion service or use the UI upload feature.

**Q: How do I delete a vector database?**

A: Use the Llama Stack API or recreate the pgvector volume.

**Q: Can I ingest from local files?**

A: Mount a volume and use URL source with `file://` paths.

**Q: What document formats are supported?**

A: Currently PDF only. Docling supports others but requires code changes.

**Q: Can I customize chunking strategy?**

A: Yes, modify the `HybridChunker` parameters in `ingest.py`.

**Q: How does web crawling work?**

A: When enabled, the crawler starts from root URLs, extracts all links, and recursively processes linked pages up to the configured depth and page limits.

**Q: Why is crawling slow?**

A: Crawling includes deliberate delays to be respectful to target servers. Adjust the `delay` setting, but be mindful of server load.

**Q: Crawler isn't finding pages I expect?**

A: Check that links use `<a>` tags with `href` attributes. The crawler follows HTML links, not JavaScript-generated content.

**Q: Can I crawl password-protected sites?**

A: Not directly. The crawler uses basic HTTP requests without authentication. Consider downloading content first or extending the crawler for your auth method.

## Support

For issues and questions:
- Check logs: `podman logs rag-ingestion`
- Review configuration syntax in `ingestion-config.yaml`
- Ensure all services are healthy: `podman ps`
- Check network connectivity to sources

## License

This ingestion service is part of the Red Hat RAG Blueprint project.

