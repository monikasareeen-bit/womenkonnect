from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='community/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='community/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='community/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='community/password_reset_complete.html'), name='password_reset_complete'),
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('post/<int:pk>/report/', views.report_post, name='report_post'),
    path('reply/<int:pk>/report/', views.report_reply, name='report_reply'),


    # Static Pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Categories
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),

    # Posts
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/create/<slug:category_slug>/', views.create_post, name='create_post_in_category'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/pin/', views.pin_post, name='pin_post'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),

    # Replies
    path('post/<int:pk>/reply/', views.add_reply, name='add_reply'),
    path('reply/<int:pk>/edit/', views.edit_reply, name='edit_reply'),
    path('reply/<int:pk>/delete/', views.delete_reply, name='delete_reply'),
    path('reply/<int:pk>/like/', views.like_reply, name='like_reply'),

    # Search
    path('search/', views.search, name='search'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/count/', views.unread_notifications_count, name='unread_notifications_count'),
    path('check-users/', views.check_users, name='check_users'),
    path('create-admin/', views.create_admin),
]