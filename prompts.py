"""
Prompt Templates for NL to SQL Conversion
Contains base prompts and few-shot examples
"""


FEW_SHOT_EXAMPLES = """
EXAMPLE QUERIES AND THEIR SQL:

Example 1 - Simple Count:
Question: "How many customers do we have?"
SQL: SELECT COUNT(*) as total_customers FROM customers;

Example 2 - Basic Select with Filter:
Question: "Show me all orders from today"
SQL: SELECT * FROM orders WHERE DATE(order_date) = CURRENT_DATE;

Example 3 - Join with Aggregation:
Question: "Who are the top 5 customers by spending?"
SQL: 
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    c.email,
    SUM(o.total) as total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY total_spent DESC
LIMIT 5;

Example 4 - Multiple Joins:
Question: "Show me orders with customer names and shipping addresses"
SQL:
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name as customer_name,
    sa.city,
    sa.state,
    o.total,
    o.order_date
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN shipping_addresses sa ON o.shipping_address_id = sa.address_id
ORDER BY o.order_date DESC
LIMIT 20;

Example 5 - Group By with Having:
Question: "Which cities have more than 2 orders?"
SQL:
SELECT 
    sa.city,
    sa.state,
    COUNT(o.order_id) as order_count
FROM orders o
JOIN shipping_addresses sa ON o.shipping_address_id = sa.address_id
GROUP BY sa.city, sa.state
HAVING COUNT(o.order_id) > 2
ORDER BY order_count DESC;

Example 6 - Date Range Filter:
Question: "Orders from last week"
SQL:
SELECT * FROM orders 
WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY order_date DESC;

Example 7 - Status Filter:
Question: "How many pending orders?"
SQL:
SELECT COUNT(*) as pending_orders 
FROM orders 
WHERE order_status = 'pending';

Example 8 - Aggregation by Category:
Question: "Average order value by payment type"
SQL:
SELECT 
    pm.payment_type,
    COUNT(o.order_id) as order_count,
    AVG(o.total) as avg_order_value,
    SUM(o.total) as total_revenue
FROM orders o
JOIN payment_methods pm ON o.payment_method_id = pm.payment_method_id
GROUP BY pm.payment_type
ORDER BY total_revenue DESC;

Example 9 - Complex Join with Order Items:
Question: "What are the most ordered products?"
SQL:
SELECT 
    oi.product_name,
    SUM(oi.quantity) as total_quantity,
    COUNT(DISTINCT oi.order_id) as order_count
FROM order_items oi
GROUP BY oi.product_name
ORDER BY total_quantity DESC
LIMIT 10;

Example 10 - Time-based Comparison:
Question: "Compare this month vs last month sales"
SQL:
SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as order_count,
    SUM(total) as total_sales
FROM orders
WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;
"""


def get_base_prompt(schema_context: str) -> str:
    """
    Generate base prompt for SQL generation
    
    Args:
        schema_context: Database schema information
        
    Returns:
        Complete prompt template
    """
    prompt = f"""You are an expert PostgreSQL database assistant. Your task is to convert natural language questions into valid PostgreSQL SQL queries.

{schema_context}

IMPORTANT RULES:
1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
2. Always use proper table aliases for readability
3. Use appropriate JOINs when querying multiple tables
4. Format dates correctly for PostgreSQL (use DATE(), CURRENT_DATE, INTERVAL, etc.)
5. Handle NULL values appropriately
6. Add reasonable LIMIT clauses (default: 100) unless user specifies otherwise
7. Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) when appropriate
8. Include ORDER BY for better readability when relevant
9. Use DISTINCT when needed to avoid duplicates
10. Always use proper column names from the schema above

DATE/TIME HANDLING:
- Today: DATE(column_name) = CURRENT_DATE
- Yesterday: DATE(column_name) = CURRENT_DATE - INTERVAL '1 day'
- Last 7 days: column_name >= CURRENT_DATE - INTERVAL '7 days'
- This month: DATE_TRUNC('month', column_name) = DATE_TRUNC('month', CURRENT_DATE)
- Last month: DATE_TRUNC('month', column_name) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')

{FEW_SHOT_EXAMPLES}

RESPONSE FORMAT:
- Return ONLY the SQL query
- Do NOT include explanations, comments, or markdown formatting
- Do NOT wrap in ```sql``` code blocks
- End with a semicolon

Now, convert the following question to SQL:"""
    
    return prompt


def get_error_recovery_prompt(schema_context: str, user_query: str, previous_sql: str, error_message: str) -> str:
    """
    Generate prompt for error recovery
    
    Args:
        schema_context: Database schema information
        user_query: Original user query
        previous_sql: SQL that failed
        error_message: Error message from database
        
    Returns:
        Error recovery prompt
    """
    prompt = f"""You are an expert PostgreSQL database assistant. A previous SQL query failed and needs to be fixed.

{schema_context}

ORIGINAL USER QUESTION:
{user_query}

PREVIOUS SQL (FAILED):
{previous_sql}

ERROR MESSAGE:
{error_message}

Please generate a corrected SQL query that:
1. Fixes the error mentioned above
2. Still answers the original user question
3. Follows all the same rules as before (SELECT only, proper JOINs, etc.)

Return ONLY the corrected SQL query, no explanations."""
    
    return prompt


def get_clarification_prompt(schema_context: str, user_query: str, ambiguity: str) -> str:
    """
    Generate prompt when query is ambiguous
    
    Args:
        schema_context: Database schema information
        user_query: User's ambiguous query
        ambiguity: Description of what's ambiguous
        
    Returns:
        Clarification request
    """
    return f"""The query "{user_query}" is ambiguous because: {ambiguity}

Please clarify:
- Which specific table or data are you asking about?
- What time range should be included?
- How should the results be sorted?

Available tables: customers, orders, order_items, shipping_addresses, payment_methods, payment_transactions"""


# Common query patterns for quick reference
QUERY_PATTERNS = {
    'count': 'SELECT COUNT(*) FROM {table}',
    'top_n': 'SELECT * FROM {table} ORDER BY {column} DESC LIMIT {n}',
    'group_by': 'SELECT {column}, COUNT(*) FROM {table} GROUP BY {column}',
    'join': 'SELECT * FROM {table1} t1 JOIN {table2} t2 ON t1.{key} = t2.{key}',
    'date_filter': 'SELECT * FROM {table} WHERE DATE({date_column}) = CURRENT_DATE',
}


def get_narrative_prompt(natural_query: str, sql: str, results: list, column_names: list, row_count: int) -> str:
    """
    Generate prompt for natural language summary of query results
    
    Args:
        natural_query: Original user question
        sql: Executed SQL query
        results: Query results (limited to first 20 rows)
        column_names: Column names
        row_count: Total number of rows returned
        
    Returns:
        Prompt for narrative generation
    """
    # Format results as a readable table
    results_text = ""
    if results:
        # Header
        results_text += " | ".join(column_names) + "\n"
        results_text += "-" * (len(column_names) * 15) + "\n"
        
        # Rows (limit to first 20)
        for row in results[:20]:
            results_text += " | ".join(str(val) if val is not None else "NULL" for val in row) + "\n"
        
        if row_count > 20:
            results_text += f"\n... ({row_count - 20} more rows not shown)\n"
    
    prompt = f"""You are a friendly data analyst. A user asked a question about their database, and a SQL query was executed. Please provide a brief, natural language summary of the results.

USER'S QUESTION:
{natural_query}

SQL EXECUTED:
{sql}

RESULTS ({row_count} total rows):
{results_text if results else "No results found."}

INSTRUCTIONS:
1. Write a concise 1-2 sentence summary in a friendly, conversational tone
2. Include the key numbers or insights from the results
3. Use "you have" or "your database contains" phrasing
4. If no results, say "No records found matching your query."
5. For counts/aggregates, emphasize the number
6. For lists, mention "Found X records" and highlight top items
7. Do NOT just repeat the table data
8. Do NOT include technical jargon

EXAMPLE SUMMARIES:
- "Your database currently has **1,250 customers**."
- "Found **15 orders** from last week, with a total value of **$4,532**."
- "The top product by sales is **'Premium Widget'** with 342 units sold."
- "No orders found matching those criteria."

Now, write a natural lang summary (1-2 sentences max):"""
    
    return prompt


if __name__ == "__main__":
    # Test prompt generation
    sample_schema = "TABLE: customers\n- customer_id (INTEGER)\n- first_name (VARCHAR)\n- last_name (VARCHAR)"
    prompt = get_base_prompt(sample_schema)
    print(prompt)
    print("\n" + "=" * 80)
    print("Prompt length:", len(prompt), "characters")