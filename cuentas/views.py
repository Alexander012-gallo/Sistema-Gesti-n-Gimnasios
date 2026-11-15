from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import SocioRegistroForm, SocioEdicionForm
from .models import Socio
from .roles import recepcion_requerido, obtener_rol_usuario, ROL_SOCIO
from .services import registrar_socio, actualizar_socio


@login_required
@recepcion_requerido
def lista_socios_view(request):
    """Listado de socios con búsqueda por nombre, documento o teléfono."""
    query = request.GET.get("q", "").strip()
    socios = Socio.objects.select_related("usuario").prefetch_related("membresias__plan")

    if query:
        socios = socios.filter(
            Q(usuario__first_name__icontains=query)
            | Q(usuario__last_name__icontains=query)
            | Q(documento_identidad__icontains=query)
            | Q(telefono__icontains=query)
            | Q(usuario__username__icontains=query)
        )

    context = {
        "socios": socios,
        "query": query,
    }
    return render(request, "cuentas/lista_socios.html", context)


@login_required
@recepcion_requerido
def crear_socio_view(request):
    """Registro de un nuevo socio y su cuenta de usuario."""
    if request.method == "POST":
        form = SocioRegistroForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            socio = registrar_socio(
                username=data["username"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                password=data["password"],
                documento_identidad=data["documento_identidad"],
                telefono=data["telefono"],
                foto=data.get("foto"),
            )
            messages.success(request, f"Socio '{socio.nombre_completo}' registrado con éxito.")
            return redirect("cuentas:detalle_socio", socio_id=socio.id)
    else:
        form = SocioRegistroForm()

    return render(request, "cuentas/form_socio.html", {"form": form, "titulo": "Registrar Nuevo Socio"})


@login_required
@recepcion_requerido
def detalle_socio_view(request, socio_id):
    """Ficha informativa detallada del socio: datos, membresías, pagos y accesos."""
    socio = get_object_or_404(
        Socio.objects.select_related("usuario").prefetch_related("membresias__plan", "membresias__pagos", "accesos"),
        pk=socio_id,
    )
    membresias = socio.membresias.all().order_by("-fecha_inicio")
    ultimos_accesos = socio.accesos.all().order_by("-fecha_hora")[:10]

    context = {
        "socio": socio,
        "membresias": membresias,
        "ultimos_accesos": ultimos_accesos,
    }
    return render(request, "cuentas/detalle_socio.html", context)


@login_required
@recepcion_requerido
def editar_socio_view(request, socio_id):
    """Edición de datos del socio."""
    socio = get_object_or_404(Socio.objects.select_related("usuario"), pk=socio_id)

    if request.method == "POST":
        form = SocioEdicionForm(request.POST, request.FILES, instance=socio)
        if form.is_valid():
            actualizar_socio(
                socio,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                telefono=form.cleaned_data["telefono"],
                foto=form.cleaned_data.get("foto"),
            )
            messages.success(request, f"Datos de '{socio.nombre_completo}' actualizados correctamente.")
            return redirect("cuentas:detalle_socio", socio_id=socio.id)
    else:
        form = SocioEdicionForm(instance=socio)

    return render(
        request,
        "cuentas/form_socio.html",
        {"form": form, "titulo": f"Editar Socio: {socio.nombre_completo}", "socio": socio},
    )


@login_required
def perfil_socio_view(request):
    """Vista de perfil para el socio autenticado."""
    rol = obtener_rol_usuario(request.user)
    if not hasattr(request.user, "socio"):
        messages.info(request, "Tu cuenta no tiene una ficha de socio asociada.")
        return redirect("panel:inicio")

    socio = request.user.socio
    membresias = socio.membresias.all().order_by("-fecha_inicio")
    ultimos_accesos = socio.accesos.all().order_by("-fecha_hora")[:10]

    context = {
        "socio": socio,
        "membresias": membresias,
        "ultimos_accesos": ultimos_accesos,
        "es_propio": True,
    }
    return render(request, "cuentas/detalle_socio.html", context)
