import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, JobQueue
import datetime

# Import configuration
from config.config import TOKEN, ADMIN_ID, WELCOME_MESSAGE

# Import database utilities
from utils.database import init_db

# Import handlers
from handlers.location_handlers import (
    handle_location, 
    get_all_locations, 
    my_location_history, 
    find_nearby_users,
    share_location_button
)
from handlers.settings_handlers import (
    toggle_tracking_command,
    settings_menu
)
from handlers.admin_handlers import (
    admin_panel,
    broadcast_message,
    export_data,
    admin_generate_report
)
from handlers.poi_handlers import poi_conv_handler
from handlers.alert_handlers import (
    view_alerts,
    send_alert_to_user,
    alert_nearby_users,
    handle_alert_location,
    handle_alert_radius,
    handle_alert_message,
    handle_alerts_callback
)
from handlers.callback_handlers import register_callback_handlers

# Import scheduled tasks
from utils.notifications import (
    check_weather_alerts,
    send_daily_summary,
    check_inactive_users
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Send welcome message when the command /start is issued"""
    user = update.effective_user
    await update.message.reply_text(
        f"{WELCOME_MESSAGE}\n\nHalo {user.first_name}!"
    )

async def help_command(update, context):
    """Send a help message when the command /help is issued"""
    help_text = """
📱 *Bantuan Aplikasi Lacak Lokasi*

*Perintah Umum:*
/start - Memulai bot
/help - Menampilkan bantuan
/share - Mengirim tombol untuk membagikan lokasi
/history [jumlah] - Melihat riwayat lokasi Anda
/nearby [radius] - Mencari pengguna terdekat
/settings - Pengaturan pengguna
/alerts - Melihat notifikasi
/poi - Menu tempat menarik

*Perintah Privasi:*
/tracking [on/off] - Mengaktifkan/menonaktifkan pelacakan

*Perintah Admin:*
/admin - Panel admin
/broadcast [pesan] - Mengirim pesan ke semua pengguna
/report - Menghasilkan laporan pengguna
/export - Mengekspor data lokasi
/alert [user_id] [pesan] - Mengirim pesan ke pengguna tertentu
/alert_nearby - Mengirim peringatan ke pengguna dalam radius
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def error_handler(update, context):
    """Log errors caused by updates"""
    logger.error('Update "%s" caused error "%s"', update, context.error)
    
    # If we can, notify the user that something went wrong
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi nanti."
        )
    
    # Also notify admin about the error
    if ADMIN_ID:
        error_text = f"⚠️ *Error*\n\n```{str(context.error)}```"
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=error_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

def main():
    """Start the bot"""
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Get the job queue
    job_queue = application.job_queue
    
    # Regular commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("share", share_location_button))
    application.add_handler(CommandHandler("history", my_location_history))
    application.add_handler(CommandHandler("nearby", find_nearby_users))
    application.add_handler(CommandHandler("settings", settings_menu))
    application.add_handler(CommandHandler("alerts", view_alerts))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("report", admin_generate_report))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(CommandHandler("alert", send_alert_to_user))
    application.add_handler(CommandHandler("alert_nearby", alert_nearby_users))
    
    # Privacy commands
    application.add_handler(CommandHandler("tracking", toggle_tracking_command))
    
    # Location handling
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    # Special handlers for alert system
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            lambda u: u.message and u.message.chat.type == 'private' and 
            u.message.from_user and 
            u.message.from_user.id == ADMIN_ID and 
            u.message.chat.type == 'private' and 
            getattr(u.message.from_user, 'id', None) == ADMIN_ID
        ),
        handle_alert_message
    ))
    
    # POI conversation handler
    application.add_handler(poi_conv_handler)
    
    # Register all callback handlers
    register_callback_handlers(application)
    
    # Add callback handler for alerts
    application.add_handler(CallbackQueryHandler(handle_alerts_callback, pattern=r"^alerts_"))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Schedule jobs
    # Check weather every 3 hours
    job_queue.run_repeating(check_weather_alerts, interval=10800, first=10)
    
    # Send daily summary at 8:00 AM
    job_queue.run_daily(send_daily_summary, time=datetime.time(hour=8, minute=0))
    
    # Check inactive users once a day
    job_queue.run_daily(check_inactive_users, time=datetime.time(hour=9, minute=0))
    
    # Start the Bot
    application.run_polling()
    
    logger.info("Bot started")

if __name__ == '__main__':
    main() 