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
    notifications = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "notifications"]

    def get_notifications(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile:
            return {}
        return {
            "email": profile.email_notifications,
            "sms": profile.sms_notifications,
            "system": profile.system_notifications,
        }


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
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [ "email", "password", "first_name", "last_name", "phone", "country"]
        extra_kwargs = {
            "username": {"read_only": True, "required": False},  # hidden from user
            "password": {"write_only": True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        country = validated_data.pop("country", "")

        # force username = email
        validated_data["username"] = validated_data["email"]

        user = User.objects.create_user(**validated_data)

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

    class Meta:
        model = Transaction
        fields = (
            "id",
            "user",
            "type",
            "amount",
            "status",
            "meta",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and not request.user.is_anonymous:
            validated_data["user"] = request.user
        return super().create(validated_data)


class InvestmentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    earnings = serializers.SerializerMethodField()

    class Meta:
        model = Investment
        fields = ("id", "user", "plan", "amount", "earnings", "status", "created_at", "updated_at")

    def get_earnings(self, obj):
        return str(obj.calculate_earnings())
