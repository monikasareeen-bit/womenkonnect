"""
WSGI config for womenconnect project.
Configured for PythonAnywhere deployment.
"""

import os
import sys

# ====================================================
# PythonAnywhere path setup
# Replace 'yourusername' with your actual PythonAnywhere username
# ====================================================
path = '/home/yourusername/womenconnect'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenconnect.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
