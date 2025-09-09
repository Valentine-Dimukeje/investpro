from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail, mail_admins
from django.contrib.auth.models import User

from django.http import JsonResponse
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Sum
from decimal import Decimal



import user_agents

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    TransactionSerializer,
    DeviceSerializer,
    UserDetailSerializer
)
from .models import Transaction, Profile, Device



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

@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Send welcome email (Anymail will handle via Brevo API)
        try:
            send_mail(
                subject="🎉 Welcome to Heritage Investment",
                message=(
                    f"Dear {user.first_name or user.username},\n\n"
                    "We’re delighted to welcome you to Heritage Investment!\n\n"
                    "Your account has been successfully created, and you’re now part of a community "
                    "committed to building a secure and prosperous financial future.\n\n"
                    "Here’s what you can do next:\n"
                    "- Log in to your account and explore your dashboard.\n"
                    "- Start investing with our carefully curated opportunities.\n"
                    "- Reach out to our support team anytime you need assistance.\n\n"
                    "At Heritage Investment, we believe in transparency, trust, and growth. "
                    "We’re excited to have you on board and can’t wait to see you achieve your goals.\n\n"
                    "Warm regards,\n"
                    "The Heritage Investment Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,  # Prevents signup from breaking if email fails
            )

        except Exception as e:
            # you can log this if you want
            pass

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    # Return exact errors so frontend can show them
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    user.delete()
    if request.accepted_renderer.format == "html":
        return redirect("/")
    return Response({"message": "Account deleted successfully"})


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
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_transaction_action(request, pk):
    try:
        txn = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get("action")
    if action == "approve":
        txn.status = "completed"
        txn.save()
        profile = getattr(txn.user, "profile", None)
        if profile:
            if txn.type == "deposit":
                profile.main_wallet += Decimal(txn.amount)
            elif txn.type == "withdraw":
                profile.main_wallet -= Decimal(txn.amount)
                if profile.main_wallet < 0:
                    profile.main_wallet = Decimal("0.00")
            elif txn.type == "profit":
                profile.profit_wallet += Decimal(txn.amount)
            profile.save()
        return Response(TransactionSerializer(txn).data)

    if action == "reject":
        txn.status = "rejected"
        txn.save()
        return Response(TransactionSerializer(txn).data)

    return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


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

    txn = Transaction.objects.create(
        user=user,
        type="deposit",
        amount=amount,
        status="pending",
        meta={"method": method, "tx_id": tx_id}  # ✅ save in JSON
    )

    return Response({
        "message": "Deposit submitted! Waiting for admin approval.",
        "transaction": TransactionSerializer(txn).data,
        "new_balance": str(user.profile.main_wallet)  # balance unchanged until approved
    }, status=201)


# ✅ Admin approves deposit
@api_view(["POST"])
@permission_classes([IsAdminUser])  # only staff/admin can approve
def approve_deposit(request, txn_id):
    try:
        txn = Transaction.objects.get(id=txn_id, type="deposit")
    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found"}, status=404)

    if txn.status != "pending":
        return Response({"error": "Transaction already processed"}, status=400)

    profile = txn.user.profile
    profile.main_wallet += txn.amount
    profile.wallet_balance += txn.amount
    profile.save()

    txn.status = "completed"
    txn.save()

    return Response({
        "message": "Deposit approved and credited.",
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    user = request.user
    tx = Transaction.objects.filter(user=user)

    deposits = tx.filter(type="deposit", status="completed").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    withdrawals = tx.filter(type="withdraw", status="completed").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    investments = tx.filter(type="investment", status="active").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    earnings = tx.filter(type="profit").aggregate(total=Sum("amount"))["total"] or Decimal("0")

    recent = TransactionSerializer(tx.order_by("-created_at")[:10], many=True).data

    return Response({
        "wallet": str(user.profile.main_wallet),
        "profit_wallet": str(user.profile.profit_wallet),
        "total_deposits": str(deposits),
        "total_withdrawals": str(withdrawals),
        "total_investments": str(investments),
        "total_earnings": str(earnings),
        "recent": recent
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
def me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
