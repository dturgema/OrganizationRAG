#!/usr/bin/env python3
"""
Simple Docling-Enhanced MFS Ingestion
Advanced document structure analysis and content extraction
"""

import os
import requests
import psycopg2
from bs4 import BeautifulSoup
import time
import hashlib
import json
import tempfile

def setup_docling_simple():
    """Simple Docling setup without complex pipeline options"""
    try:
        from docling.document_converter import DocumentConverter
        
        # Simple converter without pipeline options that cause issues
        converter = DocumentConverter()
        
        print("✅ Docling initialized (simple mode)")
        return converter
        
    except Exception as e:
        print(f"⚠️ Docling setup failed: {e}")
        return None

def analyze_with_docling_simple(html_content: str, title: str, docling_converter):
    """Simple Docling analysis"""
    if not docling_converter:
        return None
        
    try:
        # Create proper HTML document
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
</head>
<body>
    {html_content}
</body>
</html>"""
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
            temp_file.write(full_html)
            temp_file_path = temp_file.name
        
        # Process with Docling
        result = docling_converter.convert(temp_file_path)
        
        # Clean up
        os.unlink(temp_file_path)
        
        # Extract enhanced content
        markdown_content = result.document.export_to_markdown()
        text_content = result.document.export_to_text()
        
        # Prefer markdown for better structure, fallback to text
        enhanced_content = markdown_content if len(markdown_content) > len(text_content) else text_content
        
        return {
            'enhanced_content': enhanced_content,
            'markdown': markdown_content,
            'text': text_content,
            'length_improvement': len(enhanced_content) - len(html_content)
        }
        
    except Exception as e:
        print(f"⚠️ Docling analysis failed: {e}")
        return None

def setup_database():
    """Standard database setup"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'rag-pgvector-openai'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'ragdb'),
            user=os.getenv('POSTGRES_USER', 'raguser'),
            password=os.getenv('POSTGRES_PASSWORD', 'ragpassword')
        )
        
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Use existing table structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content_id VARCHAR(255) UNIQUE,
                title TEXT,
                content TEXT,
                url TEXT,
                source_type VARCHAR(50),
                embedding vector(1536),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx 
            ON documents USING ivfflat (embedding vector_cosine_ops);
        """)
        
        conn.commit()
        print("✅ Database ready (existing schema)")
        return conn
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def get_embedding(text: str, api_key: str):
    """Get OpenAI embedding"""
    try:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "text-embedding-ada-002",
            "input": text[:8000]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return None

def scrape_confluence(url: str):
    """Scrape Confluence with auth"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if username and api_token:
            response = requests.get(url, headers=headers, auth=(username, api_token), timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "MFS Document"
        
        # Get clean HTML content
        # Remove scripts, styles, navigation
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Get main content area
        content_area = (
            soup.find('div', {'id': 'main-content'}) or
            soup.find('div', {'class': 'wiki-content'}) or
            soup.find('main') or
            soup.body
        )
        
        if content_area:
            clean_html = str(content_area)
            fallback_text = content_area.get_text(separator='\n', strip=True)
        else:
            clean_html = str(soup)
            fallback_text = soup.get_text(separator='\n', strip=True)
        
        return {
            'title': title,
            'clean_html': clean_html,
            'fallback_text': fallback_text,
            'url': url
        }
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return None

def main():
    """Main enhanced ingestion"""
    print("🚀 Simple Docling-Enhanced MFS Ingestion")
    print("=" * 50)
    
    # Setup
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY required")
        return
    print("✅ OpenAI API key found")
    
    db = setup_database()
    if not db:
        return
    
    docling_converter = setup_docling_simple()
    cursor = db.cursor()
    
    # URLs to process
    urls = [
        "https://doront.atlassian.net/wiki/spaces/MFS/pages/884737",
        "https://doront.atlassian.net/wiki/spaces/MFS/whiteboard/917505"
    ]
    
    total_processed = 0
    
    for url in urls:
        print(f"\n📄 Processing: {url}")
        
        # Scrape content
        scraped = scrape_confluence(url)
        if not scraped:
            continue
        
        print(f"   📝 Title: {scraped['title']}")
        print(f"   📊 Raw content: {len(scraped['fallback_text'])} characters")
        
        # Try Docling enhancement
        final_content = scraped['fallback_text']
        content_source = 'confluence_scraping'
        
        if docling_converter and len(scraped['clean_html']) > 200:
            print("   🔬 Enhancing with Docling...")
            
            docling_result = analyze_with_docling_simple(
                scraped['clean_html'], 
                scraped['title'], 
                docling_converter
            )
            
            if docling_result and len(docling_result['enhanced_content']) > len(final_content):
                final_content = docling_result['enhanced_content']
                content_source = 'docling_enhanced'
                improvement = docling_result['length_improvement']
                print(f"   ✅ Docling enhanced: +{improvement} characters")
                print(f"   📋 Content preview: {final_content[:200]}...")
            else:
                print("   ⚠️ Docling didn't improve content, using original")
        
        print(f"   📊 Final content: {len(final_content)} characters")
        
        # Generate embedding
        embedding = get_embedding(final_content, api_key)
        if not embedding:
            print("   ❌ Embedding failed")
            continue
        
        # Store in database
        content_id = hashlib.md5(url.encode()).hexdigest()
        
        try:
            cursor.execute("""
                INSERT INTO documents (content_id, title, content, url, source_type, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    source_type = EXCLUDED.source_type
            """, (
                content_id,
                scraped['title'],
                final_content,
                url,
                content_source,
                embedding,
                json.dumps({
                    'scraped_at': time.time(),
                    'content_length': len(final_content),
                    'docling_enhanced': content_source == 'docling_enhanced',
                    'original_length': len(scraped['fallback_text'])
                })
            ))
            
            db.commit()
            print("   ✅ Stored successfully")
            total_processed += 1
            
        except Exception as e:
            print(f"   ❌ Storage failed: {e}")
    
    cursor.close()
    db.close()
    
    print(f"\n🎉 Enhanced Ingestion Complete!")
    print(f"   📄 Pages processed: {total_processed}")
    print(f"   🔬 Docling used: {'Yes' if docling_converter else 'No'}")
    
    if total_processed > 0:
        print(f"\n💡 Your RAG system now has Docling-enhanced content!")
        print(f"   🌐 Visit: http://localhost:8501")
        print(f"   💬 Try asking about MFS order validation rules!")

if __name__ == "__main__":
    main()