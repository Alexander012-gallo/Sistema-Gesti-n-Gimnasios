from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from cuentas.models import Socio
from cuentas.roles import admin_requerido, recepcion_requerido, obtener_rol_usuario, ROL_SOCIO
from .forms import PlanForm, AsignarMembresiaForm, PagoRegistroForm
from .models import Plan, Membresia, Pago
from .services import (
    asignar_o_renovar_membresia,
    registrar_pago,
    actualizar_estados_vigencias,
)


# === GESTIÓN DE PLANES (ADMIN) ===

@login_required
@admin_requerido
def lista_planes_view(request):
    """Listado de todos los planes de membresía creados."""
    planes = Plan.objects.all().order_by("-activo", "precio")
    return render(request, "membresias/lista_planes.html", {"planes": planes})


@login_required
@admin_requerido
def crear_plan_view(request):
    """Creación de un nuevo plan de suscripción."""
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f"Plan '{plan.nombre}' creado exitosamente.")
            return redirect("membresias:lista_planes")
    else:
        form = PlanForm()

    return render(request, "membresias/form_plan.html", {"form": form, "titulo": "Crear Plan de Membresía"})


@login_required
@admin_requerido
def editar_plan_view(request, plan_id):
    """Edición de un plan existente."""
    plan = get_object_or_404(Plan, pk=plan_id)
    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plan '{plan.nombre}' actualizado.")
            return redirect("membresias:lista_planes")
    else:
        form = PlanForm(instance=plan)

    return render(request, "membresias/form_plan.html", {"form": form, "titulo": f"Editar Plan: {plan.nombre}", "plan": plan})


# === GESTIÓN DE MEMBRESÍAS (RECEPCIÓN Y ADMIN) ===

@login_required
@recepcion_requerido
def lista_membresias_view(request):
    """Listado general de membresías y vigencias con filtros."""
    actualizar_estados_vigencias()
    query = request.GET.get("q", "").strip()
    filtro_estado = request.GET.get("estado", "").strip()

    membresias = Membresia.objects.select_related("socio__usuario", "plan").all()

    if filtro_estado:
        membresias = membresias.filter(estado=filtro_estado)

    if query:
        membresias = membresias.filter(
            Q(socio__usuario__first_name__icontains=query)
            | Q(socio__usuario__last_name__icontains=query)
            | Q(socio__documento_identidad__icontains=query)
            | Q(plan__nombre__icontains=query)
        )

    context = {
        "membresias": membresias,
        "query": query,
        "filtro_estado": filtro_estado,
        "estados": Membresia.Estado.choices,
    }
    return render(request, "membresias/lista_membresias.html", context)


@login_required
@recepcion_requerido
def asignar_membresia_view(request):
    """Asignación o renovación de una membresía con opción de registro de pago."""
    socio_id_param = request.GET.get("socio")
    initial_data = {}
    if socio_id_param:
        initial_data["socio"] = socio_id_param

    if request.method == "POST":
        form = AsignarMembresiaForm(request.POST)
        if form.is_valid():
            socio = form.cleaned_data["socio"]
            plan = form.cleaned_data["plan"]
            fecha_inicio = form.cleaned_data.get("fecha_inicio")
            registrar_pago_auto = form.cleaned_data.get("registrar_pago", False)
            metodo = form.cleaned_data.get("metodo_pago", Pago.Metodo.EFECTIVO)
            monto = form.cleaned_data.get("monto")

            membresia, pago = asignar_o_renovar_membresia(
                socio=socio,
                plan=plan,
                fecha_inicio=fecha_inicio,
                registrado_por=request.user,
                registrar_pago_automatico=registrar_pago_auto,
                metodo_pago=metodo,
                monto_pagado=monto,
            )

            msg = f"Membresía asignada a '{socio.nombre_completo}' ({plan.nombre}) hasta {membresia.fecha_fin}."
            if pago:
                msg += f" Comprobante generado: {pago.numero_comprobante}."
            messages.success(request, msg)
            return redirect("cuentas:detalle_socio", socio_id=socio.id)
    else:
        form = AsignarMembresiaForm(initial=initial_data)

    return render(request, "membresias/form_asignar.html", {"form": form})


# === GESTIÓN DE PAGOS (RECEPCIÓN Y ADMIN) ===

@login_required
@recepcion_requerido
def lista_pagos_view(request):
    """Historial y registro contable de pagos recibidos."""
    query = request.GET.get("q", "").strip()
    pagos = Pago.objects.select_related("membresia__socio__usuario", "membresia__plan", "registrado_por").all()

    if query:
        pagos = pagos.filter(
            Q(numero_comprobante__icontains=query)
            | Q(membresia__socio__documento_identidad__icontains=query)
            | Q(membresia__socio__usuario__first_name__icontains=query)
            | Q(membresia__socio__usuario__last_name__icontains=query)
        )

    return render(request, "membresias/lista_pagos.html", {"pagos": pagos, "query": query})


@login_required
@recepcion_requerido
def registrar_pago_view(request):
    """Registro individual de un pago para una membresía."""
    if request.method == "POST":
        form = PagoRegistroForm(request.POST)
        if form.is_valid():
            pago = registrar_pago(
                membresia=form.cleaned_data["membresia"],
                monto=form.cleaned_data["monto"],
                metodo=form.cleaned_data["metodo"],
                registrado_por=request.user,
            )
            messages.success(request, f"Pago registrado con éxito. Comprobante: {pago.numero_comprobante}")
            return redirect("membresias:comprobante_pago", pago_id=pago.id)
    else:
        membresia_id = request.GET.get("membresia")
        initial_data = {}
        if membresia_id:
            try:
                membresia_obj = Membresia.objects.get(pk=membresia_id)
                initial_data = {"membresia": membresia_obj, "monto": membresia_obj.plan.precio}
            except Membresia.DoesNotExist:
                pass
        form = PagoRegistroForm(initial=initial_data)

    return render(request, "membresias/form_pago.html", {"form": form})


@login_required
def detalle_comprobante_pago_view(request, pago_id):
    """Comprobante oficial de pago para impresión o consulta."""
    pago = get_object_or_404(
        Pago.objects.select_related("membresia__socio__usuario", "membresia__plan", "registrado_por"),
        pk=pago_id,
    )

    # Validar que un socio solo pueda ver sus propios comprobantes
    rol = obtener_rol_usuario(request.user)
    if rol == ROL_SOCIO:
        if not hasattr(request.user, "socio") or pago.membresia.socio != request.user.socio:
            raise PermissionDenied("No tienes permiso para ver este comprobante.")

    return render(request, "membresias/comprobante_pago.html", {"pago": pago})
