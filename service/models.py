from django.db import models

# Create your models here.
class Booking(models.Model):
    user_id = models.PositiveIntegerField(verbose_name="Внешний id пользователя")
    date = models.DateField(verbose_name="Дата")

    def __str__(self):
        return self.date



# class Profile(models.Model):
#     external_id = models.PositiveIntegerField(
#         verbose_name='Внешний ID пользователя'
#     )
#     name = models.CharField(
#         max_length=64,
#         verbose_name='Имя пользователя'
#     )
#
#     def __str__(self):
#         return self.name
#
#
# class Order(models.Model):
#     user = models.ForeignKey(
#         Profile,
#         on_delete=models.CASCADE
#     )
#     date = models.DateField()
#
#     def __str__(self):
#         return f"{self.user.name} - {self.date}"
