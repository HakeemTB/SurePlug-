from django.contrib import admin
from .models import BuyerSignal, BuyerSignalResponse, SellerLocation


@admin.register(SellerLocation)
class SellerLocationAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'location_label', 'service_radius_km', 'updated_at')
    search_fields = ('vendor__business_name', 'location_label')


class BuyerSignalResponseInline(admin.TabularInline):
    model = BuyerSignalResponse
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(BuyerSignal)
class BuyerSignalAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'user', 'category', 'status', 'urgency', 'expires_at')
    list_filter = ('status', 'urgency', 'category')
    search_fields = ('item_name', 'description', 'location_label', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [BuyerSignalResponseInline]
