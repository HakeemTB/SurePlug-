from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from categories.models import Category
from vendors.models import VendorProfile


class SellerLocation(models.Model):
    vendor = models.OneToOneField(VendorProfile, on_delete=models.CASCADE, related_name='geo_location')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_label = models.CharField(max_length=180, blank=True)
    service_radius_km = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(100)])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.vendor.business_name} location'


class BuyerSignal(models.Model):
    URGENCY_CHOICES = [('low', 'Whenever'), ('normal', 'Soon'), ('urgent', 'Urgent')]
    STATUS_CHOICES = [
        ('broadcast', 'Active'), ('paused', 'Paused'), ('connected', 'Connected'),
        ('fulfilled', 'Fulfilled'), ('closed', 'Closed'), ('expired', 'Expired'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_signals')
    item_name = models.CharField(max_length=180)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='buyer_signals')
    description = models.TextField(blank=True, max_length=2000)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    location_label = models.CharField(max_length=180)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(100)])
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='normal')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='broadcast')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['category', 'status']),
        ]

    def save(self, *args, **kwargs):
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError('Minimum budget cannot exceed maximum budget.')
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError('Latitude and longitude must be supplied together.')
        super().save(*args, **kwargs)

    def expire_if_needed(self):
        if self.status == 'broadcast' and self.expires_at <= timezone.now():
            self.status = 'expired'
            self.save(update_fields=['status', 'updated_at'])


class BuyerSignalResponse(models.Model):
    signal = models.ForeignKey(BuyerSignal, on_delete=models.CASCADE, related_name='responses')
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='signal_responses')
    message = models.CharField(max_length=1000)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='signal_responses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['signal', 'vendor'], name='unique_vendor_signal_response')]
