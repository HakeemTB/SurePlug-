from django.contrib import admin, messages
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'price', 'approval_status', 'is_published', 'availability', 'created_at')
    list_filter = ('approval_status', 'is_published', 'availability', 'condition', 'category', 'campus')
    search_fields = ('name', 'vendor__business_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    actions = ('approve_selected', 'reject_selected')

    @admin.action(description='Approve selected listings (verified sellers only)')
    def approve_selected(self, request, queryset):
        approved, skipped = 0, 0
        for product in queryset.filter(approval_status='pending').select_related('vendor'):
            try:
                product.approve(request.user)
                approved += 1
            except ValueError:
                skipped += 1
        if approved:
            self.message_user(request, f'{approved} listing(s) approved and published.', messages.SUCCESS)
        if skipped:
            self.message_user(request, f'{skipped} listing(s) skipped because their seller is not verified.', messages.WARNING)

    @admin.action(description='Reject selected listings')
    def reject_selected(self, request, queryset):
        count = 0
        for product in queryset.filter(approval_status='pending'):
            product.reject(request.user, 'Please edit the listing and resubmit it for review.')
            count += 1
        self.message_user(request, f'{count} listing(s) rejected.', messages.WARNING)
