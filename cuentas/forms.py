from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Socio, validar_documento

User = get_user_model()


class SocioRegistroForm(forms.Form):
    first_name = forms.CharField(
        label="Nombres",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Juan Carlos"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Pérez Gómez"}),
    )
    documento_identidad = forms.CharField(
        label="Documento de Identidad",
        max_length=20,
        validators=[validar_documento],
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "DNI, Cédula o Pasaporte"}),
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "socio@email.com"}),
    )
    telefono = forms.CharField(
        label="Teléfono / Celular",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+51 987654321"}),
    )
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "usuario_login"}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    foto = forms.ImageField(
        label="Fotografía del Socio",
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_documento_identidad(self):
        documento = self.cleaned_data.get("documento_identidad")
        if Socio.objects.filter(documento_identidad=documento).exists():
            raise ValidationError("Ya existe un socio registrado con este documento de identidad.")
        return documento


class SocioEdicionForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombres",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Socio
        fields = ["documento_identidad", "telefono", "foto"]
        widgets = {
            "documento_identidad": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "foto": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.usuario.first_name
            self.fields["last_name"].initial = self.instance.usuario.last_name
            self.fields["email"].initial = self.instance.usuario.email
