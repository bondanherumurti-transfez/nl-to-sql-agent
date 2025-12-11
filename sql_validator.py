"""
SQL Validator - Ensures only safe SELECT queries are executed
"""

import re
from typing import Tuple, List


class SQLValidator:
    """Validate SQL queries for safety"""
    
    # Dangerous SQL keywords that should not be allowed
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE',
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE',
        'EXEC', 'CALL', 'REPLACE'
    ]
    
    # Allowed keywords for SELECT queries
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 
        'RIGHT', 'OUTER', 'ON', 'GROUP', 'BY', 'HAVING',
        'ORDER', 'LIMIT', 'OFFSET', 'AS', 'AND', 'OR',
        'IN', 'NOT', 'LIKE', 'BETWEEN', 'IS', 'NULL',
        'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'CAST',
        'COALESCE', 'NULLIF', 'DATE', 'CURRENT_DATE',
        'CURRENT_TIMESTAMP', 'NOW', 'EXTRACT', 'DATE_TRUNC'
    ]
    
    @staticmethod
    def is_safe_query(sql: str) -> Tuple[bool, str]:
        """
        Check if SQL query is safe to execute
        
        Args:
            sql: SQL query string
            
        Returns:
            Tuple of (is_safe: bool, message: str)
        """
        if not sql or not sql.strip():
            return False, "Empty query"
        
        # Remove comments
        sql_clean = SQLValidator._remove_comments(sql)
        
        # Convert to uppercase for keyword checking
        sql_upper = sql_clean.upper()
        
        # Check for dangerous keywords
        for keyword in SQLValidator.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Dangerous keyword detected: {keyword}"
        
        # Must start with SELECT
        if not sql_upper.strip().startswith('SELECT'):
            return False, "Query must start with SELECT"
        
        # Check for semicolons (multiple statements)
        # Allow one semicolon at the end, but not multiple
        semicolon_count = sql_clean.count(';')
        if semicolon_count > 1:
            return False, "Multiple statements not allowed"
        
        # Check for common SQL injection patterns
        injection_patterns = [
            r';\s*--',  # Comment after semicolon
            r'--\s*[^\n]*;\s*',  # Semicolon in comment
            r'\/\*.*\*\/.*;\s*',  # Semicolon in block comment
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_clean, re.IGNORECASE):
                return False, "Potential SQL injection pattern detected"
        
        return True, "Query is safe"
    
    @staticmethod
    def _remove_comments(sql: str) -> str:
        """Remove SQL comments from query"""
        # Remove single-line comments (-- comment)
        sql = re.sub(r'--[^\n]*', '', sql)
        
        # Remove multi-line comments (/* comment */)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        return sql
    
    @staticmethod
    def add_limit_if_missing(sql: str, default_limit: int = 100) -> str:
        """
        Add LIMIT clause if not present
        
        Args:
            sql: SQL query string
            default_limit: Default limit to add
            
        Returns:
            SQL query with LIMIT clause
        """
        sql_upper = sql.upper()
        
        # Check if LIMIT already exists
        if 'LIMIT' in sql_upper:
            return sql
        
        # Remove trailing semicolon if present
        sql = sql.rstrip(';').strip()
        
        # Add LIMIT
        sql_with_limit = f"{sql} LIMIT {default_limit};"
        
        return sql_with_limit
    
    @staticmethod
    def clean_sql(sql: str) -> str:
        """
        Clean and format SQL query
        
        Args:
            sql: Raw SQL query
            
        Returns:
            Cleaned SQL query
        """
        # Remove markdown code blocks if present
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove extra whitespace
        sql = ' '.join(sql.split())
        
        # Ensure ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        return sql


def test_validator():
    """Test the SQL validator"""
    test_cases = [
        # Safe queries
        ("SELECT * FROM customers;", True),
        ("SELECT name, email FROM customers WHERE id = 1;", True),
        ("SELECT COUNT(*) FROM orders;", True),
        ("""
            SELECT c.first_name, COUNT(o.order_id) 
            FROM customers c 
            LEFT JOIN orders o ON c.customer_id = o.customer_id 
            GROUP BY c.first_name;
        """, True),
        
        # Unsafe queries
        ("DROP TABLE customers;", False),
        ("DELETE FROM orders WHERE id = 1;", False),
        ("UPDATE customers SET name = 'test';", False),
        ("INSERT INTO customers VALUES (1, 'test');", False),
        ("SELECT * FROM customers; DROP TABLE orders;", False),
        ("", False),
    ]
    
    print("Testing SQL Validator...")
    print("=" * 80)
    
    for sql, expected_safe in test_cases:
        is_safe, message = SQLValidator.is_safe_query(sql)
        status = "✓" if is_safe == expected_safe else "✗"
        print(f"\n{status} Query: {sql[:50]}...")
        print(f"   Expected: {'Safe' if expected_safe else 'Unsafe'}")
        print(f"   Result: {'Safe' if is_safe else 'Unsafe'} - {message}")


if __name__ == "__main__":
    test_validator()