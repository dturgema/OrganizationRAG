#!/bin/bash
# Confluence Integration Test Script
# Tests the enhanced Confluence client and integration

set -e

echo "🔍 Testing Confluence Integration"
echo "=================================="

# Check if Python dependencies are available
echo "📦 Checking dependencies..."
python3 -c "import requests, bs4, yaml" 2>/dev/null || {
    echo "❌ Missing Python dependencies. Installing..."
    pip3 install requests beautifulsoup4 pyyaml lxml
}

# Test 1: URL parsing (no auth required)
echo -e "\n🔗 Test 1: URL Parsing"
echo "----------------------"
python3 confluence-test.py 2>/dev/null | head -20

# Test 2: Public Confluence access
echo -e "\n🌐 Test 2: Public Confluence Access"  
echo "-----------------------------------"
echo "Testing with Apache Kafka documentation..."

# Set up test environment
export CONFLUENCE_BASE_URL="https://cwiki.apache.org/confluence"

# Run basic connectivity test
echo "Checking network connectivity..."
curl -s -I "https://cwiki.apache.org/confluence/" | head -1

# Test 3: Docker-based integration test
if command -v docker &> /dev/null; then
    echo -e "\n🐳 Test 3: Docker Integration Test"
    echo "----------------------------------"
    echo "Building test container..."
    
    # Create minimal test environment file
    cat > .env.test << EOF
CONFLUENCE_BASE_URL=https://cwiki.apache.org/confluence
OPENAI_API_KEY=${OPENAI_API_KEY:-}
INFERENCE_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EOF
    
    # Run the test
    docker-compose -f docker-compose-confluence-test.yml --env-file .env.test run --rm confluence-test
    
    # Cleanup
    rm -f .env.test
    echo "✨ Docker test completed"
else
    echo "⏭️  Docker not available, skipping container test"
fi

# Test 4: Your Confluence instance (if configured)
if [[ -n "$CONFLUENCE_API_TOKEN" && -n "$CONFLUENCE_USERNAME" ]]; then
    echo -e "\n🏢 Test 4: Your Confluence Instance"
    echo "-----------------------------------"
    echo "Testing with your configured Confluence..."
    
    # Test authentication
    echo "Testing authentication..."
    python3 -c "
import os, requests, base64
base_url = os.getenv('CONFLUENCE_BASE_URL')
username = os.getenv('CONFLUENCE_USERNAME') 
token = os.getenv('CONFLUENCE_API_TOKEN')

if all([base_url, username, token]):
    auth = base64.b64encode(f'{username}:{token}'.encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    
    try:
        response = requests.get(f'{base_url}/rest/api/user/current', headers=headers, timeout=10)
        if response.status_code == 200:
            user = response.json()
            print(f'✅ Authentication successful: {user.get(\"displayName\", \"Unknown\")}')
        else:
            print(f'❌ Authentication failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Connection error: {e}')
else:
    print('⏭️  Confluence credentials not configured')
"
else
    echo -e "\n⚙️  Test 4: Configure Your Confluence"
    echo "------------------------------------"
    echo "To test with your Confluence instance, set these environment variables:"
    echo ""
    echo "export CONFLUENCE_BASE_URL='https://your-company.atlassian.net'"
    echo "export CONFLUENCE_USERNAME='your-email@company.com'"
    echo "export CONFLUENCE_API_TOKEN='your-api-token'"
    echo ""
    echo "Get your API token from:"
    echo "https://id.atlassian.com/manage-profile/security/api-tokens"
fi

# Test 5: Full ingestion test (if Docker available)
if command -v docker &> /dev/null; then
    echo -e "\n🚀 Test 5: Full Ingestion Test"
    echo "------------------------------"
    
    read -p "Run full ingestion test with Docker? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting full ingestion test..."
        
        # Create test environment
        cat > .env.ingestion << EOF
CONFLUENCE_BASE_URL=${CONFLUENCE_BASE_URL:-https://cwiki.apache.org/confluence}
CONFLUENCE_USERNAME=${CONFLUENCE_USERNAME:-}
CONFLUENCE_API_TOKEN=${CONFLUENCE_API_TOKEN:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
EOF
        
        # Start services
        docker-compose -f docker-compose-confluence-test.yml --env-file .env.ingestion up -d pgvector llamastack
        
        echo "Waiting for services to start..."
        sleep 15
        
        # Run ingestion
        docker-compose -f docker-compose-confluence-test.yml --env-file .env.ingestion run --rm confluence-ingestion
        
        echo "Ingestion completed. Check logs:"
        docker-compose -f docker-compose-confluence-test.yml logs confluence-ingestion
        
        # Cleanup
        docker-compose -f docker-compose-confluence-test.yml down
        rm -f .env.ingestion
    fi
fi

echo -e "\n✅ Confluence Integration Test Complete!"
echo "========================================"
echo ""
echo "🎯 Summary:"
echo "- URL parsing and page ID extraction"
echo "- Public Confluence connectivity"  
echo "- Authentication testing (if configured)"
echo "- Docker integration testing (if available)"
echo ""
echo "📚 Next Steps:"
echo "1. Configure your Confluence credentials"
echo "2. Test with a small number of pages first"
echo "3. Monitor logs for any issues"
echo "4. Scale up to full ingestion"
echo ""
echo "📖 Documentation:"
echo "- See ingestion-config-confluence-working.yaml for configuration"
echo "- See CONFLUENCE-INTEGRATION.md for detailed setup guide"