"""
api/urls.py
───────────
URL routing for the entire API.

Auth endpoints:
  POST /api/register/         → Step 1: create user + send OTP
  POST /api/verify-register/  → Step 2: verify OTP + activate account
  POST /api/login/            → Step 1: validate credentials + send OTP
  POST /api/login/verify/     → Step 2: verify OTP + return token
  POST /api/logout/           → delete auth token
  POST /api/resend-otp/       → resend OTP (register or login)

Existing endpoints (unchanged):
  /api/cart/
  /api/cart/add/
  /api/cart/remove/<id>/
  /api/order/place/
  /api/order/history/
  /api/products/
  /api/categories/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # DRF ViewSets
    CategoryViewSet,
    ProductViewSet,
    CartViewSet,
    CartItemViewSet,
    OrderViewSet,

    # OTP Auth views
    register_view,
    verify_register_view,
    login_view,
    login_verify_view,
    logout_view,
    resend_otp_view,

    # Cart & Order views
    get_cart,
    add_to_cart,
    remove_from_cart,
    place_order,
    order_history,
)

# ── DRF Router for ViewSets ───────────────────────────────────
router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('products',   ProductViewSet)
router.register('cart-items', CartItemViewSet)
router.register('orders',     OrderViewSet)

urlpatterns = [
    # ViewSet routes (products, categories, etc.)
    path('', include(router.urls)),

    # ── OTP Authentication ────────────────────────────────────
    # Registration flow
    path('register/',        register_view,        name='register'),
    path('verify-register/', verify_register_view, name='verify-register'),

    # Login flow (2-step)
    path('login/',           login_view,           name='login'),
    path('login/verify/',    login_verify_view,    name='login-verify'),

    # Logout
    path('logout/',          logout_view,          name='logout'),

    # Resend OTP (works for both register and login purposes)
    path('resend-otp/',      resend_otp_view,      name='resend-otp'),

    # ── Cart ──────────────────────────────────────────────────
    path('cart/',                      get_cart,          name='cart'),
    path('cart/add/',                  add_to_cart,       name='cart-add'),
    path('cart/remove/<int:item_id>/', remove_from_cart,  name='cart-remove'),

    # ── Orders ────────────────────────────────────────────────
    path('order/place/',   place_order,   name='order-place'),
    path('order/history/', order_history, name='order-history'),
]
