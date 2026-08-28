from django.db import models


class TimeStampedModel(models.Model):
    """Спільні часові поля — успадковують усі сутності tables.md."""

    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        abstract = True


class SeoFieldsMixin(models.Model):
    """SEO override на сутності (ecommerce_db_schema_skill, + seo_h1 понад канон — ТЗ §2.5)."""

    seo_title = models.CharField("SEO title", max_length=512, null=True, blank=True)
    seo_description = models.TextField("SEO description", null=True, blank=True)
    seo_h1 = models.CharField("SEO H1", max_length=255, null=True, blank=True)
    seo_keywords = models.CharField("SEO keywords", max_length=512, null=True, blank=True)

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """Базовий клас для CMS page-singletons (600i2) — рівно один рядок, pk=1."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton не видаляється

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
