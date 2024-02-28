"""
Models used only by test framework.
"""

from typing import Any

from django.db import models, transaction

from animal3.django import unique_slug
from animal3.utils.text import currency

from ..models import BaseModel, OrderableModel, SingletonModel


class SlugOnly(models.Model):
    slug = models.SlugField(unique=True)


class SimpleModel(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.title


class SingletonSample(SingletonModel):
    price = models.DecimalField(default='9.99', decimal_places=2, max_digits=9)

    def __str__(self) -> str:
        return currency(self.price)


class DatedModel(models.Model):
    """
    Sample model for date handling.
    """
    name = models.CharField(max_length=255)
    date = models.DateTimeField(blank=True, null=True)
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)


class TestModel(OrderableModel):
    """
    Concrete model only instantiated by test framework.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(
        blank=True, null=True,
        decimal_places=2,
        max_digits=9)
    description = models.TextField(blank=True)

    @transaction.atomic
    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = unique_slug(TestModel.objects.all(), self.name)
        super().save(*args, **kwargs)
