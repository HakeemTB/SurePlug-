from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from vendors.models import VendorProfile, VendorVerification


class VendorVerificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='seller_verify', password='CampusMarket!2468')
        self.vendor = VendorProfile.objects.create(user=self.user, business_name='Verification Store', slug='verification-store', phone='08030000000')
        self.reviewer = User.objects.create_superuser(username='review_admin', email='admin@example.test', password='CampusMarket!2468')

    def payload(self):
        return {'legal_name': 'Ada Seller', 'document_type': 'student_id', 'document_last4': 'A123', 'contact_phone': '08030000000'}

    def test_seller_can_submit_verification_without_full_document_number(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('vendor-verification'), self.payload(), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['submission']['status'], 'pending')
        self.assertEqual(response.data['submission']['document_last4'], 'A123')
        self.assertFalse(self.vendor.is_verified)

    def test_duplicate_pending_verification_is_rejected(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse('vendor-verification'), self.payload(), format='json')
        response = self.client.post(reverse('vendor-verification'), self.payload(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.vendor.verification_submissions.count(), 1)

    def test_verification_status_is_private_to_authenticated_seller(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse('vendor-verification'), self.payload(), format='json')
        response = self.client.get(reverse('vendor-verification'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['submission']['legal_name'], 'Ada Seller')

    def test_admin_approval_marks_vendor_verified(self):
        submission = VendorVerification.objects.create(vendor=self.vendor, **self.payload())
        submission.approve(self.reviewer)
        self.vendor.refresh_from_db()
        submission.refresh_from_db()
        self.assertTrue(self.vendor.is_verified)
        self.assertEqual(submission.status, 'approved')
        self.assertEqual(submission.reviewed_by, self.reviewer)

    def test_rejection_does_not_verify_vendor_and_allows_resubmission(self):
        submission = VendorVerification.objects.create(vendor=self.vendor, **self.payload())
        submission.reject(self.reviewer, 'Please confirm the submitted details.')
        self.vendor.refresh_from_db()
        self.assertFalse(self.vendor.is_verified)
        self.assertEqual(submission.status, 'rejected')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('vendor-verification'), self.payload(), format='json')
        self.assertEqual(response.status_code, 201)
