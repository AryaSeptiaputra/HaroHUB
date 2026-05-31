from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Address


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            'recipient_name', 'phone', 'full_address',
            'city', 'postal_code', 'notes',
            'place_id', 'latitude', 'longitude', 'is_default',
        )
        widgets = {
            'place_id': forms.HiddenInput,
            'latitude': forms.HiddenInput,
            'longitude': forms.HiddenInput,
        }
