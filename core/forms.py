from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Outlet, NFCCard, TopupVolunteer, Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'mobile_no', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'required': True
            }),
            'mobile_no': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'required': True
            })
        }
        labels = {
            'name': 'Full Name',
            'mobile_no': 'Mobile Number',
            'email': 'Email Address'
        }

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
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(max_length=254, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Outlet
        fields = ['username', 'email', 'password', 'confirm_password', 'outlet_name', 'address', 'contact_person', 'phone_number', 'is_active']
        widgets = {
            'outlet_name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

class NFCCardForm(forms.ModelForm):
    class Meta:
        model = NFCCard
        fields = ['card_id', 'customer', 'balance', 'is_active']
        widgets = {
            'card_id': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
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

class VolunteerCreationForm(UserCreationForm):
    VOLUNTEER_TYPE_CHOICES = (
        ('topup_volunteer', 'Topup Volunteer'),
        ('outlet_volunteer', 'Outlet Volunteer'),
    )

    volunteer_type = forms.ChoiceField(choices=VOLUNTEER_TYPE_CHOICES, required=True, label="Volunteer Type")
    full_name = forms.CharField(max_length=100, required=True)
    contact_number = forms.CharField(max_length=15, required=False)
    adhaar_card_no = forms.CharField(max_length=20, required=False)
    outlet = forms.ModelChoiceField(queryset=None, required=False, label="Outlet")

    class Meta:
        model = User
        fields = ('username', 'volunteer_type', 'full_name', 'contact_number', 'adhaar_card_no', 'outlet', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Outlet
        self.fields['outlet'].queryset = Outlet.objects.filter(is_active=True)
        self.fields['outlet'].widget.attrs.update({'class': 'form-input'})

    def clean(self):
        cleaned_data = super().clean()
        volunteer_type = cleaned_data.get('volunteer_type')
        outlet = cleaned_data.get('outlet')
        if volunteer_type == 'outlet_volunteer' and not outlet:
            self.add_error('outlet', 'This field is required for Outlet Volunteers.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            from .models import Profile, TopupVolunteer, OutletVolunteer
            volunteer_type = self.cleaned_data['volunteer_type']
            if volunteer_type == 'topup_volunteer':
                volunteer = TopupVolunteer.objects.create(
                    user=user,
                    full_name=self.cleaned_data['full_name'],
                    contact_number=self.cleaned_data.get('contact_number', ''),
                    adhaar_card_no=self.cleaned_data.get('adhaar_card_no', '')
                )
            elif volunteer_type == 'outlet_volunteer':
                volunteer = OutletVolunteer.objects.create(
                    user=user,
                    full_name=self.cleaned_data['full_name'],
                    contact_number=self.cleaned_data.get('contact_number', ''),
                    adhaar_card_no=self.cleaned_data.get('adhaar_card_no', ''),
                    outlet=self.cleaned_data.get('outlet')
                )
            profile, created = Profile.objects.get_or_create(user=user)
            profile.user_type = volunteer_type
            profile.save()
        return user
