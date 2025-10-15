from django.contrib import admin
from .models import Warehouse , Rate, Shipment ,ShipmentImage, Courier, CourierSelection, ShipmentStatusHistory

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('country_name', 'code', 'password_hash')
    search_fields = ('country_name', 'code')
    readonly_fields = ('password_hash',)  # Prevent manual editing of hashed password

    def save_model(self, request, obj, form, change):
        """
        Optional: automatically hash the code if password_hash is empty.
        This is handled in the model save(), so this is optional.
        """
        super().save_model(request, obj, form, change)

@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_kg", "min_charge", "currency", "active")
    list_filter = ("active", "currency")
    search_fields = ("name",)



    
    
    
    
    
@admin.register(ShipmentImage)
class ShipmentImageAdmin(admin.ModelAdmin):
    list_display = ("shipment", "captured_at", "uploaded_by")
    search_fields = ("shipment__suit_number",)
    list_filter = ("captured_at",)
    
    




# warehouse/admin.py
from django.contrib import admin
from .models import Shipment, StaffNotification

@admin.register(StaffNotification)
class StaffNotificationAdmin(admin.ModelAdmin):
    list_display = ("type", "shipment", "text", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("text", "shipment__suit_number", "shipment__tracking_number")
    ordering = ("-created_at",)


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(CourierSelection)
class CourierSelectionAdmin(admin.ModelAdmin):
    list_display = ("shipment", "courier", "service_name", "total_price", "currency", "is_active", "created_at")
    list_filter = ("is_active", "currency", "courier")
    search_fields = ("shipment__suit_number", "service_name", "carrier_rate_id")


@admin.register(ShipmentStatusHistory)
class ShipmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("shipment", "status", "message", "location", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("shipment__suit_number", "status", "message", "location")



from django.contrib import admin
from .models import Shipment
# import the model from your delivery app
from customer.models import DeliveryAddress

class DeliveryAddressInline(admin.StackedInline):
    model = DeliveryAddress
    can_delete = False
    extra = 0
    
    
    
    
    
    from django.contrib import admin
from .models import Shipment
from customer.models import Payment  # adjust import to your app label

class PaymentInline(admin.StackedInline):
    model = Payment
    can_delete = False
    extra = 0
    max_num = 1






@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("suit_number", "tracking_number", "package_type", "weight_kg", "arrival_date", "warehouse" )
    list_filter = ("package_type", "arrival_date", "warehouse", "status")
    inlines = [PaymentInline]
    inlines = [DeliveryAddressInline]

    search_fields = ("suit_number", "tracking_number")
    
 
    
