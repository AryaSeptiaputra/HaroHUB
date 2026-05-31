import re
from django.core.exceptions import ValidationError


def validate_indonesian_phone(value):
    pattern = r'^(\+62|62|0)8[1-9][0-9]{7,10}$'
    if not re.match(pattern, value.replace(' ', '').replace('-', '')):
        raise ValidationError('Masukkan nomor HP Indonesia yang valid (contoh: 08123456789).')
