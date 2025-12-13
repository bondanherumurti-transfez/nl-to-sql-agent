import sys
from unittest.mock import MagicMock

# Mock psycopg2 before importing the module that uses it
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extensions'] = MagicMock()

from schema_introspection import SchemaIntrospection
import os

def test_config_loading():
    print("Testing Configuration Loading Logic...")
    
    # Mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Instantiate introspector
    intro = SchemaIntrospection(mock_conn)
    
    # Test 1: Load Relationships from JSON
    print("\nTest 1: Loading Relationships from schema_config.json")
    summary = intro.generate_relationship_summary()
    
    if "customers → orders" in summary:
        print("✅ Success: Loaded relationships correctly.")
    else:
        print("❌ Failure: Did not load relationships.")

    # Test 2: formatting schema context with Enums
    print("\nTest 2: Injecting Enums into Schema Context")
    
    # Mock get_tables
    intro.get_tables = MagicMock(return_value=["orders"])
    
    # Mock get_table_columns for 'orders' table
    intro.get_table_columns = MagicMock(return_value=[
        {'name': 'order_id', 'type': 'integer', 'nullable': False, 'default': None},
        {'name': 'order_status', 'type': 'varchar', 'nullable': False, 'default': None}
    ])
    
    # Mock get_foreign_keys (empty)
    intro.get_foreign_keys = MagicMock(return_value=[])
    
    # Mock get_sample_data (empty)
    intro.get_sample_data = MagicMock(return_value=[])
    
    full_context = intro.get_full_schema_context()
    print("Generated Context Snippet:")
    print(full_context)
    
    if "Enum: ['processing', 'delivered', 'shipped', 'pending']" in full_context:
        print("✅ Success: Enum values injected into context.")
    else:
        print("❌ Failure: Enum values MISSING from context.")

if __name__ == "__main__":
    test_config_loading()
