from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from utils.database import save_point_of_interest, get_points_of_interest
from utils.geo_utils import calculate_distance, geocode_address, generate_directions_url
import re

# Define conversation states
CHOOSING_POI_ACTION, ENTERING_POI_NAME, ENTERING_POI_DESCRIPTION, ENTERING_POI_LOCATION, ENTERING_POI_ADDRESS = range(5)

async def poi_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display points of interest menu"""
    keyboard = [
        [InlineKeyboardButton("➕ Tambah Tempat", callback_data="poi_add")],
        [InlineKeyboardButton("🔍 Lihat Semua Tempat", callback_data="poi_view_all")],
        [InlineKeyboardButton("🔍 Cari Tempat Terdekat", callback_data="poi_nearby")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🗺️ Tempat Menarik\n\n"
        "Pilih opsi:",
        reply_markup=reply_markup
    )
    return CHOOSING_POI_ACTION

async def handle_poi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle POI menu callback queries"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    
    if action == "add":
        # Start the process to add a new POI
        await query.edit_message_text(
            "➕ Tambah Tempat Menarik\n\n"
            "Kirim nama untuk tempat menarik baru:"
        )
        return ENTERING_POI_NAME
    
    elif action == "view_all":
        # View all points of interest
        points = get_points_of_interest()
        
        if not points:
            await query.edit_message_text("Belum ada tempat menarik yang disimpan.")
            return ConversationHandler.END
        
        response = "📍 Daftar Tempat Menarik\n\n"
        
        for i, point in enumerate(points):
            response += f"{i+1}. *{point['name']}*\n"
            response += f"   {point['description']}\n"
            maps_url = f"https://maps.google.com/?q={point['latitude']},{point['longitude']}"
            response += f"   🔗 [Lihat di Maps]({maps_url})\n\n"
        
        # Add a back button
        keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="poi_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        return CHOOSING_POI_ACTION
    
    elif action == "nearby":
        # Ask for user's current location
        await query.edit_message_text(
            "🔍 Cari Tempat Terdekat\n\n"
            "Silakan kirim lokasi Anda saat ini untuk melihat tempat menarik terdekat."
        )
        
        # Create a keyboard with location button
        await update.callback_query.message.reply_text(
            "Atau klik tombol di bawah:",
            reply_markup=ReplyKeyboardMarkup(
                [[{"text": "📍 Bagikan Lokasi Saat Ini", "request_location": True}]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return ENTERING_POI_LOCATION
    
    elif action == "back":
        # Go back to main POI menu
        await poi_menu(update, context)
        return CHOOSING_POI_ACTION

async def handle_poi_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle POI name input"""
    name = update.message.text
    
    # Store in context for later
    context.user_data['poi_name'] = name
    
    await update.message.reply_text(
        f"🏷️ Nama: {name}\n\n"
        "Sekarang, kirim deskripsi untuk tempat ini:"
    )
    
    return ENTERING_POI_DESCRIPTION

async def handle_poi_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle POI description input"""
    description = update.message.text
    
    # Store in context for later
    context.user_data['poi_description'] = description
    
    await update.message.reply_text(
        f"📝 Deskripsi: {description}\n\n"
        "Sekarang, kirim lokasi untuk tempat ini, atau ketik alamat lengkapnya."
    )
    
    # Create a keyboard with location button
    await update.message.reply_text(
        "Atau klik tombol di bawah untuk memilih lokasi saat ini:",
        reply_markup=ReplyKeyboardMarkup(
            [[{"text": "📍 Gunakan Lokasi Saat Ini", "request_location": True}]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    
    return ENTERING_POI_ADDRESS

async def handle_poi_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle POI address input"""
    # Check if this is a location message
    if update.message.location:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
    else:
        # This is a text message with an address
        address = update.message.text
        
        # Geocode the address
        location_data = geocode_address(address)
        
        if not location_data:
            await update.message.reply_text(
                "❌ Tidak dapat menemukan alamat tersebut. Silakan coba lagi dengan alamat yang lebih spesifik:"
            )
            return ENTERING_POI_ADDRESS
        
        latitude = location_data['latitude']
        longitude = location_data['longitude']
        
        # Inform user about the found address
        await update.message.reply_text(
            f"📍 Alamat ditemukan: {location_data['formatted_address']}"
        )
    
    # Save the POI to database
    user_id = update.effective_user.id
    name = context.user_data.get('poi_name', 'Unnamed Place')
    description = context.user_data.get('poi_description', 'No description')
    
    save_point_of_interest(name, description, latitude, longitude, user_id)
    
    # Clear keyboard
    await update.message.reply_text(
        "✅ Tempat menarik berhasil disimpan!",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Clear conversation data
    context.user_data.pop('poi_name', None)
    context.user_data.pop('poi_description', None)
    
    return ConversationHandler.END

async def handle_poi_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle POI location query"""
    # Check if this is a location message
    if not update.message.location:
        await update.message.reply_text(
            "Silakan kirim lokasi Anda menggunakan tombol 'Bagikan Lokasi'."
        )
        return ENTERING_POI_LOCATION
    
    location = update.message.location
    user_latitude = location.latitude
    user_longitude = location.longitude
    
    # Find nearby POIs
    points = get_points_of_interest()
    
    if not points:
        await update.message.reply_text(
            "Belum ada tempat menarik yang disimpan.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Calculate distance to each POI
    nearby_points = []
    for point in points:
        distance = calculate_distance(
            user_latitude, user_longitude,
            point['latitude'], point['longitude']
        )
        
        nearby_points.append({
            'point': point,
            'distance': distance
        })
    
    # Sort by distance
    nearby_points.sort(key=lambda x: x['distance'])
    
    # Take the 5 nearest points
    nearest_points = nearby_points[:5]
    
    if not nearest_points:
        await update.message.reply_text(
            "Tidak ada tempat menarik yang ditemukan di dekat Anda.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    response = "🔍 Tempat Menarik Terdekat:\n\n"
    
    for i, item in enumerate(nearest_points):
        point = item['point']
        distance = item['distance']
        
        response += f"{i+1}. *{point['name']}*\n"
        response += f"   {point['description']}\n"
        response += f"   📏 Jarak: {distance:.2f} km\n"
        
        # Create directions link
        directions_url = generate_directions_url(
            user_latitude, user_longitude,
            point['latitude'], point['longitude']
        )
        response += f"   🧭 [Petunjuk Arah]({directions_url})\n\n"
    
    # Clear keyboard
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

async def cancel_poi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the POI conversation"""
    await update.message.reply_text(
        "❌ Operasi dibatalkan.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Clear conversation data
    context.user_data.pop('poi_name', None)
    context.user_data.pop('poi_description', None)
    
    return ConversationHandler.END

# Create the conversation handler
poi_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("poi", poi_menu)],
    states={
        CHOOSING_POI_ACTION: [CallbackQueryHandler(handle_poi_callback, pattern=r"^poi_")],
        ENTERING_POI_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poi_name)],
        ENTERING_POI_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poi_description)],
        ENTERING_POI_ADDRESS: [
            MessageHandler(filters.LOCATION, handle_poi_address),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poi_address)
        ],
        ENTERING_POI_LOCATION: [MessageHandler(filters.LOCATION, handle_poi_location)]
    },
    fallbacks=[CommandHandler("cancel", cancel_poi)],
) 