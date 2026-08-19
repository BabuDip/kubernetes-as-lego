import uuid

from django.db import models


class Category(models.Model):
    """Top-level grouping for the menu (Coffee, Bakery, ...)."""

    class Tint(models.TextChoices):
        PINE = "pine", "Pine (coffee)"
        CREMA = "crema", "Crema (bakery)"
        GREY = "grey", "Grey (other)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    # Bootstrap Icons class name (e.g. "cup-hot"), used as a fallback visual when a
    # product has no uploaded image. https://icons.getbootstrap.com/
    icon = models.CharField(max_length=50, default="shop")
    # Tinted glyph tile colour — there is no product photography, by design.
    tint = models.CharField(max_length=10, choices=Tint.choices, default=Tint.GREY)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """A single menu item a customer can order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True)
    is_available = models.BooleanField(default=True)
    # Which MODIFIER_GROUPS keys (see modifiers.py) apply, e.g. ["milk", "size"].
    modifier_groups = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__display_order", "name"]

    def __str__(self) -> str:
        return self.name
