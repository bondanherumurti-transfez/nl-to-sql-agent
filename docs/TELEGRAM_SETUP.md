# Telegram Bot Setup Guide

This guide will walk you through setting up the Telegram bot for your NL-to-SQL agent.

## Prerequisites

- Telegram account
- Telegram app installed (mobile or desktop)
- Your NL-to-SQL agent project set up locally

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather by clicking "Start"
3. **Create a new bot**:
   - Send the command: `/newbot`
   - BotFather will ask for a **display name** (e.g., "My SQL Assistant")
   - Then provide a **username** ending in "bot" (e.g., `my_sql_assistant_bot`)

4. **Save your token**:
   - BotFather will provide an HTTP API token that looks like:
     ```
     1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345678
     ```
   - ⚠️ **Keep this token secret!** It's like a password for your bot.

## Step 2: Configure Your Bot (Optional)

You can customize your bot's appearance and behavior:

### Set Bot Description
```
/setdescription
```
Example: "I help you query your database using natural language"

### Set Bot Commands
```
/setcommands
```
Then paste:
```
start - Start the bot and see welcome message
help - Show help and usage instructions
schema - View database schema
```

### Set Bot Profile Picture
```
/setuserpic
```
Upload an image (e.g., a database or chat icon)

## Step 3: Configure Environment Variables

Add your Telegram bot token to your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345678

# Optional: Restrict access to specific users (comma-separated user IDs)
# Leave empty to allow everyone
TELEGRAM_ALLOWED_USERS=

# Optional: For webhook mode (leave empty for polling)
TELEGRAM_WEBHOOK_URL=
```

### Finding User IDs (for allowlist)

If you want to restrict access to specific users:

1. Add a temporary user ID logger to your bot, or
2. Use a bot like `@userinfobot` - send it a message and it will reply with your user ID
3. Add the user IDs to `TELEGRAM_ALLOWED_USERS` separated by commas:
   ```bash
   TELEGRAM_ALLOWED_USERS=123456789,987654321
   ```

## Step 4: Install Dependencies

Install the Telegram bot library:

```bash
pip install python-telegram-bot==21.7
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 5: Test Locally

1. **Start the bot**:
   ```bash
   python bot_telegram.py
   ```

2. **Find your bot** in Telegram by searching for the username you created

3. **Start a conversation**:
   - Click "Start" or send `/start`
   - You should see the welcome message

4. **Test a query**:
   - Send: "How many customers do we have?"
   - The bot should generate SQL and return results

5. **Try other commands**:
   - `/help` - View help
   - `/schema` - See database schema

## Bot Features

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/help` | Detailed help and usage examples |
| `/schema` | View complete database schema |

### Natural Language Queries

Simply type your question in plain English:

**Examples:**
- "Show me total revenue by month"
- "How many orders were placed yesterday?"
- "What are the top 5 customers by order value?"

### Security Features

✅ **Read-only queries**: Only `SELECT` statements are allowed  
✅ **Result limits**: Results are limited to 100 rows by default  
✅ **Query timeout**: Queries timeout after 30 seconds  
✅ **User allowlist**: Optional access control by user ID  
✅ **SQL injection protection**: Built-in validation

### Message Formatting

The bot returns results in a formatted table view with:
- ✅ Success indicator
- 📊 Generated SQL query (syntax highlighted)
- 📋 Results table (up to 20 rows displayed)
- ⚠️ Helpful error messages if query fails

## Troubleshooting

### Bot doesn't respond

1. **Check the bot is running**:
   ```bash
   python bot_telegram.py
   ```
   You should see: `Bot is running! Press Ctrl+C to stop.`

2. **Verify your token**:
   - Make sure `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
   - Token should have no spaces or quotes

3. **Check database connection**:
   - Ensure all `DB_*` environment variables are set
   - Test database connectivity separately

### "Access denied" message

- If you've set `TELEGRAM_ALLOWED_USERS`, make sure your user ID is in the list
- To disable allowlist, set `TELEGRAM_ALLOWED_USERS=` (empty)

### Schema command returns truncated data

- Telegram has a 4096 character limit per message
- For very large schemas, consider using `/schema` less frequently
- The full schema is always loaded for query processing

### Bot stops responding after a while

- This might be a network issue
- The bot uses long-polling by default which is resilient
- Check your logs for error messages
- Restart the bot if needed

## Next Steps

Once the bot works locally, you're ready to deploy it to DigitalOcean!

See [DIGITALOCEAN_DEPLOYMENT.md](./DIGITALOCEAN_DEPLOYMENT.md) for deployment instructions.

## Advanced: Webhook Mode (Optional)

For production, you can use webhook mode instead of polling:

1. Set up a public HTTPS URL (DigitalOcean provides this)
2. Add to `.env`:
   ```bash
   TELEGRAM_WEBHOOK_URL=https://your-app.ondigitalocean.app
   ```
3. Modify `bot_telegram.py` to use webhooks instead of polling

Polling mode is simpler and works great for most use cases. Use webhooks only if you need instant responses or have high traffic.
