from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Address, User


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input-field'})
        self.fields['first_name'].required = True


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input-field', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'date_of_birth')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'phone_number': forms.TextInput(attrs={'class': 'input-field', 'placeholder': '08xxxxxxxxxx'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            'recipient_name', 'phone', 'full_address',
            'city', 'postal_code', 'notes',
            'is_default',
            'place_id', 'latitude', 'longitude',
        )
        widgets = {
            'recipient_name': forms.TextInput(attrs={'class': 'input-field'}),
            'phone': forms.TextInput(attrs={'class': 'input-field', 'placeholder': '08xxxxxxxxxx'}),
            'full_address': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'input-field'}),
            'postal_code': forms.TextInput(attrs={'class': 'input-field', 'maxlength': '10'}),
            'notes': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Patokan, nomor rumah, dsb.'}),
            'place_id': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
