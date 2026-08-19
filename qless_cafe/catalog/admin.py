from django.contrib import admin

from .models import Category
from .models import Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "icon", "display_order"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "is_available"]
    list_filter = ["category", "is_available"]
    prepopulated_fields = {"slug": ("name",)}
