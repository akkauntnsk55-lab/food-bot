import telebot
from telebot import types

TOKEN = "8568834586:AAH4XUyblCA12kE-CSpvxeESHPz3gEmY8hw"
bot = telebot.TeleBot(TOKEN)

# --- СОСТОЯНИЕ ---
user_states = {}


# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🍔 Добавить продукт")
    btn2 = types.KeyboardButton("📋 Список продуктов")
    btn3 = types.KeyboardButton("ℹ️ Помощь")

    markup.add(btn1, btn2, btn3)

    bot.send_message(message.chat.id, "Выбери действие 👇", reply_markup=markup)


# --- ДОБАВЛЕНИЕ ПРОДУКТА ---
@bot.message_handler(func=lambda m: m.text == "🍔 Добавить продукт")
def add_product(message):
    user_states[message.chat.id] = {}
    bot.send_message(message.chat.id, "Напиши название продукта:")


# --- ЛОВИМ НАЗВАНИЕ ---
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "name" not in user_states[m.chat.id])
def get_name(message):
    user_states[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Теперь напиши срок годности (например: 10.06):")


# --- ЛОВИМ ДАТУ ---
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "date" not in user_states[m.chat.id])
def get_date(message):
    user_states[message.chat.id]["date"] = message.text

    name = user_states[message.chat.id]["name"]
    date = user_states[message.chat.id]["date"]

    bot.send_message(message.chat.id, f"✅ Добавлено: {name} до {date}")

    # очищаем состояние
    user_states[message.chat.id] = {}


# --- ПОМОЩЬ ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help_message(message):
    bot.send_message(message.chat.id, "Я помогу тебе отслеживать срок годности продуктов 🥦")


# --- СПИСОК (пока заглушка) ---
@bot.message_handler(func=lambda m: m.text == "📋 Список продуктов")
def list_products(message):
    bot.send_message(message.chat.id, "📋 Список пока пуст")


# --- ЗАПУСК ---
bot.polling()
