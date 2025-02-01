from django.urls import path

from .views import RecipeRedirectView


app_name = 'recipes'


urlpatterns = [
    path('<int:pk>/', RecipeRedirectView.as_view(), name='short-link'),
]
