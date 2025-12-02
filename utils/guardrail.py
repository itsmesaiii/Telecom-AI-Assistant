"""
Semantic Guardrail Utility
Uses LLM to verify if a query is relevant to the Telecom domain.
"""

from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from config.config import config

def check_telecom_relevance(query):
    """
    Checks if the query is related to telecom services using an LLM.
    Returns:
        bool: True if relevant, False if not.
        str: Rejection message if not relevant.
    """
    try:
        # Ensure LLM is configured
        if not Settings.llm:
            Settings.llm = OpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY, temperature=0)
            
        check_prompt = f"""
        Analyze if this query is related to a Telecom Company's services (Billing, Network, Plans, Technical Support, 5G, Account, etc.).
        
        Query: "{query}"
        
        Respond with ONLY "YES" or "NO".
        - YES: If it is about telecom services, bills, network, phones, app, account, or even if it's a vague request that COULD be telecom (e.g., "help me", "not working").
        - NO: If it is clearly about food, cooking, weather, general knowledge, coding, jokes, or anything else unrelated.
        """
        
        relevance = Settings.llm.complete(check_prompt).text.strip().upper()
        
        if "NO" in relevance:
            return False, "I apologize, but I can only assist with Telecom-related queries (Billing, Network, Plans, Technical Support). I cannot help with other topics."
            
        return True, ""
        
    except Exception as e:
        # If check fails, default to allowing (fail open) to avoid blocking valid queries due to errors
        return True, ""
