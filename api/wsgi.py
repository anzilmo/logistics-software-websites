import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("WSGI app starting...")
logger.info("WSGI application initialized")

# Add environment variable checks
import os
logger.info(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Python path: {os.sys.path}")

# Check for common missing env vars
required_env_vars = ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
for var in required_env_vars:
    if var in os.environ:
        logger.info(f"{var}: SET")
    else:
        logger.warning(f"{var}: NOT SET")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testweb.testweb.settings")
logger.info(f"Final DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

try:
    app = get_wsgi_application()
    logger.info("WSGI application created successfully")
except Exception as e:
    logger.error(f"Failed to create WSGI application: {e}")
    raise