from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

router_v1 = DefaultRouter()

router_v1.register(r"tags", views.TagViewSet, basename="tags")
router_v1.register(
    r"ingredients", views.IngredientsViewSet, basename="ingredients"
)
router_v1.register(r"recipes", views.RecipesViewSet, basename="recipes")
router_v1.register(
    r"recipes/(?P<recipe_id>\d+)/favorite",
    views.FavoriteViewSet,
    basename="favorite",
)
router_v1.register(
    r"recipes/(?P<recipe_id>\d+)/shopping_cart",
    views.ShoppingCartViewSet,
    basename="shopping_cart",
)
router_v1.register(
    r"users/(?P<user_id>\d+)/subscribe", views.FollowViewSet, basename="follow"
)
router_v1.register(
    r"users/subscriptions", views.SubscriptionsViewSet, basename="follow"
)

urlpatterns = [
    path("", include(router_v1.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
