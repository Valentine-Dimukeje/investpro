from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from decimal import Decimal
# from .models import Profile

# core/models.py

from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    phone = PhoneNumberField(blank=True, null=True)
    country = CountryField(blank=True, null=True)
    flag = models.CharField(max_length=10, blank=True, null=True)  # NEW FIELD

    # existing fields...
    main_wallet = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_wallet = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# models.py

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('investment', 'Investment'),
        ('profit', 'Profit'),
        # ('earning', 'Earning'),  # optional if you log weekly profits separately
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),        # <- add this for investments
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    meta = models.JSONField(null=True, blank=True)  # txid, gateway/plan, proof, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} | {self.type} | {self.amount}'


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# @receiver(post_save, sender=Transaction)
# def handle_deposit_approval(sender, instance, created, **kwargs):
#     """
#     When an admin approves a deposit (status -> completed), 
#     credit the user's wallet.
#     """
#     if not created and instance.type == "deposit" and instance.status == "completed":
#         wallet, _ = Wallet.objects.get_or_create(user=instance.user)
#         wallet.main_balance += instance.amount
#         wallet.save()


class Referral(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals')
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referred_by')
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"


class Investment(models.Model):
    PLAN_CHOICES = [
        ("Amateur Plan", "Amateur Plan"),
        ("Exclusive Plan", "Exclusive Plan"),
        ("Diamond Plan", "Diamond Plan"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=100, choices=PLAN_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=50, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    PLAN_RATES = {
        "Amateur Plan": Decimal("0.05"),   # 5% weekly
        "Exclusive Plan": Decimal("0.08"), # 8% weekly
        "Diamond Plan": Decimal("0.12"),   # 12% weekly
    }

    def calculate_earnings(self):
        """Calculate earnings based on weeks since start."""
        if self.status != "Active":
            return self.earnings

        now = timezone.now()
        weeks = (now - self.created_at) // timedelta(weeks=1)
        rate = self.PLAN_RATES.get(self.plan, Decimal("0.05"))
        return self.amount * rate * weeks


# class ActivityLog(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
#     action = models.CharField(max_length=255)  # e.g., "Visited Dashboard", "Clicked Invest Now"
#     page = models.CharField(max_length=255, null=True, blank=True)  # e.g., "/admin/plans"
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     user_agent = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.action} ({self.created_at})"
