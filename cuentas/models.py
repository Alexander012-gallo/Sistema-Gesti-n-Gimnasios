from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

validar_documento = RegexValidator(
    regex=r"^[A-Za-z0-9]{5,20}$",
    message="El documento debe tener entre 5 y 20 letras o números, sin espacios.",
)


class Socio(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="socio"
    )
    documento_identidad = models.CharField(
        max_length=20, unique=True, validators=[validar_documento]
    )
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to="socios/%Y/%m/", blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["usuario__last_name", "usuario__first_name"]

    @property
    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username

    def __str__(self):
        return f"{self.nombre_completo} ({self.documento_identidad})"
