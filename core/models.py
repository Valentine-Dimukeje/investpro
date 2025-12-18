from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField


User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = PhoneNumberField(blank=True, null=True)
    country = CountryField(blank=True, null=True)
    flag = models.CharField(max_length=10, blank=True, null=True)

    main_wallet = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )
    profit_wallet = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user}'s Profile"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('investment', 'Investment'),
        ('profit', 'Profit'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Referral(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referrals")
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referred_by")
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    last_active = models.DateTimeField(auto_now=True)


class Investment(models.Model):
    PLAN_CHOICES = [
        ("Amateur Plan", "Amateur Plan"),
        ("Exclusive Plan", "Exclusive Plan"),
        ("Diamond Plan", "Diamond Plan"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=100, choices=PLAN_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=50, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
