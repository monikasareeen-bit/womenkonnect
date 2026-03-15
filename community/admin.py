from django.contrib import admin
from .models import Category, UserProfile, Post, Reply

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified_woman', 'joined_date']
    list_filter = ['is_verified_woman', 'joined_date']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_at', 'total_likes']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at', 'total_likes']
    list_filter = ['created_at']
from .models import Notification, Report

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'from_user', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['description']
