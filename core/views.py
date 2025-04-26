from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count
import json
import uuid
import random
import string
import qrcode
import io
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
import pytz
from .forms import (
    ProfileUpdateForm, OutletForm, 
    NFCCardForm, TopUpForm, PaymentForm, VolunteerCreationForm
)
from .models import (
    Profile, Outlet, USER_TYPE_CHOICES, NFCCard, NFCLog, 
    Transaction, TopupVolunteer, OutletVolunteer
)

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    mobile_no = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'mobile_no', 'password1', 'password2')

def home(request):
    return render(request, 'core/home.html')

# Signup is disabled - only admins can create users
def signup(request):
    # Redirect to login page with message
    messages.info(request, 'Signup is disabled. Please contact an administrator for access.')
    return redirect('login')

@login_required
def dashboard(request):
    # Debug logging for user and profile info
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
    try:
        profile = request.user.profile
        logger.debug(f"User profile found: {profile}, user_type: {profile.user_type}")
    except Profile.DoesNotExist:
        logger.debug("User profile does not exist")
        messages.error(request, 'Access denied. You do not have a valid profile.')
        return redirect('logout')

    # Check user type
    try:
        # Debug log the user type
        logger.debug(f"User type: {profile.user_type}")
        
        # If user is admin, redirect to management dashboard
        if request.user.is_staff:
            logger.debug("User is staff, redirecting to admin dashboard")
            return redirect('admin_dashboard')
        
        # If user is a topup volunteer
        elif profile.user_type == 'topup_volunteer':
            logger.debug("User is topup volunteer, preparing dashboard")
            # Verify TopupVolunteer record exists
            try:
                volunteer = TopupVolunteer.objects.get(user=request.user)
                if not volunteer.is_active:
                    logger.debug("Topup volunteer is not active")
                    messages.error(request, 'Your account is not active. Please contact an administrator.')
                    return redirect('logout')
            except TopupVolunteer.DoesNotExist:
                logger.debug("TopupVolunteer record not found")
                messages.error(request, 'Invalid volunteer account. Please contact an administrator.')
                return redirect('logout')
                
            # Get transactions where this topup volunteer is the user
            transactions = Transaction.objects.filter(
                user=request.user,
                payment_method__in=['cash', 'upi']  # Only show cash/upi top-ups
            ).order_by('-timestamp')
            
            # Calculate total amount collected
            total_collected = transactions.aggregate(total=Sum('amount'))['total'] or 0
            
            # Convert transaction timestamps to Indian Standard Time (IST)
            ist = pytz.timezone('Asia/Kolkata')
            for transaction in transactions:
                if transaction.timestamp:
                    transaction.timestamp = transaction.timestamp.astimezone(ist)
            
            logger.debug(f"Rendering topup volunteer dashboard with {transactions.count()} transactions")
            return render(request, 'core/topup_volunteer_dashboard.html', {
                'transactions': transactions,
                'total_sales': total_collected
            })
            
        # If user is an outlet
        elif profile.user_type == 'outlet':
            # Get outlet transactions
            if hasattr(request.user, 'outlet'):
                transactions = Transaction.objects.filter(outlet=request.user.outlet).order_by('-timestamp')
                total_sales = Transaction.objects.filter(outlet=request.user.outlet, status='completed').aggregate(total=Sum('amount'))['total'] or 0
                
                # Convert transaction timestamps to Indian Standard Time (IST)
                ist = pytz.timezone('Asia/Kolkata')
                for transaction in transactions:
                    if transaction.timestamp:
                        transaction.timestamp = transaction.timestamp.astimezone(ist)
            else:
                transactions = []
                total_sales = 0
                
            # Render outlet dashboard with transactions
            return render(request, 'core/outlet_dashboard.html', {
                'transactions': transactions,
                'total_sales': total_sales
            })
        
        # If user is an outlet volunteer
        elif profile.user_type == 'outlet_volunteer':
            # Get transactions where this outlet volunteer is the user
            transactions = Transaction.objects.filter(
                user=request.user,
                status='completed'
            ).order_by('-timestamp')
            
            # Calculate total amount collected
            total_collected = transactions.aggregate(total=Sum('amount'))['total'] or 0
            
            # Convert transaction timestamps to Indian Standard Time (IST)
            ist = pytz.timezone('Asia/Kolkata')
            for transaction in transactions:
                if transaction.timestamp:
                    transaction.timestamp = transaction.timestamp.astimezone(ist)
            
            # Render volunteer dashboard with payment access
            return render(request, 'core/volunteer_dashboard.html', {
                'transactions': transactions,
                'total_sales': total_collected,
                'can_accept_payment': True  # Add flag to enable payment link
            })
        
        # If user is neither admin, outlet, nor volunteer, show access denied
        else:
            messages.error(request, 'Access denied. You do not have permission to access the dashboard.')
            return redirect('logout')
            
    except Profile.DoesNotExist:
        # If profile doesn't exist, show access denied
        messages.error(request, 'Access denied. You do not have a valid profile.')
        return redirect('logout')

@login_required
def update_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
    
    # Initialize form with user data if profile fields are empty
    initial_data = {
        'first_name': profile.first_name or request.user.first_name,
        'last_name': profile.last_name or request.user.last_name,
        'email': profile.email or request.user.email,
        'mobile_no': profile.mobile_no
    }

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=profile, initial=initial_data)
    
    return render(request, 'core/update_profile.html', {'form': form})

# Admin-only views
def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    outlets = Outlet.objects.all()
    return render(request, 'core/admin_dashboard.html', {'outlets': outlets})

@user_passes_test(is_admin)
def create_outlet(request):
    if request.method == 'POST':
        form = OutletForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                
                # Get or update the profile (it should already exist from the signal)
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'email': form.cleaned_data['email'],
                        'user_type': 'outlet'
                    }
                )
                
                # If the profile already existed, update it
                if not created:
                    profile.email = form.cleaned_data['email']
                    profile.user_type = 'outlet'
                    profile.save()
                
                # Create outlet
                outlet = Outlet(
                    outlet_name=form.cleaned_data['outlet_name'],
                    address=form.cleaned_data['address'],
                    contact_person=form.cleaned_data['contact_person'],
                    phone_number=form.cleaned_data['phone_number'],
                    is_active=form.cleaned_data['is_active'],
                    user=user
                )
                outlet.save()
                
                messages.success(request, f'Outlet {outlet.outlet_name} created successfully!')
                return redirect('admin_dashboard')
    else:
        form = OutletForm()
    
    return render(request, 'core/create_outlet.html', {'form': form})

@user_passes_test(is_admin)
def create_volunteer(request):
    if request.method == 'POST':
        form = VolunteerCreationForm(request.POST)
        if form.is_valid():
            volunteer_type = form.cleaned_data.get('volunteer_type')
            form.save()
            messages.success(request, f'{volunteer_type.replace("_", " ").title()} created successfully!')
            return redirect('admin_dashboard')
    else:
        form = VolunteerCreationForm()
    
    return render(request, 'core/create_volunteer.html', {'form': form})

@user_passes_test(is_admin)
def update_outlet(request, outlet_id):
    outlet = get_object_or_404(Outlet, id=outlet_id)
    
    if request.method == 'POST':
        form = OutletForm(request.POST, instance=outlet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Outlet {outlet.outlet_name} updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = OutletForm(instance=outlet)
    
    return render(request, 'core/update_outlet.html', {'form': form, 'outlet': outlet})

@user_passes_test(is_admin)
def delete_outlet(request, outlet_id):
    outlet = get_object_or_404(Outlet, id=outlet_id)
    
    if request.method == 'POST':
        user = outlet.user
        outlet.delete()
        user.delete()  # This will cascade delete the profile as well
        messages.success(request, 'Outlet deleted successfully!')
        return redirect('admin_dashboard')
    
    return render(request, 'core/delete_outlet.html', {'outlet': outlet})

# Custom login view
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has a profile and is a topup volunteer
            try:
                profile = user.profile
                if profile.user_type == 'topup_volunteer':
                    # Verify TopupVolunteer record exists and is active
                    try:
                        volunteer = TopupVolunteer.objects.get(user=user)
                        if volunteer.is_active:
                            login(request, user)
                            return redirect('dashboard')
                        else:
                            messages.error(request, 'Your account is not active. Please contact an administrator.')
                            return render(request, 'core/login.html')
                    except TopupVolunteer.DoesNotExist:
                        messages.error(request, 'Invalid volunteer account. Please contact an administrator.')
                        return render(request, 'core/login.html')
                else:
                    # For non-volunteer users, proceed with normal login
                    login(request, user)
                    return redirect('dashboard')
            except Profile.DoesNotExist:
                messages.error(request, 'Your account does not have a valid profile. Please contact an administrator.')
                return render(request, 'core/login.html')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')

# Custom logout view
def custom_logout(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def email_view(request):
    """View for the Email page"""
    return render(request, 'core/email.html')

def contact_view(request):
    """View for the Contact page"""
    return render(request, 'core/contact.html')

def help_view(request):
    """View for the Help page"""
    return render(request, 'core/help.html')

def privacy_policy_view(request):
    """View for the Privacy Policy page"""
    return render(request, 'core/privacy_policy.html')

def terms_of_service_view(request):
    """View for the Terms of Service page"""
    return render(request, 'core/terms_of_service.html')

def about_us_view(request):
    """View for the About Us page"""
    return render(request, 'core/about_us.html')

# Card operation views
@login_required
def issue_card_view(request):
    """View for the issue card page"""
    # Check if user is admin or topup volunteer
    if not (request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'topup_volunteer')):
        messages.error(request, 'Access denied. Only administrators or topup volunteers can issue cards.')
        return redirect('dashboard')
    return render(request, 'core/issue_card.html')

@login_required
def top_up_view(request):
    """View for the top-up page"""
    # Check if user is admin or topup volunteer
    if not (request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.user_type == 'topup_volunteer')):
        messages.error(request, 'Access denied. Only administrators or topup volunteers can top-up cards.')
        return redirect('dashboard')
    return render(request, 'core/top_up.html')

@login_required
def balance_inquiry_view(request):
    """View for the balance inquiry page"""
    # Check if user is admin
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Only administrators can check card balances.')
        return redirect('dashboard')
    return render(request, 'core/balance_inquiry.html')

@login_required
def payment_view(request):
    """View for the payment page"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # The actual payment processing is handled by the JavaScript in the template
            # which calls the NFC API directly
            messages.success(request, 'Form is valid. Please scan the NFC card to complete the payment.')
            return render(request, 'core/payment.html', {'form': form})
    else:
        form = PaymentForm()
    
    return render(request, 'core/payment.html', {'form': form})

@login_required
def transactions_view(request):
    """View for listing transactions"""
    # Get transactions for the current outlet
    if hasattr(request.user, 'outlet'):
        transactions = Transaction.objects.filter(outlet=request.user.outlet).order_by('-timestamp')
        total_sales = Transaction.objects.filter(outlet=request.user.outlet, status='completed').aggregate(total=Sum('amount'))['total'] or 0
    else:
        transactions = []
        total_sales = 0
    
    return render(request, 'core/transactions.html', {
        'transactions': transactions,
        'total_sales': total_sales
    })

# QR code generation view
def generate_upi_qr(request):
    """Generate a QR code for UPI payment with the specified amount"""
    amount = request.GET.get('amount', '0')
    
    try:
        # Validate amount
        amount_float = float(amount)
        if amount_float <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        # Create UPI payment link (replace with your actual UPI ID)
        upi_id = "7898575626@fam"  # Replace with your actual UPI ID
        upi_link = f"upi://pay?pa={upi_id}&pn=NFC%20System&am={amount_float}&cu=INR"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_link)
        qr.make(fit=True)
        
        # Create an image from the QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Return the image as an HTTP response
        return HttpResponse(buffer, content_type="image/png")
    
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': str(e)}, status=400)

# NFC related views
@login_required
def nfc_reader(request):
    """View for the NFC reader interface"""
    # Get recent logs for this user/outlet
    recent_logs = []
    
    if hasattr(request.user, 'profile'):
        if request.user.profile.user_type == 'outlet' and hasattr(request.user, 'outlet'):
            # For outlet users, show logs for their outlet
            recent_logs = NFCLog.objects.filter(outlet=request.user.outlet).order_by('-timestamp')[:10]
        elif request.user.is_staff:
            # For admin users, show all logs
            recent_logs = NFCLog.objects.all().order_by('-timestamp')[:10]
    
    return render(request, 'core/nfc_reader.html', {
        'recent_logs': recent_logs
    })

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def nfc_management(request):
    """Admin view for managing NFC cards"""
    cards = NFCCard.objects.all().order_by('-created_at')
    logs = NFCLog.objects.all().order_by('-timestamp')[:20]
    
    # Handle form for creating/updating cards
    if request.method == 'POST':
        form = NFCCardForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'NFC card saved successfully!')
            return redirect('nfc_management')
    else:
        form = NFCCardForm()
    
    return render(request, 'core/nfc_management.html', {
        'cards': cards,
        'logs': logs,
        'form': form
    })

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def card_management(request):
    """Admin view for managing cards"""
    cards = NFCCard.objects.all().order_by('-created_at')
    logs = NFCLog.objects.all().order_by('-timestamp')[:20]
    
    # Handle form for creating/updating cards
    if request.method == 'POST':
        form = NFCCardForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Card saved successfully!')
            return redirect('card_management')
    else:
        form = NFCCardForm()
    
    return render(request, 'core/card_management.html', {
        'cards': cards,
        'logs': logs,
        'form': form
    })

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def create_nfc_card(request):
    """View for creating a new NFC card"""
    if request.method == 'POST':
        form = NFCCardForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'NFC card created successfully!')
            return redirect('nfc_management')
    else:
        form = NFCCardForm()
    
    return render(request, 'core/nfc_management.html', {
        'form': form,
        'cards': NFCCard.objects.all().order_by('-created_at'),
        'logs': NFCLog.objects.all().order_by('-timestamp')[:20]
    })

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def update_nfc_card(request, card_id):
    """View for updating an existing NFC card"""
    card = get_object_or_404(NFCCard, id=card_id)
    
    if request.method == 'POST':
        form = NFCCardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, 'NFC card updated successfully!')
            return redirect('nfc_management')
    else:
        form = NFCCardForm(instance=card)
    
    return render(request, 'core/nfc_management.html', {
        'form': form,
        'cards': NFCCard.objects.all().order_by('-created_at'),
        'logs': NFCLog.objects.all().order_by('-timestamp')[:20]
    })

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def delete_nfc_card(request, card_id):
    """View for deleting an NFC card"""
    card = get_object_or_404(NFCCard, id=card_id)
    
    if request.method == 'POST':
        card.delete()
        messages.success(request, 'NFC card deleted successfully!')
        return redirect('nfc_management')
    
    return render(request, 'core/delete_nfc_card.html', {
        'card': card
    })

@csrf_exempt
def nfc_api(request):
    """API endpoint for NFC card operations"""
    if request.method == 'POST':
        try:
            # Parse JSON data
            data = json.loads(request.body)
            card_id = data.get('card_id')
            secure_key = data.get('secure_key')
            action = data.get('action', '')
            
            # For initial card registration, we need the card_id
            if not card_id and not secure_key:
                return JsonResponse({'status': 'error', 'message': 'Card ID or Secure Key is required'}, status=400)
            
            # If this is a new card being registered
            if card_id and not secure_key and action not in ['balance_inquiry', 'top_up', 'payment']:
                # Get or create the card with a new secure key
                card, created = NFCCard.objects.get_or_create(
                    card_id=card_id,
                    defaults={'name': f'Card {card_id[:8]}...'}
                )
            # For transactions, use the secure key instead of card_id
            elif secure_key:
                try:
                    card = NFCCard.objects.get(secure_key=secure_key)
                    created = False
                except NFCCard.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Invalid secure key'}, status=400)
            # If only card_id is provided for transactions
            elif card_id:
                try:
                    card = NFCCard.objects.get(card_id=card_id)
                    created = False
                except NFCCard.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Card not found'}, status=400)
            
            # Enforce payment method restrictions for top_up and issue_card
            if action in ['top_up', 'issue_card']:
                payment_method = data.get('payment_method', 'cash')
                if payment_method not in ['cash', 'upi']:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid payment method for top-up or card issuance. Only cash and UPI are allowed.'
                    }, status=400)
            
            # Enforce NFC-only payment for outlets
            if action == 'payment':
                payment_method = data.get('payment_method', 'nfc')
                if payment_method != 'nfc':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid payment method for outlet payment. Only NFC payments are allowed.'
                    }, status=400)
            
            # Handle specific actions
            if action == 'issue_card':
                # Check if the card has already been issued
                if card.customer_name or card.mobile_number or float(card.balance) > 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This card has already been issued and cannot be re-issued.',
                        'card_id': card.card_id,
                        'customer_name': card.customer_name,
                        'mobile_number': card.mobile_number,
                        'balance': float(card.balance)
                    }, status=400)
                
                customer_name = data.get('customer_name', '')
                mobile_number = data.get('mobile_number', '')
                initial_balance = data.get('initial_balance', 0)
                payment_method = data.get('payment_method', 'cash')  # Default to cash if not provided
                
                # Update card with customer info and balance
                card.customer_name = customer_name
                card.mobile_number = mobile_number
                card.balance = initial_balance
                
                # Ensure the card has a secure_key (should be handled by pre_save signal, but double-check)
                if not card.secure_key:
                    # Generate a unique secure key
                    while True:
                        secure_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
                        if not NFCCard.objects.filter(secure_key=secure_key).exists():
                            card.secure_key = secure_key
                            break
                
                card.save()
                
                # Create transaction record for the card issuance
                transaction = Transaction.objects.create(
                    card=card,
                    card_identifier=card.card_id,
                    amount=initial_balance,
                    payment_method=payment_method,
                    previous_balance=0,
                    new_balance=initial_balance,
                    status='completed',
                    notes='Card issuance transaction'
                )
                
                # If user is authenticated, add user and outlet info
                if request.user.is_authenticated:
                    transaction.user = request.user
                    if hasattr(request.user, 'outlet'):
                        transaction.outlet = request.user.outlet
                    transaction.save()
                
                action_description = f"Card issued to {customer_name} with initial balance {initial_balance} (Payment: {payment_method})"
            
            elif action == 'top_up':
                amount = data.get('amount', 0)
                payment_method = data.get('payment_method', 'cash')  # Default to cash if not provided
                
                # Retrieve current balance
                current_balance = float(card.balance)
                # Calculate new balance
                new_balance = current_balance + float(amount)
                
                # Update card balance
                card.balance = new_balance
                card.save()
                
                # Create transaction record for the top-up
                transaction = Transaction.objects.create(
                    card=card,
                    card_identifier=card.card_id,
                    amount=amount,
                    payment_method=payment_method,
                    previous_balance=current_balance,
                    new_balance=new_balance,
                    status='completed',
                    notes='Top-up transaction'
                )
                
                # If user is authenticated, add user and outlet info
                if request.user.is_authenticated:
                    transaction.user = request.user
                    if hasattr(request.user, 'outlet'):
                        transaction.outlet = request.user.outlet
                    transaction.save()
                
                # Log the updated balance
                print(f"Updated balance for card {card.card_id}: {current_balance} + {amount} = {new_balance}")
                
                action_description = f"Top-up of {amount} added to card (Payment: {payment_method})"
            
            elif action == 'balance_inquiry':
                action_description = f"Balance inquiry: Current balance is {card.balance}"
            
            elif action == 'payment':
                amount = Decimal(data.get('amount', 0))
                notes = data.get('notes', '')
                
                # Enforce that user is an outlet for payment
                if not (request.user.is_authenticated and hasattr(request.user, 'outlet')):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Only outlet users can perform payments.'
                    }, status=403)
                
                # Check if card is active
                if not card.is_active:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This card is inactive and cannot be used for payment.'
                    }, status=400)
                
                # Check if card has sufficient balance
                if card.balance < amount:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Insufficient balance',
                        'balance': float(card.balance),
                        'amount': float(amount)
                    }, status=400)
                
                # Create transaction record with enforced payment_method='nfc'
                transaction = Transaction(
                    card=card,
                    card_identifier=card.card_id,
                    amount=amount,
                    payment_method='nfc',  # Enforced NFC for outlet payments
                    notes=notes
                )
                
                # If user is authenticated, add user and outlet info
                if request.user.is_authenticated:
                    transaction.user = request.user
                    if hasattr(request.user, 'outlet'):
                        transaction.outlet = request.user.outlet
                
                # For AJAX requests from JavaScript, try to get the user from the session
                elif 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
                    # Get the session key from the request
                    session_key = request.COOKIES.get('sessionid')
                    if session_key:
                        from django.contrib.sessions.models import Session
                        from django.contrib.auth.models import User
                        try:
                            # Get the session
                            session = Session.objects.get(session_key=session_key)
                            # Get the user_id from the session
                            user_id = session.get_decoded().get('_auth_user_id')
                            if user_id:
                                # Get the user
                                user = User.objects.get(pk=user_id)
                                transaction.user = user
                                # If the user has an outlet, add it to the transaction
                                if hasattr(user, 'outlet'):
                                    transaction.outlet = user.outlet
                        except (Session.DoesNotExist, User.DoesNotExist):
                            pass
                
                # Store the previous balance
                previous_balance = card.balance
                
                # Save transaction (this will update card balance in the save method)
                transaction.save()
                
                # Ensure the status is set to completed and save again
                transaction.status = 'completed'
                transaction.save()
                
                # Verify the balance was updated correctly
                if card.balance != previous_balance - amount:
                    # If not, update it manually
                    card.balance = max(Decimal('0.00'), previous_balance - amount)
                    card.save()
                    
                    # Update transaction with correct balances
                    transaction.previous_balance = previous_balance
                    transaction.new_balance = card.balance
                    transaction.save()
                
                action_description = f"Payment of {amount} processed. New balance: {card.balance}"
                
                # Add transaction info to response
                response_data = {
                    'status': 'success',
                    'card_id': card.card_id,
                    'secure_key': card.secure_key,
                    'action': action,
                    'transaction_id': str(transaction.id),
                    'amount': float(amount),
                    'previous_balance': float(transaction.previous_balance),
                    'new_balance': float(transaction.new_balance),
                    'timestamp': transaction.timestamp.isoformat()
                }
                
                # Create log entry
                log = NFCLog.objects.create(
                    card=card,
                    card_identifier=card.card_id,
                    action=action_description,
                    success=True,
                    notes=f"Transaction ID: {transaction.id}"
                )
                
                # If user is authenticated, add user and outlet info to log
                if request.user.is_authenticated:
                    log.user = request.user
                    if hasattr(request.user, 'outlet'):
                        log.outlet = request.user.outlet
                    log.save()
                
                response_data['log_id'] = str(log.id)
                
                return JsonResponse(response_data)
            
            else:
                action_description = action
            
            # Create log entry (for non-payment actions)
            log = NFCLog.objects.create(
                card=card,
                card_identifier=card_id or card.card_id,  # Use card.card_id as fallback if card_id is None
                action=action_description,
                success=True
            )
            
            # If user is authenticated, add user and outlet info
            if request.user.is_authenticated:
                log.user = request.user
                if hasattr(request.user, 'outlet'):
                    log.outlet = request.user.outlet
                log.save()
            
            response_data = {
                'status': 'success',
                'card_id': card.card_id,
                'secure_key': card.secure_key,
                'action': action,
                'card_registered': not created,
                'log_id': str(log.id)
            }
            
            # Add balance to response for balance inquiry
            if action == 'balance_inquiry':
                response_data['balance'] = float(card.balance)
                response_data['customer_name'] = card.customer_name
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    # Handle GET request - return basic info
    return JsonResponse({
        'status': 'ready',
        'message': 'NFC API is ready. Send POST requests with card_id and action.'
    })
