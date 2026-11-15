from .roles import obtener_rol_usuario, ROL_ADMIN, ROL_RECEPCION, ROL_SOCIO


def roles_context(request):
    """Context processor global que inyecta información de roles a todas las plantillas."""
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {
            "rol_usuario": None,
            "es_admin": False,
            "es_recepcion": False,
            "es_socio": False,
        }

    rol = obtener_rol_usuario(request.user)
    return {
        "rol_usuario": rol,
        "es_admin": rol == ROL_ADMIN,
        "es_recepcion": rol in (ROL_ADMIN, ROL_RECEPCION),
        "es_socio": rol == ROL_SOCIO,
    }
