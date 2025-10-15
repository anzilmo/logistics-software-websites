from django.urls import path
from . import views



urlpatterns = [
    path('',views.login,name='warehouse-login'),
    path('logout/', views.w_logout, name='warehous-logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("notifications/mark-all-read/", views.mark_notifications_read, name="mark_notifications_read"),

    
    
    path('shipments/', views.shipment_list, name='shipment_list'),
    path('shipments/create/', views.shipment_create, name='shipment_create'),
    path('shipments/<int:pk>/update/', views.shipment_update, name='shipment_update'),
    # path('shipments/<int:pk>/', views.shipment_detail, name='shipment_detail'),
    path("shipments/<str:suit_number>/", views.shipment_detail, name="shipment_detail"),
    path('shipments/<int:pk>/delete/', views.shipment_delete, name='shipment_delete'),
    path("shipments/<str:suit_number>/hold/", views.shipment_hold, name="shipment_hold"),
    path("shipments/<str:suit_number>/release/", views.shipment_release, name="shipment_release"),
    
    
    
    path('purchases/', views.purchase_list_for_warehouse, name='purchase_list'),
    path('purchases/<int:pk>/', views.purchase_detail_for_warehouse, name='purchase_detail'),
    path('purchases/<int:pk>/download/', views.purchase_pdf_download, name='purchase_download'),
    
    
    
    path("shipment/<str:suit_number>/camera/", views.shipment_camera_by_suit, name="shipment_camera"),
    path("shipment/<str:suit_number>/upload/", views.upload_shipment_image_by_suit, name="upload_shipment_image"),
    path("shipment/<str:suit_number>/upload_base64/", views.upload_shipment_image_base64_by_suit, name="upload_shipment_image_base64"),
    path("shipment/<str:suit_number>/images/", views.shipment_images_list_by_suit, name="shipment_images_list"),
    
    
    path("shipment/<int:pk>/accept/", views.shipment_accept, name="shipment_accept"),
    path("shipment/<int:pk>/delivered/", views.shipment_mark_delivered, name="shipment_mark_delivered"),
    
 


    
]
