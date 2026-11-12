from django.contrib import admin, messages
from .models import VendorProfile, VendorVerification


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'campus', 'is_verified', 'is_active', 'created_at')
    list_filter = ('is_verified', 'is_active', 'campus')
    search_fields = ('business_name', 'user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VendorVerification)
class VendorVerificationAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'legal_name', 'document_type', 'status', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'document_type', 'submitted_at')
    search_fields = ('vendor__business_name', 'legal_name', 'contact_phone')
    readonly_fields = ('submitted_at', 'reviewed_at', 'reviewed_by')
    actions = ('approve_selected', 'reject_selected')

    @admin.action(description='Approve selected seller verifications')
    def approve_selected(self, request, queryset):
        count = 0
        for submission in queryset.filter(status='pending').select_related('vendor'):
            submission.approve(request.user)
            count += 1
        self.message_user(request, f'{count} seller verification(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected seller verifications')
    def reject_selected(self, request, queryset):
        count = 0
        for submission in queryset.filter(status='pending').select_related('vendor'):
            submission.reject(request.user, 'Please contact SurePlug support for the next steps.')
            count += 1
        self.message_user(request, f'{count} seller verification(s) rejected.', messages.WARNING)
