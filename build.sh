#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenconnect.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists():
    User.objects.create_superuser(
        os.environ['admin'],
        os.environ['monikasareeen@gmail.com'],
        os.environ['Satija2026!']
    )
    print('Superuser created.')
else:
    print('Superuser already exists, skipping.')
"
