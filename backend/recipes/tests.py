from django.test import TestCase

from .models import Ingredient

# from users.models import User


class IngredientModelTestCase(TestCase):

    def test_smoke(self):
        Ingredient.objects.create(name='salt', measurement_unit='gr')
