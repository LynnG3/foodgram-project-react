from typing import Optional

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

from users.models import CustomUser

User = get_user_model()


class Ingredient(models.Model):

    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """Тэги."""
    # Отображается в UI
    name = models.CharField(
        max_length=200, verbose_name='Название', unique=True
    )
    color = models.CharField(
        max_length=200, null=True, verbose_name='Цвет', unique=True
    )
    slug = models.SlugField(
        max_length=200, null=True, verbose_name='Слаг', unique=True
    )


class RecipeQuerySet(models.QuerySet):

    def add_user_annotations(self, user_id: Optional[int]):
        return self.annotate(
            is_favorite=Exists(
                Favorite.objects.filter(
                    user_id=user_id, recipe__pk=OuterRef('pk')
                )
            ),
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        "Ссылка на изображение",
        upload_to="recipes/images/",
        null=True,
        default=None
    )
    text = models.TextField(verbose_name='Текст')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1,
                'Время приготовления не может быть меньше 1 минуты'
            )
        ],
    )
    tags = models.ManyToManyField(
        Tag, related_name="recipes"
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class TagsInRecipe(models.Model):

    tag = models.ForeignKey(
        Tag, verbose_name="Тег в рецепте", on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Теги в рецепте"
        verbose_name_plural = verbose_name


class RecipeIngredient(models.Model):
    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}'

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'


class Favorite(models.Model):
    """Модель избранных рецептов. """

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        default=None,
        verbose_name='Рецепт'
    )

    def __str__(self):
        return f'Избранный {self.recipe} у {self.user}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_user_recipe'
            )
        ]
        default_related_name = 'favorite'
        verbose_name = 'Объект избранного'
        verbose_name_plural = 'Объекты избранного'


class ShoppingCart(models.Model):
    """Модель Список покупок"""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        null=True,
        default=None,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        default_related_name = 'shopping_cart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_recipe_list'
            )
        ]

    def __str__(self):
        return f"Список покупок пользователя {self.user.username}"
