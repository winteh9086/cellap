from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import sqlite3
import os

DB_FILE = 'phones.db'
AUTHORIZED_USER_ID = 612217861   # 🔁 Replace with your Telegram user ID

def get_price(model: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Match any model that includes the search text (e.g., iPhone 12 -> matches iPhone 12 Mini, iPhone 12 Pro)
    c.execute("SELECT model, price, storage FROM phones WHERE lower(model) LIKE ?", (f"%{model.lower()}%",))
    results = c.fetchall()
    conn.close()
    return results


def add_phone(model: str, price: str, storage: str) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO phones (model, price, storage) VALUES (?, ?, ?)", (model, price, storage))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding phone: {e}")
        return False


def delete_phone(model: str) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM phones WHERE lower(model) = ?", (model.lower(),))
        conn.commit()
        conn.close()

        return c.rowcount > 0
    except Exception as e:
        print(f"Error deleting phone: {e}")
        return False

def clear_all_phones() -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM phones")  # Deletes all rows
        conn.commit()
        conn.close()
        return c.rowcount >= 0  # Success if rows were affected
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False

def update_price(model: str, price: str) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE phones SET price = ? WHERE lower(model) = ?", (price, model.lower()))
        conn.commit()
        updated = c.rowcount
        conn.close()
        return updated > 0
    except:
        return False

def list_phones() -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT model, price FROM phones")
    rows = c.fetchall()
    conn.close()
    return rows

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📱Send Your SAMSUNG / HUAWEI / IPHONE / REDMI phone Model to get the PRICE.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = update.message.text.strip()
    results = get_price(model)
    
    if results:
        reply = "\n".join([f"{m.title()} ({s}) - {p}" for m, p, s in results])
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text(
            "❌ Sorry, I couldn't find that model.\n\n"
            "Feel free to contact us directly for more information.\n"
            "📞 On Telegram: [Contact me on Telegram](024-585-9086)\n"
            "📲 Or on WhatsApp: [Contact me on WhatsApp](024-585-9086)",
            disable_web_page_preview=True
        )

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 You're not authorized to add phones.")
        return

    try:
        _, data = update.message.text.split(" ", 1)
        entries = data.split(";")
        added = []

        for entry in entries:
            parts = [x.strip() for x in entry.split(",", 2)]
            if len(parts) == 3:
                model, price, storage = parts
                if add_phone(model, price, storage):
                    added.append(f"✅ Added {model} ({storage}) - {price}")
                else:
                    added.append(f"❌ Failed to add {model}")
            else:
                added.append("⚠️ Incorrect format. Use: model, price, storage")

        await update.message.reply_text("\n".join(added))

    except Exception as e:
        await update.message.reply_text("❗ Usage: /add model, price, storage\nExample: /add iPhone 15, $899, 128GB; Galaxy S22, $799, 256GB")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 You're not authorized to delete phones.")
        return

    try:
        # Get the phone model to be deleted
        _, model = update.message.text.split(" ", 1)
        model = model.strip()

        if delete_phone(model):
            await update.message.reply_text(f"✅ {model.title()} has been deleted from the database.")
        else:
            await update.message.reply_text(f"❌ Could not find {model.title()} to delete.")
    
    except Exception as e:
        await update.message.reply_text("❗ Usage: /delete model\nExample: /delete iPhone 15")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 You're not authorized to clear the database.")
        return

    try:
        if clear_all_phones():
            await update.message.reply_text("✅ All phone models and prices have been cleared from the database.")
        else:
            await update.message.reply_text("❌ Failed to clear the database.")
    
    except Exception as e:
        await update.message.reply_text("❗ An error occurred while clearing the database.")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("You're not authorized to update phones.")
        return

    try:
        _, data = update.message.text.split(" ", 1)
        model, price = [x.strip() for x in data.split(",", 1)]
        if update_price(model, price):
            await update.message.reply_text(f"🔄 Updated {model} to new price {price}")
        else:
            await update.message.reply_text(f"❌ Couldn't find model '{model}' to update.")
    except:
        await update.message.reply_text("❗ Usage: /update model, price")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phones = list_phones()
    if phones:
        msg = "\n".join([f"{model.title()}: {price}" for model, price in phones])
        await update.message.reply_text(f"📋 Available Phones:\n{msg}")
    else:
        await update.message.reply_text("No phones available.")

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_command))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(CommandHandler("clear", clear_command))
app.add_handler(CommandHandler("update", update_command))  # Add this
app.add_handler(CommandHandler("list", list_command))      # Add this
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()

