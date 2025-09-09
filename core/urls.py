from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import send_test_email
from .views import dashboard_summary
from .views import update_notifications


urlpatterns = [
    # Auth
    path('api/auth/register/', views.register_view, name='auth-register'),
    path('api/auth/login/', views.MyTokenObtainPairView.as_view(), name='auth-login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),

    # Profile & account
    path('api/auth/me/', views.get_profile, name='auth-me'),
    path('auth/me/update/', views.update_profile, name='auth-me-update'),
    path('auth/change-password/', views.change_password_view, name='auth-change-password'),
    path('auth/delete/', views.delete_account, name='auth-delete'),

    # Notifications
    path('auth/notifications/', views.notifications_view, name='auth-notifications'),

    # Devices
    path('auth/devices/', views.get_devices, name='auth-devices'),
    path('auth/devices/logout/', views.logout_device, name='auth-devices-logout'),

    # Transactions
    path('transactions/', views.transactions_view, name='transactions'),
    path('transactions/<int:pk>/admin-action/', views.admin_transaction_action, name='admin-transaction-action'),

    path("deposit/", views.deposit, name="deposit"),
    path("deposit/approve/<int:txn_id>/", views.approve_deposit, name="approve_deposit"),
    path("withdraw/", views.withdraw_view, name="withdraw"),
    path("invest/", views.invest_view, name="invest"),
    path("investments/", views.investments_list, name="investments_list"),
    path("api/dashboard-summary/", views.dashboard_summary, name="dashboard_summary"),

    
    path("send-email/", send_test_email, name="send_email"),
    # path("dashboard-summary/", dashboard_summary, name="dashboard-summary"),
    path("api/auth/notifications/", update_notifications, name="update_notifications"),

]
