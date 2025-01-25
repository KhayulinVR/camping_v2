from myapp.models import MyModel

def get_all_dates():
    # Используем ORM Django для выборки всех значений поля 'date' из таблицы
    all_dates = MyModel.objects.values_list('date', flat=True)

    # Преобразуем выбранные значения в список
    date_list = list(all_dates)

    # Возвращаем список дат
    return date_list