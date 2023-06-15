import logging
import os
from dotenv import load_dotenv
from telegram import ParseMode

import notion

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters


PORT = int(os.environ.get('PORT', 5000))
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
load_dotenv()
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Global variables bc i am lazy
CONNECT = 1


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def daily_update(update, context):
    user_name = update.message.from_user.first_name.lower()
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {user_name}! Could I have your Database ID please?"
    )
    return CONNECT


def notion_connect(update, context):
    databaseID = update.message.text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Thank you. Allow me to retrieve your database."
    )
    activities = notion.connectToNotion(databaseID)
    if activities == "":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="The Database ID you provided could not be found. Have you configured your database with us?"
                 "If yes, try again. "
        )
        return CONNECT
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Here are your activities for today:\n{activities}",
            parse_mode=ParseMode.HTML
        )
        # end of conversation
        return ConversationHandler.END


def cancel(update, context):
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Your request has been cancelled."
    )

    # end of conversation
    return ConversationHandler.END


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("goodmorning", daily_update)],
        states={
            CONNECT: [
                CommandHandler('cancel', cancel),
                MessageHandler(Filters.text, notion_connect)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://notion-telegrambot-8af621fe34d8.herokuapp.com/' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
