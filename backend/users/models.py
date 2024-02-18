from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    "Кастомная модель пользователя."

    id = models.AutoField(primary_key=True)
    email = models.EmailField(
        'Электронная почта',
        blank=False,
        null=False,
        unique=True,
        max_length=254
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        # ordering = ???
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email',
            )
        ]

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки"""

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'),
            models.CheckConstraint(
                name='user_is_not_author',
                check=~models.Q(user=models.F('author'))
            ),
        ]

    def __str__(self):
        return f"{self.user.username} подписан на {self.author.username}"
