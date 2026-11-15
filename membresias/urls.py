from django.urls import path
from . import views

app_name = "membresias"

urlpatterns = [
    # Planes
    path("planes/", views.lista_planes_view, name="lista_planes"),
    path("planes/nuevo/", views.crear_plan_view, name="crear_plan"),
    path("planes/<int:plan_id>/editar/", views.editar_plan_view, name="editar_plan"),

    # Membresías
    path("listado/", views.lista_membresias_view, name="lista_membresias"),
    path("asignar/", views.asignar_membresia_view, name="asignar_membresia"),

    # Pagos
    path("pagos/", views.lista_pagos_view, name="lista_pagos"),
    path("pagos/registrar/", views.registrar_pago_view, name="registrar_pago"),
    path("pagos/<int:pago_id>/comprobante/", views.detalle_comprobante_pago_view, name="comprobante_pago"),
]
