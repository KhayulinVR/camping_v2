from django.db import models


# Create your models here.
class User(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='Внешний ID'
    )
    username = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    first_name = models.CharField(
        max_length=255
    )
    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


# class Booking(models.Model):
#     date = models.DateField(
#         verbose_name='Дата'
#     )
#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE
#     )

