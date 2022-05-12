from django_filters import FilterSet, AllValuesMultipleFilter
from recipes import models


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name="tags__slug")

    class Meta:
        model = models.Recipe
        fields = ["author", "tags"]
