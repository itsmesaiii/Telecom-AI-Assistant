"""
Billing Agent - CrewAI implementation with context-aware responses.
Simple queries get short answers, complex queries get detailed analysis.
"""

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from utils.database import db
from config.config import config
import os

# LlamaIndex imports for RAG
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import chromadb

# Initialize RAG for Billing
def _get_billing_knowledge(query):
    """Retrieve relevant info from Billing FAQs."""
    try:
        # Configure settings
        Settings.llm = OpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY, temperature=0)
        Settings.embed_model = OpenAIEmbedding(api_key=config.OPENAI_API_KEY)
        
        # Initialize Chroma client
        chroma_client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        collection_name = "billing_docs"
        
        try:
            chroma_collection = chroma_client.get_collection(collection_name)
        except:
            chroma_collection = chroma_client.create_collection(collection_name)
            # Load specific billing document
            doc_path = os.path.join(config.DOCUMENTS_PATH, "Billing FAQs.txt")
            if os.path.exists(doc_path):
                documents = SimpleDirectoryReader(input_files=[doc_path]).load_data()
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

billing_specialist = Agent(
    role="Billing Specialist",
    goal="Provide helpful, accurate, and detailed billing information to customers",
    backstory="""You are an expert billing analyst for a telecom company.
    
    Your goal is to help customers understand their bills completely.
    
    **GUIDELINES:**
    
    1. **Tone:** Professional, empathetic, and clear.
    2. **Currency:** ALWAYS use Indian Rupees (₹) for all monetary values.
    3. **For Simple Queries:** Provide the requested amount clearly, but also offer a brief, helpful breakdown (e.g., "Your total is ₹500, which includes your plan cost of ₹400 and ₹100 in add-ons.").
    4. **For Complex/High Bill Queries:** 
       - Analyze the data thoroughly.
       - Compare usage against plan limits.
       - Identify specific causes for extra charges.
       - Suggest actionable solutions (e.g., "Upgrade plan", "Use Wi-Fi").
    5. **NO SIGNATURES:** Do NOT end responses with "Best regards", "[Your Name]", "Billing Specialist", or any signature. End with helpful information only.
    
    Never be abrupt. Always aim to resolve the customer's confusion.""",
    verbose=False,
    llm=ChatOpenAI(model="gpt-4o", temperature=0)
)

service_advisor = Agent(
    role="Service Plan Advisor",
    goal="Provide plan recommendations when specifically requested",
    backstory="""You recommend plans ONLY when user explicitly asks for recommendations.
    
    For simple billing questions: Keep response concise, no unsolicited recommendations.""",
    verbose=False,
    llm=ChatOpenAI(model="gpt-4o", temperature=0)
)

def get_customer_billing_details(customer_id):
    """Fetch customer billing data from database
    
    Args:
        customer_id: Unique customer identifier
        
    Returns:
        Tuple of customer and billing details
    """
    sql = """
    SELECT c.name, c.email, c.service_plan_id,
           u.data_used_gb, u.voice_minutes_used, u.sms_count_used,
           u.additional_charges, u.total_bill_amount,
           p.monthly_cost, p.data_limit_gb, p.voice_minutes, p.sms_count
    FROM customers c
    LEFT JOIN customer_usage u ON c.customer_id = u.customer_id
    LEFT JOIN service_plans p ON c.service_plan_id = p.plan_id
    WHERE c.customer_id = ?
    ORDER BY u.billing_period_end DESC
    LIMIT 1;
    """
    row = db.query_one(sql, [customer_id])
    return row

from utils.guardrail import check_telecom_relevance

def process_billing_query(query, customer_id="CUST001"):
    """Process billing query using CrewAI agents with context-awareness
    
    Args:
        query: User's billing question
        customer_id: Customer identifier (default: CUST001 for demo)
        
    Returns:
        AI-generated response tailored to query complexity
    """
    # 1. Semantic Guardrail Check
    is_relevant, rejection_msg = check_telecom_relevance(query)
    if not is_relevant:
        return rejection_msg

    db_data = get_customer_billing_details(customer_id)
    
    if not db_data:
        return "Could not find billing records for this customer."
    
    billing_dict = {
        "name": db_data[0],
        "email": db_data[1],
        "service_plan_id": db_data[2],
        "data_used_gb": db_data[3],
        "voice_minutes_used": db_data[4],
        "sms_count_used": db_data[5],
        "additional_charges": db_data[6],
        "total_bill_amount": db_data[7],
        "monthly_cost": db_data[8],
        "data_limit_gb": db_data[9],
        "voice_minutes": db_data[10],
        "sms_count": db_data[11]
    }
    
    # Get relevant knowledge from FAQs
    knowledge_context = _get_billing_knowledge(query)
    
    # Detect query type for context-aware response
    query_lower = query.lower()
    
    # Keywords that indicate a request for explanation/analysis (Complex)
    complex_keywords = ["why", "explain", "reason", "break down", "analyze", "details", "high", "expensive", "tax", "fee", "charge"]
    is_complex = any(keyword in query_lower for keyword in complex_keywords)
    
    # Keywords for simple status checks
    simple_keywords = [
        "what's my bill", "whats my bill", "how much", "bill amount", 
        "what do i owe", "current bill", "total bill"
    ]
    
    # It's simple ONLY if it matches simple keywords AND doesn't have complex ones
    is_simple_query = any(keyword in query_lower for keyword in simple_keywords) and not is_complex
    
    if is_simple_query:
        task_desc = f"""Customer asked: "{query}"
        
This is a SIMPLE query asking for bill amount.

Provide a CLEAR, HELPFUL response:
1. State the Total Bill Amount: ₹{billing_dict['total_bill_amount']}
2. Provide a quick breakdown: Base Plan (₹{billing_dict['monthly_cost']}) + Additional Charges (₹{billing_dict['additional_charges']})
3. Be polite and professional.

Data: {billing_dict}"""
    else:
        task_desc = f"""Customer asked: "{query}"

This is a DETAILED query requiring analysis.

Provide a COMPREHENSIVE explanation:
1. Start with the total bill amount: ₹{billing_dict['total_bill_amount']}
2. Compare usage vs plan limits:
   - Data: {billing_dict['data_used_gb']}GB used vs {billing_dict['data_limit_gb']}GB limit
   - Voice: {billing_dict['voice_minutes_used']} mins used vs {billing_dict['voice_minutes']} limit
   - SMS: {billing_dict['sms_count_used']} used vs {billing_dict['sms_count']} limit
3. EXPLICITLY identify what caused extra charges (if any):
   - Additional Charges: ₹{billing_dict['additional_charges']}
   - Base Plan Cost: ₹{billing_dict['monthly_cost']}
4. Explain WHY the bill is high (e.g., "You exceeded your data limit by X GB").
5. Suggest a solution (e.g., "Consider upgrading to a higher data plan").

**RELEVANT KNOWLEDGE BASE INFO:**
{knowledge_context}
(Use this info to explain taxes, fees, or policies if relevant)

Data: {billing_dict}"""
    
    billing_task = Task(
        description=task_desc,
        agent=billing_specialist,
        expected_output="Contextual response matching query complexity"
    )
    
    crew = Crew(
        agents=[billing_specialist],
        tasks=[billing_task],
        verbose=False
    )
    
    result = crew.kickoff(inputs={"query": query, "billing_data": billing_dict})
    return str(result)
