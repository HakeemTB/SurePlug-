from django.urls import path
from .views import ProductCreateAPIView, ProductDeleteAPIView, ProductDetailAPIView, ProductListAPIView, ProductUpdateAPIView

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products/create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/<slug:slug>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/<slug:slug>/update/', ProductUpdateAPIView.as_view(), name='product-update'),
    path('products/<slug:slug>/delete/', ProductDeleteAPIView.as_view(), name='product-delete'),
]
