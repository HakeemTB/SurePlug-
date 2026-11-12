import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vendors', '0001_initial'),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('legal_name', models.CharField(max_length=180)),
                ('document_type', models.CharField(choices=[('nin', 'National Identification Number (NIN)'), ('voters_card', "Voter's card"), ('drivers_license', "Driver's licence"), ('passport', 'International passport'), ('student_id', 'Institutional/student ID'), ('business_document', 'Business registration document')], max_length=30)),
                ('document_last4', models.CharField(max_length=4)),
                ('contact_phone', models.CharField(max_length=30)),
                ('status', models.CharField(choices=[('pending', 'Pending review'), ('approved', 'Approved'), ('rejected', 'Changes required / rejected')], default='pending', max_length=12)),
                ('admin_notes', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_vendor_verifications', to=django.conf.settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verification_submissions', to='vendors.vendorprofile')),
            ],
            options={'ordering': ['-submitted_at']},
        ),
    ]
