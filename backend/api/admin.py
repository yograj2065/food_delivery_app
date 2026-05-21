"""
api/admin.py
────────────
Registers all models in the Django admin panel.
EmailOTP is registered with extra display columns and filters
so admins can monitor OTP activity and manually clean up stale records.
"""

from django.contrib import admin
from django.utils import timezone

from .models import (
    Category, Product,
    Cart, CartItem,
    Order, OrderItem,
    EmailOTP,
)


# ─────────────────────────────────────────────
# Existing model registrations
# ─────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'category', 'price', 'available')
    list_filter   = ('category', 'available')
    search_fields = ('name',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'total_price', 'created_at')
    list_filter   = ('created_at',)
    search_fields = ('user__username',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')


# ─────────────────────────────────────────────
# EmailOTP admin
# ─────────────────────────────────────────────

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    Admin view for OTP records.

    Useful for:
      - Monitoring active OTPs
      - Manually deleting stale/expired OTPs
      - Debugging email delivery issues
    """
    list_display  = ('id', 'user', 'purpose', 'is_expired_display',
                     'attempts', 'is_verified', 'created_at')
    list_filter   = ('purpose', 'is_verified')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('otp', 'created_at', 'attempts')

    # Do NOT allow creating OTPs from admin — they must be generated via API
    def has_add_permission(self, request):
        return False

    @admin.display(boolean=True, description='Expired?')
    def is_expired_display(self, obj):
        """Shows a red/green icon in the admin list for expiry status."""
        return obj.is_expired()

    def get_queryset(self, request):
        """Show most recent OTPs first."""
        return super().get_queryset(request).select_related('user')
