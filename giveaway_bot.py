import logging
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

giveaways = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎉 **Привет! Я бот для проведения розыгрышей в каналах.**\n\n"
        "**Как запустить конкурс:**\n"
        "1. Добавьте меня в свой канал как Администратора с правом публикации.\n"
        "2. Напишите мне в личные сообщения команду в одну строчку:\n\n"
        "`/giveaway @имя_канала количество_победителей приз`",
        parse_mode="Markdown"
    )

async def start_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Неверный формат! Используйте: `/giveaway @имя_канала количество_победителей приз`", parse_mode="Markdown")
        return

    channel_username = context.args
    try:
        winners_count = int(context.args)
        if winners_count <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Количество победителей должно быть числом больше нуля!")
        return

    prize = " ".join(context.args[2:])
    keyboard = [[InlineKeyboardButton("🎯 Участвовать", callback_data=f"join_{winners_count}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"🎉 **НОВЫЙ РОЗЫГРЫШ!** 🎉\n\n🎁 Приз: **{prize}**\n👥 Количество победителей: **{winners_count}**\n\nНажмите кнопку ниже!"

    try:
        channel_msg = await context.bot.send_message(chat_id=channel_username, text=text, reply_markup=reply_markup, parse_mode="Markdown")
        giveaways[channel_msg.message_id] = set()
        await update.message.reply_text(
            f"✅ Розыгрыш опубликован в {channel_username}!\n🆔 ID сообщения: `{channel_msg.message_id}`\n\n"
            f"Для завершения введите:\n`/finish {channel_username} {channel_msg.message_id} {winners_count}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка публикации. Убедитесь, что бот админ в канале. Ошибка: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    msg_id = query.message.message_id

    if msg_id not in giveaways:
        giveaways[msg_id] = set()

    if user_id in giveaways[msg_id]:
        await context.bot.send_message(chat_id=user_id, text="ℹ️ Вы уже участвуете!")
    else:
        giveaways[msg_id].add(user_id)
        await context.bot.send_message(chat_id=user_id, text="🎉 Вы успешно зарегистрированы!")

async def finish_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Формат: `/finish @имя_канала ID_сообщения количество_победителей`", parse_mode="Markdown")
        return

    channel_username = context.args
    try:
        msg_id = int(context.args)
        requested_winners = int(context.args)
    except ValueError:
        await update.message.reply_text("❌ ID и количество победителей должны быть числами!")
        return

    if msg_id not in giveaways or not giveaways[msg_id]:
        await update.message.reply_text("❌ Для этого сообщения нет участников!")
        return

    participants = list(giveaways[msg_id])
    lucky_winners = random.sample(participants, min(requested_winners, len(participants)))

    winners_mentions = []
    for idx, w_id in enumerate(lucky_winners, start=1):
        try:
            user_chat = await context.bot.get_chat(w_id)
            name = f"@{user_chat.username}" if user_chat.username else (user_chat.first_name or "Участник")
            winners_mentions.append(f"{idx}. {name} (ID: {w_id})")
        except Exception:
            winners_mentions.append(f"{idx}. Участник [ID: {w_id}]")

    result_text = f"🎉 **ИТОГИ РОЗЫГРЫША!** 🎉\n\nПобедители:\n" + "\n".join(winners_mentions)
    
    try:
        await context.bot.send_message(chat_id=channel_username, text=result_text, reply_to_message_id=msg_id, parse_mode="Markdown")
        await update.message.reply_text("✅ Итоги опубликованы в канале!")
        del giveaways[msg_id]
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка публикации итогов: {e}")

def main():
    TOKEN = "8991023395:AAFlvladXmCZclRGW2-iEa55bDFGw88q30A"
    
    # Стандартное официальное подключение без прокси для хостинга
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("giveaway", start_giveaway))
    app.add_handler(CommandHandler("finish", finish_giveaway))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот успешно запущен на хостинге и слушает команды...")
    app.run_polling()

if __name__ == '__main__':
    main()
