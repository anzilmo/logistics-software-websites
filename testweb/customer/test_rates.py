# customer/tests/test_rates.py
from decimal import Decimal
from django.test import TestCase
from customer.models import Courier, CourierRate

class RateCalcTests(TestCase):
    def setUp(self):
        self.c = Courier.objects.create(name="FastX")
        self.r = CourierRate.objects.create(
            courier=self.c, price_per_kg=Decimal("10.00"),
            min_charge=Decimal("25.00"), currency="USD", active=True
        )

    def test_min_charge_applies(self):
        self.assertEqual(self.r.price_for_weight(Decimal("1.5")), Decimal("25.00"))  # 15 < 25

    def test_linear_price(self):
        self.assertEqual(self.r.price_for_weight(Decimal("3.0")), Decimal("30.00"))  # 30 >= 25

    def test_invalid_weight_falls_back(self):
        self.assertEqual(self.r.price_for_weight(None), Decimal("25.00"))
        self.assertEqual(self.r.price_for_weight("oops"), Decimal("25.00"))
