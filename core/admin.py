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
from .models import Profile, Outlet, NFCCard, NFCLog, Transaction, Volunteer

# Register your models here.
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('card_identifier', 'outlet', 'user', 'amount', 'payment_method', 'timestamp', 'status')
    list_filter = ('status', 'payment_method', 'outlet', 'timestamp')
    search_fields = ('card_identifier', 'notes')
    readonly_fields = ('timestamp', 'previous_balance', 'new_balance')
    date_hierarchy = 'timestamp'

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class VolunteerInline(admin.StackedInline):
    model = Volunteer
    can_delete = False
    verbose_name_plural = 'Volunteer Details'
    fk_name = 'user'

class OutletInline(admin.StackedInline):
    model = Outlet
    can_delete = False
    verbose_name_plural = 'Outlet'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_user_type')
    list_select_related = ('profile',)

    def get_user_type(self, instance):
        try:
            return instance.profile.user_type
        except Profile.DoesNotExist:
            return ''
    get_user_type.short_description = 'User Type'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        
        inline_instances = []
        for inline_class in self.inlines:
            if inline_class == OutletInline and hasattr(obj, 'profile') and obj.profile.user_type != 'outlet':
                continue
            if inline_class == VolunteerInline and hasattr(obj, 'profile') and obj.profile.user_type != 'volunteer':
                continue
            inline = inline_class(self.model, self.admin_site)
            inline_instances.append(inline)
        return inline_instances

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        
        inlines = []
        if hasattr(obj, 'profile') and obj.profile.user_type == 'outlet':
            inlines = [ProfileInline, OutletInline]
        elif hasattr(obj, 'profile') and obj.profile.user_type == 'volunteer':
            inlines = [ProfileInline, VolunteerInline]
        else:
            inlines = [ProfileInline]
        return inlines

class OutletAdmin(admin.ModelAdmin):
    list_display = ('outlet_name', 'contact_person', 'phone_number', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('outlet_name', 'contact_person', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

class NFCCardAdmin(admin.ModelAdmin):
    list_display = ('card_id', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('card_id', 'name')
    readonly_fields = ('created_at', 'updated_at')

class NFCLogAdmin(admin.ModelAdmin):
    list_display = ('card_identifier', 'outlet', 'user', 'timestamp', 'action', 'success')
    list_filter = ('success', 'action', 'outlet')
    search_fields = ('card_identifier', 'notes')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

class AnalyticsAdmin(admin.ModelAdmin):
    """Admin model for analytics view"""
    change_list_template = 'admin/analytics_change_list.html'
    
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
            path('export/', self.admin_site.admin_view(self.export_analytics), name='export_analytics'),
        ]
        return custom_urls + urls
    
    def export_analytics(self, request):
        """Export analytics data for a date range as CSV"""
        # Get date range from request
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # Default to last 30 days if dates are invalid
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{start_date}_to_{end_date}.csv"'
        
        # Get all outlets
        outlets = Outlet.objects.filter(is_active=True)
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Create header row with outlet names
        header = ['Date', 'Cards Issued', 'Total Top-ups', 'Top-up Amount', 'Total Payments', 'Payment Amount']
        for outlet in outlets:
            header.extend([
                f'{outlet.outlet_name} - Transactions',
                f'{outlet.outlet_name} - Top-ups',
                f'{outlet.outlet_name} - Top-up Amount',
                f'{outlet.outlet_name} - Payments',
                f'{outlet.outlet_name} - Payment Amount'
            ])
        
        writer.writerow(header)
        
        # Generate data for each day in the range
        current_date = start_date
        while current_date <= end_date:
            # Calculate start and end datetime for the current date
            start_datetime = timezone.datetime.combine(current_date, timezone.datetime.min.time())
            end_datetime = timezone.datetime.combine(current_date, timezone.datetime.max.time())
            
            # Get analytics data for the current date
            cards_issued = NFCCard.objects.filter(
                created_at__range=(start_datetime, end_datetime)
            ).count()
            
            # Get topup transactions (negative amounts)
            topups = Transaction.objects.filter(
                timestamp__range=(start_datetime, end_datetime),
                amount__lt=0  # Negative amounts are topups
            )
            
            # Get payment transactions (positive amounts)
            payments = Transaction.objects.filter(
                timestamp__range=(start_datetime, end_datetime),
                amount__gt=0  # Positive amounts are payments
            )
            
            # Calculate totals
            total_topups = topups.count()
            topup_amount = abs(topups.aggregate(Sum('amount'))['amount__sum'] or 0)
            total_payments = payments.count()
            payment_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Get transactions by outlet for the current date
            all_transactions = Transaction.objects.filter(
                timestamp__range=(start_datetime, end_datetime)
            )
            
            # Group transactions by outlet
            outlet_transactions = {}
            for outlet in outlets:
                outlet_transactions[outlet.id] = {
                    'count': 0,
                    'topups': 0,
                    'topup_amount': 0,
                    'payments': 0,
                    'payment_amount': 0
                }
            
            for transaction in all_transactions:
                if transaction.outlet and transaction.outlet.id in outlet_transactions:
                    outlet_id = transaction.outlet.id
                    outlet_transactions[outlet_id]['count'] += 1
                    
                    if transaction.amount < 0:  # Topup
                        outlet_transactions[outlet_id]['topups'] += 1
                        outlet_transactions[outlet_id]['topup_amount'] += abs(transaction.amount)
                    else:  # Payment
                        outlet_transactions[outlet_id]['payments'] += 1
                        outlet_transactions[outlet_id]['payment_amount'] += transaction.amount
            
            # Create row for current date
            row = [
                current_date.strftime('%Y-%m-%d'),
                cards_issued,
                total_topups,
                topup_amount,
                total_payments,
                payment_amount
            ]
            
            # Add outlet-specific data
            for outlet in outlets:
                outlet_data = outlet_transactions.get(outlet.id, {
                    'count': 0,
                    'topups': 0,
                    'topup_amount': 0,
                    'payments': 0,
                    'payment_amount': 0
                })
                
                row.extend([
                    outlet_data['count'],
                    outlet_data['topups'],
                    outlet_data['topup_amount'],
                    outlet_data['payments'],
                    outlet_data['payment_amount']
                ])
            
            # Write row
            writer.writerow(row)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return response
    
    def changelist_view(self, request, extra_context=None):
        # Check if export action is requested
        if 'export' in request.GET:
            return self.export_analytics(request)
        
        # Get the selected date from the request or use today
        date_str = request.GET.get('date')
        if date_str:
            try:
                selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = timezone.now().date()
        else:
            selected_date = timezone.now().date()
        
        # Calculate start and end datetime for the selected date
        start_datetime = timezone.datetime.combine(selected_date, timezone.datetime.min.time())
        end_datetime = timezone.datetime.combine(selected_date, timezone.datetime.max.time())
        
        # Get analytics data for the selected date
        cards_issued = NFCCard.objects.filter(
            created_at__range=(start_datetime, end_datetime)
        ).count()
        
        # Get topup transactions (negative amounts)
        topups = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            amount__lt=0  # Negative amounts are topups
        )
        
        # Get payment transactions (positive amounts)
        payments = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            amount__gt=0  # Positive amounts are payments
        )
        
        # Calculate totals
        total_topups = topups.count()
        topup_amount = abs(topups.aggregate(Sum('amount'))['amount__sum'] or 0)
        total_payments = payments.count()
        payment_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get transactions by outlet
        all_transactions = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime)
        )
        
        # Group transactions by outlet
        outlet_transactions = {}
        for transaction in all_transactions:
            if transaction.outlet:
                outlet_name = transaction.outlet.outlet_name
                if outlet_name not in outlet_transactions:
                    outlet_transactions[outlet_name] = {
                        'count': 0,
                        'topups': 0,
                        'topup_amount': 0,
                        'payments': 0,
                        'payment_amount': 0
                    }
                
                outlet_transactions[outlet_name]['count'] += 1
                
                if transaction.amount < 0:  # Topup
                    outlet_transactions[outlet_name]['topups'] += 1
                    outlet_transactions[outlet_name]['topup_amount'] += abs(transaction.amount)
                else:  # Payment
                    outlet_transactions[outlet_name]['payments'] += 1
                    outlet_transactions[outlet_name]['payment_amount'] += transaction.amount
        
        # Sort outlets by transaction count (descending)
        sorted_outlets = sorted(
            outlet_transactions.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Default date range for export (last 30 days)
        today = timezone.now().date()
        default_start_date = today - timedelta(days=30)
        
        # Prepare context
        context = {
            'title': 'Analytics',
            'selected_date': selected_date,
            'cards_issued': cards_issued,
            'total_topups': total_topups,
            'topup_amount': topup_amount,
            'total_payments': total_payments,
            'payment_amount': payment_amount,
            'outlet_transactions': sorted_outlets,
            'default_start_date': default_start_date,
            'default_end_date': today,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return super().changelist_view(request, context)

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Outlet, OutletAdmin)
admin.site.register(Volunteer, admin.ModelAdmin)
admin.site.register(NFCCard, NFCCardAdmin)
admin.site.register(NFCLog, NFCLogAdmin)
admin.site.register(Transaction, TransactionAdmin)

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
        verbose_name = 'Payment Collection Analytics'
        verbose_name_plural = 'Payment Collection Analytics'

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
        header = ['User', 'User Type', 'Cash Top-ups', 'Cash Amount (₹)', 'UPI Top-ups', 'UPI Amount (₹)', 'Total Top-ups', 'Total Amount (₹)']
        writer.writerow(header)
        
        # Calculate start and end datetime for the date range
        start_datetime = timezone.datetime.combine(start_date, timezone.datetime.min.time())
        end_datetime = timezone.datetime.combine(end_date, timezone.datetime.max.time())
        
        # Get all transactions in the date range
        transactions = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            amount__lt=0  # Only top-ups (negative amounts)
        )
        
        # Group transactions by user
        user_data = {}
        
        for transaction in transactions:
            if transaction.user:
                user_id = transaction.user.id
                username = transaction.user.username
                
                # Get user type
                user_type = "Unknown"
                try:
                    if transaction.user.is_staff:
                        user_type = "Admin"
                    elif hasattr(transaction.user, 'profile'):
                        user_type = transaction.user.profile.get_user_type_display().capitalize()
                except:
                    pass
                
                if user_id not in user_data:
                    user_data[user_id] = {
                        'username': username,
                        'user_type': user_type,
                        'cash_topups': 0,
                        'cash_amount': 0,
                        'upi_topups': 0,
                        'upi_amount': 0,
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
        transactions = Transaction.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            amount__lt=0  # Only top-ups (negative amounts)
        )
        
        # Group transactions by user
        user_data = {}
        
        for transaction in transactions:
            if transaction.user:
                user_id = transaction.user.id
                username = transaction.user.username
                
                # Get user type
                user_type = "Unknown"
                try:
                    if transaction.user.is_staff:
                        user_type = "Admin"
                    elif hasattr(transaction.user, 'profile'):
                        user_type = transaction.user.profile.get_user_type_display().capitalize()
                except:
                    pass
                
                if user_id not in user_data:
                    user_data[user_id] = {
                        'username': username,
                        'user_type': user_type,
                        'cash_topups': 0,
                        'cash_amount': 0,
                        'upi_topups': 0,
                        'upi_amount': 0,
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
        total_topups = total_cash_topups + total_upi_topups
        total_amount = total_cash_amount + total_upi_amount
        
        # Prepare context
        context = {
            'title': 'Payment Collection Analytics',
            'start_date': start_date,
            'end_date': end_date,
            'user_data': sorted_users,
            'total_cash_topups': total_cash_topups,
            'total_cash_amount': total_cash_amount,
            'total_upi_topups': total_upi_topups,
            'total_upi_amount': total_upi_amount,
            'total_topups': total_topups,
            'total_amount': total_amount,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return super().changelist_view(request, context)

# Register the analytics views
admin.site.register(Analytics, AnalyticsAdmin)
admin.site.register(PaymentCollectionAnalytics, PaymentCollectionAnalyticsAdmin)
