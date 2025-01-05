import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Config dosyasını yükleme
def load_config(file_path="config.csv"):
    config = {}
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = row["KEY"]
            value = row["VALUE"]
            if key == "CREATOR_IDS":
                config[key] = [int(x.strip()) for x in value.strip("[]").split(",")]
            else:
                config[key] = value
    return config

config = load_config()

# Banlı kullanıcılar listesi
def load_banned_users(file_path="bans.csv"):
    banned_users = []
    try:
        with open(file_path, mode="r") as file:
            reader = csv.reader(file)
            banned_users = [int(row[0]) for row in reader]
    except FileNotFoundError:
        pass
    return banned_users

banned_users = load_banned_users()

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in banned_users:
        return  # Eğer kullanıcı banlıysa, yanıt verme

    keyboard = [
        [InlineKeyboardButton("💳 Bakiye Satın Al", callback_data="buy_balance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Merhaba! Bakiye satın almak için aşağıdaki butona tıklayınız.",
        reply_markup=reply_markup
    )

# Bakiye seçeneklerini güncelleme
async def show_balance_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id in banned_users:
        return  # Eğer kullanıcı banlıysa, mesaj atma.

    await query.answer()

    # Yeni içerik ve reply_markup
    new_text = "Lütfen almak istediğiniz Bakiye miktarını seçin:"
    keyboard = [
        [InlineKeyboardButton("10K BAKİYE 500₺", callback_data="10k_500")],
        [InlineKeyboardButton("30K BAKİYE 800₺", callback_data="30k_800")],
        [InlineKeyboardButton("50K BAKİYE 1000₺", callback_data="50k_1000")],
        [InlineKeyboardButton("100K BAKİYE 1500₺", callback_data="100k_1500")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Eski içerik ile yeni içeriği karşılaştır
    if query.message.text != new_text or query.message.reply_markup != reply_markup:
        await query.edit_message_text(
            text=new_text,
            reply_markup=reply_markup
        )

# Ödeme seçeneklerini güncelleme
async def show_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id in banned_users:
        return  # Eğer kullanıcı banlıysa, mesaj atma.

    await query.answer()

    selection_map = {
        "10k_500": ("500₺", "10K Bakiye"),
        "30k_800": ("800₺", "30K Bakiye"),
        "50k_1000": ("1000₺", "50K Bakiye"),
        "100k_1500": ("1500₺", "100K Bakiye")
    }
    selected_price, selected_balance = selection_map.get(query.data, ("Bilinmeyen Fiyat", "Bilinmeyen Bakiye"))

    keyboard = [
        [InlineKeyboardButton("IBAN ile Ödeme", callback_data="iban_payment")],
        [InlineKeyboardButton("Kripto ile Ödeme", callback_data="crypto_payment")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"{selected_price}'ye {selected_balance} almak istiyorsunuz. Lütfen ödeme yöntemini seçin:",
        reply_markup=reply_markup
    )

# IBAN ile ödeme
async def iban_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id in banned_users:
        return  # Eğer kullanıcı banlıysa, mesaj atma.

    await query.answer()

    iban = config.get("IBAN", "Bilinmiyor")
    name = config.get("NAME", "Bilinmiyor")

    await query.edit_message_text(
        f"📝 IBAN ile ödeme yapmak üzeresiniz:\n\n"
        f"💳 IBAN: {iban}\n"
        f"👤 Ad-Soyad: {name}\n\n"
        f"✅ Ödeme Talimatı: Ödeme yaptıktan sonra dekontu bota PDF olarak gönderin. "
        f"⏳ Ödemeniz en fazla 2 saat içinde onaylanacak veya reddedilecektir.\n\n"
        f"⚠️ Sorun mu yaşıyorsunuz? Sorun yaşadığınız ekranın ekran görüntüsünü alıp bize gönderin."
    )

# Kripto ile ödeme
async def crypto_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id in banned_users:
        return  # Eğer kullanıcı banlıysa, mesaj atma.

    await query.answer()

    await query.edit_message_text("Kripto İle Ödeme İşlemi Şu Anda Aktif Değildir ⚠")

# PDF yükleme
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document.mime_type == "application/pdf":
        user_id = update.message.from_user.id
        admin_channel_id = config.get("ADMIN_CHANNEL_ID")
        file_id = update.message.document.file_id

        # Admin kanalına mesaj gönder
        keyboard = [
            [InlineKeyboardButton("Onayla", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton("Reddet", callback_data=f"reject_{user_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        caption = f"Kullanıcı {user_id}'in Dekontu"
        await context.bot.send_document(chat_id=admin_channel_id, document=file_id, caption=caption, reply_markup=reply_markup)

        await update.message.reply_text("Dekontunuz başarıyla gönderildi. İncelendikten sonra bilgilendirileceksiniz.")
    else:
        await update.message.reply_text("Lütfen PDF formatında bir dosya gönderin.")

# Görüntü dosyası yüklendiğinde
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in banned_users:
        return  # Eğer kullanıcı banlıysa, mesaj atma.

    await update.message.reply_text("Lütfen PDF Gönderin.")

# Admin aksiyonu: Onayla veya Reddet
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.data.split("_")[1])

    if query.data.startswith("approve"):
        # Kullanıcıyı banla
        banned_users.append(user_id)
        with open("bans.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([user_id])
        await query.edit_message_caption("Dekont onaylandı ve kullanıcı banlandı.")
    elif query.data.startswith("reject"):
        # Kullanıcıya reddedildi mesajı gönder
        await context.bot.send_message(chat_id=user_id, text="Dekontunuz reddedildi. Lütfen işlemi tekrar gözden geçirin.")
        await query.edit_message_caption("Dekont reddedildi.")

# Botu başlatma
if __name__ == "__main__":
    application = ApplicationBuilder().token(config["TOKEN"]).build()

    # Komutları ekleme
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_balance_options, pattern="^buy_balance$"))
    application.add_handler(CallbackQueryHandler(show_payment_options, pattern="^(10k_500|30k_800|50k_1000|100k_1500)$"))
    application.add_handler(CallbackQueryHandler(iban_payment, pattern="^iban_payment$"))
    application.add_handler(CallbackQueryHandler(crypto_payment, pattern="^crypto_payment$"))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject)_\\d+$"))

    print("Bot çalışıyor...")
    application.run_polling()
