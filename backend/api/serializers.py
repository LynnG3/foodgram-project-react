from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('amount', 'name', 'measurement_unit', 'id')


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('recipe', 'id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Получение списка рецептов."""

    ingredients = serializers.SerializerMethodField()
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
        fields = ('name', 'ingredients', 'is_favorite', 'text', 'author')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    def validate_ingredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент."
            )
        return value

    def create(self, validated_data):
        """Создание рецепта"""
        image = validated_data.pop("image")
        ingredients_data = validated_data.pop("ingredients")
        recipes = Recipe.objects.create(image=image, **validated_data)
        tags = self.initial_data.get("tags")
        recipes.tags.set(tags)
        self.create_ingredients(ingredients_data, recipes)
        return recipes

    def create_ingredients(self, validated_data):
        """Добавление ингредиентов в рецепт"""
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)

        create_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(
            create_ingredients
        )
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get("tags")
        instance.tags.set(tags_data)
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()

            create_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            RecipeIngredient.objects.bulk_create(
                create_ingredients
            )
        return super().update(instance, validated_data)

    def to_representation(self, obj):
        """Возвращаем прдеставление в таком же виде, как и GET-запрос."""
        self.fields.pop('ingredients')
        self.fields.pop('tags')
        representation = super().to_representation(obj)
        representation['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data
        representation['tags'] = TagSerializer(
            Tag.objects.filter(recipe=obj).all(), many=True
        ).data
        return representation

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


class UsersRecipeSerializer(serializers.ModelSerializer):
    """Cериализатор рецептов автора для подписок"""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError('Невозможно подписаться на себя')
        # elif is_subscribed == True:
        #     raise serializers.ValidationError('Вы уже подписаны на этого автора')
        return data

    class Meta:
        model = Follow
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )


    def get_is_subscribed(self, obj):
        """Проверка подписки
        текущего пользователя на автора
        """
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        """Получение рецептов автора"""
        # request = self.context.get("request")
        # limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj.author)
        # if limit:
        #     queryset = queryset[: int(limit)]
        return UsersRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Получение общего
        количества рецептов автора
        """
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
        fields = ["id", "name", "image", "cooking_time"]
        validators = UniqueTogetherValidator(
            queryset=Favorite.objects.all(), fields=("user", "recipes")
            )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор Список покупок"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(max_length=None, use_url=False)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = ShoppingCart
        fields = ["id", "name", "image", "cooking_time"]
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(), fields=("user", "recipes")
            )
        ]
