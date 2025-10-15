import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

def _preclean_courier_fk(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("UPDATE warehouse_courierselection SET courier_id = NULL")

class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0025_alter_consoleshipment_options_and_more'),
        ('warehouse', '0013_staffnotification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Courier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
            ],
        ),
        # … all your rename/add/remove ops stay the same …

        # 1) RELAX the existing 'courier' column FIRST (still pointing at customer.CourierCompany)
        migrations.AlterField(
            model_name='courierselection',
            name='courier',
            field=models.ForeignKey(
                to='customer.couriercompany',
                on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True,
                related_name='selections_legacy',  # name doesn't matter much; keep or drop
            ),
        ),

        # 2) Now it's legal to NULL them out
        migrations.RunPython(_preclean_courier_fk, migrations.RunPython.noop),

        # 3) Retarget FK to the new table (still nullable)
        migrations.AlterField(
            model_name='courierselection',
            name='courier',
            field=models.ForeignKey(
                to='warehouse.courier',
                on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True,
                related_name='selections',
            ),
        ),

        # 4) Indexes etc.
        migrations.AddIndex(
            model_name='courierselection',
            index=models.Index(fields=['shipment'], name='warehouse_c_shipmen_f3fb2b_idx'),
        ),
        migrations.AddIndex(
            model_name='courierselection',
            index=models.Index(fields=['courier'], name='warehouse_c_courier_51bbed_idx'),
        ),
    ]
