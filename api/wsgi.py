import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("WSGI app starting...")
logger.info("WSGI application initialized")
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testweb.testweb.settings")
app = get_wsgi_application()