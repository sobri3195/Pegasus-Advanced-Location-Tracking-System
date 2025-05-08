from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.database import get_all_user_locations, create_alert
from config.config import ADMIN_ID
import json

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display admin panel with options"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 Lihat Semua Lokasi", callback_data="admin_all_locations")],
        [InlineKeyboardButton("📊 Statistik Pengguna", callback_data="admin_stats")],
        [InlineKeyboardButton("📣 Kirim Notifikasi", callback_data="admin_notify")],
        [InlineKeyboardButton("🗺️ Peta Semua Pengguna", callback_data="admin_map")],
        [InlineKeyboardButton("⚙️ Pengaturan Admin", callback_data="admin_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 Panel Admin\n\n"
        "Silakan pilih opsi:",
        reply_markup=reply_markup
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callback queries"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    
    if action == "all_locations":
        # Get all locations and send them as a list
        locations = get_all_user_locations()
        
        if not locations:
            await query.edit_message_text("Belum ada lokasi pengguna yang tersimpan.")
            return
        
        response = "🌍 Daftar Lokasi Pengguna:\n\n"
        for i, loc in enumerate(locations):
            user_info = f"{loc['full_name']} (@{loc['username']})" if loc['username'] else loc['full_name']
            maps_url = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
            
            response += f"{i+1}. {user_info}\n"
            response += f"   🔗 <a href='{maps_url}'>Lihat di Maps</a>\n"
            response += f"   🕒 Terakhir: {loc['last_updated']}\n\n"
        
        # If response is too long, split it
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await context.bot.send_message(
                    chat_id=query.message.chat_id, 
                    text=chunk,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
        else:
            await query.edit_message_text(
                response,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    
    elif action == "stats":
        # Show user statistics
        locations = get_all_user_locations()
        
        total_users = len(locations)
        active_today = sum(1 for loc in locations if "T" in loc['last_updated'] and loc['last_updated'].split('T')[0] == "today")  # Simplified check
        
        response = "📊 Statistik Pengguna\n\n"
        response += f"👥 Total Pengguna: {total_users}\n"
        response += f"✅ Aktif Hari Ini: {active_today}\n"
        
        await query.edit_message_text(response)
    
    elif action == "notify":
        # Show notification options
        keyboard = [
            [InlineKeyboardButton("🔔 Notifikasi ke Semua", callback_data="notify_all")],
            [InlineKeyboardButton("👤 Notifikasi ke Pengguna Tertentu", callback_data="notify_specific")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="admin_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📣 Kirim Notifikasi\n\n"
            "Pilih jenis notifikasi yang ingin Anda kirim:",
            reply_markup=reply_markup
        )
    
    elif action == "map":
        # Generate map with all users
        locations = get_all_user_locations()
        
        if not locations:
            await query.edit_message_text("Belum ada lokasi pengguna yang tersimpan.")
            return
        
        # Store locations in context to be used for map generation
        context.user_data['map_locations'] = [
            {
                'name': loc['full_name'] or f"User {loc['user_id']}",
                'lat': loc['latitude'],
                'lon': loc['longitude']
            } for loc in locations
        ]
        
        # Generate static map URL with markers for all users
        # For simplicity, we'll just use Google Maps with multiple markers
        map_url = "https://www.google.com/maps/dir/"
        for loc in context.user_data['map_locations']:
            map_url += f"{loc['lat']},{loc['lon']}/"
        
        await query.edit_message_text(
            "🗺️ Peta Semua Pengguna\n\n"
            f"<a href='{map_url}'>Lihat Peta</a>",
            parse_mode="HTML"
        )
    
    elif action == "settings":
        # Admin settings
        keyboard = [
            [InlineKeyboardButton("🔐 Konfigurasi Bot", callback_data="admin_config")],
            [InlineKeyboardButton("🔄 Reset Database", callback_data="admin_reset")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="admin_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ Pengaturan Admin\n\n"
            "Pilih opsi:",
            reply_markup=reply_markup
        )
    
    elif action == "back":
        # Go back to admin panel
        await admin_panel(update, context)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to all users"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return
    
    # Check if we have a message to broadcast
    if not context.args:
        await update.message.reply_text(
            "Gunakan format: /broadcast [pesan]\n"
            "Contoh: /broadcast Halo semua pengguna!"
        )
        return
    
    message = ' '.join(context.args)
    
    # Get all users
    locations = get_all_user_locations()
    sent_count = 0
    
    # Create alert for all users
    for loc in locations:
        create_alert(loc['user_id'], "admin_broadcast", message)
        
        try:
            await context.bot.send_message(
                chat_id=loc['user_id'],
                text=f"📣 *Pengumuman dari Admin*\n\n{message}",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception as e:
            print(f"Error sending message to {loc['user_id']}: {e}")
    
    await update.message.reply_text(f"✅ Pesan terkirim ke {sent_count}/{len(locations)} pengguna.")

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all location data as JSON"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return
    
    locations = get_all_user_locations()
    
    # Convert to serializable format
    export_data = []
    for loc in locations:
        export_data.append({
            'user_id': loc['user_id'],
            'username': loc['username'],
            'full_name': loc['full_name'],
            'latitude': loc['latitude'],
            'longitude': loc['longitude'],
            'last_updated': loc['last_updated'],
            'tracking_enabled': loc['tracking_enabled']
        })
    
    # Save to file
    with open('data/export.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    # Send file to admin
    await update.message.reply_document(
        document=open('data/export.json', 'rb'),
        caption="📊 Ekspor data lokasi pengguna"
    )

async def admin_generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a report of user activity"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return
    
    locations = get_all_user_locations()
    
    # Generate a simple report
    report = "📊 Laporan Aktivitas Pengguna\n\n"
    report += f"Total Pengguna: {len(locations)}\n\n"
    
    # Count active users by time period
    today_active = 0
    week_active = 0
    month_active = 0
    
    # Placeholder logic - in a real app, you'd check dates properly
    for loc in locations:
        # Simplified for demonstration
        today_active += 1 if "2023-" in loc['last_updated'] else 0
        week_active += 1 if "2023-" in loc['last_updated'] else 0
        month_active += 1 if "2023-" in loc['last_updated'] else 0
    
    report += f"Aktif Hari Ini: {today_active}\n"
    report += f"Aktif Minggu Ini: {week_active}\n"
    report += f"Aktif Bulan Ini: {month_active}\n\n"
    
    report += "10 Pengguna Terakhir Aktif:\n"
    # Sort by last_updated and take the 10 most recent
    recent_users = sorted(locations, key=lambda x: x['last_updated'], reverse=True)[:10]
    
    for i, user in enumerate(recent_users):
        user_info = f"{user['full_name']} (@{user['username']})" if user['username'] else user['full_name']
        report += f"{i+1}. {user_info} - {user['last_updated']}\n"
    
    await update.message.reply_text(report) 