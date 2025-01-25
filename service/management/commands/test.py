import telebot
import calendar
from datetime import datetime, timedelta
from django.conf import settings
from telebot import types

from service.models import *

bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)

CALENDAR, BOOKING_DATE = range(2)


class BookingData:
    def __init__(self):
        self.user_id = None
        self.selected_dates = []


booking_data = BookingData()


def generate_calendar(year, month):
    markup = telebot.types.InlineKeyboardMarkup()
    month_calendar = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    row = []
    for day_name in calendar.day_name:
        row.append(telebot.types.InlineKeyboardButton(text=day_name[:2], callback_data='none'))
    markup.row(*row)

    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(telebot.types.InlineKeyboardButton(text=' ', callback_data='none'))
            else:
                day_str = datetime(year, month, day).strftime('%d.%m.%Y')
                if datetime(year, month, day) < datetime.today():
                    row.append(telebot.types.InlineKeyboardButton(text=str(day), callback_data='none'))
                elif day_str in booking_data.selected_dates:
                    row.append(telebot.types.InlineKeyboardButton(text=str(day) + '✅', callback_data='day_selected,' + day_str))
                else:
                    row.append(
                        telebot.types.InlineKeyboardButton(text=str(day), callback_data='calendar_day,' + day_str))
        markup.row(*row)

    return markup, month_name


def update_calendar(year, month, chat_id, message_id):
    markup, month_name = generate_calendar(year, month)
    # Add 'Order' button
    markup.row(types.InlineKeyboardButton('Забронировать', callback_data='order'))

    # Add 'Hide' button
    markup.row(types.InlineKeyboardButton('Скрыть календарь', callback_data='hide'))

    day_str = datetime(year, month, 1).strftime('%d.%m.%Y')

    markup.row(types.InlineKeyboardButton('<', callback_data='PREV_MONTH,'+day_str), types.InlineKeyboardButton('>', callback_data='NEXT_MONTH,'+day_str))

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)




@bot.message_handler(commands=['start'])
def handle_book_command(message):
    booking_data.user_id = message.chat.id
    booking_data.selected_dates = []
    today = datetime.today()
    markup, month_name = generate_calendar(today.year, today.month)
    bot.send_message(chat_id=message.chat.id, text='Choose a date:', reply_markup=markup)
    booking_data.current_calendar_month = today.month
    booking_data.current_calendar_year = today.year
    booking_data.current_message_id = None
    booking_data.current_message_text = None
    booking_data.current_state = CALENDAR




@bot.callback_query_handler(func=lambda call: call.data == 'hide')
def handle_hide_calendar(callback_query):
    bot.edit_message_text(text='Календарь скрыт', chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id)




@bot.callback_query_handler(func=lambda call: call.data.startswith('PREV_MONTH'))
def handle_hide_calendar(callback_query):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%d.%m.%Y')
    print(day_str)
    print(day.day)
    print(day.month)
    print(day.year)

    update_calendar(int(day.year), int(day.month), callback_query.message.chat.id, callback_query.message.message_id)




@bot.callback_query_handler(func=lambda call: call.data.startswith('day_selected,'))
def handle_hide_calendar(callback_query, selected_dates=None):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%d.%m.%Y')
    try:
        # Находим индекс элемента
        index = booking_data.selected_dates.index(day_str)
        booking_data.selected_dates.pop(index)
    except ValueError:
        pass
    print(booking_data.current_calendar_year)
    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month,
                    callback_query.message.chat.id, callback_query.message.message_id)




@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_day,'))
def handle_calendar_day(callback_query):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%d.%m.%Y')
    booking_data.selected_dates.append(day_str)
    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month,
                    callback_query.message.chat.id, callback_query.message.message_id)




@bot.callback_query_handler(func=lambda call: True)
def handle_all_other_callbacks(callback_query):
    bot.answer_callback_query(callback_query.id, text='This feature is not implemented yet')





@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_day,'))
def handle_calendar_day(callback_query):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%d.%m.%Y')

    # Check if the day is already booked
    if Booking.objects.filter(booking_date=day).exists():
        bot.answer_callback_query(callback_query.id, text='Этот день уже забронирован', show_alert=True)
        return

    booking_data.selected_dates.append(day_str)
    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month,
                    callback_query.message.chat.id, callback_query.message.message_id)

    # Save booking to database
    booking = Booking(user_id=booking_data.user_id, booking_date=day)
    booking.save()





@bot.callback_query_handler(func=lambda call: call.data == 'order')
def handle_order(callback_query):
    booking_date_str = ', '.join(booking_data.selected_dates)
    bot.send_message(callback_query.message.chat.id, f'Вы заказали даты: {booking_date_str}')

    # Reset selected dates
    booking_data.selected_dates = []

    # Remove calendar
    bot.edit_message_text(text='Календарь скрыт', chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id)

    # Save bookings to database
    user_id = booking_data.user_id
    bookings = [Booking(user_id=user_id, booking_date=datetime.strptime(date_str, '%d.%m.%Y')) for date_str in
                booking_data.selected_dates]
    Booking.objects.bulk_create(bookings)


bot.polling()
