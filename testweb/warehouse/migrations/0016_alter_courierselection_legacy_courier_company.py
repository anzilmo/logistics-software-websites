# Fix the lazy reference after rename

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0027_rename_couriercompany_to_courier'),
        ('warehouse', '0015_alter_courierselection_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courierselection',
            name='legacy_courier_company',
            field=models.ForeignKey(
                blank=True,
                help_text='Temporary during migration; remove after backfill.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='selections_legacy',
                to='customer.courier',
            ),
        ),
    ]