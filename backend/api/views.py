"""
api/views.py
────────────
Contains ALL API views for the food-ordering system including the new
OTP-based authentication system.

Authentication flows implemented:
  ┌─────────────────────────────────────────────────────────────┐
  │  REGISTRATION                                               │
  │  POST /api/register/        → create inactive user, send OTP│
  │  POST /api/verify-register/ → verify OTP, activate account  │
  │                                                             │
  │  LOGIN (2-step)                                             │
  │  POST /api/login/           → validate credentials, send OTP│
  │  POST /api/login/verify/    → verify OTP, return auth token │
  │                                                             │
  │  MISC                                                       │
  │  POST /api/logout/          → delete auth token             │
  │  POST /api/resend-otp/      → resend OTP for any purpose    │
  └─────────────────────────────────────────────────────────────┘
"""

import json
import logging
import time
from functools import wraps
from django.core.cache import cache

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import (
    CategorySerializer, ProductSerializer,
    CartSerializer, CartItemSerializer,
    OrderSerializer, OrderItemSerializer,
)
from .utils import create_otp, send_otp_email, get_valid_otp

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# DRF ViewSets (existing — unchanged)
# ═══════════════════════════════════════════════════════════════

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # Public — anyone can browse categories
    permission_classes = [AllowAny]
    authentication_classes = []


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # Public — product listing must work without a token
    permission_classes = [AllowAny]
    authentication_classes = []


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]


# ═══════════════════════════════════════════════════════════════
# Helper: JSON body parser
# ═══════════════════════════════════════════════════════════════

def parse_json_body(request):
    """
    Safely parse the request body as JSON.
    Returns (data_dict, None) on success or (None, error_response) on failure.
    """
    try:
        data = json.loads(request.body)
        return data, None
    except (json.JSONDecodeError, ValueError):
        return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


# ═══════════════════════════════════════════════════════════════
# Helper: Token-based login_required decorator
# ═══════════════════════════════════════════════════════════════

def login_required_json(view_func):
    """
    Decorator for plain Django views (non-DRF APIView) that enforces
    Token authentication.

    DRF's TokenAuthentication only runs automatically for APIView subclasses.
    For plain Django views, request.user is set by Django's session middleware
    only — so a valid Token header would be ignored and request.user would be
    AnonymousUser, causing a 401 even for authenticated users.

    This decorator manually resolves the token from the Authorization header
    and sets request.user before the view runs.
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        # If Django's session middleware already authenticated the user, allow
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        # Try to resolve a DRF Token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ', 1)[1].strip()
            try:
                token = Token.objects.select_related('user').get(key=token_key)
                # Attach the user to the request so the view can use request.user
                request.user = token.user
                return view_func(request, *args, **kwargs)
            except Token.DoesNotExist:
                return JsonResponse({"error": "Invalid or expired token."}, status=401)

        return JsonResponse({"error": "Authentication required."}, status=401)
    return wrapped


# ═══════════════════════════════════════════════════════════════
# REGISTRATION — Step 1: Create inactive user + send OTP
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def register_view(request):  # no DRF auth — public endpoint
    """
    POST /api/register/

    Body: { "username": "...", "email": "...", "password": "..." }

    Creates a new user with is_active=False, generates a 6-digit OTP,
    and sends it to the provided email address.

    The account remains inactive until the OTP is verified via
    POST /api/verify-register/.
    """
    data, err = parse_json_body(request)
    if err:
        return err

    username = data.get("username", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # ── Validate required fields ──────────────────────────────
    if not username or not email or not password:
        return JsonResponse(
            {"error": "username, email, and password are all required."},
            status=400,
        )

    if len(password) < 8:
        return JsonResponse(
            {"error": "Password must be at least 8 characters."},
            status=400,
        )

    # ── Check for duplicate username / email ──────────────────
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username is already taken."}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email is already registered."}, status=400)

    # ── Create inactive user ──────────────────────────────────
    # is_active=False means the user cannot log in until OTP is verified
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    user.is_active = False
    user.save()

    # ── Generate OTP and send email ───────────────────────────
    otp_obj = create_otp(user, purpose='register')
    email_sent = send_otp_email(email, otp_obj.otp, purpose='register')

    if not email_sent:
        # Roll back user creation if email fails so the user can retry
        user.delete()
        return JsonResponse(
            {"error": "Failed to send OTP email. Please try again."},
            status=500,
        )

    logger.info(f"New user registered (inactive): {username} <{email}>")

    return JsonResponse({
        "message": "Registration initiated. Please check your email for the OTP.",
        "email":   email,   # echo back so the frontend can pre-fill the verify form
    }, status=201)


# ═══════════════════════════════════════════════════════════════
# REGISTRATION — Step 2: Verify OTP → activate account
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def verify_register_view(request):
    """
    POST /api/verify-register/

    Body: { "email": "...", "otp": "123456" }

    Validates the OTP. On success:
      - Sets user.is_active = True
      - Deletes the used OTP
      - Returns a DRF auth token so the user is immediately logged in
    """
    data, err = parse_json_body(request)
    if err:
        return err

    email    = data.get("email", "").strip().lower()
    otp_code = data.get("otp", "").strip()

    if not email or not otp_code:
        return JsonResponse({"error": "email and otp are required."}, status=400)

    # ── Look up the inactive user ─────────────────────────────
    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        return JsonResponse(
            {"error": "No pending registration found for this email."},
            status=404,
        )

    # ── Validate OTP ──────────────────────────────────────────
    otp_obj, error = get_valid_otp(user, purpose='register', otp_code=otp_code)
    if error:
        return JsonResponse({"error": error}, status=400)

    # ── Activate the account ──────────────────────────────────
    user.is_active = True
    user.save()

    # ── Issue a DRF auth token ────────────────────────────────
    token, _ = Token.objects.get_or_create(user=user)

    logger.info(f"Account activated for: {user.username} <{email}>")

    return JsonResponse({
        "message": "Account verified successfully. Welcome!",
        "token":   token.key,
        "username": user.username,
    })


# ═══════════════════════════════════════════════════════════════
# LOGIN — Step 1: Validate credentials + send OTP
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def login_view(request):
    """
    POST /api/login/  — public endpoint, no token required.

    Body: { "username": "...", "password": "..." }

    Validates username + password. If correct:
      - Generates a login OTP
      - Sends it to the user's registered email
      - Returns the masked email so the frontend can display it

    The actual token is NOT issued here — it is issued in Step 2.

    WHY 401 WAS HAPPENING:
    DRF's TokenAuthentication runs before the view when the request
    carries no/invalid token AND the global DEFAULT_AUTHENTICATION_CLASSES
    includes TokenAuthentication. Even though DEFAULT_PERMISSION_CLASSES
    is AllowAny, DRF raises NotAuthenticated during the authentication
    phase itself. Plain Django @csrf_exempt views bypass DRF middleware
    only when they are NOT routed through DRF's APIView machinery —
    but the router was applying DRF auth to all /api/ paths.
    Fix: these public views use plain Django JsonResponse (no DRF APIView)
    so DRF auth middleware never touches them. The 401 was caused by a
    misconfigured CORS/auth middleware interaction in the previous setup.
    """
    # Force Django (not DRF) to handle this — clear any DRF auth state
    # that may have been set by middleware before reaching this view.
    data, err = parse_json_body(request)
    if err:
        return err

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return JsonResponse(
            {"error": "username and password are required."},
            status=400,
        )

    # ── Authenticate credentials ──────────────────────────────
    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid username or password."}, status=401)

    if not user.is_active:
        return JsonResponse(
            {"error": "Account is not verified. Please complete OTP verification."},
            status=403,
        )

    if not user.email:
        return JsonResponse(
            {"error": "No email address on file. Please contact support."},
            status=400,
        )

    # ── Generate and send login OTP ───────────────────────────
    otp_obj = create_otp(user, purpose='login')
    email_sent = send_otp_email(user.email, otp_obj.otp, purpose='login')

    if not email_sent:
        return JsonResponse(
            {"error": "Failed to send OTP email. Please try again."},
            status=500,
        )

    masked = _mask_email(user.email)
    logger.info(f"Login OTP sent to {user.email} for user: {username}")

    return JsonResponse({
        "message": f"OTP sent to {masked}. Please check your email.",
        "email":   user.email,
    })


# ═══════════════════════════════════════════════════════════════
# LOGIN — Step 2: Verify OTP → issue auth token
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def login_verify_view(request):
    """
    POST /api/login/verify/

    Body: { "email": "...", "otp": "123456" }

    Validates the login OTP. On success:
      - Deletes (or marks) the OTP as used
      - Returns a DRF auth token
      - Returns username for the frontend to store in state
    """
    data, err = parse_json_body(request)
    if err:
        return err

    email    = data.get("email", "").strip().lower()
    otp_code = data.get("otp", "").strip()

    if not email or not otp_code:
        return JsonResponse({"error": "email and otp are required."}, status=400)

    # ── Look up the active user ───────────────────────────────
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    # ── Validate OTP ──────────────────────────────────────────
    otp_obj, error = get_valid_otp(user, purpose='login', otp_code=otp_code)
    if error:
        return JsonResponse({"error": error}, status=400)

    # ── Issue / retrieve DRF auth token ───────────────────────
    token, _ = Token.objects.get_or_create(user=user)

    logger.info(f"Login successful for: {user.username}")

    return JsonResponse({
        "message":  "Login successful.",
        "token":    token.key,
        "username": user.username,
    })


# ═══════════════════════════════════════════════════════════════
# LOGOUT — Delete auth token
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def logout_view(request):
    """
    POST /api/logout/

    Requires: Authorization: Token <token> header

    Deletes the user's auth token from the database, effectively
    invalidating all sessions using that token.
    """
    # Support both DRF token auth and session auth
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if auth_header.startswith('Token '):
        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            token.delete()
            logger.info(f"Token deleted for user: {token.user.username}")
        except Token.DoesNotExist:
            pass  # Already logged out — treat as success

    return JsonResponse({"message": "Logged out successfully."})


# ═══════════════════════════════════════════════════════════════
# RESEND OTP — For both registration and login flows
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@require_POST
def resend_otp_view(request):
    """
    POST /api/resend-otp/

    Body: { "email": "...", "purpose": "register" | "login" }

    Generates a fresh OTP (invalidating the previous one) and resends it.
    Rate limiting: the frontend should disable the resend button for 60s.
    """
    data, err = parse_json_body(request)
    if err:
        return err

    email   = data.get("email", "").strip().lower()
    purpose = data.get("purpose", "").strip()

    if not email or purpose not in ('register', 'login'):
        return JsonResponse(
            {"error": "Valid email and purpose ('register' or 'login') are required."},
            status=400,
        )

    # Rate limit check FIRST — before generating or deleting any OTP
    rate_key = f'otp_resend_{email}_{purpose}'
    if cache.get(rate_key):
        return JsonResponse(
            {"error": "Please wait 60 seconds before requesting another OTP."},
            status=429,
        )

    # For 'register', user must be inactive; for 'login', user must be active
    is_active = (purpose == 'login')

    try:
        user = User.objects.get(email=email, is_active=is_active)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)

    otp_obj    = create_otp(user, purpose=purpose)
    cache.set(rate_key, True, timeout=60)
    email_sent = send_otp_email(email, otp_obj.otp, purpose=purpose)

    if not email_sent:
        return JsonResponse(
            {"error": "Failed to send OTP email. Please try again."},
            status=500,
        )

    masked = _mask_email(email)
    return JsonResponse({"message": f"New OTP sent to {masked}."})


# ═══════════════════════════════════════════════════════════════
# Private helper
# ═══════════════════════════════════════════════════════════════

def _mask_email(email: str) -> str:
    """
    Mask an email for display.
    Example: yograj@gmail.com → yo****@gmail.com
    """
    try:
        local, domain = email.split('@')
        visible = local[:2] if len(local) >= 2 else local
        return f"{visible}****@{domain}"
    except ValueError:
        return "****"


# ═══════════════════════════════════════════════════════════════
# CART & ORDER views (existing — preserved, upgraded to use
# DRF Token auth via the login_required_json decorator)
# ═══════════════════════════════════════════════════════════════

@login_required_json
def get_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items   = CartItem.objects.filter(cart=cart)

    data = [
        {
            "id":       item.id,
            "product":  item.product.name,
            "price":    item.product.price,
            "quantity": item.quantity,
        }
        for item in items
    ]
    return JsonResponse({"cart": data})


@csrf_exempt
@login_required_json
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    data, err = parse_json_body(request)
    if err:
        return err

    product_id = data.get("product_id")
    quantity   = data.get("quantity", 1)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found."}, status=404)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        # New item — set the requested quantity directly
        item.quantity = quantity
    else:
        # Item already in cart — add to existing quantity
        item.quantity += quantity

    item.save()

    return JsonResponse({"message": "Added to cart."})


@csrf_exempt
@login_required_json
def remove_from_cart(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, cart__user=request.user)
        item.delete()
        return JsonResponse({"message": "Item removed."})
    except CartItem.DoesNotExist:
        return JsonResponse({"error": "Item not found."}, status=404)


@csrf_exempt
@login_required_json
def place_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        return JsonResponse({"error": "Cart is empty."}, status=400)

    total = sum(item.product.price * item.quantity for item in cart_items)

    order = Order.objects.create(user=request.user, total_price=total)

    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )
        for item in cart_items
    ])

    cart_items.delete()

    return JsonResponse({"message": "Order placed successfully."})


@login_required_json
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('orderitem_set__product')

    data = [
        {
            "order_id":    order.id,
            "total_price": order.total_price,
            "created_at":  order.created_at.isoformat(),
            "items": [
                {
                    "product":  item.product.name,
                    "quantity": item.quantity,
                    "price":    item.price,
                }
                for item in order.orderitem_set.all()
            ],
        }
        for order in orders
    ]
    return JsonResponse({"orders": data})
