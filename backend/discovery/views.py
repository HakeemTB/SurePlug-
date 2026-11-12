from math import asin, cos, radians, sin, sqrt

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product
from products.serializers import ProductListSerializer
from vendors.models import VendorProfile
from vendors.serializers import VendorProfileSerializer
from .models import BuyerSignal, BuyerSignalResponse, SellerLocation
from .serializers import BuyerSignalSerializer, BuyerSignalResponseSerializer, SellerLocationSerializer


def distance_km(lat1, lon1, lat2, lon2):
    earth_radius = 6371.0088
    d_lat, d_lon = radians(float(lat2) - float(lat1)), radians(float(lon2) - float(lon1))
    value = sin(d_lat / 2) ** 2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(d_lon / 2) ** 2
    return 2 * earth_radius * asin(sqrt(value))


class NearbyDiscoveryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = serializers.Serializer(data=request.query_params)
        params.fields['latitude'] = serializers.FloatField(min_value=-90, max_value=90)
        params.fields['longitude'] = serializers.FloatField(min_value=-180, max_value=180)
        params.fields['radius_km'] = serializers.FloatField(min_value=1, max_value=100, default=5, required=False)
        params.fields['kind'] = serializers.ChoiceField(choices=['all', 'products', 'vendors'], default='all', required=False)
        params.is_valid(raise_exception=True)
        lat, lng = params.validated_data['latitude'], params.validated_data['longitude']
        radius, kind = params.validated_data['radius_km'], params.validated_data['kind']
        locations = SellerLocation.objects.select_related('vendor', 'vendor__user', 'vendor__campus').filter(vendor__is_active=True)
        matches = []
        for location in locations:
            distance = distance_km(lat, lng, location.latitude, location.longitude)
            if distance <= radius:
                matches.append((location, round(distance, 1)))
        matches.sort(key=lambda item: item[1])
        vendor_ids = [item[0].vendor_id for item in matches]
        result = {'radius_km': radius, 'vendors': [], 'products': []}
        if kind in ('all', 'vendors'):
            for location, distance in matches:
                vendor_data = VendorProfileSerializer(location.vendor).data
                vendor_data['distance_km'] = distance
                vendor_data['location_label'] = location.location_label or location.vendor.location_description
                result['vendors'].append(vendor_data)
        if kind in ('all', 'products') and vendor_ids:
            products = Product.objects.filter(
                vendor_id__in=vendor_ids, vendor__is_active=True,
                is_published=True, approval_status='approved', availability__in=['in_stock', 'limited'],
            ).select_related('vendor', 'vendor__user', 'vendor__campus', 'category', 'campus')
            distance_by_vendor = {location.vendor_id: distance for location, distance in matches}
            for product in ProductListSerializer(products, many=True).data:
                product['distance_km'] = distance_by_vendor.get(product['vendor']['id'])
                result['products'].append(product)
            result['products'].sort(key=lambda item: item['distance_km'] if item['distance_km'] is not None else 999999)
        return Response(result)


class SellerLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_vendor(self, request):
        vendor = getattr(request.user, 'vendor_profile', None)
        if not vendor or not vendor.is_active:
            return None
        return vendor

    def get(self, request):
        vendor = self.get_vendor(request)
        if not vendor:
            return Response({'error': 'An active seller account is required.'}, status=403)
        location = SellerLocation.objects.filter(vendor=vendor).first()
        if not location:
            return Response({}, status=200)
        return Response(SellerLocationSerializer(location).data)

    def put(self, request):
        vendor = self.get_vendor(request)
        if not vendor:
            return Response({'error': 'An active seller account is required.'}, status=403)
        location = SellerLocation.objects.filter(vendor=vendor).first()
        serializer = SellerLocationSerializer(location, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(vendor=vendor)
        return Response({'message': 'Seller location and service area saved.'})


class BuyerSignalListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        BuyerSignal.objects.filter(status='broadcast', expires_at__lte=timezone.now()).update(status='expired')
        vendor = getattr(request.user, 'vendor_profile', None)
        if vendor and vendor.is_active:
            queryset = BuyerSignal.objects.filter(status='broadcast', expires_at__gt=timezone.now()).select_related('category').annotate(response_count=Count('responses'))
        else:
            queryset = BuyerSignal.objects.filter(user=request.user).select_related('category').annotate(response_count=Count('responses'))
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        if vendor and vendor.is_active:
            if hasattr(vendor, 'geo_location'):
                loc = vendor.geo_location
                eligible = []
                for signal in queryset:
                    if signal.latitude is None:
                        eligible.append(signal.pk)
                    elif distance_km(loc.latitude, loc.longitude, signal.latitude, signal.longitude) <= min(signal.radius_km, loc.service_radius_km):
                        eligible.append(signal.pk)
                queryset = queryset.filter(pk__in=eligible)
            else:
                queryset = queryset.filter(latitude__isnull=True)
        return Response(BuyerSignalSerializer(queryset, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = BuyerSignalSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        signal = serializer.save()
        return Response(BuyerSignalSerializer(signal).data, status=status.HTTP_201_CREATED)


class BuyerSignalDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, signal_id):
        signal = get_object_or_404(BuyerSignal, pk=signal_id)
        if signal.user_id != request.user.id:
            return Response({'error': 'You can only manage your own requests.'}, status=403)
        if signal.status in ('fulfilled', 'closed', 'expired'):
            return Response({'error': 'This request is already closed.'}, status=400)
        serializer = BuyerSignalSerializer(signal, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if request.data.get('status') in ('paused', 'broadcast', 'connected', 'fulfilled', 'closed'):
            signal.status = request.data['status']
            signal.save(update_fields=['status', 'updated_at'])
        return Response(BuyerSignalSerializer(signal, context={'request': request}).data)

    def delete(self, request, signal_id):
        signal = get_object_or_404(BuyerSignal, pk=signal_id)
        if signal.user_id != request.user.id:
            return Response({'error': 'You can only delete your own requests.'}, status=403)
        signal.delete()
        return Response(status=204)


class BuyerSignalResponseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, signal_id):
        vendor = getattr(request.user, 'vendor_profile', None)
        if not vendor or not vendor.is_active:
            return Response({'error': 'An active seller account is required.'}, status=403)
        signal = get_object_or_404(BuyerSignal, pk=signal_id, status='broadcast', expires_at__gt=timezone.now())
        if signal.user_id == request.user.id:
            return Response({'error': 'You cannot respond to your own request.'}, status=400)
        serializer = BuyerSignalResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data.get('product')
        if product and product.vendor_id != vendor.id:
            return Response({'error': 'You can only attach one of your own listings.'}, status=400)
        if BuyerSignalResponse.objects.filter(signal=signal, vendor=vendor).exists():
            return Response({'error': 'You have already responded to this request.'}, status=409)
        response = BuyerSignalResponse.objects.create(signal=signal, vendor=vendor, **serializer.validated_data)
        return Response(BuyerSignalResponseSerializer(response).data, status=201)
