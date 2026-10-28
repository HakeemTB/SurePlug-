from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('accounts.urls')),
    path('api/v1/', include('campuses.urls')),
    path('api/v1/', include('categories.urls')),
    path('api/v1/', include('vendors.urls')),
    path('api/v1/', include('products.urls')),
    path('api/v1/', include('moderation.urls')),
]
