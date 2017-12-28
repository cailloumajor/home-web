"""
WSGI config for home_web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home_web.settings")

from configurations.wsgi import get_wsgi_application  # noqa

application = get_wsgi_application()
