import pytest
from unittest.mock import MagicMock, patch
from agent import NLToSQLAgent

@pytest.fixture
def mock_agent_deps():
    with patch('agent.Anthropic') as mock_anthropic, \
         patch('agent.psycopg2.connect') as mock_connect, \
         patch('agent.SchemaIntrospection') as mock_introspection:
        
        # Setup mock client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Setup mock introspection
        mock_intro_instance = MagicMock()
        mock_introspection.return_value = mock_intro_instance
        mock_intro_instance.get_full_schema_context.return_value = "Mock Schema"
        
        yield {
            'anthropic': mock_anthropic,
            'client': mock_client,
            'connect': mock_connect,
            'conn': mock_conn,
            'cursor': mock_cursor,
            'introspection': mock_introspection,
            'intro_instance': mock_intro_instance
        }

def test_agent_initialization(mock_agent_deps):
    """Test that agent initializes correctly with env vars"""
    with patch('agent.load_dotenv'):
        with patch.dict('os.environ', {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_USER': 'user',
            'DB_PASSWORD': 'pass',
            'DB_NAME': 'db',
            'ANTHROPIC_API_KEY': 'sk-test'
        }):
            agent = NLToSQLAgent()
            assert agent.db_config['host'] == 'localhost'
            assert agent.client is not None

def test_generate_sql(mock_agent_deps):
    """Test SQL generation calling Anthropic API"""
    agent = NLToSQLAgent()
    
    # Create a "fake" response that mimics what Claude API returns
    # This prevents us from spending money on tokens during testing
    mock_response = MagicMock()  # Step 1: Create a dummy response object
    
    # Step 2: Mimic Claude's data structure: response.content[0].text
    # The real API returns a list with an object that has a .text attribute
    mock_response.content = [MagicMock(text="SELECT * FROM customers;")]
    
    # Step 3: "Intercept" the API call - when agent calls client.messages.create(),
    # return our fake response instead of making a real API request
    mock_agent_deps['client'].messages.create.return_value = mock_response
    
    sql = agent.generate_sql("Show me all customers")
    
    assert sql == "SELECT * FROM customers;"
    mock_agent_deps['client'].messages.create.assert_called_once()
    assert "Show me all customers" in mock_agent_deps['client'].messages.create.call_args[1]['messages'][0]['content']

def test_execute_sql_success(mock_agent_deps):
    """Test successful SQL execution"""
    agent = NLToSQLAgent()
    
    # Setup mock cursor
    mock_cursor = mock_agent_deps['cursor']
    mock_cursor.fetchall.return_value = [(1, 'John'), (2, 'Jane')]
    mock_cursor.description = [('id',), ('name',)]
    
    results, columns = agent.execute_sql("SELECT * FROM customers;")
    
    assert len(results) == 2
    assert columns == ['id', 'name']
    mock_cursor.execute.assert_called()

def test_query_integration(mock_agent_deps):
    """Test the full query flow from NL to results"""
    agent = NLToSQLAgent()
    
    # Mock the Claude LLM's response (same pattern as above)
    # We're telling the test: "When the agent asks Claude for SQL, pretend Claude said this:"
    mock_response = MagicMock()  # Create fake response object
    mock_response.content = [MagicMock(text="SELECT * FROM products;")]  # Fake SQL from "Claude"
    mock_agent_deps['client'].messages.create.return_value = mock_response  # Return it when called
    
    # Mock the Database's response
    # We're telling the test: "When the agent runs SQL against the DB, pretend the DB returned this:"
    mock_cursor = mock_agent_deps['cursor']
    mock_cursor.fetchall.return_value = [('Product A', 100)]  # Fake data rows
    mock_cursor.description = [('name',), ('price',)]  # Fake column names
    
    result = agent.query("Show products")
    
    assert result['success'] is True
    assert result['sql'] == "SELECT * FROM products LIMIT 100;"
    assert result['row_count'] == 1
    assert result['results'][0][0] == 'Product A'
