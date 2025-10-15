# Generated manually to add active field to CourierRate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0029_add_active_to_courier'),
    ]

    operations = [
        migrations.AddField(
            model_name='courierrate',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]