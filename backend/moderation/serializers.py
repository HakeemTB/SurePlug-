from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'product', 'vendor', 'reporter_name', 'reporter_email', 'reason', 'message', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

    def validate(self, attrs):
        if not attrs.get('product') and not attrs.get('vendor'):
            raise serializers.ValidationError('A product or vendor must be specified.')
        return attrs
