from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes import models
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
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
    id = SerializerMethodField()
    name = SerializerMethodField()
    measurement_unit = SerializerMethodField()

    class Meta:
        model = models.IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


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
    tags = PrimaryKeyRelatedField(queryset=models.Tag.objects.all(), many=True)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self._context).data

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = models.Recipe.objects.create(**validated_data)

        for tag in tags:
            models.TagRecipe.objects.create(tag=tag, recipe=recipe)

        for ingredient in ingredients:
            amount = ingredient.get("amount")
            ingr = ingredient.get("ingredient")
            print(ingr, amount)
            models.IngredientRecipe.objects.create(
                recipe=recipe, ingredient=ingr, amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = super().update(instance, validated_data)

        old_tags = recipe.tags.all()
        # Удаляем ненужные больше теги
        for tag in old_tags:
            if tag not in tags:
                recipe.tag_recipe.filter(tag=tag).delete()

        # Добавляем новые теги
        for tag in tags:
            if tag not in old_tags:
                recipe.tag_recipe.create(tag=tag)
        old_ingredients_amount = recipe.ingredients.all()

        new_ingredients_amounts = []
        for ingredient in ingredients:
            amount = ingredient.get("amount")
            ingr = ingredient.get("ingredient")
            recipe_ingr_am, _ = recipe.ingredients.get_or_create(
                ingredient=ingr, amount=amount
            )
            new_ingredients_amounts.append(recipe_ingr_am)

        for ingredient_amount in old_ingredients_amount:
            if ingredient_amount not in new_ingredients_amounts:
                ingredient_amount.delete()
        return instance


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
