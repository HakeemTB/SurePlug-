from django.urls import path
from .views import CsrfCookieAPIView, HealthCheckAPIView, LoginAPIView, LogoutAPIView, RegisterVendorAPIView
from .admin_views import (
    AdminActivityAPIView, AdminOverviewAPIView, AdminProductListAPIView,
    AdminProductReviewAPIView, AdminProfileAPIView, AdminUserListAPIView,
    AdminVendorListAPIView, AdminVerificationListAPIView, AdminVerificationReviewAPIView,
)

urlpatterns = [
    path('health/', HealthCheckAPIView.as_view(), name='health-check'),
    path('auth/csrf/', CsrfCookieAPIView.as_view(), name='csrf-cookie'),
    path('auth/register/', RegisterVendorAPIView.as_view(), name='register-vendor'),
    path('auth/login/', LoginAPIView.as_view(), name='login-user'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout-user'),
    path('admin/profile/', AdminProfileAPIView.as_view(), name='admin-profile'),
    path('admin/overview/', AdminOverviewAPIView.as_view(), name='admin-overview'),
    path('admin/users/', AdminUserListAPIView.as_view(), name='admin-users'),
    path('admin/users/<int:user_id>/', AdminUserListAPIView.as_view(), name='admin-user-detail'),
    path('admin/vendors/', AdminVendorListAPIView.as_view(), name='admin-vendors'),
    path('admin/verifications/', AdminVerificationListAPIView.as_view(), name='admin-verifications'),
    path('admin/verifications/<int:verification_id>/review/', AdminVerificationReviewAPIView.as_view(), name='admin-verification-review'),
    path('admin/products/', AdminProductListAPIView.as_view(), name='admin-products'),
    path('admin/products/<int:product_id>/review/', AdminProductReviewAPIView.as_view(), name='admin-product-review'),
    path('admin/activity/', AdminActivityAPIView.as_view(), name='admin-activity'),
]
