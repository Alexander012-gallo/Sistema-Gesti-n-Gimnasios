from django.contrib import admin
from .models import Socio


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ("id", "documento_identidad", "nombre_completo", "telefono", "creado_en")
    search_fields = (
        "documento_identidad",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__username",
        "telefono",
    )
    list_filter = ("creado_en",)
    list_select_related = ("usuario",)
