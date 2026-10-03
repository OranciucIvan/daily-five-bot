import asyncio
import logging
import os
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import storage
import ai

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "daily_five.db")

BTN_SKIP = "🙅 Skip/Refuse"
BTN_REPORT = "📊 Weekly report"


def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton(BTN_REPORT), KeyboardButton(BTN_SKIP)],
    ], resize_keyboard=True)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    storage.upsert_user(u.id, u.first_name or u.username or "friend")
    await update.message.reply_text(
        "Hi! I'll ask you once a day for 5 good things. Use /addfriend <user_id> to pair with a friend. "
        "Weekly reports auto-delete after 7 days.",
        reply_markup=main_menu(),
    )


async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(update.effective_user.id))


async def cmd_addfriend(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /addfriend <user_id>")
        return
    try:
        friend_id = int(args[0])
    except ValueError:
        await update.message.reply_text("user_id must be a number.")
        return
    if storage.set_friend(update.effective_user.id, friend_id):
        await update.message.reply_text("Friend added. You can now see weekly reports.")
    else:
        await update.message.reply_text("You already have a friend or invalid id.")


async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    entries = storage.weekly_entries(update.effective_user.id)
    lines = []
    for d, text, skipped in entries:
        lines.append(f"{d}: {'skipped' if skipped else text}")
    friend_id = storage.get_friend_id(update.effective_user.id)
    friend_section = ""
    if friend_id:
        friend_entries = storage.weekly_entries(friend_id)
        friend_lines = []
        for d, text, skipped in friend_entries:
            friend_lines.append(f"{d}: {'skipped' if skipped else text}")
        friend_section = "\n\nFriend's report:\n" + ("\n".join(friend_lines) if friend_lines else "No entries yet.")
    await update.message.reply_text("Your weekly report:\n" + "\n".join(lines) + friend_section)


async def cmd_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    entries = storage.weekly_entries(update.effective_user.id)
    summary = ai.weekly_summary(entries)
    await update.message.reply_text(f"AI summary:\n{summary}")


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_SKIP:
        storage.save_entry(update.effective_user.id, skipped=True)
        await update.message.reply_text("Skipped today. That's okay.")
        return
    if text == BTN_REPORT:
        await cmd_report(update, ctx)
        return
    # assume any free text is today's 5 good things
    storage.save_entry(update.effective_user.id, text=text)
    await update.message.reply_text("Saved. Nice noticing!")


async def reminder_loop(app: Application):
    while True:
        await asyncio.sleep(60)
        for chat_id, name in storage.users_with_reminder_due():
            try:
                await app.bot.send_message(
                    chat_id,
                    "Time for your 5 good things today. Reply with 5 points or skip.",
                    reply_markup=main_menu(),
                )
                storage.mark_reminded(chat_id)
            except Exception as exc:
                logging.warning("reminder failed %s: %s", chat_id, exc)


def main():
    storage.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("addfriend", cmd_addfriend))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    async def post_init(application):
        asyncio.create_task(reminder_loop(application))

    app.post_init = post_init
    app.run_polling()


if __name__ == "__main__":
    main()
