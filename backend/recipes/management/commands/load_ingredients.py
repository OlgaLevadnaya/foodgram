import csv
from django.core.management.base import BaseCommand

from foodgram import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов'

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR / 'data/ingredients.csv'
        with open(file_path, 'r', encoding='utf-8') as file:
            for ingredient in csv.reader(file):
                Ingredient.objects.update_or_create(
                    name=ingredient[0],
                    measurement_unit=ingredient[1]
                )
