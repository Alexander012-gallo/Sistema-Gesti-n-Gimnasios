from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from cuentas.models import Socio
from cuentas.roles import (
    obtener_rol_usuario,
    ROL_ADMIN,
    ROL_RECEPCION,
    ROL_SOCIO,
    recepcion_requerido,
)
from membresias.models import Membresia, Plan, Pago
from membresias.services import (
    actualizar_estados_vigencias,
    obtener_membresia_actual_socio,
)
from accesos.models import RegistroAcceso
from accesos.services import (
    crear_qr_socio,
    obtener_datos_qr_socio,
    validar_y_registrar_acceso,
)


@login_required
def inicio_panel(request):
    """
    Panel central adaptativo según el rol del usuario autenticado:
    - Administrador: Métricas globales, ingresos, planes, membresías y auditoría.
    - Recepción: Operaciones del día, acceso rápido al escáner QR, socios y pagos.
    - Socio: Portal personal con membresía actual, historial y carnet QR dinámico.
    """
    actualizar_estados_vigencias()
    rol = obtener_rol_usuario(request.user)
    hoy = timezone.localdate()

    context = {
        "rol": rol,
        "ROL_ADMIN": ROL_ADMIN,
        "ROL_RECEPCION": ROL_RECEPCION,
        "ROL_SOCIO": ROL_SOCIO,
        "hoy": hoy,
    }

    if rol == ROL_ADMIN:
        total_socios = Socio.objects.count()
        membresias_activas = Membresia.objects.filter(
            estado=Membresia.Estado.ACTIVA,
            fecha_fin__gte=hoy,
        ).count()
        accesos_hoy = RegistroAcceso.objects.filter(fecha_hora__date=hoy).count()
        accesos_permitidos_hoy = RegistroAcceso.objects.filter(
            fecha_hora__date=hoy,
            resultado=RegistroAcceso.Resultado.PERMITIDO,
        ).count()

        # Ingresos del mes actual
        ingresos_mes = Pago.objects.filter(
            fecha_pago__year=hoy.year,
            fecha_pago__month=hoy.month,
        ).aggregate(Sum("monto"))["monto__sum"] or Decimal("0.00")

        ultimos_accesos = RegistroAcceso.objects.select_related("socio__usuario").order_by("-fecha_hora")[:8]
        ultimos_pagos = Pago.objects.select_related("membresia__socio__usuario", "membresia__plan").order_by("-fecha_pago")[:6]
        planes_activos = Plan.objects.filter(activo=True).count()

        context.update({
            "total_socios": total_socios,
            "membresias_activas": membresias_activas,
            "accesos_hoy": accesos_hoy,
            "accesos_permitidos_hoy": accesos_permitidos_hoy,
            "ingresos_mes": ingresos_mes,
            "ultimos_accesos": ultimos_accesos,
            "ultimos_pagos": ultimos_pagos,
            "planes_activos": planes_activos,
        })

    elif rol == ROL_RECEPCION:
        total_socios = Socio.objects.count()
        membresias_activas = Membresia.objects.filter(
            estado=Membresia.Estado.ACTIVA,
            fecha_fin__gte=hoy,
        ).count()
        accesos_hoy = RegistroAcceso.objects.filter(fecha_hora__date=hoy).count()
        ultimos_accesos = RegistroAcceso.objects.select_related("socio__usuario").order_by("-fecha_hora")[:8]

        context.update({
            "total_socios": total_socios,
            "membresias_activas": membresias_activas,
            "accesos_hoy": accesos_hoy,
            "ultimos_accesos": ultimos_accesos,
        })

    elif rol == ROL_SOCIO:
        socio = getattr(request.user, "socio", None)
        if socio:
            membresia_actual = obtener_membresia_actual_socio(socio)
            datos_qr = obtener_datos_qr_socio(socio)
            mis_pagos = Pago.objects.filter(
                membresia__socio=socio
            ).select_related("membresia__plan").order_by("-fecha_pago")[:5]
            mis_accesos = socio.accesos.all().order_by("-fecha_hora")[:5]

            dias_restantes = 0
            if membresia_actual and membresia_actual.esta_vigente:
                dias_restantes = (membresia_actual.fecha_fin - hoy).days

            context.update({
                "socio": socio,
                "membresia_actual": membresia_actual,
                "dias_restantes": dias_restantes,
                "datos_qr": datos_qr,
                "mis_pagos": mis_pagos,
                "mis_accesos": mis_accesos,
            })
        else:
            messages.warning(request, "Tu cuenta no tiene una ficha de socio asociada.")

    return render(request, "panel/inicio.html", context)


@login_required
def carnet_socio_view(request, socio_id=None):
    """
    Muestra el carnet digital dinámico del socio con el código QR firmado
    y contador de 30 segundos con auto-recarga vía JavaScript.
    """
    rol = obtener_rol_usuario(request.user)

    if socio_id is not None:
        if rol == ROL_SOCIO and (not hasattr(request.user, "socio") or request.user.socio.id != socio_id):
            raise PermissionDenied("Solo puedes ver tu propio carnet digital.")
        socio = get_object_or_404(Socio.objects.select_related("usuario"), pk=socio_id)
    else:
        if not hasattr(request.user, "socio"):
            messages.error(request, "No se encontró un perfil de socio vinculado a esta cuenta.")
            return redirect("panel:inicio")
        socio = request.user.socio

    datos_qr = obtener_datos_qr_socio(socio)
    membresia_actual = obtener_membresia_actual_socio(socio)

    context = {
        "socio": socio,
        "datos_qr": datos_qr,
        "qr_imagen": datos_qr["qr_imagen"],
        "membresia_actual": membresia_actual,
    }
    return render(request, "panel/carnet.html", context)


@login_required
@recepcion_requerido
def validar_acceso_view(request):
    """Redirige o procesa la validación de acceso mediante la vista de la app 'accesos'."""
    from accesos.views import validar_acceso_view as accesos_validar
    return accesos_validar(request)
