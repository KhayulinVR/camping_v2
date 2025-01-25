import datetime
import telebot as tb
from telebot import types
import calendar
import token_bot

bot = tb.TeleBot(token_bot.token)


def create_callback_data(action, year, month, day):
    # print(f"create_callback_data works")
    """ Create the callback data associated to each button"""
    return "CALENDAR" + ";" + ";".join([action, str(year), str(month), str(day)])


def separate_callback_data(data):
    # print(f"separate_callback_data works")
    """ Separate the callback data"""
    # print(data.split(";"))
    return data.split(";")


def create_calendar(year=None, month=None, day_select=None):
    # print(f"create_calendar works")
    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0)
    data_confirm = create_callback_data("CONFIRM", year, month, 32)
    keyboard = []
    # First row - Month and Year
    row = []
    row.append(types.InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=data_ignore))
    keyboard.append(row)
    # Second row - Week Days
    row = []
    for day in ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]:
        row.append(types.InlineKeyboardButton(day, callback_data=data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    print(my_calendar)
    # берем с сервера джанго год и месяц и числа
    # для year = ..., month = ...
    date_close = [3, 4, 5, 15, 16]

    for week in my_calendar:
        for day in range(len(week)):
            if week[day] in date_close:
                week[day] = "❌"
            elif week[day] == day_select:
                week[day] = "✅"

    for week in my_calendar:
        row = []
        for day in week:
            if (day == 0):
                row.append(types.InlineKeyboardButton(" ", callback_data=data_ignore))
            elif (day == "❌"):
                row.append(types.InlineKeyboardButton("❌", callback_data=data_ignore))
            else:
                row.append(
                    types.InlineKeyboardButton(str(day), callback_data=create_callback_data("DAY", year, month, day)))
        keyboard.append(row)


    # Last row - Buttons
    row = []
    row.append(types.InlineKeyboardButton("<", callback_data=create_callback_data("PREV-MONTH", year, month, day)))
    row.append(types.InlineKeyboardButton("Confirm", callback_data=data_confirm))
    row.append(types.InlineKeyboardButton(">", callback_data=create_callback_data("NEXT-MONTH", year, month, day)))
    keyboard.append(row)

    return types.InlineKeyboardMarkup(keyboard)


@bot.message_handler(commands=['start'])
def profile(message):
    bot.send_message(message.chat.id, 'Выберите дату', reply_markup=create_calendar())


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    (_, action, year, month, day) = separate_callback_data(call.data)
    print((_, action, year, month, day, call.from_user.id, call.from_user.first_name))
    # print(call)
    # print(call.message.message_id)
    # print(call.from_user.id)
    # print(type(call.from_user.id))

    curr = datetime.datetime(int(year), int(month), 1)

    """context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                 text=messages.calendar_response_message % (date.strftime("%d/%m/%Y")),
                                 reply_markup=ReplyKeyboardRemove())"""

    if action == "DAY":
        bot.edit_message_text(text="Выберите дату 2-ю",
                              chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              reply_markup=create_calendar(int(year), int(month), int(day)))

    if action == "PREV-MONTH":
        pre = curr - datetime.timedelta(days=1)
        bot.edit_message_text(text="Выберите дату",
                                  chat_id=call.from_user.id,
                                  message_id=call.message.message_id,
                                  reply_markup=create_calendar(int(pre.year), int(pre.month)))

    elif action == "NEXT-MONTH":
        ne = curr + datetime.timedelta(days=31)
        bot.edit_message_text(text="Выберите дату",
                                  chat_id=call.from_user.id,
                                  message_id=call.message.message_id,
                                  reply_markup=create_calendar(int(ne.year), int(ne.month)))

    elif action == "CONFIRM":
        ne = curr + datetime.timedelta(days=31)
        bot.edit_message_text(text="Выберите дату",
                              chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              reply_markup=create_calendar(int(ne.year), int(ne.month)))



bot.polling(none_stop=True)


# работает)