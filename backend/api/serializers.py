import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from core.constants import UsersConstants
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Subscription, Tag)


User = get_user_model()

user_constants = UsersConstants()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        if self.context.get('request'):
            user = self.context.get('request').user
            if user.is_authenticated:
                return Subscription.objects.filter(
                    user=user,
                    subscription=obj
                ).exists()
        return False


class UserSetPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        max_length=user_constants.CUSTOMUSER_PASSWORD_LENGTH
    )
    current_password = serializers.CharField(
        max_length=user_constants.CUSTOMUSER_PASSWORD_LENGTH
    )

    class Meta:
        model = User
        fields = ('new_password', 'current_password')


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientCreateRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientReadRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserReadSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientReadRecipeSerializer(
        many=True, source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        if self.context.get('request'):
            user = self.context.get('request').user
            if user.is_authenticated:
                return Favorite.objects.filter(
                    user=user,
                    recipe=obj
                ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context.get('request'):
            user = self.context.get('request').user
            if user.is_authenticated:
                return ShoppingCart.objects.filter(
                    user=user,
                    recipe=obj
                ).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = IngredientCreateRecipeSerializer(
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    def create(self, validated_data):

        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            ** validated_data)
        for tag in tags:
            RecipeTag.objects.create(
                recipe=recipe,
                tag=tag)
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(id=ingredient['id'])
            current_amount = ingredient['amount']
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=current_amount
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        for tag in tags:
            RecipeTag.objects.create(
                recipe=instance,
                tag=tag)
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(id=ingredient['id'])
            current_amount = ingredient['amount']
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=current_ingredient,
                amount=current_amount
            )
        return instance

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not tags:
            raise serializers.ValidationError(
                'Не заполнены теги!'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Не заполнены ингредиенты!'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Повторяющиеся теги!'
            )

        if len(ingredients) != len(
            set(
                ingredient['id'] for ingredient in ingredients
            )
        ):
            raise serializers.ValidationError(
                'Повторяющиеся ингредиенты!'
            )
        if any(ingredient['amount'] < 1 for ingredient in ingredients):
            raise serializers.ValidationError(
                'Некорректное количество ингредиента!'
            )

        if not all(
            Ingredient.objects.filter(
                id=ingredient['id']
            ).exists() for ingredient in ingredients
        ):
            raise serializers.ValidationError(
                'Рецепт с несуществующим ингредиентом!'
            )
        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data

    class Meta:
        model = Recipe
        fields = '__all__'


class FavoriteReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'

    def to_representation(self, instance):
        return FavoriteReadSerializer(instance.recipe).data


class ShoppingCartReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def to_representation(self, instance):
        return ShoppingCartReadSerializer(instance.recipe).data


class UserSubscriptionReadSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        fields = UserReadSerializer.Meta.fields + ('recipes',
                                                   'recipes_count',
                                                   )

    def get_recipes(self, obj):
        recipes = Recipe.objects.values(
            'id', 'name', 'image', 'cooking_time'
        ).filter(author=obj)

        try:
            recipes_limit = self.context.get(
                'request').query_params.get('recipes_limit')
            return recipes[:int(recipes_limit)]
        except:
            return recipes

    def get_recipes_count(self, obj):
        return self.get_recipes(obj).count()


class UserSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = '__all__'

    def to_representation(self, instance):
        return UserSubscriptionReadSerializer(
            instance.subscription,
            context={'request': self.context.get('request')}).data
