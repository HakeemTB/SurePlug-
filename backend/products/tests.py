from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from campuses.models import Campus
from categories.models import Category
from products.models import Product
from vendors.models import VendorProfile


class ProductApiTests(APITestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name='University of Lagos', zone='Akoka')
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.owner = User.objects.create_user(username='product_owner', password='CampusMarket!2468')
        self.vendor = VendorProfile.objects.create(
            user=self.owner,
            business_name='Owner Store',
            slug='owner-store',
            phone='08030000000',
            campus=self.campus,
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            campus=self.campus,
            name='USB-C charger',
            description='Fast charger for campus.',
            price=Decimal('6500.00'),
        )

    def test_public_discovery_applies_query_and_campus_filters(self):
        response = self.client.get(reverse('product-list'), {
            'q': 'charger',
            'category': 'electronics',
            'campus': 'University of Lagos',
            'min_price': '6000',
            'max_price': '7000',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['slug'] for item in response.data], [self.product.slug])
        self.assertEqual(response.data[0]['campus']['name'], 'University of Lagos')

    def test_invalid_price_range_returns_validation_error(self):
        response = self.client.get(reverse('product-list'), {
            'min_price': '10000',
            'max_price': '5000',
        })

        self.assertEqual(response.status_code, 400)

    def test_public_detail_does_not_expose_drafts(self):
        self.product.is_published = False
        self.product.save()

        response = self.client.get(reverse('product-detail', args=[self.product.slug]))

        self.assertEqual(response.status_code, 404)

    def test_vendor_can_create_product_and_duplicate_names_receive_unique_slugs(self):
        self.client.force_authenticate(user=self.owner)
        payload = {
            'name': 'USB-C charger',
            'description': 'A second listing.',
            'category': 'Electronics',
            'campus': 'University of Lagos',
            'price': '7000.00',
            'condition': 'new',
            'availability': 'in_stock',
        }

        response = self.client.post(reverse('product-create'), payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data['slug'], self.product.slug)
        self.assertTrue(Product.objects.filter(slug=response.data['slug'], vendor=self.vendor).exists())

    def test_vendor_cannot_create_product_with_negative_price(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(reverse('product-create'), {
            'name': 'Invalid listing',
            'description': 'A negative price should be rejected.',
            'category': 'Electronics',
            'campus': 'University of Lagos',
            'price': '-1.00',
            'condition': 'new',
            'availability': 'in_stock',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Product.objects.filter(name='Invalid listing').exists())

    def test_only_product_owner_can_update_or_delete(self):
        other_user = User.objects.create_user(username='other_vendor', password='CampusMarket!2468')
        VendorProfile.objects.create(
            user=other_user,
            business_name='Other Store',
            slug='other-store',
            phone='08030000001',
        )
        self.client.force_authenticate(user=other_user)

        update_response = self.client.patch(
            reverse('product-update', args=[self.product.slug]),
            {'price': '1.00'},
            format='json',
        )
        delete_response = self.client.delete(reverse('product-delete', args=[self.product.slug]))

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('6500.00'))

    def test_product_update_validates_values_and_missing_objects_return_404(self):
        self.client.force_authenticate(user=self.owner)
        invalid_update = self.client.patch(
            reverse('product-update', args=[self.product.slug]),
            {'price': '-1.00'},
            format='json',
        )
        missing_product = self.client.patch(
            reverse('product-update', args=['missing-product']),
            {'price': '1.00'},
            format='json',
        )

        self.assertEqual(invalid_update.status_code, 400)
        self.assertEqual(missing_product.status_code, 404)
