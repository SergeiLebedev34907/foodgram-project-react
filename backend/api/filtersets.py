from django_filters import FilterSet, AllValuesMultipleFilter, CharFilter
from recipes import models


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name="tags__slug")
    is_favorited = CharFilter(method='filter_is_favorited')
    is_in_shopping_cart = CharFilter(method='filter_is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value == "1":
            queryset = queryset.filter(
                favorite_recipe__user=user
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value == "1":
            queryset = queryset.filter(
                shopping_cart_recipe__user=user
            )
        return queryset

    class Meta:
        model = models.Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")
