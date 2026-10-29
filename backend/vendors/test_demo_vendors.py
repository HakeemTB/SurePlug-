from django.core.management import call_command
from django.test import TestCase

from vendors.models import VendorProfile


class DemoVendorsCommandTests(TestCase):
    def test_creates_five_safe_demo_vendors_only_once(self):
        call_command('seed_demo_vendors')
        call_command('seed_demo_vendors')
        self.assertEqual(VendorProfile.objects.count(), 5)
        for vendor in VendorProfile.objects.select_related('user'):
            self.assertFalse(vendor.user.has_usable_password())
            self.assertFalse(vendor.is_verified)
            self.assertTrue(vendor.is_active)
            self.assertTrue(vendor.business_name.startswith('Demo '))

    def test_demo_vendors_appear_in_the_public_vendor_list(self):
        call_command('seed_demo_vendors')
        response = self.client.get('/api/v1/vendors/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

    def test_remove_deletes_them(self):
        call_command('seed_demo_vendors')
        call_command('seed_demo_vendors', remove=True)
        self.assertEqual(VendorProfile.objects.count(), 0)
