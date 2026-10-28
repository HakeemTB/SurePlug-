from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from products.models import Product
from products.serializers import ProductListSerializer
from .models import VendorProfile
from .serializers import VendorProfileSerializer


class VendorListAPIView(ListAPIView):
    queryset = VendorProfile.objects.filter(is_active=True).select_related('user', 'campus')
    serializer_class = VendorProfileSerializer


class VendorDetailAPIView(APIView):
    def get(self, request, slug):
        vendor = get_object_or_404(
            VendorProfile.objects.filter(is_active=True).select_related('user', 'campus'),
            slug=slug,
        )
        products = Product.objects.filter(
            vendor=vendor,
            is_published=True,
        ).select_related('category', 'campus', 'vendor', 'vendor__user', 'vendor__campus')
        serializer = VendorProfileSerializer(vendor)
        product_serializer = ProductListSerializer(products, many=True)
        return Response({
            'vendor': serializer.data,
            'products': product_serializer.data,
        })


class VendorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'vendor_profile', None)
        if not profile:
            return Response({'error': 'This user is not a vendor.'}, status=403)

        products = Product.objects.filter(vendor=profile).select_related('category', 'campus', 'vendor')
        payload = {
            'vendor': VendorProfileSerializer(profile).data,
            'stats': {
                'published': products.filter(is_published=True).count(),
                'unavailable': products.filter(availability='unavailable').count(),
                'drafts': products.filter(is_published=False).count(),
                'total': products.count(),
            },
            'products': ProductListSerializer(products, many=True).data,
        }
        return Response(payload)
