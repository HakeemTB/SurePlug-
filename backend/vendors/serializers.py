from rest_framework import serializers
from .models import VendorProfile, VendorVerification


class VendorSummarySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    campus_name = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = ['id', 'slug', 'business_name', 'description', 'phone', 'whatsapp', 'website', 'campus_name', 'location_description', 'image', 'username', 'is_verified']

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


class VendorVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorVerification
        fields = ['id', 'legal_name', 'document_type', 'document_last4', 'contact_phone', 'status', 'admin_notes', 'submitted_at', 'reviewed_at']
        read_only_fields = ['id', 'status', 'admin_notes', 'submitted_at', 'reviewed_at']

    def validate_document_last4(self, value):
        value = value.strip()
        if len(value) != 4 or not value.isalnum():
            raise serializers.ValidationError('Enter only the final four letters or digits of the document reference.')
        return value

    def validate(self, attrs):
        vendor = self.context['vendor']
        if vendor.is_verified:
            raise serializers.ValidationError('This seller is already verified.')
        if vendor.verification_submissions.filter(status='pending').exists():
            raise serializers.ValidationError('A verification submission is already awaiting review.')
        return attrs
