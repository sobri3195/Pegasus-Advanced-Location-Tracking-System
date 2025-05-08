from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.database import toggle_tracking, update_user_settings, get_user_settings
from config.config import ADMIN_ID

async def toggle_tracking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle location tracking on/off"""
    user_id = update.effective_user.id
    
    # Check if we should enable or disable tracking
    enable = True
    if context.args and context.args[0].lower() in ('off', 'disable', '0', 'false'):
        enable = False
    
    # Update tracking status in database
    toggle_tracking(user_id, enable)
    
    if enable:
        await update.message.reply_text("✅ Pelacakan lokasi telah diaktifkan. Admin akan dapat melihat lokasi Anda.")
    else:
        await update.message.reply_text("❌ Pelacakan lokasi telah dinonaktifkan. Admin tidak akan dapat melihat lokasi Anda.")

async def privacy_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage privacy settings"""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    
    # Current privacy level
    current_level = settings['privacy_level'] if settings else 1
    
    # Privacy levels explanation
    levels = {
        1: "Normal (Semua admin dapat melihat lokasi Anda)",
        2: "Terbatas (Hanya admin utama yang dapat melihat lokasi Anda)",
        3: "Privat (Lokasi Anda tidak akan dibagikan ke siapapun)"
    }
    
    # Create keyboard for privacy levels
    keyboard = []
    for level, description in levels.items():
        text = f"✓ {description}" if level == current_level else description
        keyboard.append([InlineKeyboardButton(text, callback_data=f"privacy_{level}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔒 Pengaturan Privasi\n\n"
        "Pilih tingkat privasi yang Anda inginkan:",
        reply_markup=reply_markup
    )

async def handle_privacy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle privacy setting callback queries"""
    query = update.callback_query
    await query.answer()
    
    # Extract privacy level from callback data
    level = int(query.data.split('_')[1])
    
    # Update user settings
    update_user_settings(query.from_user.id, privacy_level=level)
    
    # Get level description
    levels = {
        1: "Normal (Semua admin dapat melihat lokasi Anda)",
        2: "Terbatas (Hanya admin utama yang dapat melihat lokasi Anda)",
        3: "Privat (Lokasi Anda tidak akan dibagikan ke siapapun)"
    }
    
    await query.edit_message_text(
        f"🔒 Pengaturan Privasi\n\n"
        f"Privasi diatur ke: {levels[level]}"
    )

async def notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage notification settings"""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    
    # Current notification status
    notifications_enabled = settings['notifications_enabled'] if settings else True
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✓ Aktif" if notifications_enabled else "Aktif", 
                callback_data="notif_1"
            ),
            InlineKeyboardButton(
                "✓ Nonaktif" if not notifications_enabled else "Nonaktif", 
                callback_data="notif_0"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔔 Pengaturan Notifikasi\n\n"
        "Apakah Anda ingin menerima notifikasi?",
        reply_markup=reply_markup
    )

async def handle_notification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notification setting callback queries"""
    query = update.callback_query
    await query.answer()
    
    # Extract notification setting from callback data
    enabled = query.data.split('_')[1] == "1"
    
    # Update user settings
    update_user_settings(query.from_user.id, notifications_enabled=enabled)
    
    await query.edit_message_text(
        f"🔔 Pengaturan Notifikasi\n\n"
        f"Notifikasi: {'Aktif' if enabled else 'Nonaktif'}"
    )

async def language_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage language settings"""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    
    # Current language
    current_lang = settings['language'] if settings else 'id'
    
    # Available languages
    languages = {
        'id': 'Bahasa Indonesia',
        'en': 'English'
    }
    
    # Create keyboard for languages
    keyboard = []
    for lang_code, lang_name in languages.items():
        text = f"✓ {lang_name}" if lang_code == current_lang else lang_name
        keyboard.append([InlineKeyboardButton(text, callback_data=f"lang_{lang_code}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 Pengaturan Bahasa\n\n"
        "Pilih bahasa yang Anda inginkan:",
        reply_markup=reply_markup
    )

async def handle_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language setting callback queries"""
    query = update.callback_query
    await query.answer()
    
    # Extract language from callback data
    lang = query.data.split('_')[1]
    
    # Update user settings
    update_user_settings(query.from_user.id, language=lang)
    
    # Messages based on language
    messages = {
        'id': "Bahasa diubah ke Bahasa Indonesia",
        'en': "Language changed to English"
    }
    
    await query.edit_message_text(
        f"🌐 Pengaturan Bahasa\n\n"
        f"{messages[lang]}"
    )

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main settings menu"""
    keyboard = [
        [InlineKeyboardButton("🔒 Pengaturan Privasi", callback_data="settings_privacy")],
        [InlineKeyboardButton("🔔 Pengaturan Notifikasi", callback_data="settings_notifications")],
        [InlineKeyboardButton("🌐 Pengaturan Bahasa", callback_data="settings_language")],
        [InlineKeyboardButton("📡 Pelacakan Lokasi", callback_data="settings_tracking")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ Menu Pengaturan\n\n"
        "Silakan pilih pengaturan yang ingin Anda ubah:",
        reply_markup=reply_markup
    )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    setting_type = query.data.split('_')[1]
    
    if setting_type == "privacy":
        await privacy_settings(update, context)
    elif setting_type == "notifications":
        await notification_settings(update, context)
    elif setting_type == "language":
        await language_settings(update, context)
    elif setting_type == "tracking":
        # Create tracking toggle buttons
        user_id = query.from_user.id
        settings = get_user_settings(user_id)
        tracking_enabled = settings.get('tracking_enabled', True)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✓ Aktif" if tracking_enabled else "Aktif", 
                    callback_data="tracking_1"
                ),
                InlineKeyboardButton(
                    "✓ Nonaktif" if not tracking_enabled else "Nonaktif", 
                    callback_data="tracking_0"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📡 Pelacakan Lokasi\n\n"
            "Apakah Anda ingin mengaktifkan pelacakan lokasi?",
            reply_markup=reply_markup
        ) 