import time
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from cuentas.models import Socio
from membresias.models import Plan, Membresia
from .models import RegistroAcceso
from .services import (
    generar_firma_qr,
    generar_payload_qr,
    crear_qr_socio,
    validar_y_registrar_acceso,
)

User = get_user_model()


class AccesosQRE2ETestCase(TestCase):
    def setUp(self):
        # Crear usuario y socio
        self.user = User.objects.create_user(
            username="socio_test",
            password="password123",
            first_name="Carlos",
            last_name="Valdez",
        )
        self.socio = Socio.objects.create(
            usuario=self.user,
            documento_identidad="DOC123456",
            telefono="555-1234",
        )

        # Plan de 30 días
        self.plan = Plan.objects.create(
            nombre="Plan Mensual Pro",
            precio=50.00,
            duracion_dias=30,
            activo=True,
        )

        # Membresía activa
        self.hoy = timezone.localdate()
        self.membresia = Membresia.objects.create(
            socio=self.socio,
            plan=self.plan,
            fecha_inicio=self.hoy,
            fecha_fin=self.hoy + timedelta(days=30),
            estado=Membresia.Estado.ACTIVA,
        )

    def test_generacion_qr_valido(self):
        qr_b64 = crear_qr_socio(self.socio)
        self.assertTrue(len(qr_b64) > 100)
        self.assertIsInstance(qr_b64, str)

    def test_acceso_permitido_con_qr_vigente(self):
        payload, _ = generar_payload_qr(self.socio.id)
        permitido, mensaje, registro = validar_y_registrar_acceso(payload, puerta="Principal")

        self.assertTrue(permitido)
        self.assertIn("permitido", mensaje.lower())
        self.assertIsNotNone(registro)
        self.assertEqual(registro.resultado, RegistroAcceso.Resultado.PERMITIDO)
        self.assertEqual(registro.socio, self.socio)

    def test_acceso_denegado_por_qr_expirado(self):
        # QR generado hace 45 segundos (ventana es 30s)
        timestamp_antiguo = int(timezone.now().timestamp()) - 45
        payload, _ = generar_payload_qr(self.socio.id, timestamp=timestamp_antiguo)

        permitido, mensaje, registro = validar_y_registrar_acceso(payload)

        self.assertFalse(permitido)
        self.assertIn("expirado", mensaje.lower())
        self.assertEqual(registro.resultado, RegistroAcceso.Resultado.QR_EXPIRADO)

    def test_acceso_denegado_por_firma_invalida(self):
        timestamp = int(timezone.now().timestamp())
        payload_falsificado = f"{self.socio.id}|{timestamp}|firma_falsa_12345"

        permitido, mensaje, registro = validar_y_registrar_acceso(payload_falsificado)

        self.assertFalse(permitido)
        self.assertIn("firma", mensaje.lower())
        self.assertEqual(registro.resultado, RegistroAcceso.Resultado.FIRMA_INVALIDA)

    def test_acceso_denegado_por_membresia_vencida(self):
        # Marcar membresía como vencida con fechas válidas en el pasado
        self.membresia.fecha_inicio = self.hoy - timedelta(days=31)
        self.membresia.fecha_fin = self.hoy - timedelta(days=1)
        self.membresia.estado = Membresia.Estado.VENCIDA
        self.membresia.save()

        payload, _ = generar_payload_qr(self.socio.id)
        permitido, mensaje, registro = validar_y_registrar_acceso(payload)

        self.assertFalse(permitido)
        self.assertIn("membresía", mensaje.lower())
        self.assertEqual(registro.resultado, RegistroAcceso.Resultado.MEMBRESIA_VENCIDA)
