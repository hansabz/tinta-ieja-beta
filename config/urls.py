from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.users.urls")),
    path("accounts/", include("allauth.urls")),  # solo el flujo OAuth de Google, ver templates/users/login.html
    path("contacto/", include("apps.contacts.urls")),
    path("chat/", include("apps.chatbot.urls")),
    path("citas/", include("apps.appointments.urls")),
    path("", include("apps.studio.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
