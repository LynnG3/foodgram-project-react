from django.conf.urls import url
from django.urls import include, path
from rest_framework import routers

from api.views import (CustomUserViewSet, FavoriteViewSet, IngredientViewSet,
                       RecipeViewSet, ShoppingCartViewSet, TagViewSet)

router_v1 = routers.DefaultRouter()
router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register(r'tags', TagViewSet)
router_v1.register(r'ingredients', IngredientViewSet)
router_v1.register(r'recipes', RecipeViewSet)
router_v1.register(r'subscriptions', CustomUserViewSet,
                   basename='subscriptions')


urlpatterns = [
    url(r'^auth/', include('djoser.urls')),
    url(r'^auth/', include('djoser.urls.authtoken')),
    url(r'', include(router_v1.urls)),
    path(
        'recipes/<int:id>/favorite/',
        FavoriteViewSet.as_view({'post': 'create', 'delete': 'delete'}),
        name='favorite',
    ),
    path(
        'recipes/<int:id>/shopping_cart/',
        ShoppingCartViewSet.as_view({'post': 'create', 'delete': 'delete'}),
        name='shopping_cart',
    ),
]
