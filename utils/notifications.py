import datetime
from utils.database import get_all_user_locations, create_alert, get_user_settings
from utils.geo_utils import get_weather
from config.config import ADMIN_ID

async def check_weather_alerts(context):
    """Check weather conditions and send alerts if necessary"""
    # Get all users with tracking enabled
    locations = get_all_user_locations()
    
    for loc in locations:
        # Check user settings
        settings = get_user_settings(loc['user_id'])
        
        # Skip users who have disabled notifications
        if not settings['notifications_enabled']:
            continue
        
        # Get weather for user's location
        weather = get_weather(loc['latitude'], loc['longitude'])
        
        if not weather:
            continue
        
        # Check for severe weather conditions
        alerts = []
        
        # Heavy rain
        if 'rain' in weather['description'].lower() and 'heavy' in weather['description'].lower():
            alerts.append("Hujan lebat terdeteksi di lokasi Anda. Berhati-hatilah saat bepergian.")
        
        # Extreme temperatures
        if weather['temperature'] > 35:
            alerts.append(f"Suhu sangat tinggi ({weather['temperature']}°C) di lokasi Anda. Jaga hidrasi dan hindari aktivitas di luar ruangan yang berlebihan.")
        
        if weather['temperature'] < 10:
            alerts.append(f"Suhu sangat rendah ({weather['temperature']}°C) di lokasi Anda. Gunakan pakaian hangat saat bepergian.")
        
        # High humidity
        if weather['humidity'] > 90:
            alerts.append(f"Kelembaban tinggi ({weather['humidity']}%) di lokasi Anda.")
        
        # Send alerts if any
        for alert_msg in alerts:
            # Create an alert in the database
            create_alert(loc['user_id'], "weather", alert_msg)
            
            # Send message to user
            try:
                await context.bot.send_message(
                    chat_id=loc['user_id'],
                    text=f"⚠️ *Peringatan Cuaca*\n\n{alert_msg}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error sending weather alert to {loc['user_id']}: {e}")

async def send_daily_summary(context):
    """Send a daily summary to the admin"""
    # Get all users
    locations = get_all_user_locations()
    
    # Create a summary
    now = datetime.datetime.now()
    summary = f"📊 *Ringkasan Harian ({now.strftime('%d/%m/%Y')})*\n\n"
    summary += f"Total Pengguna: {len(locations)}\n"
    
    # Count active users in the last 24 hours
    active_count = 0
    for loc in locations:
        # Convert the ISO timestamp to datetime
        try:
            last_update = datetime.datetime.fromisoformat(loc['last_updated'])
            one_day_ago = now - datetime.timedelta(days=1)
            
            if last_update > one_day_ago:
                active_count += 1
        except (ValueError, TypeError):
            pass
    
    summary += f"Pengguna Aktif (24 jam terakhir): {active_count}\n\n"
    
    # Add a list of the 5 most recently active users
    summary += "Pengguna Terakhir Aktif:\n"
    
    # Sort by last_updated
    try:
        recent_users = sorted(locations, key=lambda x: x['last_updated'], reverse=True)[:5]
        
        for i, user in enumerate(recent_users):
            user_info = f"{user['full_name']} (@{user['username']})" if user['username'] else user['full_name']
            summary += f"{i+1}. {user_info} - {user['last_updated']}\n"
    except Exception as e:
        summary += f"Error sorting users: {e}\n"
    
    # Send summary to admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=summary,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending daily summary: {e}")

async def check_inactive_users(context):
    """Alert admin about users who haven't updated their location in a while"""
    # Get all users
    locations = get_all_user_locations()
    
    # Current time
    now = datetime.datetime.now()
    
    # Find users inactive for more than 3 days
    inactive_users = []
    for loc in locations:
        try:
            last_update = datetime.datetime.fromisoformat(loc['last_updated'])
            three_days_ago = now - datetime.timedelta(days=3)
            
            if last_update < three_days_ago:
                inactive_users.append({
                    'user_id': loc['user_id'],
                    'name': f"{loc['full_name']} (@{loc['username']})" if loc['username'] else loc['full_name'],
                    'last_updated': loc['last_updated']
                })
        except (ValueError, TypeError):
            pass
    
    if not inactive_users:
        return
    
    # Create report
    report = "⚠️ *Pengguna Tidak Aktif*\n\n"
    report += f"Ada {len(inactive_users)} pengguna yang tidak memperbarui lokasi mereka selama lebih dari 3 hari:\n\n"
    
    for i, user in enumerate(inactive_users):
        report += f"{i+1}. {user['name']}\n"
        report += f"   ID: {user['user_id']}\n"
        report += f"   Terakhir Aktif: {user['last_updated']}\n\n"
    
    # Send report to admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=report,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending inactive users report: {e}") 