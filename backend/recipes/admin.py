from django.contrib import admin
from import_export.admin import ImportMixin

from .models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    verbose_name = "Ингредиент"
    verbose_name_plural = "Ингредиенты"
    extra = 0


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    verbose_name = "Тег"
    verbose_name_plural = "Теги"
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        IngredientRecipeInline,
        TagRecipeInline,
    ]
    list_display = ("name", "author")
    search_fields = ("name",)
    list_filter = ("name", "author", "tags")
    readonly_fields = ("favorite_count",)


class IngredientAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("name",)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
