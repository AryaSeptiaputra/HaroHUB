"""View autentikasi (register/login/logout), profil, wishlist, dan manajemen alamat."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, LoginForm, ProfileForm, RegistrationForm
from .models import Address


def register_view(request):
    """Tampilkan dan proses form registrasi akun baru.

    User yang sudah login akan di-redirect ke root. Setelah registrasi berhasil,
    user langsung di-login dan diarahkan ke halaman profil.

    Args:
        request (HttpRequest): HTTP request objek.

    Returns:
        HttpResponse: Redirect ke profil jika sukses, atau halaman register dengan form.
    """
    if request.user.is_authenticated:
        return redirect('/')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Akun berhasil dibuat. Selamat datang!')
        return redirect('accounts:profile')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Tampilkan dan proses form login berbasis email.

    Mendukung query param ``?next=`` untuk redirect setelah login. User yang sudah
    terautentikasi di-redirect langsung ke root.

    Args:
        request (HttpRequest): HTTP request objek.

    Returns:
        HttpResponse: Redirect ke ``next`` atau root jika sukses, atau halaman login dengan form.
    """
    if request.user.is_authenticated:
        return redirect('/')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        messages.error(request, 'Email atau password salah.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Proses logout; hanya POST yang menghapus sesi, GET hanya redirect.

    Args:
        request (HttpRequest): HTTP request objek.

    Returns:
        HttpResponse: Redirect ke root.
    """
    if request.method == 'POST':
        logout(request)
    return redirect('/')


@login_required
def profile_view(request):
    """Tampilkan halaman profil dengan alamat, pesanan terakhir, dan preview wishlist.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.

    Returns:
        HttpResponse: Render template ``accounts/profile.html`` dengan konteks:
            - ``addresses``: QuerySet alamat user diurutkan default-first.
            - ``recent_orders``: 5 pesanan terakhir dengan prefetch items.
            - ``wishlist_preview``: 4 item wishlist terbaru.
            - ``wishlist_count``: Total jumlah item wishlist.
    """
    from apps.recommendations.models import Wishlist

    addresses     = request.user.addresses.all().order_by('-is_default', 'recipient_name')
    recent_orders = (request.user.orders
                     .prefetch_related('items')
                     .order_by('-created_at')[:5])
    wishlist_preview = (Wishlist.objects
                        .filter(user=request.user)
                        .select_related('product__grade')
                        .prefetch_related('product__images')
                        .order_by('-created_at')[:4])
    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    return render(request, 'accounts/profile.html', {
        'addresses':       addresses,
        'recent_orders':   recent_orders,
        'wishlist_preview': wishlist_preview,
        'wishlist_count':  wishlist_count,
    })


@login_required
def wishlist_view(request):
    """Tampilkan semua produk dalam wishlist user.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.

    Returns:
        HttpResponse: Render template ``accounts/wishlist.html`` dengan konteks:
            - ``wishlist_items``: QuerySet Wishlist diurutkan terbaru, lengkap dengan relasi produk.
    """
    from apps.recommendations.models import Wishlist

    items = (Wishlist.objects
             .filter(user=request.user)
             .select_related('product__grade', 'product__series__timeline')
             .prefetch_related('product__images')
             .order_by('-created_at'))
    return render(request, 'accounts/wishlist.html', {'wishlist_items': items})


@login_required
def profile_edit_view(request):
    """Tampilkan dan proses form edit profil (nama, HP, tanggal lahir).

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.

    Returns:
        HttpResponse: Redirect ke profil jika berhasil, atau halaman edit dengan form.
    """
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profil berhasil diperbarui.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def address_create_view(request):
    """Tampilkan dan proses form tambah alamat baru.

    Jika ``is_default=True``, semua alamat lain user di-unset secara atomik dalam satu transaksi.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.

    Returns:
        HttpResponse: Redirect ke profil jika berhasil, atau form dengan Google Maps API key.
    """
    form = AddressForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        with transaction.atomic():
            if address.is_default:
                request.user.addresses.update(is_default=False)
            address.save()
        messages.success(request, 'Alamat berhasil ditambahkan.')
        return redirect('accounts:profile')
    return render(request, 'accounts/address_form.html', {
        'form': form,
        'action': 'Tambah Alamat',
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY_FRONTEND,
    })


@login_required
def address_update_view(request, pk):
    """Tampilkan dan proses form edit alamat yang sudah ada.

    Hanya alamat milik request.user yang bisa diubah (404 jika bukan miliknya).
    Jika ``is_default=True``, alamat lain di-unset secara atomik.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        pk (int): Primary key alamat yang akan diubah.

    Returns:
        HttpResponse: Redirect ke profil jika berhasil, atau form edit dengan data yang ada.

    Raises:
        Http404: Jika alamat dengan ``pk`` tidak ditemukan atau bukan milik request.user.
    """
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            if form.cleaned_data.get('is_default'):
                request.user.addresses.exclude(pk=pk).update(is_default=False)
            form.save()
        messages.success(request, 'Alamat berhasil diperbarui.')
        return redirect('accounts:profile')
    return render(request, 'accounts/address_form.html', {
        'form': form,
        'action': 'Edit Alamat',
        'address': address,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY_FRONTEND,
    })


@login_required
def address_delete_view(request, pk):
    """Tampilkan konfirmasi dan proses hapus alamat.

    Hanya alamat milik request.user yang bisa dihapus.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        pk (int): Primary key alamat yang akan dihapus.

    Returns:
        HttpResponse: Redirect ke profil jika POST berhasil, atau halaman konfirmasi jika GET.

    Raises:
        Http404: Jika alamat dengan ``pk`` tidak ditemukan atau bukan milik request.user.
    """
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Alamat berhasil dihapus.')
        return redirect('accounts:profile')
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})


@login_required
def address_set_default_view(request, pk):
    """Set satu alamat sebagai default dan hapus flag default dari alamat lain.

    Operasi dilakukan dalam satu transaksi atomik untuk menghindari race condition.
    Hanya menerima POST; GET di-ignore dan tetap redirect ke profil.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        pk (int): Primary key alamat yang akan dijadikan default.

    Returns:
        HttpResponse: Redirect ke halaman profil.

    Raises:
        Http404: Jika alamat dengan ``pk`` tidak ditemukan atau bukan milik request.user.
    """
    if request.method == 'POST':
        address = get_object_or_404(Address, pk=pk, user=request.user)
        with transaction.atomic():
            request.user.addresses.update(is_default=False)
            address.is_default = True
            address.save(update_fields=['is_default'])
        messages.success(request, f'"{address.recipient_name}" dijadikan alamat utama.')
    return redirect('accounts:profile')
