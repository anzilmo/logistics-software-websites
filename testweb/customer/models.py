# customer/models.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from uuid import uuid4
import os
import logging

from django.conf import settings
from django.db import models
from django.db.models import Q
from warehouse.models import Shipment

logger = logging.getLogger(__name__)


from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

# ---- optional deps (PhoneNumberField) ----
try:
    from phonenumber_field.modelfields import PhoneNumberField
except Exception:  # fallback if lib not installed
    class PhoneNumberField(models.CharField):  # type: ignore
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("max_length", 32)
            super().__init__(*args, **kwargs)

# ---- optional validator for file size ----
try:
    from .validators import validate_file_size
except Exception:
    def validate_file_size(f):  # 5MB default fallback
        limit = 5 * 1024 * 1024
        if f.size > limit:
            raise models.ValidationError("File too large (max 5 MB).")


# ========= tiny helpers =========
def money2(value) -> Decimal:
    d = Decimal(str(value or "0"))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ========= MembershipTier =========
class MembershipTier(models.Model):
    """
    A tier that may charge:
      - percent_fee: percentage applied to a base amount (0-100)
      - fixed_fee: flat fee in the same currency
    Example rows:
      - Silver: percent_fee=0, fixed_fee=0
      - Gold: percent_fee=10, fixed_fee=8
      - Platinum: percent_fee=25, fixed_fee=15
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    percent_fee = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))]
    )
    fixed_fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    currency = models.CharField(max_length=8, default="USD")
    active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ("ordering", "name")

    def __str__(self):
        return f"{self.name} ({self.currency})"

    def calculate_fee(self, base_amount):
        """
        Given a base_amount (Decimal or numeric), compute discounts:
          - percent_amount (base_amount * percent_fee / 100) as discount
          - fixed_fee as additional discount
          - total_discount = percent_amount + fixed_fee
          - total_cost = base_amount - total_discount

        Returns a dict with Decimal values quantized to 2 decimals.
        """
        from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

        quant = Decimal("0.01")
        try:
            base = Decimal(str(base_amount))
        except (InvalidOperation, TypeError):
            base = Decimal("0.00")

        percent_amount = (base * (self.percent_fee / Decimal("100"))).quantize(quant, rounding=ROUND_HALF_UP)
        fixed = Decimal(str(self.fixed_fee)).quantize(quant, rounding=ROUND_HALF_UP)
        total_discount = (percent_amount + fixed).quantize(quant, rounding=ROUND_HALF_UP)
        total_cost = (base - total_discount).quantize(quant, rounding=ROUND_HALF_UP)

        return {
            "base_amount": base.quantize(quant, rounding=ROUND_HALF_UP),
            "percent_fee_pct": self.percent_fee.quantize(quant),
            "percent_amount": percent_amount,
            "fixed_fee": fixed,
            "total_fee": total_discount,  # kept as total_fee for compatibility
            "total_cost": total_cost,
            "currency": self.currency,
        }


# ========= Profile =========
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    user_id_custom = models.CharField(max_length=10, unique=True, blank=True)
    membership_tier = models.ForeignKey(MembershipTier, null=True, blank=True, on_delete=models.SET_NULL, related_name="profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _generate_next_user_id(self) -> str:
        """Sequential IDs like SNF001, SNF002, …"""
        last = Profile.objects.order_by("id").last()
        if last and last.user_id_custom:
            try:
                n = int(last.user_id_custom.replace("SNF", ""))
            except ValueError:
                n = 0
            return f"SNF{n + 1:03d}"
        return "SNF001"

    def save(self, *args, **kwargs):
        if not self.user_id_custom:
            self.user_id_custom = self._generate_next_user_id()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user.username} — {self.user_id_custom}"




# ========= Country =========
class Country(models.Model):
    country_logo = models.ImageField(upload_to="country_logos/", blank=True, null=True)
    country_name = models.CharField(max_length=100, unique=True)
    warehouse_address = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    provider_code = models.CharField(max_length=80, blank=True, help_text="internal provider key for adapter lookup")
    api_base = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ("country_name",)

    def __str__(self) -> str:
        return self.country_name


# ========= Purchase Bill (PDF upload) =========
def purchase_pdf_upload_to(instance: "PurchaseBill", filename: str) -> str:
    base, ext = os.path.splitext(filename)
    return f"purchase_bills/{instance.invoice_number}{ext or '.pdf'}"

class PurchaseBill(models.Model):
    supplier = models.CharField(max_length=200)
    invoice_number = models.CharField(max_length=100, unique=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    pdf = models.FileField(
        upload_to=purchase_pdf_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"]), validate_file_size],
        null=True,
        blank=True,
        help_text="Upload a PDF file (max 5 MB).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} — {self.supplier}"

    def delete(self, *args, **kwargs):
        path = self.pdf.path if self.pdf else None
        super().delete(*args, **kwargs)
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass






# ========= Courier / Rates =========
class Courier(models.Model):
    name = models.CharField(max_length=120, unique=True)
    logo = models.ImageField(upload_to="courier_logos/", null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @property
    def logo_url(self) -> str | None:
        try:
            return self.logo.url
        except Exception:
            return None


class CourierRate(models.Model):
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, related_name="rates")
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    min_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="USD")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("courier__name", "currency", "id")
        indexes = [
            models.Index(fields=["courier", "active"]),
        ]
        verbose_name = "Courier rate"
        verbose_name_plural = "Courier rates"

    def __str__(self) -> str:
        return f"{self.courier.name} — {self.currency} {self.price_per_kg}/kg"

    def price_for_weight(self, weight_kg) -> Decimal:
        if weight_kg in (None, ""):
            return money2(self.min_charge)
        try:
            w = Decimal(str(weight_kg))
        except (InvalidOperation, TypeError, ValueError):
            w = Decimal("0")
        price = (w * self.price_per_kg)
        if price < self.min_charge:
            price = self.min_charge
        return money2(price)


# ========= Console Shipment (activity/flags) =========

# customer/models_membership.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Plan(models.Model):
    BILLING_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    slug = models.SlugField(unique=True)             # "gold", "platinum"
    name = models.CharField(max_length=50)           # "Gold", "Platinum"
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    currency = models.CharField(max_length=3, default="USD")
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CHOICES, default="monthly")
    features = models.JSONField(default=list, blank=True)   # ["5 shipments/mo", "Priority support"]
    active = models.BooleanField(default=True)
    sort = models.PositiveIntegerField(default=0)

    # 👇 add inside the class
    DISCOUNT_MAP = {
        "silver": Decimal("0.00"),
        "gold": Decimal("0.10"),
        "platinum": Decimal("0.25"),
    }

    def get_discount_rate(self) -> Decimal:
        """
        Returns the discount rate for this plan as a Decimal between 0 and 1.
        Match by slug first (preferred), then fallback to name (case-insensitive).
        Unrecognized plans get 0% discount.
        """
        slug_key = (self.slug or "").strip().lower()
        if slug_key in self.DISCOUNT_MAP:
            return self.DISCOUNT_MAP[slug_key]

        name_key = (self.name or "").strip().lower()
        return self.DISCOUNT_MAP.get(name_key, Decimal("0.00"))

    def get_discounted_price(self) -> Decimal:
        """
        Price after discount, rounded to 2 decimals using bankers-friendly HALF_UP.
        """
        rate = self.get_discount_rate()
        discounted = self.price * (Decimal("1.00") - rate)
        return discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def discount_label(self) -> str:
        """e.g. '10% off' or 'No discount'"""
        rate = self.get_discount_rate()
        if rate == 0:
            return "No discount"
        pct = (rate * 100).quantize(Decimal("1"))
        return f"{pct}% off"

    class Meta:
        ordering = ("sort", "price")

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"


class Membership(models.Model):
    STATUS = [
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField(max_length=10, choices=STATUS, default="active")

    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)   # optional for fixed terms
    auto_renew = models.BooleanField(default=True)

    # snapshot the price/currency at signup (so future price changes don’t affect existing)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    billing_cycle = models.CharField(max_length=10, default="monthly")

    class Meta:
        constraints = [
            # one active membership per user
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="active"),
                name="one_active_membership_per_user",
            )
        ]
        ordering = ("-started_at",)

    def __str__(self):
        return f"{self.user} → {self.plan.name} [{self.status}]"

    @property
    def is_active(self):
        if self.status != "active":
            return False
        if self.ends_at and self.ends_at <= timezone.now():
            return False
        return True

    def cancel(self, when=None):
        self.status = "canceled"
        self.auto_renew = False
        if when is None:
            when = timezone.now()
        if not self.ends_at or self.ends_at > when:
            self.ends_at = when
        self.save(update_fields=["status", "auto_renew", "ends_at"])

    def cancel(self, when=None):
        self.status = "canceled"
        self.auto_renew = False
        if when is None:
            when = timezone.now()
        if not self.ends_at or self.ends_at > when:
            self.ends_at = when
        self.save(update_fields=["status", "auto_renew", "ends_at"])


class MembershipApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership_applications")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="applications")
    billing_cycle = models.CharField(max_length=10, choices=Plan.BILLING_CHOICES, default="monthly")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="pending"),
                name="one_pending_application_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.plan.name} ({self.status})"

    def approve(self):
        """Approve the application and create a membership."""
        if self.status != "pending":
            return False
        # Create membership
        membership, created = Membership.objects.get_or_create(
            user=self.user,
            plan=self.plan,
            defaults={
                "status": "active",
                "price": self.plan.price,
                "currency": self.plan.currency,
                "billing_cycle": self.billing_cycle,
                "started_at": timezone.now(),
                "auto_renew": True,
            }
        )
        if created:
            self.status = "approved"
            self.save(update_fields=["status", "updated_at"])
            return True
        return False

    def reject(self, notes=""):
        """Reject the application."""
        if self.status != "pending":
            return False
        self.status = "rejected"
        if notes:
            self.notes = notes
        self.save(update_fields=["status", "notes", "updated_at"])
        return True




from decimal import Decimal
from django.db import models
from django.utils import timezone

class DeliveryAddress(models.Model):
    shipment = models.OneToOneField("warehouse.Shipment", on_delete=models.CASCADE, related_name="delivery_address", null=True, blank=True)
    consolidation = models.OneToOneField("Consolidation", on_delete=models.CASCADE, related_name="delivery_address", null=True, blank=True)
    recipient_name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient_name} — {self.address_line1}, {self.city}"


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    shipment = models.OneToOneField("warehouse.Shipment", on_delete=models.CASCADE, related_name="payment", null=True, blank=True)
    consolidation = models.OneToOneField("Consolidation", on_delete=models.CASCADE, related_name="payment", null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider = models.CharField(max_length=64, blank=True)  # e.g., stripe, paypal
    provider_reference = models.CharField(max_length=255, blank=True)  # provider transaction id
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_success(self, provider_reference: str = ""):
        self.status = self.STATUS_SUCCESS
        if provider_reference:
            self.provider_reference = provider_reference
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "provider_reference", "updated_at"])

    def mark_failed(self, provider_reference: str = ""):
        self.status = self.STATUS_FAILED
        if provider_reference:
            self.provider_reference = provider_reference
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "provider_reference", "updated_at"])

    def __str__(self):
        if self.shipment is None:
            return f"No shipment — {self.amount} {self.currency} ({self.status})"
        return f"{self.shipment.suit_number or self.shipment.pk} — {self.amount} {self.currency} ({self.status})"
    
    
    






# ========= Console Shipment (activity/flags) =========
class ConsoleShipment(models.Model):
    ACTION_CHOICES = [
        ("hold", "Hold"),
        ("release", "Release"),
        ("packed", "Packed"),
        ("invoiced", "Invoiced"),
        ("paid", "Paid"),
        ("delivered", "Delivered"),
        ("problem", "Problem / Exception"),
        ("cancelled", "Cancelled"),
    ]

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name="console_entries",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    note = models.TextField(blank=True, max_length=2000)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="console_shipments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["shipment", "action"], name="uniq_shipment_action"),
        ]
        indexes = [
            models.Index(fields=["shipment", "action"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Console Shipment Action"
        verbose_name_plural = "Console Shipment Actions"

    def save(self, *args, **kwargs):
        if self.action:
            self.action = self.action.lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        suit = getattr(self.shipment, "suit_number", None) or f"#{self.shipment_id}"
        return f"{suit} — {self.get_action_display()}"


# ========= Consolidation =========
class Consolidation(models.Model):
    STATUS_CHOICES = [
        ("quoted", "Quoted"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consolidations")

    total_cbm = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0"))
    total_volume_weight = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    total_gross_weight = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))

    chargeable_weight = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    chargeable_basis = models.CharField(max_length=32, default="volume")  # 'volume' or 'gross'

    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    currency = models.CharField(max_length=8, default="USD")

    shipments_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="confirmed")

    # Courier selection
    selected_courier = models.ForeignKey(
        "warehouse.Courier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="selected_consolidations",
    )
    selected_rate = models.ForeignKey(
        CourierRate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="selected_consolidations",
    )
    selected_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Consolidation #{self.pk} — {self.price} {self.currency} ({self.shipments_count} items)"


class ConsolidationItem(models.Model):
    consolidation = models.ForeignKey(Consolidation, on_delete=models.CASCADE, related_name="items")
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="consolidation_items")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["consolidation", "shipment"], name="uniq_consolidation_shipment"),
        ]
        indexes = [
            models.Index(fields=["consolidation"]),
            models.Index(fields=["shipment"]),
        ]

    def __str__(self) -> str:
        suit = getattr(self.shipment, "suit_number", None) or f"#{self.shipment_id}"
        return f"Cons #{self.consolidation_id} — {suit}"






