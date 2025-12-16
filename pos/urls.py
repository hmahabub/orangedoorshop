from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_dashboard, name='pos_dashboard'),
    path('api/product/<int:product_id>/', views.get_product_details, name='get_product_details'),
    path('api/create-sale/', views.create_sale, name='create_sale'),
    path('api/customer/search-create/', views.search_or_create_customer, name='search_or_create_customer'),
    path('api/customer/by-phone/<str:phone>/', views.get_customer_by_phone, name='get_customer_by_phone'),
    path('receipt/<int:sale_id>/', views.print_receipt, name='print_receipt'),
    path('daily-sales/', views.daily_sales_report, name='daily_sales'),
]