from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from cuentas.models import Socio
from cuentas.roles import (
    garantizar_roles_y_permisos,
    ROL_ADMIN,
    ROL_RECEPCION,
    ROL_SOCIO,
)
from membresias.models import Plan, Membresia, Pago
from membresias.services import asignar_o_renovar_membresia

User = get_user_model()


class Command(BaseCommand):
    help = "Crea usuarios de prueba representativos para cada uno de los tres roles (Admin, Recepción, Socio)."

    def handle(self, *args, **options):
        garantizar_roles_y_permisos()
        grupo_admin = Group.objects.get(name=ROL_ADMIN)
        grupo_recep = Group.objects.get(name=ROL_RECEPCION)
        grupo_socio = Group.objects.get(name=ROL_SOCIO)

        # 1. Administrador demo
        admin_user, creado = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Administrador",
                "last_name": "Principal",
                "email": "admin@gym.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.groups.add(grupo_admin)
        admin_user.save()

        # 2. Recepción demo
        recep_user, _ = User.objects.get_or_create(
            username="recepcion",
            defaults={
                "first_name": "Ana",
                "last_name": "Recepción",
                "email": "recepcion@gym.com",
                "is_staff": False,
            },
        )
        recep_user.set_password("recepcion123")
        recep_user.groups.add(grupo_recep)
        recep_user.save()

        # 3. Plan de prueba
        plan, _ = Plan.objects.get_or_create(
            nombre="Plan Mensual Pro",
            defaults={
                "precio": Decimal("49.99"),
                "duracion_dias": 30,
                "descripcion": "Acceso ilimitado al gimnasio, sala de pesas y cardio.",
                "activo": True,
            },
        )

        # 4. Socio demo
        socio_user, _ = User.objects.get_or_create(
            username="socio",
            defaults={
                "first_name": "Carlos",
                "last_name": "Gómez",
                "email": "carlos.socio@gmail.com",
            },
        )
        socio_user.set_password("socio123")
        socio_user.groups.add(grupo_socio)
        socio_user.save()

        socio, _ = Socio.objects.get_or_create(
            usuario=socio_user,
            defaults={
                "documento_identidad": "DNI77889900",
                "telefono": "+51 987654321",
            },
        )

        # Asignar membresía vigente al socio demo para que el QR sea válido
        hoy = timezone.localdate()
        membresia_activa = Membresia.objects.filter(
            socio=socio,
            estado=Membresia.Estado.ACTIVA,
            fecha_fin__gte=hoy,
        ).first()

        if not membresia_activa:
            asignar_o_renovar_membresia(
                socio=socio,
                plan=plan,
                fecha_inicio=hoy,
                registrado_por=admin_user,
                registrar_pago_automatico=True,
                metodo_pago=Pago.Metodo.EFECTIVO,
                monto_pagado=plan.precio,
            )

        self.stdout.write(self.style.SUCCESS("Usuarios demo creados / actualizados con éxito."))
