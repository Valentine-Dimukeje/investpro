from django.db import transaction as db_transaction
from decimal import Decimal
from core.models import Profile, Transaction

@db_transaction.atomic
def approve_deposit(txn: Transaction):
    if txn.type != "deposit":
        return

    if txn.status == "completed":
        return  # already approved

    meta = txn.meta or {}

    profile = Profile.objects.select_for_update().get(user=txn.user)

    # credit wallet
    profile.main_wallet += Decimal(txn.amount)
    profile.save(update_fields=["main_wallet"])

    # mark transaction completed + credited
    meta["credited"] = True
    txn.meta = meta
    txn.status = "completed"
    txn.save(update_fields=["status", "meta"])
