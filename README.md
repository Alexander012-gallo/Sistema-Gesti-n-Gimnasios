# Sistema-Gestion-Gimnasios
# Sistema de Gestión de Gimnasios

Aplicación web desarrollada con **Python y Django**, orientada a la administración y control de las operaciones de un gimnasio. El sistema centraliza la gestión de socios, planes, membresías, pagos y accesos, incorporando mecanismos de autenticación, autorización y validación mediante códigos QR dinámicos.

## Características principales

- **Gestión de socios:** registro y administración de información personal, fotografías y datos de contacto.
- **Gestión de planes:** administración de planes y sus respectivas condiciones.
- **Membresías:** asignación, seguimiento y renovación de membresías.
- **Control de pagos:** registro de transacciones y generación de comprobantes.
- **Carnet digital:** generación de carnets de identificación con códigos QR dinámicos.
- **Control de accesos:** validación de códigos QR mediante firmas HMAC-SHA256, con una vigencia de 30 segundos.
- **Historial de accesos:** registro y consulta de los intentos de validación.
- **Gestión de usuarios:** administración de permisos mediante control de acceso basado en roles (RBAC).
- **Panel administrativo:** visualización de información y métricas relacionadas con las operaciones del gimnasio.

## Roles del sistema

| Rol | Descripción |
|---|---|
| Administrador | Gestiona socios, planes, membresías, pagos, accesos y métricas del gimnasio. |
| Recepción | Registra socios, administra membresías, registra pagos y valida accesos. |
| Socio | Consulta su perfil, membresía, pagos, historial y carnet digital. |

## Tecnologías utilizadas

| Tecnología | Descripción |
|---|---|
| Python 3.12 | Lenguaje de programación. |
| Django 5.2 | Framework para el desarrollo backend. |
| MySQL 8 | Sistema de gestión de bases de datos. |
| PyMySQL | Conector para la comunicación con MySQL. |
| Pillow | Procesamiento y gestión de imágenes. |
| qrcode | Generación de códigos QR. |
| python-dotenv | Gestión de variables de entorno. |
| Bootstrap 5.3 | Framework para el diseño de interfaces. |
| Bootstrap Icons | Biblioteca de iconos. |

## Estructura del proyecto

```text
gymproject/
│
├── accesos/             # Generación y validación de códigos QR
├── cuentas/             # Gestión de usuarios, socios y roles
├── membresias/          # Gestión de planes, membresías y pagos
├── panel/               # Panel principal y carnets digitales
│
├── gymproject/          # Configuración principal del proyecto Django
│
├── templates/           # Plantillas HTML
├── static/              # Recursos estáticos
├── media/               # Archivos multimedia
│
├── manage.py            # Punto de entrada de Django
└── requirements.txt     # Dependencias del proyecto
```

## Funcionamiento del código QR dinámico

El sistema incorpora un mecanismo de identificación y validación de socios mediante códigos QR dinámicos.

Cada código contiene tres componentes:

```text
socio_id | timestamp | firma_hmac
```

La firma se genera mediante el algoritmo criptográfico HMAC-SHA256, utilizando la clave secreta de Django. Cada código tiene una vigencia de 30 segundos, lo que permite validar su autenticidad y controlar el acceso de los socios.

Los intentos de validación quedan registrados para mantener un historial de auditoría.

## Autor

**Alexander Gallo**

Universidad Nacional de Loja — Ecuador.
