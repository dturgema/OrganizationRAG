#!/usr/bin/env python3
"""
MFS RAG System - Streamlit UI
Production-ready RAG interface with OpenAI integration
"""

import streamlit as st
import os
import psycopg2
import openai
from typing import List, Dict, Any
import time

# Configure OpenAI
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'rag-pgvector-openai'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'ragdb'),
    'user': os.getenv('POSTGRES_USER', 'raguser'),
    'password': os.getenv('POSTGRES_PASSWORD', 'ragpassword')
}

@st.cache_resource
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

@st.cache_data(show_spinner=False)
def search_documents(query: str, client, db, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for relevant documents using vector similarity"""
    try:
        # Get query embedding
        response = client.embeddings.create(
            model=os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'),
            input=query
        )
        query_embedding = response.data[0].embedding
        
        # Search database
        cursor = db.cursor()
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
        return results
        
    except Exception as e:
        st.error(f"Search failed: {e}")
        return []

def generate_response(query: str, context: str, client) -> str:
    """Generate response using OpenAI"""
    try:
        system_prompt = """You are an expert assistant for the MFS (Manufacturing & Configuration System) documentation. 
        You have access to comprehensive information about:
        - Order validation and status management
        - Configuration workflows and business rules
        - Inventory management and item validation
        - System architecture and integrations
        
        Provide accurate, helpful responses based on the provided context. If the information isn't in the context, say so clearly."""
        
        response = client.chat.completions.create(
            model=os.getenv('INFERENCE_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating response: {e}"

def main():
    st.set_page_config(
        page_title="MFS RAG System",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 MFS Knowledge Assistant")
    st.markdown("Ask questions about your MFS configuration system, order validation, and business processes.")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Sidebar with system info
    with st.sidebar:
        st.header("📊 System Status")
        
        db = get_db_connection()
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                st.success(f"✅ Database: {doc_count} documents")
                cursor.close()
            except Exception as e:
                st.error(f"❌ Database error: {e}")
        else:
            st.error("❌ Database offline")
        
        if os.getenv('OPENAI_API_KEY'):
            st.success("✅ OpenAI connected")
        else:
            st.error("❌ OpenAI not configured")
        
        st.markdown("---")
        st.markdown("**Sample questions:**")
        st.markdown("- What are valid order status values?")
        st.markdown("- Does the system check order existence?")
        st.markdown("- How does configuration validation work?")
        st.markdown("- What business rules exist for orders?")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about MFS configuration, orders, or validation rules..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching MFS documentation..."):
                db = get_db_connection()
                if db and openai_client:
                    # Search for relevant documents
                    relevant_docs = search_documents(prompt, openai_client, db)
                    
                    if relevant_docs:
                        # Build context
                        context = "Relevant information from MFS documentation:\n\n"
                        for i, doc in enumerate(relevant_docs, 1):
                            context += f"{i}. {doc['title']} (similarity: {doc['similarity']:.3f})\n"
                            # Use more content for whiteboard documents, less for others
                            metadata = doc.get('metadata', {}) or {}
                            source_type = metadata.get('source_type', '') if metadata else ''
                            if 'whiteboard' in source_type.lower():
                                content_length = 3000  # More content for whiteboard docs
                            else:
                                content_length = 1000  # Standard content length
                            context += f"{doc['content'][:content_length]}...\n\n"
                    else:
                        context = "No specific MFS documentation found for this query."
                    
                    # Generate response
                    response = generate_response(prompt, context, openai_client)
                    st.markdown(response)
                    
                    # Show sources
                    if relevant_docs:
                        with st.expander("📚 Sources", expanded=False):
                            for doc in relevant_docs[:5]:
                                st.markdown(f"**{doc['title']}** (similarity: {doc['similarity']:.3f})")
                                if doc.get('url'):
                                    st.markdown(f"🔗 [View source]({doc['url']})")
                                st.markdown(f"```\n{doc['content'][:300]}...\n```")
                                st.markdown("---")
                    
                    # Add assistant response to session state
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    error_msg = "System not properly configured. Please check database and OpenAI connections."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()