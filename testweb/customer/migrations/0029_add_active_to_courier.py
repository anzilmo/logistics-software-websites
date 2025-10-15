# Generated manually to add active field to Courier

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0028_add_created_at_to_courierrate'),
    ]

    operations = [
        migrations.AddField(
            model_name='courier',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]