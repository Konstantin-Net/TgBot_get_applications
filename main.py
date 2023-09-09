import os
import asyncio
import logging
import functools
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters, ConversationHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Load environment variables and retrieve the TOKEN value.
load_dotenv()
TOKEN = os.environ['TOKEN']

# Initialize logging with custom format and set 'httpx' logs to 'WARNING' level.
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Constants for conversation stages
DESCRIPTION, TERMS, BUDGET, PHONE, CANCEL = range(5)

# Global variables
ROW = 0


async def async_save_to_sheet(*args, **kwargs):
    """Asynchronously saves or updates data to the Google Sheets using a thread pool."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, functools.partial(save_or_update_to_sheet, *args, **kwargs))
        return result


def get_next_row_number(sheet, spreadsheet_id, range_name):
    """Retrieves the next available row number from the Google Sheets."""
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    return len(values) + 1


def get_value_from_sheet(sheet, spreadsheet_id, range_name):
    """
    Fetches the first value from a specified range in the Google Sheets.
    """
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    if values and values[0]:
        return values[0][0]  # Return the first value from the range
    return None  # Return None if the cell is empty


def save_or_update_to_sheet(action, telegram_id=None, username=None, language=None, description=None,
                            terms=None, budget=None, phone=None, date=None, row_number=None):
    """
    Saves or updates data to the Google Sheets based on the specified action.
    Supports creating new entries, updating existing ones, and fetching specific data.
    """
    creds_path = os.environ["CREDENTIALS_PATH"]
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=[
        "https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    spreadsheet_id = os.environ['SPREADSHEET_ID']
    range_name = "application"
    value_input_option = "RAW"
    value_range_body = {
        "values": [[telegram_id, username, language, description, terms, budget, phone, date]]
    }

    if action == "create":
        # Get the next available row number
        next_row = get_next_row_number(sheet, spreadsheet_id, range_name)
        insert_data_option = "INSERT_ROWS"
        sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option,
            body=value_range_body
        ).execute()
        global ROW
        ROW = next_row  # Return the row number of the newly created row
    elif action == "update" and row_number:
        range_name = f"A{row_number}:H{row_number}"
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=value_range_body
        ).execute()
    elif action == "get_man":
        return get_value_from_sheet(sheet, spreadsheet_id, "application!J2")
    elif action == "get_adm":
        return get_value_from_sheet(sheet, spreadsheet_id, "admins!A2")
    else:
        raise ValueError("Invalid action or missing row number for update.")


async def start(update: Update, context: CallbackContext) -> None:
    """
    Initiates the conversation with the user, sends a greeting message, and prompts the user
    for the main functionality of the desired Telegram bot. Also saves initial user details to the Google Sheets.
    """
    user = update.effective_user
    context.user_data["language"] = user.language_code or "en"
    context.user_data["username"] = user.username or "N/A"
    telegram_id = user.id
    username = user.username or "N/A"
    language = user.language_code or "N/A"
    if language == 'ru':
        await update.message.reply_text(
            "Здравствуйте! Мы - студия разработки Raccoonators. Пожалуйста, ответьте на "
            "несколько вопросов и мы постараемся вам помочь."
        )
        await update.message.reply_text("Опишите основной функционал Telegram бота, который вам нужен:")
    else:
        await update.message.reply_text(
            "Hello! Raccoonators team welcomes you! Please, answer a few questions and we will be happy to help you."
        )
        await update.message.reply_text("Describe main functionality of Telegram bot you need:")
    await async_save_to_sheet("create", telegram_id=telegram_id, username=username, language=language,
                              date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row_number=ROW)
    return DESCRIPTION


# Next are the incoming message handlers
async def collect_description(update: Update, context: CallbackContext):
    description = update.message.text
    language = context.user_data["language"]
    await async_save_to_sheet("update", description=description, row_number=ROW)
    if language == 'ru':
        await update.message.reply_text("В течение какого срока вы хотели бы получить готового бота?")
    else:
        await update.message.reply_text("How long would you like to receive a ready-made bot?")
    return TERMS


async def collect_terms(update: Update, context: CallbackContext):
    terms = update.message.text
    language = context.user_data["language"]
    await async_save_to_sheet("update", terms=terms, row_number=ROW)
    if language == 'ru':
        await update.message.reply_text("Каким бюджетом на разработку вы располагаете")
    else:
        await update.message.reply_text("What is your development budget?")
    return BUDGET


async def collect_budget(update: Update, context: CallbackContext):
    budget = update.message.text
    man = save_or_update_to_sheet("get_man")
    language = context.user_data["language"]
    username = context.user_data["username"]
    await async_save_to_sheet("update", budget=budget, row_number=ROW)
    if language == 'ru' and username == "N/A":
        await update.message.reply_text("Укажите номер телефона, привязанный к вашему Telegram-аккаунту, чтобы мы "
                                        "могли с вами связаться.")
        return PHONE
    elif username == "N/A":
        await update.message.reply_text("Please, enter the phone number associated with your Telegram account so "
                                        "that we can contact you.")
        return PHONE
    elif language == 'ru':
        await update.message.reply_text(f"Спасибо! С вами свяжется [наш менеджер](https://t.me/{man}) "
                                        f"как только мы обработаем вашу заявку.", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"Thank you! [Our manager](https://t.me/{man}) will contact you "
                                        f"as soon as we process your application.", parse_mode='Markdown')
    await admins()
    return CANCEL


async def collect_phone(update: Update, context: CallbackContext):
    man = save_or_update_to_sheet("get_man")
    phone = update.message.text
    language = context.user_data["language"]
    await async_save_to_sheet("update", phone=phone, row_number=ROW)
    if language == 'ru':
        await update.message.reply_text(f"Спасибо! С вами свяжется [наш менеджер](https://t.me/{man}) "
                                        f"как только мы обработаем вашу заявку.", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"Thank you! [Our manager](https://t.me/{man}) will contact you "
                                        f"as soon as we process your application.", parse_mode='Markdown')
    await admins()
    return CANCEL


async def admins(*args, **kwargs):
    """Sends a notification to the admin about a new application."""
    bot = Bot(token=TOKEN)
    man = save_or_update_to_sheet("get_adm")
    await bot.send_message(chat_id=man, text="New application")


async def cancel(update: Update, context: CallbackContext):
    language = context.user_data["language"]
    """
    Handles the scenario when the user cancels the operation. Sends a message to the user about restarting the process.
    """
    if language == 'ru':
        await update.message.reply_text("Если вы хотите заполнить заявку ещё раз, введите /start")
    else:
        await update.message.reply_text("If you want to fill out the application again, enter /start")
    return ConversationHandler.END


def main():
    """
    The main entry point for the bot. Sets up handlers, initializes the bot, and starts polling for updates.
    """
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_description)],
            TERMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_terms)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_budget)],
            CANCEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    # Bot initialization
    application = Application.builder().token(TOKEN).build()
    # Registering handlers
    application.add_handler(conversation_handler)
    # Launching a bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()






