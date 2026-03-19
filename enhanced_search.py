#!/usr/bin/env python3
"""
Enhanced RAG Search with Query Expansion
Improve semantic matching for natural language queries
"""

import os
import requests
import psycopg2
import openai
from typing import List, Dict

def expand_query(original_query: str, client) -> List[str]:
    """Generate query variations for better matching"""
    try:
        # Generate query variations using OpenAI
        expansion_prompt = f"""Generate 3-4 alternative phrasings of this query that might find relevant documentation:

Original: "{original_query}"

Generate variations that mean the same thing but use different terminology. Focus on:
- Synonyms and alternative terms
- More specific technical language
- Process-oriented vs outcome-oriented phrasing

Return only the alternative queries, one per line, without explanations."""

        response = client.chat.completions.create(
            model=os.getenv('INFERENCE_MODEL', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": expansion_prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        variations = [line.strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
        
        # Combine original with variations
        all_queries = [original_query] + variations
        print(f"🔍 Query variations generated: {len(all_queries)} total")
        for i, q in enumerate(all_queries):
            print(f"   {i+1}. {q}")
        
        return all_queries
        
    except Exception as e:
        print(f"⚠️ Query expansion failed: {e}")
        return [original_query]

def search_with_multiple_queries(queries: List[str], client, db, limit: int = 10):
    """Search using multiple query variations and combine results"""
    all_results = {}  # Use dict to deduplicate by content_id
    
    for i, query in enumerate(queries):
        try:
            print(f"\n🔎 Searching variation {i+1}: '{query}'")
            
            # Get embedding
            response = client.embeddings.create(
                model=os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'),
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # Search database
            cursor = db.cursor()
            cursor.execute("""
                SELECT 
                    content_id,
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
            
            results = cursor.fetchall()
            
            # Add to combined results with query context
            for content_id, title, content, url, metadata, similarity in results:
                if content_id not in all_results or similarity > all_results[content_id]['similarity']:
                    all_results[content_id] = {
                        'title': title,
                        'content': content,
                        'url': url,
                        'metadata': metadata or {},
                        'similarity': float(similarity),
                        'matched_query': query,
                        'query_variation': i+1
                    }
            
            cursor.close()
            print(f"   Found {len(results)} results (best similarity: {results[0][5]:.3f})")
            
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
    
    # Sort combined results by similarity
    final_results = sorted(all_results.values(), key=lambda x: x['similarity'], reverse=True)
    return final_results[:limit]

def test_enhanced_search():
    """Test enhanced search for both problematic queries"""
    print("🚀 Enhanced RAG Search Test")
    print("=" * 50)
    
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
    
    # Test the problematic query
    test_queries = [
        "explain the product configurator flow",
        "explain the product configurator flow of events"
    ]
    
    for original_query in test_queries:
        print(f"\n" + "="*70)
        print(f"🔍 TESTING: '{original_query}'")
        print("="*70)
        
        # Generate variations
        expanded_queries = expand_query(original_query, client)
        
        # Search with all variations
        enhanced_results = search_with_multiple_queries(expanded_queries, client, conn, 5)
        
        print(f"\n📊 ENHANCED SEARCH RESULTS:")
        print(f"Combined {len(enhanced_results)} unique documents")
        
        for i, result in enumerate(enhanced_results, 1):
            print(f"\n  {i}. {result['title']}")
            print(f"     Similarity: {result['similarity']:.3f}")
            print(f"     Matched query variation: #{result['query_variation']}")
            print(f"     Matched query: {result['matched_query']}")
            print(f"     Content: {result['content'][:150]}...")
    
    conn.close()

if __name__ == "__main__":
    test_enhanced_search()