from django.core.management.base import BaseCommand, CommandError

from src.shipping.services import is_live_mode, sync_cities_and_warehouses


class Command(BaseCommand):
    help = "Підтягнути всі міста і відділення Нової Пошти в локальний довідник."

    def handle(self, *args, **options):
        if not is_live_mode():
            raise CommandError("NP_API_KEY порожній у контейнері. Перевірте .env і recreate backend.")
        stats = sync_cities_and_warehouses()
        self.stdout.write(
            self.style.SUCCESS(
                f"НП синк: міста {stats['cities']}, відділення {stats['warehouses']}"
            )
        )
