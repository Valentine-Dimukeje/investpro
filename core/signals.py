from decimal import Decimal
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Transaction, Profile
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in


User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
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
@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    if created:
        profile = getattr(instance, "profile", None)
        if profile and profile.email_notifications:
            try:
                send_brevo_email(
                    "Welcome to Our Site",
                    f"<p>Hi {instance.first_name or instance.username}, welcome to our platform!</p>",
                    instance.email,
                    instance.username
                )
            except Exception as e:
                print("⚠️ Welcome email failed:", e)

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


# store previous status before save

@receiver(pre_save, sender=Transaction)
def store_previous_status(sender, instance, **kwargs):
    """
    Store previous status so we only credit once
    """
    if instance.pk:
        try:
            instance._previous_status = Transaction.objects.get(pk=instance.pk).status
        except Transaction.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Transaction)
def credit_wallet_on_deposit(sender, instance, created, **kwargs):
    """
    Credit main_wallet ONLY when:
    - type == deposit
    - status changes to completed
    """
    if instance.type != "deposit":
        return

    prev_status = getattr(instance, "_previous_status", None)

    # Only credit ONCE
    if instance.status == "completed" and prev_status != "completed":
        profile = Profile.objects.get(user=instance.user)
        profile.main_wallet += instance.amount
        profile.save()
