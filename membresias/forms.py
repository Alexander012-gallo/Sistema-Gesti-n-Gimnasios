from django import forms
from django.utils import timezone
from .models import Plan, Membresia, Pago
from cuentas.models import Socio


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["nombre", "precio", "duracion_dias", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Mensual Básico"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "duracion_dias": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AsignarMembresiaForm(forms.Form):
    socio = forms.ModelChoiceField(
        queryset=Socio.objects.select_related("usuario").order_by("usuario__last_name", "usuario__first_name"),
        label="Socio",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(activo=True),
        label="Plan de Gimnasio",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    fecha_inicio = forms.DateField(
        label="Fecha de Inicio",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        help_text="Opcional: Si se deja en blanco, inicia hoy o al finalizar su membresía activa.",
    )
    registrar_pago = forms.BooleanField(
        label="Registrar Pago Inmediato",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    metodo_pago = forms.ChoiceField(
        choices=Pago.Metodo.choices,
        label="Método de Pago",
        required=False,
        initial=Pago.Metodo.EFECTIVO,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    monto = forms.DecimalField(
        label="Monto Pagado",
        required=False,
        max_digits=8,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Monto del plan"}),
        help_text="Si se deja vacío se aplicará el precio del plan seleccionado.",
    )


class PagoRegistroForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["membresia", "monto", "metodo"]
        widgets = {
            "membresia": forms.Select(attrs={"class": "form-select"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "metodo": forms.Select(attrs={"class": "form-select"}),
        }
