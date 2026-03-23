import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'womenconnect.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
new_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

try:
    user = User.objects.get(email=email)
    user.is_staff = True
    user.is_superuser = True
    user.set_password(new_password)
    user.username = 'admin'   # ← force a known username
    user.save()
    print(f"✅ Success! Login with:")
    print(f"   Username: admin")
    print(f"   Password: (your DJANGO_SUPERUSER_PASSWORD value)")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
except User.DoesNotExist:
    print(f"❌ No user found with email: {email}")
    print("All users:")
    for u in User.objects.all():
        print(f"  - {u.username} | {u.email}")