from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from cuentas.models import Socio


class Plan(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    precio = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    duracion_dias = models.PositiveIntegerField(
        validators=[MinValueValidator(1)])
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (US$ {self.precio}, {self.duracion_dias} días)"


class Membresia(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        VENCIDA = "VENCIDA", "Vencida"
        SUSPENDIDA = "SUSPENDIDA", "Suspendida"

    socio = models.ForeignKey(
        Socio, on_delete=models.PROTECT, related_name="membresias")
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name="membresias")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=12, choices=Estado.choices, default=Estado.ACTIVA
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_inicio"]
        indexes = [
            models.Index(fields=["socio", "estado"]),
            models.Index(fields=["fecha_fin"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="membresia_fechas_validas",
            ),
        ]

    @property
    def esta_vigente(self):
        hoy = timezone.localdate()
        return (
            self.estado == self.Estado.ACTIVA
            and self.fecha_inicio <= hoy <= self.fecha_fin
        )

    def __str__(self):
        return f"{self.socio} · {self.plan.nombre} · {self.fecha_inicio} a {self.fecha_fin}"


class Pago(models.Model):
    class Metodo(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"

    membresia = models.ForeignKey(
        Membresia, on_delete=models.PROTECT, related_name="pagos"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos_registrados",
    )
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    metodo = models.CharField(max_length=15, choices=Metodo.choices)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    numero_comprobante = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["-fecha_pago"]

    def __str__(self) -> str:
        return str(self.numero_comprobante)
