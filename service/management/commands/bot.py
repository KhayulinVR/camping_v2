import telebot
import calendar
from datetime import datetime, timedelta, date
from django.conf import settings
from telebot import types
from .models import *

from service.models import *


bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)

CALENDAR, BOOKING_DATE = range(2)


class BookingData:
    def __init__(self):
        self.user_id = None
        self.selected_dates = []


booking_data = BookingData()



def generate_calendar(year, month):
    closed_dates = MyBooking.objects.values_list('date', flat=True)

    markup = telebot.types.InlineKeyboardMarkup()
    month_calendar = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    markup.row(types.InlineKeyboardButton(f'{year}, {calendar.month_name[month]}', callback_data='none'))
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
                day_date = date(year, month, day)
                day_str = datetime(year, month, day).strftime('%Y.%m.%d')
                if datetime(year, month, day) < datetime.today():
                    row.append(telebot.types.InlineKeyboardButton(text=str(day), callback_data='none'))
                elif day_str in booking_data.selected_dates:
                    row.append(telebot.types.InlineKeyboardButton(text=str(day) + '✅', callback_data='day_selected,' + day_str))
                elif day_date in closed_dates:
                    row.append(telebot.types.InlineKeyboardButton(text=str(day) + '❌',
                                                                  callback_data='day_closed'))
                else:
                    row.append(
                        telebot.types.InlineKeyboardButton(text=str(day), callback_data='calendar_day,' + day_str))
        markup.row(*row)
    markup.row(types.InlineKeyboardButton('<', callback_data='PREV_MONTH,' + str(year) + "," + str(month)),
               types.InlineKeyboardButton('>', callback_data='NEXT_MONTH,' + str(year) + "," + str(month)))
    markup.row(types.InlineKeyboardButton('Забронировать', callback_data='order'))
    markup.row(types.InlineKeyboardButton('Скрыть календарь', callback_data='hide'))

    return markup, month_name


def update_calendar(year, month, chat_id, message_id):
    markup, month_name = generate_calendar(year, month)
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)




@bot.message_handler(commands=['start'])
def handle_book_command(message):
    booking_data.user_id = message.chat.id
    booking_data.selected_dates = []
    today = datetime.today()
    markup, month_name = generate_calendar(today.year, today.month)
    bot.send_message(chat_id=message.chat.id, text='Выберите даты:', reply_markup=markup)
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
    #print(callback_query.data.split(','))
    _, curr_year, curr_month = callback_query.data.split(',')
    curr = datetime(int(curr_year), int(curr_month), 1)
    pre = curr - timedelta(days=1)
    booking_data.current_calendar_year = int(pre.year)
    booking_data.current_calendar_month = int(pre.month)

    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month , callback_query.message.chat.id, callback_query.message.message_id)



@bot.callback_query_handler(func=lambda call: call.data.startswith('NEXT_MONTH'))
def handle_hide_calendar(callback_query):
    #print(callback_query.data.split(','))
    _, curr_year, curr_month = callback_query.data.split(',')
    curr = datetime(int(curr_year), int(curr_month), 1)
    pre = curr + timedelta(days=31)
    booking_data.current_calendar_year = int(pre.year)
    booking_data.current_calendar_month = int(pre.month)


    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month , callback_query.message.chat.id, callback_query.message.message_id)




@bot.callback_query_handler(func=lambda call: call.data.startswith('day_selected,'))
def handle_hide_calendar(callback_query, selected_dates=None):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%Y.%m.%d')
    try:
        # Находим индекс элемента
        index = booking_data.selected_dates.index(day_str)
        booking_data.selected_dates.pop(index)
    except ValueError:
        pass
    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month,
                    callback_query.message.chat.id, callback_query.message.message_id)




@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_day,'))
def handle_calendar_day(callback_query):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%Y.%m.%d')
    booking_data.selected_dates.append(day_str)
    # print(MyBooking.objects.values_list('date', flat=True))


    update_calendar(booking_data.current_calendar_year, booking_data.current_calendar_month,
                    callback_query.message.chat.id, callback_query.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'order')
def handle_order(callback_query):
    booking_date_str = ', '.join(booking_data.selected_dates)
    bot.send_message(callback_query.message.chat.id, f'Вы заказали даты: {booking_date_str}')

    for i in range(len(booking_data.selected_dates)):
        #print(booking_data.selected_dates[i])
        new_date = date(int(booking_data.selected_dates[i][:4]),
                                 int(booking_data.selected_dates[i][5:7]),
                                 int(booking_data.selected_dates[i][8:]))
        k = MyBooking(user_id=callback_query.message.chat.id, date=new_date)
        k.save()

    # Reset selected dates
    booking_data.selected_dates = []

    # Remove calendar
    bot.edit_message_text(text='Календарь скрыт', chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id)

    # Save bookings to database
    # user_id = booking_data.user_id
    # bookings = [Booking(user_id=user_id, booking_date=datetime.strptime(date_str, '%d.%m.%Y')) for date_str in
    #             booking_data.selected_dates]
    # MyBooking.objects.bulk_create(bookings)




@bot.callback_query_handler(func=lambda call: True)
def handle_all_other_callbacks(callback_query):
    bot.answer_callback_query(callback_query.id, text='This feature is not implemented yet')





@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_day,'))
def handle_calendar_day(callback_query):
    _, day_str = callback_query.data.split(',')
    day = datetime.strptime(day_str, '%Y.%m.%d')

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






bot.polling()
