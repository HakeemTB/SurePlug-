from django.db import migrations


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
        Category.objects.get_or_create(
            slug=category["slug"],
            defaults={
                "name": category["name"],
                "description": category["description"],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, migrations.RunPython.noop),
    ]
