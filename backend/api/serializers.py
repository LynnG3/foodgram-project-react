'''Сериализатор для приложений recipes и users. '''
import re

from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.serializers import SerializerMethodField, ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Follow


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор создания/редактирования/удаления пользователя. """

    email = serializers.EmailField()
    username = serializers.CharField(required=True, max_length=150)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )

    def validate_username(self, username):

        pattern = r'^[\w.@+-]+\Z'
        if not re.match(pattern, username):
            raise serializers.ValidationError(
                'Имя пользователя содержит недопустимый символ.'
            )
        return username


class SubscriptionMixin:

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj.id).exists()


class CustomUserGetSerializer(UserSerializer, SubscriptionMixin):
    """Сериализатор для просмотра инфо пользователя. """

    is_subscribed = SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed'
        )


class PasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля. """

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = '__all__'


class TokenSerializer(serializers.ModelSerializer):
    """Сериализатор получения токена. """

    token = serializers.CharField(source='key')

    class Meta:
        model = Token
        fields = ('token',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега. """

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента. """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Получение рецепта."""

    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True
    )
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        """Получение избранных рецептов."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Получение списка покупок."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return ShoppingCart.objects.filter(recipe=obj, user=user).exists()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'image',
            'author',
            'ingredients',
            'cooking_time',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания/изменения/удаления своего рецепта. """

    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    tags = serializers.SlugRelatedField(
        many=True, queryset=Tag.objects.all(), slug_field='id'
    )
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'author',
            'ingredients',
            'tags',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        """Метод валидации данных перед созданием рецепта."""
        image = data.get('image')
        if not image:
            raise serializers.ValidationError(
                {'Добавьте фото'}
            )
        data['image'] = image
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'Добавьте хотя бы один ингредиент'}
            )
        ingredients_result = []
        for ingredient in ingredients:
            if ingredient in ingredients_result:
                raise serializers.ValidationError(
                    'Этот ингредиент уже добавлен'
                )
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    {'amount': 'Маловато будет!'}
                )
            ingredients_result.append(ingredient)
        data['ingredients'] = ingredients_result

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'Добавьте хотя бы один тег'}
            )
        settags = set(tags)
        if len(tags) != len(settags):
            raise serializers.ValidationError('Этот тег уже добавлен')
        data['tags'] = tags
        return data

    @staticmethod
    def create_ingredients_in_recipe(ingredients, recipe):
        """Создание ингредиента в рецепте. """
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_item.get('ingredient'),
                amount=ingredient_item.get('amount'),
            ) for ingredient_item in ingredients
        ])

    def create(self, validated_data):
        """Создание рецепта. """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_in_recipe(
            ingredients, recipe
        )
        return recipe

    def update(self, instance, validated_data):
        """Редактирование рецепта. """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_in_recipe(
            recipe=instance,
            ingredients=ingredients,
        )
        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        """Определяет сериализатор, используемый для чтения. """
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class UsersRecipeSerializer(serializers.ModelSerializer):
    """Cериализатор чтения рецептов
    для подписок, избранного и корзины. """

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowReadSerializer(serializers.ModelSerializer, SubscriptionMixin):
    """Сериализатор просмотра подписок текущего пользователя. """

    is_subscribed = SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """Получение рецептов автора. """
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
            queryset = queryset[:recipes_limit]
        serializer = UsersRecipeSerializer(
            queryset,
            many=True,
            context=self.context
        )
        return serializer.data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора"""
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор создания/удаления подписки."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора. '
            ),
        )

    def validate(self, data):
        """
        Проверка подписки на самого себя.
        """
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise ValidationError(['Нельзя подписаться на себя.'])
        return data

    def to_representation(self, instance):
        """Определяет сериализатор, используемый для чтения."""
        return FollowReadSerializer(
            instance.author,
            context={'request':
                     self.context['request']}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов. """

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное. '
            ),
        )

    def to_representation(self, instance):
        """Определяет сериализатор для чтения."""
        recipe_instance = instance.recipe
        return UsersRecipeSerializer(
            recipe_instance,
            context={'request':
                     self.context['request']}
        ).data


class ShoppingCartSerializer(FavoriteSerializer):
    """Сериализатор списка покупок. """

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину покупок. '
            ),
        )
