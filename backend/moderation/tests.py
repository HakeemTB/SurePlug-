from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from moderation.models import Report
from products.models import Product
from vendors.models import VendorProfile


class ReportSubmissionTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='reported_vendor', password='CampusMarket!2468')
        vendor = VendorProfile.objects.create(
            user=user,
            business_name='Reported Store',
            slug='reported-store',
            phone='08030000000',
        )
        self.product = Product.objects.create(
            vendor=vendor,
            name='Reported item',
            description='Test listing.',
            price='1000.00',
        )

    def test_report_submission_is_created_pending(self):
        response = self.client.post(reverse('report-create'), {
            'product': self.product.pk,
            'reason': 'misleading_price',
            'message': 'The listed price does not match.',
            'status': 'resolved',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        report = Report.objects.get()
        self.assertEqual(report.status, 'pending')
        self.assertEqual(response.data['report']['status'], 'pending')

    def test_report_must_target_a_product_or_vendor(self):
        response = self.client.post(reverse('report-create'), {
            'reason': 'other',
            'message': 'No target supplied.',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Report.objects.exists())
