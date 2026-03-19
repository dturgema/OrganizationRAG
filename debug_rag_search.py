#!/usr/bin/env python3
"""
Debug RAG Search Issues
Test both query variations to see exactly what the RAG app returns
"""

import os
import requests
import psycopg2
import openai

def debug_rag_search():
    print("🔍 Debug RAG Search Behavior")
    print("=" * 50)
    
    # Setup (same as RAG app)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    client = openai.OpenAI(api_key=api_key)
    
    conn = psycopg2.connect(
        host='rag-pgvector-openai',
        port=5432, 
        database='ragdb',
        user='raguser',
        password='ragpassword'
    )
    
    def search_documents_debug(query: str, limit: int = 10):
        """Exact copy of RAG app search function with debug info"""
        try:
            print(f"\n🔎 Searching for: '{query}'")
            
            # Get query embedding (same as RAG app)
            response = client.embeddings.create(
                model=os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'),
                input=query
            )
            query_embedding = response.data[0].embedding
            print(f"✅ Generated embedding for query")
            
            # Search database (same as RAG app)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    title,
                    content,
                    url,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity
                FROM documents 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, query_embedding, limit))
            
            results = []
            for row in cursor.fetchall():
                title, content, url, metadata, similarity = row
                results.append({
                    'title': title,
                    'content': content,
                    'url': url,
                    'metadata': metadata or {},
                    'similarity': float(similarity)
                })
            
            cursor.close()
            
            print(f"✅ Found {len(results)} results")
            
            # Show results with similarity scores
            print(f"\n📋 Search Results:")
            for i, doc in enumerate(results, 1):
                print(f"  {i}. {doc['title']}")
                print(f"     Similarity: {doc['similarity']:.3f}")
                print(f"     Content length: {len(doc['content'])} chars")
                print(f"     Preview: {doc['content'][:100]}...")
                print()
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def build_context_debug(relevant_docs):
        """Debug context building (same as RAG app)"""
        if relevant_docs:
            print(f"\n🔧 Building context from {len(relevant_docs)} documents")
            
            context = "Relevant information from MFS documentation:\\n\\n"
            for i, doc in enumerate(relevant_docs, 1):
                context += f"{i}. {doc['title']} (similarity: {doc['similarity']:.3f})\\n"
                
                # Same logic as RAG app
                metadata = doc.get('metadata', {}) or {}
                source_type = metadata.get('source_type', '') if metadata else ''
                if 'whiteboard' in source_type.lower():
                    content_length = 3000  # More content for whiteboard docs
                else:
                    content_length = 1000  # Standard content length
                context += f"{doc['content'][:content_length]}...\\n\\n"
            
            print(f"✅ Context built: {len(context)} characters")
            return context
        else:
            print("⚠️ No relevant docs found")
            return "No specific MFS documentation found for this query."
    
    # Test both queries
    print("\n" + "="*60)
    print("🧪 TESTING PROBLEMATIC QUERY")
    print("="*60)
    
    results1 = search_documents_debug("explain the product configurator flow")
    context1 = build_context_debug(results1)
    
    print("\n" + "="*60) 
    print("🧪 TESTING WORKING QUERY")
    print("="*60)
    
    results2 = search_documents_debug("explain the product configurator flow of events")
    context2 = build_context_debug(results2)
    
    # Compare
    print("\n" + "="*60)
    print("📊 COMPARISON")
    print("="*60)
    
    print(f"Query 1 results: {len(results1)}")
    print(f"Query 2 results: {len(results2)}")
    
    if results1 and results2:
        print(f"Best similarity 1: {results1[0]['similarity']:.3f}")
        print(f"Best similarity 2: {results2[0]['similarity']:.3f}")
        
        print(f"Context 1 length: {len(context1)}")
        print(f"Context 2 length: {len(context2)}")
    
    conn.close()

if __name__ == "__main__":
    debug_rag_search()