"""Data-міграція: група «Менеджери» замість кастомної моделі ролей.

Права уточнюються після відповіді клієнта на 7.3 (docs/Питання_без_відповіді.md) —
поки що повний доступ до commerce/catalog/shipping/content, без auth/accounts.
"""
from django.db import migrations

MANAGED_APP_LABELS = ["catalog", "commerce", "shipping", "content"]


def create_managers_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group, _ = Group.objects.get_or_create(name="Менеджери")
    permissions = Permission.objects.filter(content_type__app_label__in=MANAGED_APP_LABELS)
    group.permissions.set(permissions)


def remove_managers_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Менеджери").delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("catalog", "0001_initial"),
        ("commerce", "0002_initial"),
        ("shipping", "0001_initial"),
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_managers_group, remove_managers_group),
    ]
