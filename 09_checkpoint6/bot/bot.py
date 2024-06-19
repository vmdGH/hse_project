import logging
import os
import pandas as pd
import requests
import json

from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    # Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

_APP_ADDRESS_UPDATE = "http://app:5001/update_data"
_APP_ADDRESS_SEND = "http://app:5001/send_data"

AUTHORS = os.getenv("AUTHORS").split(',')

CHOICE_SHOW, CHOICE_DOWNLOAD, PREDICT, LOOP = range(4)

keyboard = [
    [InlineKeyboardButton("Да", callback_data="Да")],
    [InlineKeyboardButton("Нет", callback_data="Нет")],
]
_REPLY_MARKUP = InlineKeyboardMarkup(keyboard)



async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Прекращение диалога.
    """
    user = update.message.from_user
    logger.info("Пользователь %s остановил диалог.", user.first_name)

    await update.message.reply_text(
        "Будем на связи.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Начало диалога.
    """
    user = update.effective_user
    logger.info("Пользователь %s начал диалог.", user.first_name)

    await update.message.reply_text(
        f"Привет, {user.first_name}. "
        "В любой момент диалог можно прекратить с помощью команды /stop.\n\n"
        "Чтобы скачать все публикации с прогнозами, введите /download\n"
        "Чтобы показать новые публикации с прогнозами, введите /show\n"
    )
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправить файл с прогнозами. Да/нет 

    """
    user = update.effective_user
    logger.info("Пользователь %s начал функцию download.", user.first_name)

    await update.message.reply_text(
    "Хочешь скачать все статьи?",
        reply_markup=_REPLY_MARKUP,
    )
    return CHOICE_DOWNLOAD
async def choice_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправить файл с прогнозами.    
    """

    query = update.callback_query
    await query.answer()
    answer = query.data

    logger.info("Начинаю функцию choice_download")

    if answer.lower() == "нет":
        logger.info("Пользователь ответил %s. Окончание диалога." % answer)
        await update.callback_query.message.reply_text(
            "Будем на связи.", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        await update.callback_query.message.reply_text("Загружаю данные")
        logger.info("Пользователь ответил %s." % answer)

        answer = requests.post(_APP_ADDRESS_SEND).json()

        df_list = []
        for author in AUTHORS:
            df = pd.DataFrame(answer[author]['articles'])
            df['author'] = author
            df['base_url'] = answer[author]['base_url']
            df['month_activity'] = answer[author]['month_activity']
            df['profitability'] = answer[author]['profitability']
            df['size'] = answer[author]['size']
            df['subscribers'] = answer[author]['subscribers']

            df = df[['author', 'base_url', 'subscribers', 'size', 'month_activity', 'profitability', 'date', 'prediction', 'text', 'ticker']]
            df_list.append(df)
        result = pd.concat(df_list, ignore_index=True)
        result.to_csv('./output/result.csv', index=False, encoding='utf-8')

        logger.info("Результат сохранен локально")

        chat_id = update.effective_chat.id
        await context.bot.send_document(chat_id=chat_id, document='./output/result.csv')
        logger.info("Результат возвращен пользователю")
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправка новых публикаций. Да/нет 
    """
    user = update.effective_user
    logger.info("Пользователь %s начал функцию show.", user.first_name)

    await update.message.reply_text(
    "Хочешь просмотреть новые статьи?",
        reply_markup=_REPLY_MARKUP,
    )
    return CHOICE_SHOW
async def choice_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправить новые публикации.
    """
    query = update.callback_query
    await query.answer()
    answer = query.data

    if answer.lower() == "нет":
        logger.info("Пользователь ответил %s. Окончание диалога." % answer)
        await update.callback_query.message.reply_text(
            "Будем на связи.", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        await update.callback_query.message.reply_text("Проверяю, есть ли новые публикации")
        logger.info("Пользователь ответил %s." % answer)

        answer = requests.post(_APP_ADDRESS_UPDATE).json()
        if  answer:
            await update.callback_query.message.reply_text("Вот список новых публикаций")
            for author in answer:
                    for article in answer[author]['articles']:
                        await update.callback_query.message.reply_text(f"Автор {author}. Опубликовано {article['date']}\n"
                                                                        f"{article['text']}\n"
                                                                        f"Акция: {article['ticker']}\n"
                                                                        f"Прогноз: {article['prediction']}\n"
                                                                    )
        else:
            await update.callback_query.message.reply_text(
                "Новых статей не обнаружено\n"
                "Хотите скачать все статьи?",
                    reply_markup=_REPLY_MARKUP,
                )
            return CHOICE_DOWNLOAD

def main(TOKEN:str) -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        allow_reentry=True,
        entry_points=[CommandHandler("start", start),
                    CommandHandler("download", download),
                    CommandHandler("stop", stop_command),
                    CommandHandler("show", show),],
        states={
            CHOICE_SHOW: [CallbackQueryHandler(choice_show)],
            CHOICE_DOWNLOAD: [CallbackQueryHandler(choice_download)],

        },
        fallbacks=[CommandHandler("stop", stop_command)],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    logger.info(TOKEN)
    main(TOKEN)