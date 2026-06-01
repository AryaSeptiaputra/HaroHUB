"""View listing produk dengan filter, detail produk, autocomplete search, dan lazy-load series."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Grade, Product, ProductStatus, Series, Timeline


def listing_view(request):
    """Halaman listing produk dengan filter multi-kriteria dan paginasi.

    Mendukung filter: grade (multi-value), timeline, series, rentang harga,
    status ketersediaan, dan keyword search (name + description).

    Args:
        request (HttpRequest): HTTP request dengan query params:
            - ``grade`` (list[str]): Slug grade, bisa lebih dari satu.
            - ``timeline`` (str): Slug timeline.
            - ``series`` (str): Slug series.
            - ``price_min`` (str): Harga minimum (integer).
            - ``price_max`` (str): Harga maksimum (integer).
            - ``status`` (str): ``ACTIVE`` atau ``PRE_ORDER``.
            - ``q`` (str): Keyword pencarian nama/deskripsi.
            - ``page`` (str): Nomor halaman paginasi.

    Returns:
        HttpResponse: Render ``catalog/listing.html`` dengan konteks:
            - ``page_obj``: Objek paginasi berisi produk.
            - ``grades``: Semua Grade untuk sidebar filter.
            - ``timelines``: Semua Timeline untuk sidebar filter.
            - ``series_for_timeline``: Series yang tersedia untuk timeline yang dipilih.
            - ``filters``: Dict nilai filter aktif saat ini.
            - ``has_filters``: Boolean; True jika ada filter aktif.
            - ``total_count``: Total produk yang cocok sebelum paginasi.
    """
    qs = Product.objects.for_listing().order_by('-created_at')

    grade_slugs = request.GET.getlist('grade')
    timeline_slug = request.GET.get('timeline', '').strip()
    series_slug = request.GET.get('series', '').strip()
    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()
    availability = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()

    if grade_slugs:
        qs = qs.filter(grade__slug__in=grade_slugs)
    if timeline_slug:
        qs = qs.filter(series__timeline__slug=timeline_slug)
    if series_slug:
        qs = qs.filter(series__slug=series_slug)
    if price_min:
        try:
            qs = qs.filter(price__gte=int(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            qs = qs.filter(price__lte=int(price_max))
        except ValueError:
            pass
    if availability == 'ACTIVE':
        qs = qs.filter(status=ProductStatus.ACTIVE)
    elif availability == 'PRE_ORDER':
        qs = qs.filter(status=ProductStatus.PRE_ORDER)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    series_for_timeline = []
    if timeline_slug:
        series_for_timeline = Series.objects.filter(timeline__slug=timeline_slug).order_by('name')

    filters = {
        'grade': grade_slugs,
        'timeline': timeline_slug,
        'series': series_slug,
        'price_min': price_min,
        'price_max': price_max,
        'status': availability,
        'q': q,
    }
    has_filters = any([grade_slugs, timeline_slug, series_slug, price_min, price_max, availability, q])

    return render(request, 'catalog/listing.html', {
        'page_obj': page_obj,
        'grades': Grade.objects.all(),
        'timelines': Timeline.objects.all(),
        'series_for_timeline': series_for_timeline,
        'filters': filters,
        'has_filters': has_filters,
        'total_count': paginator.count,
    })


def detail_view(request, slug):
    """Tampilkan halaman detail produk dan catat event VIEW jika user login.

    Produk DISCONTINUED tidak dapat diakses (404). Untuk user yang login,
    event VIEW dicatat ke BehaviorEvent dan status wishlist dikembalikan ke template.

    Args:
        request (HttpRequest): HTTP request objek.
        slug (str): Slug unik produk yang akan ditampilkan.

    Returns:
        HttpResponse: Render ``catalog/detail.html`` dengan konteks:
            - ``product``: Instance Product.
            - ``images``: List semua gambar produk.
            - ``primary_image``: Gambar utama produk.
            - ``is_wishlisted``: Boolean; True jika produk ada di wishlist user.

    Raises:
        Http404: Jika produk dengan slug tidak ditemukan atau statusnya DISCONTINUED.
    """
    product = get_object_or_404(
        Product.objects
               .filter(status__in=[ProductStatus.ACTIVE, ProductStatus.PRE_ORDER])
               .select_related('grade', 'series__timeline')
               .prefetch_related('images'),
        slug=slug,
    )

    is_wishlisted = False
    if request.user.is_authenticated:
        from apps.recommendations.models import Wishlist
        from apps.recommendations.services import record_event
        record_event(request.user, product, 'VIEW')
        is_wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()

    return render(request, 'catalog/detail.html', {
        'product': product,
        'images': list(product.images.all()),
        'primary_image': product.images.filter(is_primary=True).first(),
        'is_wishlisted': is_wishlisted,
    })


def search_autocomplete_view(request):
    """HTMX endpoint — kembalikan partial autocomplete hasil pencarian nama produk.

    Hanya memproses query dengan panjang minimal 2 karakter untuk menghindari
    hasil yang terlalu luas. Mengembalikan maksimal 5 produk.

    Args:
        request (HttpRequest): HTTP request dengan query param:
            - ``q`` (str): Keyword pencarian nama produk.

    Returns:
        HttpResponse: Render partial ``partials/_search_autocomplete.html`` dengan konteks:
            - ``products``: List produk yang cocok (maks 5), atau list kosong.
            - ``q``: Keyword pencarian yang digunakan.
    """
    q = request.GET.get('q', '').strip()
    products = []
    if len(q) >= 2:
        products = (Product.objects.active()
                    .filter(name__icontains=q)
                    .select_related('grade')
                    .prefetch_related('images')[:5])
    return render(request, 'partials/_search_autocomplete.html', {
        'products': products,
        'q': q,
    })


def series_for_timeline_view(request):
    """HTMX endpoint — kembalikan daftar series untuk timeline tertentu.

    Digunakan untuk lazy-load dropdown series di form filter listing
    setelah user memilih timeline.

    Args:
        request (HttpRequest): HTTP request dengan query param:
            - ``timeline`` (str): Slug timeline yang dipilih.

    Returns:
        HttpResponse: Render partial ``partials/_series_options.html`` dengan konteks:
            - ``series``: QuerySet Series yang termasuk dalam timeline, atau list kosong.
    """
    timeline_slug = request.GET.get('timeline', '').strip()
    series = []
    if timeline_slug:
        series = Series.objects.filter(timeline__slug=timeline_slug).order_by('name')
    return render(request, 'partials/_series_options.html', {'series': series})
