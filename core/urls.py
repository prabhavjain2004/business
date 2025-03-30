from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Admin routes - using 'management' instead of 'admin' to avoid conflict with Django admin
    path('management/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('management/outlets/create/', views.create_outlet, name='create_outlet'),
    path('management/outlets/<int:outlet_id>/update/', views.update_outlet, name='update_outlet'),
    path('management/outlets/<int:outlet_id>/delete/', views.delete_outlet, name='delete_outlet'),
    
    # NFC related routes
    path('nfc/reader/', views.nfc_reader, name='nfc_reader'),
    path('nfc/management/', views.nfc_management, name='nfc_management'),
    path('nfc/cards/create/', views.create_nfc_card, name='create_nfc_card'),
    path('nfc/cards/<uuid:card_id>/update/', views.update_nfc_card, name='update_nfc_card'),
    path('nfc/cards/<uuid:card_id>/delete/', views.delete_nfc_card, name='delete_nfc_card'),
    path('api/nfc/', views.nfc_api, name='nfc_api'),
]
