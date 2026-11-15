"""
Definición de roles, permisos y decoradores para el control de acceso basado en roles (RBAC).
Roles del sistema:
- Administrador: gestiona usuarios, socios, planes, membresías, pagos, estadísticas y configuración.
- Recepción: registra socios, consulta membresías, registra pagos y valida accesos por QR.
- Socio: consulta su perfil, membresía, historial de pagos y carnet QR dinámico.
"""

from functools import wraps
from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

ROL_ADMIN = "Administrador"
ROL_RECEPCION = "Recepción"
ROL_SOCIO = "Socio"

ROLES_CHOICES = (
    (ROL_ADMIN, "Administrador"),
    (ROL_RECEPCION, "Recepción"),
    (ROL_SOCIO, "Socio"),
)


def obtener_rol_usuario(user) -> str:
    """Devuelve el rol principal de un usuario según sus permisos y grupos."""
    if not user.is_authenticated:
        return "Anonimo"

    if user.is_superuser:
        return ROL_ADMIN

    nombres_grupos = set(user.groups.values_list("name", flat=True))

    if ROL_ADMIN in nombres_grupos:
        return ROL_ADMIN
    if ROL_RECEPCION in nombres_grupos:
        return ROL_RECEPCION
    if ROL_SOCIO in nombres_grupos or hasattr(user, "socio"):
        return ROL_SOCIO

    if user.is_staff:
        return ROL_ADMIN

    return "Sin Rol"


def es_administrador(user) -> bool:
    return obtener_rol_usuario(user) == ROL_ADMIN


def es_recepcion(user) -> bool:
    return obtener_rol_usuario(user) in (ROL_ADMIN, ROL_RECEPCION)


def es_socio(user) -> bool:
    return obtener_rol_usuario(user) == ROL_SOCIO or hasattr(user, "socio")


def rol_requerido(*roles_permitidos):
    """
    Decorador para proteger vistas exigiendo que el usuario pertenezca
    a uno de los roles indicados.
    """
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            rol_actual = obtener_rol_usuario(request.user)

            # Superusuarios siempre tienen acceso administrativo
            if request.user.is_superuser and ROL_ADMIN in roles_permitidos:
                return view_func(request, *args, **kwargs)

            if rol_actual in roles_permitidos:
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                f"No tienes permisos suficientes para acceder a esta sección. (Rol requerido: {', '.join(roles_permitidos)})"
            )
            return redirect("panel:inicio")

        return wrapper
    return decorador


# Atajos semánticos para decoradores comunes
admin_requerido = rol_requerido(ROL_ADMIN)
recepcion_requerido = rol_requerido(ROL_ADMIN, ROL_RECEPCION)
socio_requerido = rol_requerido(ROL_SOCIO)


def garantizar_roles_y_permisos():
    """
    Crea los grupos base del sistema en la base de datos si no existen
    y asocia permisos estándar de Django.
    """
    grupo_admin, _ = Group.objects.get_or_create(name=ROL_ADMIN)
    grupo_recepcion, _ = Group.objects.get_or_create(name=ROL_RECEPCION)
    grupo_socio, _ = Group.objects.get_or_create(name=ROL_SOCIO)

    # Permisos para Recepción (Socio, Membresia, Pago, RegistroAcceso)
    try:
        from cuentas.models import Socio
        from membresias.models import Membresia, Plan, Pago
        from accesos.models import RegistroAcceso

        ct_socio = ContentType.objects.get_for_model(Socio)
        ct_membresia = ContentType.objects.get_for_model(Membresia)
        ct_plan = ContentType.objects.get_for_model(Plan)
        ct_pago = ContentType.objects.get_for_model(Pago)
        ct_acceso = ContentType.objects.get_for_model(RegistroAcceso)

        perms_recepcion = Permission.objects.filter(
            content_type__in=[ct_socio, ct_membresia, ct_plan, ct_pago, ct_acceso],
            codename__in=[
                "add_socio", "change_socio", "view_socio",
                "add_membresia", "change_membresia", "view_membresia",
                "view_plan",
                "add_pago", "view_pago",
                "add_registroacceso", "view_registroacceso",
            ]
        )
        grupo_recepcion.permissions.set(perms_recepcion)
    except Exception:
        pass

    return {
        "admin": grupo_admin,
        "recepcion": grupo_recepcion,
        "socio": grupo_socio,
    }
