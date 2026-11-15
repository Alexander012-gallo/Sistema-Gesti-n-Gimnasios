from django.contrib import admin
from .models import RegistroAcceso


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fecha_hora",
        "socio",
        "puerta",
        "resultado",
        "validado_por",
    )
    list_filter = ("resultado", "puerta", "fecha_hora")
    search_fields = (
        "socio__documento_identidad",
        "socio__usuario__first_name",
        "socio__usuario__last_name",
        "puerta",
    )
    list_select_related = ("socio__usuario", "validado_por")
    date_hierarchy = "fecha_hora"
