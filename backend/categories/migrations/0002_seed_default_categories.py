from django.db import migrations
from django.db.models import Q


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")

    default_categories = [
        {
            "name": "Food & Drinks",
            "slug": "food-drinks",
            "description": "Meals, snacks, beverages, and everyday kitchen essentials.",
        },
        {
            "name": "Clothing & Fashion",
            "slug": "clothing-fashion",
            "description": "Apparel, footwear, and fashion accessories for everyday wear.",
        },
        {
            "name": "Electronics & Gadgets",
            "slug": "electronics-gadgets",
            "description": "Phones, gadgets, devices, and digital accessories.",
        },
        {
            "name": "Books & Stationery",
            "slug": "books-stationery",
            "description": "Books, journals, office supplies, and study essentials.",
        },
        {
            "name": "Beauty & Personal Care",
            "slug": "beauty-personal-care",
            "description": "Skincare, grooming, cosmetics, and personal care products.",
        },
        {
            "name": "Thrift & Vintage",
            "slug": "thrift-vintage",
            "description": "Secondhand, retro, and unique pre-loved finds.",
        },
        {
            "name": "Bags & Accessories",
            "slug": "bags-accessories",
            "description": "Handbags, backpacks, wallets, and everyday carry essentials.",
        },
        {
            "name": "Hostel & Room Essentials",
            "slug": "hostel-room-essentials",
            "description": "Room necessities, hostel supplies, and home basics.",
        },
        {
            "name": "Services",
            "slug": "services",
            "description": "Professional and personal services offered by vendors.",
        },
        {
            "name": "Other",
            "slug": "other",
            "description": "Miscellaneous products and listings that do not fit other categories.",
        },
    ]

    for category in default_categories:
        # Both name and slug are unique, so skip any category that already
        # exists under either one (keeps the migration safe on existing data).
        if Category.objects.filter(
            Q(slug=category["slug"]) | Q(name=category["name"])
        ).exists():
            continue
        Category.objects.create(
            slug=category["slug"],
            name=category["name"],
            description=category["description"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, migrations.RunPython.noop),
    ]
