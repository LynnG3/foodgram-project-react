from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Follow


@admin.register(CustomUser)
class UserAdmin(UserAdmin):
    """Администрирование пользователей."""

    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
    )
    list_filter = ('username', 'email',)
    search_fields = ('username', 'email',)
    ordering = ('username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Администрирование подписок."""

    list_display = (
        'user',
        'author',
    )
    list_filter = ('user', 'author',)
    search_fields = ('user__username', 'author__username',)
