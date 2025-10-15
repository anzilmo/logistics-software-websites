# customer/migrations/0037_seed_plans.py
from django.db import migrations

def seed_plans(apps, schema_editor):
    Plan = apps.get_model("customer", "Plan")
    Plan.objects.update_or_create(
        slug="silver",
        defaults=dict(
            name="Silver",
            price="9.00",
            currency="USD",
            billing_cycle="monthly",
            features=["Up to 2 shipments/mo", "Basic support"],
            active=True,
            sort=5,
        ),
    )
    Plan.objects.update_or_create(
        slug="gold",
        defaults=dict(
            name="Gold",
            price="19.00",
            currency="USD",
            billing_cycle="monthly",
            features=["Up to 5 shipments/mo", "Standard support"],
            active=True,
            sort=10,
        ),
    )
    Plan.objects.update_or_create(
        slug="platinum",
        defaults=dict(
            name="Platinum",
            price="49.00",
            currency="USD",
            billing_cycle="monthly",
            features=["Unlimited shipments", "Priority support", "Best courier rates"],
            active=True,
            sort=20,
        ),
    )

def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("customer", "Plan")
    Plan.objects.filter(slug__in=["gold", "platinum"]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("customer", "0036_plan_membership"),
    ]
    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]