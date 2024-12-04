from core.constants import UsersConstants
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

user_constants = UsersConstants()


class CustomUser(AbstractUser):
    first_name = models.CharField(
        max_length=user_constants.CUSTOMUSER_FIRST_NAME_LENGTH,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=user_constants.CUSTOMUSER_LAST_NAME_LENGTH,
        verbose_name='Фамилия'
    )
    username = models.CharField(
        max_length=user_constants.CUSTOMUSER_USERNAME_LENGTH,
        unique=True,
        verbose_name='Никнейм',
        validators=(RegexValidator(
            regex=r'^[\w.@+-]+\Z', message='Недопустимые символы'),)
    )
    email = models.EmailField(
        max_length=user_constants.CUSTOMUSER_EMAIL_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Адрес электронной почты',
    )
    password = models.CharField(
        max_length=user_constants.CUSTOMUSER_PASSWORD_LENGTH,
        verbose_name='Пароль'
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
