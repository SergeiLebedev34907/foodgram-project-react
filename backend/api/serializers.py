from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes import models
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
    ReadOnlyField,
)

User = get_user_model()


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        if self._context.get("request")._auth:
            user = self._context.get("request").user
            return obj.following.filter(user=user).exists()
        return "false"


class TagSerializer(ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = models.Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ("id", "name", "measurement_unit")


class IngredientReedRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source="ingredient.id")
    name = ReadOnlyField(source="ingredient.name")
    measurement_unit = ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = models.IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientRecipeSerializer(IngredientReedRecipeSerializer):
    id = PrimaryKeyRelatedField(
        queryset=models.Ingredient.objects.all(), source="ingredient"
    )

    def to_representation(self, instance):
        return IngredientReedRecipeSerializer(instance).data


class RecipeReadSerializer(ModelSerializer):
    author = SerializerMethodField(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientRecipeSerializer(many=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = models.Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        if self._context.get("request")._auth:
            user = self._context.get("request").user
            return obj.favorite_recipe.filter(user=user).exists()
        return "false"

    def get_is_in_shopping_cart(self, obj):
        if self._context.get("request")._auth:
            user = self._context.get("request").user
            return obj.shopping_cart_recipe.filter(user=user).exists()
        return "false"

    def get_author(self, obj):
        return UserSerializer(context=self.context).to_representation(
            obj.author
        )


class RecipeSerializer(RecipeReadSerializer):
    tags = PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(),
        many=True
    )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self._context).data

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = models.Recipe.objects.create(**validated_data)

        recipes_tags_list = []
        for tag in tags:
            recipes_tag = models.TagRecipe(tag=tag, recipe=recipe)
            recipes_tags_list.append(recipes_tag)
        recipe.tag_recipe.bulk_create(recipes_tags_list)

        recipes_ingredients_list = []
        for recipes_ingredient in ingredients:
            ingr = recipes_ingredient.get("ingredient")
            amount = recipes_ingredient.get("amount")
            recipes_ingredient = models.IngredientRecipe(
                ingredient=ingr,
                amount=amount,
                recipe=recipe
            )
            recipes_ingredients_list.append(recipes_ingredient)
        recipe.ingredients.bulk_create(recipes_ingredients_list)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = super().update(instance, validated_data)

        old_tags = recipe.tags.all()
        # Удаляем ненужные больше теги
        tags_for_delete = []
        for tag in old_tags:
            if tag not in tags:
                tags_for_delete.append(tag)
        if tags_for_delete:
            recipe.tag_recipe.filter(tag__in=tags_for_delete).delete()

        # Добавляем новые теги
        recipes_tags_for_create = []
        for tag in tags:
            if tag not in old_tags:
                recipes_tag = models.TagRecipe(tag=tag, recipe=recipe)
                recipes_tags_for_create.append(recipes_tag)
        if recipes_tags_for_create:
            recipe.tag_recipe.bulk_create(recipes_tags_for_create)

        old_recipes_ingredients = recipe.ingredients.all()
        recipes_ingredients_for_create = []
        recipes_ingredients_for_update = []
        new_ingredients_list = []
        ingredients_for_delete = []

        for ingredient in ingredients:
            amount = ingredient.get("amount")
            ing = ingredient.get("ingredient")
            recipes_ing = models.IngredientRecipe(
                ingredient=ing,
                amount=amount,
                recipe=recipe
            )
            new_ingredients_list.append(recipes_ing.ingredient)

            qs_old_recipes_ing = old_recipes_ingredients.filter(
                ingredient=ing
            )
            if not qs_old_recipes_ing.exists():
                recipes_ingredients_for_create.append(recipes_ing)
            else:
                old_recipes_ing = qs_old_recipes_ing.get()
                if old_recipes_ing.amount != amount:
                    old_recipes_ing.amount = amount
                    recipes_ingredients_for_update.append(old_recipes_ing)

        if recipes_ingredients_for_create:
            recipe.ingredients.bulk_create(recipes_ingredients_for_create)
        if recipes_ingredients_for_update:
            recipe.ingredients.bulk_update(
                recipes_ingredients_for_update,
                ['amount']
            )

        for recipes_ing in old_recipes_ingredients:
            if recipes_ing.ingredient not in new_ingredients_list:
                ingredients_for_delete.append(recipes_ing.ingredient)
        if ingredients_for_delete:
            recipe.ingredients.filter(
                ingredient__in=ingredients_for_delete
            ).delete()
        return recipe


class FavoriteSerializer(RecipeReadSerializer):
    class Meta:
        model = models.Favorite
        fields = ()


class CutawaySerializer(ModelSerializer):
    class Meta:
        model = models.Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSubscribeSerializer(UserSerializer):
    recipes = CutawaySerializer(many=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()
