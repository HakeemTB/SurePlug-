import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0002_seed_default_categories'),
        ('vendors', '0001_initial'),
        ('products', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='SellerLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('location_label', models.CharField(blank=True, max_length=180)),
                ('service_radius_km', models.PositiveSmallIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='geo_location', to='vendors.vendorprofile')),
            ],
        ),
        migrations.CreateModel(
            name='BuyerSignal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True, max_length=2000)),
                ('budget_min', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('budget_max', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('location_label', models.CharField(max_length=180)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('radius_km', models.PositiveSmallIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('urgency', models.CharField(choices=[('low', 'Whenever'), ('normal', 'Soon'), ('urgent', 'Urgent')], default='normal', max_length=10)),
                ('status', models.CharField(choices=[('broadcast', 'Active'), ('paused', 'Paused'), ('connected', 'Connected'), ('fulfilled', 'Fulfilled'), ('closed', 'Closed'), ('expired', 'Expired')], default='broadcast', max_length=12)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='buyer_signals', to='categories.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_signals', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at'], 'indexes': [models.Index(fields=['status', 'expires_at']), models.Index(fields=['category', 'status'])]},
        ),
        migrations.CreateModel(
            name='BuyerSignalResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=1000)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signal_responses', to='products.product')),
                ('signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='discovery.buyersignal')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signal_responses', to='vendors.vendorprofile')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='buyersignalresponse',
            constraint=models.UniqueConstraint(fields=('signal', 'vendor'), name='unique_vendor_signal_response'),
        ),
    ]
