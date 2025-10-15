# warehouse/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Shipment, StaffNotification

@receiver(pre_save, sender=Shipment)
def notify_on_selection_change(sender, instance: Shipment, **kwargs):
    if not instance.pk:
        return
    old = sender.objects.filter(pk=instance.pk).values("selected_courier_id", "selected_rate_id", "selected_price").first()
    if not old:
        return
    changed = (
        old["selected_courier_id"] != (instance.selected_courier_id) or
        old["selected_rate_id"] != (instance.selected_rate_id) or
        str(old["selected_price"]) != (str(instance.selected_price) if instance.selected_price is not None else None)
    )
    if changed and instance.selected_courier and instance.selected_rate and instance.selected_price is not None:
        StaffNotification.objects.create(
            type="courier_selected",
            shipment=instance,
            text=f"Courier updated to {instance.selected_courier.name} for shipment #{instance.id} at {instance.selected_price} {instance.selected_rate.currency}",
        )
