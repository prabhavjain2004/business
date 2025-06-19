from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Sum
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta
from .models import Profile, Outlet, NFCCard, NFCLog, Transaction, TopupVolunteer, OutletVolunteer

# Register your models here.
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('card_identifier', 'outlet', 'user', 'amount', 'payment_method', 'timestamp', 'status')
    list_filter = ('status', 'payment_method', 'outlet', 'timestamp')
    search_fields = ('card_identifier', 'notes')
    readonly_fields = ('timestamp', 'previous_balance', 'new_balance')
    date_hierarchy = 'timestamp'

class ProfileInline(admin.StackedInline):
    model = Profile

# Create a proxy model for analytics
class Analytics(Transaction):
    class Meta:
        proxy = True
        verbose_name = 'Analytics'
        verbose_name_plural = 'Analytics'

# Create a proxy model for user payment collection analytics
class PaymentCollectionAnalytics(Transaction):
    class Meta:
        proxy = True
        verbose_name = 'Collection Analytics'
        verbose_name_plural = 'Collection Analytics'

class PaymentCollectionAnalyticsAdmin(admin.ModelAdmin):
    """Admin model for user-wise payment collection analytics view"""
    change_list_template = 'admin/payment_collection_analytics_change_list.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_view_permission(self, request, obj=None):
        # Only allow superusers to view the analytics
        return request.user.is_superuser
    
    def has_module_permission(self, request):
        # Only show the analytics module to superusers
        return request.user.is_superuser
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export/', self.admin_site.admin_view(self.export_analytics), name='export_payment_collection'),
        ]
        return custom_urls + urls
    
    def export_analytics(self, request):
        """Export payment collection analytics data for a date range as CSV"""
        # Get date range from request
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        user_type_filter = request.GET.get('user_type', '')
        payment_method_filter = request.GET.get('payment_method', '')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # Default to last 30 days if dates are invalid
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payment_collection_{start_date}_to_{end_date}.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Create header row
        header = ['User', 'User Type', 'Cash Top-ups', 'Cash Amount (₹)', 'UPI Top-ups', 'UPI Amount (₹)', 'NFC Top-ups', 'NFC Amount (₹)', 'Total Top-ups', 'Total Amount (₹)']
        writer.writerow(header)
        
        # Calculate start and end datetime for the date range
        start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
        end_datetime = timezone.datetime.combine(end_date, timezone.datetime.max.time())
        
        # Get all transactions in the date range
        transactions_query = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            amount__gt=0  # Only top-ups (positive amounts)
        )
        
        # Apply payment method filter if provided
        if payment_method_filter:
            transactions_query = transactions_query.filter(payment_method=payment_method_filter)
        
        transactions = transactions_query
        
        # Group transactions by user
        user_data = {}
        
        for transaction in transactions:
            if transaction.user:
                user_id = transaction.user.id
                username = transaction.user.username
                
                # Get user type and filter out outlets
                user_type = "Unknown"
                try:
                    if transaction.user.is_staff:
                        user_type = "Admin"
                    elif hasattr(transaction.user, 'profile'):
                        user_type = transaction.user.profile.get_user_type_display().capitalize()
                        if user_type.lower() == 'outlet':
                            continue  # Skip outlets
                except:
                    pass
                
                # Apply user type filter if provided
                if user_type_filter and user_type.lower() != user_type_filter.lower():
                    continue
                
                if user_id not in user_data:
                    user_data[user_id] = {
                        'username': username,
                        'user_type': user_type,
                        'cash_topups': 0,
                        'cash_amount': 0,
                        'upi_topups': 0,
                        'upi_amount': 0,
                        'nfc_topups': 0,
                        'nfc_amount': 0,
                        'total_topups': 0,
                        'total_amount': 0
                    }
                
                # Update counts and amounts
                amount = abs(transaction.amount)
                user_data[user_id]['total_topups'] += 1
                user_data[user_id]['total_amount'] += amount
                
                if transaction.payment_method == 'cash':
                    user_data[user_id]['cash_topups'] += 1
                    user_data[user_id]['cash_amount'] += amount
                elif transaction.payment_method == 'upi':
                    user_data[user_id]['upi_topups'] += 1
                    user_data[user_id]['upi_amount'] += amount
                elif transaction.payment_method == 'nfc':
                    user_data[user_id]['nfc_topups'] += 1
                    user_data[user_id]['nfc_amount'] += amount
        
        # Sort users by total amount (descending)
        sorted_users = sorted(
            user_data.values(),
            key=lambda x: x['total_amount'],
            reverse=True
        )
        
        # Write data rows
        for user in sorted_users:
            writer.writerow([
                user['username'],
                user['user_type'],
                user['cash_topups'],
                user['cash_amount'],
                user['upi_topups'],
                user['upi_amount'],
                user['nfc_topups'],
                user['nfc_amount'],
                user['total_topups'],
                user['total_amount']
            ])
        
        return response
    
    def changelist_view(self, request, extra_context=None):
        # Check if export action is requested
        if 'export' in request.GET:
            return self.export_analytics(request)
        
        # Get the selected date range from the request or use default (last 30 days)
        end_date = timezone.now().date()
        
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        user_type_filter = request.GET.get('user_type', '')
        payment_method_filter = request.GET.get('payment_method', '')
        
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = end_date - timedelta(days=30)
                
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
        
        # Calculate start and end datetime for the date range
        start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
        end_datetime = timezone.datetime.combine(end_date, timezone.datetime.max.time())
        
        # Get all transactions in the date range
        transactions_query = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            amount__gt=0  # Only top-ups (positive amounts)
        )
        
        # Apply payment method filter if provided
        if payment_method_filter:
            transactions_query = transactions_query.filter(payment_method=payment_method_filter)
        
        transactions = transactions_query
        
        # Group transactions by user
        user_data = {}
        
        for transaction in transactions:
            if transaction.user:
                user_id = transaction.user.id
                username = transaction.user.username
                
                # Get user type and filter out outlets
                user_type = "Unknown"
                try:
                    if transaction.user.is_staff:
                        user_type = "Admin"
                    elif hasattr(transaction.user, 'profile'):
                        user_type = transaction.user.profile.get_user_type_display().capitalize()
                        if user_type.lower() == 'outlet':
                            continue  # Skip outlets
                except:
                    pass
                
                # Apply user type filter if provided
                if user_type_filter and user_type.lower() != user_type_filter.lower():
                    continue
                
                if user_id not in user_data:
                    user_data[user_id] = {
                        'username': username,
                        'user_type': user_type,
                        'cash_topups': 0,
                        'cash_amount': 0,
                        'upi_topups': 0,
                        'upi_amount': 0,
                        'nfc_topups': 0,
                        'nfc_amount': 0,
                        'total_topups': 0,
                        'total_amount': 0
                    }
                
                # Update counts and amounts
                amount = abs(transaction.amount)
                user_data[user_id]['total_topups'] += 1
                user_data[user_id]['total_amount'] += amount
                
                if transaction.payment_method == 'cash':
                    user_data[user_id]['cash_topups'] += 1
                    user_data[user_id]['cash_amount'] += amount
                elif transaction.payment_method == 'upi':
                    user_data[user_id]['upi_topups'] += 1
                    user_data[user_id]['upi_amount'] += amount
                elif transaction.payment_method == 'nfc':
                    user_data[user_id]['nfc_topups'] += 1
                    user_data[user_id]['nfc_amount'] += amount
        
        # Sort users by total amount (descending)
        sorted_users = sorted(
            user_data.values(),
            key=lambda x: x['total_amount'],
            reverse=True
        )
        
        # Calculate totals
        total_cash_topups = sum(user['cash_topups'] for user in user_data.values())
        total_cash_amount = sum(user['cash_amount'] for user in user_data.values())
        total_upi_topups = sum(user['upi_topups'] for user in user_data.values())
        total_upi_amount = sum(user['upi_amount'] for user in user_data.values())
        total_nfc_topups = sum(user['nfc_topups'] for user in user_data.values())
        total_nfc_amount = sum(user['nfc_amount'] for user in user_data.values())
        total_topups = total_cash_topups + total_upi_topups + total_nfc_topups
        total_amount = total_cash_amount + total_upi_amount + total_nfc_amount
        
        # Prepare context with filter options
        context = {
            'title': 'Payment Collection Analytics',
            'start_date': start_date,
            'end_date': end_date,
            'user_data': sorted_users,
            'total_cash_topups': total_cash_topups,
            'total_cash_amount': total_cash_amount,
            'total_upi_topups': total_upi_topups,
            'total_upi_amount': total_upi_amount,
            'total_nfc_topups': total_nfc_topups,
            'total_nfc_amount': total_nfc_amount,
            'total_topups': total_topups,
            'total_amount': total_amount,
            'user_type_filter': user_type_filter,
            'payment_method_filter': payment_method_filter,
            'user_types': ['Admin', 'Topup Volunteers'],  # Available user type filters
            'payment_methods': ['cash', 'upi', 'nfc'],  # Available payment method filters
        }
        
        if extra_context:
            context.update(extra_context)
        
        return super().changelist_view(request, context)

# Register the analytics views
# admin.site.register(Analytics, AnalyticsAdmin)
admin.site.register(PaymentCollectionAnalytics, PaymentCollectionAnalyticsAdmin)

# Register volunteers
admin.site.register(TopupVolunteer)
admin.site.register(OutletVolunteer)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'email', 'mobile_no')
    search_fields = ('user__username', 'email', 'mobile_no')
    list_filter = ('user_type',)

class OutletAdmin(admin.ModelAdmin):
    list_display = ('outlet_name', 'contact_person', 'phone_number', 'is_active')
    search_fields = ('outlet_name', 'contact_person', 'phone_number')
    list_filter = ('is_active',)

class NFCCardAdmin(admin.ModelAdmin):
    list_display = ('card_id', 'customer', 'balance', 'is_active')
    search_fields = ('card_id', 'customer__name')
    list_filter = ('is_active',)

class NFCLogAdmin(admin.ModelAdmin):
    list_display = ('card_identifier', 'outlet', 'user', 'timestamp', 'action', 'success')
    search_fields = ('card_identifier', 'action', 'notes')
    list_filter = ('success', 'timestamp')

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Outlet, OutletAdmin)
admin.site.register(NFCCard, NFCCardAdmin)
admin.site.register(NFCLog, NFCLogAdmin)
