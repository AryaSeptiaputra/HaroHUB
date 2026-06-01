"""Context processor global — menyuntikkan cart_count ke semua template."""


def cart_count(request):
    """Kembalikan jumlah item dalam keranjang user untuk ditampilkan di navbar.

    Selalu aman dipanggil — exception (misalnya Cart belum dibuat) di-handle
    dengan mengembalikan 0 agar tidak mengganggu render template.

    Args:
        request (HttpRequest): HTTP request objek dengan atribut ``request.user``.

    Returns:
        dict: Dict dengan satu key ``'cart_count'`` berisi integer jumlah item.
            Mengembalikan ``{'cart_count': 0}`` untuk user yang belum login.
    """
    if not request.user.is_authenticated:
        return {'cart_count': 0}
    try:
        return {'cart_count': request.user.cart.items.count()}
    except Exception:
        return {'cart_count': 0}
