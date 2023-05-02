import logging

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler

from db.db import Session, User
from send_sheets import send_data

from config import TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

session = Session()

MUSCLE, EXECISE, WEIGHT, REPETS, SHEET = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
    1. Создайте таблицу - https://docs.google.com/spreadsheets/u/0/ 
    2. В настройках доступа добавьте пользователя в качестве редактора:
    gymstat@keen-phalanx-385315.iam.gserviceaccount.com
    3. Скопируйте id таблицы из url`a 
    (примерный формат: '1wHvw2VWglwWZ-AyQBv0cVWUKWzZgvmYKidPCX5-5HZg')
    4. Вызовите метод /send_id {sheet_id}
    5. Вызовите метод /add_workout для добавления записи (/cancel - отмена)
    """
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=text)

    # keyboard = [
    #     [
    #         InlineKeyboardButton("Option 1", callback_data="1"),
    #         InlineKeyboardButton("Option 2", callback_data="2"),
    #     ],
    #     [InlineKeyboardButton("Option 3", callback_data="3")],
    # ]
    #
    # reply_markup = InlineKeyboardMarkup(keyboard)
    #
    # await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if len(context.args) == 1:
        sheet_id = context.args[0]
        user = session.query(User).filter_by(tg_id=tg_user.id).first()
        # print(user)
        if user:
            user.sheet_id = sheet_id
            session.commit()
        else:
            user = User(tg_id=tg_user.id, name=tg_user.name, sheet_id=sheet_id)
            session.add(user)
            session.commit()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Добавлен {sheet_id}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Введите корректный sheet id.\n /send_id {sheet_id}")


async def add_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    user = session.query(User).filter_by(tg_id=tg_user.id).first()
    if not user:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Вы не добавили sheet id! Смотрите /start")
    else:
        reply_keyboard = [["Спина", "Грудь"], ["Ноги", "Плечи"], ["Руки", "Пресс"]]

        await update.message.reply_text(
            "Выберите группу мышц",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Группа мышцы"
            ),
        )
        return EXECISE


async def add_execise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    muscle = update.message.text
    dct_execises = {"Спина": [["Становая тяга", "Подтягивания", "Гиперэкстенция"],
                              ["Тяга штанги к поясу", "Тяга блока к поясу"], ["Тяга гантели к поясу",
                                                                              "Тяга блока к подбородку"]],
                    "Грудь": [["Жим штанги лёжа", "Жим штанги в наклоне", "Жим гантелей"], ["Жим гантелей в наклоне",
                                                                                            "Бочка с гантелями"],
                              ["Бочка в тренажере", "Отжимания на брусьях"]],
                    "Ноги": [["Присед", "Толчок плиты"], ["Стульчик", "Икры"]],
                    "Плечи": [["Армейскй жим", "Жим гантелей"], ["Тяга к ушам",
                                                                 "Вбок хуяришь", "Вперёд хуяришь"]],
                    "Руки": [["Гантели на бицепс", "Изогнутый гриф на бицепс"], ["Гантели на трицепс",
                                                                                 "Французский жим", "Бычьи яйцы"]],
                    "Пресс": [["Пресс для девочек", "И для пидоров"]]
                    }
    reply_keyboard = dct_execises[muscle]
    logger.info("Группа мышц пользователя %s: %s", user.first_name, muscle)
    await update.message.reply_text(
        "Выберите название упражнения",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Название упражнения"
        ),
    )
    return WEIGHT


async def add_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    execise = update.message.text
    logger.info("Упражнение пользователя %s: %s", user.first_name, execise)
    us = session.query(User).filter_by(tg_id=user.id).first()
    us.execise = execise
    session.commit()

    await update.message.reply_text("Напишите вес",
                                    reply_markup=ReplyKeyboardRemove())

    return REPETS


async def add_repets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    weight = update.message.text
    logger.info("Вес: %s", weight)
    us = session.query(User).filter_by(tg_id=user.id).first()
    us.weight = weight
    session.commit()
    await update.message.reply_text("Напишите количество повторений")

    return SHEET


async def send_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    repeats = update.message.text
    logger.info("Количество повторений: %s", repeats)
    us = session.query(User).filter_by(tg_id=user.id).first()
    us.repeats = repeats
    session.commit()

    send_data(us.sheet_id, us.execise, us.weight, us.repeats)

    await update.message.reply_text("Запись отправлена")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Отмена", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    send_id_handler = CommandHandler('send_id', send_id)
    workout_handler = ConversationHandler(
        entry_points=[CommandHandler("add_workout", add_workout)],
        states={
            EXECISE: [MessageHandler(filters.Regex("^(Спина|Грудь|Ноги|Плечи|Руки|Пресс)$"),
                                     add_execise)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_weight)],
            REPETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_repets)],
            SHEET: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sheet)]

        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(start_handler)
    application.add_handler(send_id_handler)
    application.add_handler(workout_handler)

    application.run_polling()
