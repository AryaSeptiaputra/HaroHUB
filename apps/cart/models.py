from django.db import models

from apps.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='cart'
    )

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()

    def __str__(self):
        return f'Cart({self.user.email})'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'produk.Product', on_delete=models.CASCADE, related_name='+'
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
        return self.quantity * self.product.price

    def __str__(self):
        return f'{self.product.name} ×{self.quantity}'
