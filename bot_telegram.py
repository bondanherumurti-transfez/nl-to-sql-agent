"""
Telegram Bot for NL-to-SQL Agent
Provides a chat interface for querying database using natural language
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from agent import NLToSQLAgent

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramNLToSQLBot:
    """Telegram bot wrapper for NL-to-SQL Agent"""
    
    def __init__(self):
        """Initialize bot with agent and configuration"""
        load_dotenv()
        
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # Optional: User allowlist for access control
        allowed_users = os.getenv("TELEGRAM_ALLOWED_USERS", "")
        self.allowed_users = set(map(int, allowed_users.split(","))) if allowed_users else None
        
        # Initialize NL-to-SQL Agent
        self.agent = NLToSQLAgent()
        
        logger.info("Telegram bot initialized successfully")
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot"""
        if self.allowed_users is None:
            return True  # No allowlist = everyone allowed
        return user_id in self.allowed_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if not self.is_user_allowed(user.id):
            await update.message.reply_text(
                "⛔ Sorry, you don't have access to this bot.\n\n"
                "To get access, please send your **Telegram ID** to Bon.\n\n"
                "🔍 **How to find your ID:**\n"
                "1. Search for @userinfobot in Telegram\n"
                "2. Send it a message\n"
                "3. Copy the numerical ID it sends back",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        welcome_message = (
            f"👋 Hi {user.first_name}!\n\n"
            "I'm your **NL-to-SQL data assistant**. 📊\n\n"
            "Imagine you are an **e-commerce owner** with a complete database containing "
            "customers, products, orders, shipping details, and payment transactions. "
            "You can now query this data just like you'd ask your lead data analyst!\n\n"
            "👇 **Click a question below to try it out:**\n\n"
            "Available Commands:\n"
            "/help - Detailed usage guide\n"
            "/schema - View technical database structure\n\n"
            "‼️ This project is highly experimental, AI might hallucinate and does not recall memory‼️"
        )
        
        # Create clickable example questions as inline buttons
        keyboard = [
            [InlineKeyboardButton("📊 How many customers?", callback_data="query:How many customers do we have in our database?")],
            [InlineKeyboardButton("💰 Revenue by month", callback_data="query:Show me the total revenue grouped by month")],
            [InlineKeyboardButton("🏆 Top 5 products", callback_data="query:What are our top 5 products by sales volume?")],
            [InlineKeyboardButton("📦 Low stock items", callback_data="query:Which products are currently low on stock?")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🤖 *NL-to-SQL Bot Help*\n\n"
            "*How to use:*\n"
            "Simply type your question in natural language, and I'll:\n"
            "1. Convert it to SQL\n"
            "2. Execute the query\n"
            "3. Return the results\n\n"
            "*Examples:*\n"
            "• How many orders were placed today?\n"
            "• Show me customers from New York\n"
            "• What's the average order value?\n\n"
            "*Commands:*\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/schema - View database schema\n\n"
            "*Security:*\n"
            "• Only SELECT queries are allowed\n"
            "• Results are limited to 100 rows by default\n"
            "• Queries timeout after 30 seconds\n"
        )
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
    
    async def schema_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /schema command"""
        if not self.is_user_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ Access denied.")
            return
        
        await update.message.reply_text("🔍 Loading database schema...")
        
        try:
            schema = self.agent.load_schema_context()
            
            # Telegram has message length limits, so we might need to truncate
            if len(schema) > 4000:
                schema = schema[:3900] + "\n\n... (truncated, schema too long)"
            
            await update.message.reply_text(
                f"📊 *Database Schema:*\n\n```\n{schema}\n```",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            await update.message.reply_text(f"❌ Error loading schema: {str(e)}")
    
    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language queries"""
        user = update.effective_user
        
        if not self.is_user_allowed(user.id):
            await update.message.reply_text("⛔ Access denied.")
            return
        
        natural_query = update.message.text.strip()
        
        # Log query for monitoring
        logger.info(f"User {user.id} ({user.username}) query: {natural_query}")
        
        # Send "thinking" message
        thinking_msg = await update.message.reply_text("🤔 Processing your question...")
        
        try:
            # Query the agent
            result = self.agent.query(natural_query)
            
            # Delete thinking message
            await thinking_msg.delete()
            
            # Format and send response
            if result['success']:
                # Generate natural language narrative
                narrative = self.agent.generate_narrative(
                    natural_query=natural_query,
                    sql=result['sql'],
                    results=result['results'][:20],
                    column_names=result['column_names'],
                    row_count=result['row_count']
                )
                response = self.format_success_response(result, narrative)
            else:
                response = self.format_error_response(result)
            
            # Send response (might be multiple messages if too long)
            await self.send_long_message(update, response)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            await thinking_msg.delete()
            await update.message.reply_text(
                f"❌ *Error*\n\n"
                f"An unexpected error occurred:\n"
                f"`{str(e)}`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def format_success_response(self, result: dict, narrative: str = None) -> str:
        """Format successful query result for Telegram"""
        sql = result['sql']
        results = result['results']
        column_names = result['column_names']
        row_count = result['row_count']
        attempt = result.get('attempt', 1)
        
        response = "✅ *Query Successful*\n\n"
        
        if narrative:
            response += f"📊 **Summary:** {narrative}\n\n"
        
        if attempt > 1:
            response += f"_(Succeeded on attempt {attempt})_\n\n"
        
        # Show SQL
        response += f"*Generated SQL:*\n```sql\n{sql}\n```\n\n"
        
        # Show results
        if row_count > 0:
            response += f"*Results:* {row_count} row(s)\n\n"
            
            # Format results as a simple table
            response += self.format_table(results, column_names)
        else:
            response += "📭 *No results found*"
        
        return response
    
    def format_error_response(self, result: dict) -> str:
        """Format error response for Telegram"""
        error = result['error']
        sql = result.get('sql')
        attempt = result.get('attempt', 1)
        
        response = "❌ *Query Failed*\n\n"
        response += f"*Error:*\n`{error}`\n\n"
        
        if sql:
            response += f"*Failed SQL:*\n```sql\n{sql}\n```\n\n"
        
        if attempt > 1:
            response += f"_(Failed after {attempt} attempts)_\n\n"
        
        response += "💡 *Tips:*\n"
        response += "• Try rephrasing your question\n"
        response += "• Be more specific about what you're looking for\n"
        response += "• Use /schema to see available tables and columns"
        
        return response
    
    def format_table(self, results: list, column_names: list, max_rows: int = 20) -> str:
        """Format query results as a Telegram-friendly table"""
        if not results:
            return ""
        
        # Limit rows for display
        display_results = results[:max_rows]
        truncated = len(results) > max_rows
        
        # Create simple text table
        table = "```\n"
        
        # Header
        table += " | ".join(str(col) for col in column_names) + "\n"
        table += "-" * (len(table) - 4) + "\n"
        
        # Rows
        for row in display_results:
            # Convert values to strings and truncate if too long
            row_values = []
            for val in row:
                val_str = str(val) if val is not None else "NULL"
                if len(val_str) > 30:
                    val_str = val_str[:27] + "..."
                row_values.append(val_str)
            
            table += " | ".join(row_values) + "\n"
        
        if truncated:
            table += f"\n... ({len(results) - max_rows} more rows)\n"
            table += "⚠️ *Showing first 20 rows for token optimization*"
        
        table += "\n```"
        
        return table
    
    async def send_long_message(self, update: Update, text: str):
        """Send long messages by splitting if needed (Telegram has 4096 char limit)"""
        max_length = 4000  # Leave some buffer
        
        if len(text) <= max_length:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            # Split by code blocks or natural boundaries
            parts = self.split_message(text, max_length)
            for part in parts:
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
    
    def split_message(self, text: str, max_length: int) -> list:
        """Split message into parts while preserving markdown blocks"""
        parts = []
        current = ""
        
        # Simple split by newlines
        lines = text.split("\n")
        
        for line in lines:
            if len(current) + len(line) + 1 > max_length:
                parts.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        
        if current:
            parts.append(current)
        
        return parts
    
    async def handle_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button clicks"""
        query = update.callback_query
        await query.answer()  # Acknowledge the button click
        
        # Extract the query text from callback_data
        callback_data = query.data
        if callback_data.startswith("query:"):
            natural_query = callback_data[6:]  # Remove "query:" prefix
            
            # Log the button click
            user = update.effective_user
            logger.info(f"User {user.id} ({user.username}) clicked button: {natural_query}")
            
            # Send "thinking" message
            thinking_msg = await query.message.reply_text("🤔 Processing your question...")
            
            try:
                # Query the agent
                result = self.agent.query(natural_query)
                
                # Delete thinking message
                await thinking_msg.delete()
                
                # Format and send response
                if result['success']:
                    # Generate natural language narrative
                    narrative = self.agent.generate_narrative(
                        natural_query=natural_query,
                        sql=result['sql'],
                        results=result['results'][:20],
                        column_names=result['column_names'],
                        row_count=result['row_count']
                    )
                    response = self.format_success_response(result, narrative)
                else:
                    response = self.format_error_response(result)
                
                # Send response
                await self.send_long_message_to_query(query, response)
                
            except Exception as e:
                logger.error(f"Error processing button query: {e}", exc_info=True)
                await thinking_msg.delete()
                await query.message.reply_text(
                    f"❌ *Error*\n\n"
                    f"An unexpected error occurred:\n"
                    f"`{str(e)}`",
                    parse_mode=ParseMode.MARKDOWN
                )
    
    async def send_long_message_to_query(self, query, text: str):
        """Send long messages by splitting if needed (for callback queries)"""
        max_length = 4000
        
        if len(text) <= max_length:
            await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            parts = self.split_message(text, max_length)
            for part in parts:
                await query.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ An error occurred while processing your request. "
                "Please try again later."
            )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("schema", self.schema_command))
        
        # Register callback handler for inline buttons
        application.add_handler(CallbackQueryHandler(self.handle_button_callback))
        
        # Register message handler for queries
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_query
        ))
        
        # Register error handler
        application.add_error_handler(self.error_handler)
        
        # Start polling
        logger.info("Bot is running! Press Ctrl+C to stop.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    try:
        bot = TelegramNLToSQLBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
