import telebot
from telebot import types
import json
import os
from datetime import datetime, date
import calendar

TOKEN = "8568834586:AAH4XUyblCA12kE-CSpvxeESHPz3gEmY8hw"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "products.json"
user_states = {}

# =======================
# 📦 Работа с файлом
# =======================

def load_products():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =======================
# 📅 КАЛЕНДАРЬ
# =======================

def create_calendar(year, month, chat_id):
    markup = types.InlineKeyboardMarkup()

    # Навигация
    markup.row(
        types.InlineKeyboardButton("⬅️", callback_data=f"prev_{year}_{month}"),
        types.InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        types.InlineKeyboardButton("➡️", callback_data=f"next_{year}_{month}")
    )

    markup.row(
        types.InlineKeyboardButton("<<", callback_data=f"year_{year-1}_{month}"),
        types.InlineKeyboardButton(">>", callback_data=f"year_{year+1}_{month}")
    )

    # Дни недели
    days = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in days])

    cal = calendar.monthcalendar(year, month)
    today = date.today()

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                current = date(year, month, day)
                text = str(day)

                if current == today:
                    text = f"🟢{day}"
                elif current < today:
                    text = f"🔴{day}"
                elif "selected_date" in user_states.get(chat_id, {}) and \
                     user_states[chat_id]["selected_date"] == current:
                    text = f"🟡{day}"

                row.append(types.InlineKeyboardButton(
                    text,
                    callback_data=f"day_{year}_{month}_{day}"
                ))
        markup.row(*row)

    return markup

# =======================
# 🟢 СТАРТ
# =======================

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить продукт", "📋 Список продуктов")
    bot.send_message(message.chat.id, "Выбери действие 👇", reply_markup=markup)

# =======================
# ➕ ДОБАВИТЬ
# =======================

@bot.message_handler(func=lambda m: m.text == "➕ Добавить продукт")
def add_product(message):
    user_states[message.chat.id] = {}
    bot.send_message(message.chat.id, "Напиши название продукта:")

@bot.message_handler(func=lambda m: m.chat.id in user_states and "name" not in user_states[m.chat.id])
def get_name(message):
    user_states[message.chat.id]["name"] = message.text

    now = datetime.now()
    markup = create_calendar(now.year, now.month, message.chat.id)

    bot.send_message(message.chat.id, "Выбери дату:", reply_markup=markup)

# =======================
# 📅 CALLBACK
# =======================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data = call.data

    if data == "ignore":
        return

    chat_id = call.message.chat.id

    if data.startswith("prev_"):
        _, y, m = data.split("_")
        y, m = int(y), int(m) - 1
        if m == 0:
            m = 12
            y -= 1
        bot.edit_message_reply_markup(chat_id, call.message.message_id,
            reply_markup=create_calendar(y, m, chat_id))

    elif data.startswith("next_"):
        _, y, m = data.split("_")
        y, m = int(y), int(m) + 1
        if m == 13:
            m = 1
            y += 1
        bot.edit_message_reply_markup(chat_id, call.message.message_id,
            reply_markup=create_calendar(y, m, chat_id))

    elif data.startswith("year_"):
        _, y, m = data.split("_")
        bot.edit_message_reply_markup(chat_id, call.message.message_id,
            reply_markup=create_calendar(int(y), int(m), chat_id))

    elif data.startswith("day_"):
        _, y, m, d = data.split("_")

        selected = date(int(y), int(m), int(d))
        user_states[chat_id]["selected_date"] = selected

        products = load_products()

        if str(chat_id) not in products:
            products[str(chat_id)] = []

        name = user_states[chat_id]["name"]

        products[str(chat_id)].append({
            "name": name,
            "date": str(selected)
        })

        save_products(products)

        today = date.today()
        status = "❌ Просрочен" if selected < today else "✅ Ок"

        bot.send_message(chat_id, f"✅ Добавлено: {name}\n📅 {selected}\n{status}")

        user_states.pop(chat_id, None)

# =======================
# 📋 СПИСОК
# =======================

@bot.message_handler(func=lambda m: m.text == "📋 Список продуктов")
def show_products(message):
    products = load_products()
    chat_id = str(message.chat.id)

    if chat_id not in products or not products[chat_id]:
        bot.send_message(message.chat.id, "Список пуст 😢")
        return

    text = "📋 Твои продукты:\n\n"
    today = date.today()

    for p in products[chat_id]:
        exp = datetime.strptime(p["date"], "%Y-%m-%d").date()

        if exp < today:
            status = "🔴 Просрочен"
        else:
            status = "🟢 Свежий"

        text += f"{p['name']} — {p['date']} {status}\n"

    bot.send_message(message.chat.id, text)

# =======================

bot.infinity_polling()
