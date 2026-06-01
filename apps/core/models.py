"""Abstract base models yang digunakan lintas app — tidak punya migrations sendiri."""
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract model yang menambahkan field timestamp otomatis ke model turunan.

    Diwarisi oleh model yang membutuhkan tracking waktu pembuatan dan pembaruan
    tanpa harus mendefinisikan field secara berulang.

    Attributes:
        created_at (DateTimeField): Timestamp saat objek pertama kali dibuat; auto-set saat INSERT.
        updated_at (DateTimeField): Timestamp terakhir objek diperbarui; auto-update saat setiap SAVE.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
