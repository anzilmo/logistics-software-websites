# Generated manually to add created_at to Shipment

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0018_populate_couriers'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]