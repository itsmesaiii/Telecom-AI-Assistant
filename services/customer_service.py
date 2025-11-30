"""
Customer Service Module
Handles database interactions for fetching customer profile and usage data.
"""

from utils.database import db

def get_customer_profile(email):
    """
    Fetch customer profile and plan details by email.
    Falls back to demo account (CUST001) if email not found.
    """
    # 1. Get Customer ID
    email_query = "SELECT customer_id FROM customers WHERE email = ?"
    result = db.query_one(email_query, [email])
    customer_id = result[0] if result else "CUST001"
    
    # 2. Fetch Profile + Plan
    customer_query = """
    SELECT c.customer_id, c.name, c.email, c.phone_number, c.address, 
           c.account_status, c.registration_date, c.last_billing_date,
           p.name, p.monthly_cost, p.data_limit_gb, 
           p.voice_minutes, p.sms_count, p.unlimited_data, p.unlimited_voice, p.unlimited_sms
    FROM customers c
    LEFT JOIN service_plans p ON c.service_plan_id = p.plan_id
    WHERE c.customer_id = ?
    """
    customer_data = db.query_one(customer_query, [customer_id])
    
    return customer_id, customer_data

def get_usage_history(customer_id):
    """
    Fetch last 6 months of usage history for a customer.
    """
    usage_query = """
    SELECT billing_period_start, billing_period_end, 
           data_used_gb, voice_minutes_used, sms_count_used,
           additional_charges, total_bill_amount
    FROM customer_usage
    WHERE customer_id = ?
    ORDER BY billing_period_end DESC LIMIT 6
    """
    return db.query(usage_query, [customer_id])
