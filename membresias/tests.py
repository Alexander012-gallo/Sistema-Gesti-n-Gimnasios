from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from cuentas.models import Socio
from .models import Plan, Membresia, Pago
from .services import (
    asignar_o_renovar_membresia,
    registrar_pago,
    actualizar_estados_vigencias,
)

User = get_user_model()


class MembresiasServicesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user",
            password="password123",
            first_name="Ana",
            last_name="Ríos",
        )
        self.socio = Socio.objects.create(
            usuario=self.user,
            documento_identidad="DOC987654",
        )
        self.plan = Plan.objects.create(
            nombre="Plan Anual",
            precio=Decimal("300.00"),
            duracion_dias=365,
        )

    def test_asignacion_membresia_con_pago_automatico(self):
        membresia, pago = asignar_o_renovar_membresia(
            socio=self.socio,
            plan=self.plan,
            registrar_pago_automatico=True,
            metodo_pago=Pago.Metodo.TARJETA,
        )

        self.assertIsNotNone(membresia)
        self.assertEqual(membresia.estado, Membresia.Estado.ACTIVA)
        self.assertEqual(membresia.fecha_fin, membresia.fecha_inicio + timedelta(days=365))
        self.assertTrue(membresia.esta_vigente)

        self.assertIsNotNone(pago)
        self.assertEqual(pago.monto, Decimal("300.00"))
        self.assertEqual(pago.metodo, Pago.Metodo.TARJETA)
        self.assertTrue(pago.numero_comprobante.startswith("REC-"))

    def test_renovacion_encadena_fechas_correctamente(self):
        # Primera membresía
        mem1, _ = asignar_o_renovar_membresia(socio=self.socio, plan=self.plan)

        # Segunda membresía debe iniciar al día siguiente de la primera
        plan_mensual = Plan.objects.create(
            nombre="Plan Mes Adicional",
            precio=Decimal("35.00"),
            duracion_dias=30,
        )
        mem2, _ = asignar_o_renovar_membresia(socio=self.socio, plan=plan_mensual)

        self.assertEqual(mem2.fecha_inicio, mem1.fecha_fin + timedelta(days=1))
        self.assertEqual(mem2.fecha_fin, mem2.fecha_inicio + timedelta(days=30))

    def test_actualizacion_automatica_de_vigencias(self):
        ayer = timezone.localdate() - timedelta(days=1)
        Membresia.objects.create(
            socio=self.socio,
            plan=self.plan,
            fecha_inicio=ayer - timedelta(days=30),
            fecha_fin=ayer,
            estado=Membresia.Estado.ACTIVA,
        )

        actualizadas = actualizar_estados_vigencias()
        self.assertEqual(actualizadas, 1)

        mem = Membresia.objects.get(socio=self.socio)
        self.assertEqual(mem.estado, Membresia.Estado.VENCIDA)
        self.assertFalse(mem.esta_vigente)
