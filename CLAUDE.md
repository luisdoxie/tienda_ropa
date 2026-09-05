# FashionStore — Contexto del proyecto

Plataforma de e-commerce de ropa con vestidor virtual por realidad aumentada.
Proyecto académico, Sistemas II, UAGRM. Metodología PUDS, modelado UML 2.5.

## Stack
- Backend: Python 3.13 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic
- BD: PostgreSQL en Railway
- Web: Angular + PrimeNG (back office: admin, encargado, cajero; más una
  tienda pública para clientes: catálogo, registro/login, carrito y
  checkout — sin probador AR)
- Móvil: Flutter + Dart, Material 3 (cliente: catálogo, favoritos,
  carrito/checkout y el probador AR, exclusivo de esta app)
- Imágenes: Cloudinary
- IA: Groq (búsqueda por voz y recomendador)
- Probador: google_mlkit_pose_detection (modo espejo) + Vertex AI (generativo)
- Pagos: Libélula y PayPal, ambos en sandbox
- Despliegue: Railway sin Docker, y Vercel para el Angular

## Arquitectura
Monolito modular en capas. 13 paquetes de negocio bajo `backend/app/`:
core, seguridad, organizacion, catalogo, abastecimiento, inventario,
reservas, ventas, pagos, entregas, probador, inteligencia, reportes.

Cada paquete tiene exactamente estos archivos:
  models.py       modelos SQLAlchemy
  schemas.py      schemas Pydantic (Crear, Actualizar, Respuesta)
  repository.py   acceso a datos
  service.py      reglas de negocio
  router.py       endpoints FastAPI

## Reglas obligatorias
1. Sin dependencias circulares entre paquetes.
2. Un paquete NUNCA consulta las tablas de otro paquete. Llama al service
   del otro paquete. Ejemplo: ventas llama a
   inventario.service.registrar_movimiento(), no hace UPDATE sobre stock.
3. Todo CRUD hereda de core/crud_base.py. No repetir código CRUD.
4. Todo cambio de esquema va en una migración de Alembic. Nunca a mano.
5. El router no toca la base de datos. El service no sabe de HTTP.
6. Toda operación que afecte stock va dentro de una transacción.
7. Nombres en español, tablas en singular, snake_case.
8. Borrado lógico con el campo `activo`. Nunca DELETE físico en tablas de negocio.
9. Los secretos van en variables de entorno. Nunca en el código.
10. El hash de contraseñas usa la librería `bcrypt` directamente.
    NO usar `passlib`: está sin mantenimiento y rompe con las versiones
    actuales de bcrypt.
11. La versión de Python es 3.13, fijada con `.python-version` en la raíz
    del backend para que el entorno local y Railway coincidan.

## Esquema de base de datos
El esquema completo y definitivo está en `docs/fashionstore_esquema.sql`
(61 tablas). No inventar tablas ni columnas nuevas sin pedirlo explícitamente.
Ese archivo es documentación de referencia: NO se ejecuta contra la base.
Las tablas las crea Alembic a partir de los modelos.

## Plan de desarrollo
`docs/plan_desarrollo_fashionstore.md`

## Tokens de diseño
Paleta terracota oscurecida (tienda de hombre: menos crema/pastel, base más
piedra/carbón, acento tipo cuero curtido en vez de coral). Fondo #EAE4DA
(contenido) / #FFFFFF (superficie/cards) · Texto #1C1713 / tenue #6E6156 ·
Acento #9A3E1F (hover #732E16, suave #E3D2C1) ·
Sidebar #241C18 (texto #C9BCB2, activo rgba(154,62,31,.28) / #F0DDCE) ·
Éxito #16A34A (suave #E8F6EE) · Advertencia #B45309 (suave #FDF0DD) ·
Error #DC2626 · Borde #DBD0C1 · Muted #C7BCAC.
Radio: 6px (inputs/filas/densos) · 10px (cards/stat tiles) · 18px (diálogos/hero).
Tipografía: Fraunces (serif, 500/600/700, itálica para marca y saludos) +
Public Sans (400-700, UI y datos). Números alineados en columna usan
tabular-nums. Espaciado en múltiplos de 4px.
El back office es denso (tablas compactas). El cliente móvil es amplio,
con la fotografía como protagonista.

## Alcance del probador virtual
Solo prendas superiores masculinas (poleras, camisas, chamarras).
Modo espejo obligatorio en Flutter. Modo generativo opcional.

## Entorno local
- PostgreSQL instalado localmente. Base de desarrollo: `fashionstore_dev`,
  creada manualmente antes de la primera migración.
- pgAdmin se usa solo para consulta. Las tablas NUNCA se crean ni se
  modifican desde pgAdmin.
- Conexión por variable de entorno DATABASE_URL en `.env`:
  postgresql+psycopg://postgres:PASSWORD@localhost:5432/fashionstore_dev
- Producción: PostgreSQL en Railway, DATABASE_URL provista por el servicio.

## Flujo de cambios de esquema
1. Modificar el modelo SQLAlchemy.
2. alembic revision --autogenerate -m "descripcion"
3. Revisar a mano el archivo generado. Atención con la columna generada
   `stock.cantidad_disponible`: autogenerate suele proponerla mal.
4. alembic upgrade head en local.
5. Commit y push. Railway aplica la migración al desplegar.