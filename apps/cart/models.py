"""Model Cart dan CartItem — harga dibaca live dari produk, tidak disimpan."""
from django.db import models

from apps.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    """Keranjang belanja yang terikat satu-satu dengan User.

    Harga tidak disimpan di Cart maupun CartItem — selalu dibaca live dari
    ``Product.price`` saat dibutuhkan. Hal ini memastikan harga selalu terkini,
    namun harga bisa berubah sebelum checkout.

    Attributes:
        user (OneToOneField): Pemilik keranjang; CASCADE saat user dihapus.
    """

    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='cart'
    )

    @property
    def total(self):
        """Total harga semua item dalam keranjang dihitung dari harga live produk.

        Returns:
            Decimal: Jumlah subtotal semua CartItem.
        """
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        """Jumlah baris item unik dalam keranjang (bukan total quantity).

        Returns:
            int: Jumlah CartItem yang terhubung ke keranjang ini.
        """
        return self.items.count()

    def __str__(self):
        """Return representasi string berupa email pemilik keranjang."""
        return f'Cart({self.user.email})'


class CartItem(models.Model):
    """Satu baris produk dalam keranjang dengan quantity tertentu.

    Constraint database memastikan satu produk hanya muncul satu kali per cart
    (duplikat di-handle dengan increment quantity, bukan baris baru).

    Attributes:
        cart (ForeignKey): Keranjang induk; CASCADE saat cart dihapus.
        product (ForeignKey): Produk yang ditambahkan.
        quantity (PositiveIntegerField): Jumlah item; minimal 1.
        added_at (DateTimeField): Timestamp saat item ditambahkan.
    """

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'catalog.Product', on_delete=models.CASCADE, related_name='+'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'], name='unique_product_per_cart'
            )
        ]

    @property
    def subtotal(self):
        """Harga total item ini (harga live × quantity).

        Returns:
            Decimal: Hasil perkalian ``product.price`` × ``quantity``.
        """
        return self.quantity * self.product.price

    def __str__(self):
        """Return nama produk dan quantity."""
        return f'{self.product.name} ×{self.quantity}'
