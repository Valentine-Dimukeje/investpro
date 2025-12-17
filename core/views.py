from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail, mail_admins
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
reset_tokens ={}

from rest_framework import status

token_generator = PasswordResetTokenGenerator()


import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from django.http import JsonResponse


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Sum
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Referral
from .serializers import ReferralSerializer


from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.views.decorators.http import require_GET



from .serializers import UserProfileSerializer  # ✅ ADD TH

from core.utils_email import send_brevo_email
from django.template.loader import render_to_string




import user_agents
import logging

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    TransactionSerializer,
    DeviceSerializer,
    UserDetailSerializer
)
from .models import Transaction, Profile, Device
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags
from .email import send_brevo_email


# ----------------------------
# Helper: Get Client IP
# ----------------------------
def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@api_view(["GET"])
def create_admin_once(request):
    if User.objects.filter(username="admin").exists():
        return Response({"status": "admin already exists"})

    User.objects.create_superuser(
        username="admin",
        email="admin@octa-investment.com",
        password="Admin12345!"
    )

    return Response({"status": "admin created"})

from django.http import HttpResponse

def robots_txt(request):
    content = """User-agent: *
Disallow:
"""
    return HttpResponse(content, content_type="text/plain")


@require_GET
def reset_admin_password(request):
    User = get_user_model()

    username = "admin"
    new_password = "Admin@12345"  # change later

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": "admin@octa-investment.com",
            "is_staff": True,
            "is_superuser": True,
        }
    )

    user.set_password(new_password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()

    return JsonResponse({
        "status": "success",
        "created": created,
        "username": username,
        "password": new_password
    })
# ----------------------------
# Track Device on Login
# ----------------------------
def track_device(request, user):
    ua_string = request.META.get("HTTP_USER_AGENT", "")
    ua = user_agents.parse(ua_string)
    device_name = f"{ua.browser.family} on {ua.os.family}"
    ip = get_client_ip(request) or "0.0.0.0"

    Device.objects.update_or_create(
        user=user,
        device_name=device_name,
        ip_address=ip,
        defaults={"last_active": timezone.now()}
    )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already registered"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        is_active=True
    )

    # Ensure profile exists
    from .models import Profile
    Profile.objects.get_or_create(user=user)

    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "Account created successfully",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    print("==== LOGIN DEBUG START ====")
    print("RAW BODY:", request.body)
    print("PARSED request.data:", request.data)
    print("HEADERS:", request.headers)
    print("==== LOGIN DEBUG END ====")

    email_or_username = request.data.get("username") or request.data.get("email")
    password = request.data.get("password")

    if not email_or_username or not password:
        return Response({"detail": "Email/username and password required."}, status=400)

    # Accept login using either email OR username
    try:
        user = User.objects.get(email=email_or_username)
        username = user.username
    except User.DoesNotExist:
        username = email_or_username

    user = authenticate(username=username, password=password)

    if not user:
        return Response({"detail": "Invalid credentials"}, status=401)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context["request"]
        track_device(request, self.user)
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# ----------------------------
# Profile Views
# ----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


# core/views.py
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_referrals(request):
    referrals = Referral.objects.filter(user=request.user)
    serializer = ReferralSerializer(referrals, many=True)
    return Response({"referrals": serializer.data})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    user.first_name = request.data.get("first_name", user.first_name)
    user.last_name = request.data.get("last_name", user.last_name)
    user.email = request.data.get("email", user.email)
    user.username = user.email  # Keep username = email

    # phone/country are raw strings; country should be alpha-2 in DB
    # If you want to accept full names here too, you can reuse lookup_country_code
    profile.phone = request.data.get("phone", profile.phone)
    if "country" in request.data:
        from .utils import lookup_country_code, country_to_flag
        code = lookup_country_code(request.data.get("country"))
        profile.country = code
        profile.flag = country_to_flag(code)

    user.save()
    profile.save()
    return Response({"message": "Profile updated successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not user.check_password(old_password):
        return Response({"detail": "Old password is incorrect"}, status=400)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Password changed successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notifications_view(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    for key in ["email", "sms", "system"]:
        if key in request.data:
            setattr(prof, f"{key}_notifications", bool(request.data[key]))
    prof.save()
    return Response({"message": "Notifications updated"})


# ----------------------------
# Devices Views
# ----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_devices(request):
    qs = Device.objects.filter(user=request.user).order_by("-last_active")
    return Response({"devices": DeviceSerializer(qs, many=True).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_device(request):
    device_id = request.data.get("device_id")
    if not device_id:
        return Response({"detail": "device_id is required"}, status=400)
    Device.objects.filter(user=request.user, id=device_id).delete()
    return Response({"message": "Device logged out"})


# ----------------------------
# Delete Account (redirect to / for browsers)
# ----------------------------
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user

    # 🔹 Soft delete: mark inactive instead of deleting row
    user.is_active = False

    # (Optional) anonymize username if your User model requires unique usernames
    if hasattr(user, "username"):
        user.username = f"deleted_{user.pk}"

    user.save()

    return Response({"message": "Account deleted successfully"}, status=status.HTTP_200_OK)



# ----------------------------
# Transactions Views
# ----------------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def transactions_view(request):
    if request.method == "GET":
        qs = Transaction.objects.filter(user=request.user).order_by("-created_at")
        return Response(TransactionSerializer(qs, many=True).data)

    serializer = TransactionSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    txn = serializer.save()

    if txn.type == "withdraw":
        mail_admins(
            subject=f"New withdrawal request #{txn.id}",
            message=f"User {request.user.username} requested withdraw ${txn.amount}. Check admin panel."
        )

    return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)

from django.db import transaction as db_transaction

@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_transaction_action(request, pk):
    txn = Transaction.objects.get(pk=pk)

    action = request.data.get("action")

    if action == "approve":
        txn.status = "completed"
        txn.save(update_fields=["status"])

    elif action == "reject":
        txn.status = "rejected"
        txn.save(update_fields=["status"])

    return Response(TransactionSerializer(txn).data)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deposit(request):

    print("AUTH HEADER:", request.headers.get("Authorization"))
    user = request.user
    data = request.data

    amount = data.get("amount")
    method = data.get("method")
    tx_id = data.get("tx_id")

    if not amount or not method or not tx_id:
        return Response({"error": "Missing required fields"}, status=400)

    try:
        amount = Decimal(str(amount))  # ✅ force to Decimal
    except Exception:
        return Response({"error": "Invalid amount format"}, status=400)

    txn = Transaction.objects.create(
        user=user,
        type="deposit",
        amount=amount,
        status="pending",
        meta={"method": method, "tx_id": tx_id},
    )

    return Response({
        "message": "Deposit submitted! Waiting for admin approval.",
        "transaction": TransactionSerializer(txn).data,
        "new_balance": str(user.profile.main_wallet),  # balance unchanged until approved
    }, status=201)
    

# --- CREATE INVESTMENT (deduct from wallet, save plan & rate) ---
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invest_view(request):
    amount = request.data.get("amount")
    plan = request.data.get("plan")  # e.g. "Amateur Plan", "Exclusive Plan", "Diamond Plan"

    if not amount or not plan:
        return Response({"error": "Amount and plan are required"}, status=400)

    try:
        amount = Decimal(str(amount))
    except:
        return Response({"error": "Invalid amount"}, status=400)

    profile = request.user.profile
    if profile.main_wallet < amount:
        return Response({"error": "Insufficient funds"}, status=400)

    # Deduct
    profile.main_wallet -= amount
    profile.save()

    # plan → weekly rate
    plan_rates = {
        "Amateur Plan": Decimal("0.05"),    # 5%
        "Exclusive Plan": Decimal("0.08"),  # 8%
        "Diamond Plan": Decimal("0.12"),    # 12%
    }
    rate = plan_rates.get(plan, Decimal("0.05"))

    txn = Transaction.objects.create(
        user=request.user,
        type="investment",
        amount=amount,
        status="active",
        meta={
            "plan": plan,
            "rate": str(rate),
            "earnings": "0.00",  # optional live tracker
            "next_payout": (timezone.now() + timezone.timedelta(days=7)).isoformat()
        },
    )

    return Response({
        "message": "Investment successful",
        "transaction": TransactionSerializer(txn).data,
        "new_balance": str(profile.main_wallet)
    }, status=201)


# --- LIST USER INVESTMENTS (shape it for the Investments page) ---
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def investments_list(request):
    qs = Transaction.objects.filter(user=request.user, type="investment").order_by("-created_at")
    out = []
    for t in qs:
        meta = t.meta or {}
        out.append({
            "plan": meta.get("plan", ""),
            "amount": str(t.amount),
            "earnings": str(meta.get("earnings", "0")),
            "status": "Active" if t.status in ["active", "pending"] else t.status.capitalize(),
            "created_at": t.created_at.isoformat(),
        })
    return Response(out)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def withdraw_view(request):
    amount = request.data.get("amount")
    if not amount:
        return Response({"error": "Amount is required"}, status=400)

    try:
        amount = Decimal(amount)
    except:
        return Response({"error": "Invalid amount"}, status=400)

    profile = request.user.profile
    if profile.main_wallet < amount:
        return Response({"error": "Insufficient balance"}, status=400)

    # Create withdrawal request (status = pending)
    txn = Transaction.objects.create(
        user=request.user,
        type="withdraw",
        amount=amount,
        status="pending"
    )

    # Notify admin by email
    mail_admins(
        subject=f"New Withdrawal Request from {request.user.username}",
        message=(
            f"User {request.user.username} has requested a withdrawal of ${amount}.\n\n"
            f"Login to the Django Admin to approve or reject this request."
        )
    )

    return Response({
        "message": "Withdrawal request submitted. Awaiting admin approval.",
        "transaction": txn.id
    }, status=status.HTTP_201_CREATED)



def _fmt(v):
    if v is None:
        return "0.00"
    if isinstance(v, Decimal):
        return format(v, ".2f")
    try:
        return format(Decimal(v), ".2f")
    except Exception:
        return str(v)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):

    print("AUTH HEADER:", request.headers.get("Authorization"))
    user = request.user
    tx = Transaction.objects.filter(user=user)

    deposits = tx.filter(type="deposit", status__in=["completed", "approved"]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    withdrawals = tx.filter(type="withdraw", status__in=["completed", "approved"]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    investments = tx.filter(type="investment", status__in=["active", "completed"]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    earnings = tx.filter(type="profit", status__in=["completed", "approved"]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    recent = TransactionSerializer(tx.order_by("-created_at")[:10], many=True).data

    # ensure profile values are included and formatted
    main_wallet = getattr(user.profile, "main_wallet", Decimal("0.00"))
    profit_wallet = getattr(user.profile, "profit_wallet", Decimal("0.00"))

    return Response({
        "wallet": _fmt(main_wallet),
        "profit_wallet": _fmt(profit_wallet),
        "total_deposits": _fmt(deposits),
        "total_withdrawals": _fmt(withdrawals),
        "total_investments": _fmt(investments),
        "total_earnings": _fmt(earnings),
        "recent": recent,
    })



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_notifications(request):
    profile = request.user.profile
    data = request.data

    if "email" in data:
        profile.email_notifications = data["email"]
    if "sms" in data:
        profile.sms_notifications = data["sms"]
    if "system" in data:
        profile.system_notifications = data["system"]

    profile.save()
    return Response({"success": True, "notifications": {
        "email": profile.email_notifications,
        "sms": profile.sms_notifications,
        "system": profile.system_notifications,
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return the logged-in user's profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@csrf_exempt  # 👈 disable CSRF for this test endpoint
@api_view(["GET", "OPTIONS"])
@permission_classes([AllowAny])
def cors_test(request):
    return Response({"ok": True})


@csrf_exempt
def raw_debug_view(request):
    """
    Simple endpoint to debug CORS/CSRF issues.
    Returns request meta and checks CORS headers.
    """
    return JsonResponse({
        "method": request.method,
        "origin": request.META.get("HTTP_ORIGIN"),
        "host": request.get_host(),
        "headers": dict(request.headers),
    })

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        subject = "Password Reset Request"
        html_content = f"""
            <h2>Hello {user.username},</h2>
            <p>Click below to reset your password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>If you didn’t request this, ignore this email.</p>
        """

        try:
            send_brevo_email(subject, html_content, email, user.username)
            return Response({"message": "✅ Password reset email sent!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")

        if not uidb64 or not token or not password:
            return Response({"error": "UID, token and password required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid UID."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        return Response({"message": "✅ Password reset successful!"}, status=status.HTTP_200_OK)
