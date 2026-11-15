from django.urls import path
from . import views

app_name = "panel"

urlpatterns = [
    path("", views.inicio_panel, name="inicio"),
    path("carnet/", views.carnet_socio_view, name="carnet_propio"),
    path("socios/<int:socio_id>/carnet/", views.carnet_socio_view, name="carnet_socio"),
    path("accesos/validar/", views.validar_acceso_view, name="validar_acceso"),
]
