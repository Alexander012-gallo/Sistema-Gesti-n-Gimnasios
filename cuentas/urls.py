from django.urls import path
from . import views

app_name = "cuentas"

urlpatterns = [
    path("socios/", views.lista_socios_view, name="lista_socios"),
    path("socios/nuevo/", views.crear_socio_view, name="crear_socio"),
    path("socios/<int:socio_id>/", views.detalle_socio_view, name="detalle_socio"),
    path("socios/<int:socio_id>/editar/", views.editar_socio_view, name="editar_socio"),
    path("perfil/", views.perfil_socio_view, name="perfil"),
]
