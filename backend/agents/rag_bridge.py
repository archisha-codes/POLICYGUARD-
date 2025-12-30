# backend/agents/rag_bridge.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rag_prep')))

from semantic_search_demo import semantic_search

def retrieve_relevant_rules(transaction_text):
    # Search for rules relevant to the transaction type
    results = semantic_search(transaction_text)
    
    # Format for LLM Context
    context_string = ""
    for r in results:
        context_string += f"Rule Section: {r['section']}\nText: {r['content']}\n\n"
        
    return context_string