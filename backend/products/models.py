from decimal import Decimal

from django.db import models
from django.template.defaultfilters import slugify

from campuses.models import Campus
from categories.models import Category
from vendors.models import VendorProfile


class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ('in_stock', 'In stock'),
        ('limited', 'Limited stock'),
        ('out_of_stock', 'Out of stock'),
        ('unavailable', 'Unavailable'),
    ]
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('thrift', 'Thrift'),
    ]
    APPROVAL_CHOICES = [
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('rejected', 'Changes required / rejected'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='NGN')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='in_stock')
    is_published = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=12, choices=APPROVAL_CHOICES, default='pending')
    moderation_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_sureplug_products')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products', blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    external_url = models.URLField(blank=True)
    price_updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'product'
            self.slug = base_slug
            suffix = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base_slug}-{suffix}'
                suffix += 1
        super().save(*args, **kwargs)

    def approve(self, reviewer):
        from django.utils import timezone
        if not self.vendor.is_verified:
            raise ValueError('Verify the seller before approving this listing.')
        self.approval_status = 'approved'
        self.is_published = True
        self.moderation_note = ''
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['approval_status', 'is_published', 'moderation_note', 'reviewed_by', 'reviewed_at', 'updated_at'])

    def reject(self, reviewer, note=''):
        from django.utils import timezone
        self.approval_status = 'rejected'
        self.is_published = False
        self.moderation_note = note
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['approval_status', 'is_published', 'moderation_note', 'reviewed_by', 'reviewed_at', 'updated_at'])

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='products/gallery')
    created_at = models.DateTimeField(auto_now_add=True)
