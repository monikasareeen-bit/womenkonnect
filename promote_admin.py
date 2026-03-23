import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenconnect.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
print('DEBUG: username=' + username + ' email=' + email + ' pass_len=' + str(len(password)))
user, created = User.objects.get_or_create(username=username)
user.email = email
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()
print('SUCCESS: ' + ('CREATED' if created else 'UPDATED') + ' ' + username)
