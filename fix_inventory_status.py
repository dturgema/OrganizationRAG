#!/usr/bin/env python3
"""
Fix Inventory Status Information
Add correct inventory statuses to distinguish from order statuses
"""

import os
import requests
import psycopg2
import json
import hashlib
import time

def get_embedding(text: str, api_key: str):
    """Get OpenAI embedding"""
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-embedding-ada-002",
        "input": text
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    return result["data"][0]["embedding"]

def main():
    print("🛠️ Fixing Inventory Status Information")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    # Connect to database
    conn = psycopg2.connect(
        host='rag-pgvector-openai',
        port=5432,
        database='ragdb',
        user='raguser',
        password='ragpassword'
    )
    cursor = conn.cursor()
    
    # Create clear inventory status documentation
    inventory_content = """MFS Inventory Status Values - Official Reference

🏭 INVENTORY STATUS DEFINITIONS:

The MFS system uses the following standardized inventory status values:

INVENTORY STATUS VALUES:
• AVAILABLE - Item is in stock and ready for use
• RESERVED - Item is allocated but not yet consumed  
• OUT_OF_STOCK - Item is temporarily unavailable
• DISCONTINUED - Item is no longer carried
• PENDING_RECEIPT - Item is ordered but not yet received
• DAMAGED - Item exists but is not usable
• ON_HOLD - Item is temporarily suspended from use

⚠️ IMPORTANT DISTINCTION:
These are INVENTORY statuses (for items/products), which are completely different from:
- ORDER statuses (Open, Closed, Draft) - which apply to orders/transactions
- CONFIGURATION statuses - which apply to system configurations

BUSINESS RULES:
✅ AVAILABLE items can be allocated to new orders
✅ RESERVED items are committed but can be released if needed  
✅ OUT_OF_STOCK items trigger automatic reorder processes
✅ DISCONTINUED items cannot be ordered but existing stock can be used
✅ PENDING_RECEIPT items are tracked for incoming shipments
✅ DAMAGED items require quality assessment before disposal
✅ ON_HOLD items require manager approval before release

INTEGRATION POINTS:
- Order processing checks inventory status before allocation
- Configuration system validates inventory availability  
- Reporting systems aggregate by inventory status
- Workflow automation triggers based on status changes

This information is specific to INVENTORY management and should not be confused with order statuses or other system statuses."""
    
    print("📝 Creating inventory status reference document...")
    
    # Generate embedding
    embedding = get_embedding(inventory_content, api_key)
    
    # Store in database
    content_id = hashlib.md5("mfs_inventory_statuses_official".encode()).hexdigest()
    
    cursor.execute("""
        INSERT INTO documents (content_id, title, content, url, source_type, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (content_id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            metadata = EXCLUDED.metadata
    """, (
        content_id,
        "MFS Inventory Status Values - Official Reference",
        inventory_content,
        "https://doront.atlassian.net/wiki/spaces/MFS/inventory-statuses",
        "mfs_inventory_status_reference",
        embedding,
        json.dumps({
            'content_type': 'inventory_status_definitions',
            'priority': 'high',
            'created_at': time.time(),
            'purpose': 'fix_inventory_status_confusion'
        })
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Inventory status reference document created!")
    print("🔍 This will help distinguish inventory statuses from order statuses")
    print("\n💡 Test with: 'What are the optional inventory statuses?'")
    print("   Expected: AVAILABLE, RESERVED, OUT_OF_STOCK, etc.")

if __name__ == "__main__":
    main()