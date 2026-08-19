from django.core.management.base import BaseCommand
from django.db import transaction

from qless_cafe.catalog.models import Category
from qless_cafe.catalog.models import Product
from qless_cafe.identity.models import User

CATEGORIES = [
    {
        "name": "Coffee",
        "slug": "coffee",
        "icon": "cup-hot-fill",
        "tint": "pine",
        "display_order": 1,
    },
    {
        "name": "Bakery",
        "slug": "bakery",
        "icon": "cookie",
        "tint": "crema",
        "display_order": 2,
    },
    {
        "name": "Other",
        "slug": "other",
        "icon": "cup-straw",
        "tint": "grey",
        "display_order": 3,
    },
]

PRODUCTS = [
    (
        "coffee",
        "Flat White",
        "Espresso with steamed milk and a thin layer of microfoam.",
        "4.50",
        ["milk", "size", "shot"],
    ),
    (
        "coffee",
        "Long Black",
        "Espresso shots topped with hot water.",
        "4.00",
        ["size", "shot"],
    ),
    (
        "coffee",
        "Cappuccino",
        "Espresso, steamed milk, and a deep layer of foam.",
        "4.50",
        ["milk", "size", "shot"],
    ),
    (
        "coffee",
        "Iced Latte",
        "Espresso, milk, and ice.",
        "5.00",
        ["milk", "size", "shot"],
    ),
    (
        "bakery",
        "Croissant",
        "Buttery, flaky, classic French pastry.",
        "4.20",
        ["heat"],
    ),
    (
        "bakery",
        "Banana Bread",
        "Moist banana bread slice.",
        "4.80",
        ["heat"],
    ),
    (
        "bakery",
        "Blueberry Muffin",
        "Freshly baked with real blueberries.",
        "4.60",
        [],
    ),
    (
        "bakery",
        "Almond Biscotti",
        "Twice-baked Italian almond biscuit.",
        "3.50",
        [],
    ),
    (
        "other",
        "Hot Chocolate",
        "Rich hot chocolate topped with cream.",
        "4.80",
        ["milk", "size"],
    ),
    (
        "other",
        "Chai Latte",
        "Spiced black tea with steamed milk.",
        "4.70",
        ["milk", "size"],
    ),
    (
        "other",
        "Fresh Orange Juice",
        "Cold-pressed orange juice.",
        "5.50",
        [],
    ),
]


class Command(BaseCommand):
    help = (
        "Seed demo categories, products, and a manager/customer user for local demos."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for data in CATEGORIES:
            category, _created = Category.objects.update_or_create(
                slug=data["slug"],
                defaults=data,
            )
            categories[data["slug"]] = category

        for slug, name, description, price, modifier_groups in PRODUCTS:
            Product.objects.update_or_create(
                slug=name.lower().replace(" ", "-"),
                defaults={
                    "category": categories[slug],
                    "name": name,
                    "description": description,
                    "price": price,
                    "is_available": True,
                    "modifier_groups": modifier_groups,
                },
            )

        manager, created = User.objects.get_or_create(
            email="manager@qless.cafe",
            defaults={"name": "Cafe Manager", "is_staff": True},
        )
        if created:
            manager.set_password("Manager-Pass-123!")
            manager.save()

        customer, created = User.objects.get_or_create(
            email="customer@qless.cafe",
            defaults={"name": "Demo Customer"},
        )
        if created:
            customer.set_password("Customer-Pass-123!")
            customer.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(CATEGORIES)} categories, {len(PRODUCTS)} products. "
                "Manager login: manager@qless.cafe / Manager-Pass-123! "
                "Customer login: customer@qless.cafe / Customer-Pass-123!",
            ),
        )
