from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import uuid
import random
import string
from decimal import Decimal

# User type choices
USER_TYPE_CHOICES = (
    ('admin', 'Admin'),
    ('outlet', 'Outlet'),
    ('topup_volunteer', 'Topup Volunteers'),
    ('outlet_volunteer', 'Outlet Volunteers'),
)

# New model for Outlet Volunteer
class OutletVolunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15, blank=True)
    adhaar_card_no = models.CharField(max_length=20, blank=True)
    outlet = models.ForeignKey('Outlet', on_delete=models.CASCADE, related_name='volunteers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    mobile_no = models.CharField(max_length=15, blank=True)
    user_type = models.CharField(max_length=16, choices=USER_TYPE_CHOICES, default='outlet')

    def __str__(self):
        return self.user.username

# Signal to create/update user profile
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
    else:
        try:
            profile = instance.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=instance)
    if instance.is_staff:
        profile.user_type = 'admin'
        profile.save()

class Outlet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    outlet_name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.outlet_name

class NFCCard(models.Model):
    """Model for storing NFC card information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card_id = models.CharField(max_length=255, unique=True, help_text="Unique identifier of the NFC card")
    secure_key = models.CharField(max_length=16, unique=True, blank=True,
                                 help_text="Secure 16-character alphanumeric key for transactions")
    name = models.CharField(max_length=100, blank=True, help_text="Optional name for the card")
    customer_name = models.CharField(max_length=100, blank=True, help_text="Name of the customer")
    mobile_number = models.CharField(max_length=15, blank=True, help_text="Mobile number of the customer")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Current balance on the card")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.card_id})" if self.name else self.card_id
    
    def generate_secure_key(self):
        """Generate a random 16-character alphanumeric secure key"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(16))

# Signal to generate secure_key for NFCCard
@receiver(pre_save, sender=NFCCard)
def ensure_secure_key(sender, instance, **kwargs):
    """Ensure NFCCard has a secure_key before saving"""
    if not instance.secure_key:
        # Generate a unique secure key
        while True:
            secure_key = instance.generate_secure_key()
            if not NFCCard.objects.filter(secure_key=secure_key).exists():
                instance.secure_key = secure_key
                break

class NFCLog(models.Model):
    """Model for logging NFC card scans"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(NFCCard, on_delete=models.CASCADE, null=True, blank=True)
    card_identifier = models.CharField(max_length=255, help_text="Card ID at the time of scan")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, blank=True, help_text="Action performed with the card")
    success = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.card_identifier} at {self.timestamp}"

class Transaction(models.Model):
    """Model for storing payment transactions"""
    TRANSACTION_STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('nfc', 'NFC'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(NFCCard, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='transactions', help_text="NFC card used for the transaction")
    card_identifier = models.CharField(max_length=255, help_text="Card ID at the time of transaction")
    outlet = models.ForeignKey(Outlet, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='transactions', help_text="Outlet where the transaction occurred")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                            help_text="User who processed the transaction")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Transaction amount")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cash',
                                    help_text="Method used for payment (Cash or UPI)")
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                         help_text="Card balance before transaction")
    new_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                    help_text="Card balance after transaction")
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Transaction {self.id} - {self.amount} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # If this is a new transaction and the card exists
        if not self.pk and self.card:
            # Store the previous balance
            self.previous_balance = self.card.balance
            
            # Update the card balance
            self.card.balance = max(Decimal('0.00'), self.card.balance - self.amount)
            self.new_balance = self.card.balance
            self.card.save()
            
            # Set status to completed
            self.status = 'completed'
        
        super().save(*args, **kwargs)

# New model for Volunteer
class TopupVolunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15, blank=True)
    adhaar_card_no = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
