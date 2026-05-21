from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────────
# Existing Models (unchanged)
# ─────────────────────────────────────────────

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s cart"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.product.name


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.product.name


# ─────────────────────────────────────────────
# OTP Model
# ─────────────────────────────────────────────

class EmailOTP(models.Model):
    """
    Stores a 6-digit OTP tied to a user.

    Fields:
      - user         : FK to Django's User model (one active OTP per user)
      - otp          : 6-digit string code
      - purpose      : 'register' or 'login' — distinguishes the flow
      - created_at   : timestamp of creation (used for 5-min expiry check)
      - attempts     : how many times the user has tried to verify this OTP
                       (max 5 attempts before the OTP is invalidated)
      - is_verified  : True once the OTP has been successfully used
    """

    PURPOSE_REGISTER = 'register'
    PURPOSE_LOGIN    = 'login'
    PURPOSE_CHOICES  = [
        (PURPOSE_REGISTER, 'Registration'),
        (PURPOSE_LOGIN,    'Login'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp         = models.CharField(max_length=6)
    purpose     = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    created_at  = models.DateTimeField(auto_now_add=True)
    attempts    = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    class Meta:
        # Most recent OTP first
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP({self.user.username} | {self.purpose} | verified={self.is_verified})"

    def is_expired(self):
        """Returns True if the OTP was created more than 5 minutes ago."""
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def is_max_attempts(self):
        """Returns True if the user has exceeded 5 failed attempts."""
        return self.attempts >= 5
