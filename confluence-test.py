#!/usr/bin/env python3
"""
Confluence Integration Test Script
Tests the enhanced Confluence client to verify it can fetch and parse pages.
"""

import os
import sys
import logging
from urllib.parse import urlparse

# Add the ingestion-service directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ingestion-service'))

from ingest import ConfluenceClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_space_discovery():
    """Test Confluence space discovery functionality."""
    print(f"\n🏢 Testing Space Discovery")
    print("=" * 30)
    
    # Test space URLs
    test_space_urls = [
        "https://cwiki.apache.org/confluence/display/KAFKA/Home",
        "https://your-company.atlassian.net/wiki/spaces/ENG/overview",
        "https://company.atlassian.net/wiki/spaces/HR/pages/viewspace.action",
    ]
    
    # Create client for testing (minimal config)
    client = ConfluenceClient(base_url="https://cwiki.apache.org/confluence")
    
    for url in test_space_urls:
        print(f"\n📍 Testing: {url}")
        
        # Test space detection
        is_space = client.is_space_url(url)
        print(f"   Is space URL: {is_space}")
        
        # Test space key extraction
        space_key = client.extract_space_key_from_url(url)
        if space_key:
            print(f"   ✅ Space key: {space_key}")
            
            # For public Confluence, try to get space info
            if "cwiki.apache.org" in url:
                space_info = client.get_space_info(space_key)
                if space_info:
                    print(f"   ✅ Space name: {space_info.get('name', 'Unknown')}")
                    print(f"   📄 Space description: {space_info.get('description', {}).get('plain', 'No description')[:100]}...")
                    
                    # Try to discover some pages
                    print(f"   🔍 Discovering pages in space...")
                    pages = client.get_space_pages(space_key, limit=5, include_attachments=False)
                    print(f"   📄 Found {len(pages)} pages/items")
                    
                    for i, page in enumerate(pages[:3]):  # Show first 3
                        content_type = page.get('content_type', 'page')
                        title = page.get('title', 'Unknown')
                        print(f"      {i+1}. [{content_type.upper()}] {title}")
                else:
                    print(f"   ❌ Could not get space info (may require auth)")
            else:
                print(f"   ⚠️  Skipping detailed discovery (requires authentication)")
        else:
            print(f"   ❌ Could not extract space key")

def test_confluence_client():
    """Test Confluence client with different authentication methods."""
    
    print("🔍 Testing Confluence Integration")
    print("=" * 50)
    
    # Test configuration - replace with your actual values
    test_configs = [
        {
            "name": "Atlassian Cloud with API Token",
            "base_url": os.getenv("CONFLUENCE_BASE_URL", "https://your-domain.atlassian.net"),
            "username": os.getenv("CONFLUENCE_USERNAME", "your-email@company.com"),
            "api_token": os.getenv("CONFLUENCE_API_TOKEN"),
            "test_urls": [
                "https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Test+Page",
                "https://your-domain.atlassian.net/wiki/display/SPACE/Test+Page"
            ],
            "space_urls": [
                "https://your-domain.atlassian.net/wiki/spaces/ENG/overview",
                "https://your-domain.atlassian.net/wiki/spaces/HR/overview"
            ]
        },
        {
            "name": "Public Confluence (no auth)",
            "base_url": "https://cwiki.apache.org/confluence",
            "test_urls": [
                "https://cwiki.apache.org/confluence/display/KAFKA/Home"
            ],
            "space_urls": [
                "https://cwiki.apache.org/confluence/display/KAFKA/Home"
            ]
        }
    ]
    
    for config in test_configs:
        print(f"\n📝 Testing: {config['name']}")
        print("-" * 30)
        
        # Skip if required credentials not provided
        if config.get("api_token") and not config["api_token"]:
            print("⏭️  Skipping - no API token provided")
            continue
            
        try:
            # Initialize client
            client = ConfluenceClient(
                base_url=config["base_url"],
                username=config.get("username"),
                api_token=config.get("api_token")
            )
            
            # Test URL parsing
            test_urls = config.get("test_urls", [])
            for url in test_urls:
                print(f"\n🔗 Testing URL: {url}")
                
                # Test page ID extraction
                page_id = client.extract_page_id_from_url(url)
                if page_id:
                    print(f"✅ Extracted page ID: {page_id}")
                    
                    # Test content fetching
                    page_data = client.get_page_content(page_id)
                    if page_data:
                        print(f"✅ Fetched page: {page_data.get('title', 'Unknown')}")
                        
                        # Test content conversion
                        body = page_data.get('body', {}).get('storage', {})
                        if body and 'value' in body:
                            text_content = client.convert_storage_to_text(body['value'])
                            word_count = len(text_content.split())
                            print(f"✅ Converted to text: {word_count} words")
                            
                            # Show preview
                            preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                            print(f"📄 Preview: {preview}")
                        else:
                            print("⚠️  No content body found")
                    else:
                        print("❌ Failed to fetch page data")
                else:
                    print("❌ Could not extract page ID from URL")
            
            # Test space discovery if space URLs provided
            space_urls = config.get("space_urls", [])
            if space_urls:
                print(f"\n📁 Testing Space Discovery:")
                for space_url in space_urls:
                    print(f"\n  🏢 Space URL: {space_url}")
                    
                    # Test space detection
                    is_space = client.is_space_url(space_url)
                    print(f"      Is space URL: {is_space}")
                    
                    # Test space key extraction
                    space_key = client.extract_space_key_from_url(space_url)
                    if space_key:
                        print(f"      ✅ Space key: {space_key}")
                        
                        # Try to discover content in the space
                        try:
                            print(f"      🔍 Discovering content...")
                            space_content = client.get_space_pages(
                                space_key, 
                                limit=10, 
                                include_attachments=True
                            )
                            
                            if space_content:
                                print(f"      ✅ Found {len(space_content)} items in space")
                                
                                # Categorize content
                                pages = [item for item in space_content if item.get('content_type') == 'page']
                                blog_posts = [item for item in space_content if item.get('content_type') == 'blogpost']
                                attachments = [item for item in space_content if item.get('content_type') == 'attachment']
                                
                                print(f"         📄 Pages: {len(pages)}")
                                print(f"         📰 Blog posts: {len(blog_posts)}")
                                print(f"         📎 Attachments: {len(attachments)}")
                                
                                # Show some examples
                                for i, item in enumerate(space_content[:3]):
                                    content_type = item.get('content_type', 'unknown')
                                    title = item.get('title', 'Unknown')
                                    depth = item.get('depth', 0)
                                    depth_indent = "  " * depth
                                    print(f"         {i+1}. {depth_indent}[{content_type.upper()}] {title}")
                                    
                            else:
                                print(f"      ❌ No content found in space")
                                
                        except Exception as space_error:
                            print(f"      ❌ Error discovering space content: {space_error}")
                    else:
                        print(f"      ❌ Could not extract space key")
                    
        except Exception as e:
            print(f"❌ Error testing {config['name']}: {e}")
    
    print(f"\n🎯 Test Configuration Help:")
    print("To test with your Confluence instance, set these environment variables:")
    print("export CONFLUENCE_BASE_URL='https://your-domain.atlassian.net'")
    print("export CONFLUENCE_USERNAME='your-email@company.com'")
    print("export CONFLUENCE_API_TOKEN='your-api-token'")
    print("\nGet API token from: https://id.atlassian.com/manage-profile/security/api-tokens")

def test_url_parsing():
    """Test various Confluence URL formats."""
    print(f"\n🔗 Testing URL Parsing")
    print("=" * 30)
    
    # Create a minimal client for URL testing
    client = ConfluenceClient(base_url="https://test.atlassian.net")
    
    test_urls = [
        "https://company.atlassian.net/wiki/spaces/ENG/pages/123456/Development+Guidelines",
        "https://company.atlassian.net/wiki/display/ENG/Development+Guidelines",
        "https://company.atlassian.net/wiki/pages/viewpage.action?pageId=123456",
        "https://company.atlassian.net/rest/api/content/123456",
        "https://cwiki.apache.org/confluence/display/KAFKA/Home"
    ]
    
    for url in test_urls:
        print(f"\n📍 URL: {url}")
        page_id = client.extract_page_id_from_url(url)
        if page_id:
            print(f"   ✅ Page ID: {page_id}")
        else:
            print(f"   ❌ Could not extract page ID")

if __name__ == "__main__":
    print("🚀 Confluence Integration Test Suite")
    print("=====================================")
    
    # Test URL parsing first (no auth required)
    test_url_parsing()
    
    # Test space discovery functionality
    test_space_discovery()
    
    # Test full integration
    test_confluence_client()
    
    print(f"\n✨ Test completed!")
    print(f"\n📋 Summary of Enhanced Features:")
    print("  ✅ URL parsing for pages and spaces")
    print("  ✅ Space discovery (all pages, blog posts, attachments)")
    print("  ✅ Recursive child page discovery")
    print("  ✅ Attachment detection and processing")
    print("  ✅ Multiple authentication methods")
    print("  ✅ Enhanced storage format parsing")
    print(f"\n🎯 Next Steps:")
    print("  1. Configure your Confluence credentials")
    print("  2. Test with ingestion-config-confluence-space-discovery.yaml")
    print("  3. Run full ingestion: docker-compose run --rm confluence-ingestion")
    print("  4. Monitor logs for space discovery progress")