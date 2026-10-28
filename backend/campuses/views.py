from rest_framework.generics import ListAPIView

from .models import Campus
from .serializers import CampusSerializer


class CampusListAPIView(ListAPIView):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer

