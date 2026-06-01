"""URL configuration untuk app catalog (namespace: catalog)."""
from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.listing_view, name='listing'),
    path('catalog/search/', views.search_autocomplete_view, name='search_autocomplete'),
    path('catalog/series/', views.series_for_timeline_view, name='series_for_timeline'),
    path('catalog/<slug:slug>/', views.detail_view, name='detail'),
]
