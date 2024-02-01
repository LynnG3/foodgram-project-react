from djoser.views import UserViewSet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientSearchFilter, RecipesFilter

from api.permissions import IsOwnerOrReadOnly, IsAdminUser
from api.serializers import (RecipeReadSerializer,
                             FollowSerializer,
                             RecipeCreateUpdateSerializer,
                             CustomUserSerializer,
                             CustomUserGetSerializer,
                             IngredientSerializer,
                             RecipeIngredientSerializer,
                             TagSerializer,
                             FavoriteSerializer,
                             ShoppingCartSerializer)
from recipes.models import Ingredient, Recipe, Tag, Favorite, ShoppingCart
from users.models import CustomUser, Follow


class CommonPagination(PageNumberPagination):
    """Пагинация."""
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(UserViewSet):
    """Api для работы с пользователями.

    """
    pagination_class = CommonPagination
    permission_classes = (AllowAny, )

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

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Просмотр подписок пользователя"""
        queryset = self.request.user.follower.all()
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page,
                                      many=True,
                                      context={"request": request})
        return self.get_paginated_response(serializer.data)

    # @action(detail=False, permission_classes=[IsAuthenticated])
    # def subscriptions(self, request):
    #     """Просмотр подписок пользователя"""
    #     queryset = self.request.user.follower.all()
    #     page = self.paginate_queryset(queryset)
    #     serializer = FollowSerializer(page,
    #                                   many=True,
    #                                   context={"request": request})
    #     return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """Получение списка рецептов/отдельного рецепта,
    создание, редактирование, удаление своего рецепта. """

    queryset = Recipe.objects.all()
    # http_method_names = ['get', 'post', 'patch',]
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = CommonPagination
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'delete'):
            return RecipeCreateUpdateSerializer
        # elif self.request.method == 'GET':
        #     return CustomUserGetSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


    # @action(methods=["GET"], detail=False,
    #         permission_classes=[IsAuthenticated])
    # def download_shopping_cart(self, request):
    #     """Скачивание списка покупок"""


class IngredientViewSet(ReadOnlyModelViewSet):
    filter_backends = [IngredientSearchFilter]
    search_fields = ['^name']
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class FollowViewSet(ModelViewSet):
    """ Создание и удаление подписки. """

    serializer_class = FollowSerializer
    pagination_class = CommonPagination
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Создание подписки"""
        user_id = self.kwargs['id']
        user = get_object_or_404(CustomUser, id=user_id)
        subscribe = Follow.objects.create(user=request.user, author=user)
        serializer = FollowSerializer(subscribe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Удаление подписки"""
        author_id = self.kwargs['id']
        user_id = request.user.id
        Follow.objects.filter(user_id, author_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(ModelViewSet):
    """Cписок избранных рецептов
    Добавление / удаление рецепта из списка.
    """

    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список избранного. """
        recipes_id = self.kwargs['id']
        recipes = get_object_or_404(Recipe, id=recipes_id)
        Favorite.objects.create(user=request.user, recipes=recipes)
        serializer = FavoriteSerializer()
        return Response(
            serializer.to_representation(instance=recipes),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта
        из списка избранного
        """
        recipes_id = self.kwargs["id"]
        user_id = request.user.id
        Favorite.objects.filter(
            user__id=user_id, recipes__id=recipes_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(ModelViewSet):
    """ViewSet Список покупок
    Добавление рецепта в список покупок /
    удаление рецепта из списка покупок /
    скачивание списка покупок
    """

    serializer_class = ShoppingCartSerializer
    pagination_class = CommonPagination
    queryset = ShoppingCart.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список покупок. """
        recipe_id = self.kwargs['id']
        recipes = get_object_or_404(Recipe, id=recipe_id)
        ShoppingCart.objects.create(user=request.user, recipes=recipes)
        serializer = ShoppingCartSerializer()
        return Response(
            serializer.to_representation(instance=recipes),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта из
        списка покупок
        """
        recipe_id = self.kwargs["id"]
        user_id = request.user.id
        ShoppingCart.objects.filter(user__id=user_id,
                                    recipes__id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
