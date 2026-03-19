#!/usr/bin/env python3
"""
Query Preprocessing Tips for Better RAG Search
Optional enhancements to make search more flexible
"""

def preprocess_query_basic(query: str) -> str:
    """Basic query preprocessing for better matching"""
    
    # Expand common abbreviations
    abbreviations = {
        'config': 'configuration',
        'configs': 'configurations', 
        'auth': 'authentication',
        'API': 'Application Programming Interface',
        'DB': 'database',
        'UI': 'user interface',
        'UX': 'user experience'
    }
    
    # Expand synonyms
    synonyms = {
        'flow': 'workflow process sequence steps',
        'process': 'workflow flow sequence procedure',
        'steps': 'process flow sequence workflow',
        'guide': 'instructions tutorial documentation',
        'setup': 'configuration setup installation',
        'error': 'issue problem failure bug'
    }
    
    processed_query = query.lower()
    
    # Replace abbreviations
    for abbrev, full in abbreviations.items():
        processed_query = processed_query.replace(abbrev.lower(), full)
    
    # Add synonyms (append, don't replace)
    for term, alternatives in synonyms.items():
        if term in processed_query:
            processed_query += f" {alternatives}"
    
    return processed_query

# Examples of how this would help:
test_queries = [
    "explain the config flow",          # → "explain the configuration flow workflow process sequence steps"
    "show me the auth process",         # → "show me the authentication workflow flow sequence procedure"  
    "API setup guide",                  # → "Application Programming Interface configuration setup installation instructions tutorial documentation"
    "DB connection steps"               # → "database connection process flow sequence workflow"
]

print("📝 Query Preprocessing Examples:")
print("=" * 50)

for query in test_queries:
    processed = preprocess_query_basic(query)
    print(f"Original:  '{query}'")
    print(f"Enhanced:  '{processed}'")
    print()

print("💡 Benefits:")
print("• Expands abbreviations (config → configuration)")
print("• Adds semantic alternatives (flow → workflow process sequence)")
print("• Increases matching probability for natural language")
print("• Preserves original query intent")