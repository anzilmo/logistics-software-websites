from django.core.management.base import BaseCommand
from warehouse.models import Warehouse

class Command(BaseCommand):
    help = 'Seed default warehouses (country_name + code). Password will be set to code.'

    WAREHOUSES = [
        ('Chain', 'CHW001'),
        ('Qatar', 'QR002'),
        ('UAE', 'UAE03'),
        ('USA', 'USA04'),
        ('Bahrain', 'BR005'),
        ('Turkey', 'TR006'),
    ]

    def handle(self, *args, **options):
        created = 0
        for country, code in self.WAREHOUSES:
            obj, is_new = Warehouse.objects.get_or_create(
                country_name=country,
                defaults={'code': code}
            )
            if is_new:
                obj.set_password(code)
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Created {country} ({code})'))
                created += 1
            else:
                self.stdout.write(f'{country} already exists')
        self.stdout.write(self.style.SUCCESS(f'Done. {created} created.'))