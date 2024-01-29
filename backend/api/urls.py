from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from api.views import (
    RecipesViewSet,
    IngredientViewSet,
    CustomUserViewSet,
    TagViewSet,
    ShoppingCartViewSet,
    FollowViewSet,
    FavoriteViewSet
)

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register(r'tags', TagViewSet)
router_v1.register(r'recipes', RecipesViewSet)
# router_v1.register(r'subscriptions', FollowViewSet)
router_v1.register(r'ingredients', IngredientViewSet)
# router_v1.register(r'favorite', FavoriteViewSet)
# router_v1.register(r'shopping_cart', ShoppingCartViewSet)

urlpatterns = [
    url(r'^auth/', include('djoser.urls')),
    url(r'^auth/', include('djoser.urls.authtoken')),
    url(r'', include(router_v1.urls)),
    path(
        'recipes/<int:id>/favorite/',
        FavoriteViewSet.as_view({"post": "create", "delete": "delete"}),
        name="favorite",
    ),
    path(
        'users/<int:id>/subscribe/',
        FollowViewSet.as_view({"post": "create", "delete": "delete"}),
        name="subscribe",
    ),
    path(
        'recipes/<int:id>/shopping_cart/',
        ShoppingCartViewSet.as_view({"post": "create", "delete": "delete"}),
        name="shopping_cart",
    ),
]
