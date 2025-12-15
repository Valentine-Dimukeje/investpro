from decimal import Decimal
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Transaction, Profile


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
