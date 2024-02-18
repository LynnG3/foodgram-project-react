from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

# admin.site.register(Recipe)
# admin.site.register(Ingredient)
# admin.site.register(RecipeIngredient)
# admin.site.register(Favorite)
# admin.site.register(Tag)
# admin.site.register(ShoppingCart)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """ Администрирование ингредиентов. """

    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """ Администрирование тегов. """

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color')
    list_filter = ('name', 'color')


class RecipeIngredientInline(admin.TabularInline):
    """ Администрирование ингредиентов в рецептах. """

    model = RecipeIngredient


class TagInline(admin.TabularInline):
    """Администрирование тегов к рецептам. """

    model = Recipe.tags.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """ Администрирование рецептов. """

    inlines = (RecipeIngredientInline, TagInline)
    list_display = (
        'name',
        'text',
        'author',
        'pub_date',
        'cooking_time',
        'display_ingredients',
        'favorite_count',
        'display_tags'
    )
    search_fields = ('name', 'author__username', 'favorite_count')
    list_filter = ('name', 'author', 'tags')

    @admin.display(description='Количество добавлений в избранное')
    def favorite_count(self, obj):
        return obj.favorite.count()

    @admin.display(description='Отображение ингредиентов')
    def display_ingredients(self, recipe):
        return ', '.join([
            ingredients.name for ingredients in recipe.ingredients.all()])

    @admin.display(description='Теги')
    def display_tags(self, recipe):
        return ', '.join([tags.name for tags in recipe.tags.all()])


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Администрирование списков покупок.
    """

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(ShoppingCartAdmin):
    """ Администрирование избранного. """
