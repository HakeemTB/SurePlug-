from django.db import models

from products.models import Product
from vendors.models import VendorProfile


class Report(models.Model):
    REASONS = [
        ('misleading_price', 'Misleading price'),
        ('suspicious_vendor', 'Suspicious vendor'),
        ('incorrect_product_info', 'Incorrect product information'),
        ('inappropriate_content', 'Inappropriate content'),
        ('unavailable_listing', 'Unavailable or misleading listing'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
    ]

    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    vendor = models.ForeignKey(VendorProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    reporter_name = models.CharField(max_length=120, blank=True)
    reporter_email = models.EmailField(blank=True)
    reason = models.CharField(max_length=40, choices=REASONS, default='other')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.reason} | {self.status}'
