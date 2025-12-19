# bot_telegram.py - Technical Documentation

## Overview

`bot_telegram.py` implements a Telegram bot interface for the NL-to-SQL agent. It provides a chat-based interface where users can query a database using natural language through Telegram.

## Architecture

```
User (Telegram) → Telegram Bot API → bot_telegram.py → agent.py → Database
                                                      ↓
                                                  Claude API
```

## Class: `TelegramNLToSQLBot`

Main bot class that handles all Telegram interactions and integrates with the NL-to-SQL agent.

### Initialization

```python
def __init__(self):
    """
    Initialize bot with agent and configuration
    
    Loads:
    - TELEGRAM_BOT_TOKEN from environment
    - TELEGRAM_ALLOWED_USERS (optional) from environment
    - Initializes NLToSQLAgent instance
    
    Raises:
        ValueError: If TELEGRAM_BOT_TOKEN is not set
    """
```

**Environment Variables:**
- `TELEGRAM_BOT_TOKEN` (required): Bot token from BotFather
- `TELEGRAM_ALLOWED_USERS` (optional): Comma-separated user IDs for access control

### Access Control

```python
def is_user_allowed(self, user_id: int) -> bool:
    """
    Check if user is allowed to use the bot
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if user is allowed (or no allowlist configured)
    """
```

**Behavior:**
- If `TELEGRAM_ALLOWED_USERS` is not set or empty → everyone allowed
- If set → only users in the list can interact with the bot

### Command Handlers

#### `/start` Command

```python
async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    
    Sends welcome message with:
    - Bot introduction
    - Inline keyboard buttons with example queries
    - Available commands
    
    Checks user access before responding
    """
```

**Response includes:**
- Welcome message
- **Clickable inline keyboard buttons** with example questions:
  - 📊 How many customers?
  - 💰 Revenue by month
  - 🏆 Top 5 products
  - 📦 Low stock items
- List of available commands

**User Experience:**
- Users can click buttons to instantly send predefined queries
- Buttons appear only once in the welcome message (clean UI)
- Users can still type their own custom questions normally

#### `/help` Command

```python
async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command
    
    Sends detailed help including:
    - How to use the bot
    - Example queries
    - Available commands
    - Security features
    """
```

#### `/schema` Command

```python
async def schema_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /schema command
    
    Loads and displays database schema
    
    Features:
    - Checks user access
    - Shows loading message
    - Truncates if schema > 4000 chars (Telegram limit)
    - Formats as code block for readability
    
    Note: Schema is truncated at 3900 chars to fit Telegram's 4096 limit
    """
```

### Message Handlers

#### Natural Language Query Handler

```python
async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle natural language queries
    
    Flow:
    1. Check user access
    2. Log query for monitoring
    3. Send "thinking" message
    4. Call agent.query()
    5. Delete "thinking" message
    6. Format and send response
    
    Error Handling:
    - Catches all exceptions
    - Logs errors with stack trace
    - Sends user-friendly error message
    """
```

#### Natural Language Narratives (New)

The bot now provides a conversational summary of the results before showing the SQL and table. This is generated via a second LLM call to Claude after the query results are obtained.

- **Limit**: To optimize tokens and costs, only the first 20 rows of results are sent to Claude for summarization.
- **Tone**: Friendly, conversational, and direct.
- **Fallback**: If the narrative generation fails, the bot gracefully proceeds to show the SQL and table without the summary.

**Processing Steps:**
1. Extract message text
2. Validate user access
3. Log query (user ID, username, query text)
4. Show "Processing..." indicator
5. Execute query via agent
6. Format results
7. Send response (potentially split into multiple messages)

#### Inline Button Callback Handler

```python
async def handle_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline keyboard button clicks
    
    Flow:
    1. Acknowledge button click (prevents loading spinner)
    2. Extract query text from callback_data
    3. Log button click for monitoring
    4. Send "thinking" message
    5. Call agent.query() with the predefined question
    6. Delete "thinking" message
    7. Format and send response
    
    Error Handling:
    - Catches all exceptions
    - Logs errors with stack trace
    - Sends user-friendly error message
    """
```

**Button Format:**
- Callback data: `query:Full question text here`
- Example: `query:How many customers do we have in our database?`
- Buttons are registered via `CallbackQueryHandler`

### Response Formatting

#### Success Response

```python
def format_success_response(self, result: dict) -> str:
    """
    Format successful query result for Telegram
    
    Args:
        result: Dictionary from agent.query() with keys:
            - sql: Generated SQL query
            - results: List of tuples (query results)
            - column_names: List of column names
            - row_count: Number of rows returned
            - attempt: Number of attempts taken
            - natural_query: Original user question
    
    Returns:
        Formatted markdown string with:
        - Success indicator (✅)
        - Natural language summary (📊 **Summary:** ...)
        - Generated SQL (code block)
        - Results table (limited to 20 rows)
        - Row count
    
    Features:
    - Shows retry attempt if > 1
    - Displays natural language summary (if generated)
    - Formats results as ASCII table
    - Limits display to 20 rows (shows count and "trimming" notice if more)
    """
```

**Format:**
```
✅ Query Successful

📊 **Summary:** Your database currently has **1,250 customers**.

Generated SQL:
```sql
SELECT ...
```

Results: 15 row(s)

```
col1 | col2 | col3
-----|------|-----
val1 | val2 | val3
...
```
```

#### Error Response

```python
def format_error_response(self, result: dict) -> str:
    """
    Format error response for Telegram
    
    Args:
        result: Dictionary from agent.query() with keys:
            - error: Error message
            - sql: Failed SQL (if available)
            - attempt: Number of attempts made
    
    Returns:
        Formatted markdown string with:
        - Error indicator (❌)
        - Error message
        - Failed SQL (if available)
        - Helpful tips
    """
```

**Format:**
```
❌ Query Failed

Error:
`error message here`

Failed SQL:
```sql
SELECT ...
```

💡 Tips:
• Try rephrasing your question
• Be more specific
• Use /schema to see available tables
```

#### Table Formatting

```python
def format_table(self, results: list, column_names: list, max_rows: int = 20) -> str:
    """
    Format query results as a Telegram-friendly table
    
    Args:
        results: List of tuples (query results)
        column_names: List of column names
        max_rows: Maximum rows to display (default: 20)
    
    Returns:
        Formatted ASCII table in code block
    
    Features:
    - Truncates long values (> 30 chars)
    - Shows "NULL" for None values
    - Adds "X more rows" indicator if truncated
    - Uses pipe-separated format for readability
    """
```

**Example output:**
```
```
name | age | city
-----|-----|-----
John | 30  | New York
Jane | 25  | Los Angeles
...

... (15 more rows)
```
```

### Message Splitting

```python
async def send_long_message(self, update: Update, text: str):
    """
    Send long messages by splitting if needed
    
    Telegram has a 4096 character limit per message.
    This method splits messages that exceed 4000 chars.
    
    Args:
        update: Telegram update object
        text: Message text (potentially long)
    
    Implementation:
    - If ≤ 4000 chars: Send as single message
    - If > 4000 chars: Split and send multiple messages
    """
```

```python
def split_message(self, text: str, max_length: int) -> list:
    """
    Split message into parts while preserving markdown blocks
    
    Args:
        text: Full message text
        max_length: Maximum length per part
    
    Returns:
        List of message parts
    
    Strategy:
    - Split by newlines
    - Preserve code blocks when possible
    - Keep each part under max_length
    """
```

### Error Handling

```python
async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler for uncaught exceptions
    
    Args:
        update: Telegram update that caused the error
        context: Context containing the error
    
    Behavior:
    - Logs error with full context
    - Sends generic error message to user
    - Prevents bot from crashing
    """
```

### Main Execution

```python
def run(self):
    """
    Start the bot
    
    Setup:
    1. Create Application with bot token
    2. Register command handlers (/start, /help, /schema)
    3. Register callback handler (for inline button clicks)
    4. Register message handler (for queries)
    5. Register error handler
    6. Start polling
    
    Uses long-polling mode:
    - No webhook URL needed
    - Works behind firewalls
    - Resilient to network issues
    - Suitable for development and production
    """
```

## Dependencies

- `python-telegram-bot==21.7`: Telegram Bot API wrapper
- `agent.NLToSQLAgent`: Core NL-to-SQL agent
- `python-dotenv`: Environment variable loading
- `logging`: Structured logging

## Logging

The bot uses Python's standard logging module with INFO level:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

**Logged events:**
- Bot startup
- User queries (with user ID and username)
- Errors (with full stack traces)
- Bot shutdown

## Security Features

1. **User Allowlist**: Optional access control via `TELEGRAM_ALLOWED_USERS`
2. **SQL Validation**: Inherits from `agent.py` (only SELECT queries)
3. **Query Timeout**: 30-second limit (configured in agent)
4. **Result Limits**: Default 100 rows (configured in agent)
5. **No Token Exposure**: Token stored in environment, never logged

## Performance Considerations

- **Schema Caching**: Schema is loaded once and cached by agent
- **Long Polling**: Efficient for low-to-medium traffic
- **Async Handlers**: All handlers are async/await for concurrency
- **Message Splitting**: Handles large responses without blocking

## Error Recovery

- **Retry Logic**: Inherits agent's retry mechanism (up to 3 attempts)
- **Graceful Failures**: Shows user-friendly error messages
- **Continuous Operation**: Error handler prevents crashes

## Testing Locally

```bash
# Set environment variables in .env
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ALLOWED_USERS=  # Optional

# Run the bot
python bot_telegram.py
```

Expected output:
```
2024-12-17 15:00:00 - __main__ - INFO - Telegram bot initialized successfully
2024-12-17 15:00:00 - __main__ - INFO - Starting Telegram bot...
2024-12-17 15:00:01 - __main__ - INFO - Bot is running! Press Ctrl+C to stop.
```

## Production Deployment

See [DIGITALOCEAN_DEPLOYMENT.md](./DIGITALOCEAN_DEPLOYMENT.md) for deployment instructions.

## Future Enhancements

Potential improvements:
- **Webhook Mode**: For faster response in high-traffic scenarios
- **Rate Limiting**: Per-user query limits
- **Query History**: Track user queries for analytics
- **Inline Queries**: Support for inline bot queries
- **Result Pagination**: Navigate through large result sets with buttons
- **Multi-language Support**: i18n for error messages
- **Database Selection**: Allow users to choose different databases
