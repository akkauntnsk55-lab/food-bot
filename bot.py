import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from datetime import datetime, timedelta

TOKEN = "8568834586:AAH4XUyblCA12kE-CSpvxeESHPz3gEmY8hw"
bot = telebot.TeleBot(TOKEN)

# --- БАЗА ---
conn = sqlite3.connect("products.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    expiry_date TEXT,
    notified_15 INTEGER DEFAULT 0,
    notified_7 INTEGER DEFAULT 0,
    notified_3 INTEGER DEFAULT 0
)
""")
conn.commit()

# --- МЕНЮ ---
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить продукт")
    markup.add("📋 Список", "🗑 Удалить")
    return markup

# --- СТАРТ ---
from telebot import types

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("🍔 Добавить продукт")
    btn2 = types.KeyboardButton("📋 Список продуктов")
    btn3 = types.KeyboardButton("ℹ️ Помощь")

    markup.add(btn1, btn2, btn3)

    bot.send_message(message.chat.id, "Выбери действие 👇", reply_markup=markup)
    
# --- СОСТОЯНИЕ ---
user_states = {}

# --- ДОБАВЛЕНИЕ ---
@bot.message_handler(func=lambda m: m.text == "🍔 Добавить продукт")
def add_product(message):
    user_states[message.chat.id] = {}
    bot.send_message(message.chat.id, "Напиши название продукта:")


# 👉 ЛОВИМ НАЗВАНИЕ
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "name" not in user_states[m.chat.id])
def get_name(message):
    user_states[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Теперь напиши срок годности:")


# 👉 ЛОВИМ СРОК
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "date" not in user_states[m.chat.id])
def get_date(message):
    user_states[message.chat.id]["date"] = message.text

    bot.send_message(message.chat.id, "Продукт сохранён ✅")

    user_states[message.chat.id] = {}
    
    user_states[message.chat.id]["name"] = message.text

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Сегодня", callback_data="today"),
        InlineKeyboardButton("Завтра", callback_data="tomorrow")
    )
    markup.add(
        InlineKeyboardButton("+3 дня", callback_data="3days"),
        InlineKeyboardButton("+7 дней", callback_data="7days")
    )

    bot.send_message(message.chat.id, "Выбери срок годности:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["today", "tomorrow", "3days", "7days"])
def set_date(call):
    now = datetime.now()

    if call.data == "today":
        date = now
    elif call.data == "tomorrow":
        date = now + timedelta(days=1)
    elif call.data == "3days":
        date = now + timedelta(days=3)
    elif call.data == "7days":
        date = now + timedelta(days=7)

    date_str = date.strftime("%Y-%m-%d")
    name = user_states[call.message.chat.id]["name"]

    cursor.execute(
        "INSERT INTO products (user_id, name, expiry_date) VALUES (?, ?, ?)",
        (call.message.chat.id, name, date_str)
    )
    conn.commit()

    bot.send_message(call.message.chat.id, f"✅ Добавлено: {name} до {date_str}", reply_markup=main_menu())

    user_states.pop(call.message.chat.id)

# --- СПИСОК ---
@bot.message_handler(func=lambda m: m.text == "📋 Список")
def list_products(message):
    cursor.execute("SELECT id, name, expiry_date FROM products WHERE user_id=?", (message.chat.id,))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "Список пуст", reply_markup=main_menu())
        return

    text = "📋 Твои продукты:\n\n"
    for r in rows:
        text += f"{r[1]} — до {r[2]}\n"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# --- УДАЛЕНИЕ ---
@bot.message_handler(func=lambda m: m.text == "🗑 Удалить")
def delete_product(message):
    cursor.execute("SELECT id, name FROM products WHERE user_id=?", (message.chat.id,))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "Нечего удалять", reply_markup=main_menu())
        return

    markup = InlineKeyboardMarkup()

    for r in rows:
        markup.add(InlineKeyboardButton(r[1], callback_data=f"del_{r[0]}"))

    bot.send_message(message.chat.id, "Выбери продукт:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def confirm_delete(call):
    product_id = int(call.data.split("_")[1])

    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()

    bot.send_message(call.message.chat.id, "🗑 Удалено", reply_markup=main_menu())

print("Бот запущен...")
import threading
import time

def check_expiry():
    while True:
        now = datetime.now()

        cursor.execute("SELECT id, user_id, name, expiry_date, notified_15, notified_7, notified_3 FROM products")
        rows = cursor.fetchall()

        for row in rows:
            product_id, user_id, name, expiry_date, n15, n7, n3 = row
            exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
            days_left = (exp_date - now).days

            # 15 дней
            if 14 <= days_left <= 15 and not n15:
                bot.send_message(user_id, f"⚠️ {name} испортится через 15 дней")
                cursor.execute("UPDATE products SET notified_15=1 WHERE id=?", (product_id,))
                conn.commit()

            # 7 дней
            if 6 <= days_left <= 7 and not n7:
                bot.send_message(user_id, f"⚠️ {name} испортится через 7 дней")
                cursor.execute("UPDATE products SET notified_7=1 WHERE id=?", (product_id,))
                conn.commit()

            # 3 дня
            if 2 <= days_left <= 3 and not n3:
                bot.send_message(user_id, f"⚠️ {name} испортится через 3 дня")
                cursor.execute("UPDATE products SET notified_3=1 WHERE id=?", (product_id,))
                conn.commit()

        time.sleep(10)  # проверка раз в день

# запуск в фоне
threading.Thread(target=check_expiry).start()

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "🍔 Добавить продукт":
        bot.send_message(message.chat.id, "Напиши название продукта")

    elif message.text == "📋 Список продуктов":
        bot.send_message(message.chat.id, "Пока пусто 😄")

    elif message.text == "ℹ️ Помощь":
        bot.send_message(message.chat.id, "Это бот для продуктов 🍎")

bot.polling()
