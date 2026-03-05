#!/bin/bash
# Enhanced RAG Ingestion Service Build Script
# Builds Docker containers with recursive web crawling capabilities

set -e

# Configuration
IMAGE_NAME="rag-ingestion-enhanced"
VERSION="2.0.0"
REGISTRY="ghcr.io/dturgema"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Enhanced RAG Ingestion Service Builder${NC}"
echo -e "${BLUE}=============================================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"  
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Build selection
echo ""
echo "Select build type:"
echo "1) Enhanced (full features, ~800MB)"
echo "2) Production (optimized, ~600MB)"  
echo "3) Both"
echo ""
read -p "Choose option (1-3): " build_choice

build_enhanced() {
    print_status "Building enhanced image..."
    docker build -f ingestion-service/Containerfile.enhanced \
        -t ${IMAGE_NAME}:${VERSION}-enhanced \
        -t ${IMAGE_NAME}:enhanced \
        .
    print_status "Enhanced image built successfully"
}

build_production() {
    print_status "Building production image..."
    docker build -f ingestion-service/Containerfile.production \
        -t ${IMAGE_NAME}:${VERSION}-production \
        -t ${IMAGE_NAME}:production \
        -t ${IMAGE_NAME}:latest \
        .
    print_status "Production image built successfully"
}

case $build_choice in
    1)
        build_enhanced
        ;;
    2)
        build_production
        ;;
    3)
        build_enhanced
        build_production
        ;;
    *)
        print_error "Invalid option selected"
        exit 1
        ;;
esac

# Show built images
echo ""
print_status "Built images:"
docker images | grep ${IMAGE_NAME}

# Optional: Push to registry
echo ""
read -p "Push to registry? (y/N): " push_choice
if [[ $push_choice =~ ^[Yy]$ ]]; then
    print_status "Pushing to registry..."
    
    case $build_choice in
        1)
            docker tag ${IMAGE_NAME}:enhanced ${REGISTRY}/${IMAGE_NAME}:enhanced
            docker push ${REGISTRY}/${IMAGE_NAME}:enhanced
            ;;
        2)
            docker tag ${IMAGE_NAME}:production ${REGISTRY}/${IMAGE_NAME}:production
            docker tag ${IMAGE_NAME}:latest ${REGISTRY}/${IMAGE_NAME}:latest
            docker push ${REGISTRY}/${IMAGE_NAME}:production
            docker push ${REGISTRY}/${IMAGE_NAME}:latest
            ;;
        3)
            docker tag ${IMAGE_NAME}:enhanced ${REGISTRY}/${IMAGE_NAME}:enhanced
            docker tag ${IMAGE_NAME}:production ${REGISTRY}/${IMAGE_NAME}:production  
            docker tag ${IMAGE_NAME}:latest ${REGISTRY}/${IMAGE_NAME}:latest
            docker push ${REGISTRY}/${IMAGE_NAME}:enhanced
            docker push ${REGISTRY}/${IMAGE_NAME}:production
            docker push ${REGISTRY}/${IMAGE_NAME}:latest
            ;;
    esac
    
    print_status "Images pushed to registry"
fi

# Test run option
echo ""
read -p "Test run the container? (y/N): " test_choice
if [[ $test_choice =~ ^[Yy]$ ]]; then
    print_status "Running test container..."
    
    # Use production image if available, otherwise enhanced
    if docker images | grep -q "${IMAGE_NAME}.*production"; then
        TEST_IMAGE="${IMAGE_NAME}:production"
    else
        TEST_IMAGE="${IMAGE_NAME}:enhanced"  
    fi
    
    docker run --rm \
        -v "$(pwd)/ingestion-config-crawl-demo.yaml:/config/ingestion-config.yaml:ro" \
        -e LOG_LEVEL=DEBUG \
        ${TEST_IMAGE}
fi

echo ""
print_status "Build complete! 🎉"
echo ""
echo "Usage examples:"
echo "  docker run -v /path/to/config.yaml:/config/ingestion-config.yaml ${IMAGE_NAME}:production"
echo "  docker-compose up -d  # Using the provided docker-compose.yml"
echo ""
print_warning "Remember to mount your configuration file and ensure network connectivity for crawling!"