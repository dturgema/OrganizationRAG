# Confluence Integration Guide

The enhanced RAG system now supports seamless integration with **Atlassian Confluence**, allowing you to crawl and process Confluence spaces, pages, and documents alongside regular web content.

## 🎯 What This Enables

- **🔗 Mixed Content Processing**: Combine Confluence pages with regular documentation sites
- **📚 Space-Wide Crawling**: Automatically discover and process entire Confluence spaces  
- **🔄 API-Based Access**: Use Confluence REST APIs for reliable content extraction
- **🛡️ Authentication Support**: Multiple authentication methods for secure access
- **📄 Rich Content Extraction**: Convert Confluence storage format to clean text

## 🚀 Quick Start

### 1. Basic Confluence + Web Crawling

```yaml
pipelines:
  mixed-confluence-docs:
    enabled: true
    source: URL
    config:
      urls:
        - "https://docs.company.com/guide/"              # Regular docs
        - "https://company.atlassian.net/wiki/spaces/ENG/overview"  # Confluence space
      
      crawl:
        enabled: true
        confluence:
          base_url: "https://company.atlassian.net"
          username: "your-email@company.com"
          api_token: "${CONFLUENCE_API_TOKEN}"
```

### 2. Environment Setup

```bash
# Set your Confluence API token
export CONFLUENCE_API_TOKEN="your-atlassian-api-token"

# Run ingestion
docker run --rm \
  -v $(pwd)/config.yaml:/config/ingestion-config.yaml:ro \
  -e CONFLUENCE_API_TOKEN="$CONFLUENCE_API_TOKEN" \
  rag-ingestion-enhanced:production
```

## 🔐 Authentication Methods

### Option 1: API Token (Recommended for Atlassian Cloud)

**Setup:**
1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create new API token
3. Use your email + API token

**Configuration:**
```yaml
confluence:
  base_url: "https://yourcompany.atlassian.net"
  username: "your-email@company.com"
  api_token: "${CONFLUENCE_API_TOKEN}"
```

### Option 2: Personal Access Token (Server/Data Center)

**Setup:**
1. Go to Confluence → Settings → Personal Access Tokens
2. Create token with read permissions
3. Use token directly

**Configuration:**
```yaml
confluence:
  base_url: "https://confluence.company.com"
  token: "${CONFLUENCE_PAT}"
```

### Option 3: Basic Authentication (Legacy)

**Configuration:**
```yaml
confluence:
  base_url: "https://confluence.company.com"
  username: "your-username"  
  password: "${CONFLUENCE_PASSWORD}"
```

## 📋 Supported URL Formats

The system automatically detects and processes various Confluence URL formats:

### Space URLs
```
https://company.atlassian.net/wiki/spaces/ENG/overview
https://company.atlassian.net/wiki/spaces/HR/pages/
```

### Specific Page URLs
```
# Modern format
https://company.atlassian.net/wiki/spaces/ENG/pages/123456/Development+Guidelines

# Display format  
https://company.atlassian.net/wiki/display/ENG/Development+Guidelines

# Direct page ID
https://company.atlassian.net/wiki/pages/viewpage.action?pageId=123456
```

## ⚙️ Configuration Options

### Crawling Configuration

```yaml
crawl:
  enabled: true
  max_depth: 3              # How deep to crawl
  same_domain_only: false   # Allow multiple domains (Confluence + docs sites)
  max_pages: 150           # Confluence pages can be numerous
  delay: 2.0               # Be respectful to Confluence servers
  
  confluence:
    base_url: "https://company.atlassian.net"
    username: "service-account@company.com"
    api_token: "${CONFLUENCE_TOKEN}"
```

### Advanced Options

```yaml
confluence:
  base_url: "https://company.atlassian.net"
  username: "user@company.com"
  api_token: "${TOKEN}"
  
  # Optional: Limit space processing
  spaces:
    - "ENG"     # Engineering space
    - "PROD"    # Product space
    - "SUPPORT" # Support space
  
  # Optional: Page filtering  
  include_patterns:
    - "*guideline*"
    - "*process*"
  exclude_patterns:
    - "*draft*"
    - "*template*"
```

## 🔄 How It Works

### 1. URL Detection
The system automatically detects Confluence URLs during crawling:
```python
# Detected patterns:
- '/wiki/' in URL
- '/display/' in URL  
- '/spaces/' in URL
- 'atlassian.net' in domain
- 'confluence' in domain
```

### 2. API-Based Content Extraction
Instead of scraping HTML, the system uses Confluence REST APIs:
```
GET /rest/api/content/{pageId}?expand=body.storage,space,version
```

### 3. Content Processing
- **Storage Format Conversion**: Confluence XML → Clean text
- **Metadata Extraction**: Title, space, URL, version info
- **Intelligent Chunking**: Optimized for RAG retrieval

### 4. Link Discovery
From Confluence pages, the system can discover:
- **Related pages** in the same space
- **Cross-space links** (if crawling allows)
- **External links** to documentation sites

## 📊 Content Processing Flow

```
🔗 Confluence URL → 🔑 API Authentication → 📄 Fetch Page Content
                ↓
📝 Convert Storage Format → ✂️ Chunk Text → 🔢 Create Embeddings
                ↓
🗄️ Store in Vector Database ← 🏷️ Add Metadata ← 🔍 Extract Links
```

## 🎛️ Usage Examples

### Company Knowledge Base
```yaml
company-kb-pipeline:
  source: URL
  config:
    urls:
      - "https://company.atlassian.net/wiki/spaces/HR/overview"
      - "https://company.atlassian.net/wiki/spaces/ENG/overview"  
      - "https://docs.company.com/policies/"
    
    crawl:
      enabled: true
      max_depth: 4
      max_pages: 200
      confluence:
        base_url: "https://company.atlassian.net"
        username: "kb-service@company.com"
        api_token: "${KB_CONFLUENCE_TOKEN}"
```

### Product Documentation Mix
```yaml
product-docs-pipeline:
  source: URL
  config:
    urls:
      - "https://docs.product.com/api/"                    # API docs
      - "https://product.atlassian.net/wiki/spaces/PROD/overview"  # Internal specs
      - "https://support.product.com/kb/"                 # Support KB
    
    crawl:
      enabled: true
      same_domain_only: false  # Allow multiple domains
      confluence:
        base_url: "https://product.atlassian.net"
        token: "${PRODUCT_CONFLUENCE_PAT}"
```

### Engineering Documentation
```yaml
eng-docs-pipeline:
  source: URL
  config:
    urls:
      - "https://eng.company.net/wiki/spaces/ARCH/overview"  # Architecture
      - "https://eng.company.net/wiki/spaces/API/overview"   # API specs
      - "https://github.com/company/docs"                    # GitHub docs
    
    crawl:
      enabled: true
      max_depth: 5  # Deep crawling for comprehensive coverage
      confluence:
        base_url: "https://eng.company.net"
        username: "engineering-bot@company.com"
        api_token: "${ENG_CONFLUENCE_TOKEN}"
```

## 🔧 Docker Integration

The enhanced Docker containers automatically include Confluence support:

### Using Enhanced Container
```bash
docker run --rm \
  -v $(pwd)/confluence-config.yaml:/config/ingestion-config.yaml:ro \
  -e CONFLUENCE_API_TOKEN="${YOUR_TOKEN}" \
  rag-ingestion-enhanced:production
```

### Docker Compose with Confluence
```yaml
services:
  rag-ingestion-enhanced:
    environment:
      - CONFLUENCE_API_TOKEN=${CONFLUENCE_API_TOKEN}
      - CONFLUENCE_BASE_URL=https://company.atlassian.net
    volumes:
      - ./ingestion-config-confluence-example.yaml:/config/ingestion-config.yaml:ro
```

## 🔍 Troubleshooting

### Common Issues

#### Authentication Failures
```
Error: 401 Unauthorized
```
**Solutions:**
- Verify API token is correct and not expired
- Check username (should be email for Atlassian Cloud)
- Ensure user has read permissions for the spaces

#### Page Not Found
```
Error: Could not extract page ID from Confluence URL
```
**Solutions:**
- Check URL format is supported
- Verify page exists and is accessible
- Try using direct page ID format

#### Rate Limiting
```
Error: 429 Too Many Requests
```
**Solutions:**
- Increase crawl delay: `delay: 3.0` or higher
- Reduce max_pages limit
- Contact Confluence admin about rate limits

### Debug Mode

Enable debug logging for detailed information:
```yaml
# In your config
log_level: DEBUG

# Or via environment
LOG_LEVEL=DEBUG docker run ...
```

### Testing Confluence Access

```bash
# Test API access manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://company.atlassian.net/rest/api/content?limit=1"

# Should return JSON with content list
```

## 📈 Performance Considerations

### Optimization Tips

1. **Use Service Accounts**: Dedicated service accounts avoid personal rate limits
2. **Batch Processing**: Process multiple spaces in separate pipelines
3. **Selective Crawling**: Use space filters and include/exclude patterns
4. **Caching**: The system caches API responses during crawling sessions

### Rate Limiting Guidelines

| Confluence Type | Recommended Delay | Max Pages |
|----------------|-------------------|-----------|
| **Atlassian Cloud** | 2-3 seconds | 100-150 |
| **Server/Data Center** | 1-2 seconds | 200+ |
| **Public Cloud** | 3-5 seconds | 50-75 |

## 🛡️ Security Best Practices

### Token Management
- **Use environment variables** for tokens
- **Rotate tokens regularly** (every 90 days)
- **Use service accounts** with minimal permissions
- **Never commit tokens** to version control

### Access Control  
- **Read-only permissions** for ingestion service
- **Space-specific access** where possible
- **Monitor API usage** in Confluence admin

### Network Security
```yaml
# Example: Restrict to internal Confluence only
confluence:
  base_url: "https://internal-confluence.company.com"
  # Internal network access only
```

## 🎯 Next Steps

1. **Set up authentication** using one of the methods above
2. **Test with a single space** using the demo configuration
3. **Expand to multiple spaces** as needed
4. **Monitor performance** and adjust crawling parameters
5. **Integrate with your RAG UI** for seamless querying

The Confluence integration makes your RAG system a powerful tool for organizational knowledge management, combining internal Confluence content with external documentation in a single, searchable interface! 🚀