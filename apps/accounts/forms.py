"""Form registrasi, login, edit profil, dan manajemen alamat."""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Address, User


class RegistrationForm(UserCreationForm):
    """Form registrasi akun baru berbasis email.

    Menggunakan ``UserCreationForm`` standar Django dengan ``first_name`` dijadikan wajib
    dan semua field mendapat class CSS ``input-field`` untuk styling Tailwind.

    Attributes:
        Meta.model: Model ``User``.
        Meta.fields: email, first_name, last_name, password1, password2.
    """

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        """Inisialisasi form; tambahkan class CSS dan jadikan first_name wajib."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input-field'})
        self.fields['first_name'].required = True


class LoginForm(forms.Form):
    """Form login menggunakan email dan password.

    Attributes:
        email (EmailField): Alamat email untuk autentikasi.
        password (CharField): Password dengan widget PasswordInput.
    """

    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input-field', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))


class ProfileForm(forms.ModelForm):
    """Form edit profil user: nama, nomor HP, tanggal lahir.

    Attributes:
        Meta.model: Model ``User``.
        Meta.fields: first_name, last_name, phone_number, date_of_birth.
    """

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
    """Form tambah/edit alamat pengiriman, termasuk field tersembunyi dari Google Maps.

    Field ``place_id``, ``latitude``, dan ``longitude`` diisi otomatis oleh
    JavaScript Maps autocomplete dan disimpan sebagai HiddenInput.

    Attributes:
        Meta.model: Model ``Address``.
        Meta.fields: Semua field alamat termasuk koordinat GPS.
    """

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
