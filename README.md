This is a Natural language to SQL Language, it helps non technical people to query business analytics

- Entry point is agent.py
- The query is coming from Interactive shell from interactiveMode() function, from there it will call query() function. Query function will call generate_sql() function to generate SQL from natural language query, then it will call execute_sql() function to execute the SQL query.

Role of files
- agent.py: Entry point of application, mostly control interactive shell
- clickhouse_schema.py: Schema introspection for a clickhouse database for transfez specific use cases, its an experimental file to test schema instrospection with more than 100 tables
- prompts.py: a prompts builder it combined between schema instrospection, key relationships, few shots examples, and user query to generate a prompt for Claude
- schema_introspection.py: an schema introspection class that will be used to get schema context from database, this the one that used to generate schema context for prompts
- sql_validator.py: a sql validator class that will ensures only safe SELECT queries are executed
