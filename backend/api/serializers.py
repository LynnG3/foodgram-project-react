from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.serializers import ValidationError
from rest_framework.serializers import SerializerMethodField
from rest_framework.authtoken.models import Token
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import Ingredient, RecipeIngredient, Recipe, Tag, Favorite, ShoppingCart
from users.models import CustomUser, Follow


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор для создания/редактирования/удаления пользователя"""

    email = serializers.EmailField()
    username = serializers.CharField()

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


# class SubscribeMixin():
#     is_subscribed = serializers.SerializerMethodField()

#     # def get_is_subscribed(self, obj):
#     #     # user_id = obj.id if isinstance(obj, CustomUser) else obj.author.id
#     #     # request_user = self.context.get('request').user.id
#     #     request = self.context.get("request")
#     #     if request is None or request.user.is_anonymous:
#     #         return False
#     #     return Follow.objects.filter(
#     #         user=request.user, author=obj
#     #     ).exists()
#     #     # return Follow.objects.filter(
#     #     #     author=user_id,
#     #     #     user=request_user
#     #     #     ).exists()
    
#     def get_is_subscribed(self, obj):
#         """Проверка подписки пользователя"""
#         user = self.context.get("request").user
#         if user.is_anonymous:
#             return False
#         return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomUserGetSerializer(UserSerializer):
    """Сериализатор для получения модели пользователя и списка пользолвателей"""
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
    # recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        # source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredients.name', read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredients.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Получение рецептов."""

    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    is_favorite = serializers.BooleanField()
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    def get_ingredients(self, obj):
        """Возвращает отдельный сериализатор."""
        return RecipeIngredient(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data

    class Meta:
        model = Recipe
        fields = ('name', 'ingredients', 'is_favorite', 'text', 'author', 'tags')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания/изменения/удаления своего рецепта. """

    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = CustomUserSerializer(read_only=True)
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
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'Добавьте хотя бы один ингредиент'}
            )
        ingredients_result = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_item["id"]
            )
            if ingredient in ingredients_result:
                raise serializers.ValidationError(
                    'Ингредиент уже добавлен в рецепт'
                )
            amount = ingredient_item['amount']
            if not (isinstance(ingredient_item['amount'], int)
                    or ingredient_item['amount'].isdigit()):
                raise ValidationError('Введите целое число')
            ingredients_result.append({'ingredients': ingredient,
                                       'amount': amount
                                       })
        data['ingredients'] = ingredients_result

        tags = self.initial_data.get('tags')
        tags_result = []
        for tag_item in tags:
            tag = get_object_or_404(
                Tag,
                name=tag_item["name"]
            )
        # if len(tags) != len(set(tags)):
            if tag in tags_result:
                raise serializers.ValidationError(
                    'Этот тег уже добавлен'
                )
        data['tags'] = tags_result

        return data

    # def validate_ingredients(self, value):
    #     if len(value) < 1:
    #         raise serializers.ValidationError(
    #             "Добавьте хотя бы один ингредиент."
    #         )
    #     return value

    def create_ingredients_in_recipe(ingredients, recipes):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipes=recipes,
                ingredients=ingredient["ingredients"],
                amount=ingredient.get("amount"),
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        """Создание рецепта. """
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        tags_data = validated_data.pop('tags')
        image = validated_data.pop('tags')
        recipe.tags.set(tags_data)
        self.create_ingredients_in_recipe(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Редактирование рецепта. """
        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get("tags")
        instance.tags.set(tags_data)
        RecipeIngredient.objects.filter(recipes=instance).all().delete()
        self.create_ingredients_in_recipe(
            validated_data.get('ingredients'),
            instance
        )
        instance.save()
        return instance

    # def to_representation(self, obj):
    #     """Возвращаем прдеставление в таком же виде, как и GET-запрос. """
    #     self.fields.pop('ingredients')
    #     self.fields.pop('tags')
    #     representation = super().to_representation(obj)
    #     representation['ingredients'] = RecipeIngredientSerializer(
    #         RecipeIngredient.objects.filter(recipe=obj).all(), many=True
    #     ).data
    #     representation['tags'] = TagSerializer(
    #         Tag.objects.filter(recipe=obj).all(), many=True
    #     ).data
    #     return representation
    def to_representation(self, instance):
        """Определяет какой сериализатор будет использоваться для чтения."""
        return RecipeReadSerializer(
            instance,
            context={'request':
                     self.context['request']}
            ).data

    def get_is_favorited(self, obj):
        """Проверка наличия рецепта в избранном"""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(recipefavorites__user=user,
                                     id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в списке покупок"""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(shoppinglist__user=user,
                                     id=obj.id).exists()


class UsersRecipeSerializer(serializers.ModelSerializer):
    """Cериализатор рецептов автора для подписок"""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""

    # user_id = serializers.ReadOnlyField(source='user.id')
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='user.email')
    # id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'user',
            'author',
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны'
            )
        ]

    def validate(self, value):
        """
        Проверка подписки на самого себя/на несуществующего автора.
        """
        author = self.initial_data.get('author')
        author = get_object_or_404(
                Follow,
                id=author["id"]
            )
        if value['user'] == value['author']:
            raise ValidationError(['Нельзя подписаться на себя.'])
        # elif not value['author'].exists():
        
        return value

    def get_is_subscribed(self, obj):
        """Проверка подписки текущего юзера на автора. """

        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        """Получение рецептов автора"""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[: int(limit)]
        return UsersRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора"""
        return Recipe.objects.filter(author=obj.author).count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        validators = UniqueTogetherValidator(
            queryset=Favorite.objects.all(), fields=('user', 'recipes')
            )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор Список покупок"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(max_length=None, use_url=False)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = ShoppingCart
        fields = ['id', 'name', 'image', 'cooking_time']
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(), fields=('user', 'recipes')
            )
        ]
