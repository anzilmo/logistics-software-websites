from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal, ROUND_UP, InvalidOperation
import math
from django.conf import settings
from django.db import models, transaction, IntegrityError
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import os







User = get_user_model()



def generate_suit_number():
    return f"SUIT-{uuid.uuid4().hex[:8].upper()}"



class Warehouse(models.Model):
    country_name = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=150, default='')
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)


    def set_password(self, raw_password):
        """Hash and set the warehouse password."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if the provided password matches the hashed password."""
        if not self.password_hash:
            return False
        return check_password(raw_password, self.password_hash)

    def save(self, *args, **kwargs):
        """Automatically hash the code as password if password_hash is not set."""
        if not self.password_hash and self.code:
            self.set_password(self.code)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.country_name} ({self.code})"



class Rate(models.Model):
    """
    Admin-managed global rate. Superadmin adds rates in Django admin and marks one (or more) active.
    """
    name = models.CharField(max_length=120)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    min_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="USD")
    active = models.BooleanField(default=True)

    def price_for_weight(self, weight_kg):
        w = Decimal(str(weight_kg))
        price = (w * self.price_per_kg).quantize(Decimal("0.01"))
        if price < self.min_charge:
            price = self.min_charge.quantize(Decimal("0.01"))
        return price

    def __str__(self):
        return f"{self.name} ({self.currency} {self.price_per_kg}/kg)"






# warehouse/models.py
class Shipment(models.Model):
    # --- canonical workflow status (keep this if you really track lifecycle) ---
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_IN_TRANSIT = "in_transit"
    STATUS_DELIVERED = "delivered"
    STATUS_HELD = "held"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Warehouse Accepted"),
        (STATUS_IN_TRANSIT, "In Transit"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_HELD, "Held"),
        ("accepted", "Delivery Accepted"),
        ("started", "Delivery Start"),
        ("completed", "Delivery Completed"),
    ]

    # Ownership (old model used owner=user; new used profile)
    # keep profile but add owner if you still need it. otherwise drop owner.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="shipments", null=True, blank=True
    )
    profile = models.ForeignKey(
        "customer.Profile", on_delete=models.CASCADE,
        related_name="shipments", null=True, blank=True
    )

    # Identifiers
    suit_number = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    tracking_number = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="accepted")
    status_updated_at = models.DateTimeField(auto_now=True)
    status_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="updated_shipments"
    )

    # Warehouse / courier relations
    warehouse = models.ForeignKey(
        "warehouse.Warehouse", on_delete=models.PROTECT,
        null=True, blank=True, related_name="shipments"
    )
    courier = models.ForeignKey(
        "warehouse.Courier", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="shipments"
    )
    selected_courier = models.ForeignKey(
        "warehouse.Courier", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="selected_shipments"
    )
    # IMPORTANT: points to CourierSelection
    selected_rate = models.ForeignKey(
        "warehouse.CourierSelection", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+"
    )
    selected_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Status dates
    status = models.CharField(max_length=32, choices=STATUS_CHOICES,
                              default=STATUS_PENDING, db_index=True)
    status_last_synced = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)

    # Physicals (cm / kg) — switch to Decimal for precision
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    width_cm  = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal("0.000"))

    package_type = models.CharField(max_length=50, blank=True)
    arrival_date = models.DateField(null=True, blank=True)

    # freeform
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    # ------------------ Display helpers ------------------
    @property
    def ui_status(self):
        """Lightweight UI label similar to your property-based status."""
        return "Normal" if self.selected_courier_id else "Pending"

    def __str__(self):
        owner_label = getattr(self.profile, "user_id_custom", None) or str(self.owner_id) or "unknown"
        return f"{self.suit_number} - {self.tracking_number or 'NoTrack'} ({owner_label})"

    # ------------------ Suit number generation (race-safe) ------------------
    def _base_user_code(self):
        """Choose what to prefix. Prefer profile.user_id_custom; fallback to owner id."""
        if self.profile and getattr(self.profile, "user_id_custom", None):
            return str(self.profile.user_id_custom)
        if self.owner_id:
            return f"U{self.owner_id}"
        return None

    def _generate_suit_number_candidate(self, base_code, next_num):
        return f"{base_code}-{next_num:03d}"

    def _generate_next_suit_number(self):
        base = self._base_user_code()
        if not base:
            return None

        # Find last numeric suffix for this base
        last = (
            Shipment.objects
            .filter(suit_number__startswith=f"{base}-")
            .order_by("-id")
            .values_list("suit_number", flat=True)
            .first()
        )
        last_num = 0
        if last:
            try:
                last_num = int(last.split("-")[-1])
            except Exception:
                last_num = 0
        # Try a few candidates in case of race
        for offset in range(1, 1000):
            yield self._generate_suit_number_candidate(base, last_num + offset)

    def save(self, *args, **kwargs):
        if not self.suit_number:
            base = self._base_user_code()
            if base:
                # race-safe loop
                for candidate in self._generate_next_suit_number():
                    self.suit_number = candidate
                    try:
                        with transaction.atomic():
                            super().save(*args, **kwargs)
                        break
                    except IntegrityError:
                        # try next candidate
                        self.suit_number = None
                        continue
                if not self.pk:
                    # if we never broke out successfully
                    raise IntegrityError("Could not assign a unique suit_number.")
                return
        super().save(*args, **kwargs)

    # compatibility with your old helper
    def set_tracking_number(self, tracking_number):
        self.tracking_number = tracking_number
        self.status_last_synced = None
        self.save(update_fields=["tracking_number", "status_last_synced", "updated_at"])

    # ------------------ Decimal helpers ------------------
    @staticmethod
    def _to_decimal(value):
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    # ------------------ Volume & weight calculations ------------------
    def cbm(self, from_unit="cm"):
        """
        Return volume in cubic meters.
        from_unit: 'cm' (default) or 'm'
        """
        l = self._to_decimal(self.length_cm)
        w = self._to_decimal(self.width_cm)
        h = self._to_decimal(self.height_cm)

        if from_unit == "cm":
            # cm -> m is /100 per dimension => /1_000_000 for volume
            l /= Decimal("100")
            w /= Decimal("100")
            h /= Decimal("100")
        elif from_unit != "m":
            raise ValueError("from_unit must be 'cm' or 'm'")

        cbm_val = l * w * h
        return cbm_val.quantize(Decimal("0.000001"))

    def volume_weight(self, from_unit="cm", factor=Decimal("200")):
        """
        Volumetric weight (kg) = CBM * factor.
        Common IATA factor for air: 167; many couriers use 200.
        """
        cbm_val = self.cbm(from_unit=from_unit)
        vw = cbm_val * Decimal(str(factor))
        return vw.quantize(Decimal("0.01"))

    def chargeable_weight(self, from_unit="cm", rounding="ceil_0_5"):
        """
        Chargeable weight (kg) = max(gross, volumetric).
        rounding:
          - 'no_round' : keep 2 decimals
          - 'ceil_int' : ceil to next integer
          - 'ceil_0_5' : ceil to next 0.5 kg (default)
        """
        gross = self._to_decimal(self.weight_kg)
        vol = self.volume_weight(from_unit=from_unit)
        chosen = gross if gross > vol else vol

        if rounding == "no_round":
            return chosen.quantize(Decimal("0.01"))
        elif rounding == "ceil_int":
            return Decimal(math.ceil(chosen)).quantize(Decimal("0.01"))
        elif rounding == "ceil_0_5":
            doubled = chosen * Decimal("2")
            rounded = doubled.quantize(Decimal("1"), rounding=ROUND_UP)
            return (rounded / Decimal("2")).quantize(Decimal("0.01"))
        else:
            raise ValueError("Unknown rounding option")

    # ------------------ Price calculation ------------------
    def price_using_active_rate(self, from_unit="cm", rounding="ceil_0_5"):
        """
        Use the first active warehouse.Rate to compute price.
        """
        Rate = apps.get_model("warehouse", "Rate")  # unify on warehouse.Rate
        rate = Rate.objects.filter(active=True).first()
        if not rate:
            return None, None
        cw = self.chargeable_weight(from_unit=from_unit, rounding=rounding)
        price = rate.price_for_weight(cw)
        return rate, price

    def total_using_rate(self, rate_instance=None, from_unit="cm", rounding="ceil_0_5"):
        """
        Compute price using a provided Rate instance, or the first active one.
        """
        if rate_instance is None:
            Rate = apps.get_model("warehouse", "Rate")
            rate_instance = Rate.objects.filter(active=True).first()
            if not rate_instance:
                return None
        cw = self.chargeable_weight(from_unit=from_unit, rounding=rounding)
        return rate_instance.price_for_weight(cw)

    # ------------------ Validation ------------------
    def clean(self):
        if self.length_cm <= 0 or self.width_cm <= 0 or self.height_cm <= 0:
            raise ValidationError("Length, width and height must be positive numbers.")
        if self.weight_kg <= 0:
            raise ValidationError("Weight must be a positive number.")








# waerhouse/models.py 
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Consolidation(models.Model):
    """
    Represents a consolidation request that groups multiple shipments into one consolidated shipment.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="warehouse_consolidations")
    shipments = models.ManyToManyField("Shipment", related_name="consolidations")
    total_cbm = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))
    total_volume_weight = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    total_gross_weight = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    chargeable_weight = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    rate_per_kg = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.00"))
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Consolidation #{self.pk} by {self.owner} — {self.chargeable_weight} kg / {self.price}"
























# uplode funtion 
# ======================
# Upload Path Functions
# ======================
def shipment_image_upload_to(instance, filename):
    return f"shipments/{instance.shipment.id}/{filename}"

def purchase_pdf_upload_to(instance, filename):
    return f"purchase_bills/{instance.invoice_number}/{filename}"


class ShipmentImage(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=shipment_image_upload_to)
    captured_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_images"
    )

    class Meta:
        ordering = ("-captured_at",)
        verbose_name = "Shipment Image"
        verbose_name_plural = "Shipment Images"

    def clean(self):
        if not self.shipment:
            raise ValidationError("Shipment is required for ShipmentImage.")

    def __str__(self):
        return f"Image {self.id} for {self.shipment.suit_number}"














# warehouse/models.py
# from django.conf import settings
# from django.db import models

# class CourierSelection(models.Model):
#     shipment   = models.ForeignKey("warehouse.Shipment", on_delete=models.CASCADE, related_name="courier_selections")
#     courier    = models.ForeignKey("customer.CourierCompany", on_delete=models.PROTECT)
#     rate       = models.ForeignKey("customer.CourierRate", on_delete=models.PROTECT)
#     price      = models.DecimalField(max_digits=10, decimal_places=2)
#     currency   = models.CharField(max_length=10)
#     chosen_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
#     chosen_at  = models.DateTimeField(auto_now_add=True)
    
    

#     # NEW: Warehouse notification state
#     seen_by_warehouse = models.BooleanField(default=False)

#     class Meta:
#         ordering = ("-chosen_at",)

#     def __str__(self):
#         return f"{self.courier.name} — {self.price} {self.currency} (#{self.shipment_id})"
# warehouse/models.py
from django.conf import settings
from django.db import models

class Courier(models.Model):
    name = models.CharField(max_length=120, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CourierSelection(models.Model):
    """
    One selectable carrier/rate option for a Shipment.
    Reverse accessor on Shipment: `courier_selections`.
    """
    shipment = models.ForeignKey(
        "warehouse.Shipment",
        on_delete=models.CASCADE,
        related_name="courier_selections",
        db_index=True,
    )
    # NEW: normalized courier (targeting warehouse.Courier)
    courier = models.ForeignKey(
        "warehouse.Courier",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="selections",
        db_index=True,
    )

    # Legacy (temporary) to help migrate from old schema
    legacy_courier_company = models.ForeignKey(
        "customer.Courier",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="selections_legacy",
        help_text="Temporary during migration; remove after backfill.",
    )
    legacy_rate = models.ForeignKey(
        "customer.CourierRate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="selections_legacy",
        help_text="Temporary during migration; remove after backfill.",
    )

    # Descriptive
    service_name = models.CharField(max_length=120, blank=True)
    carrier_rate_id = models.CharField(max_length=128, blank=True)

    # Pricing (normalized)
    currency = models.CharField(max_length=10, default="USD")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    surcharge  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Audit / status
    chosen_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)  # replaces chosen_at
    is_active  = models.BooleanField(default=True)
    seen_by_warehouse = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shipment"]),
            models.Index(fields=["courier"]),
        ]

    def __str__(self):
        c = (self.courier and self.courier.name) or (self.legacy_courier_company and self.legacy_courier_company.name) or "Courier"
        return f"{c} {self.service_name or ''} — {self.total_price} {self.currency}".strip()










# warehouse/models.py  (add below your Shipment model)
from django.conf import settings
from django.db import models

class StaffNotification(models.Model):
    TYPE_CHOICES = [
        ("courier_selected", "Courier selected"),
    ]

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    shipment = models.ForeignKey("warehouse.Shipment", on_delete=models.CASCADE, related_name="notifications")
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"[{self.get_type_display()}] {self.text}"







# shipments/models.py (append)
class ShipmentStatusHistory(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=64)
    message = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["shipment", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        suit = getattr(self.shipment, "suit_number", "") or f"ID {self.shipment_id}"
        return f"{suit} — {self.status} @ {self.created_at.isoformat()}"
    
    
    
  