from django.conf import settings
from django.db import models
from cuentas.models import Socio


class RegistroAcceso(models.Model):
    class Resultado(models.TextChoices):
        PERMITIDO = "ACCESO_PERMITIDO", "Acceso permitido"
        MEMBRESIA_VENCIDA = "DENEGADO_MEMBRESIA_VENCIDA", "Denegado: membresía no vigente"
        QR_EXPIRADO = "DENEGADO_QR_EXPIRADO", "Denegado: QR expirado"
        FIRMA_INVALIDA = "DENEGADO_FIRMA_INVALIDA", "Denegado: QR inválido"
        SOCIO_INACTIVO = "DENEGADO_SOCIO_INACTIVO", "Denegado: socio inactivo"

    socio = models.ForeignKey(
        Socio, on_delete=models.SET_NULL, null=True, blank=True, related_name="accesos"
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validaciones",
    )
    puerta = models.CharField(max_length=30, default="Principal")
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    resultado = models.CharField(max_length=35, choices=Resultado.choices)

    class Meta:
        ordering = ["-fecha_hora"]
        indexes = [models.Index(fields=["socio", "fecha_hora"])]

    def __str__(self):
        return f"{self.fecha_hora:%d/%m/%Y %H:%M:%S} · {self.resultado}"
