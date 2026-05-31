from django import template

register = template.Library()


@register.filter
def rupiah(value):
    try:
        return f'Rp {int(value):,}'.replace(',', '.')
    except (ValueError, TypeError):
        return value


@register.simple_tag(takes_context=True)
def url_with_page(context, page_num):
    request = context['request']
    params = request.GET.copy()
    params['page'] = page_num
    return f'?{params.urlencode()}'


@register.simple_tag(takes_context=True)
def url_remove_param(context, param, value=None):
    """Return current URL with a specific query param (or value) removed."""
    request = context['request']
    params = request.GET.copy()
    if value is not None:
        values = params.getlist(param)
        params.setlist(param, [v for v in values if v != str(value)])
    else:
        params.pop(param, None)
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'
