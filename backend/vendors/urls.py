from django.urls import path
from .views import VendorDashboardAPIView, VendorDetailAPIView, VendorListAPIView

urlpatterns = [
    path('vendors/', VendorListAPIView.as_view(), name='vendor-list'),
    path('vendors/dashboard/', VendorDashboardAPIView.as_view(), name='vendor-dashboard'),
    path('vendors/<slug:slug>/', VendorDetailAPIView.as_view(), name='vendor-detail'),
]
