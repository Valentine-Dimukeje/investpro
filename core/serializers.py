# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Transaction, Device, Investment
from .utils import lookup_country_code, country_to_flag

class ProfileSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    flag = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "main_wallet",
            "profit_wallet",
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
    username = serializers.CharField(required=False, allow_blank=True)  # 👈 make optional

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "phone", "country"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        country = validated_data.pop("country", "")

        # Force username = email if missing
        email = validated_data["email"]
        if not validated_data.get("username"):
            validated_data["username"] = email

        password = validated_data.pop("password")

        user = User(
            username=validated_data["username"],
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        user.set_password(password)
        user.save()

        # Profile handling
        profile, _ = Profile.objects.get_or_create(user=user)
        if phone:
            profile.phone = phone
        if country:
            code = lookup_country_code(country)
            profile.country = code
            profile.flag = country_to_flag(code)
        profile.save()

        return user

# -------- Transactions --------
class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    amount = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    method = serializers.SerializerMethodField()  # 👈 extract from meta

    class Meta:
        model = Transaction
        fields = (
            "id",
            "user",
            "type",
            "amount",
            "status",
            "method",       # 👈 new field for readability
            "meta",
            "created_at",
            "updated_at",
        )

    def get_amount(self, obj):
        # Always return as string with 2 decimals
        return f"{obj.amount:.2f}"

    def get_type(self, obj):
        return obj.type.capitalize() if obj.type else "-"

    def get_status(self, obj):
        return obj.status.capitalize() if obj.status else "-"

    def get_method(self, obj):
        """
        Extract a human-readable method/plan/gateway from meta.
        """
        meta = obj.meta or {}
        return meta.get("gateway") or meta.get("plan") or meta.get("method") or "-"

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and not request.user.is_anonymous:
            validated_data["user"] = request.user
        return super().create(validated_data)


class InvestmentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    earnings = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

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
        return f"{obj.amount:.2f}"

    def get_earnings(self, obj):
        return f"{obj.calculate_earnings():.2f}"

