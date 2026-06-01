"""AppConfig untuk app core — abstract models, tidak punya views/urls/migrations."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
