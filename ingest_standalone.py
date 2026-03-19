#!/usr/bin/env python3
"""
Standalone MFS Confluence Ingestion
Works independently without LlamaStack dependency
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
    """Set up PostgreSQL connection and ensure vector extension is enabled"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'rag-pgvector-openai'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'ragdb'),
            user=os.getenv('POSTGRES_USER', 'raguser'),
            password=os.getenv('POSTGRES_PASSWORD', 'ragpassword')
        )
        
        cursor = conn.cursor()
        
        # Enable vector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create documents table
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
        
        # Create index on embeddings
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

def get_openai_embedding(text: str, api_key: str) -> List[float]:
    """Get embedding from OpenAI using direct API call"""
    try:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "text-embedding-ada-002",  # Use most compatible model
            "input": text[:8000]  # Limit text length
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return None

def scrape_confluence_page(url: str) -> Dict[str, Any]:
    """Scrape content from Confluence page"""
    try:
        print(f"🌐 Scraping: {url}")
        
        # Add some headers to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # Add Confluence authentication if available
        username = os.getenv('CONFLUENCE_USERNAME')
        api_token = os.getenv('CONFLUENCE_API_TOKEN')
        
        if username and api_token:
            print(f"   🔐 Using Confluence authentication for {username}")
            response = requests.get(url, headers=headers, auth=(username, api_token), timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1', {'id': 'title-text'}) or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Unknown Title"
        
        # Extract main content
        content_area = (
            soup.find('div', {'id': 'main-content'}) or
            soup.find('div', {'class': 'wiki-content'}) or
            soup.find('div', {'id': 'content'}) or
            soup.find('main') or
            soup.body
        )
        
        if content_area:
            # Remove navigation, headers, footers, etc.
            for element in content_area.find_all(['nav', 'header', 'footer', 'script', 'style', 'aside']):
                element.decompose()
                
            # Extract clean text
            content = content_area.get_text(separator='\n', strip=True)
            
            # Clean up the content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
        else:
            content = "No content found"
        
        # Generate content ID
        content_id = hashlib.md5(url.encode()).hexdigest()
        
        return {
            'content_id': content_id,
            'title': title,
            'content': content,
            'url': url,
            'source_type': 'confluence_web_scraping',
            'metadata': {
                'scraped_at': time.time(),
                'content_length': len(content),
                'title': title
            }
        }
        
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return None

def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Simple text chunking with overlap"""
    words = content.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) > 50:  # Only meaningful chunks
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
    
    return chunks if chunks else [content]  # Return original if no chunks created

def ingest_mfs_pages():
    """Main ingestion function"""
    print("🚀 Fixed MFS Confluence Ingestion")
    print("=" * 50)
    
    # Check environment
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print("✅ OpenAI API key found")
    
    # Check Confluence authentication
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
    
    # Your MFS pages to ingest
    urls_to_process = [
        "https://doront.atlassian.net/wiki/spaces/MFS/pages/884737",
        "https://doront.atlassian.net/wiki/spaces/MFS/whiteboard/917505",
        # Add more URLs as needed
        # "https://doront.atlassian.net/wiki/spaces/MFS/overview",
    ]
    
    total_processed = 0
    total_chunks = 0
    
    for url in urls_to_process:
        print(f"\n📄 Processing: {url}")
        
        # Scrape content
        doc_data = scrape_confluence_page(url)
        if not doc_data:
            continue
            
        print(f"   Title: {doc_data['title']}")
        print(f"   Content: {len(doc_data['content'])} characters")
        
        # Create chunks
        chunks = chunk_content(doc_data['content'])
        print(f"   Created: {len(chunks)} chunks")
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                print(f"   Processing chunk {i+1}/{len(chunks)}...", end=' ')
                
                embedding = get_openai_embedding(chunk, openai_key)
                if not embedding:
                    print("❌ Failed")
                    continue
                
                # Create unique ID for chunk
                chunk_id = f"{doc_data['content_id']}_chunk_{i}"
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO documents (content_id, title, content, url, source_type, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (content_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, (
                    chunk_id,
                    f"{doc_data['title']} - Part {i+1}",
                    chunk,
                    doc_data['url'],
                    doc_data['source_type'],
                    embedding,
                    json.dumps(doc_data['metadata'])
                ))
                
                print("✅")
                total_chunks += 1
                
                # Small delay to be respectful to APIs
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing chunk: {e}")
                continue
        
        db.commit()
        total_processed += 1
        
        # Delay between pages
        if len(urls_to_process) > 1:
            print("   ⏳ Waiting 2 seconds before next page...")
            time.sleep(2)
    
    cursor.close()
    db.close()
    
    print(f"\n🎉 Ingestion Complete!")
    print(f"   📄 Pages processed: {total_processed}")
    print(f"   📊 Total chunks stored: {total_chunks}")
    print(f"   💾 Database: ragdb (table: documents)")
    
    return True

if __name__ == "__main__":
    success = ingest_mfs_pages()
    if success:
        print("\n💡 Next steps:")
        print("   1. Check your Streamlit app at http://localhost:8501")
        print("   2. Try asking questions about your MFS content!")
        print("   3. Add more URLs to the script if needed")
    else:
        print("\n❌ Ingestion failed. Check the errors above.")