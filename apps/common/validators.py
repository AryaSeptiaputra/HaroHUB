"""Validator form/model kustom untuk input spesifik Indonesia."""
import re
from django.core.exceptions import ValidationError


def validate_indonesian_phone(value):
    """Validasi bahwa nilai adalah nomor HP Indonesia yang valid.

    Mendukung format: ``+62``, ``62``, atau ``0`` sebagai prefix, diikuti
    ``8[1-9]`` dan 7–10 digit berikutnya. Spasi dan tanda hubung di-strip
    sebelum validasi.

    Args:
        value (str): Nomor HP yang akan divalidasi.

    Raises:
        ValidationError: Jika format nomor tidak sesuai pola nomor HP Indonesia.

    Example:
        >>> validate_indonesian_phone('08123456789')  # valid, tidak raise
        >>> validate_indonesian_phone('1234567')      # raise ValidationError
    """
    pattern = r'^(\+62|62|0)8[1-9][0-9]{7,10}$'
    if not re.match(pattern, value.replace(' ', '').replace('-', '')):
        raise ValidationError('Masukkan nomor HP Indonesia yang valid (contoh: 08123456789).')
