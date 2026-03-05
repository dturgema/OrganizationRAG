# Enhanced RAG Docker Deployment Guide

This guide covers deploying the enhanced RAG system with recursive web crawling capabilities using Docker containers.

## 🎯 What's Enhanced

- **🕷️ Recursive Web Crawling** - Automatically discover and process linked web pages
- **📄 Multi-Format Support** - Process PDF, HTML, DOCX, PPTX documents  
- **⚙️ Production-Ready** - Optimized containers with security and monitoring
- **🔧 Easy Deployment** - Automated build scripts and docker-compose orchestration

## 📦 Available Container Images

### 1. Enhanced Container (`Containerfile.enhanced`)
- **Size**: ~800MB
- **Features**: Full development features, debugging tools
- **Use case**: Development, testing, experimentation

### 2. Production Container (`Containerfile.production`)  
- **Size**: ~600MB
- **Features**: Multi-stage build, security hardened, optimized
- **Use case**: Production deployments, CI/CD pipelines

## 🚀 Quick Start

### Option 1: Using Build Script (Recommended)

```bash
# Make script executable and run
chmod +x build-enhanced-ingestion.sh
./build-enhanced-ingestion.sh

# Follow interactive prompts to:
# 1. Choose build type (enhanced/production/both)
# 2. Optionally push to registry
# 3. Test run the container
```

### Option 2: Manual Build

```bash
# Build enhanced version
docker build -f ingestion-service/Containerfile.enhanced \
  -t rag-ingestion-enhanced:enhanced .

# Build production version  
docker build -f ingestion-service/Containerfile.production \
  -t rag-ingestion-enhanced:production .
```

### Option 3: Complete Stack with Docker Compose

```bash
# Start the entire enhanced RAG stack
docker-compose -f docker-compose.enhanced.yml up -d

# Watch ingestion progress
docker-compose -f docker-compose.enhanced.yml logs -f rag-ingestion-enhanced

# Access RAG UI
open http://localhost:8501
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INGESTION_CONFIG` | `/config/ingestion-config.yaml` | Configuration file path |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MAX_WORKERS` | `4` | Maximum parallel workers |
| `CRAWL_DELAY` | `1.0` | Delay between requests (seconds) |
| `MAX_PAGES` | `50` | Maximum pages to crawl per pipeline |

### Volume Mounts

```bash
# Configuration file (required)
-v /path/to/config.yaml:/config/ingestion-config.yaml:ro

# Logs (optional)
-v /path/to/logs:/app/logs

# Temporary files (optional, improves performance)
-v /path/to/temp:/app/temp
```

## 🔧 Usage Examples

### Basic Document Processing

```bash
docker run --rm \
  -v "$(pwd)/ingestion-config-crawl-demo.yaml:/config/ingestion-config.yaml:ro" \
  rag-ingestion-enhanced:production
```

### Web Crawling with Custom Configuration

```bash
# Create custom config
cat > my-crawl-config.yaml << EOF
llamastack:
  base_url: "http://llamastack:8321"
vector_db:
  embedding_model: "all-MiniLM-L6-v2"
  embedding_dimension: 384
pipelines:
  my-docs:
    enabled: true
    name: "my-knowledge-base"
    source: URL
    config:
      urls:
        - "https://docs.mycompany.com/"
      crawl:
        enabled: true
        max_depth: 3
        max_pages: 100
EOF

# Run with custom config
docker run --rm \
  -v "$(pwd)/my-crawl-config.yaml:/config/ingestion-config.yaml:ro" \
  -e LOG_LEVEL=DEBUG \
  rag-ingestion-enhanced:production
```

### Production Deployment with Logging

```bash
docker run -d \
  --name rag-ingestion \
  -v "$(pwd)/config:/config:ro" \
  -v "$(pwd)/logs:/app/logs" \
  -e LOG_LEVEL=INFO \
  -e MAX_WORKERS=8 \
  --memory=2g \
  --cpus=2 \
  rag-ingestion-enhanced:production
```

## 📊 Monitoring and Troubleshooting

### Check Container Status

```bash
# View running containers
docker ps

# Check logs
docker logs rag-ingestion-enhanced

# Monitor resource usage
docker stats rag-ingestion-enhanced
```

### Debug Mode

```bash
# Run in debug mode with shell access
docker run -it --rm \
  -v "$(pwd)/config:/config:ro" \
  --entrypoint /bin/bash \
  rag-ingestion-enhanced:enhanced

# Inside container, run manually
python ingest.py
```

### Health Checks

The containers include health checks:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' rag-ingestion-enhanced

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' rag-ingestion-enhanced
```

## 🔒 Security Features

### Production Container Security

- **Non-root user**: Runs as `raguser` (UID 1000)
- **Minimal base image**: Uses Python slim for reduced attack surface  
- **Read-only config**: Configuration mounted read-only
- **Resource limits**: Memory and CPU limits enforced
- **Health checks**: Built-in container health monitoring

### Network Security

```bash
# Run with restricted network access
docker run --rm \
  --network none \
  --add-host llamastack:host-gateway \
  -v config:/config:ro \
  rag-ingestion-enhanced:production
```

## 🎛️ Advanced Configuration

### Custom Dockerfile Extensions

```dockerfile
# Extend the enhanced image
FROM rag-ingestion-enhanced:production

# Add custom dependencies
USER root
RUN pip install custom-package
USER raguser

# Add custom scripts
COPY custom-scripts/ /app/custom/
```

### Multi-Architecture Builds

```bash
# Build for multiple architectures
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f ingestion-service/Containerfile.production \
  -t rag-ingestion-enhanced:multi-arch \
  --push .
```

## 🔧 Development Workflow

### Local Development

```bash
# Mount source code for live development
docker run -it --rm \
  -v "$(pwd)/ingestion-service:/app:rw" \
  -v "$(pwd)/config:/config:ro" \
  --entrypoint /bin/bash \
  rag-ingestion-enhanced:enhanced

# Make changes and test immediately
```

### CI/CD Pipeline Example

```yaml
# .github/workflows/docker-build.yml
name: Build Enhanced RAG Containers
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and test
        run: |
          ./build-enhanced-ingestion.sh
          docker run --rm rag-ingestion-enhanced:production --help
```

## 📚 Configuration Examples

The repository includes several ready-to-use configurations:

- `ingestion-config-crawl-demo.yaml` - Basic crawling demo
- `ingestion-config-html-example.yaml` - Comprehensive examples  
- `deploy/local/ingestion-config.yaml` - Default configuration

## 🆘 Support and Troubleshooting

### Common Issues

1. **Out of Memory**: Increase Docker memory limits or reduce `MAX_WORKERS`
2. **Network Timeouts**: Increase `CRAWL_DELAY` for external sites  
3. **Permission Errors**: Ensure volume mounts have correct permissions
4. **Build Failures**: Check Docker version and available disk space

### Getting Help

- **Logs**: Always check container logs first: `docker logs <container>`
- **Debug Mode**: Use enhanced container with shell access for debugging
- **Resource Monitoring**: Use `docker stats` to monitor resource usage
- **Health Checks**: Container health status indicates operational state

## 🎉 Next Steps

1. **Test with demo config**: Start with `ingestion-config-crawl-demo.yaml`
2. **Customize for your needs**: Modify configurations for your URLs
3. **Scale up**: Use docker-compose for full stack deployment
4. **Monitor**: Set up logging and monitoring for production use
5. **Extend**: Add custom processing logic or data sources