import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import processor

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Dictionary to store user context (text from last PDF)
user_context = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and instructions."""
    welcome_text = (
        "👋 Welcome to *BrainyEduBot*! \n\n"
        "I am your AI Study Companion. How I can help you: \n"
        "1. 📄 *Upload a PDF*: I'll summarize it into study notes.\n"
        "2. 💬 *Ask Questions*: After uploading, ask me anything about the document.\n"
        "3. 📝 *Direct Text*: Send me any text, and I'll summarize it for you.\n\n"
        "Ready to start? Send me a PDF or some text!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles PDF file uploads."""
    doc = update.message.document
    
    if doc.mime_type != 'application/pdf':
        await update.message.reply_text("❌ Please upload a PDF document.")
        return

    wait_message = await update.message.reply_text("📥 Downloading and processing your document... please wait.")
    
    # Download the file
    file = await context.bot.get_file(doc.file_id)
    file_path = f"temp_{doc.file_name}"
    await file.download_to_drive(file_path)
    
    # Extract text
    text = processor.extract_text_from_pdf(file_path)
    
    if text:
        # Store context for follow-up questions
        user_context[update.effective_user.id] = text
        
        # Generate summary
        await wait_message.edit_text("🤖 Generating study notes...")
        summary = processor.generate_study_notes(text)
        
        # Send summary in chunks if it's too long for Telegram (4096 chars)
        if len(summary) > 4000:
            for i in range(0, len(summary), 4000):
                await update.message.reply_text(summary[i:i+4000], parse_mode='Markdown')
        else:
            await update.message.reply_text(summary, parse_mode='Markdown')
        
        await update.message.reply_text("💡 You can now ask me any questions about this document!")
    else:
        await wait_message.edit_text("❌ Failed to extract text from the PDF. It might be an image-based PDF or encrypted.")
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages (summarization or Q&A)."""
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # If the user has a context (uploaded a PDF), treat this as a question
    if user_id in user_context:
        wait_message = await update.message.reply_text("🤔 Thinking...")
        answer = processor.answer_question(user_context[user_id], user_text)
        await wait_message.edit_text(answer, parse_mode='Markdown')
    else:
        # Otherwise, treat it as text to be summarized
        wait_message = await update.message.reply_text("📜 Summarizing your text...")
        summary = processor.generate_study_notes(user_text)
        await wait_message.edit_text(summary, parse_mode='Markdown')

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file.")
    else:
        app = ApplicationBuilder().token(token).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", start))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("Bot is running...")
        app.run_polling()
