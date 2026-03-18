#!/bin/bash
# RAG System Deployment Script
# Supports both PC and OpenShift deployment with multiple LLM providers

set -e

echo "🚀 RAG System Deployment Script"
echo "==============================="
echo ""
echo "💡 Quick PC development setup available: ./start-rag-openai.sh"
echo ""

# Function to display deployment options
show_deployment_options() {
    echo "📋 Available Deployment Options:"
    echo ""
    echo "💻 PC Development:"
    echo "   1. PC + OpenAI (Recommended for development)"
    echo "   2. PC + Ollama (Self-hosted, privacy-focused)"
    echo ""
    echo "🏢 OpenShift/Kubernetes Production:"
    echo "   3. OpenShift + OpenAI (Enterprise, external API)"
    echo "   4. OpenShift + Azure OpenAI (Enterprise compliance)"
    echo "   5. OpenShift AI (RHOAI model serving)"
    echo "   6. OpenShift + vLLM (High performance, GPU)"
    echo "   7. OpenShift + Ollama (Self-hosted enterprise)"
    echo ""
    echo "❓ Other:"
    echo "   8. Show detailed comparison"
    echo "   9. Help/Documentation"
    echo ""
}

# Function for PC + OpenAI deployment
deploy_pc_openai() {
    echo "🌐 Deploying RAG with PC + OpenAI"
    echo "=================================="
    
    # Check if start script exists
    if [ ! -f "./start-rag-openai.sh" ]; then
        echo "❌ start-rag-openai.sh not found. Are you in the RAG directory?"
        exit 1
    fi
    
    echo "✅ Found OpenAI deployment script"
    echo ""
    echo "📋 Requirements:"
    echo "   • Docker Desktop running"
    echo "   • OpenAI API key"
    echo "   • 2GB+ RAM available"
    echo ""
    
    read -p "Do you have an OpenAI API key ready? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🔑 Get your API key from: https://platform.openai.com/api-keys"
        echo "💡 Then run this script again"
        exit 0
    fi
    
    echo "🚀 Starting PC deployment with OpenAI..."
    ./start-rag-openai.sh
}

# Function for PC + Ollama deployment  
deploy_pc_ollama() {
    echo "🏠 Deploying RAG with PC + Ollama"
    echo "=================================="
    
    echo "📋 Requirements:"
    echo "   • Docker Desktop running"
    echo "   • Ollama installed locally"
    echo "   • 8GB+ RAM (16GB recommended)"
    echo "   • GPU recommended for performance"
    echo ""
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo "❌ Ollama not found. Installing..."
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "✅ Ollama is installed"
    fi
    
    # Check if model is downloaded
    echo "🔍 Checking for Llama model..."
    if ! ollama list | grep -q "llama3.2:3b"; then
        echo "📥 Downloading Llama 3.2 model (this may take a while)..."
        ollama pull llama3.2:3b-instruct
    else
        echo "✅ Llama model is ready"
    fi
    
    echo "🚀 Starting Ollama services..."
    if [ -f "./deploy/local/podman-compose.yml" ]; then
        docker-compose -f deploy/local/podman-compose.yml up -d
        echo "✅ Services started!"
        echo "🌐 Access the UI at: http://localhost:8501"
    else
        echo "❌ Ollama compose file not found"
        exit 1
    fi
}

# Function for OpenShift deployment
deploy_openshift() {
    local provider=$1
    
    echo "🏢 Deploying RAG to OpenShift with $provider"
    echo "=============================================="
    
    # Check if kubectl/oc is available
    if ! command -v oc &> /dev/null && ! command -v kubectl &> /dev/null; then
        echo "❌ Neither 'oc' nor 'kubectl' found. Please install OpenShift CLI or kubectl."
        exit 1
    fi
    
    # Use oc if available, otherwise kubectl
    if command -v oc &> /dev/null; then
        K8S_CMD="oc"
    else
        K8S_CMD="kubectl"
    fi
    
    echo "✅ Using $K8S_CMD for deployment"
    
    # Check if Helm is installed
    if ! command -v helm &> /dev/null; then
        echo "❌ Helm not found. Please install Helm 3.x"
        echo "💡 See: https://helm.sh/docs/intro/install/"
        exit 1
    fi
    
    echo "✅ Helm is available"
    
    # Check cluster connection
    if ! $K8S_CMD cluster-info &> /dev/null; then
        echo "❌ Cannot connect to Kubernetes cluster"
        echo "💡 Run: oc login <cluster-url> or kubectl config current-context"
        exit 1
    fi
    
    echo "✅ Connected to cluster"
    
    # Create namespace
    echo "📝 Creating namespace..."
    $K8S_CMD create namespace rag-system --dry-run=client -o yaml | $K8S_CMD apply -f -
    
    # Apply security context constraints for OpenShift
    if command -v oc &> /dev/null; then
        echo "🔒 Applying OpenShift security policies..."
        oc adm policy add-scc-to-user anyuid system:serviceaccount:rag-system:default || true
    fi
    
    # Deploy based on provider
    case $provider in
        "openai")
            deploy_openshift_openai
            ;;
        "azure-openai")
            deploy_openshift_azure_openai
            ;;
        "openshift-ai")
            deploy_openshift_ai
            ;;
        "vllm")
            deploy_openshift_vllm
            ;;
        "ollama")
            deploy_openshift_ollama
            ;;
        *)
            echo "❌ Unknown provider: $provider"
            exit 1
            ;;
    esac
}

# OpenShift + OpenAI deployment
deploy_openshift_openai() {
    echo "🔑 Setting up OpenAI credentials..."
    
    read -p "Enter your OpenAI API key: " -s openai_key
    echo
    
    if [[ -z "$openai_key" ]]; then
        echo "❌ OpenAI API key is required"
        exit 1
    fi
    
    # Create secret
    $K8S_CMD create secret generic openai-credentials \
        --from-literal=api-key="$openai_key" \
        --namespace rag-system \
        --dry-run=client -o yaml | $K8S_CMD apply -f -
    
    echo "✅ OpenAI credentials configured"
    
    # Deploy with Helm
    echo "🚀 Deploying RAG with OpenAI..."
    helm upgrade --install rag ./deploy/helm/rag \
        -f ./deploy/helm/rag/values-openai.yaml \
        --namespace rag-system \
        --timeout 10m
    
    show_deployment_status
}

# OpenShift + Azure OpenAI deployment
deploy_openshift_azure_openai() {
    echo "🔑 Setting up Azure OpenAI credentials..."
    
    read -p "Enter your Azure OpenAI API key: " -s azure_key
    echo
    read -p "Enter your Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com): " azure_endpoint
    
    if [[ -z "$azure_key" || -z "$azure_endpoint" ]]; then
        echo "❌ Both Azure OpenAI API key and endpoint are required"
        exit 1
    fi
    
    # Create secret
    $K8S_CMD create secret generic azure-openai-credentials \
        --from-literal=api-key="$azure_key" \
        --from-literal=endpoint="$azure_endpoint" \
        --namespace rag-system \
        --dry-run=client -o yaml | $K8S_CMD apply -f -
    
    echo "✅ Azure OpenAI credentials configured"
    
    # Deploy with Helm
    echo "🚀 Deploying RAG with Azure OpenAI..."
    helm upgrade --install rag ./deploy/helm/rag \
        -f ./deploy/helm/rag/values-azure-openai.yaml \
        --namespace rag-system \
        --timeout 10m
    
    show_deployment_status
}

# OpenShift + vLLM deployment
deploy_openshift_vllm() {
    echo "🎯 Setting up vLLM high-performance deployment..."
    
    # Check for GPU nodes
    echo "🔍 Checking for GPU nodes..."
    if ! $K8S_CMD get nodes -l feature.node.kubernetes.io/pci-10de.present=true --no-headers | grep -q .; then
        echo "⚠️  No GPU nodes detected. vLLM requires GPU nodes for optimal performance."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    else
        echo "✅ GPU nodes available"
    fi
    
    # Deploy with Helm
    echo "🚀 Deploying RAG with vLLM..."
    helm upgrade --install rag ./deploy/helm/rag \
        -f ./deploy/helm/rag/values-vllm.yaml \
        --namespace rag-system \
        --timeout 15m
    
    show_deployment_status
}

# OpenShift + Ollama deployment
deploy_openshift_ollama() {
    echo "🏠 Setting up Ollama self-hosted deployment..."
    
    # Deploy with Helm
    echo "🚀 Deploying RAG with Ollama..."
    helm upgrade --install rag ./deploy/helm/rag \
        -f ./deploy/helm/rag/values-ollama.yaml \
        --namespace rag-system \
        --timeout 15m
    
    show_deployment_status
}

# Show deployment status
show_deployment_status() {
    echo ""
    echo "🎉 Deployment initiated!"
    echo "======================="
    echo ""
    echo "📊 Checking deployment status..."
    
    # Wait a moment for pods to start
    sleep 10
    
    echo "Pod Status:"
    $K8S_CMD get pods -n rag-system
    
    echo ""
    echo "Service Status:"
    $K8S_CMD get svc -n rag-system
    
    echo ""
    echo "🔧 Useful Commands:"
    echo "   • Check logs: $K8S_CMD logs -f deployment/rag -n rag-system"
    echo "   • Get pods: $K8S_CMD get pods -n rag-system"
    echo "   • Port forward UI: $K8S_CMD port-forward svc/rag 8501:8501 -n rag-system"
    echo ""
    
    if command -v oc &> /dev/null; then
        echo "🌐 Creating OpenShift route..."
        oc create route edge --service=rag --port=8501 -n rag-system || true
        route_url=$(oc get route rag -n rag-system -o jsonpath='{.spec.host}' 2>/dev/null || echo "Route not ready yet")
        if [[ "$route_url" != "Route not ready yet" ]]; then
            echo "🎯 Access your RAG system at: https://$route_url"
        fi
    fi
    
    echo ""
    echo "⏳ Services may take 2-5 minutes to fully start up"
    echo "💡 Run '$K8S_CMD get pods -n rag-system -w' to watch startup progress"
}

# Show detailed comparison
show_comparison() {
    echo "📊 Detailed Deployment Comparison"
    echo "================================="
    echo ""
    echo "💻 PC + OpenAI:"
    echo "   ✅ Fastest setup (2 minutes)"
    echo "   ✅ No hardware requirements"
    echo "   ✅ Latest AI models"
    echo "   💰 Cost: \$1-5/month"
    echo "   🎯 Best for: Development, personal use"
    echo ""
    echo "💻 PC + Ollama:"
    echo "   ✅ Complete privacy"
    echo "   ✅ No ongoing costs"
    echo "   ⚠️  Requires good hardware"
    echo "   💰 Cost: Free (electricity)"
    echo "   🎯 Best for: Privacy-focused, learning"
    echo ""
    echo "🏢 OpenShift + OpenAI:"
    echo "   ✅ Enterprise scalability"
    echo "   ✅ Production ready"
    echo "   ✅ No GPU infrastructure needed"
    echo "   💰 Cost: \$50-500/month"
    echo "   🎯 Best for: Enterprise production"
    echo ""
    echo "🏢 OpenShift + Azure OpenAI:"
    echo "   ✅ Enterprise compliance"
    echo "   ✅ Azure ecosystem integration"
    echo "   ✅ Private networking"
    echo "   💰 Cost: \$100-1000/month"
    echo "   🎯 Best for: Regulated industries"
    echo ""
    echo "🤖 OpenShift AI (RHOAI):"
    echo "   ✅ Integrated model serving"
    echo "   ✅ Data science workflows"
    echo "   ✅ Model management & monitoring"
    echo "   💰 Cost: Hardware + subscription"
    echo "   🎯 Best for: ML platform integration"
    echo ""
    echo "🏢 OpenShift + vLLM:"
    echo "   ✅ Maximum performance"
    echo "   ✅ Custom models"
    echo "   ⚠️  Requires GPU cluster"
    echo "   💰 Cost: Hardware + electricity"
    echo "   🎯 Best for: High throughput"
    echo ""
    echo "🏢 OpenShift + Ollama:"
    echo "   ✅ Self-hosted enterprise"
    echo "   ✅ Complete data control"
    echo "   ⚠️  Infrastructure management"
    echo "   💰 Cost: Hardware + maintenance"
    echo "   🎯 Best for: Air-gapped environments"
    echo ""
}

# Show help
show_help() {
    echo "📚 RAG System Deployment Help"
    echo "=============================="
    echo ""
    echo "🎯 Quick Start Recommendations:"
    echo ""
    echo "👤 Personal/Development Use:"
    echo "   → Choose option 1 (PC + OpenAI)"
    echo "   → Get API key from: https://platform.openai.com/api-keys"
    echo "   → Costs ~\$1-5/month for typical usage"
    echo ""
    echo "🏢 Enterprise/Production Use:"
    echo "   → Choose option 3 (OpenShift + OpenAI) for quick start"
    echo "   → Choose option 4 (Azure OpenAI) for compliance requirements"
    echo "   → Choose option 5 (OpenShift AI) for integrated ML platform"
    echo "   → Choose option 6 (vLLM) for high performance needs"
    echo ""
    echo "🔒 Privacy/Security Focused:"
    echo "   → Choose option 2 (PC + Ollama) for personal use"
    echo "   → Choose option 7 (OpenShift + Ollama) for enterprise"
    echo ""
    echo "📖 Documentation:"
    echo "   • DEPLOYMENT-OPTIONS.md - Comprehensive guide"
    echo "   • README-OPENAI.md - PC setup with OpenAI"
    echo "   • CONFLUENCE-SPACE-DISCOVERY.md - Confluence integration"
    echo ""
    echo "🆘 Support:"
    echo "   • Check logs for troubleshooting"
    echo "   • Review configuration files in deploy/ directory"
    echo "   • Ensure all prerequisites are met"
    echo ""
}

# Main script logic
main() {
    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "deploy" ]; then
        echo "❌ Please run this script from the RAG project root directory"
        exit 1
    fi
    
    show_deployment_options
    
    read -p "Choose your deployment option (1-8): " choice
    
    case $choice in
        1)
            deploy_pc_openai
            ;;
        2)
            deploy_pc_ollama
            ;;
        3)
            deploy_openshift "openai"
            ;;
        4)
            deploy_openshift "azure-openai"
            ;;
        5)
            deploy_openshift "openshift-ai"
            ;;
        6)
            deploy_openshift "vllm"
            ;;
        7)
            deploy_openshift "ollama"
            ;;
        8)
            show_comparison
            echo ""
            read -p "Press Enter to return to menu..."
            main
            ;;
        9)
            show_help
            echo ""
            read -p "Press Enter to return to menu..."
            main
            ;;
        *)
            echo "❌ Invalid choice. Please select 1-9."
            exit 1
            ;;
    esac
}

# Run main function
main