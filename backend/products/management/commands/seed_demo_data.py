import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from campuses.models import Campus
from categories.models import Category
from products.models import Product
from vendors.models import VendorProfile


class Command(BaseCommand):
    help = 'Create repeatable local SurePlug demo campuses, categories, vendors, and products.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=os.environ.get('SUREPLUG_DEMO_PASSWORD', 'SurePlugDemo123!'),
            help='Password assigned only when demo users are first created.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        if len(password) < 8:
            self.stderr.write(self.style.ERROR('Demo password must be at least 8 characters long.'))
            return

        campuses = {}
        for name, zone in [
            ('University of Lagos', 'Akoka'),
            ('Yaba College of Technology', 'Yaba'),
        ]:
            campus, _ = Campus.objects.get_or_create(
                name=name,
                defaults={'zone': zone, 'description': f'Local marketplace around {zone}.'},
            )
            campuses[name] = campus

        categories = {}
        for name, description in [
            ('Food & Drinks', 'Meals, snacks, and refreshments.'),
            ('Fashion', 'Clothing, footwear, and accessories.'),
            ('Electronics', 'Phones, computers, and useful gadgets.'),
            ('Books & Study', 'Textbooks, stationery, and study supplies.'),
        ]:
            category, _ = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'description': description},
            )
            categories[name] = category

        vendors = []
        for username, business_name, campus_name, phone, location in [
            ('sureplug_demo_bites', 'Akoka Bites', 'University of Lagos', '08030000001', 'Near the main gate'),
            ('sureplug_demo_style', 'Yaba Style Corner', 'Yaba College of Technology', '08030000002', 'Yaba campus'),
            ('sureplug_demo_tech', 'Campus Tech Desk', 'University of Lagos', '08030000003', 'Student centre'),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.test'},
            )
            if created:
                user.set_password(password)
                user.save(update_fields=['password'])

            vendor_slug = slugify(business_name)
            vendor, _ = VendorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'business_name': business_name,
                    'slug': vendor_slug,
                    'phone': phone,
                    'whatsapp': phone,
                    'campus': campuses[campus_name],
                    'location_description': location,
                    'description': f'{business_name} serves students around {campus_name}.',
                    'is_verified': False,
                    'is_active': True,
                },
            )
            vendors.append(vendor)

        product_rows = [
            (vendors[0], 'Jollof rice lunch pack', 'Food & Drinks', 'University of Lagos', '2500.00', 'Fresh jollof rice with a choice of protein.', 'in_stock'),
            (vendors[0], 'Chilled zobo drink', 'Food & Drinks', 'University of Lagos', '700.00', 'Locally prepared chilled hibiscus drink.', 'limited'),
            (vendors[1], 'Everyday campus backpack', 'Fashion', 'Yaba College of Technology', '12500.00', 'Durable backpack with a padded laptop sleeve.', 'in_stock'),
            (vendors[1], 'Classic low-top sneakers', 'Fashion', 'Yaba College of Technology', '18000.00', 'Comfortable everyday sneakers in several sizes.', 'limited'),
            (vendors[2], 'USB-C fast charger', 'Electronics', 'University of Lagos', '6500.00', 'Compact charger for USB-C phones and tablets.', 'in_stock'),
            (vendors[2], 'Engineering mathematics textbook', 'Books & Study', 'University of Lagos', '9000.00', 'Used textbook in good readable condition.', 'in_stock'),
        ]

        for vendor, name, category_name, campus_name, price, description, availability in product_rows:
            Product.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    'vendor': vendor,
                    'category': categories[category_name],
                    'campus': campuses[campus_name],
                    'name': name,
                    'description': description,
                    'price': price,
                    'currency': 'NGN',
                    'condition': 'used' if 'textbook' in name.lower() else 'new',
                    'availability': availability,
                    'is_published': True,
                    'featured': name == 'Jollof rice lunch pack',
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f'Demo data ready: {len(campuses)} campuses, {len(categories)} categories, '
            f'{len(vendors)} vendors, and {len(product_rows)} products.'
        ))
        self.stdout.write('Demo vendor usernames: sureplug_demo_bites, sureplug_demo_style, sureplug_demo_tech')
        self.stdout.write('The configured demo password is used only for newly created demo users.')
