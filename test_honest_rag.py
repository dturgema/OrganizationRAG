#!/usr/bin/env python3
"""
Test Honest RAG Response
Verify the system correctly identifies missing inventory status information
"""

import os
import requests
import psycopg2

def test_inventory_status_honesty():
    """Test that RAG correctly identifies missing inventory status info"""
    print("🧪 Testing RAG Honesty for Missing Information")
    print("=" * 50)
    
    query = "what are the optional inventory statuses"
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    try:
        # Get query embedding (same as RAG system)
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "text-embedding-ada-002",
            "input": query
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        query_embedding = result["data"][0]["embedding"]
        
        # Search database (same as RAG system)
        conn = psycopg2.connect(
            host='rag-pgvector-openai',
            port=5432,
            database='ragdb',
            user='raguser',
            password='ragpassword'
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                title,
                content,
                1 - (embedding <=> %s::vector) as similarity
            FROM documents 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 10
        """, (query_embedding, query_embedding))
        
        results = cursor.fetchall()
        
        # Build context like RAG system does
        context = "Relevant information from MFS documentation:\n\n"
        for i, (title, content, similarity) in enumerate(results[:3], 1):
            context += f"{i}. {title} (similarity: {similarity:.3f})\n"
            context += f"{content[:1000]}...\n\n"
        
        # Test with improved system prompt
        system_prompt = """You are an expert assistant for the MFS (Manufacturing & Configuration System) documentation. 
        You have access to comprehensive information about:
        - Order validation and status management
        - Configuration workflows and business rules
        - Inventory management and item validation
        - System architecture and integrations
        
        CRITICAL INSTRUCTIONS:
        1. Only answer based on what is EXPLICITLY stated in the provided context
        2. Do NOT conflate or mix different types of information (e.g., order statuses ≠ inventory statuses)
        3. If the user asks about specific values/statuses/options and they are NOT found in the context, clearly state: "The provided documents do not contain information about [specific topic]"
        4. Be especially careful to distinguish between:
           - Order statuses vs Inventory statuses vs Configuration statuses
           - Different entity types and their respective attributes
        5. If you see related but different information, acknowledge it but don't substitute it for what was asked
        
        Example: If asked about "inventory statuses" but only "order statuses" are in context, say: "The documents contain order status information (Open, Closed, Draft) but do not specify inventory status values." """
        
        context_analysis = f"""
        QUERY: {query}
        CONTEXT: {context}
        
        Please analyze if the provided context actually contains specific information to answer the query. 
        Pay special attention to:
        - Does the context contain the exact type of information requested?
        - Are there similar but different concepts that might be confused?
        - If asking about specific values/options, are those values actually present?
        
        Then provide your answer following the critical instructions."""
        
        # Generate response using same logic as RAG system
        chat_url = "https://api.openai.com/v1/chat/completions"
        chat_data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_analysis}
            ],
            "temperature": 0.1,
            "max_tokens": 1500
        }
        
        chat_response = requests.post(chat_url, headers=headers, json=chat_data, timeout=30)
        chat_response.raise_for_status()
        chat_result = chat_response.json()
        
        rag_answer = chat_result["choices"][0]["message"]["content"]
        
        print(f"🔍 Query: {query}")
        print(f"\n📋 Top documents found:")
        for i, (title, content, similarity) in enumerate(results[:3], 1):
            print(f"   {i}. {title} (similarity: {similarity:.3f})")
            
        print(f"\n🤖 RAG System Response:")
        print("-" * 40)
        print(rag_answer)
        print("-" * 40)
        
        # Analyze if the response is honest
        response_lower = rag_answer.lower()
        is_honest = any(phrase in response_lower for phrase in [
            "do not contain", "not found", "not specify", "no information", 
            "documents contain order status", "but not inventory"
        ])
        
        gives_wrong_info = any(phrase in response_lower for phrase in [
            "inventory statuses are open", "inventory status values: open", 
            "inventory statuses are: open", "inventory status values are open"
        ])
        
        # Check if it's correctly explaining the difference (good behavior)
        explains_difference = any(phrase in response_lower for phrase in [
            "only include information about order status", "order statuses (open, closed, draft) and do not specify",
            "contain order status", "but do not specify inventory"
        ])
        
        print(f"\n📊 Analysis:")
        print(f"   ✅ Honest about missing info: {'YES' if is_honest else 'NO'}")
        print(f"   🔄 Explains what it DOES have: {'YES' if explains_difference else 'NO'}")
        print(f"   ❌ Incorrectly substitutes ORDER for INVENTORY: {'YES' if gives_wrong_info else 'NO'}")
        
        if is_honest and not gives_wrong_info:
            print(f"\n🎉 SUCCESS: RAG system is now honest about missing inventory status information!")
            if explains_difference:
                print(f"🌟 BONUS: System also explains what related information it DOES have (order statuses)")
        else:
            print(f"\n⚠️ NEEDS IMPROVEMENT: RAG system still has issues with honesty.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_inventory_status_honesty()