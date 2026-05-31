from django.urls import path

from . import views

app_name = 'rekomendasi'

urlpatterns = [
    path('widget/similar/<int:product_id>/', views.widget_similar, name='widget_similar'),
    path('widget/for-you/', views.widget_for_you, name='widget_for_you'),
    path('wishlist/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
]
