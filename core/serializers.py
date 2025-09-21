# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Transaction, Device, Investment
from .utils import lookup_country_code, country_to_flag
from decimal import Decimal, InvalidOperation
from .models import Referral

class UserProfileSerializer(serializers.ModelSerializer):
    main_wallet = serializers.DecimalField(source="profile.main_wallet", max_digits=12, decimal_places=2)
    profit_wallet = serializers.DecimalField(source="profile.profit_wallet", max_digits=12, decimal_places=2)
    wallet_balance = serializers.DecimalField(source="profile.wallet_balance", max_digits=12, decimal_places=2)
    phone = serializers.CharField(source="profile.phone", allow_null=True, required=False)
    country = serializers.SerializerMethodField()
    flag = serializers.CharField(source="profile.flag", allow_null=True)
    notifications = serializers.SerializerMethodField()
    devices = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username", "email", "first_name", "last_name",
            "main_wallet", "profit_wallet", "wallet_balance",
            "phone", "country", "flag", "notifications", "devices"
        ]

    def get_country(self, obj):
        return str(obj.profile.country) if obj.profile.country else None

    def get_notifications(self, obj):
        p = obj.profile
        return {
            "email": bool(p.email_notifications),
            "sms": bool(p.sms_notifications),
            "system": bool(p.system_notifications),
        }

    def get_devices(self, obj):
        # If you’re not tracking devices yet, return []
        return []


class ReferralSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    joined = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")
    status = serializers.SerializerMethodField()
    earnings = serializers.DecimalField(source="bonus_amount", max_digits=12, decimal_places=2)

    class Meta:
        model = Referral
        fields = ["name", "email", "joined", "status", "earnings"]

    def get_name(self, obj):
        return obj.referred_user.get_full_name() or obj.referred_user.username

    def get_email(self, obj):
        return obj.referred_user.email

    def get_status(self, obj):
        # Example: you can define real status logic (Active = has deposits, etc.)
        return "Active" if obj.bonus_amount > 0 else "Pending"


class ProfileSerializer(serializers.ModelSerializer):
    walletBalance = serializers.DecimalField(source="main_wallet", max_digits=12, decimal_places=2)
    profitBalance = serializers.DecimalField(source="profit_wallet", max_digits=12, decimal_places=2)
    country = serializers.SerializerMethodField()
    flag = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "walletBalance",
            "profitBalance",
            "email_notifications",
            "sms_notifications",
            "system_notifications",
            "phone",
            "country",
            "flag",
        ]

    def get_country(self, obj):
        return str(obj.country) if obj.country else None

    def get_flag(self, obj):
        from .utils import country_to_flag
        return country_to_flag(str(obj.country)) if obj.country else None

# -------- Device --------
class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "device_name", "ip_address", "last_active"]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    devices = DeviceSerializer(many=True, read_only=True)
    notifications = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile",
            "devices",
            "notifications",
        ]

    def get_notifications(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile:
            return {}
        return {
            "email": profile.email_notifications,
            "sms": profile.sms_notifications,
            "system": profile.system_notifications,
        }

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    phone = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "phone", "country"]

    def validate_email(self, value):
        # allow reactivation logic in view, so don't fail here in all cases.
        return value.lower()

    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        country = validated_data.pop("country", "")

        email = validated_data["email"].lower()

        user = User(
            username=email,
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        user.set_password(validated_data["password"])
        user.is_active = True
        user.save()

        # Ensure profile exists and wallets default to 0
        profile, created = Profile.objects.get_or_create(user=user)
        # make sure numeric fields are initialized to Decimal('0.00') by model defaults,
        # but explicitly set here for safety in some migration states:
        profile.main_wallet = profile.main_wallet or 0
        profile.profit_wallet = profile.profit_wallet or 0

        if phone:
            profile.phone = phone

        if country:
            try:
                code = lookup_country_code(country)
                profile.country = code
                profile.flag = country_to_flag(code)
            except Exception:
                profile.country = country  # fallback if lookup fails

        profile.save()
        return user



class TransactionSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ["id", "type", "amount", "status", "meta", "created_at"]

    def get_amount(self, obj):
        try:
            return format(Decimal(obj.amount), ".2f")
        except (ValueError, TypeError, InvalidOperation):
            return "0.00"


# -------- Investments --------
class InvestmentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    amount = serializers.SerializerMethodField()
    earnings = serializers.SerializerMethodField()

    class Meta:
        model = Investment
        fields = (
            "id",
            "user",
            "plan",
            "amount",
            "earnings",
            "status",
            "created_at",
            "updated_at",
        )

    def get_amount(self, obj):
        return str(obj.amount)

    def get_earnings(self, obj):
        # Assuming calculate_earnings() returns a Decimal
        return str(obj.calculate_earnings())

