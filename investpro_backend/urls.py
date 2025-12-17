from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from core.views import create_admin_once, reset_admin_password

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),

    path("create-admin-once/", create_admin_once),
    path("reset-admin-password/", reset_admin_password),

    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt",
            content_type="text/plain",
        ),
    ),
]
