from django.urls import path

from . import views

app_name = 'produk'

urlpatterns = [
    path('', views.listing_view, name='listing'),
    # Static paths dulu sebelum <slug:slug> agar tidak dikira slug
    path('produk/search/', views.search_autocomplete_view, name='search_autocomplete'),
    path('produk/series/', views.series_for_timeline_view, name='series_for_timeline'),
    path('produk/<slug:slug>/', views.detail_view, name='detail'),
]
