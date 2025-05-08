# Panduan Pengaturan dan Pemecahan Masalah

## Cara Menjalankan Bot

1. Pastikan semua dependensi telah diinstal:
   ```
   python install.py
   ```

2. Edit file `config/config.py` dan atur:
   - TOKEN: token bot Telegram Anda
   - ADMIN_ID: ID Telegram Anda

3. Jalankan bot menggunakan salah satu cara berikut:
   - `python run.py`
   - Klik dua kali pada file `run_bot.bat` (di Windows)

## Mengatasi Error Import

Jika terdapat error terkait import seperti "Import telegram could not be resolved":

1. Pastikan semua dependensi sudah terpasang:
   ```
   pip install -r requirements.txt
   ```

2. Untuk pengguna VS Code, kami telah menyediakan file `.vscode/settings.json` yang akan mematikan peringatan import.

3. Anda juga dapat menjalankan verifikasi import:
   ```
   python verify_imports.py
   ```

## Struktur Proyek

```
lacak-lokasi/
├── bot/
│   ├── __init__.py
│   └── main.py
├── config/
│   ├── __init__.py
│   └── config.py
├── data/
│   └── __init__.py
├── handlers/
│   ├── __init__.py
│   ├── admin_handlers.py
│   ├── alert_handlers.py
│   ├── callback_handlers.py
│   ├── location_handlers.py
│   ├── poi_handlers.py
│   └── settings_handlers.py
├── utils/
│   ├── __init__.py
│   ├── database.py
│   ├── geo_utils.py
│   └── notifications.py
├── __init__.py
├── run.py
├── install.py
├── verify_imports.py
├── run_bot.bat
├── README.md
└── requirements.txt
```

## Variabel Lingkungan (Opsional)

Untuk keamanan yang lebih baik, Anda dapat menggunakan variabel lingkungan untuk menyimpan token dan API key:

1. Buat file `.env` di direktori utama proyek:
   ```
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_telegram_id_here
   
   # Weather API Configuration
   WEATHER_API_KEY=your_weather_api_key_here
   
   # Geocoding API Configuration
   GEOCODING_API_KEY=your_geocoding_api_key_here
   ```

2. Bot akan otomatis membaca variabel tersebut melalui `python-dotenv`.

## Troubleshooting

### Bot Tidak Merespon
- Pastikan token bot yang Anda masukkan benar
- Cek koneksi internet
- Jalankan bot dengan menambahkan flag debug: `python run.py --debug`

### Database Error
- Pastikan direktori `data` sudah ada
- Cek izin tulis ke direktori data
- Hapus file database dan biarkan bot membuat ulang

### Error Saat Menjalankan
- Jika terdapat error, coba jalankan `python verify_imports.py` untuk memastikan semua modul dapat diimpor dengan benar
- Update semua paket: `pip install --upgrade -r requirements.txt`

## Informasi Kontak

Jika Anda mengalami masalah yang tidak dapat diatasi, silakan hubungi pengembang. 