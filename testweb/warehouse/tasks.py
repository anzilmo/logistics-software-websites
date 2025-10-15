# shipments/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import Shipment, ShipmentStatusHistory
from .courier_adapters import get_adapter_for_courier
from .notifications import notify_status_change


@shared_task(bind=True, max_retries=3)
def poll_shipment_status_task(self, shipment_id):
    try:
        shipment = Shipment.objects.select_related("courier", "owner").get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return

    if not shipment.tracking_number or not shipment.courier:
        return

    adapter = get_adapter_for_courier(shipment.courier)
    if not adapter:
        return

    try:
        new = adapter.get_status(shipment.tracking_number)
    except Exception as exc:
        # optional: log error + retry later
        raise self.retry(exc=exc, countdown=60 * 5)

    new_status = new.get("status")
    message = new.get("message", "")
    location = new.get("location", "")
    timestamp = new.get("timestamp")

    # Map provider statuses to our canonical statuses if needed
    mapping = {
        "in_transit": Shipment.STATUS_IN_TRANSIT,
        "delivered": Shipment.STATUS_DELIVERED,
        "held": Shipment.STATUS_HELD,
        "accepted": Shipment.STATUS_ACCEPTED,
    }
    canonical = mapping.get(new_status, new_status)

    # If changed, write history and notify
    with transaction.atomic():
        changed = canonical != shipment.status
        if changed:
            shipment.status = canonical
            shipment.status_last_synced = timezone.now()
            # update estimated_delivery if adapter returned it (optional)
            if new.get("estimated_delivery"):
                shipment.estimated_delivery = new.get("estimated_delivery")
            shipment.save(update_fields=["status", "status_last_synced", "estimated_delivery", "updated_at"])

            ShipmentStatusHistory.objects.create(
                shipment=shipment,
                status=canonical,
                message=message,
                location=location or "",
                raw_payload=new.get("raw", {}),
                created_at=timestamp or timezone.now()
            )

            # notify the customer (email/SMS/push — implement in notifications.py)
            notify_status_change(shipment.owner, shipment, canonical, message)

    return {"shipment": shipment.id, "status": shipment.status}