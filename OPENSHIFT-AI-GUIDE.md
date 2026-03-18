# 🤖 OpenShift AI (RHOAI) Integration Guide

This guide covers deploying the RAG system with **Red Hat OpenShift AI** for integrated model serving and data science workflows.

## 🎯 What is OpenShift AI Integration?

OpenShift AI (RHOAI) provides a comprehensive ML platform with:
- **Model Serving**: KServe-based inference services
- **Data Science Projects**: Organized workspaces for ML teams
- **Pipeline Orchestration**: Kubeflow Pipelines for ML workflows
- **Model Management**: Centralized model registry and versioning
- **Monitoring**: Built-in metrics and performance tracking

## 🏗️ Architecture Overview

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   RAG Frontend      │    │    LlamaStack        │    │   OpenShift AI      │
│   (Streamlit)       │◄──►│   Orchestrator       │◄──►│   Model Serving     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                       │                           │
                                       ▼                           ▼
┌─────────────────────────────────────────────────────────┐    ┌─────────────────────┐
│                PGVector Database                        │    │   Inference         │
│            (Vector Embeddings)                          │    │   Services          │
└─────────────────────────────────────────────────────────┘    │   • vLLM Runtime    │
                                                                │   • OpenVINO        │
                                                                │   • Custom Models   │
                                                                └─────────────────────┘
```

## 🚀 Quick Start

### **Prerequisites**
1. **OpenShift cluster** with admin access
2. **OpenShift AI operator** installed
3. **GPU nodes** (recommended for LLM serving)
4. **Sufficient resources** (8GB+ RAM per model)

### **1. Install OpenShift AI**
```bash
# Install from OperatorHub or CLI
oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: rhods-operator
  namespace: redhat-ods-operator
spec:
  channel: fast
  name: rhods-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
```

### **2. Deploy RAG with OpenShift AI**
```bash
# Use the interactive script
./deploy-rag.sh
# Choose option 5: OpenShift AI (RHOAI model serving)

# Or deploy directly
kubectl apply -f ./deploy/openshift-ai-setup.yaml
helm install rag ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-openshift-ai.yaml \
  --namespace llama-stack-rag --create-namespace
```

### **3. Access the System**
```bash
# Get the route URL
oc get route rag -n llama-stack-rag

# Access OpenShift AI Dashboard
oc get route rhods-dashboard -n redhat-ods-applications
```

## 📋 Detailed Setup Guide

### **Step 1: Verify OpenShift AI Installation**
```bash
# Check operator status
oc get csv -n redhat-ods-operator | grep rhods

# Check for Data Science Cluster
oc get datasciencecluster -A

# Verify GPU nodes (if using GPU models)
oc get nodes -l feature.node.kubernetes.io/pci-10de.present=true
```

### **Step 2: Create OpenShift AI Resources**
```bash
# Apply the comprehensive setup
kubectl apply -f ./deploy/openshift-ai-setup.yaml
```

This creates:
- **Data Science Project**: `llama-stack-rag`
- **Serving Runtimes**: vLLM and OpenVINO
- **Inference Services**: For LLM and embedding models
- **Storage Secrets**: For model storage
- **Monitoring**: ServiceMonitor for metrics

### **Step 3: Deploy RAG System**
```bash
helm install rag ./deploy/helm/rag \
  -f ./deploy/helm/rag/values-openshift-ai.yaml \
  --namespace llama-stack-rag \
  --create-namespace \
  --timeout 15m
```

### **Step 4: Monitor Deployment**
```bash
# Check inference services
oc get inferenceservice -n llama-stack-rag

# Monitor model loading
oc logs -f deployment/llama-3-2-3b-predictor-default -n llama-stack-rag

# Check RAG application
oc get pods -n llama-stack-rag
```

## 🎛️ Configuration Options

### **Model Configuration**
Edit `values-openshift-ai.yaml` to configure models:

```yaml
global:
  models:
    llama-3-2-3b-rhoai:
      id: meta-llama/Llama-3.2-3B-Instruct
      enabled: true
      serving_runtime: "vllm-runtime"
      resources:
        limits:
          nvidia.com/gpu: "1"
          memory: "8Gi"
      model_config:
        max_model_len: 8192
        tensor_parallel_size: 1
```

### **Serving Runtime Options**
- **vLLM**: High-performance LLM serving
- **OpenVINO**: Optimized for CPU/Intel hardware
- **TensorRT-LLM**: NVIDIA GPU optimization
- **Custom**: Bring your own serving runtime

### **Resource Configuration**
```yaml
# GPU requirements
resources:
  limits:
    nvidia.com/gpu: "1"
    memory: "8Gi"
  requests:
    nvidia.com/gpu: "1"
    memory: "4Gi"
    cpu: "2"
```

## 🔧 Advanced Features

### **Multi-Model Serving**
Deploy multiple models simultaneously:

```yaml
global:
  models:
    # Chat model
    llama-3-2-3b-rhoai:
      enabled: true
      serving_runtime: "vllm-runtime"
      
    # Code generation model
    codellama-7b-rhoai:
      enabled: true
      serving_runtime: "vllm-runtime"
      
    # Embedding model
    embedding-rhoai:
      enabled: true
      serving_runtime: "ovms-runtime"
```

### **Auto-scaling Configuration**
```yaml
# In InferenceService spec
spec:
  predictor:
    scaleTarget: 50  # Target requests per second
    minReplicas: 1
    maxReplicas: 5
```

### **Model Storage Options**
Configure where models are stored:

```yaml
# S3-compatible storage
storage:
  key: aws-connection-models
  path: meta-llama/Llama-3.2-3B-Instruct
  
# Or PVC storage
storage:
  storageUri: "pvc://model-storage/llama-3.2-3b"
```

## 📊 Monitoring and Observability

### **Built-in Metrics**
OpenShift AI provides comprehensive metrics:

- **Model Performance**: Latency, throughput, errors
- **Resource Usage**: GPU/CPU/memory utilization
- **Request Patterns**: Traffic analysis
- **Model Health**: Availability and responsiveness

### **Accessing Metrics**
```bash
# Port-forward to Prometheus
oc port-forward svc/prometheus -n istio-system 9090:9090

# View Grafana dashboards
oc get route grafana-route -n redhat-ods-monitoring
```

### **Custom Dashboards**
The deployment includes Grafana dashboards for:
- RAG system performance
- Model serving metrics
- Document processing statistics
- User interaction patterns

## 🔒 Security and Compliance

### **Network Security**
- **Network Policies**: Restrict traffic between components
- **Service Mesh**: Istio integration for secure communication
- **TLS Termination**: Encrypted connections

### **Access Control**
- **RBAC**: Role-based access to OpenShift AI resources
- **Service Accounts**: Dedicated accounts for each component
- **Secret Management**: Secure credential storage

### **Audit Logging**
- **Model Access**: Track all model inference requests
- **Data Access**: Log document and database operations
- **User Actions**: Monitor UI and API interactions

## 🛠️ Troubleshooting

### **Common Issues**

**Model Loading Fails**
```bash
# Check inference service status
oc describe inferenceservice llama-3-2-3b -n llama-stack-rag

# Check model serving runtime
oc logs -f deployment/llama-3-2-3b-predictor-default -n llama-stack-rag
```

**GPU Not Available**
```bash
# Verify GPU operator
oc get pods -n nvidia-gpu-operator

# Check node labels
oc get nodes -l feature.node.kubernetes.io/pci-10de.present=true
```

**Storage Issues**
```bash
# Check storage connection
oc get secret aws-connection-models -n llama-stack-rag -o yaml

# Verify model download
oc logs -f job/model-downloader -n llama-stack-rag
```

**Performance Issues**
```bash
# Monitor resource usage
oc top pods -n llama-stack-rag

# Check metrics
oc port-forward svc/prometheus 9090:9090
# Visit http://localhost:9090
```

### **Debug Commands**
```bash
# Get all RHOAI resources
oc get inferenceservice,servingruntime,datascienceproject -n llama-stack-rag

# Check operator logs
oc logs -f deployment/rhods-operator -n redhat-ods-operator

# Describe failing pods
oc describe pod <failing-pod-name> -n llama-stack-rag
```

## 🎯 Use Cases and Benefits

### **Enterprise ML Platform**
- **Integrated Workflows**: Seamless integration with existing ML pipelines
- **Model Lifecycle**: From development to production deployment
- **Team Collaboration**: Shared workspaces and resources
- **Governance**: Model approval and compliance workflows

### **Production-Ready Serving**
- **High Availability**: Multi-replica model serving
- **Auto-scaling**: Dynamic scaling based on demand
- **Load Balancing**: Distribute requests across replicas
- **A/B Testing**: Deploy multiple model versions

### **Cost Optimization**
- **Resource Sharing**: Multiple models on shared infrastructure
- **Smart Scaling**: Scale down during low usage
- **GPU Efficiency**: Maximize hardware utilization
- **Spot Instances**: Use preemptible nodes where available

## 📈 Performance Tuning

### **Model Serving Optimization**
```yaml
# vLLM configuration
env:
  - name: TENSOR_PARALLEL_SIZE
    value: "2"  # Use multiple GPUs
  - name: GPU_MEMORY_UTILIZATION
    value: "0.85"  # Optimize memory usage
  - name: MAX_BATCH_SIZE
    value: "32"  # Batch requests for efficiency
```

### **Resource Allocation**
```yaml
resources:
  limits:
    nvidia.com/gpu: "2"  # Multi-GPU setup
    memory: "16Gi"
  requests:
    nvidia.com/gpu: "1"
    memory: "8Gi"
    cpu: "4"
```

### **Caching and Storage**
- **Model Caching**: Cache frequently used models
- **Fast Storage**: Use SSD storage for model loading
- **Content Delivery**: CDN for model artifacts

## 🎉 Summary

OpenShift AI integration provides:

✅ **Enterprise-Grade Model Serving**: KServe-based inference  
✅ **Integrated ML Platform**: Full data science workflow support  
✅ **Advanced Monitoring**: Comprehensive metrics and dashboards  
✅ **High Availability**: Auto-scaling and load balancing  
✅ **Security**: Network policies and access control  
✅ **Cost Optimization**: Efficient resource utilization  

This makes it perfect for organizations that:
- Already use OpenShift AI for ML workloads
- Need integrated model lifecycle management
- Require enterprise-grade monitoring and governance
- Want to leverage existing ML platform investments

🚀 **Ready to deploy?** Run `./deploy-rag.sh` and choose option 5: **OpenShift AI (RHOAI model serving)**!