from django.conf import settings
from django.db import models
from django.utils import timezone

from campuses.models import Campus


class VendorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=30)
    whatsapp = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendors')
    location_description = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to='vendors', blank=True, null=True)
    operating_hours = models.CharField(max_length=200, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['business_name']

    def __str__(self):
        return self.business_name


class VendorVerification(models.Model):
    DOCUMENT_CHOICES = [
        ('nin', 'National Identification Number (NIN)'),
        ('voters_card', "Voter's card"),
        ('drivers_license', "Driver's licence"),
        ('passport', 'International passport'),
        ('student_id', 'Institutional/student ID'),
        ('business_document', 'Business registration document'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('rejected', 'Changes required / rejected'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='verification_submissions')
    legal_name = models.CharField(max_length=180)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_CHOICES)
    document_last4 = models.CharField(max_length=4)
    contact_phone = models.CharField(max_length=30)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_vendor_verifications')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def approve(self, reviewer):
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        VendorProfile.objects.filter(pk=self.vendor_id).update(is_verified=True)

    def reject(self, reviewer, notes=''):
        self.status = 'rejected'
        self.admin_notes = notes
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'admin_notes', 'reviewed_by', 'reviewed_at'])
        VendorProfile.objects.filter(pk=self.vendor_id).update(is_verified=False)

    def __str__(self):
        return f'{self.vendor.business_name} verification - {self.status}'
