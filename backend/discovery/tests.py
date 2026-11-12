from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from categories.models import Category
from vendors.models import VendorProfile
from discovery.models import BuyerSignal, SellerLocation


class DiscoveryApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.buyer = User.objects.create_user(username='buyer', password='CampusMarket!2468')
        self.seller_user = User.objects.create_user(username='seller', password='CampusMarket!2468')
        self.vendor = VendorProfile.objects.create(user=self.seller_user, business_name='Nearby Store', slug='nearby-store', phone='08030000000')
        self.location = SellerLocation.objects.create(vendor=self.vendor, latitude=9.203, longitude=12.481, location_label='Near campus', service_radius_km=10)

    def test_nearby_discovery_returns_vendor_with_distance_without_public_coordinates(self):
        response = self.client.get(reverse('nearby-discovery'), {'latitude': 9.203, 'longitude': 12.481, 'radius_km': 5, 'kind': 'vendors'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['vendors']), 1)
        self.assertEqual(response.data['vendors'][0]['distance_km'], 0.0)
        self.assertNotIn('latitude', response.data['vendors'][0])

    def test_seller_can_save_and_update_own_location(self):
        self.client.force_authenticate(user=self.seller_user)
        response = self.client.put(reverse('seller-location'), {'latitude': 9.2, 'longitude': 12.5, 'location_label': 'Main gate', 'service_radius_km': 8}, format='json')
        self.assertEqual(response.status_code, 200)
        self.location.refresh_from_db()
        self.assertEqual(float(self.location.latitude), 9.2)
        self.assertEqual(self.location.service_radius_km, 8)

    def test_buyer_can_create_request_and_only_see_own_requests(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(reverse('buyer-signal-list-create'), {
            'item_name': 'Used laptop', 'category': self.category.id, 'description': 'Core i5, good battery',
            'budget_min': '100000', 'budget_max': '180000', 'location_label': 'MAU campus',
            'radius_km': 5, 'urgency': 'normal', 'expiry_hours': 72,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['item_name'], 'Used laptop')
        self.assertEqual(response.data['status'], 'broadcast')
        self.assertTrue(BuyerSignal.objects.filter(user=self.buyer).exists())
        listing = self.client.get(reverse('buyer-signal-list-create'))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)

    def test_seller_can_see_and_respond_to_active_buyer_request(self):
        signal = BuyerSignal.objects.create(user=self.buyer, item_name='Phone charger', category=self.category, location_label='MAU', expires_at=timezone.now() + timedelta(days=2))
        self.client.force_authenticate(user=self.seller_user)
        listing = self.client.get(reverse('buyer-signal-list-create'))
        self.assertEqual(listing.status_code, 200)
        response = self.client.post(reverse('buyer-signal-respond', args=[signal.id]), {'message': 'I have one available.', 'price': '4500'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['vendor_name'], 'Nearby Store')

    def test_other_buyer_cannot_edit_or_delete_signal(self):
        signal = BuyerSignal.objects.create(user=self.buyer, item_name='Textbook', location_label='MAU', expires_at=timezone.now() + timedelta(days=2))
        other = User.objects.create_user(username='otherbuyer', password='CampusMarket!2468')
        self.client.force_authenticate(user=other)
        patch = self.client.patch(reverse('buyer-signal-detail', args=[signal.id]), {'item_name': 'Changed'}, format='json')
        delete = self.client.delete(reverse('buyer-signal-detail', args=[signal.id]))
        self.assertEqual(patch.status_code, 403)
        self.assertEqual(delete.status_code, 403)
