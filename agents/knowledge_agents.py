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
        query_engine = _initialize_knowledge_base()
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        return f"Error processing knowledge query: {str(e)}"
