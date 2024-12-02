from django_filters.rest_framework import FilterSet, filters

from recipes.models import Tag, Recipe


class RecipeFilterSet(FilterSet):
    is_favorited = filters.BooleanFilter(
        method='filter_by_parameter'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_parameter'
    )
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        to_field_name='id'
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
