"""
Knowledge Base Agent - LlamaIndex RAG system.
Retrieves answers from telecom documentation using semantic search.
"""


from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
from config.config import config
import os

# Global variables for lazy loading
_query_engine = None
_initialized = False

def _initialize_knowledge_base():
    """Initialize the knowledge base (called only when needed)."""
    global _query_engine, _initialized
    
    if _initialized:
        return _query_engine
    
    # Configure LlamaIndex settings
    Settings.llm = OpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY, temperature=0)
    Settings.embed_model = OpenAIEmbedding(api_key=config.OPENAI_API_KEY)
    
    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    
    # Get or create collection
    try:
        chroma_collection = chroma_client.get_collection("telecom_docs")
    except:
        # If collection doesn't exist, create it and load documents
        chroma_collection = chroma_client.create_collection("telecom_docs")
        
        # Load documents
        if os.path.exists(config.DOCUMENTS_PATH):
            documents = SimpleDirectoryReader(config.DOCUMENTS_PATH).load_data()
            
            # Create vector store and index
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Build index
            VectorStoreIndex.from_documents(
                documents, 
                storage_context=storage_context
            )
    
    # Create vector store from existing collection
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    
    # Create query engine
    _query_engine = index.as_query_engine(similarity_top_k=3)
    _initialized = True
    
    return _query_engine

def process_knowledge_query(query):
    """Run the knowledge retrieval query using LlamaIndex."""
    try:
        # STRICT Semantic Guardrail
        # Use LLM to check if query is telecom-related
        check_prompt = f"""
        Analyze if this query is related to a Telecom Company's services (Billing, Network, Plans, Technical Support, 5G, etc.).
        
        Query: "{query}"
        
        Respond with ONLY "YES" or "NO".
        - YES: If it is about telecom services, bills, network, phones, app, or account.
        - NO: If it is about food, cooking, weather, general knowledge, coding, jokes, or anything else.
        """
        
        # Ensure LLM is initialized
        _initialize_knowledge_base()
        
        # Run check
        relevance = Settings.llm.complete(check_prompt).text.strip().upper()
        
        if "NO" in relevance:
             return "I apologize, but I can only assist with Telecom-related queries (Billing, Network, Plans, Technical Support). I cannot help with other topics."
        
        # Initialize and query knowledge base
        query_engine = _initialize_knowledge_base()
        response = query_engine.query(query)
        
        # Post-process response to ensure Rupee currency
        response_text = str(response)
        # Replace common dollar patterns with Rupees
        import re
        response_text = re.sub(r'\$(\d+)', r'₹\1', response_text)
        
        return response_text
    except Exception as e:
        return f"Error processing knowledge query: {str(e)}"
