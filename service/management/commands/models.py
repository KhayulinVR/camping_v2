from django.db import models


class MyBooking(models.Model):
    user_id = models.PositiveIntegerField(verbose_name="Внешний id пользователя")
    date = models.DateField(verbose_name="Дата")