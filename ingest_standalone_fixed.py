#!/usr/bin/env python3
"""
Fixed Standalone MFS Confluence Ingestion
Direct API approach with enhanced error handling and authentication
"""

import os
import requests
import psycopg2
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import hashlib
import json

def setup_database():
    """Set up PostgreSQL connection with proper configuration"""
    try:
        # Use environment variables for connection
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'rag-pgvector-openai'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'ragdb'),
            user=os.getenv('POSTGRES_USER', 'raguser'),
            password=os.getenv('POSTGRES_PASSWORD', 'ragpassword')
        )
        
        cursor = conn.cursor()
        
        # Enable vector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create documents table if it doesn't exist
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
        
        # Create index on embeddings for efficient similarity search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx 
            ON documents USING ivfflat (embedding vector_cosine_ops);
        """)
        
        conn.commit()
        print("✅ Database setup complete")
        return conn
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return None

def get_embedding_via_api(text: str, api_key: str) -> list:
    """Get embedding using direct API call to OpenAI"""
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-embedding-ada-002",  # Most compatible model
        "input": text[:8000]  # Limit input length
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return None

def scrape_confluence_page_authenticated(url: str) -> Dict[str, Any]:
    """Scrape Confluence page with proper authentication"""
    try:
        print(f"🌐 Scraping: {url}")
        
        # Enhanced headers to appear as a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Get authentication from environment
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if username and api_token:
            print(f"   🔐 Using Confluence authentication for {username}")
            response = requests.get(url, headers=headers, auth=(username, api_token), timeout=30)
        else:
            print("   ⚠️ No Confluence authentication configured")
            response = requests.get(url, headers=headers, timeout=30)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Confluence Document"
        
        # Remove unwanted elements
        for element in soup.find_all(['nav', 'header', 'footer', 'script', 'style', 'aside']):
            element.decompose()
        
        # Try to find main content area
        content_candidates = [
            soup.find('div', {'id': 'main-content'}),
            soup.find('div', {'class': 'wiki-content'}),
            soup.find('div', {'id': 'content'}),
            soup.find('main'),
            soup.body
        ]
        
        content_area = None
        for candidate in content_candidates:
            if candidate:
                content_area = candidate
                break
        
        if content_area:
            # Extract clean text with structure preserved
            content = content_area.get_text(separator=' ', strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = ' '.join(lines)
            
            # Remove duplicate spaces
            while '  ' in content:
                content = content.replace('  ', ' ')
        else:
            content = "No content found"
        
        # Generate unique content ID
        content_id = hashlib.md5(url.encode()).hexdigest()
        
        return {
            'content_id': content_id,
            'title': title,
            'content': content,
            'url': url,
            'source_type': 'confluence_web_scraping_fixed',
            'metadata': {
                'scraped_at': time.time(),
                'content_length': len(content),
                'title': title,
                'has_authentication': bool(username and api_token)
            }
        }
        
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return None

def chunk_content_smart(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Smart text chunking with overlap, preserving sentence boundaries"""
    if len(content) <= chunk_size:
        return [content]
    
    # Split into sentences first
    sentences = content.replace('. ', '.<SPLIT>').split('<SPLIT>')
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would exceed chunk size
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap
            overlap_words = current_chunk.split()[-overlap//10:] if current_chunk else []
            current_chunk = ' '.join(overlap_words) + ' ' + sentence
        else:
            current_chunk += ' ' + sentence
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [content]

def main():
    """Main ingestion function with enhanced error handling"""
    print("🚀 Fixed MFS Confluence Ingestion")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print("✅ OpenAI API key found")
    
    # Check Confluence configuration
    confluence_username = os.getenv('CONFLUENCE_USERNAME')
    confluence_token = os.getenv('CONFLUENCE_API_TOKEN')
    
    if confluence_username and confluence_token:
        print("✅ Confluence authentication configured")
    else:
        print("⚠️ Confluence authentication not configured - may have limited access")
    
    # Setup database
    db = setup_database()
    if not db:
        return False
    
    cursor = db.cursor()
    
    # URLs to process - your MFS pages
    urls_to_process = [
        "https://doront.atlassian.net/wiki/spaces/MFS/pages/884737/Product+configurator",
        # Add more URLs as needed
    ]
    
    total_processed = 0
    total_chunks = 0
    
    for url in urls_to_process:
        print(f"\n📄 Processing: {url}")
        
        # Scrape content with authentication
        doc_data = scrape_confluence_page_authenticated(url)
        if not doc_data:
            print("   ❌ Failed to scrape page")
            continue
            
        print(f"   Title: {doc_data['title']}")
        print(f"   Content: {len(doc_data['content'])} characters")
        
        # Create smart chunks
        chunks = chunk_content_smart(doc_data['content'])
        print(f"   Created: {len(chunks)} chunks")
        
        # Process each chunk
        chunk_count = 0
        for i, chunk in enumerate(chunks):
            try:
                print(f"   Processing chunk {i+1}/{len(chunks)}...", end=' ')
                
                # Generate embedding using direct API
                embedding = get_embedding_via_api(chunk, api_key)
                if not embedding:
                    print("❌ Failed")
                    continue
                
                # Create unique ID for this chunk
                chunk_id = f"{doc_data['content_id']}_chunk_{i}"
                chunk_title = f"{doc_data['title']} - Part {i+1}" if len(chunks) > 1 else doc_data['title']
                
                # Store in database with conflict resolution
                cursor.execute("""
                    INSERT INTO documents (content_id, title, content, url, source_type, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (content_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        title = EXCLUDED.title
                """, (
                    chunk_id,
                    chunk_title,
                    chunk,
                    doc_data['url'],
                    doc_data['source_type'],
                    embedding,
                    json.dumps(doc_data['metadata'])
                ))
                
                print("✅ Stored")
                chunk_count += 1
                total_chunks += 1
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing chunk: {e}")
                continue
        
        db.commit()
        total_processed += 1
        print(f"✅ Stored {chunk_count}/{len(chunks)} chunks")
        
        # Delay between pages to be respectful
        if len(urls_to_process) > 1:
            print("   ⏳ Waiting 2 seconds before next page...")
            time.sleep(2)
    
    cursor.close()
    db.close()
    
    print(f"\n🎉 Ingestion Complete!")
    print(f"   📄 Pages processed: {total_processed}")
    print(f"   📊 Total chunks stored: {total_chunks}")
    print(f"   💾 Database: ragdb (table: documents)")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Check your Streamlit app at http://localhost:8501")
    print(f"   2. Try asking questions about your MFS content!")
    print(f"   3. Add more URLs to the script if needed")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Ingestion failed. Check the errors above.")
        exit(1)