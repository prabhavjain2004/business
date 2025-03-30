from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from .forms import ProfileUpdateForm, OutletCreationForm, OutletUpdateForm, NFCCardForm, NFCLogForm
from .models import Profile, Outlet, USER_TYPE_CHOICES, NFCCard, NFCLog

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
    # Check user type
    try:
        # If user is admin, redirect to management dashboard
        if request.user.is_staff:
            return redirect('admin_dashboard')  # This still uses the name 'admin_dashboard' but points to /management/dashboard/
        
        # If user is an outlet
        elif hasattr(request.user, 'profile') and request.user.profile.user_type == 'outlet':
            # Redirect to outlet dashboard
            return render(request, 'core/outlet_dashboard.html')
        
        # If user is neither admin nor outlet, show access denied
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
        form = OutletCreationForm(request.POST)
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
                outlet = form.save(commit=False)
                outlet.user = user
                outlet.save()
                
                messages.success(request, f'Outlet {outlet.outlet_name} created successfully!')
                return redirect('admin_dashboard')
    else:
        form = OutletCreationForm()
    
    return render(request, 'core/create_outlet.html', {'form': form})

@user_passes_test(is_admin)
def update_outlet(request, outlet_id):
    outlet = get_object_or_404(Outlet, id=outlet_id)
    
    if request.method == 'POST':
        form = OutletUpdateForm(request.POST, instance=outlet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Outlet {outlet.outlet_name} updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = OutletUpdateForm(instance=outlet)
    
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
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')

# Custom logout view
def custom_logout(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# Card operation views
@login_required
def issue_card_view(request):
    """View for the issue card page"""
    return render(request, 'core/issue_card.html')

@login_required
def top_up_view(request):
    """View for the top-up page"""
    return render(request, 'core/top_up.html')

@login_required
def balance_inquiry_view(request):
    """View for the balance inquiry page"""
    return render(request, 'core/balance_inquiry.html')

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
            if card_id and not secure_key and action != 'balance_inquiry' and action != 'top_up':
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
            
            # Handle specific actions
            if action == 'issue_card':
                customer_name = data.get('customer_name', '')
                mobile_number = data.get('mobile_number', '')
                initial_balance = data.get('initial_balance', 0)
                
                # Update card with customer info and balance
                card.customer_name = customer_name
                card.mobile_number = mobile_number
                card.balance = initial_balance
                card.save()
                
                action_description = f"Card issued to {customer_name} with initial balance {initial_balance}"
            
            elif action == 'top_up':
                amount = data.get('amount', 0)
                
                # Add amount to card balance
                card.balance += float(amount)
                card.save()
                
                action_description = f"Top-up of {amount} added to card"
            
            elif action == 'balance_inquiry':
                action_description = f"Balance inquiry: Current balance is {card.balance}"
            
            else:
                action_description = action
            
            # Create log entry
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
