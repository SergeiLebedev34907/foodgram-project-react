import tempfile
from datetime import datetime as dt

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes import models
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (
    GenericViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet,
)

from . import serializers
from .filtersets import RecipeFilter
from .pagination import PageNumberLimitPagination

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ("^name",)


class RecipesViewSet(ModelViewSet):
    serializer_class = serializers.RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_classes = PageNumberLimitPagination

    def get_queryset(self):
        queryset = models.Recipe.objects.all()

        query_dct = self.request._request.GET
        if query_dct and self.request._auth:
            favorite_recipe_st = query_dct.get("is_favorited")
            if favorite_recipe_st == "1":
                queryset = queryset.filter(
                    favorite_recipe__user=self.request.user
                )

            is_in_shopping_cart_st = query_dct.get("is_in_shopping_cart")
            if is_in_shopping_cart_st == "1":
                queryset = queryset.filter(
                    shopping_cart_recipe__user=self.request.user
                )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False)
    def download_shopping_cart(self, request):
        user = request.user
        ingredients_amounts = models.IngredientRecipe.objects.filter(
            recipe__shopping_cart_recipe__user=user
        )

        # Суммируем количество ингредиентов
        ingredients_dct = dict()
        for ingredient_amount in ingredients_amounts:
            ingredient = ingredient_amount.ingredient
            amount = ingredient_amount.amount
            if ingredient not in ingredients_dct:
                ingredients_dct[ingredient] = amount
            else:
                ingredients_dct[ingredient] += amount

        filename = "shopping_cart_{0:%S%f}.txt".format(dt.now())
        f = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        open(f.name, "w")
        for ingr_k, ingr_v in ingredients_dct.items():
            name = ingr_k.name
            measurement_unit = ingr_k.measurement_unit
            amount = ingr_v
            st = f"{name} ({measurement_unit}) - {amount}"
            f.write(st + "\n")
        f.close()

        return FileResponse(
            open(f.name, "rb"), as_attachment=True, filename=filename
        )


class CreateViewSet(CreateModelMixin, GenericViewSet):
    def get_serializer(self):
        pass

    def get_queryset(self):
        pass


class FavoriteViewSet(CreateViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            models.Recipe, id=self.kwargs.get("recipe_id")
        )
        models.Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        serializer = serializers.CutawaySerializer(recipe)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            models.Recipe, id=self.kwargs.get("recipe_id")
        )
        instance = get_object_or_404(
            models.Favorite,
            user=request.user,
            recipe=recipe,
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(CreateViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            models.Recipe, id=self.kwargs.get("recipe_id")
        )
        models.ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        serializer = serializers.CutawaySerializer(recipe)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            models.Recipe, id=self.kwargs.get("recipe_id")
        )
        instance = get_object_or_404(
            models.ShoppingCart,
            user=request.user,
            recipe=recipe,
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(CreateViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get("user_id"))
        models.Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
        serializer = serializers.UserSubscribeSerializer(
            author,
            context=self.get_serializer_context(),  # get_renderer_context()
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def delete(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get("user_id"))
        instance = get_object_or_404(
            models.Follow,
            user=request.user,
            author=author,
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsViewSet(ListModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserSubscribeSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(following__user=user)
