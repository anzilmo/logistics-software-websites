# customer/urls.py
from django.urls import path
from . import views
# optional extras
try:
    from .views import customer_shipment_photos, purchase_list, purchase_create, purchase_detail, purchase_edit
    HAS_EXTRAS = True
except Exception:
    HAS_EXTRAS = False

app_name = "customer"

urlpatterns = [
    # basic
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("dashbord/", views.dashbord, name="dashbord"),
    path("warehouse/stats/", views.warehouse_stats, name="warehouse_stats"),
    path("dashboard/search_shipments/", views.search_shipments, name="search_shipments"),# not Django admin; your customer dashboard


    # shipments
    path("shipments/new/", views.shipment_create, name="shipment_create"),
    path("shipments/", views.shipment_list, name="shipment_list"),
    path("shipments/<str:suit_number>/", views.shipment_detail, name="shipment_detail"),

    # rates
    path("rates/<int:shipment_id>/", views.shipment_rates, name="shipment_rates"),
    path("rates/success/", views.shipment_success, name="shipment_success"),


    
    path("subscribe/", views.subscribe, name="subscribe"),
    path("membership/", views.membership_manage, name="membership_manage"),
    path("membership/apply/", views.membership_application, name="membership_application"),
    path("membership/cancel/", views.membership_cancel, name="membership_cancel"),
    
    
    path("address/create/<int:shipment_id>/", views.address_create_for_shipment, name="address_create"),
    path("payment/<int:shipment_id>/", views.payment_process, name="payment_process"),
    
    
    
    
    
     path("shipments/", views.choose_courier_view, name="shipment_list"),
    path("shipments/<str:suit_number>/", views.choose_courier_view, name="shipment_detail"),
    
    path("shipments/", views.choose_courier_view, name="shipment_list"),
    path("shipments/<str:suit_number>/", views.choose_courier_view, name="shipment_detail"),
    
    
    
    path("tracking/", views.tracking_lookup, name="tracking_lookup"),
    path("tracking/<str:identifier>/", views.tracking_detail, name="tracking_detail"),


    path("console/", views.console_list, name="console_list"),
    path("console/action/create/<int:shipment_id>/", views.console_action_create, name="console_action_create"),
    path("console/consolidation/quote/", views.consolidation_quote, name="consolidation_quote"),
    path("console/details/", views.console_details, name="console_details"),
    
    
   
]

if HAS_EXTRAS:
    urlpatterns += [
        path("photos/<str:suit_number>/", customer_shipment_photos, name="shipment_photos"),
        path("purchases/", purchase_list, name="purchase_list"),
        path("purchases/new/", purchase_create, name="purchase_create"),
        path("purchases/<int:pk>/", purchase_detail, name="purchase_detail"),
        path("purchases/<int:pk>/edit/", purchase_edit, name="purchase_edit"),
    ]

