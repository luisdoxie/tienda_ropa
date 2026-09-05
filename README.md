# FashionStore

Plataforma de e-commerce de ropa con probador virtual por realidad aumentada.
Proyecto académico de la materia Sistemas de Información II (UAGRM),
desarrollado con metodología PUDS y modelado UML 2.5.

FashionStore combina una tienda pública para clientes (catálogo, carrito,
checkout y reservas para probarse en sucursal), un back office administrativo
(gestión de productos, inventario, ventas, entregas, reportes) y una app móvil
con probador virtual de prendas mediante detección de pose y modo generativo
con IA.

## Tecnologías

**Backend**
- Python 3.13 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic
- PostgreSQL (Railway en producción, local en desarrollo)
- Autenticación con JWT (PyJWT) y hash de contraseñas con `bcrypt`
- Límite de tasa de peticiones con `slowapi`
- Imágenes en Cloudinary
- IA con Groq (búsqueda por voz y recomendador) y Vertex AI (probador generativo)
- Pagos con Libélula y PayPal (sandbox)

**Web** (back office + tienda pública)
- Angular 22 + PrimeNG

**Móvil** (cliente: catálogo, favoritos, carrito/checkout y probador AR)
- Flutter + Dart, Material 3
- Riverpod, go_router, Dio
- `google_mlkit_pose_detection` para el modo espejo del probador

**Despliegue**
- Backend y base de datos en Railway (sin Docker)
- Web en Vercel

## Estructura del repositorio

```
tienda_ropa/
├── backend/        API en FastAPI, monolito modular en capas
│   └── app/
│       ├── core/            utilidades compartidas, CRUD base, notificaciones
│       ├── seguridad/        usuarios, roles, permisos, autenticación
│       ├── organizacion/     ciudades, sucursales, horarios
│       ├── catalogo/         productos, variantes, categorías, tallas, colores
│       ├── abastecimiento/   proveedores
│       ├── inventario/       stock y movimientos por sucursal
│       ├── reservas/         reservas para probarse en tienda
│       ├── ventas/           ventas presenciales y digitales
│       ├── pagos/            pasarelas de pago (Libélula, PayPal)
│       ├── entregas/         zonas de envío y direcciones
│       └── probador/         probador virtual (espejo y generativo)
│   └── alembic/       migraciones de base de datos
│
├── web/             Angular — back office (admin/encargado/cajero) y tienda pública
│   └── src/app/
│       ├── core/            servicios, guards, interceptores, modelos
│       ├── layout/           layout del back office
│       └── features/         una carpeta por pantalla/módulo
│
├── mobile/          Flutter — app cliente con probador AR
│   └── lib/
│       ├── core/             red, router, tema
│       └── features/         auth, catalogo, compras, favoritos, probador, reservas, tracking
│
├── docs/            esquema de base de datos y plan de desarrollo
└── CLAUDE.md        reglas de arquitectura y convenciones del proyecto
```

Cada paquete del backend sigue siempre la misma estructura: `models.py`,
`schemas.py`, `repository.py`, `service.py` y `router.py`. Un paquete nunca
consulta directamente las tablas de otro: llama a su capa de servicio.

## Desarrolladores

| Rol        | Integrante                     |
|------------|---------------------------------|
| Full stack | Luis Miguel Aguayo Quiroz       |
| Full stack | Alexander Osinaga Blanco        |
