# core/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import send_test_email
from .views import dashboard_summary
from .views import update_notifications
from .views import PasswordResetRequestView, PasswordResetConfirmView


urlpatterns = [
    path("auth/register/", views.register_view),
    path("auth/login/", views.login_view),
    path("auth/me/", views.me_view),
    path("cors-test/", views.cors_test, name="cors_test"),
    path("raw-debug/", views.raw_debug_view, name="raw_debug"),
    # path("auth/register/", views.register_view, name="auth-register"),
    # path("auth/login/", views.MyTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    # path("auth/me/", views.get_profile, name="auth-me"),
    path("auth/me/update/", views.update_profile, name="auth-me-update"),
    path("auth/change-password/", views.change_password_view, name="auth-change-password"),
    path("auth/delete/", views.delete_account, name="auth-delete"),
    path("auth/notifications/", views.notifications_view, name="auth-notifications"),
    path("auth/devices/", views.get_devices, name="auth-devices"),
    path("auth/devices/logout/", views.logout_device, name="auth-devices-logout"),
    path("transactions/", views.transactions_view, name="transactions"),
    path("transactions/<int:pk>/admin-action/", views.admin_transaction_action, name="admin-transaction-action"),
    path("deposit/", views.deposit, name="deposit"),
    path("deposit/approve/<int:txn_id>/", views.approve_deposit, name="approve_deposit"),
    path("withdraw/", views.withdraw_view, name="withdraw"),
    path("invest/", views.invest_view, name="invest"),
    path("investments/", views.investments_list, name="investments_list"),
    path("dashboard-summary/", views.dashboard_summary, name="dashboard_summary"),
    path("send-email/", views.send_test_email, name="send_email"),
    path("auth/notifications/update", views.update_notifications, name="update_notifications"),

    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("auth/password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
