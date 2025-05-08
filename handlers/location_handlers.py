from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.database import save_user_location, get_all_user_locations, get_user_location_history
from utils.geo_utils import reverse_geocode, calculate_distance, get_weather, generate_directions_url
from config.config import ADMIN_ID, LOCATION_SAVED

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when a user sends their location"""
    location = update.message.location
    user = update.effective_user
    user_id = user.id
    username = user.username or "Unknown"
    full_name = f"{user.first_name} {user.last_name or ''}"
    
    # Save location to database
    save_user_location(user_id, username, full_name, location.latitude, location.longitude)
    
    # Try to get address from coordinates
    address = reverse_geocode(location.latitude, location.longitude)
    address_text = f"\nLokasi: {address}" if address else ""
    
    # Try to get weather
    weather = get_weather(location.latitude, location.longitude)
    weather_text = ""
    if weather:
        weather_text = f"\nCuaca: {weather['description']}, {weather['temperature']}°C, Kelembaban: {weather['humidity']}%"
    
    await update.message.reply_text(
        f"{LOCATION_SAVED}{address_text}{weather_text}"
    )

async def get_all_locations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get all user locations (admin only)"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Anda bukan admin!")
        return

    locations = get_all_user_locations()
    
    if not locations:
        await update.message.reply_text("Belum ada lokasi pengguna yang tersimpan.")
        return
    
    response = "Daftar Lokasi Pengguna:\n\n"
    for loc in locations:
        address = reverse_geocode(loc['latitude'], loc['longitude']) or "Alamat tidak diketahui"
        user_info = f"{loc['full_name']} (@{loc['username']})" if loc['username'] else loc['full_name']
        maps_url = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
        
        response += f"🧍 {user_info}\n"
        response += f"📍 {address}\n"
        response += f"🔗 <a href='{maps_url}'>Lihat di Maps</a>\n"
        response += f"🕒 Terakhir diperbarui: {loc['last_updated']}\n\n"
    
    await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

async def my_location_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their own location history"""
    user_id = update.effective_user.id
    
    # Default to 5 locations, but allow specifying more
    limit = 5
    if context.args and context.args[0].isdigit():
        limit = min(int(context.args[0]), 20)  # Cap at 20 locations
    
    history = get_user_location_history(user_id, limit)
    
    if not history:
        await update.message.reply_text("Anda belum memiliki riwayat lokasi.")
        return
    
    response = f"🕒 Riwayat {len(history)} Lokasi Terakhir Anda:\n\n"
    
    for i, loc in enumerate(history):
        address = reverse_geocode(loc['latitude'], loc['longitude']) or "Alamat tidak diketahui"
        maps_url = f"https://maps.google.com/?q={loc['latitude']},{loc['longitude']}"
        
        response += f"{i+1}. {address}\n"
        response += f"   📅 {loc['timestamp']}\n"
        response += f"   🔗 <a href='{maps_url}'>Lihat di Maps</a>\n\n"
    
    await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

async def find_nearby_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Find users near the current user's location"""
    user_id = update.effective_user.id
    
    # Default radius 5km, but allow specifying different radius
    radius_km = 5
    if context.args and context.args[0].isdigit():
        radius_km = min(int(context.args[0]), 50)  # Cap at 50km
    
    # Get current user's location
    locations = get_all_user_locations()
    current_user = None
    for loc in locations:
        if loc['user_id'] == user_id:
            current_user = loc
            break
    
    if not current_user:
        await update.message.reply_text("Anda belum membagikan lokasi Anda. Silakan bagikan lokasi Anda terlebih dahulu.")
        return
    
    # Find nearby users
    nearby_users = []
    for loc in locations:
        if loc['user_id'] == user_id:
            continue  # Skip current user
        
        distance = calculate_distance(
            current_user['latitude'], current_user['longitude'],
            loc['latitude'], loc['longitude']
        )
        
        if distance <= radius_km:
            nearby_users.append({
                'user': loc,
                'distance': distance
            })
    
    if not nearby_users:
        await update.message.reply_text(f"Tidak ada pengguna lain dalam radius {radius_km} km dari lokasi Anda.")
        return
    
    # Sort by distance
    nearby_users.sort(key=lambda x: x['distance'])
    
    response = f"🔍 Pengguna dalam radius {radius_km} km dari Anda:\n\n"
    
    for item in nearby_users:
        user = item['user']
        distance = item['distance']
        user_info = f"{user['full_name']} (@{user['username']})" if user['username'] else user['full_name']
        
        response += f"🧍 {user_info}\n"
        response += f"📏 Jarak: {distance:.2f} km\n"
        
        # Generate directions link
        directions = generate_directions_url(
            current_user['latitude'], current_user['longitude'],
            user['latitude'], user['longitude']
        )
        response += f"🧭 <a href='{directions}'>Petunjuk Arah</a>\n\n"
    
    await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

async def share_location_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a button that allows users to share their location"""
    await update.message.reply_text(
        "Silakan bagikan lokasi Anda:",
        reply_markup=ReplyKeyboardMarkup(
            [[{"text": "📍 Bagikan Lokasi Saat Ini", "request_location": True}]],
            resize_keyboard=True
        )
    ) 