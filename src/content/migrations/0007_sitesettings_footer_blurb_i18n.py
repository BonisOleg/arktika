from django.db import migrations

UK = "Роздрібний інтернет-магазин рибної продукції власного виробництва. Доставка по Україні."
RU = "Розничный интернет-магазин рыбной продукции собственного производства. Доставка по Украине."


def seed_footer_blurb(apps, schema_editor):
    SiteSettings = apps.get_model("content", "SiteSettings")
    obj, _ = SiteSettings.objects.get_or_create(pk=1)
    obj.footer_blurb = UK
    obj.footer_blurb_uk = UK
    obj.footer_blurb_ru = RU
    obj.save(update_fields=["footer_blurb", "footer_blurb_uk", "footer_blurb_ru"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0006_sitesettings_footer_blurb"),
    ]

    operations = [
        migrations.RunPython(seed_footer_blurb, noop),
    ]
