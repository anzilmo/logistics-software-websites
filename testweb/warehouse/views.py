from asyncio.log import logger
import logging
from django.http import HttpResponse
from .notifications import notify_status_change
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test


# purchis bill/views.py
import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse, Http404
from customer.models import  CourierRate, PurchaseBill
from .models import Warehouse
# import the model from the customer app

try:
    from .models import StaffNotification
    HAS_NOTIFS = True
except ImportError:
    HAS_NOTIFS = False


# forms
# warehouse/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import NoReverseMatch, reverse


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Shipment



# warehouse/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Shipment



import base64
import os
import uuid
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.core.files.base import ContentFile
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST



import base64
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, render
from .models import Shipment, ShipmentImage


from django.shortcuts import render, get_object_or_404, redirect
from warehouse.models import Shipment
 # we'll create this form


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Shipment


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .models import Shipment

def _with_safe_select_related(qs):
    fk_names = {f.name for f in qs.model._meta.get_fields() if getattr(f, "many_to_one", False)}
    rels = [n for n in ("selected_courier", "selected_rate", "profile", "warehouse") if n in fk_names]
    return qs.select_related(*rels) if rels else qs


@csrf_protect
def login(request):
    """
    Login by providing country_name and code (code is also used as password).
    On success, stores warehouse_id in session and redirects to dashboard.
    """
    logger = logging.getLogger(__name__)
    error = None

    if request.method == "POST":
        country = request.POST.get("country_name", "").strip()
        code = request.POST.get("code", "").strip()
        logger.info(f"Login attempt: country='{country}', code='{code}'")

        if not country or not code:
            error = "Both country name and code are required."
        else:
            try:
                warehouse = Warehouse.objects.filter(country_name__iexact=country).first()
                logger.info(f"Warehouse query result: {warehouse}")
                if warehouse:
                    logger.info(f"Password hash exists: {bool(warehouse.password_hash)}")
                    logger.info(f"Password check result: {warehouse.check_password(code)}")
            except Exception as e:
                logger.error(f"Error during warehouse lookup or password check: {e}")
                error = "An error occurred during login."
                return render(request, "warehouse/wlogin.html", {"error": error})

            if not warehouse or not warehouse.check_password(code):
                error = "Invalid country name or code."
            else:
                # Success: set session and redirect
                request.session["warehouse_id"] = warehouse.id
                request.session["warehouse_country"] = warehouse.country_name
                messages.success(request, f"Logged in to warehouse: {warehouse.country_name}")
                return redirect("warehouse:dashboard")

    return render(request, "warehouse/wlogin.html", {"error": error})

def w_logout(request):
    """Clear warehouse session and logout."""
    request.session.pop("warehouse_id", None)
    request.session.pop("warehouse_country", None)
    messages.info(request, "Logged out.")
    return redirect("warehouse:warehouse-login")


# def dashboard(request):
#     """Warehouse dashboard, accessible only if logged in."""
#     warehouse_id = request.session.get("warehouse_id")
#     shipments = Shipment.objects.select_related("selected_courier", "selected_rate").order_by("-id")[:100]
   

#     if not warehouse_id:
#         messages.error(request, "Please login first.")
#         return redirect("warehouse-login")

#     warehouse = Warehouse.objects.filter(pk=warehouse_id).first()
#     if not warehouse:
#         messages.error(request, "Warehouse not found. Please login again.")
#         return redirect("warehouse-login")

#     return render(request, "warehouse/dashboard.html", {"warehouse": warehouse} )


@login_required
def dashboard(request):
    """
    Warehouse dashboard:
      - If session['warehouse_id'] is set and Warehouse exists, filter to that warehouse
      - Show latest shipments (+ selected courier/price if present)
      - Show unread staff notifications (if model exists)
    """
    warehouse = None
    warehouse_id = request.session.get("warehouse_id")

    if warehouse_id and Warehouse:
        warehouse = Warehouse.objects.filter(pk=warehouse_id).first()
        if warehouse is None:
            # Session points to a missing warehouse -> force re-login to warehouse portal
            messages.error(request, "Warehouse not found. Please login again.")
            return redirect("warehouse:warehouse-login")

    # Shipments (optionally filtered by active warehouse)
    shipments_qs = Shipment.objects.all()
    if warehouse:
        # Only filter if Shipment actually has a warehouse FK
        if "warehouse" in {f.name for f in Shipment._meta.get_fields()}:
            shipments_qs = shipments_qs.filter(warehouse=warehouse)

    shipments = _with_safe_select_related(shipments_qs).order_by("-id")[:100]


    # Notifications (optional)
    notif_count = 0
    notifications = []
    if HAS_NOTIFS:
        notif_qs = StaffNotification.objects.filter(is_read=False).order_by("-created_at")
        if warehouse and "warehouse" in {f.name for f in Shipment._meta.get_fields()}:
            notif_qs = notif_qs.filter(shipment__warehouse=warehouse)
        notif_count = notif_qs.count()
        notifications = list(notif_qs[:20])

    # Calculate dashboard metrics
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    # Total inventory: total shipments
    total_inventory = shipments_qs.count()

    # Inventory change text: compare to yesterday
    yesterday = timezone.now() - timedelta(days=1)
    yesterday_count = Shipment.objects.filter(created_at__date=yesterday.date()).count()
    if yesterday_count > 0:
        change = ((total_inventory - yesterday_count) / yesterday_count) * 100
        inventory_change_text = f"{change:+.1f}% from yesterday"
    else:
        inventory_change_text = "No data from yesterday"

    # Pending orders: shipments without selected_courier
    pending_orders = shipments_qs.filter(selected_courier__isnull=True).count()
    pending_orders_text = f"{pending_orders} shipments awaiting courier selection"

    # Today's shipments
    today = timezone.now().date()
    todays_shipments = shipments_qs.filter(created_at__date=today).count()
    shipments_text = f"{todays_shipments} shipments created today"

    # Revenue: sum of selected_price for all shipments
    revenue = shipments_qs.filter(selected_price__isnull=False).aggregate(Sum('selected_price'))['selected_price__sum'] or 0
    revenue_text = f"Total from {shipments_qs.filter(selected_price__isnull=False).count()} priced shipments"

    # Inventory summary: group by status or something, but since no status, perhaps by courier
    inventory_summary = []
    courier_counts = shipments_qs.values('selected_courier__name').annotate(count=Count('id')).order_by('-count')[:5]
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    for i, item in enumerate(courier_counts):
        inventory_summary.append({
            'name': item['selected_courier__name'] or 'No Courier',
            'quantity': item['count'],
            'color': colors[i % len(colors)]
        })

    # Recent activity: recent shipments
    recent_activity = []
    for s in shipments[:5]:
        recent_activity.append({
            'title': f'Shipment {s.suit_number}',
            'description': f'Created for {s.profile.user.email if s.profile else "Unknown"}',
            'time': s.created_at.strftime('%H:%M'),
            'icon': 'fas fa-box',
            'bg_color': '#321b66ff',
            'icon_color': '#fff'
        })

    ctx = {
        "warehouse": warehouse,
        "shipments": shipments,
        "notif_count": notif_count,
        "notifications": notifications,
        "total_inventory": total_inventory,
        "inventory_change_text": inventory_change_text,
        "pending_orders": pending_orders,
        "pending_orders_text": pending_orders_text,
        "todays_shipments": todays_shipments,
        "shipments_text": shipments_text,
        "revenue": revenue,
        "revenue_text": revenue_text,
        "inventory_summary": inventory_summary,
        "recent_activity": recent_activity,
    }
    return render(request, "warehouse/dashboard.html", ctx)


@login_required
def mark_notifications_read(request):
    """Mark all unread notifications as read (optionally scoped to active warehouse)."""
    if not HAS_NOTIFS:
        return redirect("warehouse:dashboard")

    notif_qs = StaffNotification.objects.filter(is_read=False)
    warehouse_id = request.session.get("warehouse_id")

    if warehouse_id and Warehouse and "warehouse" in {f.name for f in Shipment._meta.get_fields()}:
        notif_qs = notif_qs.filter(shipment__warehouse_id=warehouse_id)

    updated = notif_qs.update(is_read=True)
    if updated:
        messages.success(request, f"Marked {updated} notification(s) as read.")
    return redirect("warehouse:dashboard")



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from .models import Shipment
from .forms import  ShipmentForm


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ShipmentForm
from customer.models import Profile
# List all shipments
@login_required
def shipment_list(request):
    qs = Shipment.objects.filter(owner=request.user).select_related("courier", "warehouse")
    shipments = Shipment.objects.select_related("profile", "warehouse").all()

    return render(request, "warehouse/shipment_list.html", {"shipments": shipments})
# Create a new shipment
def shipment_create(request):
    warehouse_id = request.session.get("warehouse_id")
    if not warehouse_id:
        messages.error(request, "Please login first.")
        return redirect("warehouse:warehouse-login")

    warehouse = Warehouse.objects.filter(pk=warehouse_id).first()
    if not warehouse:
        messages.error(request, "Warehouse not found. Please login again.")
        return redirect("warehouse:warehouse-login")

    if request.method == "POST":
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.warehouse = warehouse
            shipment.save()
            messages.success(request, f"Shipment created with suit #{shipment.suit_number}.")
            return redirect("warehouse:shipment_detail", suit_number=shipment.suit_number)

        # invalid form
        return render(request, "warehouse/shipment_form.html", {"form": form})

    # GET
    form = ShipmentForm()
    return render(request, "warehouse/shipment_form.html", {"form": form})


# Update an existing shipment
def shipment_update(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)

    if request.method == "POST":
        form = ShipmentForm(request.POST, instance=shipment)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipment updated successfully.")
            return redirect("warehouse:shipment_list")
    else:
        form = ShipmentForm(instance=shipment)

    return render(request, "warehouse/shipment_form.html", {"form": form, "shipment": shipment})


from decimal import Decimal, InvalidOperation
from django.http import Http404
from django.shortcuts import render, redirect
from .models import Shipment
from warehouse.models import Shipment
from customer.models import DeliveryAddress as Address# adjust if needed




def _to_decimal_safe(value, default="0"):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _gross_weight_kg(s: Shipment) -> Decimal:
    # prefer weight_kg, fallback to weight
    if hasattr(s, "weight_kg") and s.weight_kg is not None:
        return _to_decimal_safe(s.weight_kg, "0")
    return _to_decimal_safe(getattr(s, "weight", 0), "0")


def _cbm_safe(s: Shipment, unit="cm"):
    try:
        return s.cbm(unit=unit)
    except Exception:
        return None


def _vol_weight_safe(s: Shipment, unit="cm"):
    try:
        return s.volume_weight(unit=unit)
    except Exception:
        return None


def _chargeable_safe(s: Shipment, unit="cm", rounding=None):
    try:
        # if your method accepts rounding, pass it; otherwise ignore
        if rounding is not None:
            return s.chargeable_weight(unit=unit, rounding=rounding)
        return s.chargeable_weight(unit=unit)
    except Exception:
        # fallback: max(gross, volume)
        gross = _gross_weight_kg(s)
        vol = _vol_weight_safe(s, unit=unit) or Decimal("0")
        return max(gross, _to_decimal_safe(vol, "0"))
    
def _best_rate_for(s: Shipment):
    """
    Pick the 'best' active courier selection (lowest total_price).
    Returns (rate_obj_or_None, price_or_None).
    """
    qs = s.courier_selections.filter(is_active=True)
    best = qs.order_by("total_price", "id").first()
    if not best:
        return (None, None)
    return (best, best.total_price)

def _owner_user_from_shipment(s: Shipment):
    # Prefer the shipment owner via profile.user; fallback to None
    return getattr(getattr(s, "profile", None), "user", None)

def _default_address(user, kind: str):
    if not user:
        return None
    return (Address.objects
            .filter(user=user, type=kind)
            .order_by("-is_default", "-created_at")
            .first())

def _addr_urls(addr):
    out = {"list": None, "create": None, "edit": None, "delete": None}
    try:
        out["list"] = reverse("customer:address_list")
        out["create"] = reverse("customer:address_create")
        if addr:
            out["edit"] = reverse("customer:address_edit", args=[addr.pk])
            out["delete"] = reverse("customer:address_delete", args=[addr.pk])
    except NoReverseMatch:
        # If address routes aren’t wired yet, keep going without links
        pass
    return out    


def _price_with_active_rate_safe(s: Shipment, unit="cm", rounding=None):
    """
    Try your domain helper if it exists; otherwise compute using the first active rate
    just so the page can render a price example.
    Returns (rate_obj_or_None, price_or_None).
    """
    # domain helper present?
    if hasattr(s, "price_using_active_rate"):
        try:
            if rounding is not None:
                return s.price_using_active_rate(unit=unit, rounding=rounding)
            return s.price_using_active_rate(unit=unit)
        except Exception:
            pass

    # fallback: first active rate price using chargeable weight
    chg = _chargeable_safe(s, unit=unit, rounding=rounding)
    rate = (
        CourierRate.objects.filter(active=True)
        .select_related("courier")
        .order_by("courier__name", "id")
        .first()
    )
    if not rate:
        return (None, None)
    try:
        return (rate, rate.price_for_weight(chg))
    except Exception:
        return (rate, None)

# ---------- main view ---------
# views.py
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.db.models import Prefetch
from customer.models import DeliveryAddress,Payment

from .models import Shipment  # adjust import if models live elsewhere

ALLOWED_UNITS = {"cm", "m"}
ALLOWED_ROUNDING = {"no_round", "ceil_int", "ceil_0_5"}

def _owner_user_from_shipment(s):
    # prefer profile.user, fallback to owner (old model)
    try:
        if getattr(s, "profile", None) and getattr(s.profile, "user", None):
            return s.profile.user
    except Exception:
        pass
    return getattr(s, "owner", None)

def _user_can_see(user, shipment):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return _owner_user_from_shipment(shipment) == user

# ---- safe wrappers around model helpers ----
def _cbm_safe(s, unit="cm"):
    try:
        # support either signature cbm(unit=...) or cbm(from_unit=...)
        try:
            return s.cbm(unit=unit)
        except TypeError:
            return s.cbm(from_unit=unit)
    except Exception:
        return Decimal("0")

def _vol_weight_safe(s, unit="cm"):
    try:
        try:
            return s.volume_weight(unit=unit)
        except TypeError:
            return s.volume_weight(from_unit=unit)
    except Exception:
        return Decimal("0")

def _gross_weight_kg(s):
    w = getattr(s, "weight_kg", None)
    if w is None:
        w = getattr(s, "weight", 0)
    try:
        return Decimal(str(w))
    except Exception:
        return Decimal("0")

def _chargeable_safe(s, unit="cm", rounding="ceil_0_5"):
    try:
        try:
            return s.chargeable_weight(unit=unit, rounding=rounding)
        except TypeError:
            return s.chargeable_weight(from_unit=unit, rounding=rounding)
    except Exception:
        return Decimal("0")

def _price_with_active_rate_safe(s, unit="cm", rounding="ceil_0_5"):
    try:
        try:
            rate, price = s.price_using_active_rate(unit=unit, rounding=rounding)
        except TypeError:
            rate, price = s.price_using_active_rate(from_unit=unit, rounding=rounding)
        return rate, price
    except Exception:
        return None, None

def _default_address(user, kind):
    """
    stub: replace with your real address fetch.
    kind in {"shipping","billing"}
    """
    return None

def _addr_urls(addr):
    """stub: return edit/view urls for given address object"""
    return {}

@login_required
def shipment_detail(request, suit_number):
    # query params (validated)
    unit = request.GET.get("unit", "cm").lower()
    rounding = request.GET.get("rounding", "ceil_0_5")
    if unit not in ALLOWED_UNITS:
        unit = "cm"
    if rounding not in ALLOWED_ROUNDING:
        rounding = "ceil_0_5"

    key = str(suit_number).strip()

    # ----- GET: lookup by suit (case-insensitive) -----
    qs = (
        Shipment.objects
        .filter(suit_number__iexact=key)
        .select_related("profile", "profile__user", "warehouse", "selected_courier", "selected_rate")
    )

    # fallback: numeric key -> PK
    if not qs.exists() and key.isdigit():
        try:
            s = Shipment.objects.select_related("profile", "profile__user", "warehouse").get(pk=int(key))
            qs = Shipment.objects.filter(pk=s.pk)
        except Shipment.DoesNotExist:
            pass

    if not qs.exists():
        raise Http404(f"No shipments found for suit number or id: {key}")

    # permission: if multiple, every one must be viewable
    for s in qs:
        if not _user_can_see(request.user, s):
            raise Http404()  # or return HttpResponseForbidden()

    # ===== Multi-shipment (same suit_number) =====
    if qs.count() > 1:
        rows = []
        for s in qs:
            cbm = _cbm_safe(s, unit=unit)
            vol_w = _vol_weight_safe(s, unit=unit)
            gross_w = _gross_weight_kg(s).quantize(Decimal("0.01"))
            charge_w = _chargeable_safe(s, unit=unit, rounding=rounding)
            rate, price = _price_with_active_rate_safe(s, unit=unit, rounding=rounding)

            rows.append({
                "shipment": s,
                "cbm": cbm,
                "volume_weight": vol_w,
                "gross_weight": gross_w,
                "chargeable_weight": charge_w,
                "rate": rate,
                "price": price,
            })

        return render(
            request,
            "customer/shipment_detail_list.html",
            {"suit_number": key, "rows": rows, "unit": unit}
        )

    # ===== Single shipment =====
    shipment = qs.first()

    # Handle POST: update status
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status and new_status in dict(Shipment.STATUS_CHOICES):
            old_status = shipment.status
            shipment.status = new_status
            shipment.status_updated_by = request.user
            shipment.save(update_fields=["status", "status_updated_by", "status_updated_at"])

            # Add to history
            from .models import ShipmentStatusHistory
            ShipmentStatusHistory.objects.create(
                shipment=shipment,
                status=new_status,
                message=f"Status updated from {old_status} to {new_status} via warehouse interface",
            )

            messages.success(request, f"Shipment status updated to {dict(Shipment.STATUS_CHOICES)[new_status]}.")
            return redirect("warehouse:shipment_detail", suit_number=suit_number)
        else:
            messages.error(request, "Invalid status value.")


    cbm = _cbm_safe(shipment, unit=unit)
    vol_w = _vol_weight_safe(shipment, unit=unit)
    gross_w = _gross_weight_kg(shipment).quantize(Decimal("0.01"))
    charge_w = _chargeable_safe(shipment, unit=unit, rounding=rounding)
    rate, price = _price_with_active_rate_safe(shipment, unit=unit, rounding=rounding)

    selection = {
        "has_selection": bool(getattr(shipment, "selected_courier", None)),
        "courier_name": getattr(getattr(shipment, "selected_courier", None), "name", None),
        "price": getattr(shipment, "selected_price", None),
        "currency": getattr(getattr(shipment, "selected_rate", None), "currency", None),
        "rate_id": getattr(getattr(shipment, "selected_rate", None), "id", None),
    }

    owner_user = _owner_user_from_shipment(shipment) or request.user
    shipping_address = _default_address(owner_user, "shipping")
    billing_address  = _default_address(owner_user, "billing")

    # Fetch DeliveryAddress and Payment from customer app
    delivery_address = None
    payment = None
    try:
        from customer.models import DeliveryAddress, Payment
        delivery_address = DeliveryAddress.objects.filter(shipment=shipment).first()
        payment = Payment.objects.filter(shipment=shipment).first()
    except Exception as e:
        logger.error(f"Error fetching delivery_address or payment: {e}")


    address_links    = {
        "shipping": _addr_urls(shipping_address),
        "billing":  _addr_urls(billing_address),
    }

    try:
        console_actions = shipment.console_actions.all().order_by("-created_at")
    except Exception:
        console_actions = []

    return render(
        request,
        "warehouse/shipment_detail.html",
        {
            "shipment": shipment,
            "selection": selection,
            "cbm": cbm,
            "volume_weight": vol_w,
            "gross_weight": gross_w,
            "chargeable_weight": charge_w,
            "rate": rate,
            "price": price,
            "console_actions": console_actions,
            "unit": unit,
            "shipping_address": shipping_address,
            "billing_address": billing_address,
            "delivery_address": delivery_address,
            "payment": payment,
            "address_links": address_links,
        },
    )


# Delete a shipment
def shipment_delete(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    if request.method == "POST":
        shipment.delete()
        messages.success(request, "Shipment deleted successfully.")
        return redirect("warehouse:shipment_list")
    return render(request, "warehouse/shipment_confirm_delete.html", {"shipment": shipment})


@login_required
def shipment_hold(request, suit_number):
    """Hold a shipment by setting status to 'held'."""
    shipment = get_object_or_404(Shipment, suit_number=suit_number)
    if request.method == "POST":
        shipment.status = Shipment.STATUS_HELD
        shipment.save()
        messages.success(request, f"Shipment {shipment.suit_number} has been held.")
        return redirect("warehouse:shipment_detail", suit_number=suit_number)
    return render(request, "warehouse/shipment_confirm_hold.html", {"shipment": shipment})


@login_required
def shipment_release(request, suit_number):
    """Release a held shipment by setting status back to 'pending'."""
    shipment = get_object_or_404(Shipment, suit_number=suit_number)
    if request.method == "POST":
        shipment.status = Shipment.STATUS_PENDING
        shipment.save()
        messages.success(request, f"Shipment {shipment.suit_number} has been released.")
        return redirect("warehouse:shipment_detail", suit_number=suit_number)
    return render(request, "warehouse/shipment_confirm_release.html", {"shipment": shipment})





# show in pdf

def is_warehouse_user(user):
    # adjust this to your real permission logic (e.g. group membership, staff flag)
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='warehouse').exists())

@login_required
# @user_passes_test(is_warehouse_user)
def purchase_list_for_warehouse(request):
    purchases = PurchaseBill.objects.all().order_by('-date', '-created_at')
    return render(request, 'warehouse/purchase_list.html', {'purchases': purchases})

@login_required
# @user_passes_test(is_warehouse_user)
def purchase_detail_for_warehouse(request, pk):
    purchase = get_object_or_404(PurchaseBill, pk=pk)
    return render(request, 'warehouse/purchase_detail.html', {'purchase': purchase})

@login_required
# @user_passes_test(is_warehouse_user)
def purchase_pdf_download(request, pk):
    purchase = get_object_or_404(PurchaseBill, pk=pk)

    if not purchase.pdf:
        raise Http404("No PDF available for this purchase.")

    try:
        # purchase.pdf.open() returns a file-like object from the storage backend
        file_obj = purchase.pdf.open('rb')
        filename = os.path.basename(purchase.pdf.name)
        response = FileResponse(file_obj, as_attachment=True, filename=filename)
        return response
    except Exception:
        # log the exception in real code
        raise Http404("Failed to open the file.")











# warehouse/views.py
import base64
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.shortcuts import render
from warehouse.models import Shipment, ShipmentImage
from warehouse.utils import resolve_shipment_by_suit_latest  # or strict resolver

@ensure_csrf_cookie
def shipment_camera_by_suit(request, suit_number):
    """
    Render camera page for shipment identified by suit_number (dup-safe).
    """
    shipment = resolve_shipment_by_suit_latest(request, suit_number)
    return render(request, "warehouse/shipment_camera.html", {"shipment": shipment})

@require_POST
def upload_shipment_image_by_suit(request, suit_number):
    """
    Accept multipart/form-data 'image' file and attach to the latest-matching Shipment.
    """
    shipment = resolve_shipment_by_suit_latest(request, suit_number)

    image_file = request.FILES.get("image")
    if not image_file:
        return HttpResponseBadRequest("No image file provided.")

    si = ShipmentImage.objects.create(
        shipment=shipment,
        image=image_file,
        uploaded_by=(request.user if request.user.is_authenticated else None),
    )
    return JsonResponse({
        "id": si.id,
        "image_url": si.image.url,
        "captured_at": si.captured_at.isoformat(),
        "shipment_pk": shipment.pk,
    })

@require_POST
def upload_shipment_image_base64_by_suit(request, suit_number):
    """
    Accept POST param 'image_data' containing data URL (data:image/jpeg;base64,...).
    """
    shipment = resolve_shipment_by_suit_latest(request, suit_number)

    image_data = request.POST.get("image_data")
    if not image_data:
        return HttpResponseBadRequest("No image_data provided.")
    try:
        header, encoded = image_data.split(",", 1)
    except ValueError:
        return HttpResponseBadRequest("Invalid image_data format")

    ext = "jpg" if "jpeg" in header or "jpg" in header else "png"
    decoded = base64.b64decode(encoded)
    filename = f"{shipment.suit_number}_{int(timezone.now().timestamp())}.{ext}"
    content = ContentFile(decoded, name=filename)

    si = ShipmentImage.objects.create(
        shipment=shipment,
        image=content,
        uploaded_by=(request.user if request.user.is_authenticated else None),
    )
    return JsonResponse({
        "id": si.id,
        "image_url": si.image.url,
        "captured_at": si.captured_at.isoformat(),
        "shipment_pk": shipment.pk,
    })

def shipment_images_list_by_suit(request, suit_number):
    """
    Return JSON list of images for a shipment (dup-safe).
    """
    shipment = resolve_shipment_by_suit_latest(request, suit_number)
    images = shipment.images.all().order_by('-captured_at', '-pk')[:50]
    data = [
        {"id": i.id, "url": i.image.url, "captured_at": i.captured_at.isoformat()}
        for i in images
    ]
    return JsonResponse({
        "shipment": {"pk": shipment.pk, "suit_number": shipment.suit_number},
        "images": data,
    })


# only views using methode 





# warehouse/views.py
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import Shipment  # your warehouse Shipment

def shipment_accept(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)

    # auth/permission checks as needed...
    shipment.status = "accepted"
    shipment.save(update_fields=["status"])

    messages.success(request, f"Shipment {shipment.suit_number or shipment.pk} has been accepted ✅")

    url = reverse("customer:shipment_detail", args=[shipment.suit_number])
    return redirect(f"{url}?single={shipment.pk}")


def shipment_mark_delivered(request, pk):
    logger = logging.getLogger(__name__)
    shipment = get_object_or_404(Shipment, pk=pk)
    logger.info(f"Marking shipment {shipment.suit_number or shipment.pk} as delivered")

    shipment.status = "delivered"
    shipment.save(update_fields=["status"])

    # Send notification to customer
    user = getattr(getattr(shipment, "profile", None), "user", None)
    if user:
        logger.info(f"Sending delivery notification to user {user.email}")
        logger.info(f"Calling notify_status_change for shipment {shipment.suit_number}")
        notify_status_change(user, shipment, "delivered", "Your package has been successfully delivered.")
        logger.info(f"notify_status_change called successfully for shipment {shipment.suit_number}")
    else:
        logger.warning(f"No user found for shipment {shipment.suit_number or shipment.pk}, cannot send notification")

    messages.success(request, f"Shipment {shipment.suit_number or shipment.pk} marked as delivered 📦")

    url = reverse("customer:shipment_detail", args=[shipment.suit_number])
    return redirect(f"{url}?single={shipment.pk}")
