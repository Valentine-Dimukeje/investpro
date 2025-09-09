from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from django.core.mail import send_mail
import requests
from decimal import Decimal
from .models import Transaction, Profile  # adjust import if Profile is elsewhere


User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


# --- Helper to send SMS (Twilio example) ---
def send_sms(to, message):
    if not getattr(settings, "TWILIO_ACCOUNT_SID", None):
        return
    twilio_sid = settings.TWILIO_ACCOUNT_SID
    twilio_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_FROM_NUMBER
    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    requests.post(
        url,
        data={"From": from_number, "To": to, "Body": message},
        auth=(twilio_sid, twilio_token)
    )

# --- Send Welcome Notification ---
@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    if created:
        profile = getattr(instance, "profile", None)
        if profile and profile.email_notifications:
            send_mail(
                "Welcome to Our Site",
                f"Hi {instance.first_name or instance.username}, welcome to our platform!",
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
                fail_silently=True
            )
        if profile and profile.sms_notifications and profile.phone:
            send_sms(profile.phone, "Welcome to our platform!")

# --- Send Login Alert ---
@receiver(user_logged_in)
def send_login_alert(sender, request, user, **kwargs):
    profile = getattr(user, "profile", None)
    if profile and profile.email_notifications:
        send_mail(
            "Login Alert",
            f"Hi {user.first_name or user.username}, you just logged in from IP {get_client_ip(request)}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
    if profile and profile.sms_notifications and profile.phone:
        send_sms(profile.phone, "Login alert: You just logged in to your account.")

# --- Helper to get IP ---
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@receiver(post_save, sender=Transaction)
def handle_deposit_approval(sender, instance, created, **kwargs):
    """
    Credit user's main_wallet when a deposit is marked completed in Admin.
    """
    if instance.type == "deposit" and instance.status == "completed":
        try:
            profile = Profile.objects.get(user=instance.user)
        except Profile.DoesNotExist:
            return  # failsafe: no profile

        # Prevent double crediting
        if not getattr(instance, "_credited", False):
            profile.main_wallet = (profile.main_wallet or Decimal("0")) + instance.amount
            profile.save()

            # runtime flag (not persisted) to avoid infinite loop
            instance._credited = True



@receiver(post_save, sender=Transaction)
def handle_withdrawal(sender, instance, created, **kwargs):
    """
    Deduct from wallet only when withdrawal is marked completed.
    """
    if instance.type == "withdraw" and instance.status == "completed":
        profile = instance.user.profile
        if profile.main_wallet >= instance.amount:
            profile.main_wallet -= instance.amount
            profile.save()
