from djoser.views import UserViewSet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
# from rest_framework.mixins import CreateModelMixin, ListModelMixin
# from rest_framework.filters import SearchFilter

from api.filters import IngredientSearchFilter, RecipesFilter

from api.permissions import IsOwnerOrReadOnly
from api.serializers import (RecipeReadSerializer,
                             FollowSerializer,
                             FollowReadSerializer,
                             RecipeCreateUpdateSerializer,
                             CustomUserSerializer,
                             CustomUserGetSerializer,
                             IngredientSerializer,
                             TagSerializer,
                             FavoriteSerializer,
                             ShoppingCartSerializer)
from recipes.models import (Ingredient,
                            Recipe,
                            RecipeIngredient,
                            Tag,
                            Favorite,
                            ShoppingCart)
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

    @action(
            detail=False,
            methods=['get', 'post'],
            permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Просмотр подписок пользователя"""
        user = request.user
        follow = Follow.objects.filter(user=user)
        user_obj = []
        for follow_obj in follow:
            user_obj.append(follow_obj.author)
        # queryset = self.request.user.follower.all()
        page = self.paginate_queryset(user_obj)
        serializer = FollowReadSerializer(
            page,
            many=True,
            context={'current_user': user}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['get', 'delete', 'post'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Создание и удаление подписок """
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
            follow.delete()
            return Response(
                f"Подписка на {author.username} отменена",
                status=status.HTTP_204_NO_CONTENT
            )


class RecipeViewSet(ModelViewSet):
    """Получение списка рецептов/отдельного рецепта,
    создание, редактирование, удаление своего рецепта. """

    queryset = Recipe.objects.all()
    # http_method_names = ['get', 'post', 'patch',]
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

    @action(methods=["GET"], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок"""
        shopping_result = {}
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values_list('ingredients__name',
                      'ingredients__measurement_unit',
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
        response = HttpResponse(shopping_itog, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_cart.txt"'
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


# class FollowViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
#     """Вьюсет модели подписки."""

#     serializer_class = FollowSerializer
#     filter_backends = [SearchFilter]
#     search_fields = ('user__username', 'author__username')

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def get_queryset(self):
#         subscriptions = self.request.user.follower.all()
#         return subscriptions

#     def delete(self, request, *args, **kwargs):
#         """Удаление подписки"""
#         author_id = self.kwargs['id']
#         user_id = request.user.id
#         Follow.objects.filter(user_id, author_id).delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

class RecipeNotFoundException(APIException):
    """Исключение для несуществующего рецепта. """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Такого рецепта не нашлось.'
    default_code = 'recipe_not_found'


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
        recipe = get_object_or_404(Recipe, id=recipe_id)
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = FavoriteSerializer()
        return Response(
            serializer.to_representation(instance=recipe),
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, *args, **kwargs):
        """Удаление рецепта
        из списка избранного
        """
        recipe_id = self.kwargs["id"]
        user_id = request.user.id
        Favorite.objects.filter(
            user__id=user_id, recipe__id=recipe_id
        ).delete()
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
        shopping_cart = ShoppingCart(user=request.user, recipe=recipe)
        shopping_cart.save()
        serializer = ShoppingCartSerializer(shopping_cart)
        return Response(
            # serializer.data,
            serializer.to_representation(instance=shopping_cart),
            status=status.HTTP_201_CREATED,
        )

    def delete(self):
        """Удаление рецепта из
        списка покупок
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
        # recipe_id = self.kwargs["id"]
        # user_id = request.user.id
        # ShoppingCart.objects.filter(user__id=user_id,
        #                             recipe__id=recipe_id).delete()
        # return Response(status=status.HTTP_204_NO_CONTENT)
