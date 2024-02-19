from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipesFilter
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
        methods=['delete', 'post'],
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
        if request.method == 'POST':
            serializer = FollowSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if follow.exists():
            follow.delete()
            return Response(
                f'Подписка на {author.username} отменена',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            'Такой подписки не существует',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['get', 'post'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """Просмотр подписок пользователя.
        Обработка запросов к '/api/users/subscriptions/
        """
        user = request.user
        queryset = (
            CustomUser.objects
            .filter(author__user=user)
        )
        pages = self.paginate_queryset(queryset)
        serializer = FollowReadSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """Представление списка рецептов/отдельного рецепта,
    создания, редактирования и удаления своего рецепта.
    Обрабатывает запросы к /api/recipes/ и /api/recipes/{id}/"""

    queryset = Recipe.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = CommonPagination
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'delete']:
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Подсчет ингредиентов и скачивание списка покупок. """
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values_list(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount'))
        shopping_result = []
        for ingredient in ingredients:
            shopping_result.append(
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["amount"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
            )
        shopping_itog = '\n'.join(shopping_result)
        response = FileResponse(
            shopping_itog,
            content_type='text/plain',
            as_attachment=True,
            filename='Список покупок.txt'
        )
        return response


class IngredientViewSet(ReadOnlyModelViewSet):
    """ Представление ингредиентов. """

    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
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


class BaseItemFavoriteShopingCartViewSet(ModelViewSet):
    model = None
    serializer_class = None

    def create(self, request):
        """Создание списка рецептов . """
        item_id = self.kwargs['id']
        item = get_object_or_404(Recipe.objects.get(id=item_id))
        user = request.user
        if self.model.objects.filter(user=user, recipe=item).exists():
            return Response(
                'Рецепт уже добавлен ',
                status=status.HTTP_400_BAD_REQUEST)

        new_item = self.model(user=user, recipe=item)
        new_item.save()
        serializer = self.serializer_class(
            new_item, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, **kwargs):
        """Удаление рецепта из списка . """
        item_id = kwargs['id']
        user = request.user
        item = get_object_or_404(Recipe, id=item_id)
        if not self.model.objects.filter(user=user, recipe=item).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.model.objects.get(user=user, recipe=item).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(ModelViewSet):
    """Cписок избранных рецептов
    Добавление / удаление рецепта из списка.
    """

    model = Favorite
    serializer_class = FavoriteSerializer
    item_type = 'favorites'
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    permission_classes = [IsAuthenticated]


class ShoppingCartViewSet(BaseItemFavoriteShopingCartViewSet):
    """ViewSet Список покупок
    Добавление рецепта в список покупок /
    удаление рецепта из списка покупок.
    """

    model = ShoppingCart
    serializer_class = ShoppingCartSerializer
    item_type = 'shopping cart'
    pagination_class = CommonPagination
    queryset = ShoppingCart.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
