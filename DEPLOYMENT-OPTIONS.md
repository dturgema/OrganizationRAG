# 🚀 RAG System Deployment Options

This guide covers all deployment options for the RAG system, from personal PC setup to enterprise OpenShift deployment.

## 📊 Deployment Comparison

| Deployment Type | Use Case | Hardware | Cost | Setup Time | Scalability |
|-----------------|----------|----------|------|------------|-------------|
| **PC + OpenAI** | Development, Personal | Any PC | $1-5/month | 2 minutes | Low |
| **PC + Ollama** | Local Development | GPU recommended | Free | 15 minutes | Low |
| **OpenShift + OpenAI** | Enterprise, Production | Any nodes | $50-500/month | 30 minutes | High |
| **OpenShift + Azure OpenAI** | Enterprise, Compliance | Any nodes | $100-1000/month | 45 minutes | High |
| **OpenShift AI (RHOAI)** | ML Platform Integration | GPU nodes | Hardware + license | 45 minutes | Very High |
| **OpenShift + vLLM** | High Performance | GPU cluster | Hardware cost | 60 minutes | Very High |
| **OpenShift + Ollama** | Self-hosted Enterprise | GPU nodes | Hardware cost | 45 minutes | High |

## 💻 Option 1: PC Development Setup

### **A. PC + OpenAI (Recommended for Development)**

**Perfect for:**
- Personal knowledge management
- Rapid prototyping
- Small team collaboration
- Learning and experimentation

**Setup:**
```bash
# Quick start (2 minutes)
./start-rag-openai.sh

# Manual setup
cp .env.openai .env
# Edit .env with your OpenAI API key
docker-compose -f docker-compose-openai.yml up -d
```

**Requirements:**
- Docker Desktop
- OpenAI API key
- 2GB+ RAM
- Internet connection

**Costs:**
- Small docs (~1000 pages): $1-2/month
- Medium docs (~5000 pages): $3-5/month
- Large docs (~10000 pages): $8-12/month

### **B. PC + Ollama (Self-hosted)**

**Perfect for:**
- Privacy-sensitive documents
- Offline development
- Cost-conscious users
- Learning about local LLMs

**Setup:**
```bash
# Install Ollama first
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b-instruct

# Start RAG system
docker-compose -f deploy/local/podman-compose.yml up -d
```

**Requirements:**
- 8GB+ RAM (16GB recommended)
- GPU recommended (NVIDIA)
- Ollama installed locally

**Costs:**
- Free (electricity only)
- Initial setup time longer

## 🏢 Option 2: Enterprise OpenShift Deployment

### **A. OpenShift + OpenAI**

**Perfect for:**
- Enterprise production deployment
- Teams needing latest AI capabilities
- Organizations with security policies allowing external APIs
- Rapid deployment with minimal infrastructure

**Setup:**
```bash
# Deploy to OpenShift
helm install rag-openai ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-openai.yaml \
  --set llama-stack.secrets.OPENAI_API_KEY="sk-your-key" \
  --namespace rag-system --create-namespace
```

**Configuration:**
- Edit `values-openai.yaml` with your settings
- Configure Confluence/GitHub integration
- Set up proper secrets management
- Configure network policies

**Benefits:**
- ✅ No GPU infrastructure needed
- ✅ Latest OpenAI models
- ✅ Predictable costs
- ✅ Fast deployment
- ✅ Auto-scaling support

### **B. OpenShift + Azure OpenAI**

**Perfect for:**
- Enterprise with Azure infrastructure
- Strict compliance requirements (HIPAA, SOX, etc.)
- Organizations requiring data residency
- Integration with Azure ecosystem

**Setup:**
```bash
# Deploy with Azure OpenAI
helm install rag-azure ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-azure-openai.yaml \
  --set llama-stack.secrets.AZURE_OPENAI_API_KEY="your-key" \
  --set llama-stack.secrets.AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com" \
  --namespace rag-system --create-namespace
```

**Additional Features:**
- Azure AD integration
- Private endpoints
- Azure Key Vault for secrets
- SharePoint/OneDrive integration
- Azure Log Analytics monitoring

**Benefits:**
- ✅ Enterprise compliance
- ✅ Data residency control
- ✅ Azure ecosystem integration
- ✅ Private networking
- ✅ Advanced monitoring

### **C. OpenShift + vLLM (High Performance)**

**Perfect for:**
- High-throughput requirements
- Large-scale document processing
- Cost optimization for heavy usage
- Custom model requirements

**Setup:**
```bash
# Deploy with vLLM backend
helm install rag-vllm ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-vllm.yaml \
  --namespace rag-system --create-namespace

# Ensure GPU nodes are available
oc get nodes -l node-type=gpu
```

**Requirements:**
- GPU-enabled OpenShift nodes
- NVIDIA GPU Operator installed
- High-memory instances
- Container storage for models

**Benefits:**
- ✅ Maximum performance
- ✅ Cost effective for high usage
- ✅ Custom model support
- ✅ On-premises data processing
- ✅ Multi-GPU scaling

### **D. OpenShift AI (RHOAI) - Model Serving Platform**

**Perfect for:**
- Organizations already using OpenShift AI
- Integrated data science workflows
- Model lifecycle management
- Advanced monitoring and governance

**Setup:**
```bash
# Prerequisites: Install OpenShift AI operator
# Apply RHOAI setup resources
kubectl apply -f ./deploy/openshift-ai-setup.yaml

# Deploy with OpenShift AI
helm install rag-rhoai ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-openshift-ai.yaml \
  --namespace llama-stack-rag --create-namespace
```

**Benefits:**
- ✅ Integrated model serving (KServe)
- ✅ Data science project management
- ✅ Model monitoring & metrics
- ✅ Pipeline orchestration
- ✅ Multi-runtime support (vLLM, OpenVINO)

### **E. OpenShift + vLLM (High Performance)**

**Perfect for:**
- High-throughput requirements
- Large-scale document processing
- Cost optimization for heavy usage
- Custom model requirements

**Setup:**
```bash
# Deploy with vLLM backend
helm install rag-vllm ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-vllm.yaml \
  --namespace rag-system --create-namespace

# Ensure GPU nodes are available
oc get nodes -l node-type=gpu
```

**Requirements:**
- GPU-enabled OpenShift nodes
- NVIDIA GPU Operator installed
- High-memory instances
- Container storage for models

**Benefits:**
- ✅ Maximum performance
- ✅ Cost effective for high usage
- ✅ Custom model support
- ✅ On-premises data processing
- ✅ Multi-GPU scaling

### **F. OpenShift + Ollama (Self-hosted Enterprise)**

**Perfect for:**
- Air-gapped environments
- Complete data sovereignty
- Cost-effective enterprise deployment
- Custom model fine-tuning

**Setup:**
```bash
# Deploy with Ollama
helm install rag-ollama ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-ollama.yaml \
  --namespace rag-system --create-namespace
```

**Benefits:**
- ✅ Complete data control
- ✅ No external API dependencies
- ✅ Customizable models
- ✅ Cost predictable (hardware only)

## 🎯 Choosing the Right Option

### **Development & Testing**
```
Personal Use → PC + OpenAI
Team Development → PC + OpenAI or OpenShift + OpenAI
Learning/Privacy → PC + Ollama
```

### **Production Deployment**
```
Quick Launch → OpenShift + OpenAI
Enterprise/Compliance → OpenShift + Azure OpenAI
High Performance → OpenShift + vLLM
Air-gapped/Sovereign → OpenShift + Ollama
```

### **Cost Considerations**
```
Budget Conscious → PC + Ollama or OpenShift + Ollama
Pay-per-use → OpenAI variants
High Volume → vLLM or Ollama
Predictable Costs → Self-hosted options
```

## ⚙️ Configuration Management

### **Environment Variables**

Each deployment type uses different environment variables:

**OpenAI:**
```bash
OPENAI_API_KEY=sk-your-key
INFERENCE_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

**Azure OpenAI:**
```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
```

**Ollama:**
```bash
OLLAMA_URL=http://ollama:11434
INFERENCE_MODEL=llama3.2:3b-instruct
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**vLLM:**
```bash
VLLM_URL=http://vllm-service:8000
TENSOR_PARALLEL_SIZE=2
GPU_MEMORY_UTILIZATION=0.85
```

### **Secrets Management**

**OpenShift with External Secrets Operator:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: openai-secret-store
spec:
  provider:
    kubernetes:
      remoteNamespace: secrets
      auth:
        serviceAccount:
          name: rag-secrets-reader
```

**Kubernetes Secrets:**
```bash
kubectl create secret generic openai-credentials \
  --from-literal=api-key="sk-your-openai-key" \
  --namespace rag-system
```

## 📋 Step-by-Step Deployment Guides

### **Quick PC Setup**
1. **Get OpenAI API key** from https://platform.openai.com/api-keys
2. **Run setup script:** `./start-rag-openai.sh`
3. **Edit .env file** with your API key
4. **Access UI** at http://localhost:8501

### **OpenShift Production Deployment**
1. **Choose provider** (OpenAI, Azure OpenAI, vLLM, Ollama)
2. **Prepare cluster:**
   ```bash
   oc new-project rag-system
   oc adm policy add-scc-to-user anyuid system:serviceaccount:rag-system:default
   ```
3. **Install dependencies:**
   ```bash
   # For GPU deployments
   helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
   helm install gpu-operator nvidia/gpu-operator --namespace gpu-operator-resources --create-namespace
   ```
4. **Deploy RAG system:**
   ```bash
   helm install rag ./deploy/helm/rag \
     -f ./deploy/helm/rag/values-[provider].yaml \
     --namespace rag-system
   ```
5. **Configure ingestion** and access UI

### **Hybrid Deployment**
You can even run both simultaneously:

```bash
# Development on PC
./start-rag-openai.sh

# Production on OpenShift  
helm install rag-prod ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-azure-openai.yaml \
  --namespace rag-prod
```

## 🔧 Advanced Configuration

### **Load Balancing Multiple Providers**
Configure multiple LLM providers for fallback:

```yaml
global:
  models:
    primary:
      provider: "openai"
      url: "https://api.openai.com/v1"
    fallback:
      provider: "azure-openai"  
      url: "https://your-resource.openai.azure.com"
```

### **Multi-Region Deployment**
Deploy across multiple OpenShift clusters:

```bash
# Region 1 (Primary)
helm install rag-us-east ./deploy/helm/rag \
  --set global.region=us-east \
  --namespace rag-system

# Region 2 (DR)  
helm install rag-us-west ./deploy/helm/rag \
  --set global.region=us-west \
  --namespace rag-system
```

### **Auto-scaling Configuration**
Enable horizontal pod autoscaling:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## 📊 Monitoring and Observability

### **Metrics Collection**
Each deployment includes monitoring capabilities:

```bash
# View metrics
kubectl port-forward svc/rag-metrics 9090:9090
# Access Prometheus at http://localhost:9090

# Check logs
kubectl logs -l app=rag-llamastack -f
```

### **Cost Monitoring**
For cloud providers, monitor usage:

```bash
# OpenAI usage
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/usage

# Azure OpenAI usage  
az monitor metrics list --resource $AZURE_OPENAI_RESOURCE_ID
```

## 🛠️ Troubleshooting

### **Common Issues by Deployment Type**

**PC Setup:**
- Port conflicts → Change ports in docker-compose
- API key errors → Verify key in .env file
- Memory issues → Increase Docker memory limit

**OpenShift:**
- Security context → Apply appropriate SCCs
- Network policies → Configure ingress/egress rules
- Resource limits → Adjust resource requests/limits

**GPU Deployments:**
- GPU not detected → Install GPU Operator
- Memory errors → Increase GPU memory allocation
- Model loading issues → Check storage and network

## 🎉 Summary

You now have **6 different deployment options** covering every use case from personal development to enterprise production. Each option is fully configured and ready to deploy:

- 💻 **PC Development**: Quick local setup with OpenAI or Ollama
- 🏢 **Enterprise Production**: Scalable OpenShift deployment with multiple provider options
- 🔧 **Flexible Configuration**: Mix and match components as needed
- 📊 **Complete Monitoring**: Built-in observability and cost tracking
- 🔒 **Security First**: Enterprise-grade security and compliance features

Choose the option that best fits your needs, and you'll have a powerful RAG system running in minutes! 🚀