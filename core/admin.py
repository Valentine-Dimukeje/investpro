# core/admin.py
from django.contrib import admin
from .models import Profile, Transaction, Referral, Device


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'main_wallet', 'profit_wallet')
    search_fields = ('user__username', 'phone')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'status', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('user', 'referred_user', 'bonus_amount', 'created_at')
    search_fields = ('user__username', 'referred_user__username')
    ordering = ('-created_at',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "device_name", "ip_address", "last_active")


# @admin.register(ActivityLog)
# class ActivityLogAdmin(admin.ModelAdmin):
#     list_display = ("user", "action", "page", "ip_address", "created_at")
#     list_filter = ("action", "created_at")
#     search_fields = ("user__username", "page", "action")
#     ordering = ("-created_at",)

    