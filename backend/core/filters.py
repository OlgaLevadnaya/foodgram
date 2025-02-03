from django_filters.rest_framework import FilterSet, filters

from recipes.models import Tag, Ingredient, Recipe


class RecipeFilterSet(FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_by_parameter'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_parameter'
    )
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart', 'tags')

    def filter_by_parameter(self, queryset, name, value):
        user = self.request.user
        if not value or not user.is_authenticated:
            return queryset
        if name == 'is_favorited':
            return queryset.filter(favorites__user=user)
        if name == 'is_in_shopping_cart':
            return queryset.filter(shoppingcarts__user=user)
        return queryset


class IngredientFilterSet(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
