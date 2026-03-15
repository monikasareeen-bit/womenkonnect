# WomenConnect – PythonAnywhere Deployment Guide

## Step 1: Upload Files
Upload the entire project folder to `/home/yourusername/womenconnect`

## Step 2: Create Virtual Environment
```bash
mkvirtualenv womenconnect --python=python3.10
```

## Step 3: Install Requirements
```bash
cd /home/yourusername/womenconnect
pip install -r requirements.txt
```

## Step 4: Configure .env
```bash
cp .env.example .env
nano .env
```
Fill in:
- `SECRET_KEY` — generate one at https://djecrety.ir/
- `ALLOWED_HOSTS` — set to `yourusername.pythonanywhere.com`
- `SITE_URL` — `https://yourusername.pythonanywhere.com`
- `CSRF_TRUSTED_ORIGINS` — `https://yourusername.pythonanywhere.com`
- Email credentials

## Step 5: Configure WSGI
In PythonAnywhere Web tab → WSGI configuration file, replace contents with:
```python
import os
import sys

path = '/home/yourusername/womenconnect'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'womenconnect.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 6: Static Files
In PythonAnywhere Web tab → Static files:
- URL: `/static/`  →  Directory: `/home/yourusername/womenconnect/staticfiles`
- URL: `/media/`   →  Directory: `/home/yourusername/womenconnect/media`

Then run:
```bash
python manage.py collectstatic --noinput
```

## Step 7: Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

## Step 8: Reload
Click **Reload** in PythonAnywhere Web tab.

## Step 9: Add Categories
Go to `https://yourusername.pythonanywhere.com/admin/` and add your categories.
