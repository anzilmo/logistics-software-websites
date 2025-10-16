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

# Add the testweb directory to Python path so Django apps can be imported
import sys
testweb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'testweb')
sys.path.insert(0, testweb_dir)
logger.info(f"Added to Python path: {testweb_dir}")
logger.info(f"Updated Python path: {os.sys.path}")

# Check for common missing env vars
required_env_vars = ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
for var in required_env_vars:
    if var in os.environ:
        logger.info(f"{var}: SET")
    else:
        logger.warning(f"{var}: NOT SET")

# Check if dj_database_url is available
try:
    import dj_database_url
    logger.info("dj_database_url imported successfully")
except ImportError as e:
    logger.error(f"Failed to import dj_database_url: {e}")
    logger.error("This could cause database configuration issues")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testweb.settings")
logger.info(f"Final DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

try:
    app = get_wsgi_application()
    logger.info("WSGI application created successfully")
except Exception as e:
    logger.error(f"Failed to create WSGI application: {e}")
    raise