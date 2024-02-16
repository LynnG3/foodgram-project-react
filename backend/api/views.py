from django.http import FileResponse
from django.db.models import OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientSearchFilter, RecipesFilter
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (CustomUserGetSerializer, CustomUserSerializer,
                             FavoriteSerializer, FollowReadSerializer,
                             FollowSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeReadSerializer, ShoppingCartSerializer,
                             TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Follow


class CommonPagination(PageNumberPagination):
    """Пагинация."""
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(UserViewSet):
    """Api для работы с пользователями.

    """
    pagination_class = CommonPagination
    permission_classes = [AllowAny, ]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'delete']:
            return CustomUserSerializer
        elif self.request.method == 'GET':
            return CustomUserGetSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=['get', 'delete', 'post'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Создание и удаление подписок.
        Обработка запросов к '/api/users/{id}/subscribe/'
        """
        user = request.user
        author = get_object_or_404(CustomUser, id=id)
        follow = Follow.objects.filter(user=user, author=author)
        data = {
            'user': user.id,
            'author': author.id,
        }
        if request.method == "GET" or request.method == "POST":
            if follow.exists():
                return Response(
                    "Вы уже подписаны", status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            if follow:
                follow.delete()
                return Response(
                    f"Подписка на {author.username} отменена",
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                "Такой подписки не существует",
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=['get', 'post'],
        detail=False,
        permission_classes=[IsAuthenticated],
        serializer_class=FollowReadSerializer,
        # pagination_class=LimitOffsetPagination
    )
    def subscriptions(self, request):
        """Просмотр подписок пользователя.
        Обработка запросов к '/api/users/subscriptions/
        """
        user = request.user
        follow = Follow.objects.filter(user=user)
        user_obj = [follow_obj.author.id for follow_obj in follow]

        recipes_limit = request.GET.get('recipes_limit', None)
        if recipes_limit is None:
            queryset = CustomUser.objects.filter(pk__in=user_obj)
        limited_recipes = Recipe.objects.filter(
            author=OuterRef('pk')
        ).order_by('-created_at')[:recipes_limit]
        queryset = (
            CustomUser.objects
            .filter(pk__in=user_obj)
            .prefetch_related(
                Prefetch(
                    'recipes',
                    queryset=limited_recipes,
                    to_attr='limited_recipes'
                )
            )
        )
        # queryset = CustomUser.objects.filter(pk__in=user_obj)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """Получение списка рецептов/отдельного рецепта,
    создание, редактирование, удаление своего рецепта. """

    queryset = Recipe.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = CommonPagination
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'delete']:
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=401)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # if self.request.user.is_authenticated:
        serializer.save(author=self.request.user)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Подсчет и скачивание списка покупок. """
        shopping_result = {}
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values_list('ingredient__name',
                      'ingredient__measurement_unit',
                      'amount')
        for ingredient in ingredients:
            name = ingredient[0]
            if name not in shopping_result:
                shopping_result[name] = {
                    'measurement_unit': ingredient[1],
                    'amount': ingredient[2],
                }
            else:
                shopping_result[name]['amount'] += ingredient[2]
        shopping_itog = (
            f"{name} - {value['amount']} " f"{value['measurement_unit']}\n"
            for name, value in shopping_result.items()
        )
        response = FileResponse(
            shopping_itog,
            content_type='text/plain',
            as_attachment=True,
            filename='Список покупок.txt'
        )
        # HttpResponse(shopping_itog, content_type='text/plain')
        # response['Content-Disposition'] = \
        #     'attachment; filename="Список покупок.txt"'
        return response


class IngredientViewSet(ReadOnlyModelViewSet):
    """ Представление ингредиентов. """

    filter_backends = [IngredientSearchFilter]
    search_fields = ['^name']
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class TagViewSet(ReadOnlyModelViewSet):
    """ Представление тегов. """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class RecipeNotFoundException(APIException):
    """Исключение для несуществующего рецепта. """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Такого рецепта не нашлось.'
    default_code = 'recipe_not_found'


class UserNotFoundException(APIException):
    """Исключение для несуществующего юзера. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Такого пользователя не нашлось.'
    default_code = 'user_not_found'


class FavoriteViewSet(ModelViewSet):
    """Cписок избранных рецептов
    Добавление / удаление рецепта из списка.
    """

    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список избранного. """
        recipe_id = self.kwargs['id']
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise RecipeNotFoundException
        if Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {'Этот рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite = Favorite(user=self.request.user, recipe=recipe)
        favorite.save()
        serializer = FavoriteSerializer(
            favorite, context={'request': request}
        )
        return Response(
            serializer.to_representation(instance=favorite),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта
        из списка избранного
        """
        recipe_id = kwargs['id']
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if not Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(ModelViewSet):
    """ViewSet Список покупок
    Добавление рецепта в список покупок /
    удаление рецепта из списка покупок /
    скачивание списка покупок
    """

    pagination_class = CommonPagination
    queryset = ShoppingCart.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список покупок. """
        recipe_id = self.kwargs['id']
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            raise RecipeNotFoundException
        if ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {'Этот рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shopping_cart = ShoppingCart(user=self.request.user, recipe=recipe)
        shopping_cart.save()
        serializer = ShoppingCartSerializer(
            shopping_cart, context={'request': request}
        )
        return Response(
            serializer.to_representation(instance=shopping_cart),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта из
        списка покупок
        """
        recipe_id = kwargs['id']
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if not ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
