from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, LoginForm, ProfileForm, RegistrationForm
from .models import Address


def register_view(request):
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
    if request.method == 'POST':
        logout(request)
    return redirect('/')


@login_required
def profile_view(request):
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
    from apps.recommendations.models import Wishlist

    items = (Wishlist.objects
             .filter(user=request.user)
             .select_related('product__grade', 'product__series__timeline')
             .prefetch_related('product__images')
             .order_by('-created_at'))
    return render(request, 'accounts/wishlist.html', {'wishlist_items': items})


@login_required
def profile_edit_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profil berhasil diperbarui.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def address_create_view(request):
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
    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Tambah Alamat'})


@login_required
def address_update_view(request, pk):
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
    })


@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Alamat berhasil dihapus.')
        return redirect('accounts:profile')
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})


@login_required
def address_set_default_view(request, pk):
    if request.method == 'POST':
        address = get_object_or_404(Address, pk=pk, user=request.user)
        with transaction.atomic():
            request.user.addresses.update(is_default=False)
            address.is_default = True
            address.save(update_fields=['is_default'])
        messages.success(request, f'"{address.recipient_name}" dijadikan alamat utama.')
    return redirect('accounts:profile')
