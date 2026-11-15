from django.urls import path
from . import views

app_name = "accesos"

urlpatterns = [
    path("validar/", views.validar_acceso_view, name="validar"),
    path("historial/", views.historial_accesos_view, name="historial"),
    path("api/validar/", views.api_validar_acceso, name="api_validar"),
    path("api/qr-actual/", views.api_generar_qr_socio, name="api_qr_actual"),
]
