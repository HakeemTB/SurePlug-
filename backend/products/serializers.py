from rest_framework import serializers

from campuses.serializers import CampusSerializer
from categories.serializers import CategorySerializer
from vendors.serializers import VendorSummarySerializer
from .models import Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductListSerializer(serializers.ModelSerializer):
    vendor = VendorSummarySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    gallery = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'slug', 'name', 'description', 'price', 'currency', 'condition', 'availability', 'is_published', 'featured', 'image', 'contact_phone', 'whatsapp_number', 'external_url', 'price_updated_at', 'vendor', 'category', 'campus', 'gallery']


class ProductDetailSerializer(ProductListSerializer):
    pass
