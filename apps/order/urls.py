"""URL configuration untuk app order (namespace: order)."""
from django.urls import path

from . import views

app_name = 'order'

urlpatterns = [
    path('', views.order_list_view, name='list'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('shipping-preview/', views.shipping_preview_view, name='shipping_preview'),
    path('<str:order_number>/', views.order_detail_view, name='detail'),
    path('<str:order_number>/payment/', views.payment_view, name='payment'),
    path('<str:order_number>/cancel/', views.cancel_order_view, name='cancel'),
]
