from django.contrib import admin
from .models import  Profile , Country ,PurchaseBill, MembershipTier


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_id_custom', 'membership_tier', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user_id_custom')
    list_filter = ('created_at', 'updated_at', 'membership_tier')
    readonly_fields = ('user_id_custom', 'created_at', 'updated_at')


@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ("name", "percent_fee", "fixed_fee", "currency", "active", "ordering")
    list_filter = ("active", "currency")
    search_fields = ("name",)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('country_name', 'city', 'state', 'zip_code', 'phone_number', 'email', 'created_at')
    search_fields = ('country_name', 'city', 'state', 'zip_code')
    list_filter = ('state',)
    readonly_fields = ('created_at',)
    
@admin.register(PurchaseBill)
class PurchaseBillAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier', 'date', 'amount', 'created_at')
    search_fields = ('invoice_number', 'supplier')
    list_filter = ('date',)
    ordering = ('-date',)    
    






# customer/admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Courier, CourierRate


class CourierRateInline(admin.TabularInline):
    model = CourierRate
    extra = 1
    fields = ("price_per_kg", "min_charge", "currency", "active")
    show_change_link = True


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ("name", "logo_preview", "active_rates_count", "total_rates_count")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [CourierRateInline]

    def logo_preview(self, obj):
        try:
            url = obj.logo.url
        except Exception:
            return "—"
        return mark_safe(f'<img src="{url}" style="height:32px;border-radius:6px;" />')
    logo_preview.short_description = "Logo"

    def active_rates_count(self, obj):
        return obj.rates.filter(active=True).count()

    def total_rates_count(self, obj):
        return obj.rates.count()


@admin.register(CourierRate)
class CourierRateAdmin(admin.ModelAdmin):
    list_display  = ("courier", "price_per_kg", "min_charge", "currency", "active")
    list_editable = ("active",)
    list_filter   = ("active", "currency", "courier")
    search_fields = ("courier__name",)
    ordering      = ("courier__name", "currency", "id")


# customer/admin.py
from django.contrib import admin
from .models import Plan, Membership

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price", "currency", "billing_cycle", "active", "sort")
    list_filter = ("billing_cycle", "active", "currency")
    search_fields = ("name", "slug")
    ordering = ("sort", "price")
    fieldsets = (
        (None, {"fields": ("name", "slug", "active", "sort")}),
        ("Pricing", {"fields": ("price", "currency", "billing_cycle")}),
        ("Features", {"fields": ("features",)}),
    )

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "started_at", "ends_at", "auto_renew", "price", "currency")
    list_filter = ("status", "plan", "auto_renew", "currency", "billing_cycle")
    search_fields = ("user__username", "user__email", "plan__name")
    autocomplete_fields = ("user", "plan")
    readonly_fields = ("started_at",)




from django.contrib import admin
from django.utils.html import format_html

from .models import DeliveryAddress

@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = (
        "recipient_name",
        "city",
        "country",
        "phone",
        "shipment_link",
        "created_at",
    )
    search_fields = (
        "recipient_name",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "phone",
        "shipment__suit_number",
        "shipment__tracking_number",
    )
    list_filter = ("country", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("shipment",)  # works if Shipment admin has search_fields

    def shipment_link(self, obj):
        if not obj.shipment_id:
            return "—"
        # admin URL for warehouse.Shipment
        return format_html(
            '<a href="/admin/warehouse/shipment/{}/change/">{}</a>',
            obj.shipment_id,
            obj.shipment,
        )
    shipment_link.short_description = "Shipment"





from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, Consolidation, ConsolidationItem, ConsoleShipment
import logging

logger = logging.getLogger(__name__)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "shipment_link",
        "amount_pretty",
        "status",
        "provider",
        "provider_reference",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "currency", "provider", "created_at")
    search_fields = (
        "provider_reference",
        "shipment__suit_number",
        "shipment__tracking_number",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("shipment",)

    actions = ("mark_as_success", "mark_as_failed")

    def amount_pretty(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_pretty.short_description = "Amount"

    def shipment_link(self, obj):
        if not obj.shipment_id:
            return "—"
        # admin change URL for warehouse.Shipment (adjust if your admin path differs)
        return format_html(
            '<a href="/admin/warehouse/shipment/{}/change/">{}</a>',
            obj.shipment_id,
            getattr(obj.shipment, "suit_number", obj.shipment_id),
        )
    shipment_link.short_description = "Shipment"

    # bulk actions
    def mark_as_success(self, request, queryset):
        updated = 0
        for p in queryset:
            p.mark_success(provider_reference=p.provider_reference or "")
            updated += 1
        self.message_user(request, f"Marked {updated} payment(s) as success.")
    mark_as_success.short_description = "Mark selected payments as SUCCESS"

    def mark_as_failed(self, request, queryset):
        updated = 0
        for p in queryset:
            p.mark_failed(provider_reference=p.provider_reference or "")
            updated += 1
        self.message_user(request, f"Marked {updated} payment(s) as failed.")
    mark_as_failed.short_description = "Mark selected payments as FAILED"


class ConsolidationItemInline(admin.TabularInline):
    model = ConsolidationItem
    extra = 0
    fields = ("shipment",)
    autocomplete_fields = ("shipment",)
    show_change_link = True

@admin.register(Consolidation)
class ConsolidationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_cbm",
        "total_volume_weight",
        "total_gross_weight",
        "chargeable_weight",
        "price",
        "currency",
        "shipments_count",
        "status",
        "selected_courier",
        "created_at",
    )
    list_filter = ("status", "currency", "selected_courier", "created_at")
    search_fields = ("user__username", "user__email", "id")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user", "selected_courier", "selected_rate")
    inlines = [ConsolidationItemInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        consolidation = form.instance
        items_count = consolidation.items.count()
        logger.info(f"Consolidation {consolidation.id} saved with {items_count} items")
        if items_count > 0:
            logger.info(f"Items: {[item.shipment.suit_number for item in consolidation.items.all()]}")


@admin.register(ConsolidationItem)
class ConsolidationItemAdmin(admin.ModelAdmin):
    list_display = ("consolidation", "shipment")
    list_filter = ("consolidation__status",)
    search_fields = ("consolidation__id", "shipment__suit_number", "shipment__tracking_number")
    autocomplete_fields = ("consolidation", "shipment")


@admin.register(ConsoleShipment)
class ConsoleShipmentAdmin(admin.ModelAdmin):
    list_display = ("shipment", "action", "note", "created_by", "created_at")
    list_filter = ("action", "created_at", "created_by")
    search_fields = ("shipment__suit_number", "shipment__tracking_number", "note")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("shipment", "created_by")





