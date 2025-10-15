# Generated manually to fix address model mismatch

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0030_add_active_to_courierrate'),
    ]

    operations = [
        # Remove the index on country_code since we're renaming it
        migrations.RemoveIndex(
            model_name='address',
            name='customer_ad_country_0a7e58_idx',
        ),
        # Rename columns to match current model
        migrations.RenameField(
            model_name='address',
            old_name='address_line1',
            new_name='line1',
        ),
        migrations.RenameField(
            model_name='address',
            old_name='address_line2',
            new_name='line2',
        ),
        migrations.RenameField(
            model_name='address',
            old_name='region',
            new_name='state',
        ),
        migrations.RenameField(
            model_name='address',
            old_name='country_code',
            new_name='country',
        ),
        # Remove fields not in current model
        migrations.RemoveField(
            model_name='address',
            name='full_name',
        ),
        migrations.RemoveField(
            model_name='address',
            name='company',
        ),
        migrations.RemoveField(
            model_name='address',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='address',
            name='email',
        ),
        migrations.RemoveField(
            model_name='address',
            name='delivery_instructions',
        ),
        migrations.RemoveField(
            model_name='address',
            name='lat',
        ),
        migrations.RemoveField(
            model_name='address',
            name='lng',
        ),
        migrations.RemoveField(
            model_name='address',
            name='normalized',
        ),
        migrations.RemoveField(
            model_name='address',
            name='meta',
        ),
        migrations.RemoveField(
            model_name='address',
            name='updated_at',
        ),
        # Alter type choices
        migrations.AlterField(
            model_name='address',
            name='type',
            field=models.CharField(choices=[('shipping', 'Shipping'), ('billing', 'Billing'), ('pickup', 'Pickup'), ('other', 'Other')], default='shipping', max_length=20),
        ),
        # Alter postal_code max_length
        migrations.AlterField(
            model_name='address',
            name='postal_code',
            field=models.CharField(blank=True, max_length=32),
        ),
        # Alter country default
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.CharField(default='', max_length=100),
        ),
    ]