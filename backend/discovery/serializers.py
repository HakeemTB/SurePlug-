from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal

from categories.models import Category
from vendors.models import VendorProfile
from .models import BuyerSignal, BuyerSignalResponse, SellerLocation


class SellerLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerLocation
        fields = ['latitude', 'longitude', 'location_label', 'service_radius_km']

    def validate(self, attrs):
        lat = attrs.get('latitude', getattr(self.instance, 'latitude', None))
        lng = attrs.get('longitude', getattr(self.instance, 'longitude', None))
        if lat is None or lng is None:
            raise serializers.ValidationError('Both latitude and longitude are required.')
        if not -90 <= float(lat) <= 90 or not -180 <= float(lng) <= 180:
            raise serializers.ValidationError('Coordinates are outside valid ranges.')
        return attrs


class BuyerSignalSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, write_only=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, write_only=True)
    responses = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    response_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = BuyerSignal
        fields = [
            'id', 'item_name', 'category', 'category_name', 'description',
            'budget_min', 'budget_max', 'location_label', 'latitude', 'longitude',
            'radius_km', 'urgency', 'status', 'expires_at', 'created_at',
            'response_count', 'responses',
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def get_responses(self, obj):
        request = self.context.get('request')
        if not request or request.user.id != obj.user_id:
            return []
        return BuyerSignalResponseSerializer(obj.responses.select_related('vendor'), many=True).data

    def validate(self, attrs):
        minimum = attrs.get('budget_min', getattr(self.instance, 'budget_min', None))
        maximum = attrs.get('budget_max', getattr(self.instance, 'budget_max', None))
        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError({'budget_max': 'Maximum budget must be at least the minimum budget.'})
        lat = attrs.get('latitude', getattr(self.instance, 'latitude', None))
        lng = attrs.get('longitude', getattr(self.instance, 'longitude', None))
        if (lat is None) != (lng is None):
            raise serializers.ValidationError('Provide both coordinates or neither.')
        if lat is not None and (not -90 <= float(lat) <= 90 or not -180 <= float(lng) <= 180):
            raise serializers.ValidationError('Coordinates are outside valid ranges.')
        return attrs

    def create(self, validated_data):
        expiry_hours = int(self.context['request'].data.get('expiry_hours', 72))
        if expiry_hours not in (24, 72, 168):
            raise serializers.ValidationError({'expiry_hours': 'Choose 24, 72, or 168 hours.'})
        validated_data['expires_at'] = timezone.now() + timedelta(hours=expiry_hours)
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BuyerSignalResponseSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)

    class Meta:
        model = BuyerSignalResponse
        fields = ['id', 'vendor_name', 'message', 'price', 'product', 'created_at']
        read_only_fields = ['id', 'created_at', 'vendor_name']
