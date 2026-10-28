from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from campuses.models import Campus
from categories.models import Category
from .models import Product
from .serializers import ProductDetailSerializer, ProductListSerializer


class ProductListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        filters = ProductFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        values = filters.validated_data

        queryset = Product.objects.filter(
            is_published=True,
            vendor__is_active=True,
        ).select_related('vendor', 'vendor__user', 'category', 'campus', 'vendor__campus')
        query = values.get('q', '')
        category = values.get('category')
        campus = values.get('campus')
        min_price = values.get('min_price')
        max_price = values.get('max_price')
        availability = values.get('availability')
        ordering = values.get('ordering', 'recent')

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if category:
            queryset = queryset.filter(category__slug=category)
        if campus:
            queryset = queryset.filter(
                Q(campus__name__icontains=campus)
                | Q(vendor__campus__name__icontains=campus)
            )
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if availability:
            queryset = queryset.filter(availability=availability)

        if ordering == 'price_asc':
            queryset = queryset.order_by('price')
        elif ordering == 'price_desc':
            queryset = queryset.order_by('-price')
        elif ordering == 'recent':
            queryset = queryset.order_by('-updated_at')
        elif ordering == 'featured':
            queryset = queryset.order_by('-featured', '-updated_at')

        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)


class ProductDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects.filter(is_published=True, vendor__is_active=True)
            .select_related('vendor', 'vendor__user', 'category', 'campus', 'vendor__campus'),
            slug=slug,
        )
        return Response(ProductDetailSerializer(product).data)


class ProductFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=200)
    category = serializers.SlugField(required=False)
    campus = serializers.CharField(required=False, allow_blank=True, max_length=150)
    min_price = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0)
    max_price = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0)
    availability = serializers.ChoiceField(required=False, choices=Product.AVAILABILITY_CHOICES)
    ordering = serializers.ChoiceField(
        required=False,
        choices=['recent', 'price_asc', 'price_desc', 'featured'],
    )

    def validate(self, attrs):
        minimum = attrs.get('min_price')
        maximum = attrs.get('max_price')
        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError({'max_price': 'Must be greater than or equal to min_price.'})
        return attrs


class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    category = serializers.CharField(max_length=150)
    campus = serializers.CharField(max_length=150)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    condition = serializers.ChoiceField(choices=Product.CONDITION_CHOICES)
    availability = serializers.ChoiceField(choices=Product.AVAILABILITY_CHOICES)
    is_published = serializers.BooleanField(default=True)
    image = serializers.ImageField(required=False, allow_null=True)
    contact_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    external_url = serializers.URLField(required=False, allow_blank=True)

    def create(self, validated_data):
        category_name = validated_data.pop('category').strip()
        campus_name = validated_data.pop('campus').strip()
        category_slug = slugify(category_name)
        category, _ = Category.objects.get_or_create(
            slug=category_slug,
            defaults={'name': category_name},
        )
        campus, _ = Campus.objects.get_or_create(name=campus_name, defaults={'zone': 'Campus', 'description': 'Campus listing'})
        vendor = self.context['request'].user.vendor_profile
        product = Product.objects.create(
            vendor=vendor,
            category=category,
            campus=campus,
            **validated_data,
        )
        return product


class ProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        vendor = getattr(request.user, 'vendor_profile', None)
        if not vendor or not vendor.is_active:
            return Response({'error': 'Only vendor accounts can create products.'}, status=403)
        serializer = ProductCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response({'message': 'Product created.', 'slug': product.slug}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, slug):
        product = get_object_or_404(Product.objects.select_related('vendor', 'vendor__user'), slug=slug)
        if product.vendor.user != request.user:
            return Response({'error': 'You can only update your own products.'}, status=403)
        serializer = ProductUpdateSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProductDetailSerializer(serializer.instance).data)


class ProductUpdateSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'price',
            'condition',
            'availability',
            'is_published',
            'image',
            'contact_phone',
            'whatsapp_number',
            'external_url',
        ]


class ProductDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, slug):
        product = get_object_or_404(Product.objects.select_related('vendor', 'vendor__user'), slug=slug)
        if product.vendor.user != request.user:
            return Response({'error': 'You can only delete your own products.'}, status=403)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
