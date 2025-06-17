from django.contrib.auth import views as auth_views
from django.urls import path, include
from . import views

urlpatterns = [
    # Main routes
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Customer details page and email verification
    path('customer-details/', views.customer_details_view, name='customer_details'),
    path('customer-details/verify-email/', views.verify_email_view, name='verify_email'),
    
    # Password reset routes
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
    
    # Profile routes
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Admin routes
    path('management/', include([
        path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
        path('outlets/', include([
            path('create/', views.create_outlet, name='create_outlet'),
            path('<int:outlet_id>/update/', views.update_outlet, name='update_outlet'),
            path('<int:outlet_id>/delete/', views.delete_outlet, name='delete_outlet'),
        ])),
        path('volunteers/', include([
            path('create/', views.create_volunteer, name='create_volunteer'),
            path('create_topup_volunteer/', views.create_volunteer, name='create_topup_volunteer'),
        ])),
    ])),
    
    # NFC related routes
    path('nfc/', include([
        path('reader/', views.nfc_reader, name='nfc_reader'),
        path('management/', views.nfc_management, name='nfc_management'),
        path('cards/', include([
            path('create/', views.create_nfc_card, name='create_nfc_card'),
            path('<uuid:card_id>/update/', views.update_nfc_card, name='update_nfc_card'),
            path('<uuid:card_id>/delete/', views.delete_nfc_card, name='delete_nfc_card'),
        ])),
        path('api/', views.nfc_api, name='nfc_api'),
    ])),
    
    # Card management
    path('management/cards/', views.card_management, name='card_management'),
    
    # Card operation pages
    path('cards/', include([
        path('issue/', views.issue_card_view, name='issue_card'),
        path('top-up/', views.top_up_view, name='top_up'),
        path('balance/', views.balance_inquiry_view, name='balance_inquiry'),
        path('payment/', views.payment_view, name='payment'),
    ])),
    path('transactions/', views.transactions_view, name='transactions'),
    
    # Volunteer dashboard
    path('topup_volunteer/dashboard/', views.dashboard, name='topup_volunteer_dashboard'),
    
    # QR code generation
    path('api/generate-upi-qr/', views.generate_upi_qr, name='generate_upi_qr'),
    
    # Footer pages
    path('info/', include([
        path('email/', views.email_view, name='email'),
        path('contact/', views.contact_view, name='contact'),
        path('help/', views.help_view, name='help'),
        path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
        path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
        path('about-us/', views.about_us_view, name='about_us'),
    ])),
]
