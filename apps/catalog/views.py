from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Grade, Product, ProductStatus, Series, Timeline


def listing_view(request):
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
    timeline_slug = request.GET.get('timeline', '').strip()
    series = []
    if timeline_slug:
        series = Series.objects.filter(timeline__slug=timeline_slug).order_by('name')
    return render(request, 'partials/_series_options.html', {'series': series})
