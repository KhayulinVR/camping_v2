from telebot import types

from .models import User, Booking
import telebot
import datetime
import calendar

bot = telebot.TeleBot("YOUR_TOKEN_HERE")


# Функция, которая создает список кнопок для каждой недели в месяце
def create_calendar(year, month):
    # Создаем объект календаря на заданный месяц и год
    cal = calendar.monthcalendar(year, month)
    # Создаем список кнопок для каждой недели в календаре
    markup = types.InlineKeyboardMarkup()
    for week in cal:
        row = []
        for day in week:
            # Получаем дату в формате гггг-мм-дд
            date = datetime.date(year, month, day) if day != 0 else None
            date_str = date.isoformat() if date is not None else ""
            # Получаем список бронирований на эту дату
            bookings = Booking.objects.filter(date=date) if date is not None else []
            if date is not None and len(bookings) > 0:
                # Если на эту дату есть бронирования, создаем кнопку с текстом "X дата (кол-во бронирований)"
                button_text = f"❌ {day} ({len(bookings)})"
            elif date is not None:
                # Если на эту дату нет бронирований, создаем кнопку с текстом "дата"
                button_text = str(day)
            else:
                # Если дата не задана, создаем пустую кнопку
                button_text = " "
            # Создаем кнопку и добавляем ее в ряд
            button = types.InlineKeyboardButton(text=button_text, callback_data=f"calendar_day_{date_str}")
            row.append(button)
            # Добавляем ряд кнопок в клавиатуру
        markup.row(*row)
        # Добавляем кнопки навигации по месяцам
        markup.row(
            types.InlineKeyboardButton(text="<<", callback_data="calendar_prev_month"),
            types.InlineKeyboardButton(text=">>", callback_data="calendar_next_month")
        )
        return markup


# Функция, которая обрабатывает выбор дня в календаре
@bot.callback_query_handler(func=lambda call: call.data in ["None", "CANCEL"])
def handle_callback(call):
    if call.data == "None":
        # Если выбрана пустая кнопка, ничего не делаем
        pass
    elif call.data == "CANCEL":
        # Если выбрана кнопка "Отмена", сообщаем об отмене бронирования
        bot.send_message(call.message.chat.id, "Бронирование отменено")
    else:
        # Иначе помечаем выбранный день крестиком
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)  # Удаляем старую разметку
        bot.answer_callback_query(callback_query_id=call.id, text="Вы выбрали дату " + call.data)
        calendar_button = telebot.types.InlineKeyboardButton(text="❌ " + call.data, callback_data="CANCEL")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=telebot.types.InlineKeyboardMarkup(
                                          inline_keyboard=[[calendar_button]]))


# Функция, которая отправляет календарь в чат
@bot.message_handler(commands=['calendar'])
def send_calendar(message):
    # Получаем текущую дату и создаем список кнопок для каждого дня в месяце
    now = datetime.datetime.now()
    month_buttons = create_calendar(now.year, now.month)
    # Отправляем первую неделю календаря
    bot.send_message(message.chat.id, "Выберите день для бронирования:", reply_markup=month_buttons[0])


# Функция, которая обрабатывает выбор следующей или предыдущей недели в календаре
@bot.callback_query_handler(func=lambda call: call.data in ["PREV", "NEXT"])
def handle_callback(call):
    # Получаем текущую дату и создаем список кнопок для каждого дня в выбранном месяце
    now = datetime.datetime.now()
    if call.data == "PREV":
        # Если выбрана кнопка "Предыдущая неделя", отправляем предыдущую неделю календаря
        month_buttons = create_calendar(now.year, now.month)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=month_buttons[call.message.week_index - 1])
    elif call.data == "NEXT":
        # Если выбрана кнопка "Следующая неделя", отправляем следующую неделю календаря
        month_buttons = create_calendar(now.year, now.month)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=month_buttons[call.message.week_index + 1])
    # Получаем пользователя, который отправил запрос
    telegram_id = call.from_user.id
    user, _ = User.objects.get_or_create(telegram_id=telegram_id)

    # Получаем дату, которую пользователь забронировал
    date = call.data.split("_")[-1]
    year, month, day = map(int, date.split("-"))

    # Создаем запись о бронировании в базе данных
    booking = Booking.objects.create(date=datetime.date(year, month, day), user=user)

    # Получаем дату, которую пользователь выбрал
    date = call.data.split("_")[-1]
    year, month, day = map(int, date.split("-"))

    # Проверяем, есть ли уже бронирование на эту дату
    booking_exists = Booking.objects.filter(date=datetime.date(year, month, day), user=user).exists()

    if booking_exists:
        # Если бронирование уже есть, удаляем его
        Booking.objects.filter(date=datetime.date(year, month, day), user=user).delete()
        # Отправляем сообщение об отмене бронирования
        bot.answer_callback_query(call.id, "Бронирование отменено.")
    else:
        # Если бронирования еще нет, создаем его
        booking = Booking.objects.create(date=datetime.date(year, month, day), user=user)
        # Отправляем сообщение о бронировании
        bot.answer_callback_query(call.id, "Дата забронирована.")


# Запускаем бота
bot.polling()
