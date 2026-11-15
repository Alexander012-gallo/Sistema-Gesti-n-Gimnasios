from django.core.management.base import BaseCommand
from cuentas.roles import garantizar_roles_y_permisos


class Command(BaseCommand):
    help = "Inicializa los grupos de roles (Administrador, Recepción, Socio) y sus permisos base."

    def handle(self, *args, **options):
        grupos = garantizar_roles_y_permisos()
        self.stdout.write(
            self.style.SUCCESS(
                f"Roles inicializados correctamente: {', '.join(grupos.keys())}"
            )
        )
