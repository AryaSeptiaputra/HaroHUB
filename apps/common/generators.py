"""Fungsi generator utilitas untuk mock data (transaction reference, dsb.)."""
import random
import string


def generate_mock_transaction_ref():
    """Generate referensi transaksi mock berformat ``MOCK-XXXXXX`` (6 karakter acak).

    Digunakan oleh ``order.services.confirm_payment()`` saat tidak ada
    referensi nyata dari payment gateway (simulasi pembayaran).

    Returns:
        str: String referensi berformat ``'MOCK-XXXXXX'`` di mana ``X`` adalah
            kombinasi huruf kapital dan angka secara acak.

    Example:
        >>> generate_mock_transaction_ref()
        'MOCK-A3B9KZ'
    """
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f'MOCK-{suffix}'
