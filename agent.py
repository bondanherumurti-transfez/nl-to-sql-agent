"""
Natural Language to SQL Agent
Main agent that orchestrates the conversion and execution
"""

import os
import psycopg2
from anthropic import Anthropic
from dotenv import load_dotenv
from typing import Dict, Any, List, Tuple, Optional
from tabulate import tabulate
from colorama import Fore, Style, init

from schema_introspection import SchemaIntrospection
from sql_validator import SQLValidator
from prompts import (
    get_base_prompt,
    get_error_recovery_prompt,
    get_clarification_prompt
)

init(autoreset=True)

class NLToSQLAgent:
    """Natural Language to SQL Agent"""
    
    def __init__(self):
        """Initialize the agent with database connection and API client"""
        load_dotenv()

        self.db_config = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5"

        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.query_timeout = int(os.getenv('QUERY_TIMEOUT', 30))
        self.default_limit = int(os.getenv('DEFAULT_LIMIT', 100))

        self.schema_context = None
        
        print(f"{Fore.GREEN}✓ Agent initialized successfully{Style.RESET_ALL}")
    
    def connect_db(self) -> psycopg2.extensions.connection:
        """Create database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"{Fore.RED}Error connecting to database: {e}{Style.RESET_ALL}")
            raise
    
    def load_schema_context(self) -> str:
        """Load and cache database schema context"""
        if self.schema_context is None:
            print(f"{Fore.CYAN}Loading database schema...{Style.RESET_ALL}")
            conn = self.connect_db()
            introspector = SchemaIntrospection(conn)
            self.schema_context = introspector.get_full_schema_context()
            conn.close()
            print(f"{Fore.GREEN}✓ Schema loaded{Style.RESET_ALL}")
        return self.schema_context

    def retry_with_error(self, natural_query: str, failed_sql: str, error_message: str, attempt: int) -> str:
        """        
        Retry SQL generation with error context
        
        Args:
            natural_query: Original user query
            failed_sql: SQL that failed
            error_message: Error message
            attempt: Current attempt number
            
        Returns:
            New SQL query
        """
        print(f"{Fore.YELLOW}Attempt {attempt}: Regenerating SQL with error context...{Style.RESET_ALL}")

        schema = self.load_schema_context()
        prompt = get_error_recovery_prompt(schema, natural_query, failed_sql, error_message)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0,
                messages=[{
                    role:"user",
                    content: prompt
                }]
            )

            sql = response.content[0].text.strip()
            sql = SQLValidator(sql).clean(sql)
            return sql
        except Exception as e:
            print(f"{Fore.RED}🙅‍♂️Retry failed: {e}{Style.RESET_ALL}")
            raise

    def generate_sql(self, natural_query: str) -> str:
        """
                Generate SQL from natural language query using Claude
        
        Args:
            natural_query: User's natural language question
            
        Returns:
            Generated SQL query
        """
        schema = self.load_schema_context()
        prompt = get_base_prompt(schema)

        full_prompt = f"{prompt}\n\nQuestion: {natural_query}\n\nSQL:"

        #print full prompt here
        # print(f"{Fore.CYAN}Full Prompt: {full_prompt}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}Generating SQL...{Style.RESET_ALL}")

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
            )
            
            sql = response.content[0].text.strip()
            sql = SQLValidator.clean_sql(sql)            
            return sql
        except Exception as e:
            print(f"{Fore.RED}✗ SQL generation failed: {e}{Style.RESET_ALL}")
            raise
    
    def execute_sql(self, sql: str) -> Tuple[List[tuple], List[str]]:
        """
        Execute SQL query
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Tuple containing query results and column names
        """
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            # Set query timeout
            cursor.execute(f"SET statement_timeout = {self.query_timeout * 1000};")
            
            # Execute query
            cursor.execute(sql)
            
            # Fetch results
            results = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []

            return results, column_names
        except Exception as e:
            print(f"{Fore.RED}✗ Query execution failed: {e}{Style.RESET_ALL}")
            raise
        finally:
            cursor.close()
            conn.close()

    
    def query(self, natural_query: str) -> Dict[str, Any]:
        """
        Main query method - converts NL to SQL and executes it

        Args:
            natural_query: User's natural language query
            
        Returns:
            Dict containing query result and metadata
        """
        print(f"\n{Fore.BLUE}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Question: {natural_query}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}\n")

        sql = None
        results = None
        column_names = None
        error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt == 1:
                    sql = self.generate_sql(natural_query)
                else:
                    sql = self.retry_with_error(natural_query, sql, error, attempt)
                
                print(f"{Fore.CYAN}Generated SQL:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{sql}{Style.RESET_ALL}\n")

                #validate SQL
                is_safe, message = SQLValidator.is_safe_query(sql)
                if not is_safe:
                    return {
                        'success': False,
                        'error': f"‼️Unsafe SQL detected: {message}",
                        'sql': sql
                    }
                
                sql = SQLValidator.add_limit_if_missing(sql, self.default_limit)

                # Execute SQL
                print(f"{Fore.CYAN}Prepare to execute query...{Style.RESET_ALL}")
                results, column_names = self.execute_sql(sql)

                # Success!
                print(f"{Fore.GREEN}✓ Query executed successfully{Style.RESET_ALL}")
                print(f"{Fore.GREEN}✓ Retrieved {len(results)} rows{Style.RESET_ALL}\n")
                
                return {
                    'success': True,
                    'sql': sql,
                    'results': results,
                    'column_names': column_names,
                    'attempt': attempt,
                    'row_count': len(results)
                }
            except Exception as e:
                error = str(e)
                print(f"{Fore.RED}✗ Attempt {attempt} failed: {error}{Style.RESET_ALL}\n")

                if attempt == self.max_retries:
                    return {
                        'success': False,
                        'error': f"Failed after {self.max_retries} attempts. Last error: {error}",
                        'sql': sql
                    }
                
        
        return {
            'success': False,
            'error': 'Unknown error occurred',
            'sql': sql
        }
    

    def format_results(self, result: Dict[str, Any]) -> str:
        """
        Format query results for display
        
        Args:
            result: Result dictionary from query method
            
        Returns:
            Formatted string
        """
        if not result['success']:
            return f"{Fore.RED}Error: {result['error']}{Style.RESET_ALL}"

        output = []

        #Show SQL query
        output.append(f"{Fore.CYAN}SQL Query:{Style.RESET_ALL}")
        output.append(result['sql'])
        output.append("")

        #Show results
        if result['row_count'] > 0:
            output.append(f"{Fore.GREEN}Results ({result['row_count']} rows):{Style.RESET_ALL}")

            table = tabulate(result['results'], headers=result['column_names'], tablefmt='fancy_grid')
            output.append(table)
        else:
            output.append(f"{Fore.YELLOW}No results found.{Style.RESET_ALL}")

        return "\n".join(output)
        
        

    def interactiveMode(self):
        """Run Agent in interactive CLI Mode"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Natural Language to SQL Agent - Interactive Mode{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Type your questions in natural language.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Type 'exit' or 'quit' to stop.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Type 'schema' to see database schema.{Style.RESET_ALL}\n")

        while True:
            try:
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}\n")
                    break
                if user_input.lower() == 'schema':
                    schema = self.load_schema_context()
                    print(f"\n{schema}\n")
                    continue
                
                result = self.query(user_input)
                formatted = self.format_results(result)
                print(f"\n{formatted}\n")
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}\n")
                
    
def main():
    """Main entry point for the agent"""
    try:
        agent = NLToSQLAgent()
        agent.interactiveMode()
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())



