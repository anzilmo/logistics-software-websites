# customer/utils.py
from decimal import Decimal

def money(amount: Decimal, currency: str) -> str:
    if amount is None:
        return "—"
    return f"{amount.quantize(Decimal('0.01'))} {currency}"
