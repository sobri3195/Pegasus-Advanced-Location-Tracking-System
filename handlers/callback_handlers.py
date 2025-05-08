from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from handlers.admin_handlers import handle_admin_callback
from handlers.settings_handlers import handle_privacy_callback, handle_notification_callback, handle_language_callback, handle_settings_callback
from utils.database import toggle_tracking

async def handle_tracking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tracking toggle callback queries"""
    query = update.callback_query
    await query.answer()
    
    # Extract tracking setting from callback data
    enabled = query.data.split('_')[1] == "1"
    
    # Update tracking status
    toggle_tracking(query.from_user.id, enabled)
    
    await query.edit_message_text(
        f"📡 Pelacakan Lokasi\n\n"
        f"Pelacakan: {'✅ Aktif' if enabled else '❌ Nonaktif'}"
    )

async def handle_notify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notification callback queries"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    
    if action == "all":
        # Store that we're going to notify all users
        context.user_data['notify_target'] = 'all'
        
        await query.edit_message_text(
            "📣 Notifikasi ke Semua Pengguna\n\n"
            "Ketik pesan yang ingin dikirim ke semua pengguna:"
        )
        
        # Switch to message handler for the text
        return True
    
    elif action == "specific":
        # Handle specific user notification
        await query.edit_message_text(
            "📣 Notifikasi ke Pengguna Tertentu\n\n"
            "Masukkan ID pengguna yang ingin diberi notifikasi:"
        )
        
        # Switch to message handler for the user ID
        context.user_data['notify_target'] = 'specific'
        return True

# Register all callback handlers
def register_callback_handlers(application):
    """Register all callback query handlers"""
    # Admin callbacks
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r"^admin_"))
    
    # Settings callbacks
    application.add_handler(CallbackQueryHandler(handle_settings_callback, pattern=r"^settings_"))
    application.add_handler(CallbackQueryHandler(handle_privacy_callback, pattern=r"^privacy_"))
    application.add_handler(CallbackQueryHandler(handle_notification_callback, pattern=r"^notif_"))
    application.add_handler(CallbackQueryHandler(handle_language_callback, pattern=r"^lang_"))
    application.add_handler(CallbackQueryHandler(handle_tracking_callback, pattern=r"^tracking_"))
    
    # POI callbacks are handled by the conversation handler 