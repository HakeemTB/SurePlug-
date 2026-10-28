from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from campuses.models import Campus
from vendors.models import VendorProfile


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'SurePlug API is running.',
            'app': 'sureplug-backend',
        })


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfCookieAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'message': 'CSRF cookie set.'})


class VendorRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    whatsapp = serializers.CharField(max_length=30, required=False, allow_blank=True)
    campus = serializers.CharField(max_length=150, required=False, allow_blank=True)
    location_description = serializers.CharField(max_length=250, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        campus_name = validated_data.pop('campus', '')
        business_name = validated_data.pop('business_name')
        phone = validated_data.pop('phone', '')
        whatsapp = validated_data.pop('whatsapp', '')
        location_description = validated_data.pop('location_description', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )

        campus = None
        if campus_name:
            campus, _ = Campus.objects.get_or_create(
                name__iexact=campus_name,
                defaults={'name': campus_name, 'zone': 'Campus', 'description': 'Marketplace location'}
            )

        slug = slugify(business_name) or 'vendor'
        base_slug = slug
        index = 1
        while VendorProfile.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{index}'
            index += 1

        vendor_profile = VendorProfile.objects.create(
            user=user,
            business_name=business_name,
            slug=slug,
            phone=phone,
            whatsapp=whatsapp,
            campus=campus,
            location_description=location_description,
            is_verified=False,
            is_active=True,
        )
        return user, vendor_profile


@method_decorator(csrf_protect, name='dispatch')
class RegisterVendorAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VendorRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, vendor = serializer.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return Response({
            'message': 'Vendor account created successfully.',
            'username': user.username,
            'business_name': vendor.business_name,
            'slug': vendor.slug,
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        profile = getattr(user, 'vendor_profile', None)
        return Response({
            'message': 'Login successful.',
            'username': user.username,
            'is_vendor': profile is not None,
            'vendor_slug': profile.slug if profile else None,
        })


@method_decorator(csrf_protect, name='dispatch')
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully.'})
