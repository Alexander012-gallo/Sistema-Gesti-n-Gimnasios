"""
Servicios para la generación y validación de códigos QR e historial de accesos.
El código QR es dinámico, firmado mediante HMAC SHA-256 y cuenta con una ventana
de vigencia de 30 segundos para evitar clonación o capturas estáticas.
"""

import base64
from io import BytesIO
import hmac
import hashlib
from django.conf import settings
from django.utils import timezone
import qrcode

from cuentas.models import Socio
from .models import RegistroAcceso


def generar_firma_qr(socio_id: int, timestamp: int) -> str:
    """Genera una firma HMAC SHA256 para autenticar el QR emitido para el socio."""
    mensaje = f"{socio_id}:{timestamp}".encode("utf-8")
    secreto = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(secreto, mensaje, hashlib.sha256).hexdigest()


def generar_payload_qr(socio_id: int, timestamp: int | None = None) -> tuple[str, int]:
    """Crea la cadena payload con formato socio_id|timestamp|firma."""
    if timestamp is None:
        timestamp = int(timezone.now().timestamp())
    firma = generar_firma_qr(socio_id, timestamp)
    payload = f"{socio_id}|{timestamp}|{firma}"
    return payload, timestamp


def renderizar_qr_base64(payload: str) -> str:
    """Renderiza cualquier cadena de datos a imagen PNG codificada en Base64."""
    qr = qrcode.QRCode(
        box_size=10,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def crear_qr_socio(socio: Socio) -> str:
    """
    Genera un código QR dinámico cifrado en Base64 para el carnet digital del socio.
    Función compatible con vistas tradicionales.
    """
    payload, _ = generar_payload_qr(socio.id)
    return renderizar_qr_base64(payload)


def obtener_datos_qr_socio(socio: Socio) -> dict:
    """
    Devuelve los datos completos del QR dinámico del socio,
    incluyendo imagen base64, timestamp y estado de vigencia.
    """
    ahora = int(timezone.now().timestamp())
    payload, timestamp = generar_payload_qr(socio.id, ahora)
    qr_imagen = renderizar_qr_base64(payload)

    # Verificar si el socio cuenta con membresía vigente
    from membresias.models import Membresia
    hoy = timezone.localdate()
    membresia_activa = Membresia.objects.filter(
        socio=socio,
        estado=Membresia.Estado.ACTIVA,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    ).first()

    validez = getattr(settings, "QR_VALIDEZ_SEGUNDOS", 30)

    return {
        "socio_id": socio.id,
        "nombre_socio": socio.nombre_completo,
        "documento": socio.documento_identidad,
        "payload": payload,
        "qr_imagen": qr_imagen,
        "timestamp": timestamp,
        "validez_segundos": validez,
        "segundos_restantes": validez,
        "membresia_vigente": bool(membresia_activa),
        "plan_nombre": membresia_activa.plan.nombre if membresia_activa else "Sin membresía activa",
        "fecha_fin": membresia_activa.fecha_fin if membresia_activa else None,
    }


def validar_y_registrar_acceso(
    codigo_qr: str,
    puerta: str = "Principal",
    usuario_validador=None,
) -> tuple[bool, str, RegistroAcceso | None]:
    """
    Procesa la lectura del QR en el punto de acceso (torniquete/recepción):
    1. Valida estructura del payload.
    2. Valida la firma HMAC criptográfica.
    3. Valida la ventana de expiración del timestamp (ej. 30 segundos).
    4. Verifica que el socio exista y su cuenta esté activa.
    5. Verifica que tenga membresía ACTIVA y vigente para la fecha actual.
    6. Registra el intento en RegistroAcceso para auditoría total.
    """
    codigo_qr = (codigo_qr or "").strip()
    socio = None

    try:
        partes = codigo_qr.split("|")
        if len(partes) != 3:
            registro = RegistroAcceso.objects.create(
                socio=None,
                validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
                puerta=puerta,
                resultado=RegistroAcceso.Resultado.FIRMA_INVALIDA,
            )
            return False, "Formato de código QR inválido.", registro

        socio_id_str, timestamp_str, firma_recibida = partes
        socio_id = int(socio_id_str)
        timestamp = int(timestamp_str)
    except (ValueError, TypeError):
        registro = RegistroAcceso.objects.create(
            socio=None,
            validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
            puerta=puerta,
            resultado=RegistroAcceso.Resultado.FIRMA_INVALIDA,
        )
        return False, "Estructura de datos no válida en el QR.", registro

    # Intentar obtener el socio
    try:
        socio = Socio.objects.select_related("usuario").get(pk=socio_id)
    except Socio.DoesNotExist:
        registro = RegistroAcceso.objects.create(
            socio=None,
            validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
            puerta=puerta,
            resultado=RegistroAcceso.Resultado.SOCIO_INACTIVO,
        )
        return False, "Socio no encontrado en el sistema.", registro

    if not socio.usuario.is_active:
        registro = RegistroAcceso.objects.create(
            socio=socio,
            validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
            puerta=puerta,
            resultado=RegistroAcceso.Resultado.SOCIO_INACTIVO,
        )
        return False, "El usuario del socio se encuentra inactivo.", registro

    # Validar firma HMAC
    firma_esperada = generar_firma_qr(socio_id, timestamp)
    if not hmac.compare_digest(firma_esperada, firma_recibida):
        registro = RegistroAcceso.objects.create(
            socio=socio,
            validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
            puerta=puerta,
            resultado=RegistroAcceso.Resultado.FIRMA_INVALIDA,
        )
        return False, "Firma digital del QR no válida (posible adulteración).", registro

    # Validar expiración temporal (30 segundos por defecto, con tolerancia de reloj de 5s futuros)
    ahora = int(timezone.now().timestamp())
    validez_max = getattr(settings, "QR_VALIDEZ_SEGUNDOS", 30)

    # Si el timestamp es del futuro lejano o ya pasó la validez
    if (ahora - timestamp) > validez_max or (timestamp - ahora) > 5:
        registro = RegistroAcceso.objects.create(
            socio=socio,
            validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
            puerta=puerta,
            resultado=RegistroAcceso.Resultado.QR_EXPIRADO,
        )
        return False, f"Código QR expirado (válido únicamente durante {validez_max} segundos).", registro

    # Validar membresía vigente
    from membresias.models import Membresia

    hoy = timezone.localdate()
    membresia_activa = Membresia.objects.filter(
        socio=socio,
        estado=Membresia.Estado.ACTIVA,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    ).first()

    if not membresia_activa:
        registro = RegistroAcceso.objects.create(
            socio=socio,
            validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
            puerta=puerta,
            resultado=RegistroAcceso.Resultado.MEMBRESIA_VENCIDA,
        )
        return False, f"Acceso denegado: El socio {socio.nombre_completo} no posee membresía vigente.", registro

    # Acceso permitido
    registro = RegistroAcceso.objects.create(
        socio=socio,
        validado_por=usuario_validador if getattr(usuario_validador, "is_authenticated", False) else None,
        puerta=puerta,
        resultado=RegistroAcceso.Resultado.PERMITIDO,
    )
    return True, f"¡Acceso permitido! Bienvenido/a, {socio.nombre_completo}.", registro
