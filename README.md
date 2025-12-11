This is a Natural language to SQL Language, it helps non technical people to query business analytics

- Entry point is agent.py
- The query is coming from Interactive shell from interactiveMode() function, from there it will call query() function. Query function will call generate_sql() function to generate SQL from natural language query, then it will call execute_sql() function to execute the SQL query.

Role of files
- agent.py: Entry point of application, mostly control interactive shell
- clickhouse_schema.py: Schema introspection for a clickhouse database for transfez specific use cases, its an experimental file to test schema instrospection with more than 100 tables
- prompts.py: a prompts builder it combined between schema instrospection, key relationships, few shots examples, and user query to generate a prompt for Claude
- schema_introspection.py: an schema introspection class that will be used to get schema context from database, this the one that used to generate schema context for prompts
- sql_validator.py: a sql validator class that will ensures only safe SELECT queries are executed

Structure of prompts: 
* System Prompt
* Schema Context
* Key Relationships
* Few Shots Examples
* User Query
Details:
Schema context is always include all table and columns, as well as sample data from each table, and foreign key relationships, there is no table filter since this is a very limited tables involved.

Sample schema context:
```sql
TABLE: shipping_addresses
--------------------------------------------------------------------------------
Columns:
  - address_id (integer, NOT NULL, DEFAULT: NO)
  - customer_id (integer, NOT NULL, DEFAULT: NO)
  - address_line1 (character varying, NOT NULL, DEFAULT: NO)
  - address_line2 (character varying, NOT NULL, DEFAULT: YES)
  - city (character varying, NOT NULL, DEFAULT: NO)
  - state (character varying, NOT NULL, DEFAULT: YES)
  - postal_code (character varying, NOT NULL, DEFAULT: NO)
  - country (character varying, NOT NULL, DEFAULT: NO)
  - is_default (boolean, NOT NULL, DEFAULT: YES)
  - created_at (timestamp without time zone, NOT NULL, DEFAULT: YES)
  - updated_at (timestamp without time zone, NOT NULL, DEFAULT: YES)

Foreign Keys:
  - customer_id → customers.customer_id

Sample Data (1 row):
  Columns: address_id, customer_id, address_line1, address_line2, city, state, postal_code, country, is_default, created_at, updated_at
  Sample: (1, 1, '123 Main St', None, 'New York', 'NY', '10001', 'USA', True, datetime.datetime(2025, 12, 3, 18, 25, 42, 295330), datetime.datetime(2025, 12, 3, 18, 25, 42, 295330))
```

Key Relationships is currenltly hardcoded, it defines the relationships between tables, this is needed to generate JOINs in the SQL query.

Few Shots Examples is currently hardcoded, it defines the examples of SQL queries that will be used to generate JOINs in the SQL query.
