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
    
    
    def load_config(self) -> Dict:
        """Load configuration from schema_config.json if it exists"""
        import json
        import os
        
        config = {
            "relationships": [],
            "enums": {}
        }
        config_path = "schema_config.json"
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_data = json.load(f)
                    
                    # Handle new format vs legacy format (if any legacy format existed, but we deleted it)
                    # Support new structured format
                    if "relationships" in file_data:
                        config["relationships"] = file_data["relationships"]
                    if "enums" in file_data:
                        config["enums"] = file_data["enums"]
                        
                    # Support flat list (fallback/legacy) - unlikely needed but safe 
                    if isinstance(file_data, list):
                        config["relationships"] = file_data
                        
            except Exception as e:
                print(f"Warning: Failed to load schema config: {e}")
                
        return config

    def get_configured_relationships(self) -> List[str]:
        """Get relationships from config"""
        config = self.load_config()
        relationships = []
        for item in config["relationships"]:
            if 'source' in item and 'target' in item and 'description' in item:
                relationships.append(
                    f"- {item['source']} → {item['target']} ({item['description']})"
                )
        return relationships
        
    def get_column_enums(self, table: str, column: str) -> Optional[List[str]]:
        """Get enum values for a column if defined in config"""
        config = self.load_config()
        enums = config.get("enums", {})
        table_enums = enums.get(table, {})
        return table_enums.get(column)

    def generate_relationship_summary(self) -> str:
        """Generate relationship summary from DB FKs and Config"""
        relationships = set()
        
        # 1. Load from Config
        configured = self.get_configured_relationships()
        for r in configured:
            relationships.add(r)
            
        # 2. Auto-discover from FKs if needed
        if not relationships:
            tables = self.get_tables()
            for table in tables:
                fkeys = self.get_foreign_keys(table)
                for fk in fkeys:
                    relationships.add(
                        f"- {table} → {fk['references_table']} (via {fk['column']})"
                    )
        
        if not relationships:
            return "No specific table relationships defined."
            
        return "Key Relationships:\n" + "\n".join(sorted(list(relationships)))

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
                
                # Check for enums
                enums = self.get_column_enums(table, col['name'])
                enum_str = f", Enum: {enums}" if enums else ""
                
                schema_parts.append(f"  - {col['name']} ({col['type']}, {nullable}{default}{enum_str})")
            
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
        schema_parts.append(self.generate_relationship_summary())
        
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
    
        

    
    
    