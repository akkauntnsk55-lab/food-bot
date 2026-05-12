import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
import calendar

TOKEN = "8568834586:AAH4XUyblCA12kE-CSpvxeESHPz3gEmY8hw"
bot = telebot.TeleBot(TOKEN)

FILE_NAME = "products.json"
user_states = {}
calendar_state = {}

# --- файл ---
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump({}, f)


def load_products():
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)


def save_products(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "🍔 Добавить продукт",
        "📋 Список продуктов",
        "🗑 Удалить продукт"
    )
    bot.send_message(message.chat.id, "Выбери действие 👇", reply_markup=markup)


# --- ДОБАВИТЬ ---
@bot.message_handler(func=lambda m: m.text == "🍔 Добавить продукт")
def add_product(message):
    user_states[message.chat.id] = {}
    now = datetime.now()
    calendar_state[message.chat.id] = {"year": now.year, "month": now.month}
    bot.send_message(message.chat.id, "Напиши название продукта:")


# --- НАЗВАНИЕ ---
@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict) and "name" not in user_states[m.chat.id])
def get_name(message):
    user_states[message.chat.id]["name"] = message.text
    show_calendar(message.chat.id)


# --- КАЛЕНДАРЬ ---
def show_calendar(chat_id):
    year = calendar_state[chat_id]["year"]
    month = calendar_state[chat_id]["month"]

    markup = types.InlineKeyboardMarkup()

    # заголовок
    markup.row(
        types.InlineKeyboardButton("⬅️", callback_data="prev"),
        types.InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        types.InlineKeyboardButton("➡️", callback_data="next")
    )

    # дни недели
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]])

    cal = calendar.monthcalendar(year, month)
    today = datetime.now()

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                text = str(day)

                # подсветка сегодня
                if day == today.day and month == today.month and year == today.year:
                    text = f"🟢{day}"

                row.append(types.InlineKeyboardButton(text, callback_data=f"day_{day}"))

        markup.row(*row)

    bot.send_message(chat_id, "📅 Выбери дату:", reply_markup=markup)


# --- ОБРАБОТКА КАЛЕНДАРЯ ---
@bot.callback_query_handler(func=lambda call: True)
def calendar_handler(call):
    chat_id = call.message.chat.id

    if call.data == "ignore":
        return

    if call.data == "prev":
        calendar_state[chat_id]["month"] -= 1
        if calendar_state[chat_id]["month"] == 0:
            calendar_state[chat_id]["month"] = 12
            calendar_state[chat_id]["year"] -= 1

        bot.delete_message(chat_id, call.message.message_id)
        show_calendar(chat_id)

    elif call.data == "next":
        calendar_state[chat_id]["month"] += 1
        if calendar_state[chat_id]["month"] == 13:
            calendar_state[chat_id]["month"] = 1
            calendar_state[chat_id]["year"] += 1

        bot.delete_message(chat_id, call.message.message_id)
        show_calendar(chat_id)

    elif call.data.startswith("day_"):
        day = int(call.data.split("_")[1])
        month = calendar_state[chat_id]["month"]
        year = calendar_state[chat_id]["year"]

        date = f"{day:02d}.{month:02d}.{year}"

        name = user_states[chat_id]["name"]
        user_id = str(chat_id)

        data = load_products()
        if user_id not in data:
            data[user_id] = []

        data[user_id].append({
            "name": name,
            "date": date
        })

        save_products(data)

        bot.send_message(chat_id, f"✅ Добавлено: {name} до {date}")

        user_states[chat_id] = {}


# --- СПИСОК ---
@bot.message_handler(func=lambda m: m.text == "📋 Список продуктов")
def list_products(message):
    data = load_products()
    user_id = str(message.chat.id)

    if user_id not in data or not data[user_id]:
        bot.send_message(message.chat.id, "📋 Список пуст")
        return

    today = datetime.now()

    def parse_date(item):
        return datetime.strptime(item["date"], "%d.%m.%Y")

    products = sorted(data[user_id], key=parse_date)

    text = "📋 Твои продукты:\n\n"

    for i, item in enumerate(products, 1):
        exp = parse_date(item)

        if exp < today:
            status = " 🔴 ПРОСРОЧЕНО"
        elif exp - today <= timedelta(days=1):
            status = " 🟡 скоро"
        else:
            status = ""

        text += f"{i}. {item['name']} — {item['date']}{status}\n"

    bot.send_message(message.chat.id, text)


# --- УДАЛЕНИЕ ---
@bot.message_handler(func=lambda m: m.text == "🗑 Удалить продукт")
def delete_start(message):
    data = load_products()
    user_id = str(message.chat.id)

    if user_id not in data or not data[user_id]:
        bot.send_message(message.chat.id, "❌ Список пуст")
        return

    text = "Напиши номер:\n\n"
    for i, item in enumerate(data[user_id], 1):
        text += f"{i}. {item['name']} — {item['date']}\n"

    user_states[message.chat.id] = {"delete": True}
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("delete"))
def delete_product(message):
    user_id = str(message.chat.id)
    data = load_products()

    try:
        index = int(message.text) - 1
        removed = data[user_id].pop(index)
        save_products(data)

        bot.send_message(message.chat.id, f"🗑 Удалено: {removed['name']}")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка")

    user_states[message.chat.id] = {}


# --- ЗАПУСК ---
bot.polling()
