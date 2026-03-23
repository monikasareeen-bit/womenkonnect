import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenconnect.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
new_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
new_username = os.environ.get('DJANGO_SUPERUSER_USERNAME')

try:
    user = User.objects.get(email=email)
    user.is_staff = True
    user.is_superuser = True
    user.set_password(new_password)
    if new_username:
        user.username = new_username
    user.save()
    print(f"✅ Success!")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
except User.DoesNotExist:
    print(f"❌ No user found with email: {email}")
    print("All users in database:")
    for u in User.objects.all():
        print(f"  - username: {u.username} | email: {u.email} | staff: {u.is_staff}")