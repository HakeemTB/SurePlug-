from django.urls import path
from .views import CsrfCookieAPIView, HealthCheckAPIView, LoginAPIView, LogoutAPIView, RegisterVendorAPIView

urlpatterns = [
    path('health/', HealthCheckAPIView.as_view(), name='health-check'),
    path('auth/csrf/', CsrfCookieAPIView.as_view(), name='csrf-cookie'),
    path('auth/register/', RegisterVendorAPIView.as_view(), name='register-vendor'),
    path('auth/login/', LoginAPIView.as_view(), name='login-user'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout-user'),
]
