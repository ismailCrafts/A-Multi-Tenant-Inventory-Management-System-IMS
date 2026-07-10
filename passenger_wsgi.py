import os
import sys

# Add the project root to Python path
PROJECT_ROOT = '/home/itbdsoft/ims_project_v1'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Tell Django which settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_project.settings')

# Load environment variables from .env file (before Django starts)
from pathlib import Path
env_file = Path(PROJECT_ROOT) / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ.setdefault(key.strip(), value.strip())

# Load Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()