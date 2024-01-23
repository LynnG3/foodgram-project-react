from django.contrib import admin

from recipes.models import Ingredient, Favorite, Recipe, RecipeIngredient, Tag

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(Tag)
