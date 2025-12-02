"""
Network Agent - AutoGen multi-agent troubleshooting system.
Checks account status first, then provides diagnostics or reactivation guidance.
"""

import autogen
from utils.database import db
from config.config import config
import os

# LlamaIndex imports for RAG
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import chromadb

# Initialize RAG for Network
def _get_network_knowledge(query):
    """Retrieve relevant info from Network Troubleshooting Guides."""
    try:
        # Configure settings
        Settings.llm = OpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY, temperature=0)
        Settings.embed_model = OpenAIEmbedding(api_key=config.OPENAI_API_KEY)
        
        # Initialize Chroma client
        chroma_client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        collection_name = "network_docs"
        
        try:
            chroma_collection = chroma_client.get_collection(collection_name)
        except:
            chroma_collection = chroma_client.create_collection(collection_name)
            # Load specific network documents
            docs_to_load = ["Network_Troubleshooting_Guide.txt", "Technical Support Guide.txt"]
            file_paths = []
            for doc in docs_to_load:
                path = os.path.join(config.DOCUMENTS_PATH, doc)
                if os.path.exists(path):
                    file_paths.append(path)
            
            if file_paths:
                documents = SimpleDirectoryReader(input_files=file_paths).load_data()
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        
        # Query
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store)
        query_engine = index.as_query_engine(similarity_top_k=2)
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        return "" # Fail silently if RAG fails

# Define network troubleshooting agents with database context
config_list = [{"model": "gpt-4o", "api_key": config.OPENAI_API_KEY}]

Diagnostics_Agent = autogen.AssistantAgent(
    name="Diagnostics_Agent",
    system_message="""You are a telecom MOBILE network diagnostics specialist. 

CRITICAL INSTRUCTION: You will receive customer information including their account status.

**IMPORTANT CONTEXT:** This is a MOBILE telecom company. Issues are about MOBILE calls, mobile data, and SMS - NOT home internet, Wi-Fi routers, or modems.

**CHECK ACCOUNT STATUS FIRST:**
- If account status is "Suspended" or "Cancelled":
  → IMMEDIATELY inform the customer their account is suspended/cancelled
  → Explain this is WHY they can't make calls/use mobile data/send SMS
  → Tell them to contact billing/customer service to reactivate
  → DO NOT provide generic network troubleshooting
  
- If account status is "Active":
  → Proceed with MOBILE network diagnostic steps
  → Check MOBILE signal strength, SIM card, APN settings, mobile data toggle
  → DO NOT mention routers, modems, or Wi-Fi unless customer asks about Wi-Fi calling

Always prioritize account status before any other troubleshooting!""",
    llm_config={"config_list": config_list, "temperature": 0.7}
)

Solution_Integrator = autogen.AssistantAgent(
    name="Solution_Integrator",
    system_message="""You are a MOBILE network solution integrator providing final solutions.

Based on the diagnostics:
- If account is suspended → Provide clear steps to reactivate account
- If MOBILE network issue → Provide step-by-step troubleshooting for MOBILE connectivity (SIM card, mobile signal, APN settings, mobile data toggle)
- Be concise and actionable
- ALWAYS provide a helpful response based on diagnostics - NEVER say "I can't assist with that" """,
    llm_config={"config_list": config_list, "temperature": 0.7}
)

user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
    code_execution_config=False
)

# Setup group chat
groupchat = autogen.GroupChat(
    agents=[user_proxy, Diagnostics_Agent, Solution_Integrator],
    messages=[],
    max_round=6
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})

from utils.guardrail import check_telecom_relevance

def process_network_query(query, customer_email="user@example.com"):
    """Run the AutoGen network troubleshooting flow with customer context."""
    
    # 1. Semantic Guardrail Check
    is_relevant, rejection_msg = check_telecom_relevance(query)
    if not is_relevant:
        return rejection_msg
    
    # Get customer info from database
    try:
        customer_query = """
        SELECT c.customer_id, c.name, c.account_status, c.service_plan_id,
               p.name as plan_name
        FROM customers c
        LEFT JOIN service_plans p ON c.service_plan_id = p.plan_id
        WHERE c.email = ?
        """
        customer_data = db.query_one(customer_query, [customer_email])
        
        if customer_data:
            customer_context = f"""
CUSTOMER INFORMATION (CHECK THIS FIRST!):
- Customer Name: {customer_data[1]}
- Account Status: {customer_data[2]} ← **CRITICAL: Check this first!**
- Current Plan: {customer_data[4]}
"""
        else:
            # Email not found in database
            if customer_email:
                return f"I'm sorry, but the email '{customer_email}' is not registered in our system. Please contact customer service to verify your account details."
            else:
                return "I'm sorry, but I couldn't identify your account. Please make sure you're logged in with a valid email address."
    except Exception as e:
        customer_context = f"Error fetching customer data: {str(e)}\nProceeding with generic troubleshooting."
    
    # Get relevant knowledge from Troubleshooting Guides
    knowledge_context = _get_network_knowledge(query)
    
    # Reset chat history
    groupchat.messages = []
    
    # Initiate chat with customer context
    chat_result = user_proxy.initiate_chat(
        manager,
        message=f"""{customer_context}

Customer Issue: {query}

**RELEVANT TECHNICAL KNOWLEDGE:**
{knowledge_context}
(Use this technical info for troubleshooting steps if relevant)

IMPORTANT INSTRUCTIONS:
1. READ the account status above CAREFULLY
2. If account is Suspended/Cancelled → Address this IMMEDIATELY as the root cause
3. If account is Active → Then proceed with network diagnostics using the technical knowledge above
4. End your final response with TERMINATE"""
    )
    
    # Extract the final response
    if chat_result.chat_history:
        agent_messages = [m for m in chat_result.chat_history if m['name'] != 'User_Proxy']
        if agent_messages:
            last_msg = agent_messages[-1]['content']
            return last_msg.replace("TERMINATE", "").strip()
    
    return "I'm sorry, I couldn't diagnose the network issue at this time."
