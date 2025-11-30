"""
Billing Agent - CrewAI implementation with context-aware responses.
Simple queries get short answers, complex queries get detailed analysis.
"""

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from utils.database import db

billing_specialist = Agent(
    role="Billing Specialist",
    goal="Provide CONCISE, DIRECT answers that match the user's question complexity",
    backstory="""You are an expert billing analyst who provides contextual responses.
    
    **CRITICAL INSTRUCTIONS:**
    
    For SIMPLE queries like "What's my bill?" or "How much do I owe?":
    - Give a SHORT, DIRECT answer with the bill amount
    - Simple breakdown: Base plan + extras = total
    - MAX 4-5 lines
    
    For DETAILED queries like "Why is my bill high?" or "Analyze my bill":
    - Provide detailed analysis
    - Explain charges and usage patterns
    - Suggest optimizations if appropriate
    
    ALWAYS match response length to question complexity!
    Simple question = Simple answer""",
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

def process_billing_query(query, customer_id="CUST001"):
    """Process billing query using CrewAI agents with context-awareness
    
    Args:
        query: User's billing question
        customer_id: Customer identifier (default: CUST001 for demo)
        
    Returns:
        AI-generated response tailored to query complexity
    """
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
    
    # Detect query type for context-aware response
    query_lower = query.lower()
    is_simple_query = any(keyword in query_lower for keyword in [
        "what's my bill", "whats my bill", "how much", "bill amount", 
        "what do i owe", "current bill", "this month"
    ])
    
    if is_simple_query:
        task_desc = f"""Customer asked: "{query}"

This is a SIMPLE query asking for bill amount.

Provide a SHORT, DIRECT response:
1. Total bill amount: ${billing_dict['total_bill_amount']}
2. Brief breakdown (base + extras)
3. MAX 5 lines total

DO NOT provide lengthy analysis!

Data: {billing_dict}"""
    else:
        task_desc = f"""Customer asked: "{query}"

Provide thorough billing analysis.

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

