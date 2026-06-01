"""Model User berbasis email (menggantikan username) dan Address pengiriman."""
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """User model HaroHUB yang menggunakan email sebagai USERNAME_FIELD.

    ``username`` dihapus sepenuhnya; autentikasi menggunakan ``email`` + ``password``.

    Attributes:
        email (EmailField): Identifier unik untuk login; wajib diisi.
        phone_number (CharField): Nomor HP opsional, format bebas.
        date_of_birth (DateField): Tanggal lahir opsional.
        objects (UserManager): Manager kustom berbasis email.
    """

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        """Return email sebagai representasi string user."""
        return self.email


class Address(models.Model):
    """Alamat pengiriman milik user — satu user bisa punya banyak alamat.

    Satu alamat bisa ditandai sebagai ``is_default`` untuk dipilih otomatis saat checkout.
    Koordinat GPS diisi opsional via Google Maps Platform autocomplete di frontend.

    Attributes:
        user (ForeignKey): Pemilik alamat; CASCADE saat user dihapus.
        recipient_name (CharField): Nama penerima paket di alamat ini.
        phone (CharField): Nomor HP penerima.
        full_address (TextField): Alamat lengkap format bebas.
        city (CharField): Nama kota; digunakan untuk lookup ``ShippingRate``.
        postal_code (CharField): Kode pos, maks 10 karakter.
        place_id (CharField): Google Maps Place ID; diisi oleh JS Maps autocomplete.
        latitude (DecimalField): Lintang dari Maps autocomplete; opsional.
        longitude (DecimalField): Bujur dari Maps autocomplete; opsional.
        notes (CharField): Catatan tambahan (patokan, nomor unit, dsb.).
        is_default (BooleanField): Alamat utama yang dipilih otomatis di checkout.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')

    recipient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    full_address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)

    # Google Maps Platform
    place_id = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    notes = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'addresses'

    def __str__(self):
        """Return nama penerima dan kota sebagai representasi string."""
        return f'{self.recipient_name} — {self.city}'
