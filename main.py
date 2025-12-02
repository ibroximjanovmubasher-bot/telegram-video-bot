import os
import subprocess
from aiogram import Bot, Dispatcher, executor, types

# ==================== 🛠️ KONFIGURATSIYA (O'zgartiring!) 🛠️ ====================
# SIZNING TOKENINGIZNI SHU YERGA YOZING!
BOT_TOKEN = "7926518043:AAEy6p8g8ro39POp9V7xw7JRDDYNDXPVvN8" 

# Fayllarni saqlash uchun vaqtincha papka
TEMP_DIR = "downloads"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
# ==============================================================================

# Bot va Dispatcher obyektlarini yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# /start buyrug'i uchun funksiya
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Assalomu alaykum! Video yuklab beruvchi botga xush kelibsiz.\n\nYouTube, Instagram yoki boshqa ijtimoiy tarmoq linkini yuboring.")


# Linklarni (matn xabarlarini) qayta ishlovchi asosiy funksiya
@dp.message_handler(content_types=types.ContentType.TEXT)
async def process_link(message: types.Message):
    link = message.text.strip()
    chat_id = message.chat.id
    
    # Har bir foydalanuvchi uchun vaqtinchalik noyob fayl nomini yaratish
    # Bu fayl nomini yo'qotmaslik uchun 'mp4' qo'shimchasi bilan birga.
    temp_file_name = f"{chat_id}_{os.urandom(8).hex()}.mp4"
    temp_file_path = os.path.join(TEMP_DIR, temp_file_name)
    
    # 1. Boshlanganlik haqida xabar berish
    status_msg = await bot.send_message(chat_id, "🔗 Link qabul qilindi. Yuklab olish boshlanmoqda...")
    
    try:
        # 2. yt-dlp buyrug'ini tuzish va bajarish
        
        # Bu buyruq videoni yuqori sifatda MP4 formatida yuklab olishga harakat qiladi.
        command = [
            "yt-dlp",
            "-o", temp_file_path,  # Chiqish fayli manzili
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4", # Audio va videoni birlashtirish (ffmpeg yordamida)
            "--no-warnings",
            "--max-filesize", "50M", # 50 Megabaytdan katta videolarni yuklamaslik (Telegram talabi)
            link
        ]
        
        # Buyruqni tizimda bajarish
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,  # Agar xato bo'lsa, CalledProcessError tashlaydi
            timeout=300  # Maksimal 5 daqiqa kutish
        )
        
        # 3. Yuklab olish tugagani haqida xabarni tahrirlash
        await bot.edit_message_text(f"✅ Yuklab olish tugadi! Fayl yuborilmoqda...", chat_id, status_msg.message_id)
        
        
        # 4. Faylni Telegramga yuborish
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'rb') as video_file:
                await bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption="Tayyor! Marhamat, yuklab oling."
                )
        else:
             await bot.send_message(chat_id, "❌ Yuklab olish yakunlandi, ammo fayl topilmadi.")

    except subprocess.CalledProcessError as e:
        # yt-dlp yoki ffmpeg ishida xato bo'lsa
        error_message = "❌ Xatolik yuz berdi. Sabab:\n- Link noto'g'ri\n- Video hajmi juda katta (>50MB)\n- Platforma qo'llab-quvvatlanmaydi."
        await bot.edit_message_text(error_message, chat_id, status_msg.message_id)
        print(f"Subprocess Xatosi: {e.stderr}")
    
    except Exception as e:
        # Boshqa kutilmagan xatolar
        await bot.edit_message_text(f"❌ Kutilmagan xato: {e}", chat_id, status_msg.message_id)
        print(f"Umumiy Xato: {e}")
        
    finally:
        # 5. Tozalash (Serverda joyni bo'shatish)
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"Fayl o'chirildi: {temp_file_path}")
        except Exception as e:
            print(f"Tozalashda xato: {e}")


# Botni ishga tushirish
if __name__ == '__main__':
    print("Bot ishga tushmoqda...")
    executor.start_polling(dp, skip_updates=True)