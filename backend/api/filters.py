from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe
from users.models import CustomUser


class IngredientFilter(FilterSet):
    """Фильтр для поиска ингредиентов по названию. """

    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipesFilter(FilterSet):
    """Фильтр для поиска рецептов по
    избранному, автору, списку покупок и
    тегам"""
    author = filters.ModelChoiceFilter(queryset=CustomUser.objects.all())
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags"]

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user.id)
        return queryset.objects.all()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user.id)
        return queryset.objects.all()
