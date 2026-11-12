from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from products.models import Product
from products.serializers import ProductListSerializer
from .models import VendorProfile
from .serializers import VendorProfileSerializer, VendorVerificationSerializer


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
            vendor=vendor, is_published=True, approval_status='approved',
        ).select_related('category', 'campus', 'vendor', 'vendor__user', 'vendor__campus')
        serializer = VendorProfileSerializer(vendor)
        product_serializer = ProductListSerializer(products, many=True)
        return Response({'vendor': serializer.data, 'products': product_serializer.data})


class VendorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'vendor_profile', None)
        if not profile:
            return Response({'error': 'This user is not a vendor.'}, status=403)

        products = Product.objects.filter(vendor=profile).select_related('category', 'campus', 'vendor')
        payload = {
            'vendor': VendorProfileSerializer(profile).data,
            'verification': profile.verification_submissions.first(),
            'stats': {
                'published': products.filter(is_published=True, approval_status='approved').count(),
                'pending_review': products.filter(approval_status='pending').count(),
                'rejected': products.filter(approval_status='rejected').count(),
                'unavailable': products.filter(availability='unavailable').count(),
                'drafts': products.filter(is_published=False).count(),
                'total': products.count(),
            },
            'products': ProductListSerializer(products, many=True).data,
        }
        verification = payload['verification']
        payload['verification'] = VendorVerificationSerializer(verification).data if verification else None
        return Response(payload)


class VendorVerificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_vendor(self, request):
        return getattr(request.user, 'vendor_profile', None)

    def get(self, request):
        vendor = self.get_vendor(request)
        if not vendor:
            return Response({'error': 'A seller account is required.'}, status=403)
        latest = vendor.verification_submissions.first()
        return Response({
            'is_verified': vendor.is_verified,
            'submission': VendorVerificationSerializer(latest).data if latest else None,
        })

    def post(self, request):
        vendor = self.get_vendor(request)
        if not vendor or not vendor.is_active:
            return Response({'error': 'An active seller account is required.'}, status=403)
        serializer = VendorVerificationSerializer(data=request.data, context={'vendor': vendor})
        serializer.is_valid(raise_exception=True)
        submission = serializer.save(vendor=vendor)
        return Response({
            'message': 'Verification details submitted. SurePlug will review your submission.',
            'submission': VendorVerificationSerializer(submission).data,
        }, status=201)
