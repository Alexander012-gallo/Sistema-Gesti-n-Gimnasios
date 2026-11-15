import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from cuentas.models import Socio
from cuentas.roles import recepcion_requerido, obtener_rol_usuario, ROL_SOCIO
from .models import RegistroAcceso
from .services import validar_y_registrar_acceso, obtener_datos_qr_socio


@login_required
@recepcion_requerido
def validar_acceso_view(request):
    """
    Vista de control de accesos para Recepción/Seguridad.
    Permite validar códigos QR escaneados manual o automáticamente.
    """
    resultado_validacion = None

    if request.method == "POST":
        codigo_qr = request.POST.get("codigo_qr", "").strip()
        puerta = request.POST.get("puerta", "Principal").strip() or "Principal"

        if codigo_qr:
            permitido, mensaje, registro = validar_y_registrar_acceso(
                codigo_qr=codigo_qr,
                puerta=puerta,
                usuario_validador=request.user,
            )
            resultado_validacion = {
                "permitido": permitido,
                "mensaje": mensaje,
                "registro": registro,
                "socio": registro.socio if registro else None,
            }

    # Últimos 5 accesos validados en la sesión
    ultimos_accesos = RegistroAcceso.objects.select_related("socio__usuario").order_by("-fecha_hora")[:5]

    context = {
        "resultado": resultado_validacion,
        "ultimos_accesos": ultimos_accesos,
    }
    return render(request, "accesos/validar.html", context)


@login_required
@recepcion_requerido
@require_POST
def api_validar_acceso(request):
    """API endpoint para escáneres automáticos o lectores de torniquete."""
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else request.POST
        codigo_qr = data.get("codigo_qr", "").strip()
        puerta = data.get("puerta", "Principal")
    except Exception:
        return JsonResponse({"ok": False, "permitido": False, "mensaje": "Datos JSON inválidos."}, status=400)

    permitido, mensaje, registro = validar_y_registrar_acceso(
        codigo_qr=codigo_qr,
        puerta=puerta,
        usuario_validador=request.user,
    )

    return JsonResponse({
        "ok": True,
        "permitido": permitido,
        "mensaje": mensaje,
        "socio": registro.socio.nombre_completo if registro and registro.socio else None,
        "documento": registro.socio.documento_identidad if registro and registro.socio else None,
        "resultado": registro.resultado if registro else "ERROR",
        "fecha_hora": registro.fecha_hora.isoformat() if registro else None,
    })


@login_required
@require_GET
def api_generar_qr_socio(request):
    """
    API endpoint para la renovación en tiempo real del código QR cada 30 segundos.
    Si el usuario es socio, devuelve su propio QR.
    Si es admin o recepción, puede consultar el QR pasando socio_id en GET.
    """
    rol = obtener_rol_usuario(request.user)
    socio_id = request.GET.get("socio_id")

    if socio_id and rol != ROL_SOCIO:
        socio = get_object_or_404(Socio, pk=socio_id)
    else:
        if not hasattr(request.user, "socio"):
            return JsonResponse({"ok": False, "error": "No se encontró ficha de socio para el usuario."}, status=404)
        socio = request.user.socio

    datos_qr = obtener_datos_qr_socio(socio)
    datos_qr["ok"] = True
    if datos_qr.get("fecha_fin"):
        datos_qr["fecha_fin"] = datos_qr["fecha_fin"].strftime("%d/%m/%Y")

    return JsonResponse(datos_qr)


@login_required
@recepcion_requerido
def historial_accesos_view(request):
    """Auditoría e historial completo de accesos con filtros por fecha, puerta y resultado."""
    query = request.GET.get("q", "").strip()
    resultado_filtro = request.GET.get("resultado", "").strip()
    puerta_filtro = request.GET.get("puerta", "").strip()
    fecha_filtro = request.GET.get("fecha", "").strip()

    accesos = RegistroAcceso.objects.select_related("socio__usuario", "validado_por").all()

    if resultado_filtro:
        accesos = accesos.filter(resultado=resultado_filtro)

    if puerta_filtro:
        accesos = accesos.filter(puerta=puerta_filtro)

    if fecha_filtro == "hoy":
        accesos = accesos.filter(fecha_hora__date=timezone.localdate())

    if query:
        accesos = accesos.filter(
            Q(socio__usuario__first_name__icontains=query)
            | Q(socio__usuario__last_name__icontains=query)
            | Q(socio__documento_identidad__icontains=query)
        )

    context = {
        "accesos": accesos[:100],
        "query": query,
        "resultado_filtro": resultado_filtro,
        "puerta_filtro": puerta_filtro,
        "fecha_filtro": fecha_filtro,
        "resultados_choices": RegistroAcceso.Resultado.choices,
    }
    return render(request, "accesos/historial.html", context)
