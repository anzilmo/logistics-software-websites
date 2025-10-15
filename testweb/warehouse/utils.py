# warehouse/utils.py
from django.http import JsonResponse, Http404
from warehouse.models import Shipment

def resolve_shipment_by_suit_or_409(request, suit_number, queryset=None):
    qs = (queryset or Shipment.objects).filter(suit_number=suit_number)

    if not qs.exists():
        raise Http404("Shipment not found")

    # Optional: permission scoping
    if hasattr(Shipment, 'owner') and not request.user.is_staff:
        qs = qs.filter(owner=request.user)

    count = qs.count()
    if count == 1:
        return qs.first()

    # Ambiguous: surface candidates so caller can pick by pk
    candidates = list(qs.order_by('-pk').values('id', 'pk'))[:10]
    resp = JsonResponse({
        "detail": "Multiple shipments found for suit_number; disambiguate by pk.",
        "suit_number": suit_number,
        "candidates": candidates,
    }, status=409)
    # Raise to let view return immediately:
    raise Exception(resp)  # caller should catch and return this JsonResponse




# warehouse/utils.py
from django.http import Http404
from warehouse.models import Shipment

def resolve_shipment_by_suit_latest(request, suit_number, queryset=None):
    qs = (queryset or Shipment.objects).filter(suit_number=suit_number)

    if not request.user.is_staff:
        if hasattr(Shipment, 'profile'):
            qs = qs.filter(profile__user=request.user)
        elif hasattr(Shipment, 'owner'):
            qs = qs.filter(owner=request.user)

    shipment = qs.order_by('-pk').first()
    if not shipment:
        raise Http404("Shipment not found")
    return shipment



from decimal import Decimal, ROUND_HALF_UP

# CBM calculation base: dimensions expected in centimeters
def compute_cbm(length_cm, width_cm, height_cm):
    try:
        length = Decimal(length_cm)
        width = Decimal(width_cm)
        height = Decimal(height_cm)
    except Exception:
        return Decimal("0")
    # CBM = L * W * H (cm^3) / 1_000_000 -> m^3
    cbm = (length * width * height) / Decimal("1000000")
    return cbm.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

def compute_volume_weight_from_cbm(cbm, factor=Decimal("200")):
    # Typically 200 or 166 depending on carrier; default 200 per your spec
    if cbm is None:
        return Decimal("0")
    vol_wt = cbm * Decimal(factor)
    return vol_wt.quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)

def compute_chargeable_weight(total_gross_weight, total_volume_weight):
    g = Decimal(total_gross_weight or 0)
    v = Decimal(total_volume_weight or 0)
    return max(g, v).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)