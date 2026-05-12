import telebot
from telebot import types
import json
import os

TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"
bot = telebot.TeleBot(TOKEN)

# --- СОСТОЯНИЕ ---
user_states = {}

# --- ФАЙЛ ---
FILE_NAME = "products.json"

# если файла нет — создаём
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump({}, f)


# --- ЗАГРУЗКА ---
def load_products():
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)


# --- СОХРАНЕНИЕ ---
def save_products(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🍔 Добавить продукт"),
        types.KeyboardButton("📋 Список продуктов"),
        types.KeyboardButton("ℹ️ Помощь")
    )

    bot.send_message(message.chat.id, "Выбери действие 👇", reply_markup=markup)


# --- ДОБАВИТЬ ---
@bot.message_handler(func=lambda m: m.text == "🍔 Добавить продукт")
def add_product(message):
    user_states[message.chat.id] = {}
    bot.send_message(message.chat.id, "Напиши название продукта:")


# --- НАЗВАНИЕ ---
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "name" not in user_states[m.chat.id])
def get_name(message):
    user_states[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Теперь напиши срок годности (например: 10.06):")


# --- ДАТА ---
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "date" not in user_states[m.chat.id])
def get_date(message):
    user_states[message.chat.id]["date"] = message.text

    name = user_states[message.chat.id]["name"]
    date = user_states[message.chat.id]["date"]
    user_id = str(message.chat.id)

    # загружаем
    data = load_products()

    # если пользователя нет — создаём
    if user_id not in data:
        data[user_id] = []

    # добавляем продукт
    data[user_id].append({
        "name": name,
        "date": date
    })

    # сохраняем
    save_products(data)

    bot.send_message(message.chat.id, f"✅ Добавлено: {name} до {date}")

    user_states[message.chat.id] = {}


# --- СПИСОК ---
@bot.message_handler(func=lambda m: m.text == "📋 Список продуктов")
def list_products(message):
    data = load_products()
    user_id = str(message.chat.id)

    if user_id not in data or len(data[user_id]) == 0:
        bot.send_message(message.chat.id, "📋 Список пуст")
        return

    text = "📋 Твои продукты:\n\n"

    for item in data[user_id]:
        text += f"• {item['name']} — до {item['date']}\n"

    bot.send_message(message.chat.id, text)


# --- ПОМОЩЬ ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help_message(message):
    bot.send_message(message.chat.id, "Я сохраняю продукты и сроки годности 📦")


# --- ЗАПУСК ---
bot.polling()
