from rest_framework import serializers
from .models import VendorProfile


class VendorSummarySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    campus_name = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = ['id', 'slug', 'business_name', 'description', 'phone', 'whatsapp', 'website', 'campus_name', 'location_description', 'image', 'username']

    def get_username(self, obj):
        return obj.user.username

    def get_campus_name(self, obj):
        return obj.campus.name if obj.campus else None


class VendorProfileSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    campus_name = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = ['id', 'slug', 'business_name', 'description', 'phone', 'whatsapp', 'website', 'campus_name', 'location_description', 'image', 'operating_hours', 'is_verified', 'is_active', 'username']

    def get_username(self, obj):
        return obj.user.username

    def get_campus_name(self, obj):
        return obj.campus.name if obj.campus else None
