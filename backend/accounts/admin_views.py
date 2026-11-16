from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from discovery.models import BuyerSignal
from products.models import Product
from vendors.models import VendorProfile, VendorVerification

User = get_user_model()


def admin_user_payload(user):
    return {
        'id': user.pk,
        'username': user.get_username(),
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }


class AdminProfileAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        user = request.user
        return Response({
            **admin_user_payload(user),
            'full_name': user.get_full_name(),
            'role': 'Super Admin' if user.is_superuser else 'Administrator',
        })

    def patch(self, request):
        user = request.user
        for field in ('first_name', 'last_name'):
            if field in request.data:
                value = str(request.data[field]).strip()
                if len(value) > 150:
                    return Response({field: 'Must be 150 characters or fewer.'}, status=400)
                setattr(user, field, value)
        if 'email' in request.data:
            email = str(request.data['email']).strip()
            if User.objects.exclude(pk=user.pk).filter(email__iexact=email).exists():
                return Response({'email': 'This email address is already in use.'}, status=400)
            user.email = email
        user.save()
        return self.get(request)


class AdminOverviewAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({
            'users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'vendors': VendorProfile.objects.count(),
            'verified_vendors': VendorProfile.objects.filter(is_verified=True).count(),
            'pending_verifications': VendorVerification.objects.filter(status='pending').count(),
            'products': Product.objects.count(),
            'pending_products': Product.objects.filter(approval_status='pending').count(),
            'published_products': Product.objects.filter(is_published=True, approval_status='approved').count(),
            'buyer_signals': BuyerSignal.objects.count(),
            'active_buyer_signals': BuyerSignal.objects.filter(status='broadcast', expires_at__gt=timezone.now()).count(),
        })


class AdminUserListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = User.objects.order_by('-date_joined')
        query = request.query_params.get('q', '').strip()
        if query:
            from django.db.models import Q
            queryset = queryset.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
        return Response([admin_user_payload(user) for user in queryset[:100]])

    def patch(self, request, user_id):
        target = User.objects.filter(pk=user_id).first()
        if not target:
            return Response({'error': 'User not found.'}, status=404)
        if target.pk == request.user.pk:
            return Response({'error': 'You cannot suspend your own administrator account.'}, status=400)
        if target.is_superuser and not request.user.is_superuser:
            return Response({'error': 'Only a superuser can manage another superuser.'}, status=403)
        if 'is_active' not in request.data or not isinstance(request.data['is_active'], bool):
            return Response({'is_active': 'A boolean is required.'}, status=400)
        target.is_active = request.data['is_active']
        target.save(update_fields=['is_active'])
        return Response(admin_user_payload(target))


class AdminVendorListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        vendors = VendorProfile.objects.select_related('user', 'campus').order_by('-created_at')[:100]
        return Response([{
            'id': vendor.pk, 'business_name': vendor.business_name,
            'username': vendor.user.username, 'email': vendor.user.email,
            'phone': vendor.phone, 'campus': vendor.campus.name if vendor.campus else '',
            'is_verified': vendor.is_verified, 'is_active': vendor.is_active,
            'created_at': vendor.created_at,
        } for vendor in vendors])


class AdminVerificationListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        submissions = VendorVerification.objects.select_related('vendor', 'vendor__user').order_by('-submitted_at')[:100]
        return Response([{
            'id': item.pk, 'vendor_id': item.vendor_id,
            'business_name': item.vendor.business_name, 'username': item.vendor.user.username,
            'email': item.vendor.user.email, 'legal_name': item.legal_name,
            'document_type': item.get_document_type_display(), 'document_last4': item.document_last4,
            'contact_phone': item.contact_phone, 'status': item.status,
            'admin_notes': item.admin_notes, 'submitted_at': item.submitted_at,
        } for item in submissions])


class AdminVerificationReviewAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, verification_id):
        submission = VendorVerification.objects.select_related('vendor').filter(pk=verification_id).first()
        if not submission:
            return Response({'error': 'Verification submission not found.'}, status=404)
        action = request.data.get('action')
        note = str(request.data.get('note', '')).strip()
        if action == 'approve':
            submission.approve(request.user)
        elif action == 'reject':
            if not note:
                return Response({'note': 'A reason is required when rejecting a verification.'}, status=400)
            submission.reject(request.user, note)
        else:
            return Response({'action': 'Choose approve or reject.'}, status=400)
        return Response({'id': submission.pk, 'status': submission.status, 'admin_notes': submission.admin_notes})


class AdminProductListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = Product.objects.select_related('vendor', 'vendor__user', 'category').order_by('-created_at')[:100]
        return Response([{
            'id': item.pk, 'name': item.name, 'slug': item.slug,
            'vendor': item.vendor.business_name, 'vendor_verified': item.vendor.is_verified,
            'price': str(item.price), 'category': item.category.name if item.category else '',
            'approval_status': item.approval_status, 'is_published': item.is_published,
            'moderation_note': item.moderation_note, 'created_at': item.created_at,
        } for item in products])


class AdminProductReviewAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, product_id):
        product = Product.objects.select_related('vendor').filter(pk=product_id).first()
        if not product:
            return Response({'error': 'Listing not found.'}, status=404)
        action = request.data.get('action')
        note = str(request.data.get('note', '')).strip()
        try:
            if action == 'approve':
                product.approve(request.user)
            elif action == 'reject':
                if not note:
                    return Response({'note': 'A reason is required when rejecting a listing.'}, status=400)
                product.reject(request.user, note)
            else:
                return Response({'action': 'Choose approve or reject.'}, status=400)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        return Response({'id': product.pk, 'approval_status': product.approval_status, 'is_published': product.is_published})


class AdminActivityAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        entries = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:30]
        return Response([{
            'id': entry.pk, 'actor': entry.user.get_username(),
            'action': entry.get_change_message() or entry.get_action_flag_display(),
            'object': entry.object_repr, 'content_type': str(entry.content_type),
            'action_time': entry.action_time,
        } for entry in entries])
