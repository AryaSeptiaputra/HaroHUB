"""AppConfig untuk app common — validators, generators, templatetags, context_processors."""
from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
