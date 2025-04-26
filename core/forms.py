from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Outlet, NFCCard, TopupVolunteer

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

class VolunteerCreationForm(UserCreationForm):
    VOLUNTEER_TYPE_CHOICES = (
        ('topup_volunteer', 'Topup Volunteer'),
        ('outlet_volunteer', 'Outlet Volunteer'),
    )

    volunteer_type = forms.ChoiceField(choices=VOLUNTEER_TYPE_CHOICES, required=True, label="Volunteer Type")
    full_name = forms.CharField(max_length=100, required=True)
    contact_number = forms.CharField(max_length=15, required=False)
    adhaar_card_no = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'volunteer_type', 'full_name', 'contact_number', 'adhaar_card_no', 'password1', 'password2')

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
                    adhaar_card_no=self.cleaned_data.get('adhaar_card_no', '')
                )
            profile, created = Profile.objects.get_or_create(user=user)
            profile.user_type = volunteer_type
            profile.save()
        return user
