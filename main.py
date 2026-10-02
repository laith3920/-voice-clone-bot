import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fish_audio_sdk import Session, TTSRequest, ReferenceAudio

# إعدادات الـ Logging
logging.basicConfig(level=logging.INFO)

# المفاتيح
FISH_API_KEY = "sk-fish-aiF21NzDoKADMGHxkSCxuNwH-zKRedsmFKliOKoJWmQ"
TELEGRAM_BOT_TOKEN = "8834779790:AAGBHu5G_c8-feafKI0aMacYM4d1XqKE7LY"

# خزن الأصوات المرجعية
user_voices = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! 🎙️\n\n"
        "1. ارسل لي بصمة صوتية قصيرة (5 إلى 10 ثوانٍ) لاستنساخ صوتك.\n"
        "2. بعد ذلك، ارسل أي نص وسأقوم بنطقه بنفس صوتك!"
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    voice = update.message.voice or update.message.audio

    if not voice:
        await update.message.reply_text("يرجى إرسال ملف صوتي صحيح.")
        return

    file = await context.bot.get_file(voice.file_id)
    file_path = f"voice_{user_id}.ogg"
    await file.download_to_drive(file_path)

    user_voices[user_id] = file_path
    await update.message.reply_text("تم حفظ نبرة صوتك بنجاح! 🎯 الآن اكتب لي أي نص لأحوله لصوتك.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text_to_speak = update.message.text

    if user_id not in user_voices:
        await update.message.reply_text("يرجى إرسال بصمة صوتية أولاً حتى أتمكن من استنساخ صوتك!")
        return

    ref_audio_path = user_voices[user_id]
    output_audio_path = f"output_{user_id}.mp3"

    msg = await update.message.reply_text("جاري توليد الصوت... ⏳")

    try:
        session = Session(FISH_API_KEY)

        with open(ref_audio_path, "rb") as f:
            audio_bytes = f.read()

        ref = ReferenceAudio(audio=audio_bytes)
        request = TTSRequest(text=text_to_speak, references=[ref])

        with open(output_audio_path, "wb") as f:
            for chunk in session.tts(request):
                f.write(chunk)

        with open(output_audio_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

        await msg.delete()

    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        await msg.edit_text("حدث خطأ أثناء توليد الصوت. يرجى المحاولة لاحقاً.")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
