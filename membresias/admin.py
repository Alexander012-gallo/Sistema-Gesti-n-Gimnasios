from django.contrib import admin
from .models import Plan, Membresia, Pago


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "duracion_dias", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "socio",
        "plan",
        "fecha_inicio",
        "fecha_fin",
        "estado",
        "esta_vigente",
    )
    list_filter = ("estado", "plan", "fecha_inicio", "fecha_fin")
    search_fields = (
        "socio__documento_identidad",
        "socio__usuario__first_name",
        "socio__usuario__last_name",
        "plan__nombre",
    )
    list_select_related = ("socio__usuario", "plan")


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_comprobante",
        "membresia",
        "monto",
        "metodo",
        "fecha_pago",
        "registrado_por",
    )
    list_filter = ("metodo", "fecha_pago")
    search_fields = (
        "numero_comprobante",
        "membresia__socio__documento_identidad",
        "membresia__socio__usuario__first_name",
        "membresia__socio__usuario__last_name",
    )
    list_select_related = ("membresia__socio__usuario", "registrado_por")
