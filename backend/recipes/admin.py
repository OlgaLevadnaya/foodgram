from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     ShoppingCart, Subscription, Tag)


@admin.register(Tag, Ingredient, Recipe, RecipeTag, RecipeIngredient, Subscription, ShoppingCart, Favorite)
class FoodgramAdmin(admin.ModelAdmin):
    pass
