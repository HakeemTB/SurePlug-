import django.conf
import django.db.models.deletion
from django.db import migrations, models


def approve_existing_published_listings(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(is_published=True).update(approval_status='approved')


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0001_initial'),
        ('vendors', '0002_vendorverification'),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='approval_status',
            field=models.CharField(choices=[('pending', 'Pending review'), ('approved', 'Approved'), ('rejected', 'Changes required / rejected')], default='pending', max_length=12),
        ),
        migrations.AddField(
            model_name='product',
            name='moderation_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_sureplug_products', to=django.conf.settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(approve_existing_published_listings, migrations.RunPython.noop),
    ]
