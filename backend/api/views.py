from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from django.conf import settings

from core.filters import RecipeFilterSet, IngredientFilterSet
from core.permissions import AuthorOrStaffOrReadOnly
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            Subscription, Tag)
from .serializers import (AvatarSerializer, CustomUserSerializer,
                          IngredientSerializer, RecipeFavoriteSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserReadSerializer, UserSetPasswordSerializer,
                          UserSubscriptionSerializer)


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
        url_path='me/avatar',
        permission_classes=permissions.IsAuthenticated
    )
    def avatar(self, request):
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
        if user.check_password(
            serializer.validated_data.get('current_password')
        ):
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=permissions.IsAuthenticated
    )
    def subscribe(self, request, id):
        user = self.request.user
        subscription = get_object_or_404(
            User,
            id=id
        )
        subscription_object = Subscription.objects.filter(
            user=user,
            subscription=subscription
        )
        if request.method == 'POST':
            if user == subscription:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if subscription_object.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(
                data={'user': user.id, 'subscription': subscription.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if subscription_object.exists():
            subscription_object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
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
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (AuthorOrStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    def favorite_or_shopping_cart(self, request, action_type, *args, **kwargs):
        if action_type == 'favorite':
            model_name = Favorite
        else:
            model_name = ShoppingCart

        user = self.request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        model_object = model_name.objects.filter(
            user=user,
            recipe=recipe
        )

        if request.method == 'POST':
            if model_object.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(
                data={'user': user.id, 'recipe': recipe.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if not model_object.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        get_object_or_404(
            model_name,
            user=user,
            recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True
    )
    def favorite(self, request, *args, **kwargs):
        return self.favorite_or_shopping_cart(
            request, 'favorite', args, kwargs
        )

    @action(
        methods=['post', 'delete'],
        detail=True
    )
    def shopping_cart(self, request, *args, **kwargs):
        return self.favorite_or_shopping_cart(
            request, 'shopping_cart', args, kwargs
        )

    @action(
        methods=['get'],
        detail=False
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        ingredients = ShoppingCart.objects.filter(
            user=request.user
        ).values(
            'recipe__ingredients__name',
            'recipe__ingredients__measurement_unit'
        ).annotate(
            total_amount=Sum('recipe__recipe_ingredients__amount')
        ).order_by('recipe__ingredients__name')

        result = [
            (
                f"\n- {ingredient['recipe__ingredients__name']} - "
                f"{ingredient['total_amount']}"
                f"{ingredient['recipe__ingredients__measurement_unit']}"
            ) for ingredient in ingredients
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
        hostname = request.META.get('HTTP_HOST')
        if not hostname:
            hostname = settings.ALLOWED_HOSTS[0]

        relative_url = reverse('recipes:short-link',
                               args=[self.kwargs.get('pk')])

        short_link = request.build_absolute_uri(relative_url)

        # relative_url = reverse('api:recipes-detail',
        #                       args=[self.kwargs.get('pk')])
        # redirect_url = request.build_absolute_uri(relative_url)

        # (
        #    f"http://{hostname}"
        #    f"{reverse('api:short-link', args=[self.kwargs.get('pk')])}"
        # )
        return Response(
            {'short-link': short_link}
        )

        # return Response(
        #    {'short-link': redirect_url}
        # )

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


# class RecipeRedirectView(APIView):
#    def get(self, request, *args, **kwargs):
#        hostname = request.META.get('HTTP_HOST')
#        if not hostname:
#            hostname = settings.ALLOWED_HOSTS[0]
#        redirect_url = f"http://{hostname}/recipes/{self.kwargs.get('pk')}"
#        return redirect(redirect_url)


class RecipeRedirectView(APIView):
    def get(self, request, *args, **kwargs):
        print(self.kwargs)
        print(request)
        relative_url = reverse('api:recipes-detail',
                               args=[self.kwargs.get('pk')])
        redirect_url = request.build_absolute_uri(relative_url)
        # redirect_url = f"http://{hostname}/recipes/{self.kwargs.get('pk')}"
        return redirect(redirect_url)
