from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from .models import Socio
from .roles import (
    obtener_rol_usuario,
    garantizar_roles_y_permisos,
    ROL_ADMIN,
    ROL_RECEPCION,
    ROL_SOCIO,
)
from .services import registrar_socio

User = get_user_model()


class CuentasRolesTestCase(TestCase):
    def setUp(self):
        garantizar_roles_y_permisos()

    def test_registro_socio_servicio(self):
        socio = registrar_socio(
            username="lucas_socio",
            first_name="Lucas",
            last_name="Torres",
            email="lucas@test.com",
            password="securepassword",
            documento_identidad="DNI458921",
            telefono="999888777",
        )

        self.assertEqual(socio.documento_identidad, "DNI458921")
        self.assertEqual(socio.nombre_completo, "Lucas Torres")
        self.assertEqual(obtener_rol_usuario(socio.usuario), ROL_SOCIO)

    def test_identificacion_rol_admin(self):
        admin_user = User.objects.create_superuser(
            username="super_admin",
            email="admin@test.com",
            password="adminpassword",
        )
        self.assertEqual(obtener_rol_usuario(admin_user), ROL_ADMIN)

    def test_identificacion_rol_recepcion(self):
        recep_user = User.objects.create_user(
            username="recepcion_1",
            email="recep@test.com",
            password="receppassword",
        )
        grupo_recep = Group.objects.get(name=ROL_RECEPCION)
        recep_user.groups.add(grupo_recep)

        self.assertEqual(obtener_rol_usuario(recep_user), ROL_RECEPCION)
