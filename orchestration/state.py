"""
LangGraph State - Defines data structure passed between graph nodes.
Tracks query, classification, responses, and customer context.
"""


from typing import TypedDict, Dict, Any, List

class TelecomState(TypedDict, total=False):
    query: str
    classification: str
    intermediate_responses: Dict[str, Any]
    final_response: str
    customer_info: Dict[str, Any]
    chat_history: List[Dict[str, str]]
