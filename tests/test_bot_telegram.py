import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from bot_telegram import TelegramNLToSQLBot
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

@pytest.fixture
def mock_bot_env():
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': '12345:test_token',
        'TELEGRAM_ALLOWED_USERS': '12345',
        'DB_HOST': 'localhost',
        'ANTHROPIC_API_KEY': 'test_key'
    }):
        with patch('bot_telegram.NLToSQLAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            yield {
                'bot': TelegramNLToSQLBot(),
                'agent_class': mock_agent_class,
                'agent': mock_agent
            }

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    user.first_name = "TestUser"
    user.username = "testuser"
    
    message = AsyncMock(spec=Message)
    message.text = "How many customers?"
    message.chat = MagicMock(spec=Chat)
    
    update.effective_user = user
    update.message = message
    return update

@pytest.mark.asyncio
async def test_start_command_allowed(mock_bot_env, mock_update):
    """Test /start command for allowed user"""
    bot = mock_bot_env['bot']
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    await bot.start_command(mock_update, context)
    
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert "Hi TestUser" in args[0]

@pytest.mark.asyncio
async def test_start_command_denied(mock_bot_env, mock_update):
    """Test /start command for disallowed user"""
    bot = mock_bot_env['bot']
    mock_update.effective_user.id = 99999
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    await bot.start_command(mock_update, context)
    
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert "access denied" in args[0].lower() or "sorry" in args[0].lower()

@pytest.mark.asyncio
async def test_handle_query_success(mock_bot_env, mock_update):
    """Test successful natural language query handling"""
    bot = mock_bot_env['bot']
    agent = mock_bot_env['agent']
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    # Mock agent response
    agent.query.return_value = {
        'success': True,
        'sql': "SELECT COUNT(*) FROM customers;",
        'results': [(100,)],
        'column_names': ['count'],
        'row_count': 1
    }
    
    # Mock thinking message
    thinking_msg = AsyncMock()
    mock_update.message.reply_text.return_value = thinking_msg
    
    await bot.handle_query(mock_update, context)
    
    # Verify thinking message was sent and then deleted
    assert mock_update.message.reply_text.call_count >= 2
    thinking_msg.delete.assert_called_once()
    
    # Verify agent was called
    agent.query.assert_called_with("How many customers?")
    
    # Verify success response was sent
    last_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Query Successful" in last_call_args
    assert "SELECT COUNT(*) FROM customers;" in last_call_args

@pytest.mark.asyncio
async def test_schema_command(mock_bot_env, mock_update):
    """Test /schema command"""
    bot = mock_bot_env['bot']
    agent = mock_bot_env['agent']
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    
    agent.load_schema_context.return_value = "Table: users (id, name)"
    
    await bot.schema_command(mock_update, context)
    
    agent.load_schema_context.assert_called_once()
    last_call_args = mock_update.message.reply_text.call_args[0][0]
    assert "Database Schema" in last_call_args
    assert "Table: users" in last_call_args
