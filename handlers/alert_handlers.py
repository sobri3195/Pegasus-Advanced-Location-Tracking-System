from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from utils.database import get_user_alerts, get_all_user_locations, create_alert, get_db_connection
from utils.geo_utils import calculate_distance
from config.config import ADMIN_ID

async def view_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all alerts for the current user"""
    user_id = update.effective_user.id
    
    # Get unread alerts by default
    unread_only = True
    if context.args and context.args[0].lower() in ('all', 'semua'):
        unread_only = False
    
    alerts = get_user_alerts(user_id, unread_only)
    
    if not alerts:
        msg = "Tidak ada notifikasi baru." if unread_only else "Tidak ada notifikasi."
        await update.message.reply_text(msg)
        return
    
    response = f"📬 {'Notifikasi Belum Dibaca' if unread_only else 'Semua Notifikasi'}\n\n"
    
    for i, alert in enumerate(alerts):
        # Format based on alert type
        if alert['alert_type'] == 'admin_broadcast':
            response += f"{i+1}. 📣 *Pengumuman Admin*\n"
        elif alert['alert_type'] == 'weather':
            response += f"{i+1}. ⚠️ *Peringatan Cuaca*\n"
        else:
            response += f"{i+1}. 🔔 *Notifikasi*\n"
        
        response += f"   {alert['message']}\n"
        response += f"   📅 {alert['created_at']}\n\n"
    
    # Add a button to mark all as read
    keyboard = [[InlineKeyboardButton("✅ Tandai Semua Dibaca", callback_data="alerts_mark_read")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_alerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle alerts callback queries"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    
    if action == "mark":
        # Mark all alerts as read
        conn = get_db_connection()
        conn.execute("UPDATE alerts SET is_read = 1 WHERE user_id = ?", (query.from_user.id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            "✅ Semua notifikasi telah ditandai sebagai dibaca.",
            parse_mode="Markdown"
        )
        
        return

async def send_alert_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send an alert to a specific user (admin only)"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return
    
    # Check if we have the necessary arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "Gunakan format: /alert [user_id] [pesan]\n"
            "Contoh: /alert 123456789 Halo, ini adalah pesan dari admin."
        )
        return
    
    # Extract target user ID and message
    try:
        target_user_id = int(context.args[0])
        message = ' '.join(context.args[1:])
    except ValueError:
        await update.message.reply_text("ID pengguna harus berupa angka.")
        return
    
    # Create alert in database
    create_alert(target_user_id, "admin_message", message)
    
    # Send message to user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🔔 *Pesan dari Admin*\n\n{message}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ Pesan berhasil dikirim ke pengguna {target_user_id}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengirim pesan: {e}")

async def alert_nearby_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send an alert to all users within a certain radius of a location"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return
    
    # Store that we're waiting for a location
    context.user_data['waiting_for_location'] = True
    context.user_data['alert_type'] = 'nearby'
    
    await update.message.reply_text(
        "🔍 Kirim lokasi untuk mengirim peringatan ke pengguna di sekitarnya:",
        reply_markup=ReplyKeyboardMarkup(
            [[{"text": "📍 Pilih Lokasi", "request_location": True}]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

async def handle_alert_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location for alert_nearby_users"""
    # Check if we're waiting for a location
    if not context.user_data.get('waiting_for_location'):
        return
    
    location = update.message.location
    
    # Clear the waiting flag
    context.user_data.pop('waiting_for_location', None)
    
    # Store the location
    context.user_data['alert_latitude'] = location.latitude
    context.user_data['alert_longitude'] = location.longitude
    
    # Ask for the radius
    await update.message.reply_text(
        "Masukkan jarak radius dalam km (1-50):",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Set flag that we're now waiting for radius
    context.user_data['waiting_for_radius'] = True

async def handle_alert_radius(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle radius for alert_nearby_users"""
    # Check if we're waiting for a radius
    if not context.user_data.get('waiting_for_radius'):
        return
    
    # Try to parse radius
    try:
        radius_km = float(update.message.text)
        if radius_km < 1 or radius_km > 50:
            await update.message.reply_text("Radius harus antara 1 dan 50 km. Silakan coba lagi:")
            return
    except ValueError:
        await update.message.reply_text("Masukkan angka yang valid. Silakan coba lagi:")
        return
    
    # Clear the waiting flag
    context.user_data.pop('waiting_for_radius', None)
    
    # Store the radius
    context.user_data['alert_radius'] = radius_km
    
    # Ask for the message
    await update.message.reply_text("Masukkan pesan peringatan yang ingin dikirim:")
    
    # Set flag that we're now waiting for message
    context.user_data['waiting_for_message'] = True

async def handle_alert_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle message for alert_nearby_users"""
    # Check if we're waiting for a message
    if not context.user_data.get('waiting_for_message'):
        return
    
    # Get the message
    message = update.message.text
    
    # Clear the waiting flag
    context.user_data.pop('waiting_for_message', None)
    
    # Get stored location and radius
    latitude = context.user_data.pop('alert_latitude', 0)
    longitude = context.user_data.pop('alert_longitude', 0)
    radius_km = context.user_data.pop('alert_radius', 0)
    
    # Find users within the radius
    locations = get_all_user_locations()
    nearby_users = []
    
    for loc in locations:
        distance = calculate_distance(
            latitude, longitude,
            loc['latitude'], loc['longitude']
        )
        
        if distance <= radius_km:
            nearby_users.append(loc)
    
    if not nearby_users:
        await update.message.reply_text("Tidak ada pengguna dalam radius tersebut.")
        return
    
    # Send alert to all nearby users
    sent_count = 0
    for user in nearby_users:
        # Create alert in database
        create_alert(user['user_id'], "location_alert", message)
        
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"⚠️ *Peringatan Area*\n\n{message}\n\n_(Anda menerima pesan ini karena Anda berada dalam radius {radius_km} km dari lokasi peringatan)_",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception as e:
            print(f"Error sending alert to {user['user_id']}: {e}")
    
    await update.message.reply_text(f"✅ Peringatan terkirim ke {sent_count}/{len(nearby_users)} pengguna dalam radius {radius_km} km.") 