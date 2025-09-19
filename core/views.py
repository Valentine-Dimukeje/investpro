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



from django.http import JsonResponse
from django.core.mail import send_mail


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Sum
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response




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





# ----------------------------
# Helper: Get Client IP
# ----------------------------
def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


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

# User = get_user_model()
# logger = logging.getLogger(__name__)


# views.py
def send_html_email(subject, html_content, to_email):
    """
    Utility to send HTML + plain text email
    """
    text_content = strip_tags(html_content)  # fallback for non-HTML clients
    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)

        if not user.is_active:
            # 🔹 Reactivate the user
            user.is_active = True
            user.set_password(request.data.get("password"))
            user.save()

            # ✅ Styled Welcome Back Email
            html_content = f""" ... your HTML ... """
            text_content = strip_tags(html_content)
            try:
                send_html_email("🎉 Welcome Back to Heritage Investment!", html_content, email, text_content)
            except Exception:
                pass  # don't block registration if email fails

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Account reactivated successfully",
                    "user": UserSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "This email is already registered. Please log in."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except User.DoesNotExist:
        # ✅ Fresh registration
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # ✅ Styled Welcome Email
            html_content = f""" ... your HTML ... """
            text_content = strip_tags(html_content)
            try:
                send_html_email("🎉 Welcome to Heritage Investment!", html_content, email, text_content)
            except Exception:
                pass  # don't block registration if email fails

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Account created successfully",
                    "user": UserSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Registration failed",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )



@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email_or_username = request.data.get("username") or request.data.get("email")
    password = request.data.get("password")

    user = None

    # Try direct authentication (works if username==email)
    user = authenticate(request, username=email_or_username, password=password)

    # If failed, fallback: check by email
    if user is None:
        try:
            user_obj = User.objects.get(email=email_or_username)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )

    return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# ----------------------
# Current user
# ----------------------
@api_view(["GET"])
def me_view(request):
    user = request.user
    if user.is_authenticated:
        return Response(UserSerializer(user).data)
    return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


def send_test_email(request):
    try:
        send_mail(
            subject="Hello from Django + Brevo 🎉",
            message="If you got this email, Brevo API is working!",
            from_email=None,  # will use DEFAULT_FROM_EMAIL from settings.py
            recipient_list=[request.user.email],


            fail_silently=False,
        )
        return JsonResponse({"status": "success", "message": "Email sent!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


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
    user = request.user
    data = UserDetailSerializer(user).data
    prof = getattr(user, "profile", None)

    if prof:  # 👈 make sure profile exists
        data["wallet_balance"] = str(prof.wallet_balance)  # 👈 add balance here

        data["notifications"] = {
            "email": bool(getattr(prof, "email_notifications", True)),
            "sms": bool(getattr(prof, "sms_notifications", False)),
            "system": bool(getattr(prof, "system_notifications", True)),
        }

    return Response(data)



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


@api_view(["POST"])
@permission_classes([IsAdminUser])
def admin_transaction_action(request, pk):
    try:
        txn = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get("action")
    if action not in ("approve", "reject"):
        return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    if txn.status != "pending":
        return Response({"detail": "Transaction already processed"}, status=status.HTTP_400_BAD_REQUEST)

    profile = getattr(txn.user, "profile", None)
    if not profile:
        return Response({"detail": "User profile missing"}, status=status.HTTP_400_BAD_REQUEST)

    if action == "approve":
        # process according to type
        if txn.type == "deposit":
            profile.main_wallet = (profile.main_wallet or Decimal("0.00")) + txn.amount
        elif txn.type == "withdraw":
            # only allow if funds sufficient (should be checked before admin approves)
            profile.main_wallet = (profile.main_wallet or Decimal("0.00")) - txn.amount
            if profile.main_wallet < Decimal("0.00"):
                profile.main_wallet = Decimal("0.00")
        elif txn.type == "investment":
            # when investment is approved you typically DEBIT main wallet and mark investment active
            profile.main_wallet = (profile.main_wallet or Decimal("0.00")) - txn.amount
        elif txn.type == "profit":
            profile.profit_wallet = (profile.profit_wallet or Decimal("0.00")) + txn.amount

        profile.save()
        txn.status = "completed"
        txn.save()

        return Response(TransactionSerializer(txn).data)

    # reject
    txn.status = "rejected"
    txn.save()
    return Response(TransactionSerializer(txn).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deposit(request):
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


# ----------- APPROVE DEPOSIT (ADMIN ONLY) -----------
@api_view(["POST"])
@permission_classes([IsAdminUser])
def approve_deposit(request, txn_id):
    try:
        txn = Transaction.objects.get(id=txn_id, type="deposit")
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=404)

    if txn.status != "pending":
        return Response({"error": "Transaction already processed"}, status=400)

    profile = txn.user.profile

    # Credit deposit to main wallet
    profile.main_wallet += txn.amount
    profile.save()

    txn.status = "completed"
    txn.save()

    return Response({
        "message": "✅ Deposit approved and credited.",
        "transaction": TransactionSerializer(txn).data,
        "new_balance": str(profile.main_wallet),
    })


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

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

token_generator = PasswordResetTokenGenerator()


class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate uid + token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        subject = "Password Reset Request - Heritage Investment"
        message = f"Click the link below to reset your password:\n{reset_link}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            return Response({"error": f"Email sending failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Password reset link sent to your email."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")

        if not uidb64 or not token or not password:
            return Response({"error": "UID, token, and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid UID"}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
