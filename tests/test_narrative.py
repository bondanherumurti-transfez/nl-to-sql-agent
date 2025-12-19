import pytest
from unittest.mock import MagicMock, patch
from agent import NLToSQLAgent

class TestNarrativeGeneration:
    @pytest.fixture
    def agent(self):
        with patch('agent.psycopg2.connect'), \
             patch('agent.Anthropic'):
            agent = NLToSQLAgent()
            agent.client = MagicMock()
            return agent

    def test_generate_narrative_success(self, agent):
        """Test successful narrative generation"""
        # Mock Claude response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Your database currently has **1,250 customers**.")]
        agent.client.messages.create.return_value = mock_response

        # Call generate_narrative
        summary = agent.generate_narrative(
            natural_query="How many customers?",
            sql="SELECT COUNT(*) FROM customers;",
            results=[(1250,)],
            column_names=["count"],
            row_count=1
        )

        # Assertions
        assert summary == "Your database currently has **1,250 customers**."
        agent.client.messages.create.assert_called_once()
        
        # Verify prompt content (internal check)
        args, kwargs = agent.client.messages.create.call_args
        prompt = kwargs['messages'][0]['content']
        assert "How many customers?" in prompt
        assert "SELECT COUNT(*) FROM customers;" in prompt
        assert "1250" in prompt

    def test_generate_narrative_failure(self, agent):
        """Test narrative generation failure handling"""
        # Mock Claude error
        agent.client.messages.create.side_effect = Exception("API Error")

        # Call generate_narrative
        summary = agent.generate_narrative(
            natural_query="Any customers?",
            sql="SELECT * FROM customers;",
            results=[],
            column_names=[],
            row_count=0
        )

        # Assertions
        assert summary == "Unable to generate summary."

    def test_query_includes_natural_query(self, agent):
        """Test that query() method now returns natural_query in result"""
        # Mock SQL generation, validation, and execution
        with patch.object(agent, 'generate_sql', return_value="SELECT 1;"), \
             patch('agent.SQLValidator.is_safe_query', return_value=(True, "")), \
             patch('agent.SQLValidator.add_limit_if_missing', return_value="SELECT 1;"), \
             patch.object(agent, 'execute_sql', return_value=([(1,)], ["col"])):
            
            result = agent.query("test query")
            
            assert result['success'] is True
            assert result['natural_query'] == "test query"
