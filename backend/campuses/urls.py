from django.urls import path
from .views import CampusListAPIView

urlpatterns = [
    path('campuses/', CampusListAPIView.as_view(), name='campus-list'),
]
