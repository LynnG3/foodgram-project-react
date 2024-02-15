import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

DICT_MODELS_RECIPES = {
    Ingredient: os.path.join(settings.STATICFILES_DIRS[0], 'ingredients.csv'),
    Tag: os.path.join(settings.STATICFILES_DIRS[0], 'tags.csv'),
}


class Command(BaseCommand):
    help = 'Заполняет базу данных данными из CSV-файлов'

    def handle(self, *args, **options):
        for key, value in DICT_MODELS_RECIPES.items():
            csv_file = value

            try:
                model = key
            except NameError:
                self.stdout.write(self.style.ERROR('Модель не найдена'))
                return

            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                model.objects.bulk_create(model(**row) for row in reader)

            self.stdout.write(self.style.SUCCESS(
                f'Данные из {csv_file} успешно загружены в базу данных'
            ))

        self.stdout.write(self.style.SUCCESS(
            'Все данные успешно загружены в базу данных!'
        ))
