import re

from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.serializers import SerializerMethodField, ValidationError
from rest_framework.validators import UniqueTogetherValidator
from users.models import CustomUser, Follow


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор для создания/редактирования/удаления пользователя"""

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


class CustomUserGetSerializer(UserSerializer):
    """Сериализатор для просмотра пользователя и списка пользолвателей"""
    is_subscribed = SerializerMethodField(read_only=True)

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

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя"""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = "__all__"


class TokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(source='key')

    class Meta:
        model = Token
        fields = ('token',)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Получение рецепта."""

    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    # image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        """Получение ингредиентов. Возвращает отдельный сериализатор."""
        return RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj), many=True
        ).data

    def get_is_favorited(self, obj):
        """Получение избранных рецептов."""
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Получение списка покупок."""
        request = self.context.get("request")
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
        many=True, queryset=Tag.objects.all(), slug_field="id"
    )
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

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
            'is_favorited',
            'is_in_shopping_cart'
        )

    def validate(self, data):
        """Метод валидации данных перед созданием рецепта."""
        image = data.get('image')
        if not image:
            raise serializers.ValidationError(
                {'Добавьте фото'}
            )
        data['image'] = image
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError(
                    {'Добавьте название рецепта'}
                )
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
                {'error': 'Добавьте хотя бы один тег'}
            )
        settags = set(tags)
        if len(tags) != len(settags):
            raise serializers.ValidationError('Этот тег уже добавлен')
        data['tags'] = tags
        return data

    @staticmethod
    def create_ingredients_in_recipe(ingredients, recipe):
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
        tags = list(validated_data.pop('tags'))
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_in_recipe(
            ingredients, recipe
        )
        return recipe

    def update(self, instance, validated_data):
        # """Редактирование рецепта. """
        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get("tags")
        instance.tags.set(tags_data)
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        self.create_ingredients_in_recipe(
            validated_data.get('ingredients'),
            instance
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        """Определяет какой сериализатор будет использоваться для чтения."""
        return RecipeReadSerializer(
            instance,
            context={'request':
                     self.context['request']}
        ).data


class UsersRecipeSerializer(serializers.ModelSerializer):
    """Cериализатор рецептов автора на чтение
    для подписок, избранного и корзины"""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowReadSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра подписки."""

    recipes = UsersRecipeSerializer(many=True)
    # recipes = serializers.SerializerMethodField('get_recipes')
    limited_recipes = serializers.SerializerMethodField('get_windowed_recipes')
    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')
    recipes_count = serializers.SerializerMethodField('get_recipes_count')

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'limited_recipes'
        )

    def get_windowed_recipes(self, obj):
        recipes = getattr(obj, 'limited_recipes', [])
        # recipes = Recipe.objects.filter(author=obj)
        # if 'recipes_limit' in self.context.get('request').GET:
        #     recipes_limit = self.context.get('request').GET['recipes_limit']
        return UsersRecipeSerializer(recipes, many=True).data
        #     return recipes_limit
        #     recipes = recipes[:int(recipes_limit)]
        # return UsersRecipeSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        """Проверка подписки текущего юзера на автора. """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=obj.id, author=obj.id).exists()
        # return Follow.objects.filter(
        #   user=self.context['request'].user, author=obj
        #   ).exists()

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора"""
        return obj.recipes.count()
        # return obj.recipes.all().count()
        # return Recipe.objects.filter(author=obj.author).count()


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
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
            )
        ]

    def validate(self, value):
        """
        Проверка подписки на самого себя .
        """
        user = value.get('user')
        author = value.get('author')
        if user == author:
            raise ValidationError(['Нельзя подписаться на себя.'])
        return value

    def to_representation(self, instance):
        """Определяет какой сериализатор будет использоваться для чтения."""
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
        validators = UniqueTogetherValidator(
            queryset=Favorite.objects.all(), fields=('user', 'recipe')
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
                queryset=ShoppingCart.objects.all(), fields=('user', 'recipe')
            ),
        )
