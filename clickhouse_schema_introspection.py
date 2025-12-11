"""
Database Schema Introspection Utility for NL to SQL Agent.
Extracts database schema information from a ClickHouse database via HTTP.
"""
import os
import clickhouse_connect
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional

class ClickHouseSchemaIntrospection:
    """Extracts database schema information from ClickHouse."""

    def __init__(self, client):
        self.client = client
        self._query_delay = 0.1  # Small delay between queries

    def _execute_query(self, query, parameters=None):
        """Execute query with delay to prevent port exhaustion."""
        time.sleep(self._query_delay)
        return self.client.query(query, parameters=parameters)

    def get_tables(self, database: str = None) -> List[str]:
        """Get all table names in the specified database."""
        if database is None:
            database = self.client.database
        
        query = """
        SELECT name
        FROM system.tables
        WHERE database = %(database)s
        AND engine NOT IN ('View', 'MaterializedView')
        ORDER BY name
        """
        result = self._execute_query(query, parameters={'database': database})
        return [row[0] for row in result.result_rows]

    def get_table_columns(self, table_name: str, database: str = None) -> List[Dict]:
        """Get column information for a specific table."""
        if database is None:
            database = self.client.database
        
        query = """
        SELECT 
            name,
            type,
            default_kind,
            default_expression,
            comment,
            is_in_partition_key,
            is_in_sorting_key,
            is_in_primary_key
        FROM system.columns
        WHERE database = %(database)s AND table = %(table)s
        ORDER BY position
        """
        result = self._execute_query(query, parameters={'database': database, 'table': table_name})
        
        columns = []
        for row in result.result_rows:
            columns.append({
                'name': row[0],
                'type': row[1],
                'default_kind': row[2],
                'default_expression': row[3],
                'comment': row[4],
                'is_in_partition_key': row[5],
                'is_in_sorting_key': row[6],
                'is_in_primary_key': row[7]
            })
        return columns
    
    def get_table_engine(self, table_name: str, database: str = None) -> Dict[str, str]:
        """Get table engine information."""
        if database is None:
            database = self.client.database
        
        query = """
        SELECT 
            engine,
            partition_key,
            sorting_key,
            primary_key,
            sampling_key
        FROM system.tables
        WHERE database = %(database)s AND name = %(table)s
        """
        result = self._execute_query(query, parameters={'database': database, 'table': table_name})
        
        if result.result_rows:
            row = result.result_rows[0]
            return {
                'engine': row[0],
                'partition_key': row[1],
                'sorting_key': row[2],
                'primary_key': row[3],
                'sampling_key': row[4]
            }
        return {}

    def get_sample_data(self, table_name: str, database: str = None, limit: int = 2) -> List[tuple]:
        """Get sample rows from a table."""
        if database is None:
            database = self.client.database
        
        query = f"SELECT * FROM {database}.{table_name} LIMIT %(limit)s"
        result = self._execute_query(query, parameters={'limit': limit})
        return result.result_rows
    
    def get_table_size(self, table_name: str, database: str = None) -> Dict[str, any]:
        """Get table size statistics."""
        if database is None:
            database = self.client.database
        
        query = """
        SELECT 
            sum(rows) as total_rows,
            formatReadableSize(sum(bytes)) as total_size,
            sum(bytes) as total_bytes
        FROM system.parts
        WHERE database = %(database)s 
        AND table = %(table)s
        AND active
        """
        result = self._execute_query(query, parameters={'database': database, 'table': table_name})
        
        if result.result_rows:
            row = result.result_rows[0]
            return {
                'total_rows': row[0],
                'total_size': row[1],
                'bytes': row[2]  # This now maps to total_bytes
            }
        return {}

    def get_full_schema_context(self, database: str = None) -> str:
        """Generate complete schema context for LLM."""
        if database is None:
            database = self.client.database
        
        schema_parts = []
        schema_parts.append("CLICKHOUSE DATABASE SCHEMA INFORMATION")
        schema_parts.append("=" * 80)
        schema_parts.append(f"Database: {database}")
        schema_parts.append("")
        
        tables = self.get_tables(database)
        
        for table in tables:
            schema_parts.append(f"\nTABLE: {table}")
            schema_parts.append("-" * 80)
            
            # Table Engine Info
            engine_info = self.get_table_engine(table, database)
            if engine_info:
                schema_parts.append(f"Engine: {engine_info.get('engine', 'N/A')}")
                if engine_info.get('partition_key'):
                    schema_parts.append(f"Partition Key: {engine_info['partition_key']}")
                if engine_info.get('sorting_key'):
                    schema_parts.append(f"Sorting Key: {engine_info['sorting_key']}")
                if engine_info.get('primary_key'):
                    schema_parts.append(f"Primary Key: {engine_info['primary_key']}")
                schema_parts.append("")
            
            # Table Size
            size_info = self.get_table_size(table, database)
            if size_info:
                schema_parts.append(f"Total Rows: {size_info.get('total_rows', 0):,}")
                schema_parts.append(f"Total Size: {size_info.get('total_size', 'N/A')}")
                schema_parts.append("")
            
            # Columns
            columns = self.get_table_columns(table, database)
            schema_parts.append("Columns:")
            for col in columns:
                col_desc = f"  - {col['name']} ({col['type']})"
                
                # Add key indicators
                key_indicators = []
                if col['is_in_primary_key']:
                    key_indicators.append("PRIMARY KEY")
                if col['is_in_sorting_key']:
                    key_indicators.append("SORTING KEY")
                if col['is_in_partition_key']:
                    key_indicators.append("PARTITION KEY")
                
                if key_indicators:
                    col_desc += f" [{', '.join(key_indicators)}]"
                
                # Add default info
                if col['default_kind']:
                    col_desc += f", DEFAULT: {col['default_kind']}"
                    if col['default_expression']:
                        col_desc += f" {col['default_expression']}"
                
                # Add comment
                if col['comment']:
                    col_desc += f" -- {col['comment']}"
                
                schema_parts.append(col_desc)
            
            # Sample data
            try:
                sample_data = self.get_sample_data(table, database, limit=1)
                if sample_data:
                    schema_parts.append("\nSample Data (1 row):")
                    col_names = [col['name'] for col in columns]
                    schema_parts.append(f"  Columns: {', '.join(col_names)}")
                    schema_parts.append(f"  Sample: {sample_data[0]}")
            except Exception as e:
                schema_parts.append(f"\nSample Data: Unable to fetch ({str(e)})")
            
            schema_parts.append("")
        
        # Add summary
        schema_parts.append("\n" + "=" * 80)
        schema_parts.append("SCHEMA SUMMARY")
        schema_parts.append("=" * 80)
        schema_parts.append(f"Total Tables: {len(tables)}")
        schema_parts.append(f"Tables: {', '.join(tables)}")
        schema_parts.append("")
        
        return "\n".join(schema_parts)

    def get_table_summary(self, database: str = None) -> str:
        """Get a brief summary of all tables."""
        if database is None:
            database = self.client.database
        
        tables = self.get_tables(database)
        summary = [f"Available Tables in '{database}':"]
        
        for table in tables:
            columns = self.get_table_columns(table, database)
            size_info = self.get_table_size(table, database)
            rows = size_info.get('total_rows', 0) if size_info else 0
            summary.append(f"  - {table} ({len(columns)} columns, {rows:,} rows)")
        
        return "\n".join(summary)


def test_connection(host, port, user, password, database):
    """Test if ClickHouse connection is working."""
    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            database=database
        )
        
        # Test with a simple query
        result = client.query('SELECT 1')
        print(f"✓ Connection successful! Result: {result.result_rows}")
        return client
        
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
        print("\nTroubleshooting steps:")
        print(f"1. Check if ClickHouse is running")
        print(f"2. Verify host: {host}, port: {port} (HTTP interface)")
        print(f"3. Verify credentials - user: {user}")
        print(f"4. Check database exists: {database}")
        print(f"5. For HTTP interface, use port 8123")
        return None


if __name__ == "__main__":
    
    load_dotenv()
    
    # Get connection parameters
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", 8123))  # HTTP port
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    database = os.getenv("CLICKHOUSE_DATABASE", "default")
    
    print("Attempting to connect to ClickHouse via HTTP...")
    print(f"Host: {host}, Port: {port}, User: {user}, Database: {database}")
    print("-" * 80)
    
    # Test connection first
    client = test_connection(host, port, user, password, database)
    
    if client:
        try:
            introspector = ClickHouseSchemaIntrospection(client)
            
            # Get schema context
            schema_context = introspector.get_full_schema_context()
            table_summary = introspector.get_table_summary()
            
            # Print to console
            print("\n" + "=" * 80)
            print(schema_context)
            
            print("\n" + "=" * 80)
            print(table_summary)
            
            # Save to file with timestamp
            output_dir = "/Users/bondanherumurti/Documents/Projects/nl-to-sql-agent"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"clickhouse_schema_{database}_{timestamp}.txt")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Schema Export Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Database: {database}\n")
                f.write(f"Host: {host}:{port}\n")
                f.write("\n")
                f.write(schema_context)
                f.write("\n\n")
                f.write("=" * 80)
                f.write("\n")
                f.write(table_summary)
            
            print("\n" + "=" * 80)
            print(f"✓ Schema saved to: {output_file}")
            
        except Exception as e:
            print(f"\n✗ Error during schema introspection: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Close client
            client.close()