from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .serializers import (
    CustomUserSerializer, UserSetPasswordSerializer, UserReadSerializer,
    TagSerializer, IngredientSerializer, RecipeSerializer,
    RecipeReadSerializer, RecipeFavoriteSerializer,
    ShoppingCartSerializer, AvatarSerializer, UserSubscriptionSerializer)
from core.filters import RecipeFilterSet
from core.permissions import AuthorOrStaffOrReadOnly
from recipes.models import (
    Tag, Ingredient, Recipe, Favorite,
    ShoppingCart, Subscription
)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.AllowAny,)

    @action(
        methods=['get'],
        detail=False
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar'
    )
    def avatar(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if self.request.method == 'PUT':
            serializer = self.get_serializer(request.user, partial=True,
                                             data=request.data)
            serializer.is_valid(raise_exception=True)
            if not serializer.validated_data.get('avatar'):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        if self.request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @ action(
        methods=['post'],
        detail=False,
    )
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        if user.check_password(request.data['current_password']):
            user.set_password(request.data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True
    )
    def subscribe(self, request, id):
        user = self.request.user
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        subscription = get_object_or_404(
            User,
            id=id
        )
        if request.method == 'POST':
            if user == subscription:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if Subscription.objects.filter(
               user=user,
               subscription=subscription
               ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(
                data={'user': user.id, 'subscription': subscription.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if Subscription.objects.filter(
                    user=user,
                    subscription=subscription).exists():
                Subscription.objects.filter(
                    user=user,
                    subscription=subscription
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == 'set_password':
            return UserSetPasswordSerializer
        if self.action in ('retrieve', 'list', 'me'):
            return UserReadSerializer
        if self.action == 'subscribe':
            return UserSubscriptionSerializer
        if self.action == 'subscriptions':
            return UserSubscriptionSerializer
        if self.action == 'avatar':
            return AvatarSerializer
        else:
            return __class__.serializer_class

    def get_permissions(self):
        if self.action == 'set_password' or self.action == 'me':
            self.permission_classes = (permissions.IsAuthenticated, )
        else:
            self.permission_classes = __class__.permission_classes
        return [permission() for permission in self.permission_classes]


class UserSubscriptionsViewSet(mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    serializer_class = UserSubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class TagViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (AuthorOrStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    @action(
        methods=['post', 'delete'],
        detail=True
    )
    def favorite(self, request, *args, **kwargs):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(
                data={'user': user.id, 'recipe': recipe.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            get_object_or_404(
                Favorite,
                user=user,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True
    )
    def shopping_cart(self, request, *args, **kwargs):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(
                data={'user': user.id, 'recipe': recipe.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            get_object_or_404(
                ShoppingCart,
                user=user,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        ingredients = ShoppingCart.objects.filter(
            user=request.user
        ).values(
            'recipe__ingredients__name',
            'recipe__ingredients__measurement_unit',
            'recipe__recipe_ingredient__amount'
        )
        ingredients_dict = {}
        for ingredient in ingredients:
            name_amount = (
                f"{ingredient['recipe__ingredients__name']} "
                f"({ingredient['recipe__ingredients__measurement_unit']})"
            )
            ingredients_dict[name_amount] = (
                ingredients_dict.get(name_amount, 0)
                + ingredient['recipe__recipe_ingredient__amount']
            )
        result = [
            f'\n- {key} - {ingredients_dict[key]}' for key in ingredients_dict
        ]
        result.insert(0, 'Cписок покупок:')
        response = HttpResponse(
            result,
            content_type='text/plain',
        )
        response['Content-Disposition'] = (
            'attachment; filename=shopping_cart'
        )
        return response

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',

    )
    def get_link(self, request, *args, **kwargs):
        return Response(
            {"short-link": reverse('api:short-link',
                                   args=[self.kwargs.get('pk')])}
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        if self.action == 'favorite':
            return RecipeFavoriteSerializer
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        return __class__.serializer_class

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]


class RecipeRedirectView(APIView):

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(
            reverse('api:recipes-detail', args=[self.kwargs.get('pk')])
        )
