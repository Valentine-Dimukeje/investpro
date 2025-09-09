# core/tasks.py
from django.utils import timezone
from decimal import Decimal
from .models import Transaction

def process_investment_growth():
    now = timezone.now()
    active_investments = Transaction.objects.filter(type="investment", status="active")

    for inv in active_investments:
        meta = inv.meta or {}
        next_payout = meta.get("next_payout")
        rate = Decimal(meta.get("rate", "0.05"))

        if next_payout and now >= timezone.datetime.fromisoformat(next_payout):
            profit = inv.amount * rate

            # credit profit to wallet
            profile = inv.user.profile
            profile.main_wallet += profit
            profile.save()

            # log earning transaction
            Transaction.objects.create(
                user=inv.user,
                type="earning",
                amount=profit,
                status="completed",
                meta={"source_investment": inv.id, "plan": meta.get("plan")}
            )

            # update next payout date
            meta["next_payout"] = (now + timezone.timedelta(days=7)).isoformat()
            inv.meta = meta
            inv.save()
