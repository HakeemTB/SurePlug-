from django.urls import path
from .views import (
    BuyerSignalDetailAPIView, BuyerSignalListCreateAPIView, BuyerSignalResponseAPIView,
    NearbyDiscoveryAPIView, SellerLocationAPIView,
)

urlpatterns = [
    path('nearby/', NearbyDiscoveryAPIView.as_view(), name='nearby-discovery'),
    path('vendors/location/', SellerLocationAPIView.as_view(), name='seller-location'),
    path('buyer-signals/', BuyerSignalListCreateAPIView.as_view(), name='buyer-signal-list-create'),
    path('buyer-signals/<int:signal_id>/', BuyerSignalDetailAPIView.as_view(), name='buyer-signal-detail'),
    path('buyer-signals/<int:signal_id>/respond/', BuyerSignalResponseAPIView.as_view(), name='buyer-signal-respond'),
]
