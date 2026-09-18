from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_productweightoption_approx_unit_weight"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="JPEG/PNG/WebP/GIF → WebP, до 500 Кб.",
                null=True,
                upload_to="categories/",
                verbose_name="Зображення",
            ),
        ),
        migrations.AlterField(
            model_name="productimage",
            name="image",
            field=models.ImageField(
                help_text="JPEG/PNG/WebP/GIF → WebP, до 500 Кб.",
                upload_to="products/",
                verbose_name="Зображення",
            ),
        ),
    ]
