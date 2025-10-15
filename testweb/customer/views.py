# customer/views_helpers.py
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from django.db import IntegrityError
from django.db.models import Count, IntegerField, Sum, Value
from django.shortcuts import redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.http import url_has_allowed_host_and_scheme

from warehouse import models
from warehouse.models import CourierSelection, Shipment

# customer/views_auth.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .models import ConsoleShipment, Consolidation, ConsolidationItem, Profile, Country, MembershipTier
from warehouse.models import Shipment

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from warehouse.models import Shipment

# customer/views_rates.py
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect

from warehouse.models import Shipment, Courier as WarehouseCourier
from customer.models import Courier, CourierRate

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from warehouse.models import Shipment
# customer/views_address.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse


# customer/views_consolidation.py
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse


# customer/views_photos.py
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render
from warehouse.models import ShipmentImage
from warehouse.utils import resolve_shipment_by_suit_latest
# customer/views_purchases.py
import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import PurchaseBill
from .forms import BulkActionForm, BulkAssignCourierForm, ConsoleShipmentForm, PurchaseBillForm




from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone


__all__ = [
    "base_shipments_for_user",
    "safe_select_related_shipments",
    "annotate_rate_count",
    "normalize_action",
    "safe_redirect",
    "user_is_owner",
    "to_money_2",
    "coerce_unit",
    "coerce_rounding",
]

ALLOWED_UNITS = {"cm", "in"}
ALLOWED_ROUNDING = {"ceil_0_5", "ceil_1", "round_0_5", "round_1"}

def base_shipments_for_user(user):
    return Shipment.objects.all() if getattr(user, "is_staff", False) else Shipment.objects.filter(profile__user=user)

def safe_select_related_shipments(qs):
    fk_names = {f.name for f in Shipment._meta.get_fields() if getattr(f, "many_to_one", False)}
    rels = [n for n in ("selected_courier", "selected_rate", "profile", "warehouse") if n in fk_names]
    return qs.select_related(*rels) if rels else qs

def _rates_accessor_name():
    reverse_rels = {
        f.get_accessor_name()
        for f in Shipment._meta.get_fields()
        if getattr(f, "auto_created", False) and not getattr(f, "concrete", True)
    }
    for cand in ("courier_selections", "rates", "shipmentrate_set"):
        if cand in reverse_rels:
            return cand
    return None

def annotate_rate_count(qs):
    accessor = _rates_accessor_name()
    if accessor:
        try:
            return qs.annotate(rate_count=Count(accessor, distinct=True))
        except Exception:
            pass
    return qs.annotate(rate_count=Value(0, output_field=IntegerField()))

def normalize_action(raw: str | None) -> str:
    if not raw:
        return ""
    raw = raw.strip().lower()
    return {
        "delevery": "hold",
        "delivery": "hold",
        "delivered": "hold",
        "deliver": "hold",
        "holde": "hold",
        "held": "hold",
    }.get(raw, raw)

def safe_redirect(request, fallback_name="customer:console_list"):
    nxt = (request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER") or "").strip()
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    try:
        return redirect(reverse(fallback_name))
    except NoReverseMatch:
        return redirect("/")

def user_is_owner(shipment: Shipment, user) -> bool:
    owner = getattr(getattr(shipment, "profile", None), "user", None)
    return bool(owner and owner == user)

def to_money_2(value) -> Decimal:
    d = Decimal(str(value or "0"))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def coerce_unit(unit: str | None) -> str:
    return unit if unit in ALLOWED_UNITS else "cm"

def coerce_rounding(rnd: str | None) -> str:
    return rnd if rnd in ALLOWED_ROUNDING else "ceil_0_5"




def home(request):
    return render(request, "customer/home.html")

def about(request):
    return render(request, "customer/about.html")


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username:
            messages.error(request, "Username is required.")
        elif len(username) < 3:
            messages.error(request, "Username must be at least 3 characters.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif not password or not confirm_password:
            messages.error(request, "Password and Confirm Password are required.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            try:
                user = User.objects.create_user(username=username, password=password)
                profile, _ = Profile.objects.get_or_create(user=user)
                custom_id_value = getattr(profile, "user_id_custom", "N/A")
                messages.success(request, f"Your User ID is {custom_id_value}")
                messages.success(request, "Account created successfully. Please login.")
                return redirect(reverse("customer:login"))
            except IntegrityError:
                messages.error(request, "Username already exists.")
    return render(request, "customer/signup.html")

def login(request):
    import logging
    logger = logging.getLogger(__name__)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            auth_login(request, user)
            # Set default membership tier to Silver if not set
            profile = getattr(user, 'profile', None)
            logger.info(f"Login: user={user.username}, profile={profile}")
            if profile and not profile.membership_tier:
                silver = MembershipTier.objects.filter(name='Silver', active=True).first()
                logger.info(f"Login: Silver tier found={silver}")
                if silver:
                    profile.membership_tier = silver
                    profile.save(update_fields=['membership_tier'])
                    logger.info(f"Login: Set Silver tier for {user.username}")
                else:
                    logger.warning(f"Login: No active Silver tier found for {user.username}")
            else:
                logger.info(f"Login: Profile has tier={profile.membership_tier if profile else None}")
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
                return redirect(next_url)
            return redirect("customer:dashbord")
        messages.error(request, "Invalid username or password.")
    return render(request, "customer/login.html")

@login_required
def dashbord(request):
    import logging
    logger = logging.getLogger(__name__)
    profile = getattr(request.user, "profile", None)
    if not profile:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        logger.info(f"Dashboard: Created profile for {request.user.username}")
    custom_id = getattr(profile, "user_id_custom", None)
    shipments = Shipment.objects.filter(profile=profile) if profile else Shipment.objects.none()
    qs = shipments
    logger.info(f"Dashboard for user {request.user.username}: shipments count {shipments.count()}, qs count {qs.count()}")
    total_shipments = shipments.count()
    in_transit = shipments.filter(selected_courier__isnull=False).count()
    delivered = shipments.filter(tracking_number__isnull=False).exclude(tracking_number='').count()
    total_spent = shipments.aggregate(total=Sum('selected_price'))['total'] or 0
    countries = Country.objects.all()
    logger.info(f"Dashboard: countries count {countries.count()}")
    for country in countries:
        logger.info(f"Country: {country.country_name}, city={country.city}, state={country.state}, zip={country.zip_code}, phone={country.phone_number}, email={country.email}")
    current_tier = profile.membership_tier if profile else None
    if profile and not current_tier:
        silver = MembershipTier.objects.filter(name='Silver', active=True).first()
        if silver:
            profile.membership_tier = silver
            profile.save(update_fields=['membership_tier'])
            current_tier = silver
            logger.info(f"Dashboard: Set Silver tier for {request.user.username}")
        else:
            logger.warning(f"Dashboard: No active Silver tier found for {request.user.username}")
    logger.info(f"Dashboard: profile={profile}, current_tier={current_tier}, custom_id={custom_id}")
    delivered_status_count = qs.filter(status__in=["delivered", "completed"]).count()
    accepted_count = qs.filter(status="accepted").count()
    logger.info(f"Counts: total_shipments={total_shipments}, in_transit={in_transit}, delivered_tracking={delivered}, delivered_status={delivered_status_count}, accepted={accepted_count}")

    return render(request, "customer/dashbord.html", {
        "custom_id": custom_id,
        "countries": countries,
        "total_shipments": total_shipments,
        "in_transit": in_transit,
        "delivered": delivered,
        "price": total_spent,
        "current_tier": current_tier,
        "delivered": qs.filter(status__in=["delivered", "completed"]).count(),
        "accepted": qs.filter(status="accepted").count(),
    })
    
@login_required
def warehouse_stats(request):
    qs = Shipment.objects.all()
    ctx = {
        "delivered": qs.filter(status="completed").count(),
        "accepted": qs.filter(status="accepted").count(),
    }
    return render(request, "customer/partials/warehouse_stats.html", ctx)    



@login_required
def shipment_create(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "Profile not found.")
        return redirect("customer:dashbord")

    if request.method == "POST":
        # For simplicity, create a basic shipment
        # In real app, use a form
        from warehouse.models import Shipment
        shipment = Shipment.objects.create(
            profile=profile,
            suit_number=f"TEMP-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            status="pending",
        )
        messages.success(request, f"Single shipment created with suit #{shipment.suit_number}.")
        return redirect("customer:shipment_detail", suit_number=shipment.suit_number)

    return render(request, "customer/shipment_create.html")
@login_required
def shipment_list(request):
    profile = getattr(request.user, "profile", None)
    shipments = Shipment.objects.filter(profile=profile) if profile else Shipment.objects.none()
    return render(request, "customer/shipment_list.html", {"shipments": shipments})








from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

# --- Assumed models (adjust imports to your app) ---
# from .models import Shipment, Courier, MembershipTier


@dataclass
class Row:
    shipment: Any
    cbm: Optional[Decimal]
    volume_weight: Optional[Decimal]
    gross_weight: Optional[Decimal]
    chargeable_weight: Optional[Decimal]
    rate: Optional[Decimal]
    price: Optional[Decimal]


# ---- Helpers ----

def _to_decimal(value: Any) -> Optional[Decimal]:
    try:
        if value is None:
            return None
        return Decimal(str(value))
    except Exception:
        return None


def compute_chargeable_weight(volume_weight: Optional[Decimal], gross_weight: Optional[Decimal]) -> Optional[Decimal]:
    if volume_weight is None and gross_weight is None:
        return None
    if volume_weight is None:
        return gross_weight
    if gross_weight is None:
        return volume_weight
    return max(volume_weight, gross_weight)


def compute_base_price(rate: Optional[Decimal], chargeable_weight: Optional[Decimal]) -> Optional[Decimal]:
    if rate is None or chargeable_weight is None:
        return None
    return (rate * chargeable_weight).quantize(Decimal("1."))


def compute_membership_prices(base_price: Optional[Decimal]) -> Dict[str, Optional[Decimal]]:
    """Return dict with silver/gold/platinum prices based on example fees.
    Silver: Basic (no extra). Gold: 10% + 8. Platinum: 25% + 15.
    Adjust to your actual business rules.
    """
    if base_price is None:
        return {"silver": None, "gold": None, "platinum": None}

    def add_fee(pct: Decimal, fixed: Decimal) -> Decimal:
        return (base_price + (base_price * pct) + fixed).quantize(Decimal("1."))

    return {
        "silver": base_price,  # assuming no fee
        "gold": add_fee(Decimal("0.10"), Decimal("8")),
        "platinum": add_fee(Decimal("0.25"), Decimal("15")),
    }


@login_required
def choose_courier_view(request: HttpRequest, suit_number: Optional[str] = None) -> HttpResponse:
    """
    Renders the "Choose Courier" page used by your template.
    - If `suit_number` points to multiple shipments, we show a table of rows.
    - If a single shipment is selected (via ?single=<pk> or only one exists), we show the detail card.
    - Handles POST from the Edit Shipment modal to update tracking_number/status.

    URL ideas:
        path("shipments/", choose_courier_view, name="customer:shipment_list")
        path("shipments/<str:suit_number>/", choose_courier_view, name="customer:shipment_detail")
    """

    # --- Replace with your actual queryset logic ---
    Shipment = _get_model_or_404("yourapp", "Shipment")

    qs = Shipment.objects.all()
    if suit_number:
        qs = qs.filter(suit_number=suit_number)

    # Fetch shipments that belong to the current user unless staff
    if not request.user.is_staff:
        qs = qs.filter(owner=request.user)

    shipments: List[Any] = list(qs.order_by("-created_at"))

    # If POST, update a shipment (from modal)
    if request.method == "POST":
        pk = request.POST.get("pk") or request.GET.get("single")
        if not pk:
            messages.error(request, "No shipment selected to update.")
            return redirect(request.path)
        target = get_object_or_404(Shipment, pk=pk)
        if not (request.user.is_staff or target.owner_id == request.user.id):
            return HttpResponseForbidden("Not allowed")
        tracking = request.POST.get("tracking_number", "").strip() or None
        status = request.POST.get("status") or target.status
        # basic assignments
        target.tracking_number = tracking
        target.status = status
        target.save(update_fields=["tracking_number", "status"])  # noqa: F405
        messages.success(request, "Shipment updated.")
        return redirect(f"{request.path}?single={target.pk}")

    # Build table rows
    rows: List[Row] = []
    for s in shipments:
        cbm = _to_decimal(getattr(s, "cbm", None))
        volume_weight = _to_decimal(getattr(s, "volume_weight", None))
        gross_weight = _to_decimal(getattr(s, "gross_weight", None))
        chargeable_weight = compute_chargeable_weight(volume_weight, gross_weight)
        rate = _to_decimal(getattr(s, "rate", None))  # per kg or unit
        price = compute_base_price(rate, chargeable_weight)
        rows.append(Row(s, cbm, volume_weight, gross_weight, chargeable_weight, rate, price))

    # Pick a single shipment
    single_pk = request.GET.get("single")
    shipment_obj: Optional[Any] = None
    if single_pk:
        shipment_obj = next((s for s in shipments if str(s.pk) == str(single_pk)), None)
        if shipment_obj is None:
            shipment_obj = get_object_or_404(Shipment, pk=single_pk)
    elif len(shipments) == 1:
        shipment_obj = shipments[0]

    # Compute detail metrics (using chosen shipment)
    cbm = volume_weight = gross_weight = chargeable_weight = rate = price = None
    selected_courier_logo = None

    if shipment_obj:
        cbm = _to_decimal(getattr(shipment_obj, "cbm", None))
        volume_weight = _to_decimal(getattr(shipment_obj, "volume_weight", None))
        gross_weight = _to_decimal(getattr(shipment_obj, "gross_weight", None))
        chargeable_weight = compute_chargeable_weight(volume_weight, gross_weight)
        rate = _to_decimal(getattr(shipment_obj, "rate", None))
        price = compute_base_price(rate, chargeable_weight)
        courier = getattr(shipment_obj, "selected_courier", None)
        if courier is not None:
            selected_courier_logo = getattr(courier, "logo_url", None)

    # Membership / pricing tiers (replace with your business logic)
    current_tier = getattr(request.user, "membership_tier", None)
    membership_prices = compute_membership_prices(price)

    context: Dict[str, Any] = {
        "suit_number": suit_number,
        "rows": rows,
        "shipment": shipment_obj,
        "cbm": cbm,
        "volume_weight": volume_weight,
        "gross_weight": gross_weight,
        "chargeable_weight": chargeable_weight,
        "rate": rate,
        "price": price,
        "current_tier": current_tier,
        "silver_price": membership_prices.get("silver"),
        "gold_price": membership_prices.get("gold"),
        "platinum_price": membership_prices.get("platinum"),
        "selected_courier_logo": selected_courier_logo,
    }

    template_name = "customer/choose_courier.html"  # point this to your cleaned template
    return render(request, template_name, context)


# --- Minimal dynamic model loader so this file doesn't crash if you paste it before models are ready ---
from django.apps import apps  # noqa: E402  (keep import at bottom for clarity)


def _get_model_or_404(app_label: str, model_name: str):  # type: ignore
    model = apps.get_model(app_label, model_name)
    if model is None:
        raise LookupError(f"Model {app_label}.{model_name} not found. Adjust imports in views.")
    return model











from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseForbidden
from django.utils.functional import cached_property

# Import your Shipment model (adjust the import path to your project)
from warehouse.models import Shipment


# --- Helper utilities -------------------------------------------------------
def coerce_unit(value):
    return value if value in ("cm", "m", "in") else "cm"


def coerce_rounding(value):
    # Accept known rounding strategies; fallback to a default
    return value if value in ("ceil_0_5", "round_2", "floor") else "ceil_0_5"


def to_money_2(value):
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except Exception:
        return None
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def has_field(model, name):
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False


def safe_select_related_shipments(qs):
    """
    Attempt to add select_related/prefetch_related only for relations that exist
    on the Shipment model. This avoids failing when a given relation doesn't exist.
    """
    related = []
    for rel in ("owner", "warehouse", "selected_courier", "selected_rate", "profile", "delivery_address", "payment"):
        if has_field(qs.model, rel):
            related.append(rel)
    if related:
        qs = qs.select_related(*related)
    # prefetch history if applicable
    if has_field(qs.model, "history"):
        qs = qs.prefetch_related("history")
    return qs


def get_shipment_owner_user_id(shipment):
    # Try common patterns for owner lookup. Returns user id or None.
    if getattr(shipment, "owner_id", None):
        return shipment.owner_id
    profile = getattr(shipment, "profile", None)
    if profile:
        return getattr(profile, "user_id", None)
    # fallback: try owner relationship object
    owner = getattr(shipment, "owner", None)
    if hasattr(owner, "id"):
        return owner.id
    return None


def compute_membership_prices(base_price, tiers=None):
    """
    Given a base_price (Decimal), return dict with keys silver_price, gold_price, platinum_price.
    If tiers dict provided (name -> {'percent_fee': Decimal, 'fixed_fee': Decimal}), use that;
    otherwise use the hardcoded fees described earlier.
    """
    if base_price is None:
        return {"silver_price": None, "gold_price": None, "platinum_price": None}

    base = Decimal(str(base_price))
    if not tiers:
        tiers = {
            "Silver": {"percent_fee": Decimal("0"), "fixed_fee": Decimal("0")},
            "Gold": {"percent_fee": Decimal("10"), "fixed_fee": Decimal("8")},
            "Platinum": {"percent_fee": Decimal("25"), "fixed_fee": Decimal("15")},
        }

    out = {}
    for name, fees in tiers.items():
        percent_amount = (base * (fees["percent_fee"] / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (base + percent_amount + fees["fixed_fee"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        key = f"{name.lower()}_price"
        out[key] = total
    return out


# # --- View ------------------------------------------------------------------
# @login_required
# def shipment_detail(request, suit_number):
#     """
#     Consolidated view that supports:
#       - multiple shipments sharing the same suit_number (renders 'rows')
#       - single shipment detail (renders 'shipment' and other context)
#     Ownership check: allow staff or owner_user for the shipments.
#     """
#     qs = safe_select_related_shipments(Shipment.objects.filter(suit_number=suit_number))

#     if not qs.exists():
#         raise Http404("No shipments found for this suit number.")

#     # Permission check based on the owner of the first shipment (suit groups usually share owner).
#     first = qs[0]
#     owner_user_id = get_shipment_owner_user_id(first)
#     if not (request.user.is_staff or (owner_user_id and owner_user_id == request.user.id)):
#         return HttpResponseForbidden("You do not have permission to view this shipment.")

#     unit = coerce_unit(request.GET.get("unit"))
#     rounding = coerce_rounding(request.GET.get("rounding"))

#     # Multiple shipments case: render rows summary
#     if qs.count() > 1:
#         rows = []
#         for s in qs:
#             try:
#                 cbm = s.cbm(unit=unit) if hasattr(s, "cbm") else None
#                 vol_w = s.volume_weight(unit=unit) if hasattr(s, "volume_weight") else None
#                 gross_w = to_money_2(getattr(s, "weight", None))
#                 charge_w = s.chargeable_weight(unit=unit, rounding=rounding) if hasattr(s, "chargeable_weight") else None

#                 if getattr(s, "selected_rate", None) and getattr(s.selected_rate, "legacy_rate", None):
#                     rate = getattr(s.selected_rate, "legacy_rate")
#                     price = getattr(s, "selected_price", None)
#                 else:
#                     # price_using_active_rate should return (rate, price)
#                     if hasattr(s, "price_using_active_rate"):
#                         rate, price = s.price_using_active_rate(unit=unit, rounding=rounding) or (None, None)
#                     else:
#                         rate = price = None

#                 price = to_money_2(price)
#             except Exception:
#                 cbm = vol_w = gross_w = charge_w = rate = price = None

#             rows.append({
#                 "shipment": s,
#                 "cbm": cbm,
#                 "volume_weight": vol_w,
#                 "gross_weight": gross_w,
#                 "chargeable_weight": charge_w,
#                 "rate": rate,
#                 "price": price,
#             })
#         return render(request, "customer/shipment_detail.html", {"suit_number": suit_number, "rows": rows})

# views.py
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.db.models import Q

from .models import Shipment  # adjust import path to your project

# helper calculators
def compute_cbm(length_inches, width_inches, height_inches):
    try:
        l = Decimal(length_inches or 0) * Decimal("2.54")  # convert inches to cm
        w = Decimal(width_inches or 0) * Decimal("2.54")
        h = Decimal(height_inches or 0) * Decimal("2.54")
    except Exception:
        return Decimal("0")
    cbm = (l * w * h) / Decimal("1000000")
    return cbm.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

def compute_volume_weight(cbm, factor=Decimal("200")):
    v = (Decimal(cbm or 0) * Decimal(factor))
    return v.quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)

@login_required
def shipment_detail(request, suit_number):
    """
    suit_number is the suit_number from the URL.
    This view finds the main shipment and any other shipments sharing the same suit_number,
    then computes cbm / volume weight / gross weight / chargeable weight either per-row
    or for the single shipment.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"shipment_detail called with suit_number: {suit_number}")

    # try pk first, then suit_number
    shipment = None
    try:
        shipment = get_object_or_404(Shipment, pk=int(suit_number))
        logger.info(f"Found shipment by pk: {shipment.pk}")
    except (ValueError, Shipment.DoesNotExist):
        shipment = get_object_or_404(Shipment, suit_number=suit_number)
        logger.info(f"Found shipment by suit_number: {shipment.suit_number}")

    # Log shipment details
    logger.info(f"Shipment: {shipment}, selected_price: {shipment.selected_price}, selected_rate: {shipment.selected_rate}")
    rate_obj, calculated_price = shipment.price_using_active_rate()
    logger.info(f"price_using_active_rate returned: rate_obj={rate_obj}, calculated_price={calculated_price}")
    if rate_obj:
        logger.info(f"Rate details: price_per_kg={rate_obj.price_per_kg}, currency={rate_obj.currency}")

    # find all shipments that belong to the same suit_number (if any)
    rows_qs = Shipment.objects.filter(suit_number=shipment.suit_number).order_by("-created_at")

    # build rows list (each row will have the shipment object + computed metrics)
    rows = []
    total_cbm = Decimal("0")
    total_gross = Decimal("0")
    for s in rows_qs:
        # adapt these attribute names if your model uses different names
        length = getattr(s, "length_cm", None) or getattr(s, "length", None) or 0
        width = getattr(s, "width_cm", None) or getattr(s, "width", None) or 0
        height = getattr(s, "height_cm", None) or getattr(s, "height", None) or 0
        gross_w = getattr(s, "weight_kg", None) or 0

        cbm = compute_cbm(length, width, height)
        vol_wt = compute_volume_weight(cbm)

        rows.append({
            "shipment": s,
            "cbm": cbm,
            "volume_weight": vol_wt,
            "gross_weight": Decimal(gross_w or 0).quantize(Decimal("0.000")),
            # per-item chargeable usually max(gross, vol); keep per-row for display
            "chargeable_weight": max(Decimal(gross_w or 0), vol_wt).quantize(Decimal("0.000")),
        })

        total_cbm += cbm
        total_gross += Decimal(gross_w or 0)

    # totals for the suit (consolidation-like totals)
    total_volume_weight = compute_volume_weight(total_cbm)
    total_chargeable = max(total_gross, total_volume_weight).quantize(Decimal("0.000"))

    # Calculate base rate and price for the shipment
    rate_obj, calculated_price = shipment.price_using_active_rate()
    rate = rate_obj.price_per_kg if rate_obj else None
    price = calculated_price

    # Use selected_price if available to prevent price changes (it's the locked price after discounts)
    if shipment.selected_price:
        price = shipment.selected_price
        logger.info(f"Using selected_price for shipment detail: {price}")
    else:
        # Apply plan discount if active membership to the calculated price
        profile = getattr(request.user, "profile", None)
        active_membership = request.user.memberships.filter(status="active").first()
        current_tier = profile.membership_tier if profile else None
        logger.info(f"Shipment detail: user={request.user.username}, profile={profile}, current_tier={current_tier}, active_membership={active_membership}, calculated_price={calculated_price}")
        if active_membership and price:
            discount_rate = active_membership.plan.get_discount_rate()
            if discount_rate > 0:
                price = price * (Decimal("1") - discount_rate)
                price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                logger.info(f"Applied plan discount {discount_rate*100}% to shipment detail price: {price}")
        else:
            logger.info(f"No active membership or no price to discount: active_membership={active_membership}, price={price}")
        logger.info(f"Using calculated price with discounts for shipment detail: {price}")

    # Add current_tier to context for template
    profile = getattr(request.user, "profile", None)
    current_tier = profile.membership_tier if profile else None
    logger.info(f"Shipment detail context: profile={profile}, current_tier={current_tier}")

    # If only one shipment exists, the template expects cbm/volume_weight/gross_weight/chargeable_weight as scalars:
    context = {
        "shipment": shipment,
        "rows": rows if len(rows) > 1 else None,
        "cbm": rows[0]["cbm"] if len(rows) == 1 else None,
        "volume_weight": rows[0]["volume_weight"] if len(rows) == 1 else None,
        "gross_weight": rows[0]["gross_weight"] if len(rows) == 1 else None,
        "chargeable_weight": rows[0]["chargeable_weight"] if len(rows) == 1 else None,
        "rate": rate,
        "price": price,
        "current_tier": current_tier,
        # totals (always present)
        "total_cbm": total_cbm.quantize(Decimal("0.000001")),
        "total_volume_weight": total_volume_weight,
        "total_gross_weight": total_gross.quantize(Decimal("0.000")),
        "total_chargeable_weight": total_chargeable,
    }

    logger.info(f"Context rate: {rate}, price: {price}")

    return render(request, "customer/shipment_detail.html", context)








    # Single shipment case: provide detailed context
    shipment = qs.first()
    try:
        cbm = shipment.cbm(unit=unit) if hasattr(shipment, "cbm") else None
        vol_w = shipment.volume_weight(unit=unit) if hasattr(shipment, "volume_weight") else None
        gross_w = to_money_2(getattr(shipment, "weight", None))
        charge_w = shipment.chargeable_weight(unit=unit, rounding=rounding) if hasattr(shipment, "chargeable_weight") else None

        if getattr(shipment, "selected_rate", None) and getattr(shipment.selected_rate, "legacy_rate", None):
            rate = getattr(shipment.selected_rate, "legacy_rate")
            price = getattr(shipment, "selected_price", None)
        else:
            if hasattr(shipment, "price_using_active_rate"):
                rate, price = shipment.price_using_active_rate(unit=unit, rounding=rounding) or (None, None)
            else:
                rate = price = None

        price = to_money_2(price)

    except Exception:
        cbm = vol_w = gross_w = charge_w = rate = price = None

    # Compute membership-tier based prices (if you want to show them). This uses base price if available.
    membership_prices = compute_membership_prices(price)

    # Attempt to get courier logo (if your model has a logo/url). Fallback None.
    selected_courier_logo = None
    if getattr(shipment, "selected_courier", None):
        selected_courier_logo = getattr(shipment.selected_courier, "logo_url", None) or getattr(shipment.selected_courier, "logo", None)

    context = {
        "shipment": shipment,
        "cbm": cbm,
        "volume_weight": vol_w,
        "gross_weight": gross_w,
        "chargeable_weight": charge_w,
        "rate": rate,
        "price": price,
        "selected_courier_logo": selected_courier_logo,
        # membership context expected by template
        "current_tier": getattr(request.user, "membership_tier", None),
        "silver_price": membership_prices.get("silver_price"),
        "gold_price": membership_prices.get("gold_price"),
        "platinum_price": membership_prices.get("platinum_price"),
    }

    return render(request, "customer/shipment_detail.html", context)




from decimal import Decimal, ROUND_HALF_UP, getcontext
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

MONEY_Q = Decimal("0.01")

def _to_decimal(val) -> Decimal:
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(0)

def _chargeable_weight(shipment) -> Decimal:
    try:
        return _to_decimal(shipment.chargeable_weight(unit="cm"))
    except Exception:
        return _to_decimal(
            getattr(shipment, "weight_kg", None)
            or getattr(shipment, "weight", 0)
            or 0
        )

def _quantize_money(amount: Decimal) -> Decimal:
    return (amount or Decimal(0)).quantize(MONEY_Q, rounding=ROUND_HALF_UP)

def _user_is_owner(shipment, user) -> bool:
    owner = getattr(getattr(shipment, "profile", None), "user", None)
    return bool(owner and owner == user)

@login_required
def shipment_rates(request, shipment_id: int):
    """
    GET  -> list active courier options (name, logo, computed price, tier prices)
    POST -> persist selection, create history + staff notification, then redirect
    """
    # prefetch what we actually use
    qs = (Shipment.objects
          .select_related("selected_courier", "selected_rate")
          .all())
    shipment = get_object_or_404(qs, pk=shipment_id)

    if not (request.user.is_staff or _user_is_owner(shipment, request.user)):
        return HttpResponseForbidden("You do not have permission to change this shipment.")

    chargeable = _chargeable_weight(shipment)

    # membership / tier
    profile = getattr(request.user, "profile", None)
    current_tier = getattr(profile, "membership_tier", None)
    user_tier = (current_tier.name.lower() if current_tier and current_tier.name else None)

    # DEBUG: Log membership info
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User {request.user.username}: profile={profile}, current_tier={current_tier}, user_tier={user_tier}")

    # Check active membership and plan
    active_membership = request.user.memberships.filter(status="active").first()
    if active_membership:
        plan_discount = active_membership.plan.get_discount_rate()
        logger.info(f"Active membership: {active_membership}, plan={active_membership.plan.name}, discount_rate={plan_discount}")
    else:
        logger.info("No active membership found")

    show_other_plans = (user_tier == "silver")
    other_tiers_qs = []
    if show_other_plans:
        other_tiers_qs = (MembershipTier.objects
                          .filter(active=True)
                          .exclude(name__iexact="silver")
                          .order_by("ordering"))

    if request.method == "POST":
        rate_id = (request.POST.get("rate_id") or "").strip()
        if not rate_id:
            messages.error(request, "Please select a courier option.")
            return redirect("customer:shipment_rates", shipment_id=shipment.id)

        rate = (CourierRate.objects
                .select_related("courier")
                .filter(pk=rate_id, active=True)
                .first())
        if not rate:
            messages.error(request, "Selected rate is not available.")
            return redirect("customer:shipment_rates", shipment_id=shipment.id)

        base_price = _to_decimal(rate.price_for_weight(chargeable))
        base_price = _quantize_money(base_price)
        logger.info(f"Base price: {base_price}, chargeable: {chargeable}")

        final_price = base_price

        # Apply plan discount from active membership
        if active_membership:
            discount_rate = active_membership.plan.get_discount_rate()
            if discount_rate > 0:
                discounted_price = base_price * (Decimal("1") - discount_rate)
                final_price = _quantize_money(discounted_price)
                logger.info(f"Applied plan discount: {discount_rate*100}%, final_price: {final_price}")

        # Then apply MembershipTier fees if any
        if current_tier:
            fee_dict = current_tier.calculate_fee(final_price)
            final_price = _quantize_money(fee_dict.get("total_cost", final_price))
            logger.info(f"Applied tier fees: {current_tier.name}, fee_dict: {fee_dict}, final_price: {final_price}")
        else:
            logger.info("No current_tier fees applied")

        with transaction.atomic():
            # lock shipment row to avoid double-submit races
            s = Shipment.objects.select_for_update().get(pk=shipment.pk)

            # map to warehouse courier (if your domain requires this)
            warehouse_courier = None
            try:
                from warehouse.models import Courier as WarehouseCourier
                warehouse_courier, _ = WarehouseCourier.objects.get_or_create(
                    name=rate.courier.name
                )
            except Exception:
                # fall back to selecting the original courier
                warehouse_courier = getattr(rate, "courier", None)

            # create CourierSelection history (best-effort)
            cs = None
            try:
                from warehouse.models import CourierSelection as WHCourierSelection
                cs = WHCourierSelection.objects.create(
                    shipment=s,
                    courier=warehouse_courier,
                    legacy_rate=rate,  # keep legacy link if your model expects it
                    total_price=final_price,
                    currency=rate.currency,
                    chosen_by=request.user,
                )
            except Exception:
                pass

            s.selected_courier = warehouse_courier or rate.courier
            s.selected_rate = cs  # assign the CourierSelection instance
            s.selected_price = final_price
            s.save(update_fields=["selected_courier", "selected_rate", "selected_price"])

        # staff notification (best-effort)
        try:
            from warehouse.models import StaffNotification
            StaffNotification.objects.create(
                type="courier_selected",
                shipment=shipment,
                text=f"{request.user.username} selected {rate.courier.name} "
                     f"for suit {shipment.suit_number or ('#' + str(shipment.id))} "
                     f"at {to_money_2(final_price)} {rate.currency}",
            )
        except Exception:
            pass

        messages.success(request, f"Courier saved: {rate.courier.name} — {final_price} {rate.currency}.")
        return redirect("customer:address_create", shipment_id=shipment.id)

    # GET — build rate table
    rows = []
    rates_qs = (CourierRate.objects
                .filter(active=True)
                .select_related("courier")
                .order_by("courier__name", "id"))

    for r in rates_qs:
        # defensive logo access
        try:
            logo_url = r.courier.logo.url if getattr(r.courier, "logo", None) else None
        except Exception:
            logo_url = None

        price = _quantize_money(_to_decimal(r.price_for_weight(chargeable)))

        # current user tier price
        tier_price = price
        if current_tier:
            fee_dict = current_tier.calculate_fee(price)
            tier_price = _quantize_money(fee_dict.get("total_cost", price))

        # other plan comparisons for silver
        other_prices = []
        if show_other_plans:
            for ot in other_tiers_qs:
                ot_fee = ot.calculate_fee(price)
                ot_total = _quantize_money(ot_fee.get("total_cost", price))
                discount = _quantize_money(price - ot_total)
                other_prices.append({
                    "name": ot.name,
                    "price": ot_total,
                    "discount": discount,
                    "currency": getattr(ot, "currency", r.currency),
                })

        rows.append({
            "rate_id": r.id,
            "courier_name": r.courier.name,
            "currency": r.currency,
            "price": price,            # base price
            "tier_price": tier_price,  # after current tier fee
            "logo_url": logo_url,
            "min_charge": r.min_charge,
            "price_per_kg": r.price_per_kg,
            "other_prices": other_prices,
        })

    return render(request, "customer/shipment_rates.html", {
        "shipment": shipment,
        "chargeable_weight": chargeable,
        "rates": rows,
        "user_tier": user_tier,
        "current_tier": current_tier,
        "show_other_plans": show_other_plans,
        "other_tiers": list(other_tiers_qs),
    })
 


@login_required
def shipment_success(request):
    return render(request, "customer/shipment_success.html")    



@login_required
def customer_shipment_photos(request, suit_number):
    shipment = resolve_shipment_by_suit_latest(request, suit_number)
    photos = (
        ShipmentImage.objects
        .filter(shipment=shipment)
        .order_by(F("captured_at").desc(nulls_last=True), "-pk")
    )
    return render(request, "customer/shipment_photos.html", {"shipment": shipment, "photos": photos})




@login_required
def purchase_list(request):
    purchases = PurchaseBill.objects.all().order_by("-date")
    return render(request, "customer/purchase_list.html", {"purchases": purchases})

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(PurchaseBill, pk=pk)
    return render(request, "customer/purchase_detail.html", {"purchase": purchase})

@login_required
def purchase_create(request):
    if request.method == "POST":
        form = PurchaseBillForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Purchase bill created.")
            return redirect("customer:purchase_list")
    else:
        form = PurchaseBillForm()
    return render(request, "customer/purchase_form.html", {"form": form})

@login_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(PurchaseBill, pk=pk)
    old_file_path = purchase.pdf.path if purchase.pdf else None

    if request.method == "POST":
        form = PurchaseBillForm(request.POST, request.FILES, instance=purchase)
        if form.is_valid():
            new_pdf = request.FILES.get("pdf")
            form.save()
            if new_pdf and old_file_path and os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception:
                    pass
            messages.success(request, "Purchase bill updated.")
            return redirect("customer:purchase_detail", pk=purchase.pk)
    else:
        form = PurchaseBillForm(instance=purchase)
    return render(request, "customer/purchase_form.html", {"form": form, "purchase": purchase})






# customer/views_membership.py
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .models import  MembershipTier
from .forms import MembershipApplicationForm, SelectMembershipForm, SubscriptionForm
from .models import MembershipApplication

logger = logging.getLogger(__name__)

@login_required
def membership_manage(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "Profile not found.")
        return redirect(reverse("customer:dashbord"))

    current_tier = profile.membership_tier
    tiers = MembershipTier.objects.filter(active=True).order_by("ordering", "name")

    # Handle plan selection via GET parameter
    plan_name = request.GET.get("plan")
    if plan_name:
        selected_tier = tiers.filter(name__iexact=plan_name).first()
        if selected_tier:
            # if already on that tier, chill
            if current_tier and current_tier.id == selected_tier.id:
                messages.info(request, f"You're already on {selected_tier.name}.")
                return redirect(reverse("customer:membership_manage"))

            # set new tier
            profile.membership_tier = selected_tier
            profile.save(update_fields=["membership_tier"])
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Updated membership tier for {request.user.username} to {selected_tier.name}")
            messages.success(request, f"Switched to {selected_tier.name}.")
            return redirect(reverse("customer:membership_manage"))
        else:
            messages.error(request, f"Invalid plan: {plan_name}.")
            return redirect(reverse("customer:membership_manage"))

    # For POST (if needed, though template uses GET)
    if request.method == "POST":
        form = SelectMembershipForm(request.POST)
        if form.is_valid():
            tier = form.cleaned_data["tier"]
            # if already on that tier, chill
            if current_tier and current_tier.id == tier.id:
                messages.info(request, f"You're already on {tier.name}.")
                return redirect(reverse("customer:membership_manage"))

            # set new tier
            profile.membership_tier = tier
            profile.save(update_fields=["membership_tier"])
            messages.success(request, f"Switched to {tier.name}.")
            return redirect(reverse("customer:membership_manage"))
    else:
        form = SelectMembershipForm()

    return render(request, "customer/membership_manage.html", {
        "current_tier": current_tier,
        "tiers": tiers,
        "form": form,
    })

@login_required
def membership_cancel(request):
    current = (request.user.memberships
               .select_related("plan")
               .filter(status="active")
               .first())
    if not current:
        messages.info(request, "No active membership to cancel.")
        return redirect(reverse("customer:membership_manage"))
    if request.method == "POST":
        current.cancel()
        messages.success(request, "Membership canceled.")
        return redirect(reverse("customer:membership_manage"))
@login_required
def subscribe(request):
    plan = request.GET.get('plan', 'silver')
    tiers = MembershipTier.objects.filter(active=True).order_by("ordering", "name")
    selected_tier = tiers.filter(name__iexact=plan).first()
    plan_price = {'silver': 9, 'gold': 29, 'platinum': 79}.get(plan.lower(), 9)

    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            # Simulate payment processing
            payment_method = form.cleaned_data['payment']
            if payment_method == 'card':
                # In real app, integrate with Stripe or similar
                # For now, assume payment succeeds
                pass
            elif payment_method == 'paypal':
                # Redirect to PayPal
                pass

            # Get the selected tier
            plan_name = form.cleaned_data['plan']
            tier = MembershipTier.objects.filter(name__iexact=plan_name, active=True).first()
            if not tier:
                messages.error(request, "Invalid plan selected.")
                return redirect('customer:subscribe')

            # Set the membership tier for the user
            profile = getattr(request.user, 'profile', None)
            if profile:
                profile.membership_tier = tier
                profile.save(update_fields=['membership_tier'])
                logger.info(f"User {request.user.username} subscribed to {tier.name} via subscribe view")
            else:
                logger.error(f"User {request.user.username} has no profile to set membership_tier in subscribe")

            # Optionally, create a Plan and Membership if needed
            # For now, just set the tier

            messages.success(request, f"Successfully subscribed to {tier.name} plan!")
            return redirect('customer:membership_manage')
    else:
        form = SubscriptionForm()
        form.initial['plan'] = plan

    return render(request, "customer/subscribeform.html", {
        'form': form,
        'selected_plan': plan,
        'selected_tier': selected_tier,
        'plan_price': plan_price,
        'tiers': tiers
    })

@login_required
def membership_cancel(request):
    current = (request.user.memberships
               .select_related("plan")
               .filter(status="active")
               .first())
    if not current:
        messages.info(request, "No active membership to cancel.")
        return redirect(reverse("customer:membership_manage"))
    if request.method == "POST":
        current.cancel()
        messages.success(request, "Membership canceled.")
        return redirect(reverse("customer:membership_manage"))
    return render(request, "customer/membership_cancel_confirm.html", {"current": current})

@login_required
def membership_application(request):
    # Check if user already has a pending application
    existing = MembershipApplication.objects.filter(user=request.user, status="pending").first()
    if existing:
        messages.info(request, "You already have a pending membership application.")
        return redirect(reverse("customer:membership_manage"))

    if request.method == "POST":
        form = MembershipApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            messages.success(request, "Membership application submitted successfully.")
            return redirect(reverse("customer:membership_manage"))
    else:
        form = MembershipApplicationForm()
    return render(request, "customer/membership_application_form.html", {"form": form})

@login_required
def membership_cancel_confirm(request):
    current = (request.user.memberships
               .select_related("plan")
               .filter(status="active")
               .first())
    if not current:
        messages.info(request, "No active membership to cancel.")
        return redirect(reverse("customer:membership_manage"))
    return render(request, "customer/membership_cancel_confirm.html", {"current": current})







from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Shipment, DeliveryAddress, Payment
from warehouse.models import ShipmentStatusHistory
from .forms import DeliveryAddressForm, PaymentForm
from django.utils import timezone

# replace this stub with real payment integration
def _process_payment_stub(amount: Decimal, currency: str, method: str, card_token: str = "") -> dict:
    """
    Simulate payment processing. Replace with Stripe/PayPal SDK in production.
    Returns dict: {"success": True/False, "provider": "demo", "reference": "txn_123"}
    """
    # Demo logic: accept any non-empty card_token when method == 'card'
    if method == "card":
        if not card_token:
            return {"success": False, "error": "Missing card token"}
        return {"success": True, "provider": "demo", "reference": f"demo_txn_{timezone.now().strftime('%Y%m%d%H%M%S')}"}
    else:
        # offline: mark pending and ask admin to reconcile
        return {"success": True, "provider": "offline", "reference": f"offline_{timezone.now().strftime('%Y%m%d%H%M%S')}"} 


def _user_is_owner(shipment: Shipment, user):
    owner = getattr(getattr(shipment, "profile", None), "user", None)
    return bool(owner and owner == user)

@login_required
def address_create_for_shipment(request, shipment_id: int):
    qs = Shipment.objects.select_related("owner", "courier").all()
    shipment = get_object_or_404(qs, pk=shipment_id)

    if not (request.user.is_staff or _user_is_owner(shipment, request.user)):
        return HttpResponseForbidden("You do not have permission to edit this shipment.")

    if request.method == "POST":
        form = DeliveryAddressForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                # create / update delivery address
                addr, created = DeliveryAddress.objects.update_or_create(
                    shipment=shipment,
                    defaults={
                        "recipient_name": data["recipient_name"],
                        "address_line1": data["address_line1"],
                        "address_line2": data["address_line2"],
                        "city": data["city"],
                        "state": data["state"],
                        "postal_code": data["postal_code"],
                        "country": data["country"],
                        "phone": data["phone"],
                    },
                )

                # Update shipment status to waiting for payment
                shipment.status = Shipment.STATUS_PENDING  # or a dedicated STATUS_AWAITING_PAYMENT if you have it
                shipment.updated_at = timezone.now()
                shipment.save(update_fields=["status", "updated_at"])

                # Optional: create history entry
                ShipmentStatusHistory.objects.create(
                    shipment=shipment,
                    status="address_provided",
                    message="Customer provided delivery address",
                    raw_payload={"address_id": addr.pk},
                    created_at=timezone.now(),
                )

            # proceed to payment step
            return redirect("customer:payment_process", shipment_id=shipment.pk)
    else:
        # prefill from existing address or user profile if you have one
        initial = {}
        if hasattr(shipment, "delivery_address") and shipment.delivery_address:
            a = shipment.delivery_address
            initial = {
                "recipient_name": a.recipient_name,
                "address_line1": a.address_line1,
                "address_line2": a.address_line2,
                "city": a.city,
                "state": a.state,
                "postal_code": a.postal_code,
                "country": a.country,
                "phone": a.phone,
            }
        else:
            profile = getattr(request.user, "profile", None)
            if profile:
                initial = {
                    "recipient_name": getattr(profile, "full_name", request.user.get_full_name() or request.user.username),
                    "phone": getattr(profile, "phone", ""),
                    # you can map other profile fields if available
                }

        form = DeliveryAddressForm(initial=initial)

    return render(request, "customer/address_create.html", {"form": form, "shipment": shipment})


@login_required
def payment_process(request, shipment_id: int):
    qs = Shipment.objects.select_related("owner", "courier").all()
    shipment = get_object_or_404(qs, pk=shipment_id)

    if not (request.user.is_staff or _user_is_owner(shipment, request.user)):
        return HttpResponseForbidden("You do not have permission to pay for this shipment.")

    # determine amount: prefer the selected_price saved earlier
    amount = getattr(shipment, "selected_price", None)
    currency = getattr(shipment, "selected_rate", None) and getattr(shipment.selected_rate, "currency", "USD")
    if amount is None:
        # fallback to a base price or error
        messages.error(request, "No price found for this shipment. Please select a courier first.")
        return redirect("customer:shipment_rates", shipment_id=shipment.pk)

    # ensure there's a payment row (pending) so admin can reconcile offline payments if needed
    payment_obj, _ = Payment.objects.get_or_create(
        shipment=shipment,
        defaults={"amount": amount, "currency": currency or "USD", "status": Payment.STATUS_PENDING},
    )

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data["payment_method"]
            card_token = form.cleaned_data.get("card_token", "")
            # process payment (replace this with real provider call)
            result = _process_payment_stub(amount, payment_obj.currency, method, card_token)
            if result.get("success"):
                # mark payment success
                payment_obj.amount = amount
                payment_obj.currency = payment_obj.currency or "USD"
                payment_obj.provider = result.get("provider", "")
                payment_obj.provider_reference = result.get("reference", "")
                payment_obj.mark_success(provider_reference=payment_obj.provider_reference)
                logger.info(f"Payment marked success for shipment {shipment.suit_number}, payment status: {payment_obj.status}")

                # update shipment status to accepted/shipped depending on your flow
                shipment.status = Shipment.STATUS_ACCEPTED
                shipment.updated_at = timezone.now()
                shipment.save(update_fields=["status", "updated_at"])
                logger.info(f"Shipment {shipment.suit_number} status updated to {shipment.status}")

                # create history event
                ShipmentStatusHistory.objects.create(
                    shipment=shipment,
                    status="paid",
                    message=f"Payment received ({payment_obj.provider})",
                    raw_payload={"payment_id": payment_obj.pk, "provider_ref": payment_obj.provider_reference},
                    created_at=timezone.now(),
                )

                messages.success(request, "Payment successful. Your shipment is being processed.")
                return redirect("customer:shipment_detail", shipment.suit_number)
            else:
                # record failure and show error
                payment_obj.mark_failed(provider_reference=result.get("reference", ""))
                messages.error(request, f"Payment failed: {result.get('error', 'Unknown error')}")
    else:
        form = PaymentForm(initial={"billing_name": request.user.get_full_name()})

    return render(request, "customer/payment_process.html", {
        "form": form,
        "shipment": shipment,
        "payment": payment_obj,
        "amount": amount,
        "currency": payment_obj.currency or "USD",
    })
    





# --- Assumed models (adjust imports to your app) ---
# from .models import Shipment, Courier, MembershipTier


@dataclass
class Row:
    shipment: Any
    cbm: Optional[Decimal]
    volume_weight: Optional[Decimal]
    gross_weight: Optional[Decimal]
    chargeable_weight: Optional[Decimal]
    rate: Optional[Decimal]
    price: Optional[Decimal]


# ---- Helpers ----

def _to_decimal(value: Any) -> Optional[Decimal]:
    try:
        if value is None:
            return None
        return Decimal(str(value))
    except Exception:
        return None


def compute_chargeable_weight(volume_weight: Optional[Decimal], gross_weight: Optional[Decimal]) -> Optional[Decimal]:
    if volume_weight is None and gross_weight is None:
        return None
    if volume_weight is None:
        return gross_weight
    if gross_weight is None:
        return volume_weight
    return max(volume_weight, gross_weight)


def compute_base_price(rate: Optional[Decimal], chargeable_weight: Optional[Decimal]) -> Optional[Decimal]:
    if rate is None or chargeable_weight is None:
        return None
    return (rate * chargeable_weight).quantize(Decimal("1."))


def compute_membership_prices(base_price: Optional[Decimal]) -> Dict[str, Optional[Decimal]]:
    """Return dict with silver/gold/platinum prices based on example fees.
    Silver: Basic (no extra). Gold: 10% + 8. Platinum: 25% + 15.
    Adjust to your actual business rules.
    """
    if base_price is None:
        return {"silver": None, "gold": None, "platinum": None}

    def add_fee(pct: Decimal, fixed: Decimal) -> Decimal:
        return (base_price + (base_price * pct) + fixed).quantize(Decimal("1."))

    return {
        "silver": base_price,  # assuming no fee
        "gold": add_fee(Decimal("0.10"), Decimal("8")),
        "platinum": add_fee(Decimal("0.25"), Decimal("15")),
    }


@login_required
def choose_courier_view(request: HttpRequest, suit_number: Optional[str] = None) -> HttpResponse:
    """
    Renders the "Choose Courier" page used by your template.
    - If `suit_number` points to multiple shipments, we show a table of rows.
    - If a single shipment is selected (via ?single=<pk> or only one exists), we show the detail card.
    - Handles POST from the Edit Shipment modal to update tracking_number/status.

    URL ideas:
        path("shipments/", choose_courier_view, name="customer:shipment_list")
        path("shipments/<str:suit_number>/", choose_courier_view, name="customer:shipment_detail")
    """

    # --- Replace with your actual queryset logic ---
    Shipment = _get_model_or_404("yourapp", "Shipment")

    qs = Shipment.objects.all()
    if suit_number:
        qs = qs.filter(suit_number=suit_number)

    # Fetch shipments that belong to the current user unless staff
    if not request.user.is_staff:
        qs = qs.filter(owner=request.user)

    shipments: List[Any] = list(qs.order_by("-created_at"))

    # If POST, update a shipment (from modal)
    if request.method == "POST":
        pk = request.POST.get("pk") or request.GET.get("single")
        if not pk:
            messages.error(request, "No shipment selected to update.")
            return redirect(request.path)
        target = get_object_or_404(Shipment, pk=pk)
        if not (request.user.is_staff or target.owner_id == request.user.id):
            return HttpResponseForbidden("Not allowed")
        tracking = request.POST.get("tracking_number", "").strip() or None
        status = request.POST.get("status") or target.status
        # basic assignments
        target.tracking_number = tracking
        target.status = status
        target.save(update_fields=["tracking_number", "status"])  # noqa: F405
        messages.success(request, "Shipment updated.")
        return redirect(f"{request.path}?single={target.pk}")

    # Build table rows
    rows: List[Row] = []
    for s in shipments:
        cbm = _to_decimal(getattr(s, "cbm", None))
        volume_weight = _to_decimal(getattr(s, "volume_weight", None))
        gross_weight = _to_decimal(getattr(s, "weight_kg", None))
        chargeable_weight = compute_chargeable_weight(volume_weight, gross_weight)
        rate = _to_decimal(getattr(s, "rate", None))  # per kg or unit
        price = compute_base_price(rate, chargeable_weight)
        rows.append(Row(s, cbm, volume_weight, gross_weight, chargeable_weight, rate, price))

    # Pick a single shipment
    single_pk = request.GET.get("single")
    shipment_obj: Optional[Any] = None
    if single_pk:
        shipment_obj = next((s for s in shipments if str(s.pk) == str(single_pk)), None)
        if shipment_obj is None:
            shipment_obj = get_object_or_404(Shipment, pk=single_pk)
    elif len(shipments) == 1:
        shipment_obj = shipments[0]

    # Compute detail metrics (using chosen shipment)
    cbm = volume_weight = gross_weight = chargeable_weight = rate = price = None
    selected_courier_logo = None

    if shipment_obj:
        cbm = _to_decimal(getattr(shipment_obj, "cbm", None))
        volume_weight = _to_decimal(getattr(shipment_obj, "volume_weight", None))
        gross_weight = _to_decimal(getattr(shipment_obj, "weight_kg", None))
        chargeable_weight = compute_chargeable_weight(volume_weight, gross_weight)
        rate = _to_decimal(getattr(shipment_obj, "rate", None))
        price = compute_base_price(rate, chargeable_weight)
        courier = getattr(shipment_obj, "selected_courier", None)
        if courier is not None:
            selected_courier_logo = getattr(courier, "logo_url", None)

    # Membership / pricing tiers (replace with your business logic)
    current_tier = getattr(request.user, "membership_tier", None)
    membership_prices = compute_membership_prices(price)

    context: Dict[str, Any] = {
        "suit_number": suit_number,
        "rows": rows,
        "shipment": shipment_obj,
        "cbm": cbm,
        "volume_weight": volume_weight,
        "gross_weight": gross_weight,
        "chargeable_weight": chargeable_weight,
        "rate": rate,
        "price": price,
        "current_tier": current_tier,
        "silver_price": membership_prices.get("silver"),
        "gold_price": membership_prices.get("gold"),
        "platinum_price": membership_prices.get("platinum"),
        "selected_courier_logo": selected_courier_logo,
    }

    template_name = "customer/choose_courier.html"  # point this to your cleaned template
    return render(request, template_name, context)


# --- Minimal dynamic model loader so this file doesn't crash if you paste it before models are ready ---
from django.apps import apps  # noqa: E402  (keep import at bottom for clarity)


def _get_model_or_404(app_label: str, model_name: str):  # type: ignore
    model = apps.get_model(app_label, model_name)
    if model is None:
        raise LookupError(f"Model {app_label}.{model_name} not found. Adjust imports in views.")
    return model






from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

# --- Assumed models (adjust imports to your app) ---
# from .models import Shipment, Courier, MembershipTier


@dataclass
class Row:
    shipment: Any
    cbm: Optional[Decimal]
    volume_weight: Optional[Decimal]
    gross_weight: Optional[Decimal]
    chargeable_weight: Optional[Decimal]
    rate: Optional[Decimal]
    price: Optional[Decimal]


# ---- Helpers ----

def _to_decimal(value: Any) -> Optional[Decimal]:
    try:
        if value is None:
            return None
        return Decimal(str(value))
    except Exception:
        return None


def compute_chargeable_weight(volume_weight: Optional[Decimal], gross_weight: Optional[Decimal]) -> Optional[Decimal]:
    if volume_weight is None and gross_weight is None:
        return None
    if volume_weight is None:
        return gross_weight
    if gross_weight is None:
        return volume_weight
    return max(volume_weight, gross_weight)


def compute_base_price(rate: Optional[Decimal], chargeable_weight: Optional[Decimal]) -> Optional[Decimal]:
    if rate is None or chargeable_weight is None:
        return None
    return (rate * chargeable_weight).quantize(Decimal("1."))


def compute_membership_prices(base_price: Optional[Decimal]) -> Dict[str, Optional[Decimal]]:
    """Return dict with silver/gold/platinum prices based on example fees.
    Silver: Basic (no extra). Gold: 10% + 8. Platinum: 25% + 15.
    Adjust to your actual business rules.
    """
    if base_price is None:
        return {"silver": None, "gold": None, "platinum": None}

    def add_fee(pct: Decimal, fixed: Decimal) -> Decimal:
        return (base_price + (base_price * pct) + fixed).quantize(Decimal("1."))

    return {
        "silver": base_price,  # assuming no fee
        "gold": add_fee(Decimal("0.10"), Decimal("8")),
        "platinum": add_fee(Decimal("0.25"), Decimal("15")),
    }


@login_required
def choose_courier_view(request: HttpRequest, suit_number: Optional[str] = None) -> HttpResponse:
    """
    Renders the "Choose Courier" page used by your template.
    - If `suit_number` points to multiple shipments, we show a table of rows.
    - If a single shipment is selected (via ?single=<pk> or only one exists), we show the detail card.
    - Handles POST from the Edit Shipment modal to update tracking_number/status.

    URL ideas:
        path("shipments/", choose_courier_view, name="customer:shipment_list")
        path("shipments/<str:suit_number>/", choose_courier_view, name="customer:shipment_detail")
    """

    # --- Replace with your actual queryset logic ---
    Shipment = _get_model_or_404("yourapp", "Shipment")

    qs = Shipment.objects.all()
    if suit_number:
        qs = qs.filter(suit_number=suit_number)

    # Fetch shipments that belong to the current user unless staff
    if not request.user.is_staff:
        qs = qs.filter(owner=request.user)

    shipments: List[Any] = list(qs.order_by("-created_at"))

    # If POST, update a shipment (from modal)
    if request.method == "POST":
        pk = request.POST.get("pk") or request.GET.get("single")
        if not pk:
            messages.error(request, "No shipment selected to update.")
            return redirect(request.path)
        target = get_object_or_404(Shipment, pk=pk)
        if not (request.user.is_staff or target.owner_id == request.user.id):
            return HttpResponseForbidden("Not allowed")
        tracking = request.POST.get("tracking_number", "").strip() or None
        status = request.POST.get("status") or target.status
        # basic assignments
        target.tracking_number = tracking
        target.status = status
        target.save(update_fields=["tracking_number", "status"])  # noqa: F405
        messages.success(request, "Shipment updated.")
        return redirect(f"{request.path}?single={target.pk}")

    # Build table rows
    rows: List[Row] = []
    for s in shipments:
        cbm = _to_decimal(getattr(s, "cbm", None))
        volume_weight = _to_decimal(getattr(s, "volume_weight", None))
        gross_weight = _to_decimal(getattr(s, "gross_weight", None))
        chargeable_weight = compute_chargeable_weight(volume_weight, gross_weight)
        rate = _to_decimal(getattr(s, "rate", None))  # per kg or unit
        price = compute_base_price(rate, chargeable_weight)
        rows.append(Row(s, cbm, volume_weight, gross_weight, chargeable_weight, rate, price))

    # Pick a single shipment
    single_pk = request.GET.get("single")
    shipment_obj: Optional[Any] = None
    if single_pk:
        shipment_obj = next((s for s in shipments if str(s.pk) == str(single_pk)), None)
        if shipment_obj is None:
            shipment_obj = get_object_or_404(Shipment, pk=single_pk)
    elif len(shipments) == 1:
        shipment_obj = shipments[0]

    # Compute detail metrics (using chosen shipment)
    cbm = volume_weight = gross_weight = chargeable_weight = rate = price = None
    selected_courier_logo = None

    if shipment_obj:
        cbm = _to_decimal(getattr(shipment_obj, "cbm", None))
        volume_weight = _to_decimal(getattr(shipment_obj, "volume_weight", None))
        gross_weight = _to_decimal(getattr(shipment_obj, "gross_weight", None))
        chargeable_weight = compute_chargeable_weight(volume_weight, gross_weight)
        rate = _to_decimal(getattr(shipment_obj, "rate", None))
        price = compute_base_price(rate, chargeable_weight)
        courier = getattr(shipment_obj, "selected_courier", None)
        if courier is not None:
            selected_courier_logo = getattr(courier, "logo_url", None)

    # Membership / pricing tiers (replace with your business logic)
    current_tier = getattr(request.user, "membership_tier", None)
    membership_prices = compute_membership_prices(price)

    context: Dict[str, Any] = {
        "suit_number": suit_number,
        "rows": rows,
        "shipment": shipment_obj,
        "cbm": cbm,
        "volume_weight": volume_weight,
        "gross_weight": gross_weight,
        "chargeable_weight": chargeable_weight,
        "rate": rate,
        "price": price,
        "current_tier": current_tier,
        "silver_price": membership_prices.get("silver"),
        "gold_price": membership_prices.get("gold"),
        "platinum_price": membership_prices.get("platinum"),
        "selected_courier_logo": selected_courier_logo,
    }

    template_name = "customer/choose_courier.html"  # point this to your cleaned template
    return render(request, template_name, context)


# --- Minimal dynamic model loader so this file doesn't crash if you paste it before models are ready ---
from django.apps import apps  # noqa: E402  (keep import at bottom for clarity)


def _get_model_or_404(app_label: str, model_name: str):  # type: ignore
    model = apps.get_model(app_label, model_name)
    if model is None:
        raise LookupError(f"Model {app_label}.{model_name} not found. Adjust imports in views.")
    return model









from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import TrackingLookupForm
from warehouse.models import Shipment, ShipmentStatusHistory


def _get_owner_user_id(shipment):
    """Try common owner patterns to return a user id or None."""
    if getattr(shipment, "owner_id", None):
        return shipment.owner_id
    profile = getattr(shipment, "profile", None)
    if profile:
        return getattr(profile, "user_id", None)
    # fallback: maybe shipment.owner is a user object
    owner = getattr(shipment, "owner", None)
    if getattr(owner, "id", None):
        return owner.id
    return None


def tracking_lookup(request):
    """
    Tracking lookup page: lets customers paste a tracking number or suit number.
    On POST redirects to tracking_detail view.
    """
    form = TrackingLookupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        q = form.cleaned_data["query"].strip()
        # Normalize: allow suit_number or tracking_number
        return redirect("customer:tracking_detail", identifier=q)
    return render(request, "customer/tracking_lookup.html", {"form": form})


@login_required
def tracking_detail(request, identifier):
    """
    Show tracking detail for a shipment found by tracking_number or suit_number.
    Access control: only staff or the shipment owner can view. If you want public
    tracking, remove the @login_required decorator and implement an email check.
    """
    # prefer exact match on tracking_number then suit_number
    shipment = Shipment.objects.filter(tracking_number=identifier).select_related(
        "selected_courier"
    ).first()
    if not shipment:
        shipment = Shipment.objects.filter(suit_number=identifier).select_related(
            "selected_courier"
        ).first()
    if not shipment:
        raise Http404("Shipment not found.")

    owner_user_id = _get_owner_user_id(shipment)
    if not (request.user.is_staff or (owner_user_id and owner_user_id == request.user.id)):
        return HttpResponseForbidden("You do not have permission to view this shipment's tracking.")

    # Fetch history ordered by created_at desc (model Meta ensures ordering, but make explicit)
    history_qs = shipment.history.all()

    # Optional: allow limited JSON response if requested by XHR
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        events = [
            {
                "status": ev.status,
                "message": ev.message,
                "location": ev.location,
                "created_at": ev.created_at.isoformat(),
                "raw_payload": ev.raw_payload,
            }
            for ev in history_qs
        ]
        from django.http import JsonResponse
        return JsonResponse({"shipment": {"suit_number": shipment.suit_number, "tracking_number": shipment.tracking_number}, "history": events})

    context = {
        "shipment": shipment,
        "history": history_qs,
    }
    return render(request, "customer/tracking_detail.html", context)





from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from warehouse.models import Shipment  # adjust import if needed


@login_required
def search_shipments(request):
    """
    AJAX endpoint: ?q=... returns up to 20 matching shipments for the current user (or all for staff).
    """
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})

    user = request.user
    if user.is_staff:
        qs = Shipment.objects.all()
    else:
        qs = Shipment.objects.filter(Q(owner=user) | Q(profile__user=user))

    qs = (
        qs.filter(Q(suit_number__icontains=q) | Q(tracking_number__icontains=q))
          .select_related("selected_courier")
          .order_by("-created_at")[:20]
    )

    results = []
    for s in qs:
        # safe status display
        status_display = s.get_status_display() if hasattr(s, "get_status_display") else getattr(s, "status", "")
        courier_name = s.selected_courier.name if getattr(s, "selected_courier", None) else None
        identifier = s.tracking_number if s.tracking_number else s.suit_number
        url = reverse("customer:tracking_detail", args=[identifier])
        results.append({
            "id": s.pk,
            "suit_number": s.suit_number,
            "tracking_number": s.tracking_number or "",
            "status": status_display,
            "courier": courier_name or "",
            "updated_at": s.created_at.isoformat() if getattr(s, "created_at", None) else "",
            "url": url,
        })

    return JsonResponse({"results": results})




 
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils.crypto import get_random_string

from .models import Shipment
from .models import Plan




@login_required
def dashboard(request):
    """
    Dashboard for customers. Staff sees all shipments.
    Returns counts and recent shipments for the template.
    """
    user = request.user

    if user.is_staff:
        qs = Shipment.objects.all()
    else:
        qs = Shipment.objects.filter(Q(owner=user) | Q(profile__user=user))

    # Avoid N+1
    qs = qs.select_related("selected_courier", "delivery_address", "payment", "profile")

    total_shipments = qs.count()
    in_transit = qs.filter(selected_courier__isnull=False).exclude(status__in=("delivered", "completed")).count()
    delivered_by_status = qs.filter(status__in=["delivered", "completed"]).count()
    delivered_by_tracking = qs.exclude(tracking_number__isnull=True).exclude(tracking_number="").count()
    total_spent = qs.aggregate(total=Coalesce(Sum("selected_price"), 0))["total"] or Decimal("0.00")

    recent_shipments = qs.order_by("-created_at")[:12]

    profile = getattr(request.user, "profile", None)
    current_tier = getattr(profile, "membership_tier", None)

    return render(request, "customer/dashboard.html", {
        "total_shipments": total_shipments,
        "in_transit": in_transit,
        "delivered_by_status": delivered_by_status,
        "delivered_by_tracking": delivered_by_tracking,
        "total_spent": total_spent,
        "recent_shipments": recent_shipments,
        "current_tier": current_tier,
        "custom_id": getattr(profile, "user_id_custom", None),
        "delivered": qs.filter(status__in=["delivered", "completed"]).count(),
    })


@login_required
def dashboard_json(request):
    """
    Lightweight JSON for polling. Returns key counts.
    """
    user = request.user
    if user.is_staff:
        qs = Shipment.objects.all()
    else:
        qs = Shipment.objects.filter(Q(owner=user) | Q(profile__user=user))

    data = {
        "total_shipments": qs.count(),
        "in_transit": qs.filter(selected_courier__isnull=False).exclude(status__in=("delivered", "completed")).count(),
        "delivered": qs.filter(status__in=["delivered", "completed"]).count(),
        "total_spent": float((qs.aggregate(total=Coalesce(Sum("selected_price"), 0))["total"] or 0)),
    }
    return JsonResponse(data)


@login_required
def search_shipments(request):
    """
    AJAX endpoint for live search on the dashboard search box.
    GET param: q
    Returns up to 20 matching shipments (restricted to current user's shipments unless staff).
    """
    q = (request.GET.get("q") or "").strip()
    if not q or len(q) < 2:
        return JsonResponse({"results": []})

    user = request.user
    if user.is_staff:
        qs = Shipment.objects.all()
    else:
        qs = Shipment.objects.filter(Q(owner=user) | Q(profile__user=user))

    qs = (
        qs.filter(Q(suit_number__icontains=q) | Q(tracking_number__icontains=q))
          .select_related("selected_courier")
          .order_by("-created_at")[:20]
    )

    results = []
    for s in qs:
        status_display = s.get_status_display() if hasattr(s, "get_status_display") else getattr(s, "status", "")
        results.append({
            "id": s.pk,
            "suit_number": s.suit_number,
            "tracking_number": s.tracking_number or "",
            "status": status_display,
            "courier": getattr(s.selected_courier, "name", "") if getattr(s, "selected_courier", None) else "",
            "url": reverse("customer:tracking_detail", args=[s.tracking_number or s.suit_number]),
        })
    return JsonResponse({"results": results})






# customer/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Shipment  # uses the Shipment model above

VALID_STATUSES = {"accepted", "started", "completed"}

# Optional: guard transitions (can’t go backwards after completed)
ALLOWED_NEXT = {
    None: {"accepted", "started", "completed"},
    "accepted": {"started", "completed"},
    "started": {"completed"},
    "completed": set(),
}

@login_required
@require_POST
def warehouse_update(request, shipment_id):
    """
    Update a shipment's warehouse/delivery status.
    Accepts POST param 'status' in {'accepted','started','completed'}.
    Returns JSON for AJAX, or redirects with a toast for normal form posts.
    """
    status = (request.POST.get("status") or "").lower().strip()
    if status not in VALID_STATUSES:
        return HttpResponseBadRequest("Invalid status")

    shipment = get_object_or_404(Shipment, pk=shipment_id)

    # transition guard (optional; delete this block if you want free moves)
    current = shipment.status or None
    if status not in ALLOWED_NEXT.get(current, VALID_STATUSES):
        msg = f"Not allowed: {current or 'none'} → {status}"
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(reverse("customer:membership_manage"))  # change to wherever you came from

    # save it
    shipment.status = status
    shipment.status_updated_at = timezone.now()
    shipment.status_updated_by = request.user
    shipment.save(update_fields=["status", "status_updated_at", "status_updated_by"])

    # AJAX? return JSON
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "shipment_id": shipment.id,
            "status": shipment.status,
            "label": shipment.get_status_display(),
            "updated_at": shipment.status_updated_at.isoformat(),
        })

    # regular POST → redirect with toast
    messages.success(request, f"Status updated to: {shipment.get_status_display()}")
    # adjust this redirect to your detail/list page
    return redirect(reverse("customer:membership_manage"))





from warehouse.models import ShipmentStatusHistory

@login_required
@require_POST
def shipment_history(request, pk: int):
    # auth-scope the shipment first
    qs = Shipment.objects.filter(pk=pk).select_related("profile")
    user = request.user
    if not user.is_staff:
        qs = qs.filter(Q(owner=user) | Q(profile__user=user))
    shipment = qs.first()
    if not shipment:
        return HttpResponseForbidden("Not allowed or not found.")

    items = [
        {
            "status": h.status,
            "message": h.message,
            "location": h.location,
            "raw_payload": h.raw_payload,
            "created_at": h.created_at.isoformat(),
        }
        for h in shipment.history.all()  # ordered desc via Meta.ordering
    ]
    return JsonResponse({"shipment_id": shipment.pk, "history": items})




@login_required
def console_list(request):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"console_list: user={request.user.username}, is_staff={request.user.is_staff}")

    ship_qs = annotate_rate_count(base_shipments_for_user(request.user))
    logger.info(f"console_list: base_shipments_for_user count={ship_qs.count()}")

    # Count shipments by status before filtering
    from django.db.models import Count
    status_counts = ship_qs.values('status').annotate(count=Count('status')).order_by('status')
    logger.info(f"console_list: status counts before filtering: {list(status_counts)}")

    # Check for consolidations and their shipment statuses
    from .models import Consolidation, ConsolidationItem
    user_filter = request.user if hasattr(request.user, 'profile') else None
    logger.info(f"console_list: user_filter={user_filter}, type={type(user_filter)}, hasattr profile={hasattr(request.user, 'profile')}")
    if hasattr(request.user, 'profile'):
        logger.info(f"console_list: request.user.profile={request.user.profile}, type={type(request.user.profile)}")
    consolidations = Consolidation.objects.filter(user=user_filter)
    logger.info(f"console_list: user consolidations count={consolidations.count()}")
    for cons in consolidations:
        logger.info(f"console_list: consolidation id={cons.id}, status={cons.status}, shipments_count={cons.shipments_count}")
        for item in cons.items.all():
            shipment = item.shipment
            logger.info(f"console_list: consolidation item shipment id={shipment.id}, suit={shipment.suit_number}, status={shipment.status}")

    # Filter to only show held shipments
    ship_qs = ship_qs.filter(status="held")
    logger.info(f"console_list: shipments count after filtering to held={ship_qs.count()}")

    shipments = safe_select_related_shipments(ship_qs).order_by("-id")[:300]
    logger.info(f"console_list: shipments count after limit={shipments.count()}")
    for s in shipments[:5]:  # log first 5
        logger.info(f"console_list: shipment id={s.id}, suit={s.suit_number}, status={s.status}")

    if request.user.is_staff:
        entries = ConsoleShipment.objects.select_related("shipment", "created_by").order_by("-created_at")[:200]
    else:
        entries = (ConsoleShipment.objects
                   .select_related("shipment", "created_by")
                   .filter(shipment__profile__user=request.user)
                   .order_by("-created_at")[:200])

    logger.info(f"console_list: entries count={entries.count()}")

    return render(request, "customer/console_list.html", {
        "shipments": shipments,
        "entries": entries,
    })




@login_required
@require_POST
def console_action_create(request, shipment_id=None):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"console_action_create: user={request.user.username}, is_staff={request.user.is_staff}, shipment_id={shipment_id}")
    logger.info(f"console_action_create: POST data keys: {list(request.POST.keys())}")
    raw_action = request.POST.get('action')
    logger.info(f"console_action_create: raw action from POST: '{raw_action}'")

    if shipment_id is None:
        logger.error(f"console_action_create: shipment_id is None, checking POST for shipment_id")
        shipment_id = request.POST.get('shipment_id')
        logger.info(f"console_action_create: shipment_id from POST: {shipment_id}")

    if not shipment_id:
        logger.error(f"console_action_create: No shipment_id provided for user {request.user.username}")
        messages.error(request, "No shipment specified.")
        return safe_redirect(request)

    try:
        shipment_id = int(shipment_id)
    except ValueError:
        logger.error(f"console_action_create: Invalid shipment_id '{shipment_id}' for user {request.user.username}")
        messages.error(request, "Invalid shipment ID.")
        return safe_redirect(request)

    shipment = get_object_or_404(Shipment, pk=shipment_id)
    owner_user = getattr(getattr(shipment, "profile", None), "user", None)
    logger.info(f"console_action_create: shipment owner_user={owner_user}, request.user={request.user}, shipment.status={shipment.status}")

    if not (request.user.is_staff or owner_user == request.user):
        logger.warning(f"console_action_create: Permission denied for user {request.user.username} on shipment {shipment_id}")
        return HttpResponseForbidden("You do not have permission to modify this shipment.")

    form = ConsoleShipmentForm(request.POST)
    if not form.is_valid():
        logger.error(f"console_action_create: Invalid form for user {request.user.username}: {form.errors}")
        messages.error(request, "Invalid form submission.")
        return safe_redirect(request)

    action = normalize_action(form.cleaned_data["action"])
    logger.info(f"console_action_create: normalized action='{action}' from raw '{raw_action}' for user {request.user.username}")
    allowed = {v for v, _ in ConsoleShipment.ACTION_CHOICES}
    logger.info(f"console_action_create: allowed actions={allowed}")
    if action not in allowed:
        logger.error(f"console_action_create: Unknown action '{action}' for user {request.user.username}")
        messages.error(request, "Unknown action.")
        return safe_redirect(request)

    logger.info(f"console_action_create: About to create ConsoleShipment for shipment {shipment_id}, action='{action}', note='{form.cleaned_data.get('note', '')}'")
    try:
        entry, created = ConsoleShipment.objects.get_or_create(
            shipment=shipment,
            action=action,
            defaults={"created_by": request.user, "note": form.cleaned_data.get("note", "")},
        )
        logger.info(f"console_action_create: get_or_create result: created={created}, entry.id={entry.id if entry else None}")
        if not created:
            note = form.cleaned_data.get("note", "")
            if note and not entry.note:
                entry.note = note
                entry.save(update_fields=["note"])
                logger.info(f"console_action_create: Updated note on existing entry {entry.id}")
            else:
                logger.info(f"console_action_create: Entry already exists, no update needed")
        else:
            logger.info(f"console_action_create: New entry created with id {entry.id}")

        # Update shipment status based on action
        if action == "hold":
            old_status = shipment.status
            shipment.status = "held"
            shipment.status_updated_at = timezone.now()
            shipment.status_updated_by = request.user
            shipment.save(update_fields=["status", "status_updated_at", "status_updated_by"])
            logger.info(f"console_action_create: Updated shipment {shipment_id} status from '{old_status}' to 'hold'")
        elif action == "delivered":
            old_status = shipment.status
            shipment.status = "delivered"
            shipment.status_updated_at = timezone.now()
            shipment.status_updated_by = request.user
            shipment.save(update_fields=["status", "status_updated_at", "status_updated_by"])
            logger.info(f"console_action_create: Updated shipment {shipment_id} status from '{old_status}' to 'delivered'")

    except Exception as e:
        logger.error(f"console_action_create: Exception during save: {e}")
        messages.error(request, "Failed to save action.")
        return safe_redirect(request)

    logger.info(f"console_action_create: Action '{action}' recorded for shipment {shipment_id} by user {request.user.username}")
    messages.success(request, f"Action recorded: {entry.get_action_display()} for shipment {getattr(shipment, 'suit_number', shipment.pk)}.")
    return safe_redirect(request)





# customer/views.py (add these imports at top)
import json
from decimal import Decimal, ROUND_HALF_UP
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.db import transaction

# ensure these are imported where appropriate:
# from .models import Shipment, Consolidation, ConsolidationItem, ConsoleShipment
# from django.contrib.auth.decorators import login_required
# ...your existing imports...

# helper functions (place near existing helpers)
def compute_cbm(length_cm, width_cm, height_cm):
    try:
        l = Decimal(length_cm or 0)
        w = Decimal(width_cm or 0)
        h = Decimal(height_cm or 0)
    except Exception:
        return Decimal("0")
    cbm = (l * w * h) / Decimal("1000000")
    return cbm.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

def compute_volume_weight(cbm, factor=Decimal("200")):
    return (Decimal(cbm or 0) * Decimal(factor)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)

# default rate (override via settings if desired)
from django.conf import settings
DEFAULT_CONSOLIDATION_RATE = getattr(settings, "DEFAULT_CONSOLIDATION_RATE", Decimal("5.00"))

@login_required
def consolidation_quote(request):
    """
    POST params:
      - shipment_ids[] : shipment ids (required, at least 2)
      - rate  : optional rate per kg (decimal)
    Renders template with shipments[] and totals{}.
    """
    if request.method == "POST":
        ids = request.POST.getlist("shipment_ids")
    else:
        ids = request.GET.getlist("ids[]") or request.GET.getlist("ids")
    if not ids:
        messages.error(request, "No shipments selected.")
        return redirect("customer:console_list")

    # fetch shipments and enforce ownership
    qs = Shipment.objects.filter(pk__in=ids)
    # convert to list for simple permission filtering
    if not request.user.is_staff:
        qs = [s for s in qs if (getattr(s, "profile", None) and getattr(s.profile, "user", None) == request.user) or getattr(s, "owner", None) == request.user]
    else:
        qs = list(qs)

    if len(qs) < 2:
        messages.error(request, "Select at least two shipments to consolidate.")
        return redirect("customer:console_list")

    per_package = []
    total_cbm = Decimal("0")
    total_gross = Decimal("0")

    for s in qs:
        # adjust field names if your Shipment uses different names
        length = getattr(s, "length_cm", None) or getattr(s, "length", None) or 0
        width = getattr(s, "width_cm", None) or getattr(s, "width", None) or 0
        height = getattr(s, "height_cm", None) or getattr(s, "height", None) or 0
        gross_w = getattr(s, "gross_weight", None) or getattr(s, "weight_kg", None) or 0

        cbm = compute_cbm(length, width, height)
        vol_wt = compute_volume_weight(cbm)
        chargeable_w = max(Decimal(gross_w or 0), vol_wt).quantize(Decimal("0.000"))

        per_package.append({
            "id": s.pk,
            "suit_number": getattr(s, "suit_number", "") or "",
            "tracking_number": getattr(s, "tracking_number", "") or "",
            "length_cm": str(length),
            "width_cm": str(width),
            "height_cm": str(height),
            "cbm": str(cbm),
            "volume_weight": str(vol_wt),
            "gross_weight": str(gross_w),
            "chargeable_weight": str(chargeable_w),
        })

        total_cbm += cbm
        total_gross += Decimal(gross_w or 0)

    total_volume_weight = compute_volume_weight(total_cbm)
    chargeable_weight = max(total_gross, total_volume_weight).quantize(Decimal("0.000"))

    rate_param = request.GET.get("rate")
    try:
        rate = Decimal(str(rate_param)) if rate_param is not None else DEFAULT_CONSOLIDATION_RATE
    except Exception:
        rate = DEFAULT_CONSOLIDATION_RATE

    price = (chargeable_weight * rate).quantize(Decimal("0.01"))

    # Offer list of available couriers (optional). Adjust model import if different app.
    couriers = []
    try:
        from warehouse.models import Courier  # update path if different
        couriers = Courier.objects.filter(active=True)[:20]
    except Exception:
        couriers = []

    return render(request, "customer/consolidation_quote.html", {
        "shipments": per_package,
        "totals": {
            "total_cbm": total_cbm.quantize(Decimal("0.000001")),
            "total_volume_weight": total_volume_weight,
            "total_gross_weight": total_gross.quantize(Decimal("0.000")),
            "chargeable_weight": chargeable_weight,
            "rate_per_kg": rate,
            "price": price,
        },
        "couriers": couriers,
    })



@login_required
def console_details_create(request):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"console_details_create: user={request.user.username}, method={request.method}")

    if request.method == "POST":
        ids = request.POST.getlist("shipment_ids")
        courier_id = request.POST.get("courier_id")
        rate = request.POST.get("rate")
        logger.info(f"console_details_create POST: shipment_ids={ids}, courier_id={courier_id}, rate={rate}")

        # Handle POST: create consolidation
        if not ids:
            ids = request.GET.getlist("shipment_ids")
        logger.info(f"console_details_create: using shipment_ids from POST or GET: {ids}")
        if not ids:
            messages.error(request, "No shipments selected.")
            return redirect("customer:console_list")

        # Fetch shipments and enforce ownership
        qs = Shipment.objects.filter(pk__in=ids)
        if not request.user.is_staff:
            qs = [s for s in qs if (getattr(s, "profile", None) and getattr(s.profile, "user", None) == request.user) or getattr(s, "owner", None) == request.user]
        else:
            qs = list(qs)

        if len(qs) < 2:
            messages.error(request, "Select at least two shipments to consolidate.")
            return redirect("customer:console_list")

        # Calculate totals
        shipments = []
        total_cbm = Decimal("0")
        total_gross = Decimal("0")

        for s in qs:
            length = getattr(s, "length_cm", None) or getattr(s, "length", None) or 0
            width = getattr(s, "width_cm", None) or getattr(s, "width", None) or 0
            height = getattr(s, "height_cm", None) or getattr(s, "height", None) or 0
            gross_w = getattr(s, "gross_weight", None) or getattr(s, "weight_kg", None) or 0

            cbm = compute_cbm(length, width, height)
            vol_wt = compute_volume_weight(cbm)
            chargeable_w = max(Decimal(gross_w or 0), vol_wt).quantize(Decimal("0.000"))

            shipments.append({
                "id": s.pk,
                "suit_number": getattr(s, "suit_number", "") or "",
                "tracking_number": getattr(s, "tracking_number", "") or "",
                "cbm": cbm,
                "volume_weight": vol_wt,
                "gross_weight": Decimal(gross_w or 0),
                "chargeable_weight": chargeable_w,
            })

            total_cbm += cbm
            total_gross += Decimal(gross_w or 0)

        total_volume_weight = compute_volume_weight(total_cbm)
        chargeable_weight = max(total_gross, total_volume_weight).quantize(Decimal("0.000"))

        # Get selected courier and rate
        selected_courier = None
        selected_rate = None
        if courier_id:
            try:
                from warehouse.models import Courier
                selected_courier = Courier.objects.get(pk=courier_id, active=True)
                if rate:
                    selected_rate = CourierRate.objects.filter(courier=selected_courier, price_per_kg=Decimal(rate), active=True).first()
                logger.info(f"console_details_create: selected_courier={selected_courier}, selected_rate={selected_rate}")
            except Exception as e:
                logger.error(f"Error fetching courier/rate: {e}")

        # Calculate price
        final_price = Decimal("0")
        if selected_rate:
            final_price = (chargeable_weight * selected_rate.price_per_kg).quantize(Decimal("0.01"))
        elif rate:
            final_price = (chargeable_weight * Decimal(rate)).quantize(Decimal("0.01"))
        logger.info(f"console_details_create: final_price={final_price}")

        # Create consolidation
        logger.info(f"console_details_create: About to create Consolidation with user={request.user}, total_cbm={total_cbm}, total_volume_weight={total_volume_weight}, total_gross={total_gross}, chargeable_weight={chargeable_weight}, final_price={final_price}, selected_courier={selected_courier}, selected_rate={selected_rate}")
        with transaction.atomic():
            try:
                consolidation = Consolidation.objects.create(
                    user=request.user,
                    total_cbm=total_cbm.quantize(Decimal("0.0001")),  # Match model decimal_places=4
                    total_volume_weight=total_volume_weight.quantize(Decimal("0.001")),  # Match decimal_places=3
                    total_gross_weight=total_gross.quantize(Decimal("0.001")),  # Match decimal_places=3
                    chargeable_weight=chargeable_weight,
                    price=final_price,
                    currency="USD",  # Assuming USD, adjust if needed
                    shipments_count=len(qs),
                    status="confirmed",
                    selected_courier=selected_courier,
                    selected_rate=selected_rate,
                    selected_price=final_price,
                )
                logger.info(f"console_details_create: Consolidation created successfully with id={consolidation.id}")
            except Exception as e:
                logger.error(f"console_details_create: Error creating Consolidation: {e}")
                raise

            # Create consolidation items
            for s in qs:
                ConsolidationItem.objects.create(consolidation=consolidation, shipment=s)
            logger.info(f"console_details_create: ConsolidationItems created for {len(qs)} shipments")

            # Create delivery address for consolidation
            addr_data = {
                "recipient_name": request.POST.get("recipient_name"),
                "address_line1": request.POST.get("address_line1"),
                "address_line2": request.POST.get("address_line2", ""),
                "city": request.POST.get("city"),
                "state": request.POST.get("state", ""),
                "postal_code": request.POST.get("postal_code", ""),
                "country": request.POST.get("country"),
                "phone": request.POST.get("phone", ""),
            }
            if all(addr_data.values()):  # Only create if all required fields are provided
                DeliveryAddress.objects.create(consolidation=consolidation, **addr_data)
                logger.info(f"console_details_create: DeliveryAddress created for consolidation {consolidation.id}")

            # Create payment for consolidation
            payment_method = request.POST.get("payment_method")
            if payment_method:
                payment_obj, created = Payment.objects.get_or_create(
                    consolidation=consolidation,
                    defaults={"amount": final_price, "currency": "USD", "status": Payment.STATUS_PENDING},
                )
                if not created:
                    payment_obj.amount = final_price
                    payment_obj.currency = "USD"
                    payment_obj.save(update_fields=["amount", "currency"])
                logger.info(f"console_details_create: Payment created for consolidation {consolidation.id}")

        messages.success(request, f"Consolidation created successfully with {len(qs)} shipments.")
        return redirect("customer:console_list")

    else:
        ids = request.GET.getlist("shipment_ids")
    logger.info(f"console_details_create: shipment_ids={ids}")

    if not ids:
        messages.error(request, "No shipments selected.")
        return redirect("customer:console_list")

    # Fetch shipments and enforce ownership
    qs = Shipment.objects.filter(pk__in=ids)
    if not request.user.is_staff:
        qs = [s for s in qs if (getattr(s, "profile", None) and getattr(s.profile, "user", None) == request.user) or getattr(s, "owner", None) == request.user]
    else:
        qs = list(qs)

    logger.info(f"console_details_create: filtered shipments count={len(qs)}")

    if len(qs) < 2:
        messages.error(request, "Select at least two shipments to consolidate.")
        return redirect("customer:console_list")

    shipments = []
    total_cbm = Decimal("0")
    total_gross = Decimal("0")

    for s in qs:
        length = getattr(s, "length_cm", None) or getattr(s, "length", None) or 0
        width = getattr(s, "width_cm", None) or getattr(s, "width", None) or 0
        height = getattr(s, "height_cm", None) or getattr(s, "height", None) or 0
        gross_w = getattr(s, "gross_weight", None) or getattr(s, "weight_kg", None) or 0

        cbm = compute_cbm(length, width, height)
        vol_wt = compute_volume_weight(cbm)
        chargeable_w = max(Decimal(gross_w or 0), vol_wt).quantize(Decimal("0.000"))

        shipments.append({
            "id": s.pk,
            "suit_number": getattr(s, "suit_number", "") or "",
            "tracking_number": getattr(s, "tracking_number", "") or "",
            "cbm": cbm,
            "volume_weight": vol_wt,
            "gross_weight": Decimal(gross_w or 0),
            "chargeable_weight": chargeable_w,
        })

        total_cbm += cbm
        total_gross += Decimal(gross_w or 0)

    total_volume_weight = compute_volume_weight(total_cbm)
    chargeable_weight = max(total_gross, total_volume_weight).quantize(Decimal("0.000"))

    rate = DEFAULT_CONSOLIDATION_RATE
    price = (chargeable_weight * rate).quantize(Decimal("0.01"))

    # Offer list of available couriers
    couriers = []
    try:
        from warehouse.models import Courier
        couriers = Courier.objects.filter(active=True)[:20]
        logger.info(f"console_details_create: couriers count={len(couriers)}")
    except Exception as e:
        logger.error(f"console_details_create: Error fetching couriers: {e}")
        couriers = []

    totals = {
        "total_cbm": total_cbm.quantize(Decimal("0.000001")),
        "total_volume_weight": total_volume_weight,
        "total_gross_weight": total_gross.quantize(Decimal("0.000")),
        "chargeable_weight": chargeable_weight,
        "rate_per_kg": rate,
        "price": price,
    }

    logger.info(f"console_details_create: totals={totals}, shipments count={len(shipments)}")

    return render(request, "customer/console_details.html", {
        "shipments": shipments,
        "totals": totals,
        "couriers": couriers,
        "selected_ids": ids,
    })
    
    
    
    
    
    
    
    
    
    

from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .models import Consolidation, ConsolidationItem, Shipment  # adjust imports to your app


def _generate_console_suit(consolidation_pk: int) -> str:
    """Create CSP0001-style IDs from the consolidation primary key."""
    return f"CSP{int(consolidation_pk):04d}"


@login_required
@transaction.atomic
def console_details_view(request, consolidation_id):
    """
    Example view that creates a Consolidation and, within the SAME transaction,
    persists a ConsolePackage representing the consolidated shipment.

    Assumptions:
    - You POST a set of shipment IDs to consolidate.
    - You already have logic that calculates totals and creates Consolidation + items.
    Replace placeholders with your existing calculations.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"console_details_view: user={request.user.username}, consolidation_id={consolidation_id}, method={request.method}")

    consolidation = get_object_or_404(Consolidation, pk=consolidation_id)
    logger.info(f"console_details_view: consolidation found, status={consolidation.status}, shipments_count={consolidation.shipments_count}")

    # Log delivery address and payment availability
    delivery_address = getattr(consolidation, 'delivery_address', None)
    payment = getattr(consolidation, 'payment', None)
    logger.info(f"console_details_view: delivery_address={delivery_address}, payment={payment}")
    if delivery_address:
        logger.info(f"console_details_view: delivery_address details - recipient_name={delivery_address.recipient_name}, city={delivery_address.city}")
    if payment:
        logger.info(f"console_details_view: payment details - amount={payment.amount}, status={payment.status}")

    if request.method == "POST":
        logger.info(f"console_details_view POST: POST data keys: {list(request.POST.keys())}")
        # --- Your existing computations (replace with real values) ---
        # Example placeholders; ensure these are set from your real logic
        total_cbm = Decimal(request.POST.get("total_cbm", "0"))
        total_volume_weight = Decimal(request.POST.get("total_volume_weight", "0"))
        total_gross = Decimal(request.POST.get("total_gross_weight", "0"))
        chargeable_weight = Decimal(request.POST.get("chargeable_weight", "0"))
        final_price = Decimal(request.POST.get("final_price", "0"))
        currency = request.POST.get("currency", "USD")
        selected_courier = None  # or look up from POST

        # `qs` should be the shipments included in this consolidation
        shipment_ids = request.POST.getlist("shipment_ids")
        logger.info(f"console_details_view: shipment_ids from POST: {shipment_ids}")
        qs = Shipment.objects.filter(pk__in=shipment_ids)
        logger.info(f"console_details_view: shipments queryset count: {qs.count()}")

        # Ensure ConsolidationItems exist (pseudo-code; adapt to your schema)
        items = [
            ConsolidationItem(
                consolidation=consolidation,
                shipment=s,
                # ... any extra fields ...
            )
            for s in qs
        ]
        ConsolidationItem.objects.bulk_create(items, ignore_conflicts=True)
        logger.info(f"console_details_view: ConsolidationItems bulk created, count: {len(items)}")

        messages.success(request, f"Consolidation updated with {len(qs)} shipments.")
        return redirect("customer:console_details_view", consolidation_id=consolidation_id)

    # GET fallback: show a page with computed totals/confirm form
    items = consolidation.items.select_related("shipment").all()
    shipments = [item.shipment for item in items]
    context = {
        "consolidation": consolidation,
        "shipments": shipments,
        "items": items,
        "delivery_address": delivery_address,
        "payment": payment,
        # include any preview totals, shipments, etc.
    }
    logger.info(f"console_details_view: rendering GET response for consolidation {consolidation_id} with {len(shipments)} shipments")
    return render(request, "customer/console_details.html", context)

