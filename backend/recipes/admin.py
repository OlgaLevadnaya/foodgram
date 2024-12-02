from django.contrib import admin

from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeTag,
    RecipeIngredient,
    Subscription,
    ShoppingCart,
    Favorite
)


@admin.register(Tag, Ingredient, Recipe, RecipeTag, RecipeIngredient, Subscription, ShoppingCart, Favorite)
class FoodgramAdmin(admin.ModelAdmin):
    pass
