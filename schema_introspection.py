"""
Database Schema Introspection Utility for NL to SQL Agent.
Extracts database schema information from a PostgreSQL database.
"""

import psycopg2
from typing import Dict, List, Optional

class SchemaIntrospection:
    """Extracts database schema information."""

    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def get_tables(self) -> List[str]:
        """Get all table names in public schema."""
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a specific table."""
        query = f"""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        self.cursor.execute(query)
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3]
            })
        return columns
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """Get foreign key relationships for a table"""
        query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s;
        """
        self.cursor.execute(query, (table_name,))
        fkeys = []
        for row in self.cursor.fetchall():
            fkeys.append({
                'column': row[0],
                'references_table': row[1],
                'references_column': row[2]
            })
        return fkeys

    def get_sample_data(self, table_name: str, limit: int = 2) -> List[tuple]:
        """Get sample rows from a table"""
        query = f"SELECT * FROM {table_name} LIMIT %s;"
        self.cursor.execute(query, (limit,))
        return self.cursor.fetchall()
    
    def get_full_schema_context(self) -> str:
        """Generate complete schema context for LLM"""
        schema_parts = []
        schema_parts.append("DATABASE SCHEMA INFORMATION")
        schema_parts.append("=" * 80)
        schema_parts.append("")
        
        tables = self.get_tables()
        
        for table in tables:
            schema_parts.append(f"\nTABLE: {table}")
            schema_parts.append("-" * 80)
            
            # Columns
            columns = self.get_table_columns(table)
            schema_parts.append("Columns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f", DEFAULT: {col['default']}" if col['default'] else ""
                schema_parts.append(f"  - {col['name']} ({col['type']}, {nullable}{default})")
            
            # Foreign Keys
            fkeys = self.get_foreign_keys(table)
            if fkeys:
                schema_parts.append("\nForeign Keys:")
                for fk in fkeys:
                    schema_parts.append(
                        f"  - {fk['column']} → {fk['references_table']}.{fk['references_column']}"
                    )
            
            # Sample data
            try:
                sample_data = self.get_sample_data(table, limit=1)
                if sample_data:
                    schema_parts.append("\nSample Data (1 row):")
                    col_names = [col['name'] for col in columns]
                    schema_parts.append(f"  Columns: {', '.join(col_names)}")
                    schema_parts.append(f"  Sample: {sample_data[0]}")
            except Exception as e:
                schema_parts.append(f"\nSample Data: Unable to fetch ({str(e)})")
            
            schema_parts.append("")
        
        # Add relationship summary
        schema_parts.append("\n" + "=" * 80)
        schema_parts.append("RELATIONSHIP SUMMARY")
        schema_parts.append("=" * 80)
#         schema_parts.append("""
# Key Relationships:
# - customers → orders (one customer can have many orders)
# - customers → shipping_addresses (one customer can have many addresses)
# - customers → payment_methods (one customer can have many payment methods)
# - orders → order_items (one order can have many items)
# - orders → payment_transactions (one order can have many transactions)
# - shipping_addresses → orders (one address can be used for many orders)
# - payment_methods → orders (one payment method can be used for many orders)
# """)
        
        return "\n".join(schema_parts)

    def get_table_summary(self) -> str:
        """Get a brief summary of all tables"""
        tables = self.get_tables()
        summary = ["Available Tables:"]
        for table in tables:
            columns = self.get_columns(table)
            summary.append(f"  - {table} ({len(columns)} columns)")
        return "\n".join(summary)

if __name__ == "__main__":
    # Test the schema introspector
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    
    introspector = SchemaIntrospection(conn)
    print(introspector.get_full_schema_context())
    
    conn.close()
    
        

    
    
    