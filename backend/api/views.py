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
from api.serializers import (RecipeListSerializer,
                             FollowSerializer,
                             RecipeCreateUpdateSerializer,
                             CustomUserSerializer,
                             CustomUserGetSerializer,
                             IngredientSerializer,
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
    # serializer_class = CustomUserGetSerializer
    permission_classes = (AllowAny, )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "delete"]:
            return CustomUserSerializer
        elif self.request.method == 'GET':
            return CustomUserGetSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    # @action(detail=False, permission_classes=[IsOwnerOrReadOnly])
    # def subscriptions(self, request):
    #     """Просмотр подписок пользователя"""
    #     subscriptions = self.request.user.following.all().order_by(
    #         '-date_joined'
    #     )
    #     page = self.paginate_queryset(subscriptions)
    #     serializer = ShowFollowerSerializer(
    #         page,
    #         many=True,
    #         context={"request": request})
    #     return self.get_paginated_response(serializer.data)

    # @action(detail=False, permission_classes=[IsAuthenticated])
    # def subscriptions(self, request):
    #     """Просмотр подписок пользователя"""
    #     queryset = self.request.user.follower.all()
    #     page = self.paginate_queryset(queryset)
    #     serializer = FollowSerializer(page,
    #                                   many=True,
    #                                   context={"request": request})
    #     return self.get_paginated_response(serializer.data)


class RecipesViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch',]
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    pagination_class = CommonPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer

        return RecipeListSerializer

    def get_queryset(self):
        qs = Recipe.objects.add_user_annotations(self.request.user.pk)

        # Фильтры из GET-параметров запроса, например.
        author = self.request.query_params.get('author', None)
        if author:
            qs = qs.filter(author=author)

        return qs


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
    """ Создание и удаление подписки
    """
    serializer_class = FollowSerializer
    pagination_class = CommonPagination
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Создание подписки"""
        user_id = self.kwargs["id"]
        user = get_object_or_404(CustomUser, id=user_id)
        subscribe = Follow.objects.create(user=request.user, author=user)
        serializer = FollowSerializer(subscribe, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Удаление подписки"""
        author_id = self.kwargs["id"]
        user_id = request.user.id
        Follow.objects.filter(user_id, author_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(ModelViewSet):
    """ViewSet Списки избранных рецептов
    Добавление /
    удаление из списка
    """
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Добавление рецепта
        в список избранного
        """
        recipes_id = self.kwargs["id"]
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
        """Добавление рецепта в список покупок
        """
        recipe_id = self.kwargs["id"]
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
