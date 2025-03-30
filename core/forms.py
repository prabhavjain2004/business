from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Outlet, NFCCard, NFCLog

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'mobile_no']

class OutletCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Outlet
        fields = ['outlet_name', 'address', 'contact_person', 'phone_number', 'is_active']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        username = cleaned_data.get('username')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        
        return cleaned_data

class OutletUpdateForm(forms.ModelForm):
    class Meta:
        model = Outlet
        fields = ['outlet_name', 'address', 'contact_person', 'phone_number', 'is_active']

class NFCCardForm(forms.ModelForm):
    class Meta:
        model = NFCCard
        fields = ['card_id', 'secure_key', 'name', 'is_active']
        widgets = {
            'card_id': forms.TextInput(attrs={'readonly': 'readonly'}),
            'secure_key': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

class NFCLogForm(forms.ModelForm):
    class Meta:
        model = NFCLog
        fields = ['card_identifier', 'action', 'notes']
        widgets = {
            'card_identifier': forms.TextInput(attrs={'readonly': 'readonly'}),
        }
