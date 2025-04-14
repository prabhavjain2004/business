from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Outlet, NFCCard

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    mobile_no = forms.CharField(max_length=15, required=False, help_text='Optional.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'mobile_no', 'password1', 'password2', )

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(max_length=254, required=False)
    mobile_no = forms.CharField(max_length=15, required=False)

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'email', 'mobile_no')

class OutletForm(forms.ModelForm):
    class Meta:
        model = Outlet
        fields = ['outlet_name', 'address', 'contact_person', 'phone_number', 'is_active']
        widgets = {
            'outlet_name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class NFCCardForm(forms.ModelForm):
    class Meta:
        model = NFCCard
        fields = ['card_id', 'name', 'customer_name', 'mobile_number', 'balance', 'is_active']
        widgets = {
            'card_id': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-input'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-input'}),
            'balance': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class TopUpForm(forms.Form):
    card_id = forms.CharField(
        max_length=255, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'})
    )
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'})
    )
    payment_method = forms.ChoiceField(
        choices=[('cash', 'Cash'), ('upi', 'UPI')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3})
    )

class PaymentForm(forms.Form):
    card_id = forms.CharField(
        max_length=255, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'})
    )
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3})
    )
