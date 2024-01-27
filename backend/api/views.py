from djoser.views import UserViewSet
from rest_framework.pagination import PageNumberPagination
from api.serializers import FollowSerializer
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
    IsAdminUser
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsOwnerOrReadOnly
from api.serializers import (RecipeListSerializer,
                             RecipeCreateUpdateSerializer,
                             ShowFollowerSerializer,
                             CustomUserSerializer,
                             IngredientSerializer,
                             TagSerializer)
from recipes.models import Ingredient, Recipe, Tag


class CommonPagination(PageNumberPagination):
    """Пагинация."""
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(UserViewSet):
    """Api для работы с пользователями.

    """
    pagination_class = CommonPagination
    serializer_class = CustomUserSerializer

    # def get_serializer_class(self):
    #     if self.action == "create":
    #         return CustomUserSerializer
    #     return super().get_serializer_class()

    @action(detail=False, permission_classes=[IsOwnerOrReadOnly])
    def subscriptions(self, request):
        """Просмотр подписок пользователя"""
        subscriptions = self.request.user.following.all().order_by(
            '-date_joined'
        )
        page = self.paginate_queryset(subscriptions)
        serializer = ShowFollowerSerializer(
            page,
            many=True,
            context={"request": request})
        return self.get_paginated_response(serializer.data)


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


class IngredientViewSet(ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None
