# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Transaction, Device, Investment
from .utils import lookup_country_code, country_to_flag
from decimal import Decimal, InvalidOperation


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
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        country = validated_data.pop("country", "")

        email = validated_data["email"]

        # Always force username = email
        user = User(
            username=email,
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        user.set_password(validated_data["password"])
        user.save()

        # Profile handling
        profile, _ = Profile.objects.get_or_create(user=user)
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

