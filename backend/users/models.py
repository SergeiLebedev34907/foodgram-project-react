from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField("Логин", max_length=150, unique=True)
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    email = models.EmailField("Электронная почта", max_length=254, unique=True)

    class Meta:
        ordering = ["date_joined"]
