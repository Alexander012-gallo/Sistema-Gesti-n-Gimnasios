"""
Servicios de negocio para la gestión de cuentas, usuarios y socios.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from .models import Socio
from .roles import ROL_SOCIO, ROL_RECEPCION, ROL_ADMIN

User = get_user_model()


@transaction.atomic
def registrar_socio(
    *,
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    documento_identidad: str,
    telefono: str = "",
    foto=None,
) -> Socio:
    """
    Crea un usuario y su perfil de socio correspondiente de forma atómica.
    Asigna automáticamente el rol de 'Socio'.
    """
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    grupo_socio, _ = Group.objects.get_or_create(name=ROL_SOCIO)
    user.groups.add(grupo_socio)

    socio = Socio.objects.create(
        usuario=user,
        documento_identidad=documento_identidad,
        telefono=telefono,
        foto=foto,
    )
    return socio


@transaction.atomic
def actualizar_socio(
    socio: Socio,
    *,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    telefono: str = None,
    foto=None,
) -> Socio:
    """Actualiza datos del socio y de su usuario subyacente."""
    usuario = socio.usuario
    modificado_user = False

    if first_name is not None:
        usuario.first_name = first_name
        modificado_user = True
    if last_name is not None:
        usuario.last_name = last_name
        modificado_user = True
    if email is not None:
        usuario.email = email
        modificado_user = True

    if modificado_user:
        usuario.save()

    if telefono is not None:
        socio.telefono = telefono
    if foto is not None:
        socio.foto = foto

    socio.save()
    return socio
