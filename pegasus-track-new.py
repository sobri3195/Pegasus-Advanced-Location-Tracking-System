import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import json

conn = sqlite3.connect('locations.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, username TEXT, latitude REAL, longitude REAL)''')
conn.commit()

TOKEN = "TOKEN_TELE"
ADMIN_ID = 0  # Replace with your actual Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Hai {user.first_name}! Kirim lokasi Anda untuk menyimpannya.",
        reply_markup=ReplyKeyboardMarkup([[{"text": "Share Location", "request_location": True}]], one_time_keyboard=True)
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user_id = update.effective_user.id
    username = update.effective_user.username

    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", 
                   (user_id, username, location.latitude, location.longitude))
    conn.commit()

    await update.message.reply_text("Lokasi Anda berhasil disimpan!")

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:  
        await update.message.reply_text("Anda bukan admin!")
        return

    cursor.execute("SELECT username, latitude, longitude FROM users")
    locations = cursor.fetchall()

    response = "Daftar Lokasi Pengguna:\n"
    for loc in locations:
        response += f"{loc[0]}: https://maps.google.com/?q={loc[1]},{loc[2]}\n"

    await update.message.reply_text(response)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CommandHandler("get_location", get_location))

    app.run_polling()

if __name__ == "__main__":
    main()