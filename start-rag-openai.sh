#!/bin/bash
# Quick Start Script for RAG with OpenAI on PC
# No GPU or local LLM required!

set -e

echo "🚀 Starting RAG with OpenAI on PC"
echo "=================================="
echo ""
echo "💡 This is the PC development setup. For enterprise OpenShift deployment,"
echo "   run: ./deploy-rag.sh (provides 6 deployment options)"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Setting up environment file..."
    
    if [ -f ".env.openai" ]; then
        cp .env.openai .env
        echo "✅ Copied .env.openai to .env"
    else
        echo "❌ .env.openai file not found!"
        exit 1
    fi
    
    echo ""
    echo "🔑 IMPORTANT: Edit .env file with your OpenAI API key:"
    echo "   1. Get API key from: https://platform.openai.com/api-keys"
    echo "   2. Edit .env file: nano .env"
    echo "   3. Replace 'sk-your-openai-api-key-here' with your actual key"
    echo "   4. Save and run this script again"
    echo ""
    
    # Open .env file for editing (try different editors)
    if command -v code &> /dev/null; then
        code .env
    elif command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    else
        echo "Please edit .env file with your text editor of choice"
    fi
    
    exit 0
fi

# Load environment variables
source .env

# Check if OpenAI API key is set
if [[ "${OPENAI_API_KEY}" == "sk-your-openai-api-key-here" ]] || [[ -z "${OPENAI_API_KEY}" ]]; then
    echo "❌ Please set your OpenAI API key in .env file"
    echo "   Edit .env and replace 'sk-your-openai-api-key-here' with your actual key"
    exit 1
fi

echo "✅ OpenAI API key configured"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Build images if needed
echo "📦 Building Docker images..."
docker-compose -f docker-compose-openai.yml build --quiet

# Start the services
echo "🏃 Starting RAG services with OpenAI..."
docker-compose -f docker-compose-openai.yml up -d pgvector llamastack

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are healthy
echo "🔍 Checking service health..."
if curl -f http://localhost:8321/health &> /dev/null; then
    echo "✅ LlamaStack is ready"
else
    echo "⚠️  LlamaStack might still be starting..."
fi

# Start the UI
echo "🖥️  Starting RAG UI..."
docker-compose -f docker-compose-openai.yml up -d rag-ui

echo ""
echo "🎉 RAG is starting up!"
echo "======================"
echo ""
echo "📊 Service URLs:"
echo "   • RAG UI: http://localhost:8501"
echo "   • LlamaStack API: http://localhost:8321"
echo "   • PostgreSQL: localhost:5432"
echo ""
echo "⏳ Please wait ~30 seconds for all services to fully start"
echo ""

# Optional: Run ingestion if configuration exists
if [ -f "ingestion-config-pc-openai.yaml" ]; then
    echo "📄 Found ingestion configuration. Run ingestion? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🔄 Running document ingestion..."
        docker-compose -f docker-compose-openai.yml run --rm rag-ingestion
        echo "✅ Ingestion completed!"
    fi
fi

echo ""
echo "🌐 Open your browser to: http://localhost:8501"
echo ""
echo "💡 To add documents:"
echo "   1. Use the web UI to upload files, or"
echo "   2. Edit ingestion-config-pc-openai.yaml with your URLs"
echo "   3. Run: docker-compose -f docker-compose-openai.yml run --rm rag-ingestion"
echo ""
echo "📊 Monitor logs: docker-compose -f docker-compose-openai.yml logs -f"
echo "🛑 Stop services: docker-compose -f docker-compose-openai.yml down"

# Wait a bit more then open browser
sleep 10
if command -v open &> /dev/null; then
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
fi

echo ""
echo "✨ PC Setup complete! Happy RAG-ing! 🤖"
echo ""
echo "🏢 For Enterprise OpenShift deployment with multiple LLM providers:"
echo "   ./deploy-rag.sh"
echo ""
echo "📚 Available deployment options:"
echo "   • PC + OpenAI (this setup) ✅"
echo "   • PC + Ollama (local models)"
echo "   • OpenShift + OpenAI (enterprise)"
echo "   • OpenShift + Azure OpenAI (compliance)"
echo "   • OpenShift AI (ML platform integration)"
echo "   • OpenShift + vLLM (high performance)"
echo "   • OpenShift + Ollama (self-hosted enterprise)"