from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from vendors.models import VendorProfile

# Clearly labelled demo storefronts so students are never misled.
# They are not verified, have no usable password (nobody can sign in as them),
# and use a placeholder phone number that cannot reach a real person.
PLACEHOLDER_PHONE = '00000000001'
DEMO_NOTE = 'Demo storefront for testing SurePlug.'

DEMO_VENDORS = [
    ('demo_vendor_bites', 'Demo Campus Bites', 'demo-campus-bites',
     f'Meals, snacks and chilled drinks. {DEMO_NOTE}', 'Near the main gate', '8am to 6pm, Monday to Saturday'),
    ('demo_vendor_thrift', 'Demo Thrift & Style', 'demo-thrift-and-style',
     f'Clothes, shoes and accessories. {DEMO_NOTE}', 'Student centre', '10am to 7pm, every day'),
    ('demo_vendor_gadgets', 'Demo Gadget Hub', 'demo-gadget-hub',
     f'Phone accessories, chargers and small electronics. {DEMO_NOTE}', 'Faculty walkway', '9am to 6pm, Monday to Saturday'),
    ('demo_vendor_books', 'Demo Book Nook', 'demo-book-nook',
     f'Textbooks, stationery and printing. {DEMO_NOTE}', 'Beside the library', '8am to 5pm, Monday to Friday'),
    ('demo_vendor_essentials', 'Demo Room Essentials', 'demo-room-essentials',
     f'Bedding, kitchenware and hostel basics. {DEMO_NOTE}', 'Hostel area', '9am to 7pm, every day'),
]


class Command(BaseCommand):
    help = 'Create 5 clearly labelled demo vendors (safe to run repeatedly). Use --remove to delete them.'

    def add_arguments(self, parser):
        parser.add_argument('--remove', action='store_true', help='Delete the demo vendors and their accounts.')

    @transaction.atomic
    def handle(self, *args, **options):
        usernames = [row[0] for row in DEMO_VENDORS]
        if options['remove']:
            User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.SUCCESS('Removed the demo vendors.'))
            return

        created = 0
        for username, name, slug, description, location, hours in DEMO_VENDORS:
            user, user_created = User.objects.get_or_create(username=username)
            if user_created:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            _, vendor_created = VendorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': name, 'slug': slug, 'description': description,
                    'phone': PLACEHOLDER_PHONE, 'location_description': location,
                    'operating_hours': hours, 'is_verified': False, 'is_active': True,
                },
            )
            created += int(vendor_created)
        self.stdout.write(self.style.SUCCESS(f'Demo vendors ready ({created} new, {len(DEMO_VENDORS) - created} already existed).'))
