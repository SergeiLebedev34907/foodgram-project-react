from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    COLORS = (
        ("#E26C2D", "#E26C2D"),
        ("#49B64E", "#49B64E"),
        ("#8775D2", "#8775D2"),
    )

    name = models.CharField(
        max_length=200, unique=True, verbose_name="Название"
    )
    color = models.CharField(
        max_length=7, choices=COLORS, unique=True, verbose_name="Цвет в HEX"
    )
    slug = models.SlugField(unique=True, verbose_name="Краткое название")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["id"]

    def __str__(self):
        return self.name


class LowerCaseCharField(models.CharField):
    """
    Определяет поле, которое автоматически преобразует все входные данные в
    нижний регистр и сохраняет.
    """

    def pre_save(self, model_instance, add):
        """
        Преобразует строку в нижний регистр перед сохранением.
        """
        current_value = getattr(model_instance, self.attname)
        setattr(model_instance, self.attname, current_value.lower())
        return getattr(model_instance, self.attname)


class Ingredient(models.Model):
    MEASURMENTS = (
        ("г", "г"),
        ("кг", "кг"),
        ("мл", "мл"),
        ("л", "л"),
        ("ст. л.", "ст. л."),
        ("ч. л.", "ч. л."),
        ("банка", "банка"),
        ("батон", "батон"),
        ("бутылка", "бутылка"),
        ("веточка", "веточка"),
        ("горсть", "горсть"),
        ("долька", "долька"),
        ("звездочка", "звездочка"),
        ("зубчик", "зубчик"),
        ("капля", "капля"),
        ("кусок", "кусок"),
        ("лист", "лист"),
        ("пакет", "пакет"),
        ("пакетик", "пакетик"),
        ("пачка", "пачка"),
        ("пласт", "пласт"),
        ("по вкусу", "по вкусу"),
        ("пучок", "пучок"),
        ("стакан", "стакан"),
        ("стебель", "стебель"),
        ("стручок", "стручок"),
        ("тушка", "тушка"),
        ("упаковка", "упаковка"),
        ("шт.", "шт."),
        ("щепотка", "щепотка"),
    )
    name = LowerCaseCharField(max_length=200, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=20,
        choices=MEASURMENTS,
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique ingredient"
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    tags = models.ManyToManyField(
        Tag, through="TagRecipe", related_name="recipes", verbose_name="Теги"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Картинка",
        blank=True,  # Удалить
        null=True,
    )
    text = models.TextField(
        max_length=400,
        verbose_name="Текстовое описание",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления в минутах"
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-id"]

    def __str__(self):
        return self.name

    def favorite_count(self):
        return self.favorite_recipe.count()


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="tag_recipe",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="tag_recipe",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "tag"], name="unique tag_recipe"
            )
        ]

    def __str__(self):
        return f"{self.tag} {self.recipe}"


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="amount_recipes",
    )
    amount = models.PositiveSmallIntegerField(verbose_name="Количество")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique ingredient_recipe",
            )
        ]

    def __str__(self):
        return f"{self.ingredient} {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_user",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite_recipe",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique favorite"
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart_user",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart_recipe",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique shopping cart"
            )
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique follow"
            )
        ]
