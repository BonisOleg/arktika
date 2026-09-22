from uuid import uuid4

from django.test import TestCase

from src.shipping.models import NPCity
from src.shipping.services import get_cities


def _city(name: str, area: str = "Київська") -> NPCity:
    return NPCity.objects.create(ref=uuid4(), name=name, area=area, is_active=True)


class CitySearchTests(TestCase):
    def test_empty_or_one_char_is_empty(self):
        _city("Авангард", "Одеська")
        _city("Євгенівка", "Миколаївська")
        self.assertEqual(list(get_cities("")), [])
        self.assertEqual(list(get_cities("к")), [])

    def test_kyiv_ranks_above_oblast_villages(self):
        kyiv = _city("Київ", "Київська")
        for index in range(25):
            _city(f"Андріївка {index} (Київська обл.)", "Київська")
        ranked = list(get_cities("київ"))
        self.assertTrue(ranked)
        self.assertEqual(ranked[0].pk, kyiv.pk)
        self.assertLessEqual(len(ranked), 20)
        self.assertIn(kyiv, ranked)
