"""Custom manager untuk User — login berbasis email, bukan username."""
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager kustom untuk model User yang menggunakan email sebagai identifier unik."""

    def create_user(self, email, password=None, **extra_fields):
        """Buat dan simpan user biasa dengan email dan password.

        Args:
            email (str): Alamat email unik user.
            password (str, optional): Password plain-text yang akan di-hash sebelum disimpan.
            **extra_fields: Field tambahan yang akan diteruskan ke model User.

        Returns:
            User: Instance user baru yang sudah disimpan ke database.

        Raises:
            ValueError: Jika ``email`` tidak disediakan atau kosong.
        """
        if not email:
            raise ValueError('Email wajib diisi.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Buat dan simpan superuser dengan is_staff dan is_superuser=True.

        Args:
            email (str): Alamat email unik superuser.
            password (str, optional): Password plain-text yang akan di-hash.
            **extra_fields: Field tambahan; ``is_staff`` dan ``is_superuser`` di-set True secara default.

        Returns:
            User: Instance superuser baru yang sudah disimpan ke database.

        Raises:
            ValueError: Jika ``is_staff`` atau ``is_superuser`` secara eksplisit di-set bukan True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser harus is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser harus is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
