# WomenConnect - Complete Setup Guide

## 🎯 What You've Already Done:
✅ Created models (Category, Post, Reply, UserProfile)
✅ Created views (all CRUD operations)
✅ Created URLs routing
✅ Created templates: base.html, home.html, category_posts.html, create_post.html, login.html, register.html
✅ Added categories in admin

## 📋 What You Need to Do Next:

### Step 1: Copy the New Templates to Your Project

Copy these 6 new template files I just created to your `templates/community/` folder:

1. **post_detail.html** - Shows full post with replies
2. **edit_post.html** - Edit a post
3. **delete_post.html** - Delete confirmation for posts
4. **edit_reply.html** - Edit a reply
5. **delete_reply.html** - Delete confirmation for replies
6. **profile.html** - User profile page

📁 File location: `your_project/templates/community/`

---

### Step 2: Run Database Migrations

Open your terminal/command prompt in your project directory and run:

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create all the database tables for your models.

---

### Step 3: Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Enter a username, email (optional), and password when prompted.

---

### Step 4: Configure Settings.py

Make sure your `settings.py` has these configurations:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'community',  # Your app name
]

# Add at the bottom of settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Login/Logout redirects
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
```

---

### Step 5: Create Static Folders (if not already created)

Create these folders in your project root:
- `static/` - For CSS, JS, images
- `media/` - For user uploads (profile pictures)

---

### Step 6: Update admin.py to Manage Your Models

Edit your `community/admin.py`:

```python
from django.contrib import admin
from .models import Category, Post, Reply, UserProfile

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_at', 'total_likes']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at', 'total_likes']
    list_filter = ['created_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified_woman', 'joined_date']
    list_filter = ['is_verified_woman', 'joined_date']
```

---

### Step 7: Add Sample Categories (if not done already)

1. Run the server: `python manage.py runserver`
2. Go to: `http://127.0.0.1:8000/admin/`
3. Login with your superuser credentials
4. Click on "Categories" → "Add Category"

Add these categories:

| Name | Slug | Icon | Color | Description |
|------|------|------|-------|-------------|
| Pregnancy Journey | pregnancy-journey | 🤰 | #FF69B4 | Share your pregnancy experiences and tips |
| Infant Care | infant-care | 👶 | #FFB6C1 | Everything about newborns and babies |
| Kids Routine & Diet | kids-routine-diet | 🍎 | #FF1493 | Daily routines and healthy eating for kids |
| Teenage Years | teenage-years | 👧 | #FF85C1 | Navigating the teenage phase |
| Health & Self Care | health-self-care | 💖 | #FF6B9D | Wellness and self-care tips |
| Office Fashion | office-fashion | 👔 | #C71585 | Professional wardrobe ideas |
| Wedding Fashion | wedding-fashion | 👰 | #FF1493 | Bridal and wedding attire |
| Body Fitness | body-fitness | 💪 | #FF69B4 | Fitness routines and goals |
| Skin Care | skin-care | ✨ | #FFB6D9 | Beauty and skincare routines |
| House Management | house-management | 🏠 | #FF85A1 | Home organization and cleaning |
| Budget & Finance | budget-finance | 💰 | #FF1493 | Money management tips |

---

### Step 8: Test Your Website

1. Start the server:
```bash
python manage.py runserver
```

2. Visit: `http://127.0.0.1:8000/`

3. Test these features:
   - ✅ Register a new user
   - ✅ Login
   - ✅ Browse categories
   - ✅ Create a post
   - ✅ View post details
   - ✅ Add a reply
   - ✅ Like a post/reply
   - ✅ Edit your post (within 24 hours)
   - ✅ Delete your post (within 24 hours)
   - ✅ View your profile

---

### Step 9: Optional Enhancements

#### A. Add Search Functionality
Create a search view to find posts by keywords.

#### B. Add Pagination
For category pages with many posts, add pagination.

#### C. Email Verification
Require email verification for new users.

#### D. Profile Picture Upload
Allow users to upload profile pictures.

#### E. Notifications
Notify users when someone replies to their post.

---

### Step 10: Deployment Checklist (When Ready)

Before deploying to production:

1. Set `DEBUG = False` in settings.py
2. Add your domain to `ALLOWED_HOSTS`
3. Use environment variables for SECRET_KEY
4. Set up a production database (PostgreSQL recommended)
5. Configure static files collection
6. Set up proper media file handling
7. Add SSL certificate (HTTPS)

---

## 🐛 Common Issues & Solutions

### Issue 1: Template Not Found
**Solution**: Make sure templates are in `templates/community/` folder

### Issue 2: Static Files Not Loading
**Solution**: 
```python
# In settings.py
import os
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
```

### Issue 3: Images Not Uploading
**Solution**: Make sure `MEDIA_URL` and `MEDIA_ROOT` are configured

### Issue 4: Can't Edit Posts
**Solution**: Check that `timezone` is properly configured in settings.py:
```python
USE_TZ = True
TIME_ZONE = 'UTC'  # or your timezone
```

---

## 📝 Next Steps for Your Site

1. **Add more features**:
   - Search functionality
   - User blocking/reporting
   - Private messaging
   - Bookmarking posts
   - Following other users

2. **Improve security**:
   - Add CAPTCHA to registration
   - Rate limiting for posts
   - Content moderation

3. **Enhance UI**:
   - Add dark mode
   - Mobile responsive design improvements
   - Add animations

4. **Add analytics**:
   - Track popular posts
   - User engagement metrics
   - Category statistics

---

## 🎨 Customization Tips

### Change Color Scheme
Edit the pink colors in your templates:
- `#FF69B4` - Hot Pink
- `#FF1493` - Deep Pink
- Replace with your preferred colors

### Add Custom Fonts
Add to base.html:
```html
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
```

---

## 📞 Need Help?

If you encounter any issues:
1. Check Django documentation
2. Review error messages in terminal
3. Check browser console for JavaScript errors
4. Verify all files are in correct locations

---

## ✅ Final Checklist

- [ ] All templates copied to correct folder
- [ ] Database migrations run
- [ ] Superuser created
- [ ] Categories added in admin
- [ ] Website tested and working
- [ ] All features tested (create, edit, delete, like, reply)
- [ ] Profile page accessible
- [ ] 24-hour edit window working

**Congratulations! Your WomenConnect community site is ready! 🎉**