# Generated manually to add created_at to CourierRate

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0027_rename_couriercompany_to_courier'),
    ]

    operations = [
        migrations.AddField(
            model_name='courierrate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]