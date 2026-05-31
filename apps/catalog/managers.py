from django.db import models


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(status='DISCONTINUED')

    def for_listing(self):
        return (self.active()
                .select_related('grade', 'series__timeline')
                .prefetch_related('images'))


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def for_listing(self):
        return self.get_queryset().for_listing()
