from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason', 'product', 'vendor', 'status', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('reporter_name', 'reporter_email', 'message', 'product__name', 'vendor__business_name')
    readonly_fields = ('created_at', 'updated_at')
