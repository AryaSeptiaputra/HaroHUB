"""Exception kustom untuk domain logic HaroHUB."""


class CheckoutError(Exception):
    """Exception untuk kondisi error yang terdeteksi saat proses checkout.

    Diangkat oleh ``order.services.checkout()`` saat validasi bisnis gagal
    (cart kosong, stok tidak cukup, kota tidak tersedia, dsb.). View menangkap
    exception ini dan menampilkan pesan ke user via ``messages.error()``.

    Attributes:
        args[0] (str): Pesan error yang aman ditampilkan langsung ke user.
    """

    pass
