from unittest.mock import patch
from uuid import UUID

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from src.shipping.models import NPCity, NPWarehouse
from src.shipping.services import sync_cities_and_warehouses

CITY_REF = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
WH_REF = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


class SyncNpTests(TestCase):
    @override_settings(NP_API_KEY="")
    def test_without_key_is_noop(self):
        stats = sync_cities_and_warehouses()
        self.assertEqual(stats, {"cities": 0, "warehouses": 0})
        self.assertEqual(NPCity.objects.count(), 0)

    @override_settings(NP_API_KEY="test-key")
    def test_command_requires_key_in_container(self):
        with override_settings(NP_API_KEY=""):
            with self.assertRaises(CommandError):
                call_command("sync_np")

    @override_settings(NP_API_KEY="test-key")
    @patch("src.shipping.services.iter_pages")
    def test_sync_upserts_city_and_warehouse(self, mocked_pages):
        def fake_pages(model, method, extra=None):
            if method == "getCities":
                return [
                    {
                        "Ref": CITY_REF,
                        "Description": "Київ",
                        "AreaDescription": "Київська",
                    }
                ]
            return [
                {
                    "Ref": WH_REF,
                    "CityRef": CITY_REF,
                    "Number": "1",
                    "Description": "Відділення №1",
                }
            ]

        mocked_pages.side_effect = fake_pages
        stats = sync_cities_and_warehouses()
        self.assertEqual(stats["cities"], 1)
        self.assertEqual(stats["warehouses"], 1)
        city = NPCity.objects.get(ref=UUID(CITY_REF))
        self.assertEqual(city.name, "Київ")
        self.assertTrue(city.is_active)
        self.assertIsNotNone(city.synced_at)
        warehouse = NPWarehouse.objects.get(ref=UUID(WH_REF))
        self.assertEqual(warehouse.city_id, city.pk)
        self.assertEqual(warehouse.number, "1")
