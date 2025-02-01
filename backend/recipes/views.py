from django.conf import settings
from django.shortcuts import redirect
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class RecipeRedirectView(APIView):
    def get(self, request, *args, **kwargs):
        hostname = request.META.get('HTTP_HOST')
        if not hostname:
            hostname = settings.ALLOWED_HOSTS[0]
        redirect_url = f"http://{hostname}/recipes/{self.kwargs.get('pk')}"
        return redirect(redirect_url)
