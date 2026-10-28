from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from vendors.models import VendorProfile


class VendorAuthenticationTests(APITestCase):
    def test_register_creates_vendor_and_authenticates_session(self):
        response = self.client.post(reverse('register-vendor'), {
            'username': 'new_vendor',
            'email': 'vendor@example.test',
            'password': 'CampusMarket!2468',
            'business_name': 'Akoka Finds',
            'phone': '08030000000',
            'campus': 'University of Lagos',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='new_vendor').exists())
        self.assertEqual(VendorProfile.objects.get(user__username='new_vendor').business_name, 'Akoka Finds')
        self.assertEqual(self.client.get(reverse('vendor-dashboard')).status_code, 200)

    def test_registration_rejects_duplicate_username_and_weak_password(self):
        User.objects.create_user(username='existing_vendor', password='OriginalPass!2468')

        duplicate = self.client.post(reverse('register-vendor'), {
            'username': 'existing_vendor',
            'password': 'CampusMarket!2468',
            'business_name': 'Duplicate Store',
        }, format='json')
        weak_password = self.client.post(reverse('register-vendor'), {
            'username': 'another_vendor',
            'password': '12345678',
            'business_name': 'Another Store',
        }, format='json')

        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(weak_password.status_code, 400)
        self.assertFalse(User.objects.filter(username='another_vendor').exists())

    def test_login_and_logout_update_session(self):
        user = User.objects.create_user(username='login_vendor', password='CampusMarket!2468')
        VendorProfile.objects.create(
            user=user,
            business_name='Login Store',
            slug='login-store',
            phone='08030000000',
        )

        login_response = self.client.post(reverse('login-user'), {
            'username': 'login_vendor',
            'password': 'CampusMarket!2468',
        }, format='json')
        dashboard_response = self.client.get(reverse('vendor-dashboard'))
        logout_response = self.client.post(reverse('logout-user'), {}, format='json')
        logged_out_dashboard = self.client.get(reverse('vendor-dashboard'))

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.data['is_vendor'])
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(logout_response.status_code, 200)
        self.assertNotEqual(logged_out_dashboard.status_code, 200)

    def test_login_and_registration_require_csrf_cookie(self):
        user = User.objects.create_user(username='csrf_vendor', password='CampusMarket!2468')
        client = APIClient(enforce_csrf_checks=True)

        rejected = client.post(reverse('login-user'), {
            'username': user.username,
            'password': 'CampusMarket!2468',
        }, format='json')
        self.assertEqual(rejected.status_code, 403)

        csrf_response = client.get(reverse('csrf-cookie'))
        self.assertEqual(csrf_response.status_code, 200)
        csrf_token = client.cookies['csrftoken'].value
        accepted = client.post(
            reverse('login-user'),
            {'username': user.username, 'password': 'CampusMarket!2468'},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(accepted.status_code, 200)

        client.logout()
        rejected_registration = client.post(reverse('register-vendor'), {
            'username': 'csrf_registration',
            'password': 'CampusMarket!2468',
            'business_name': 'CSRF Store',
        }, format='json')
        self.assertEqual(rejected_registration.status_code, 403)
