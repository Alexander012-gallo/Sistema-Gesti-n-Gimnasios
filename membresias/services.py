"""
Servicios de negocio para la gestión de planes, membresías, pagos y control de vigencias.
"""

from datetime import timedelta
from decimal import Decimal
import uuid
from django.db import transaction
from django.utils import timezone

from cuentas.models import Socio
from .models import Plan, Membresia, Pago

# Re-exportar servicios de accesos para compatibilidad con código existente
from accesos.services import (  # noqa: F401
    generar_firma_qr,
    crear_qr_socio,
    validar_y_registrar_acceso,
    obtener_datos_qr_socio,
)


def generar_numero_comprobante() -> str:
    """Genera un código único y secuencial/legible para comprobantes de pago."""
    prefijo = timezone.now().strftime("REC-%Y%m%d")
    sufijo = uuid.uuid4().hex[:6].upper()
    return f"{prefijo}-{sufijo}"


@transaction.atomic
def registrar_pago(
    membresia: Membresia,
    monto: Decimal,
    metodo: str,
    registrado_por=None,
    numero_comprobante: str | None = None,
) -> Pago:
    """Registra un pago asociado a una membresía con comprobante único."""
    if not numero_comprobante:
        numero_comprobante = generar_numero_comprobante()

    usuario_registrador = registrado_por if getattr(registrado_por, "is_authenticated", False) else None

    pago = Pago.objects.create(
        membresia=membresia,
        registrado_por=usuario_registrador,
        monto=Decimal(str(monto)),
        metodo=metodo,
        numero_comprobante=numero_comprobante,
    )
    return pago


@transaction.atomic
def asignar_o_renovar_membresia(
    socio: Socio,
    plan: Plan,
    fecha_inicio=None,
    registrado_por=None,
    registrar_pago_automatico: bool = True,
    metodo_pago: str = Pago.Metodo.EFECTIVO,
    monto_pagado: Decimal | None = None,
) -> tuple[Membresia, Pago | None]:
    """
    Crea una nueva membresía o renueva una existente:
    - Si el socio ya tiene una membresía activa vigente, la nueva inicia al día siguiente de su vencimiento.
    - Si no, inicia en la fecha_inicio proporcionada o en la fecha de hoy.
    - Calcula la fecha_fin automáticamente sumando la duración en días del plan.
    - Opcionalmente genera el comprobante de pago de manera atómica.
    """
    hoy = timezone.localdate()

    if fecha_inicio is None:
        # Revisar si tiene membresía activa futura
        membresia_actual = Membresia.objects.filter(
            socio=socio,
            estado=Membresia.Estado.ACTIVA,
            fecha_fin__gte=hoy,
        ).order_by("-fecha_fin").first()

        if membresia_actual:
            fecha_inicio = membresia_actual.fecha_fin + timedelta(days=1)
        else:
            fecha_inicio = hoy

    fecha_fin = fecha_inicio + timedelta(days=plan.duracion_dias)

    membresia = Membresia.objects.create(
        socio=socio,
        plan=plan,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=Membresia.Estado.ACTIVA,
    )

    pago = None
    if registrar_pago_automatico:
        monto = monto_pagado if monto_pagado is not None else plan.precio
        pago = registrar_pago(
            membresia=membresia,
            monto=monto,
            metodo=metodo_pago,
            registrado_por=registrado_por,
        )

    return membresia, pago


def actualizar_estados_vigencias() -> int:
    """
    Actualiza automáticamente el estado de las membresías que hayan superado
    su fecha fin a 'VENCIDA'.
    Devuelve la cantidad de membresías actualizadas.
    """
    hoy = timezone.localdate()
    afectadas = Membresia.objects.filter(
        estado=Membresia.Estado.ACTIVA,
        fecha_fin__lt=hoy,
    ).update(estado=Membresia.Estado.VENCIDA)
    return afectadas


def obtener_membresia_actual_socio(socio: Socio) -> Membresia | None:
    """Retorna la membresía activa actual o la más reciente del socio."""
    hoy = timezone.localdate()
    activa = Membresia.objects.filter(
        socio=socio,
        estado=Membresia.Estado.ACTIVA,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    ).first()

    if activa:
        return activa

    # Si no hay activa, retornar la última registrada
    return Membresia.objects.filter(socio=socio).order_by("-fecha_fin").first()
