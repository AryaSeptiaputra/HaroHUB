"""Template tags dan filter kustom HaroHUB: format rupiah, URL pagination, filter param."""
from django import template

register = template.Library()


@register.filter
def rupiah(value):
    """Format angka menjadi string Rupiah dengan pemisah titik ribuan.

    Args:
        value (int | float | Decimal): Nilai angka yang akan diformat.

    Returns:
        str: String berformat ``'Rp X.XXX.XXX'`` dengan titik sebagai pemisah ribuan.
            Mengembalikan ``value`` asli jika tidak bisa dikonversi ke integer.

    Example:
        >>> rupiah(150000)
        'Rp 150.000'
        >>> rupiah('invalid')
        'invalid'
    """
    try:
        return f'Rp {int(value):,}'.replace(',', '.')
    except (ValueError, TypeError):
        return value


@register.simple_tag(takes_context=True)
def url_with_page(context, page_num):
    """Return URL query string saat ini dengan nomor halaman yang diperbarui.

    Mempertahankan semua query param yang ada (filter aktif) dan hanya
    mengubah nilai param ``page``.

    Args:
        context (dict): Template context; digunakan untuk mengakses ``request``.
        page_num (int): Nomor halaman yang akan di-set.

    Returns:
        str: Query string berformat ``'?param1=val&...&page=N'``.
    """
    request = context['request']
    params = request.GET.copy()
    params['page'] = page_num
    return f'?{params.urlencode()}'


@register.simple_tag(takes_context=True)
def url_remove_param(context, param, value=None):
    """Return URL query string saat ini dengan param tertentu dihapus.

    Jika ``value`` disediakan, hanya menghapus satu nilai spesifik dari param
    multi-value (contoh: hapus satu grade dari list grade yang dipilih).
    Jika ``value`` tidak disediakan, hapus seluruh param.

    Args:
        context (dict): Template context; digunakan untuk mengakses ``request``.
        param (str): Nama query param yang akan dihapus atau dikurangi.
        value (str, optional): Nilai spesifik yang akan dihapus dari param multi-value.
            Jika None, seluruh param dihapus.

    Returns:
        str: Query string yang sudah dimodifikasi. Mengembalikan ``'?'`` jika
            tidak ada param tersisa setelah penghapusan.
    """
    request = context['request']
    params = request.GET.copy()
    if value is not None:
        values = params.getlist(param)
        params.setlist(param, [v for v in values if v != str(value)])
    else:
        params.pop(param, None)
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'
