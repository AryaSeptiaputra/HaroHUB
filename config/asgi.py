"""ASGI entrypoint untuk deployment async (Uvicorn, Daphne, dsb.)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_asgi_application()
