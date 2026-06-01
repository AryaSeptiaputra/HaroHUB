"""Admin order dengan action bulk transition status via state machine."""
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Order, OrderItem, OrderStatus, Payment, ShippingRate


class OrderItemInline(admin.TabularInline):
    """Inline read-only untuk melihat item pesanan di halaman Order."""

    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price_at_purchase', 'quantity', 'subtotal_display')
    fields = ('product_name', 'price_at_purchase', 'quantity', 'subtotal_display')
    can_delete = False

    def subtotal_display(self, obj):
        """Format subtotal item dalam Rupiah.

        Args:
            obj (OrderItem): Instance OrderItem yang sedang ditampilkan.

        Returns:
            str: Subtotal diformat sebagai string Rupiah (contoh: ``Rp 200.000``).
        """
        return f'Rp {obj.subtotal:,.0f}'
    subtotal_display.short_description = 'Subtotal'


class PaymentInline(admin.StackedInline):
    """Inline read-only untuk melihat detail pembayaran di halaman Order."""

    model = Payment
    extra = 0
    readonly_fields = ('method', 'status', 'amount', 'transaction_ref', 'paid_at', 'created_at')
    can_delete = False


def _do_transition(modeladmin, request, queryset, new_status, label):
    """Eksekusi transisi status untuk semua order dalam queryset.

    Order yang transisinya valid akan berhasil; yang tidak valid akan
    di-skip dengan pesan warning. Memanggil ``Order.transition_to()`` agar
    state machine dan timestamp tetap terjaga.

    Args:
        modeladmin (ModelAdmin): Instance admin yang memanggil fungsi ini.
        request (HttpRequest): HTTP request dari admin action.
        queryset (QuerySet): QuerySet Order yang dipilih di list admin.
        new_status (str): Status tujuan (nilai dari ``OrderStatus``).
        label (str): Label human-readable untuk pesan sukses.
    """
    success = fail = 0
    for order in queryset:
        try:
            order.transition_to(new_status)
            success += 1
        except ValidationError:
            fail += 1
    if success:
        modeladmin.message_user(request, f'{success} pesanan berhasil diubah ke "{label}".')
    if fail:
        modeladmin.message_user(
            request,
            f'{fail} pesanan gagal — transisi tidak valid dari status saat ini.',
            level=messages.WARNING,
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin Order dengan bulk action transisi status dan semua field sebagai read-only.

    Status hanya bisa diubah melalui actions (via state machine), bukan langsung
    di form detail, untuk memastikan validasi transisi selalu dijalankan.
    """

    list_display  = ('order_number', 'user', 'status', 'shipping_city', 'total_display', 'created_at')
    list_filter   = ('status',)
    search_fields = ('order_number', 'user__email', 'shipping_city')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'order_number', 'user', 'status',
        'subtotal', 'shipping_cost', 'total',
        'shipped_at', 'completed_at', 'cancelled_at', 'cancellation_reason',
        'created_at', 'updated_at',
    )
    inlines = [OrderItemInline, PaymentInline]
    actions = ['action_processing', 'action_shipped', 'action_completed', 'action_cancelled']

    fieldsets = (
        ('Order', {'fields': ('order_number', 'user', 'status')}),
        ('Alamat Pengiriman', {
            'fields': (
                'shipping_recipient_name', 'shipping_phone',
                'shipping_full_address', 'shipping_city', 'shipping_postal_code', 'shipping_notes',
            ),
        }),
        ('Finansial', {'fields': ('subtotal', 'shipping_cost', 'total')}),
        ('Timestamps', {'fields': ('shipped_at', 'completed_at', 'cancelled_at', 'cancellation_reason', 'created_at', 'updated_at')}),
    )

    def total_display(self, obj):
        """Format total order dalam Rupiah untuk kolom list.

        Args:
            obj (Order): Instance Order yang sedang ditampilkan.

        Returns:
            str: Total diformat sebagai string Rupiah.
        """
        return f'Rp {obj.total:,.0f}'
    total_display.short_description = 'Total'

    @admin.action(description='Tandai: Diproses (PAID → PROCESSING)')
    def action_processing(self, request, queryset):
        """Transisi order yang dipilih dari PAID ke PROCESSING."""
        _do_transition(self, request, queryset, OrderStatus.PROCESSING, 'Diproses')

    @admin.action(description='Tandai: Dikirim (PROCESSING → SHIPPED)')
    def action_shipped(self, request, queryset):
        """Transisi order yang dipilih dari PROCESSING ke SHIPPED."""
        _do_transition(self, request, queryset, OrderStatus.SHIPPED, 'Dikirim')

    @admin.action(description='Tandai: Selesai (SHIPPED → COMPLETED)')
    def action_completed(self, request, queryset):
        """Transisi order yang dipilih dari SHIPPED ke COMPLETED."""
        _do_transition(self, request, queryset, OrderStatus.COMPLETED, 'Selesai')

    @admin.action(description='Batalkan pesanan')
    def action_cancelled(self, request, queryset):
        """Batalkan order yang dipilih (jika transisi ke CANCELLED diizinkan)."""
        _do_transition(self, request, queryset, OrderStatus.CANCELLED, 'Dibatalkan')


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    """Admin ShippingRate dengan list editable untuk update ongkir langsung di list view."""

    list_display  = ('city', 'cost', 'estimated_days', 'is_active')
    list_editable = ('cost', 'estimated_days', 'is_active')
    search_fields = ('city',)
