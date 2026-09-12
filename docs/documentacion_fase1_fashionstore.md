# FashionStore — Documentación de Fase 1

**Materia:** Sistemas II | **Docente:** MSc. Ing. Angélica Garzón Cuéllar
**Metodología:** Proceso Unificado de Desarrollo de Software (PUDS) — modelado UML 2.5
**Entrega:** Presentación 1 — sábado 05/09/2026, 23:59
**Alcance de este documento:** Perfil · Parte I (fundamentación teórica) · F.T.1 Requisitos · F.T.2 Análisis · F.T.3 Diseño (hasta 3.3 Diseño de Datos)
**Fuente de verdad técnica:** `documentos/FashionStore_Consolidado.docx` y `docs/fashionstore_esquema.sql`

---

## 1. Perfil

### 1.1 Introducción

Comprar ropa por internet resuelve el problema de la disponibilidad, pero no resuelve el problema de la talla ni el de verse bien con la prenda puesta: esa incertidumbre es la causa principal de devoluciones e indecisión de compra en el comercio electrónico de moda. Al mismo tiempo, una tienda de ropa con varias sucursales físicas enfrenta un problema distinto: su inventario está fragmentado por local, y sin visibilidad centralizada no puede prometerle a un cliente que una prenda específica, en una talla y color específicos, está disponible para probar hoy mismo en la sucursal más cercana.

FashionStore es una plataforma de comercio electrónico multi-sucursal para una tienda de ropa, con dos canales de cliente (aplicación móvil Flutter y sitio web Angular) y un mismo backend en FastAPI que centraliza catálogo, inventario, reservas, ventas, pagos y entregas. Su característica distintiva es el **vestidor virtual por realidad aumentada**: el cliente ve la prenda superpuesta sobre su propio cuerpo, en tiempo real, usando la cámara del teléfono, antes de decidir si la reserva para probársela físicamente en una sucursal o la compra directamente. El alcance del vestidor está acotado, por autorización expresa de la docente, a prendas superiores masculinas (poleras, camisetas, camisas y chamarras); el resto del catálogo se navega, reserva y compra con normalidad, sin probador.

El proyecto se desarrolla como examen de la materia Sistemas II, bajo el Proceso Unificado de Desarrollo de Software (PUDS) y modelado UML 2.5, en un cronograma de cuatro semanas (25/08 al 22/09/2026) con tres entregas parciales documentales y una defensa final. Este documento corresponde a la primera entrega: perfil del proyecto, fundamentación teórica y el primer tercio del proceso PUDS (Requisitos, Análisis y Diseño hasta el diseño de datos).

### 1.2 Objetivo General

Desarrollar e implementar FashionStore, una plataforma de comercio electrónico multi-sucursal para la venta de ropa, que integre un vestidor virtual por realidad aumentada, gestión de inventario centralizada entre sucursales, reserva de prendas previa a la compra, venta digital y presencial con pasarelas de pago en sandbox, y funcionalidades de inteligencia artificial para búsqueda y recomendación, aplicando el Proceso Unificado de Desarrollo de Software y modelado UML 2.5 de principio a fin.

### 1.3 Objetivos Específicos

1. Diseñar e implementar un modelo de datos relacional de 61 tablas sobre PostgreSQL que soporte catálogo por variante (talla-color), inventario por sucursal con trazabilidad de movimientos, reservas, ventas omnicanal, pagos y entregas, respetando las ocho decisiones de diseño documentadas en el consolidado técnico.
2. Construir un backend monolito modular en FastAPI, organizado en 13 paquetes de negocio con dependencias unidireccionales y sin acoplamiento directo a las tablas de otros paquetes, exponiendo una única API REST consumida por ambos clientes.
3. Implementar el módulo de catálogo con soporte de variantes talla-color, atributos (categoría, talla, color, material, temporada) e imágenes gestionadas en Cloudinary, acotado a prendas superiores masculinas para el vestidor virtual.
4. Implementar el flujo de reserva multi-prenda de punta a punta: el cliente reserva, la sucursal prepara y atiende, y las prendas no seleccionadas se liberan de vuelta al stock disponible.
5. Implementar el vestidor virtual en modo espejo sobre la aplicación móvil, usando detección de pose on-device (`google_mlkit_pose_detection`) y overlays 2D anclados por coordenadas normalizadas, integrado dinámicamente con el catálogo.
6. Implementar la venta digital (carrito, checkout, pasarela) y la venta presencial (punto de caja con múltiples medios de cobro), registradas sobre una única entidad de venta diferenciada por canal, con actualización transaccional de inventario.
7. Integrar pasarelas de pago en modo sandbox (Libélula para el mercado nacional, PayPal para el internacional) con confirmación de transacción y trazabilidad de estado.
8. Implementar búsqueda por catálogo mediante comando de voz y un recomendador de prendas basado en historial de navegación y compra, usando un proveedor de inteligencia artificial (Groq).
9. Desplegar la plataforma completa en la nube (Railway para API y base de datos, Vercel para el frontend Angular), sin recurrir a `localhost` en ninguna etapa de evaluación.

### 1.4 Descripción del problema

Una tienda de ropa que opera con varias sucursales físicas necesita expandir su canal de venta hacia el comercio electrónico sin renunciar a la experiencia de sucursal, y enfrenta simultáneamente tres problemas que el mercado actual no resuelve de forma conjunta:

- **Incertidumbre de talla y ajuste.** El cliente que compra ropa en línea no puede verificar cómo le queda la prenda antes de recibirla, lo que deriva en devoluciones, cambios y abandono de carrito. Las soluciones de "probador virtual" comerciales existentes (SDKs de realidad aumentada de terceros) están pensadas para catálogos genéricos, no se integran de forma dinámica con un catálogo propio que cambia constantemente, y su costo o licenciamiento es incompatible con un proyecto de cuatro semanas.
- **Inventario fragmentado entre sucursales.** Sin una fuente única de verdad sobre existencias, el sistema no puede indicarle a un cliente en qué sucursal hay disponible, físicamente, la variante talla-color que quiere probarse, ni puede sostener una reserva sin arriesgarse a vender el mismo artículo dos veces.
- **Canales de venta desconectados.** Tratar la venta presencial (caja) y la venta digital (carrito y pasarela) como sistemas separados duplica reglas de negocio, duplica reportes y hace imposible una vista consolidada de ingresos e inventario por canal.

El enunciado oficial del examen exige, además, resolver estos problemas sin apoyarse en plataformas de comercio electrónico preexistentes (queda expresamente prohibido el uso de PrestaShop, Shopify, Magento, WooCommerce o similares) y con despliegue obligatorio en la nube, lo que descarta cualquier atajo de integración y obliga a construir el dominio de negocio — catálogo, inventario, reservas, ventas, pagos, entregas y probador — desde cero, con una arquitectura propia.

### 1.5 Alcance

**Incluido en el proyecto (MVP y prioridad 2 documentados en este ciclo):**
- Gestión de catálogo por variante talla-color (categorías, tallas, colores, materiales, temporadas, imágenes), acotada para efectos del vestidor virtual a prendas superiores masculinas: poleras, camisetas, camisas y chamarras. El resto del catálogo es navegable, reservable y comprable, pero no cuenta con probador.
- Gestión de sucursales, ciudades, empleados y roles con permisos.
- Inventario por sucursal con movimientos trazables, valuación por promedio ponderado y stock disponible calculado automáticamente.
- Reserva de múltiples prendas por sucursal y horario, con atención presencial y liberación de las prendas no seleccionadas.
- Vestidor virtual en modo espejo (obligatorio, tiempo real, on-device) sobre la aplicación móvil; el modo generativo por IA se documenta como extensión opcional.
- Venta digital (carrito, checkout con pasarela) y venta presencial (punto de caja con efectivo, QR, tarjeta y transferencia), sobre una única entidad de venta diferenciada por canal.
- Pagos mediante pasarela en modo sandbox (Libélula y PayPal) con confirmación de transacción.
- Gestión de zonas de entrega por anillo y tarifas, como base para el cálculo de envío a domicilio.
- Búsqueda por comando de voz y recomendación de prendas mediante inteligencia artificial (Groq), con registro de historial de navegación como insumo.
- Reportes de ventas e inventario para administración.
- Despliegue completo en la nube: Railway (API + PostgreSQL) y Vercel (Angular).

**Explícitamente fuera del alcance de este ciclo de documentación** (quedan definidos en el catálogo completo de 79 CU del consolidado técnico para retomarse en fases posteriores si el cronograma lo permite): recuperación de contraseña, favoritos, gestión de colecciones y tabla de medidas por talla, órdenes de compra formales a proveedor, transferencias y ajustes manuales de inventario entre sucursales, expiración automática de reservas, vestidor generativo por IA y recomendación automática de talla, historial de compras y ventas por sucursal para el cliente/encargado, devoluciones y cambios, promociones, anulación/reembolso de pagos, programación y seguimiento de entrega a domicilio, asistente conversacional (chatbot) y reporte por comando de voz, dashboard de indicadores.

**Restricción de plataforma:** prohibido el uso de frameworks de comercio electrónico preexistentes (PrestaShop, Shopify, Magento, WooCommerce y similares); toda la lógica de negocio se construye a medida sobre el stack exigido por el enunciado.

---

## Parte I — Fundamentación teórica

### a) Comercio electrónico (e-commerce)

El comercio electrónico es la compraventa de bienes o servicios a través de medios electrónicos, típicamente internet, donde la transacción reemplaza o complementa la interacción física entre comprador y vendedor. En el modelo B2C (business-to-consumer), que es el que aplica a FashionStore, una empresa vende directamente al consumidor final a través de un canal digital propio.

Como referencia de plataformas consolidadas que un usuario final utiliza para comprar (no para desarrollar), destacan Amazon, Alibaba y Shopify: la primera por su modelo de marketplace con logística propia (fulfillment), la segunda por su escala en comercio B2B y B2C combinados, y la tercera porque, aunque es también una plataforma de desarrollo, para una tienda pequeña se consume como servicio ya armado (catálogo, carrito, checkout y pasarela integrados sin escribir código de backend).

Desde el punto de vista del desarrollador, existen frameworks especializados en construir tiendas en línea sobre un CMS o motor de e-commerce ya existente: **Magento** (orientado a catálogos grandes y multi-tienda, con curva de aprendizaje alta), **PrestaShop** (más liviano, popular en Latinoamérica y España) y **WooCommerce** (plugin de e-commerce sobre WordPress, el de adopción más simple). Estas herramientas resuelven en semanas lo que a medida toma meses, pero a cambio imponen su propio modelo de datos, su propio ciclo de despliegue y, en la mayoría de los casos, licenciamiento o extensiones de pago para funcionalidad avanzada (multi-sucursal real, reservas, integración con hardware de punto de venta).

El enunciado del examen prohíbe expresamente el uso de estas plataformas. La razón práctica coincide con la académica: ninguna de ellas modela de forma nativa el concepto de "reserva de prenda para probar en sucursal antes de comprar", ni permite insertar un vestidor virtual que lea directamente los anclajes y assets de cada variante del catálogo propio, ni deja controlar con precisión cómo se calcula el promedio ponderado de costos por movimiento de inventario. FashionStore construye su propio backend (FastAPI + SQLAlchemy + PostgreSQL) precisamente para tener control total sobre estas reglas de negocio, que son el núcleo del proyecto y no un caso genérico de "vender productos por internet".

### b) Pasarelas de pago

Una pasarela de pago es el servicio intermediario que autoriza, procesa y confirma una transacción electrónica entre el comprador, el comercio y las entidades financieras (bancos, emisores de tarjeta), sin que el comercio necesite manejar directamente los datos sensibles de la tarjeta o cuenta del cliente. Los medios de pago habituales que una pasarela puede intermediar son: tarjeta de débito, tarjeta de crédito, código QR interoperable y transferencia bancaria directa.

FashionStore integra dos pasarelas, ambas en modo sandbox (entorno de pruebas sin movimiento de dinero real): **Libélula**, como pasarela boliviana orientada al mercado nacional, y **PayPal**, como pasarela internacional de referencia (con Stripe como alternativa equivalente mencionada en el enunciado). El cobro presencial en punto de caja no depende de una pasarela externa: se registra directamente en el sistema, admitiendo efectivo, QR, tarjeta y transferencia como medios, según la aclaración de la docente en las sesiones de audio.

El ciclo de vida de una transacción de pasarela en este proyecto sigue tres pasos: (1) el cliente inicia el pago desde el checkout o la caja, (2) el sistema de pagos externo (Libélula o PayPal) procesa la transacción y responde de forma asíncrona o síncrona con un estado, y (3) FashionStore confirma o rechaza la venta según ese estado, sin descontar inventario ni cerrar la venta hasta tener confirmación. Esta secuencia es la base de los casos de uso CU-62 (pagar mediante pasarela digital), CU-63 (procesar pago en caja) y CU-64 (confirmar o rechazar transacción, iniciado por el actor externo "Sistema de pagos").

### c) Deliverys (entrega a domicilio)

Un servicio de delivery resuelve el tramo final de la cadena de comercio electrónico: llevar el producto físico desde el punto de despacho (en este caso, una sucursal) hasta el domicilio del cliente. Plataformas regionales como Yaigo o Yummy popularizaron un modelo de cálculo de tarifa basado en distancia, tiempo estimado y, en algunos casos, peso o volumen del pedido, normalmente segmentado en zonas o anillos concéntricos alrededor del punto de despacho: cuanto más lejos el destino, mayor la tarifa.

FashionStore adopta ese mismo modelo de **zonas por anillo**: cada sucursal define zonas de cobertura (anillos) con una tarifa asociada, y el costo de envío de un pedido se calcula según la zona de la dirección de destino del cliente. Este modelo es intencionalmente más simple que un cálculo de ruteo real (no considera tráfico ni ruta óptima), lo cual es correcto para el alcance del proyecto: la entrega a domicilio es una funcionalidad de prioridad 2, no el diferenciador central del sistema. Corresponde a los casos de uso CU-67 (gestionar zonas por anillo y tarifas) y, como comportamiento incluido en el checkout, al cálculo de costo de envío.

### d) Proceso Unificado de Desarrollo de Software (PUDS)

El PUDS es una metodología de desarrollo de software iterativa e incremental, dirigida por casos de uso, centrada en la arquitectura y basada en la gestión de riesgos. A diferencia de un proceso en cascada, el PUDS no exige terminar por completo el análisis antes de empezar el diseño: cada iteración atraviesa varios flujos de trabajo (workflows) en menor o mayor profundidad, y el sistema crece por incrementos verificables.

Los flujos de trabajo fundamentales del PUDS, y que estructuran la numeración exigida por la docente para este examen, son:

1. **Captura de Requisitos** — identificar actores y casos de uso, priorizarlos, detallarlos (flujo básico, alternativo, pre/postcondiciones) y prototipar la interfaz de usuario.
2. **Análisis** — traducir cada caso de uso a un conjunto de clases de análisis estereotipadas (entidad, control, frontera), sin todavía decidir detalles de implementación, y verificar que el particionado en paquetes mantenga bajo acoplamiento y alta cohesión.
3. **Diseño** — definir la arquitectura lógica (paquetes, capas) y física (nodos de despliegue), diseñar el comportamiento interno de cada caso de uso (secuencia, estados, navegación) y diseñar el modelo de datos persistente.
4. **Implementación** — construir el sistema siguiendo la arquitectura definida, organizado por subsistemas/paquetes.
5. **Pruebas** — verificar cada caso de uso mediante su flujo normal y al menos un flujo alternativo, especialmente en los casos críticos del sistema.

Este examen distribuye esos cinco flujos de trabajo en tres entregas y una defensa: la Presentación 1 (este documento) cubre el Perfil, la Parte I teórica y los flujos 1 a 3 hasta el punto de Diseño de Datos; la Presentación 2 profundiza el resto del Diseño (clases, secuencia, estados, componentes, despliegue, API y seguridad); la Presentación final cubre Implementación y Pruebas; la Defensa no agrega contenido nuevo, sino que valida lo entregado.

### e) UML (Lenguaje Unificado de Modelado)

UML 2.5 es el lenguaje de modelado gráfico estándar usado por el PUDS para representar cada flujo de trabajo con un tipo de diagrama apropiado. Este proyecto usa dos familias de diagramas:

**Diagramas estructurales** (qué existe): diagrama de casos de uso (actores y sus metas), diagrama de clases (de análisis y de diseño, incluido el modelo de datos), diagrama de paquetes (organización de los 13 paquetes de negocio y sus dependencias), diagrama de componentes y diagrama de despliegue (nodos físicos: Railway, Vercel, PostgreSQL, servicios externos).

**Diagramas de comportamiento** (qué ocurre): diagrama de casos de uso con relaciones `«include»` y `«extend»`, diagrama de comunicación/colaboración (análisis de robustez), diagrama de secuencia (interacción temporal entre objetos para un caso de uso), diagrama de estados (ciclo de vida de una reserva, una venta o un pago) y diagrama de navegación (flujo entre pantallas de la aplicación).

Dos convenciones de estereotipo se aplican de forma consistente en todo el modelo, siguiendo la guía de la docente: una relación `«include»` se ata siempre a una **precondición** (el comportamiento incluido se ejecuta siempre, sin excepción, como parte del caso de uso base); una relación `«extend»` se ata a una **postcondición condicional** (el comportamiento extendido solo ocurre si se cumple una condición particular). Esta distinción es la que se usó en el paso previo de depuración del catálogo de casos de uso, para decidir qué comportamientos de "actor Sistema" debían modelarse como relaciones y no como casos de uso independientes.

Todos los diagramas de este documento se construyen en Enterprise Architect y se referencian desde el texto explicativo correspondiente a cada flujo de trabajo.

---

## F.T.1 — Captura de Requisitos

### 1.1 Identificar casos de uso y actores

El sistema reconoce siete actores, tal como los fija el enunciado oficial del examen. Cinco son actores primarios humanos que inician interacciones desde uno de los dos clientes (móvil o web); dos son actores secundarios de software, sistemas externos que el proyecto consume y que también pueden iniciar una interacción (por ejemplo, una pasarela de pago que notifica el resultado de una transacción).

| Actor | Tipo | Rol en el sistema | Canal |
|---|---|---|---|
| Cliente | Primario, humano | Se registra, navega el catálogo, reserva prendas, se prueba ropa en el vestidor virtual, compra en línea y paga | App móvil (principal) y web |
| Administrador | Primario, humano | Configura catálogo base, sucursales, usuarios y roles; supervisa inventario consolidado, ventas y reportes | Back office web |
| Encargado | Primario, humano | Opera una sucursal: recibe mercadería, registra movimientos de inventario, atiende reservas | Back office web |
| Cajero | Primario, humano | Registra ventas presenciales y procesa el cobro en el punto de caja de una sucursal | Back office web |
| Proveedor | Primario, humano | Suministra mercadería a la tienda; en el enunciado puede registrar información de sus propios productos | *(sin CU propio activo en esta fase — ver nota)* |
| Sistema de pagos | Secundario, externo | Pasarela de pago (Libélula o PayPal) que procesa y confirma o rechaza una transacción | API externa |
| Servicio de IA | Secundario, externo | Proveedor de inteligencia artificial (Groq) que interpreta comandos de voz y genera recomendaciones | API externa |

**Nota sobre el actor Proveedor.** El enunciado le reconoce como actor con casos de uso propios (registrar información de sus productos, asociarlos a temporada/colección). Ambos son de prioridad 2 y, siguiendo el criterio de depuración de la sección siguiente, quedan fuera del alcance documentado en esta fase: por ahora el proveedor existe como entidad de datos administrada por el Administrador (CU-25), sin iniciar sesión ni interactuar directamente con el sistema. Se retoma en una fase posterior si el cronograma lo permite.

### 1.2 Priorización de casos de uso

El consolidado técnico de origen documenta 79 casos de uso (34 comprometidos como MVP, 21 de prioridad 2, 15 de prioridad 3, más CU-38 sin ser un caso de uso independiente). Antes de detallar cada uno, se depuró ese catálogo aplicando dos criterios de calidad de modelado, además del criterio de cobertura mínima exigido para esta entrega (mínimo 30 casos de uso bien trabajados, priorizando MVP):

**Criterio 1 — Un actor "Sistema" genérico no es un actor válido.** En UML/PUDS, un caso de uso lo inicia un actor externo al sistema (una persona o un sistema externo real). Seis casos de uso del catálogo original tenían como actor la palabra genérica "Sistema", lo cual es síntoma de que en realidad son un paso interno de otro caso de uso, no una meta iniciada por alguien externo. Se remodelaron como relaciones `«include»` (si el comportamiento ocurre siempre) o `«extend»` (si ocurre solo bajo una condición), según la precondición/postcondición de cada uno:

| CU original | Actor original | Se reclasifica como | Relación | CU(s) base |
|---|---|---|---|---|
| CU-38 Actualizar inventario tras operación | Sistema | Comportamiento incluido transversal | `«include»` (siempre ocurre al cerrar la operación) | CU-29, CU-39, CU-41, CU-44/45/46 (fusionado), CU-54, CU-55 |
| CU-42 Notificar reserva a la sucursal | Sistema | Comportamiento incluido | `«include»` (ocurre siempre que una reserva se confirma) | CU-39 |
| CU-73 Registrar historial de navegación | Sistema | Comportamiento incluido | `«include»` (ocurre siempre que el cliente navega el catálogo) | CU-21, CU-22, CU-23 |
| CU-47 Expirar reservas vencidas | Sistema | Comportamiento extendido | `«extend»` (condición: se venció el plazo sin confirmación) | CU-39 |
| CU-61 Aplicar promoción al carrito | Sistema | Comportamiento extendido | `«extend»` (condición: existe una promoción vigente aplicable) | CU-53 |
| CU-68 Calcular costo de envío | Sistema | Comportamiento extendido | `«extend»` (condición: el cliente elige entrega a domicilio) | CU-39, CU-54 |

**Criterio 2 — Un caso de uso es una meta de un actor, no un paso técnico aislado.** Tres casos de uso de reservas (CU-44 Preparar prendas reservadas, CU-45 Confirmar recepción del cliente, CU-46 Liberar prendas no seleccionadas) describían pasos secuenciales de una misma sesión de atención del Encargado en mostrador. Se fusionaron en un único caso de uso, **"Atender prueba de reserva en sucursal"**, con un flujo alternativo para cubrir la liberación de prendas no compradas. De forma similar, CU-56 Emitir comprobante se conserva como caso de uso propio, pero se modela como comportamiento **incluido compartido**, invocado tanto por CU-54 (compra digital) como por CU-55 (venta presencial), en vez de aparecer como una meta independiente del Cajero.

**Resultado.** El catálogo depurado tiene **42 casos de uso de primer nivel** (todos menos uno de prioridad MVP; CU-67 se promovió desde prioridad 2 porque su backend ya está implementado y el checkout con entrega a domicilio no queda completo sin él) más **6 comportamientos transversales** `«include»`/`«extend»` documentados dentro de sus casos base. Ningún caso de uso MVP legítimo fue descartado por completo: los seis "actor Sistema" y los tres fusionados conservan toda su lógica de negocio, solo que correctamente modelada como relación en vez de como caso de uso aislado.

| # | Código | Caso de uso | Actor | Prior. | Paquete |
|---|---|---|---|---|---|
| 1 | CU-01 | Registrar cliente | Cliente | MVP | Seguridad |
| 2 | CU-02 | Iniciar sesión | Todos | MVP | Seguridad |
| 3 | CU-03 | Gestionar usuarios y roles | Administrador | MVP | Seguridad |
| 4 | CU-04 | Gestionar permisos por rol | Administrador | MVP | Seguridad |
| 5 | CU-07 | Gestionar ciudades | Administrador | MVP | Organización |
| 6 | CU-08 | Gestionar sucursales | Administrador | MVP | Organización |
| 7 | CU-09 | Gestionar empleados y asignarlos a sucursal | Administrador | MVP | Organización |
| 8 | CU-11 | Gestionar categorías | Administrador | MVP | Catálogo |
| 9 | CU-12 | Gestionar tallas | Administrador | MVP | Catálogo |
| 10 | CU-13 | Gestionar colores | Administrador | MVP | Catálogo |
| 11 | CU-14 | Gestionar materiales | Administrador | MVP | Catálogo |
| 12 | CU-15 | Gestionar temporadas | Administrador | MVP | Catálogo |
| 13 | CU-17 | Gestionar productos | Administrador | MVP | Catálogo |
| 14 | CU-18 | Gestionar variantes talla-color | Administrador | MVP | Catálogo |
| 15 | CU-20 | Cargar imágenes del producto | Administrador | MVP | Catálogo |
| 16 | CU-21 | Consultar catálogo | Cliente | MVP | Catálogo |
| 17 | CU-22 | Buscar y filtrar prendas | Cliente | MVP | Catálogo |
| 18 | CU-23 | Consultar detalle de prenda | Cliente | MVP | Catálogo |
| 19 | CU-25 | Gestionar proveedores | Administrador | MVP | Abastecimiento |
| 20 | CU-29 | Registrar recepción de mercadería | Encargado | MVP | Abastecimiento |
| 21 | CU-30 | Consultar disponibilidad por sucursal | Cliente | MVP | Inventario |
| 22 | CU-31 | Consultar inventario consolidado global | Administrador | MVP | Inventario |
| 23 | CU-32 | Registrar movimiento de inventario | Encargado | MVP | Inventario |
| 24 | CU-39 | Reservar varias prendas indicando sucursal y horario | Cliente | MVP | Reservas |
| 25 | CU-40 | Consultar estado de reserva | Cliente | MVP | Reservas |
| 26 | CU-41 | Cancelar reserva | Cliente | MVP | Reservas |
| 27 | CU-43 | Consultar reservas de la sucursal | Encargado | MVP | Reservas |
| 28 | CU-44+ | Atender prueba de reserva en sucursal *(fusión de CU-44/45/46)* | Encargado | MVP | Reservas |
| 29 | CU-48 | Cargar assets y marcar anclajes | Administrador | MVP | Probador |
| 30 | CU-49 | Probar prenda en modo espejo | Cliente | MVP | Probador |
| 31 | CU-53 | Gestionar carrito | Cliente | MVP | Ventas |
| 32 | CU-54 | Realizar compra digital | Cliente | MVP | Ventas |
| 33 | CU-55 | Registrar venta presencial | Cajero | MVP | Ventas |
| 34 | CU-56 | Emitir comprobante *(incluido compartido)* | Cajero | MVP | Ventas |
| 35 | CU-62 | Pagar mediante pasarela digital | Cliente | MVP | Pagos |
| 36 | CU-63 | Procesar pago en caja | Cajero | MVP | Pagos |
| 37 | CU-64 | Confirmar o rechazar transacción | Sistema de pagos | MVP | Pagos |
| 38 | CU-67 | Gestionar zonas por anillo y tarifas | Administrador | 2 → base | Entregas |
| 39 | CU-71 | Recomendar prendas al cliente | Servicio de IA | MVP | Inteligencia |
| 40 | CU-72 | Buscar mediante comando de voz | Cliente | MVP | Inteligencia |
| 41 | CU-76 | Consultar reporte de ventas | Administrador | MVP | Reportes |
| 42 | CU-77 | Consultar reporte de inventario | Administrador | MVP | Reportes |

### 1.3 Detallar casos de uso

#### Diagrama de casos de uso

El diagrama de casos de uso general se construye en Enterprise Architect con un paquete por área de negocio (los mismos 12 paquetes de negocio del backend, excluyendo `core`), cada uno con sus casos de uso de primer nivel según la tabla anterior, más los seis comportamientos transversales de la sección 1.2 dibujados como elipses satélite unidas por relaciones `«include»`/`«extend»` a su(s) caso(s) base. Los siete actores se ubican en los bordes del diagrama, conectados por asociación a los casos de uso que inician.

#### Comportamientos transversales `«include»` / `«extend»`

| Nombre | Tipo | Disparado por | Condición | Efecto |
|---|---|---|---|---|
| Actualizar inventario tras operación | `«include»` | CU-29, CU-39, CU-41, CU-44+, CU-54, CU-55 | Siempre, al confirmarse la operación | Genera un `movimiento_inventario`, recalcula `cantidad_disponible` y, si aplica, el costo promedio ponderado |
| Notificar reserva a la sucursal | `«include»` | CU-39 | Siempre, al confirmarse la reserva | Crea una `notificacion` visible para el Encargado de la sucursal reservada |
| Registrar historial de navegación | `«include»` | CU-21, CU-22, CU-23 | Siempre que el Cliente esté autenticado | Inserta un registro en `historial_navegacion`, insumo de CU-71 |
| Expirar reservas vencidas | `«extend»` | CU-39 (ciclo de vida de la reserva) | El plazo de atención se venció sin confirmación del cliente | Cambia el estado de la reserva a "expirada" y libera la cantidad reservada |
| Aplicar promoción al carrito | `«extend»` | CU-53 | Existe una promoción vigente aplicable a algún ítem del carrito | Recalcula el subtotal del carrito con el descuento aplicado |
| Calcular costo de envío | `«extend»` | CU-39, CU-54 | El cliente elige entrega a domicilio en vez de retiro en sucursal | Determina la zona por anillo de la dirección y añade la tarifa correspondiente |

#### Fichas de detalle por caso de uso

*(Convenciones: **Pre** = precondición · **Post** = postcondición · **FB** = flujo básico · **FA** = flujo alternativo. Las tablas siguientes agrupan los 42 casos de uso por paquete, en el mismo orden del diagrama.)*

---

##### Paquete Seguridad

**CU-01 — Registrar cliente** · Cliente · MVP
- **Pre:** el visitante no tiene una cuenta activa en el sistema.
- **FB:** 1) El cliente abre el formulario de registro (app móvil o web). 2) Ingresa nombre, correo, teléfono y contraseña. 3) El sistema valida que el correo no esté registrado. 4) El sistema calcula el hash de la contraseña con `bcrypt`. 5) El sistema crea el usuario y el registro de cliente asociado, con rol "cliente" por defecto. 6) El sistema inicia sesión automáticamente y devuelve un token JWT.
- **FA:** A1 — correo ya registrado: el sistema rechaza el registro y sugiere iniciar sesión o recuperar la contraseña.
- **Post:** existen un usuario y un cliente activos, con sesión iniciada.
- **Relaciones:** ninguna.

**CU-02 — Iniciar sesión** · Todos los actores humanos · MVP
- **Pre:** el actor tiene una cuenta activa.
- **FB:** 1) El actor ingresa correo/usuario y contraseña. 2) El sistema verifica el hash con `bcrypt`. 3) El sistema verifica que el usuario esté activo. 4) El sistema determina el/los rol(es) y sus permisos. 5) El sistema emite un token JWT con rol y expiración.
- **FA:** A1 — credenciales inválidas: rechazo con mensaje genérico. A2 — usuario inactivo: rechazo indicando cuenta deshabilitada.
- **Post:** el actor tiene una sesión autenticada vigente.
- **Relaciones:** ninguna — es habilitante de casi todos los demás CU, pero no se modela como `«include»` porque no es un paso interno de otro caso de uso.

**CU-03 — Gestionar usuarios y roles** · Administrador · MVP
- **Pre:** el administrador tiene sesión con permiso de gestión de usuarios.
- **FB:** 1) Consulta el listado de usuarios. 2) Crea, edita o desactiva un usuario. 3) Asigna uno o más roles. 4) El sistema guarda el cambio y registra auditoría (`creado_por`, `creado_en`).
- **FA:** A1 — se intenta desactivar al último administrador activo: el sistema rechaza la operación.
- **Post:** el usuario queda creado/editado/desactivado con sus roles actualizados.
- **Relaciones:** ninguna.

**CU-04 — Gestionar permisos por rol** · Administrador · MVP
- **Pre:** existen roles definidos.
- **FB:** 1) Selecciona un rol. 2) Consulta el catálogo de permisos disponibles. 3) Marca o desmarca permisos para ese rol. 4) El sistema guarda la combinación en `rol_permiso`.
- **FA:** A1 — rol protegido (ej. "administrador"): el sistema impide remover el permiso base de gestión de usuarios.
- **Post:** el rol queda con su conjunto de permisos actualizado, vigente desde la próxima emisión de token.
- **Relaciones:** ninguna.

##### Paquete Organización

**CU-07 — Gestionar ciudades** · Administrador · MVP
- **Pre:** sesión de administrador.
- **FB:** 1) Consulta el listado de ciudades. 2) Crea o edita una ciudad (nombre, país). 3) El sistema guarda el cambio.
- **FA:** A1 — la ciudad tiene sucursales activas y se intenta desactivar: el sistema exige desactivar primero las sucursales.
- **Post:** catálogo de ciudades actualizado.
- **Relaciones:** ninguna.

**CU-08 — Gestionar sucursales** · Administrador · MVP
- **Pre:** existe al menos una ciudad registrada.
- **FB:** 1) Consulta el listado de sucursales. 2) Crea o edita una sucursal (nombre, dirección, ciudad). 3) El sistema guarda el cambio.
- **FA:** A1 — dirección incompleta: el sistema rechaza hasta completar los campos obligatorios.
- **Post:** catálogo de sucursales actualizado; la sucursal queda disponible para inventario, empleados y reservas.
- **Relaciones:** ninguna.

**CU-09 — Gestionar empleados y asignarlos a sucursal** · Administrador · MVP
- **Pre:** existen la sucursal destino y el usuario del empleado.
- **FB:** 1) Consulta el listado de empleados. 2) Crea o edita un empleado, asociándolo a un usuario existente. 3) Asigna la sucursal donde trabaja (y su rol operativo: Encargado o Cajero). 4) El sistema guarda el cambio.
- **FA:** A1 — el usuario ya está asignado como empleado en otra sucursal: el sistema pregunta si reasignar o mantener ambas asignaciones.
- **Post:** el empleado queda vinculado a su sucursal con el rol operativo correspondiente.
- **Relaciones:** ninguna.

##### Paquete Catálogo

**CU-11 a CU-15 — Gestión de catálogo base (categorías, tallas, colores, materiales, temporadas)** · Administrador · MVP

Las cinco comparten un mismo patrón CRUD sobre un catálogo maestro pequeño, con borrado lógico (`activo`) y sin eliminación física, según la regla transversal del proyecto.

- **Pre común:** sesión de administrador.
- **FB común:** 1) Consulta el listado de la entidad. 2) Crea, edita o desactiva un registro. 3) El sistema valida que el identificador/nombre no se repita entre registros activos. 4) El sistema guarda el cambio.
- **FA común:** A1 — se intenta desactivar un registro referenciado por productos o variantes activos: el sistema rechaza la desactivación mientras exista al menos una referencia activa.
- **Post común:** el catálogo de la entidad queda actualizado y disponible para `producto` / `producto_variante`.

| CU | Entidad | Particularidad |
|---|---|---|
| CU-11 | categoria | Base para navegar y filtrar el catálogo completo |
| CU-12 | talla | Código de talla único (S, M, L, XL…); prepara la futura tabla de medidas |
| CU-13 | color | Nombre y código hexadecimal únicos; se reutiliza en el asset del probador |
| CU-14 | material | Alimenta la búsqueda por voz (decisión de diseño 6); el dataset de origen no lo trae, se completa a mano |
| CU-15 | temporada | El rango de fechas no puede superponerse con otra temporada activa |

**CU-17 — Gestionar productos** · Administrador · MVP
- **Pre:** existen la categoría y la temporada a asociar.
- **FB:** 1) Consulta el listado de productos. 2) Crea o edita un producto (nombre, descripción, categoría, temporada, material, precio base). 3) El sistema guarda el producto en estado sin variantes. 4) El administrador continúa hacia CU-18 para dar de alta las variantes vendibles.
- **FA:** A1 — el producto no tiene ninguna variante activa: el sistema lo marca "no disponible para venta" aunque exista en el catálogo.
- **Post:** el producto existe y queda listo para asociarle variantes.
- **Relaciones:** precede en el flujo de trabajo del administrador a CU-18 (secuencia operativa, no relación UML).

**CU-18 — Gestionar variantes talla-color** · Administrador · MVP
- **Pre:** existen el producto base (CU-17) y los catálogos de talla y color.
- **FB:** 1) Selecciona el producto. 2) Crea una variante combinando talla y color, con precio final y código de barras propio. 3) El sistema crea automáticamente el registro de `stock` en cero para cada sucursal activa. 4) El sistema guarda la variante.
- **FA:** A1 — combinación talla-color duplicada para el mismo producto: el sistema rechaza la creación.
- **Post:** la variante queda activa y vendible, con stock inicial en cero por sucursal — es la unidad real de negocio para reserva, venta e inventario (decisión de diseño 1: la variante, no el producto, es lo que se reserva y vende).
- **Relaciones:** ninguna.

**CU-20 — Cargar imágenes del producto** · Administrador · MVP
- **Pre:** existe el producto o la variante a la que se asocia la imagen.
- **FB:** 1) El administrador sube uno o más archivos. 2) El sistema los transfiere a Cloudinary. 3) El sistema guarda la URL resultante en `producto_imagen`, con orden de visualización. 4) El administrador marca una imagen como principal.
- **FA:** A1 — el archivo no es una imagen válida o excede el tamaño permitido: el sistema lo rechaza indicando el motivo.
- **Post:** el producto/variante cuenta con al menos una imagen visible en el catálogo.
- **Relaciones:** ninguna.

**CU-21 — Consultar catálogo** · Cliente · MVP
- **Pre:** ninguna (accesible sin sesión).
- **FB:** 1) El cliente abre el catálogo. 2) El sistema lista productos activos con al menos una variante vendible o reservable, paginados. 3) El cliente navega por categoría o temporada.
- **FA:** A1 — catálogo vacío para el filtro elegido: el sistema muestra un estado vacío con sugerencia de quitar filtros.
- **Post:** el cliente visualiza el catálogo disponible.
- **Relaciones:** `«include»` Registrar historial de navegación (siempre que haya sesión).

**CU-22 — Buscar y filtrar prendas** · Cliente · MVP
- **Pre:** ninguna.
- **FB:** 1) El cliente ingresa texto o selecciona filtros (categoría, talla, color, material, temporada, rango de precio). 2) El sistema consulta el catálogo aplicando los filtros combinados. 3) El sistema devuelve resultados paginados.
- **FA:** A1 — búsqueda por voz: el cliente usa CU-72 en vez de escribir, y el texto reconocido alimenta este mismo flujo desde el paso 2.
- **Post:** el cliente visualiza los resultados filtrados.
- **Relaciones:** `«include»` Registrar historial de navegación (siempre que haya sesión).

**CU-23 — Consultar detalle de prenda** · Cliente · MVP
- **Pre:** la prenda (producto) existe y está activa.
- **FB:** 1) El cliente selecciona una prenda del catálogo o de los resultados de búsqueda. 2) El sistema muestra descripción, imágenes, variantes disponibles y disponibilidad por sucursal cercana. 3) El cliente inicia una reserva (CU-39), agrega al carrito (CU-53) o se prueba la prenda (CU-49), si el producto está en el alcance del probador.
- **FA:** A1 — prenda sin stock en ninguna sucursal: el sistema indica "agotado" y solo deja disponible el aviso de disponibilidad futura.
- **Post:** el cliente cuenta con información suficiente para decidir su siguiente acción.
- **Relaciones:** `«include»` Registrar historial de navegación (siempre que haya sesión).

---

##### Paquete Abastecimiento

**CU-25 — Gestionar proveedores** · Administrador · MVP
- **Pre:** sesión de administrador.
- **FB:** 1) Consulta el listado de proveedores. 2) Crea o edita un proveedor (razón social, contacto, NIT). 3) El sistema guarda el cambio.
- **FA:** A1 — el proveedor tiene recepciones históricas y se intenta desactivar: el sistema lo permite, sin afectar el historial ya registrado.
- **Post:** catálogo de proveedores actualizado.
- **Relaciones:** ninguna.

**CU-29 — Registrar recepción de mercadería** · Encargado · MVP
- **Pre:** el proveedor existe y las variantes a recibir ya están dadas de alta en el catálogo (CU-18).
- **FB:** 1) El encargado selecciona el proveedor y la sucursal receptora. 2) Ingresa el detalle de variantes recibidas, cantidad y costo unitario de cada una. 3) El sistema calcula el costo total de la recepción. 4) El sistema confirma la recepción.
- **FA:** A1 — una variante del detalle no existe en el catálogo: el sistema rechaza esa línea hasta que la variante se cree primero.
- **Post:** la recepción queda registrada como la única entrada de stock con costo unitario, habilitando el cálculo de valuación por promedio ponderado.
- **Relaciones:** `«include»` Actualizar inventario tras operación (siempre: aumenta la existencia física y recalcula el costo promedio).

##### Paquete Inventario

**CU-30 — Consultar disponibilidad por sucursal** · Cliente · MVP
- **Pre:** la variante existe.
- **FB:** 1) El cliente consulta una variante desde el detalle de prenda o el buscador. 2) El sistema muestra, por sucursal, la cantidad disponible (física menos reservada). 3) El cliente elige la sucursal donde reservar o retirar.
- **FA:** A1 — sin disponibilidad en ninguna sucursal: el sistema indica "agotado en todas las sucursales".
- **Post:** el cliente conoce dónde puede reservar o comprar la prenda.
- **Relaciones:** ninguna.

**CU-31 — Consultar inventario consolidado global** · Administrador · MVP
- **Pre:** sesión de administrador.
- **FB:** 1) Abre el panel de inventario. 2) El sistema agrega el stock de todas las sucursales por variante, usando la vista `vw_inventario_consolidado`. 3) El administrador filtra por producto, categoría o sucursal.
- **FA:** A1 — sin datos para el filtro elegido: el sistema muestra el panel vacío.
- **Post:** el administrador tiene visibilidad global del inventario.
- **Relaciones:** ninguna.

**CU-32 — Registrar movimiento de inventario** · Encargado · MVP
- **Pre:** la variante y la sucursal existen.
- **FB:** 1) El encargado selecciona la variante, la sucursal y el tipo de movimiento (según `tipo_movimiento`: ajuste manual, merma, etc.). 2) Ingresa la cantidad y un motivo. 3) El sistema registra el movimiento como una fila inmutable, con `saldo_post` y `costo_promedio_post`. 4) El sistema recalcula `cantidad_disponible`.
- **FA:** A1 — el movimiento dejaría el saldo físico en negativo: el sistema lo rechaza.
- **Post:** el movimiento queda registrado de forma permanente — nunca se edita ni se borra (decisión de diseño 3); el stock es siempre la suma de sus movimientos.
- **Relaciones:** ninguna — este caso de uso es en sí mismo la operación base de actualización de inventario para movimientos manuales.

##### Paquete Reservas

**CU-39 — Reservar varias prendas indicando sucursal y horario** · Cliente · MVP
- **Pre:** el cliente tiene sesión y existe disponibilidad de al menos una variante en la sucursal elegida.
- **FB:** 1) El cliente selecciona una o varias variantes. 2) Elige la sucursal y un horario aproximado dentro del horario de atención. 3) El sistema valida disponibilidad de cada variante en esa sucursal. 4) El sistema crea la reserva en estado "pendiente" con su detalle. 5) El sistema confirma la reserva al cliente.
- **FA:** A1 — alguna variante pierde disponibilidad justo al confirmar: el sistema la excluye y pide confirmar el resto. A2 — el cliente elige entrega a domicilio en vez de retiro en sucursal: se dispara el cálculo de costo de envío.
- **Post:** la reserva existe en estado "pendiente", con la cantidad reservada bloqueada en el stock de cada variante (física separada de disponible — decisión de diseño 2).
- **Relaciones:** `«include»` Actualizar inventario tras operación · `«include»` Notificar reserva a la sucursal · `«extend»` Calcular costo de envío (si aplica) · `«extend»` Expirar reservas vencidas (evento posterior, condicional).

**CU-40 — Consultar estado de reserva** · Cliente · MVP
- **Pre:** el cliente tiene al menos una reserva registrada.
- **FB:** 1) El cliente abre su historial de reservas. 2) El sistema muestra el estado actual (`pendiente`, `preparada`, `en_prueba`, `completada`, `cancelada` o `expirada`, según la tabla `estado_reserva`) y el detalle de prendas.
- **FA:** A1 — la reserva expiró justo al momento de la consulta: el sistema refresca el estado antes de mostrarlo.
- **Post:** el cliente conoce el estado vigente de su reserva.
- **Relaciones:** ninguna.

**CU-41 — Cancelar reserva** · Cliente · MVP
- **Pre:** la reserva está en estado `pendiente` o `preparada` (el cliente aún no inició la prueba en sucursal).
- **FB:** 1) El cliente selecciona una reserva activa. 2) Confirma la cancelación. 3) El sistema cambia el estado a `cancelada`.
- **FA:** A1 — la reserva ya está en `en_prueba` o `completada`: el sistema rechaza la cancelación directa y sugiere contactar la sucursal.
- **Post:** la reserva queda cancelada y la cantidad reservada se libera.
- **Relaciones:** `«include»` Actualizar inventario tras operación (libera `cantidad_reservada`).

**CU-43 — Consultar reservas de la sucursal** · Encargado · MVP
- **Pre:** sesión de encargado, asignado a una sucursal.
- **FB:** 1) Abre el panel de reservas de su sucursal. 2) El sistema lista las reservas en estado `pendiente` o `preparada` ordenadas por horario. 3) El encargado selecciona una para atenderla.
- **FA:** A1 — sin reservas pendientes: el sistema muestra el panel vacío.
- **Post:** el encargado tiene visibilidad de las reservas que debe preparar.
- **Relaciones:** ninguna.

**CU-44+ — Atender prueba de reserva en sucursal** *(fusión de CU-44 Preparar, CU-45 Confirmar recepción, CU-46 Liberar)* · Encargado · MVP
- **Pre:** existe una reserva en estado `pendiente` para la sucursal del encargado (ya notificada por el comportamiento incluido de CU-39).
- **FB:** 1) El encargado separa físicamente las prendas y cambia la reserva a `preparada`. 2) Cuando el cliente llega, el encargado la pasa a `en_prueba`. 3) El cliente se prueba las prendas y decide cuáles compra. 4) El encargado registra la selección (`reserva_detalle.seleccionada`) y cierra la reserva como `completada`; las prendas compradas continúan hacia la venta (CU-55).
- **FA:** A1 — el cliente no compra ninguna prenda o deja unidades sin seleccionar: el encargado libera esas unidades de vuelta al stock disponible antes de marcar `completada`. A2 — el cliente no se presenta dentro del horario: la reserva permanece `pendiente` o `preparada` hasta expirar.
- **Post:** las prendas seleccionadas continúan hacia la venta (CU-55) y las no seleccionadas vuelven a estar disponibles para otro cliente.
- **Relaciones:** `«include»` Actualizar inventario tras operación (siempre, al liberar o descontar definitivamente las prendas).

##### Paquete Probador virtual

**CU-48 — Cargar assets y marcar anclajes** · Administrador · MVP
- **Pre:** existe la variante producto-color a la que se asocia el asset (el asset se liga a la variante de color, no a la talla).
- **FB:** 1) El administrador sube la imagen `overlay.png` (fondo transparente, 1024×1024) y `flatlay.jpg` de la variante. 2) Marca hombro izquierdo, hombro derecho y cadera sobre la imagen con el editor de anclajes del panel. 3) Ajusta `factor_ancho`, `desplazamiento_y` y `opacidad`. 4) El sistema guarda `anchors.json` con coordenadas normalizadas entre 0 y 1.
- **FA:** A1 — la imagen no cumple el formato requerido (sin canal alfa o fuera de 1024×1024): el sistema rechaza la carga.
- **Post:** la variante queda habilitada para el modo espejo del probador virtual.
- **Relaciones:** ninguna.

**CU-49 — Probar prenda en modo espejo** · Cliente · MVP
- **Pre:** la variante tiene asset y anclajes cargados (CU-48) y pertenece a una categoría dentro del alcance del probador (prenda superior masculina).
- **FB:** 1) El cliente abre el probador desde el detalle de la prenda, en la app móvil. 2) La app activa la cámara frontal y ejecuta `google_mlkit_pose_detection` on-device. 3) El sistema descarta el frame si el likelihood de algún hombro es menor a 0.6. 4) Calcula ancho corporal, ángulo y centro a partir de los hombros detectados. 5) Dibuja el overlay de la prenda escalado y rotado en tiempo real, invirtiendo el eje X por la cámara espejada. 6) El cliente puede cambiar de color/talla dentro de la misma sesión.
- **FA:** A1 — la pose no se detecta de forma confiable: el sistema mantiene el último frame válido y pide al cliente alejarse o mejorar la iluminación.
- **Post:** el cliente visualiza la prenda superpuesta en tiempo real y decide si reserva (CU-39) o descarta la prenda.
- **Relaciones:** ninguna.

---

##### Paquete Ventas

**CU-53 — Gestionar carrito** · Cliente · MVP
- **Pre:** el cliente tiene sesión.
- **FB:** 1) El cliente agrega una variante con cantidad al carrito desde el detalle de prenda. 2) El sistema valida disponibilidad antes de agregar. 3) El cliente modifica cantidades o quita ítems. 4) El sistema recalcula el subtotal en cada cambio.
- **FA:** A1 — la variante no tiene stock suficiente al agregar: el sistema limita la cantidad a la disponible. A2 — existe una promoción vigente aplicable: se dispara "Aplicar promoción al carrito".
- **Post:** el carrito refleja los ítems y el subtotal vigente, listo para el checkout (CU-54).
- **Relaciones:** `«extend»` Aplicar promoción al carrito (condicional).

**CU-54 — Realizar compra digital** · Cliente · MVP
- **Pre:** el carrito tiene al menos un ítem con disponibilidad confirmada.
- **FB:** 1) El cliente inicia el checkout desde el carrito. 2) Elige retiro en sucursal o entrega a domicilio. 3) Elige el método de pago (pasarela). 4) El sistema crea la venta en estado "pendiente de pago", canal "digital". 5) El cliente completa el pago (CU-62). 6) Al confirmarse el pago, el sistema cierra la venta y emite el comprobante.
- **FA:** A1 — el pago es rechazado: la venta queda en estado "pago rechazado" y el carrito se conserva para reintentar. A2 — se eligió entrega a domicilio: se calcula el costo de envío antes de confirmar el total.
- **Post:** la venta queda registrada y pagada, el inventario se actualiza y el comprobante fue emitido.
- **Relaciones:** `«include»` Actualizar inventario tras operación · `«include»` Emitir comprobante (compartido con CU-55) · `«extend»` Calcular costo de envío (si aplica).

**CU-55 — Registrar venta presencial** · Cajero · MVP
- **Pre:** sesión de cajero asignado a una sucursal; existe disponibilidad física de las variantes vendidas (incluye las provenientes de una reserva `completada`, CU-44+).
- **FB:** 1) El cajero agrega las variantes vendidas y sus cantidades. 2) El sistema calcula el total. 3) El cajero procesa el cobro (CU-63). 4) El sistema registra la venta con canal "presencial" y la marca "pagada". 5) El sistema emite el comprobante.
- **FA:** A1 — la venta se origina en una reserva `completada`: el detalle se prellena con las prendas seleccionadas en CU-44+.
- **Post:** la venta queda registrada y pagada, el inventario se actualiza y el comprobante fue emitido.
- **Relaciones:** `«include»` Actualizar inventario tras operación · `«include»` Emitir comprobante (compartido con CU-54).

**CU-56 — Emitir comprobante** *(comportamiento incluido compartido)* · Cajero / Cliente · MVP
- **Pre:** existe una venta cerrada y pagada (CU-54 o CU-55).
- **FB:** 1) El sistema genera un número de comprobante secuencial por sucursal/canal. 2) Arma el detalle de ítems, impuestos si aplica, y totales. 3) Pone el comprobante a disposición (descarga o impresión).
- **FA:** A1 — falla la generación del número secuencial por concurrencia: el sistema reintenta con bloqueo transaccional antes de fallar.
- **Post:** la venta cuenta con un comprobante válido y trazable.
- **Relaciones:** incluido por CU-54 y CU-55 — comportamiento compartido, no es una meta de primer nivel iniciada de forma independiente por el actor.

##### Paquete Pagos

**CU-62 — Pagar mediante pasarela digital** · Cliente · MVP
- **Pre:** existe una venta digital pendiente de pago (CU-54).
- **FB:** 1) El cliente elige Libélula o PayPal. 2) El sistema abre el flujo de la pasarela con el monto de la venta. 3) El cliente completa el pago en la pasarela. 4) La pasarela notifica el resultado al sistema (CU-64).
- **FA:** A1 — el cliente abandona el flujo de pago: la venta permanece "pendiente de pago" hasta expirar o hasta un nuevo intento.
- **Post:** se inició una transacción de pago asociada a la venta, a la espera de confirmación.
- **Relaciones:** ninguna propia — dispara CU-64 en el sistema externo.

**CU-63 — Procesar pago en caja** · Cajero · MVP
- **Pre:** existe una venta presencial con total calculado (CU-55).
- **FB:** 1) El cajero selecciona el medio de cobro: efectivo, QR, tarjeta (débito/crédito) o transferencia. 2) Registra el monto recibido (y el cambio, si es efectivo). 3) El sistema marca el pago confirmado de inmediato para efectivo, o pendiente de verificación externa para QR/tarjeta/transferencia.
- **FA:** A1 — el pago con QR/tarjeta es rechazado por la red: el sistema mantiene la venta sin cerrar y permite elegir otro medio.
- **Post:** el pago de la venta presencial queda registrado con su método y estado.
- **Relaciones:** ninguna propia.

**CU-64 — Confirmar o rechazar transacción** · Sistema de pagos · MVP
- **Pre:** existe una transacción de pasarela iniciada (CU-62).
- **FB:** 1) La pasarela procesa la transacción. 2) Envía una notificación con el resultado (aprobada/rechazada) y un identificador externo. 3) El sistema verifica la firma/autenticidad de la notificación. 4) Actualiza el estado del pago y, si fue aprobado, cierra la venta digital correspondiente.
- **FA:** A1 — notificación duplicada o fuera de orden: el sistema aplica verificación de idempotencia y descarta el duplicado. A2 — transacción rechazada: la venta pasa a "pago rechazado" y se libera el stock reservado para el checkout.
- **Post:** la venta digital queda en un estado consistente con el resultado real de la pasarela.
- **Relaciones:** ninguna propia — es el disparador externo que completa CU-54.

##### Paquete Entregas

**CU-67 — Gestionar zonas por anillo y tarifas** · Administrador · Prioridad 2, promovido a la línea base
- **Pre:** sesión de administrador; existe la sucursal desde la que se despachará.
- **FB:** 1) El administrador define zonas de cobertura (anillos) alrededor de una sucursal. 2) Para cada zona define una regla de tarifa (monto fijo o por rango de distancia/peso). 3) El sistema guarda la configuración en `zona_envio` y `regla_tarifa_envio`.
- **FA:** A1 — zonas superpuestas para la misma sucursal: el sistema advierte pero permite guardar, aplicando la de menor tarifa como criterio de desempate.
- **Post:** la sucursal cuenta con zonas y tarifas configuradas, insumo del cálculo de costo de envío usado por CU-39/CU-54.
- **Relaciones:** ninguna propia — es la configuración que consume el comportamiento extendido "Calcular costo de envío".

##### Paquete Inteligencia artificial

**CU-71 — Recomendar prendas al cliente** · Servicio de IA · MVP
- **Pre:** el cliente tiene historial de navegación o compra registrado.
- **FB:** 1) El cliente abre una sección de recomendaciones (home o detalle de prenda). 2) El sistema envía al Servicio de IA (Groq) el historial reciente del cliente y el catálogo disponible. 3) El servicio de IA devuelve una lista de variantes recomendadas. 4) El sistema guarda y muestra la recomendación.
- **FA:** A1 — el cliente no tiene historial suficiente: el sistema muestra una recomendación genérica basada en las prendas más vistas o vendidas.
- **Post:** el cliente recibe una lista de prendas recomendadas relevante a su comportamiento.
- **Relaciones:** consume como insumo de datos el comportamiento incluido "Registrar historial de navegación" (dependencia de datos, no relación UML de extensión).

**CU-72 — Buscar mediante comando de voz** · Cliente · MVP
- **Pre:** el dispositivo del cliente tiene permiso de micrófono concedido.
- **FB:** 1) El cliente activa el micrófono y dicta una consulta (ej. "blusa de primavera, de algodón, color amarillo"). 2) El dispositivo convierte voz a texto (STT nativo). 3) El sistema envía el texto al Servicio de IA para extraer entidades (categoría, temporada, material, color). 4) El sistema traduce esas entidades a los filtros de CU-22 y ejecuta la búsqueda.
- **FA:** A1 — el texto no puede interpretarse en entidades de catálogo: el sistema ejecuta una búsqueda de texto libre como respaldo.
- **Post:** el cliente visualiza resultados de búsqueda equivalentes a una búsqueda manual con filtros.
- **Relaciones:** `«include»` hacia CU-22 (los resultados se resuelven reutilizando el mismo flujo de búsqueda y filtrado).

##### Paquete Reportes

**CU-76 — Consultar reporte de ventas** · Administrador · MVP
- **Pre:** sesión de administrador.
- **FB:** 1) El administrador elige un rango de fechas y, opcionalmente, sucursal o canal. 2) El sistema consulta `vw_ventas_detalle` y agrega totales, cantidad de ventas y ticket promedio. 3) Presenta el reporte en tabla.
- **FA:** A1 — sin ventas en el rango elegido: el sistema muestra el reporte vacío con el rango indicado.
- **Post:** el administrador cuenta con una vista consolidada de ventas para el período elegido.
- **Relaciones:** ninguna — solo lectura; el paquete `reportes` no es dependido por ningún otro paquete.

**CU-77 — Consultar reporte de inventario** · Administrador · MVP
- **Pre:** sesión de administrador.
- **FB:** 1) El administrador elige sucursal, categoría o rango de fechas de movimientos. 2) El sistema agrega existencias actuales, movimientos del período y valuación por promedio ponderado. 3) Presenta el reporte.
- **FA:** A1 — la sucursal no tiene movimientos en el rango: el sistema muestra solo el stock actual, sin movimientos.
- **Post:** el administrador cuenta con una vista consolidada del estado del inventario.
- **Relaciones:** ninguna.

---

### 1.4 Prototipar interfaz (J.U.)

Se documentan a nivel de wireframe funcional (campos, acciones y validaciones visibles) las pantallas de los casos de uso más críticos — los que definen la identidad del proyecto (vestidor virtual, reserva) y los de mayor complejidad transaccional (checkout, punto de caja). El resto de las pantallas del catálogo depurado sigue el mismo lenguaje visual y los tokens de diseño del proyecto (fondo `#FFFFFF`/`#F7F7F5`, texto `#1A1A1A`/`#6B6B6B`, acento `#1F2937`, éxito `#16A34A`, error `#DC2626`, radio de 8px, espaciado en múltiplos de 4px), con el back office en formato denso de tabla y el cliente móvil en formato amplio centrado en fotografía.

**Pantalla — Probador virtual, modo espejo (CU-49, app móvil)**
```
┌─────────────────────────────────┐
│ ← Volver          Polera Azul M │
├─────────────────────────────────┤
│                                  │
│      [ vista de cámara en       │
│        vivo + overlay de la     │
│        prenda superpuesto ]     │
│                                  │
│                                  │
├─────────────────────────────────┤
│  Color:  ⚪ Azul  ⚫ Negro  ⚪ Gris│
│  Talla:  [S] [M✓] [L] [XL]      │
├─────────────────────────────────┤
│   [   Reservar esta prenda   ]  │  ← botón acento #1F2937
│   [   Ver otras prendas       ] │
└─────────────────────────────────┘
Validaciones: si no se detecta la pose con suficiente confianza,
se reemplaza el overlay por un aviso "Ubícate a un metro de la
cámara, con buena iluminación" en vez de dibujar sobre un frame
no confiable.
```

**Pantalla — Reservar prendas (CU-39, app móvil)**
```
┌─────────────────────────────────┐
│ ← Volver           Mi reserva   │
├─────────────────────────────────┤
│ Prendas seleccionadas (2)       │
│ • Polera Azul, M         [x]    │
│ • Camisa Blanca, L       [x]    │
├─────────────────────────────────┤
│ Sucursal:  [ Sucursal Norte ▾]  │
│ Horario aprox.: [ 16:00 ▾]      │
│ Entrega:  ◉ Retiro en sucursal  │
│           ○ A domicilio          │
├─────────────────────────────────┤
│  [    Confirmar reserva     ]   │  ← disabled si alguna
└─────────────────────────────────┘     prenda quedó sin stock
Validación en vivo: al elegir sucursal, se vuelve a consultar
disponibilidad de cada prenda (CU-30); la que ya no tenga stock
se marca en rojo (#DC2626) y bloquea la confirmación hasta
quitarla o cambiar de sucursal.
```

**Pantalla — Checkout de compra digital (CU-54, web/app)**
```
┌───────────────────────────────────────────┐
│ Resumen de compra                          │
├───────────────────────────────────────────┤
│ Polera Azul M      x1        Bs 120        │
│ Camisa Blanca L    x1        Bs 150        │
│                     Subtotal  Bs 270        │
│                     Envío     Bs  15        │
│                     Total     Bs 285        │
├───────────────────────────────────────────┤
│ Entrega: ◉ A domicilio   ○ Retiro sucursal │
│ Dirección: [ Av. Siempre Viva 742      ]   │
├───────────────────────────────────────────┤
│ Método de pago:  ◉ Libélula   ○ PayPal     │
│         [      Pagar Bs 285      ]         │  ← éxito #16A34A
└───────────────────────────────────────────┘
Validación: el botón de pago solo se habilita si todos los ítems
mantienen disponibilidad confirmada al momento de abrir el
checkout (repite la validación de CU-53).
```

**Pantalla — Punto de caja (CU-55 / CU-63, back office web, formato denso)**
```
┌──────────────────────────────────────────────────────────┐
│ Venta presencial · Sucursal Norte · Cajero: J. Pérez      │
├──────────────────────────────────────────────────────────┤
│ Código/Variante        Cant.   P.Unit    Subtotal          │
│ VAR-00231 Polera Azul M  1     120.00     120.00      [x]  │
│ + Agregar variante...                                       │
├──────────────────────────────────────────────────────────┤
│                                    Total:  Bs 120.00        │
├──────────────────────────────────────────────────────────┤
│ Medio de cobro: [Efectivo][QR][Tarjeta][Transferencia]     │
│ Monto recibido: [ 150.00 ]     Cambio: Bs 30.00             │
│              [   Confirmar venta y emitir comprobante  ]   │
└──────────────────────────────────────────────────────────┘
Validación: "Confirmar venta" permanece deshabilitado si el
monto recibido es menor al total (excepto QR/tarjeta/
transferencia, donde el monto exacto lo confirma la red).
```

### 1.5 Estructurar el modelo de casos de uso

El modelo de casos de uso se organiza en Enterprise Architect como un paquete raíz `Casos de Uso` con doce sub-paquetes, uno por área de negocio (Seguridad, Organización, Catálogo, Abastecimiento, Inventario, Reservas, Probador, Ventas, Pagos, Entregas, Inteligencia, Reportes), reflejando exactamente los paquetes de negocio del backend salvo `core` (que no expone casos de uso propios). Cada sub-paquete contiene:

- Los casos de uso de primer nivel que le corresponden (columna "Paquete" de la tabla de priorización, sección 1.2).
- Los comportamientos transversales `«include»`/`«extend»` cuyo caso base pertenece a ese paquete.
- Los actores que participan, repetidos visualmente en cada sub-diagrama para no forzar una referencia cruzada entre paquetes distintos.

Un diagrama general adicional (`CU - Vista general del sistema`) muestra únicamente los 42 casos de uso de primer nivel agrupados por paquete (sin desplegar los comportamientos transversales, para mantenerlo legible), con los siete actores en los bordes — este es el diagrama que se presenta como portada de la especificación de requisitos. Los doce diagramas de detalle por paquete sí incluyen las relaciones `«include»`/`«extend»` completas.

---

**Diagrama en Enterprise Architect.** El diagrama de casos de uso general (`CU-01 Vista general del sistema`) está construido en el modelo, bajo `Model / FashionStore / F.T.1 - Requisitos / Casos de Uso`, con un sub-paquete por área de negocio, los 7 actores, los 42 casos de uso de primer nivel y los 6 comportamientos transversales, con sus 58 relaciones (41 asociaciones actor-CU, 13 `«include»`, 4 `«extend»`) ya trazadas.

---

## F.T.2 — Análisis

### 2.1 Análisis de arquitectura

El análisis parte de la arquitectura ya decidida en la Parte I y el consolidado técnico: un monolito modular en capas, con dos aplicaciones cliente (app_movil en Flutter, app_web en Angular) que consumen una única API REST, y esa API dividida internamente en 13 paquetes de negocio con dependencia unidireccional (`core → seguridad → organizacion → catalogo → inventario → abastecimiento → reservas → ventas → pagos → entregas → probador → inteligencia → reportes`). A nivel de análisis, esta arquitectura se confirma —no se cuestiona el estilo monolítico, ya justificado— y se usa como marco para ubicar las clases de análisis: cada paquete de negocio del backend se convierte en un paquete de análisis con sus propias clases de entidad, control y frontera; los tres sistemas externos (pasarela de pago, servicio de IA, almacenamiento de objetos) se modelan como actores secundarios que reciben o envían mensajes desde las clases de control, nunca directamente desde una clase entidad.

### 2.2 Analizar casos de uso (clases entidad, control y frontera)

**Convención de estereotipos aplicada:**
- **Clase frontera (`«boundary»`):** la pantalla de la aplicación cliente (Flutter o Angular) con la que interactúa el actor. La API REST (`router.py`) no se modela como una frontera adicional en el diagrama de robustez: es el mecanismo de comunicación entre la frontera visual y el control, y se documenta como tal en el texto, no como una caja aparte, para no duplicar una capa que en este proyecto es puramente de transporte (el router, según la regla 5 del proyecto, no contiene lógica propia).
- **Clase control (`«control»`):** una por paquete de negocio, correspondiente 1 a 1 con el `service.py` real de ese paquete. Coordina la secuencia de pasos de sus casos de uso y es la única capa autorizada a invocar el control de otro paquete (nunca a leer sus entidades directamente — regla de dependencia del proyecto).
- **Clase entidad (`«entity»`):** corresponde a una tabla persistente (`models.py`), con sus atributos principales a nivel conceptual (los tipos y restricciones completos se fijan en el diseño de datos, sección 3.3).

Se analizan en detalle los seis casos de uso más representativos de la complejidad del sistema — los que combinan más de un paquete de control o tienen mayor valor diferenciador — y el resto de los 42 CU sigue el mismo patrón boundary→control→entity dentro de un único paquete, sin necesidad de un diagrama propio.

**Análisis 1 — CU-39 Reservar varias prendas** (incluye Actualizar inventario y Notificar reserva; extiende Calcular costo de envío)
| Frontera | Control | Entidad |
|---|---|---|
| Pantalla "Reservar prendas" (app móvil) | `ControlReservas` (coordina), `ControlInventario` (valida y actualiza disponibilidad), `ControlEntregas` (si aplica envío) | `Reserva`, `ReservaDetalle`, `EstadoReserva`, `Stock`, `MovimientoInventario`, `Notificacion` |

**Análisis 2 — CU-49 Probar prenda en modo espejo**
| Frontera | Control | Entidad |
|---|---|---|
| Pantalla "Probador virtual" (app móvil, con overlay de cámara) | `ControlProbador` (recupera asset y anclajes; no procesa video, eso ocurre en el cliente) | `ActivoProbador`, `ProductoVariante` |

**Análisis 3 — CU-54 Realizar compra digital + CU-62/CU-64 Pago con pasarela**
| Frontera | Control | Entidad |
|---|---|---|
| Pantalla "Checkout" (app móvil / web) | `ControlVentas` (crea la venta), `ControlPagos` (inicia y confirma la transacción), `ControlInventario` (descuenta stock al confirmarse el pago), `ControlEntregas` (si aplica envío) | `Venta`, `VentaDetalle`, `EstadoVenta`, `Pago`, `TransaccionPasarela`, `MetodoPago`, `Stock` |

**Análisis 4 — CU-55 Registrar venta presencial + CU-63 Procesar pago en caja**
| Frontera | Control | Entidad |
|---|---|---|
| Pantalla "Punto de caja" (back office web) | `ControlVentas`, `ControlPagos`, `ControlInventario` | `Venta`, `VentaDetalle`, `Pago`, `MetodoPago`, `Stock`, `MovimientoInventario` |

**Análisis 5 — CU-71 Recomendar prendas al cliente**
| Frontera | Control | Entidad |
|---|---|---|
| Sección "Recomendado para ti" (app móvil / web) | `ControlInteligencia` (arma el contexto y llama al Servicio de IA externo) | `HistorialNavegacion`, `Recomendacion`, `ProductoVariante` |

**Análisis 6 — CU-72 Buscar mediante comando de voz** (incluye CU-22 Buscar y filtrar)
| Frontera | Control | Entidad |
|---|---|---|
| Pantalla "Búsqueda por voz" (app móvil, micrófono) | `ControlInteligencia` (interpreta la consulta con el Servicio de IA), `ControlCatalogo` (ejecuta la búsqueda resultante) | `ConsultaVoz`, `Producto`, `ProductoVariante`, `Categoria`, `Material` |

En los seis casos, el patrón de colaboración es el mismo: la frontera envía un mensaje a un único control "entrante" (el del paquete dueño del caso de uso), y ese control invoca a los controles de los demás paquetes involucrados —nunca a sus entidades directamente—, que a su vez son los únicos que leen y escriben sus propias entidades. Este patrón es la traducción, a nivel de análisis, de la regla de dependencia ya fijada en la arquitectura: *"un paquete nunca consulta las tablas de otro; llama al service del otro paquete"*.

### 2.3 Análisis de clases

**Clases de control** (una por paquete de negocio, corresponden a `service.py`): `ControlSeguridad`, `ControlOrganizacion`, `ControlCatalogo`, `ControlAbastecimiento`, `ControlInventario`, `ControlReservas`, `ControlVentas`, `ControlPagos`, `ControlEntregas`, `ControlProbador`, `ControlInteligencia`, `ControlReportes`. El paquete `core` no aporta una clase de control de negocio: aporta la infraestructura compartida (`CRUDBase`, configuración, manejo de excepciones) de la que las demás heredan o hacen uso.

**Clases de frontera** (pantallas principales por canal): en la app móvil, Registro/Login, Catálogo, Búsqueda (texto y voz), Detalle de prenda, Probador virtual, Reserva, Carrito, Checkout, Historial de reservas. En el back office web: Login, Gestión de catálogo base, Gestión de productos y variantes, Gestión de sucursales y empleados, Inventario consolidado, Recepción de mercadería, Panel de reservas de sucursal, Punto de caja, Reportes.

**Clases de entidad** (agrupadas por paquete, mismos nombres y agrupación que las 61 tablas del diseño de datos; los atributos mostrados aquí son los relevantes a nivel de análisis — el detalle completo de tipos, claves y restricciones se fija en la sección 3.3):

| Paquete | Clases de entidad | Atributos principales de análisis |
|---|---|---|
| Seguridad | Rol, Permiso, Usuario | Usuario: correo, contraseña (hash), activo · Rol: nombre · Permiso: código, descripción |
| Organización | Ciudad, Sucursal, HorarioSucursal, Empleado, Cliente | Sucursal: nombre, dirección, ciudad · Empleado: usuario, sucursal, cargo · Cliente: usuario, teléfono |
| Catálogo | Categoria, Talla, Color, Material, Temporada, Coleccion, Producto, ProductoVariante, ProductoImagen, TablaMedida, Favorito | Producto: nombre, categoría, temporada, material · ProductoVariante: talla, color, precio, código de barras |
| Abastecimiento | Proveedor, ProductoProveedor, OrdenCompra, OrdenCompraDetalle, Recepcion, RecepcionDetalle | Proveedor: razón social, contacto · RecepcionDetalle: variante, cantidad, costo unitario |
| Inventario | Stock, TipoMovimiento, MovimientoInventario, Transferencia, TransferenciaDetalle | Stock: variante, sucursal, cantidad física, cantidad reservada, cantidad disponible (calculada) · MovimientoInventario: tipo, cantidad, saldo posterior, costo promedio posterior |
| Reservas | EstadoReserva, Reserva, ReservaDetalle, ReservaHistorial | Reserva: cliente, sucursal, horario, estado · ReservaDetalle: variante, cantidad |
| Ventas | EstadoVenta, Promocion, PromocionAlcance, Venta, VentaDetalle, Carrito, CarritoDetalle, Devolucion, DevolucionDetalle | Venta: canal, cliente/cajero, sucursal, estado, total · VentaDetalle: variante, cantidad, precio unitario |
| Pagos | MetodoPago, EstadoPago, Pago, TransaccionPasarela | Pago: venta, método, monto, estado · TransaccionPasarela: identificador externo, pasarela, resultado |
| Entregas | ZonaEnvio, ReglaTarifaEnvio, DireccionCliente, Envio | ZonaEnvio: sucursal, anillo · ReglaTarifaEnvio: zona, tarifa · Envio: venta, dirección, costo, estado |
| Probador | ActivoProbador, ProbadorGeneracion, SesionProbador | ActivoProbador: variante, overlay, anclajes · SesionProbador: cliente, variante, modo |
| Inteligencia | HistorialNavegacion, ConsultaVoz, Recomendacion | HistorialNavegacion: cliente, producto, tipo de evento · Recomendacion: cliente, variantes sugeridas |
| Núcleo (`core`) | Bitacora, Notificacion | Bitacora: entidad afectada, acción, usuario, fecha · Notificacion: destinatario, tipo, leído |

### 2.4 Análisis de paquete

Se verifica que la partición en 13 paquetes mantiene **bajo acoplamiento** (las dependencias son unidireccionales, sin ciclos, y ningún paquete accede a las tablas de otro) y **alta cohesión** (cada paquete agrupa clases que cambian juntas, por la misma razón de negocio):

| Paquete | Responsabilidad única | Depende de | Es dependido por | Cohesión / Acoplamiento |
|---|---|---|---|---|
| core | Configuración, CRUD genérico, auditoría, excepciones | — | Todos | Máxima cohesión (infraestructura transversal); es la única dependencia común, por diseño |
| seguridad | Usuarios, roles, permisos, autenticación | core | organizacion y, transitivamente, todos los que exigen sesión | Alta: todo lo relacionado a identidad y acceso vive aquí |
| organizacion | Ciudades, sucursales, horarios, empleados, clientes | core, seguridad | catalogo (no), inventario, reservas, ventas, entregas | Alta: entidades geográficas/organizativas, sin lógica de catálogo ni de stock |
| catalogo | Productos, variantes, atributos | core | abastecimiento, inventario, reservas, ventas, probador, inteligencia | Máxima: es el paquete más dependido y depende solo de `core`, tal como fija la regla de arquitectura |
| abastecimiento | Proveedores, recepciones | catalogo, inventario, organizacion | — | Alta: todo lo relativo a la entrada de mercadería |
| inventario | Existencias, movimientos, valuación | catalogo, organizacion | abastecimiento, reservas, ventas | Alta: toda operación de stock pasa por este paquete, nunca se replica en otro |
| reservas | Reserva multi-prenda y su ciclo de vida | catalogo, inventario, organizacion | ventas (una reserva `completada` deriva en venta) | Alta |
| ventas | Carrito, venta digital y presencial | catalogo, inventario, reservas | pagos, entregas | Alta |
| pagos | Métodos de pago, pasarelas, transacciones | ventas | — | Alta: aislado del resto salvo su origen (la venta que paga) |
| entregas | Zonas, tarifas, direcciones, envíos | ventas, organizacion | — | Alta |
| probador | Assets, anclajes, sesiones | catalogo | — | Alta: no conoce inventario ni ventas, solo el catálogo |
| inteligencia | Recomendador, búsqueda por voz, historial | catalogo, inventario | — | Alta |
| reportes | Indicadores y dashboards, solo lectura | ventas, inventario, reservas | — (ningún paquete depende de él) | Máxima: es de solo lectura por regla explícita del proyecto, no puede introducir un ciclo |

No se detectan ciclos de dependencia ni acoplamientos cruzados que violen la regla "un paquete nunca consulta las tablas de otro, llama a su service" — validado tanto en el diseño documentado como en el código real ya implementado para los 11 paquetes con backend avanzado.

**Diagramas construidos en Enterprise Architect.** Bajo `Model / FashionStore / F.T.2 - Analisis`: sub-paquete `Analisis de Casos de Uso` con tres diagramas de robustez consolidados — `AN-01` (Reservas y Probador virtual, 13 mensajes), `AN-02` (Venta, Pago y Entrega, 13 mensajes) y `AN-03` (Inteligencia artificial, 10 mensajes), agrupando los seis análisis de la sección 2.2 en pares por afinidad de flujo para no fragmentar en seis diagramas casi idénticos en patrón; y sub-paquete `Analisis de Paquete` con `AN-04` (los 13 paquetes de negocio y sus 24 relaciones de dependencia, dispuestos por capas desde `core`, sin ciclos), que visualiza exactamente la tabla de la sección 2.4.

---

**Diagramas en Enterprise Architect.** Bajo `Model / FashionStore / F.T.2 - Analisis`: sub-paquete `Analisis de Casos de Uso` con tres diagramas de robustez (`AN-01 Robustez - Reservas y Probador virtual`, `AN-02 Robustez - Venta, Pago y Entrega`, `AN-03 Robustez - Inteligencia artificial`, con sus 36 mensajes boundary→control→entity); y sub-paquete `Analisis de Paquete` con `AN-04 Paquetes de negocio y dependencias` (13 paquetes, 24 relaciones de dependencia, dispuestos por capas desde `core` hasta los paquetes de mayor nivel, sin ciclos).

---

## F.T.3 — Diseño

### 3.1 Diseño de arquitectura

#### Arquitectura lógica

La arquitectura lógica formaliza, en clases de diseño, lo que el análisis dejó planteado en clases conceptuales. Cada paquete de análisis se convierte en un paquete de diseño con tres capas internas, replicando exactamente la estructura real de archivos del backend (`router.py → service.py → repository.py → model.py`):

```
paquete_de_negocio/
├── router.py       — capa de presentación de la API (frontera HTTP)
├── service.py       — capa de control: reglas de negocio, orquesta repository y otros services
├── repository.py    — capa de acceso a datos: hereda de core/crud_base.py
├── schemas.py        — contratos Pydantic de entrada/salida (Crear, Actualizar, Respuesta)
└── models.py         — capa de entidad: modelos SQLAlchemy (tablas)
```

Esto añade una capa que el análisis no distinguía explícitamente: **repository**, intercalada entre control y entidad, responsable exclusiva del acceso a datos (consultas SQLAlchemy), de modo que el control (`service.py`) nunca construye una consulta SQL directamente ni conoce el motor de persistencia. Todo `repository.py` hereda de `core/crud_base.py`, que centraliza las operaciones CRUD comunes (crear, obtener por id, listar, actualizar, borrado lógico) para no repetir código entre los 13 paquetes — es la traducción arquitectónica de la regla 3 del proyecto.

La comunicación entre paquetes ocurre siempre `service.py` → `service.py` de otro paquete (nunca `service.py` → `repository.py` ni `models.py` de otro paquete), lo que preserva en diseño el bajo acoplamiento ya verificado en el análisis de paquete (sección 2.4). Por ejemplo, `ventas.service` no arma un `UPDATE` sobre la tabla `stock`: llama a `inventario.service.registrar_movimiento()`.

**Diagrama de paquetes de diseño**: mismo grafo de dependencias que `AN-04`, pero mostrando dentro de cada paquete sus cuatro archivos (router/service/repository/model) como componentes internos, y marcando expresamente que solo `router` expone puertos hacia el exterior (HTTP) y solo `service` expone puertos hacia otros paquetes.

#### Arquitectura física (despliegue)

| Nodo | Contenido | Tecnología |
|---|---|---|
| Cliente móvil | app_movil | Flutter/Dart, Material 3, corre en el dispositivo del cliente |
| Cliente web | app_web | Angular + PrimeNG, servido como estático |
| Servidor de hosting web | Vercel (o Netlify) | Sirve los estáticos de `app_web` |
| Servidor de aplicación | Railway | Un proceso FastAPI (los 13 paquetes), expone la API REST |
| Servidor de base de datos | Railway PostgreSQL | Instancia gestionada, 61 tablas + 2 vistas |
| Almacenamiento de objetos | Cloudinary | Imágenes de catálogo y assets del probador (`overlay.png`, `flatlay.jpg`, `anchors.json`, `thumb.jpg`) |
| Servicio externo de pagos | Libélula / PayPal (sandbox) | Se consume vía HTTPS desde `pagos.service` |
| Servicio externo de IA | Groq | Se consume vía HTTPS desde `inteligencia.service` y `probador.service` |

Relaciones de despliegue: el cliente móvil y el cliente web se comunican con el servidor de aplicación exclusivamente por HTTPS/REST; el servidor de aplicación se comunica con el servidor de base de datos por el protocolo nativo de PostgreSQL (dentro de la red privada de Railway) y con Cloudinary/Libélula/PayPal/Groq por HTTPS hacia servicios externos. No existe comunicación directa entre los clientes y la base de datos, ni entre los clientes y los servicios externos: todo pasa por el servidor de aplicación, que es el único punto de aplicación de las reglas de negocio y de los secretos de integración (llaves de API en variables de entorno, nunca en el código ni en el cliente).

### 3.2 Diseño de casos de uso

Para los mismos seis análisis de la sección 2.2, el diseño detalla la interacción en el tiempo (secuencia), el ciclo de vida de las entidades centrales (estados) y la navegación entre pantallas.

**Diagrama de secuencia — CU-39 Reservar prendas.** Actores de la secuencia: Cliente → `ReservaRouter` → `ReservaService` → (`InventarioService` para validar y reservar disponibilidad, `OrganizacionService` para validar horario de sucursal) → `ReservaRepository` → `Reserva`/`ReservaDetalle` (persistencia) → de vuelta, `ReservaService` dispara `NotificacionService`. Puntos de decisión: si `InventarioService` responde que una variante no tiene disponibilidad, la secuencia bifurca hacia el flujo alternativo A1 documentado en la ficha del CU (excluir esa variante y continuar).

**Diagrama de secuencia — CU-54 Realizar compra digital + CU-64 Confirmar transacción.** Dos secuencias encadenadas por un límite asíncrono: (1) Cliente → `VentaRouter` → `VentaService` (crea venta "pendiente de pago") → `PagoService` → pasarela externa (respuesta de redirección); (2) evento entrante, Sistema de pagos → `PagoRouter` (webhook) → `PagoService` (verifica firma) → `VentaService` (cierra venta) → `InventarioService` (descuenta stock) → `VentaService` (emite comprobante). Esta separación en dos secuencias con un actor externo en medio es, precisamente, la razón documentada para no usar un patrón de transacción distribuida tipo Saga: cada secuencia individual sigue siendo una única transacción de base de datos.

**Diagrama de estados — Reserva** (tabla `estado_reserva`, códigos reales del esquema): `pendiente → preparada → en_prueba → completada`, con transiciones alternativas `pendiente|preparada → cancelada` (por el cliente, CU-41) y `pendiente|preparada → expirada` (automática, comportamiento extendido). `completada`, `cancelada` y `expirada` son estados finales (`es_final = true` en la tabla); desde `completada` no hay transición de vuelta: el resultado (venta o liberación de prendas) se registra en `venta`/`movimiento_inventario`, no como un nuevo estado de la reserva.

**Diagrama de estados — Venta** (tabla `estado_venta`): `pendiente_pago → pagada → entregada`, con transición alternativa `pendiente_pago → anulada` (pago rechazado o checkout abandonado). `entregada` y `anulada` son finales. Para canal presencial con efectivo, la venta puede nacer directamente en `pagada` (confirmación inmediata); con QR/tarjeta/transferencia pasa primero por `pendiente_pago` sujeto a verificación.

**Diagrama de estados — Pago** (tabla `estado_pago`): `iniciado → aprobado` o `iniciado → rechazado`, reflejando 1 a 1 la respuesta de `«include» Confirmar o rechazar transacción` (CU-64); adicionalmente `aprobado → reembolsado`, transición cuyo disparador (CU-66 Anular o reembolsar pago) es prioridad 3 y queda fuera del alcance de casos de uso de esta fase, pero el estado ya existe en el esquema y se documenta para que el modelo de datos quede completo.

**Diagrama de navegación — Aplicación móvil (Cliente).** Home/Catálogo ⇄ Búsqueda (texto o voz) ⇄ Detalle de prenda → {Probador virtual, Agregar al carrito, Reservar} → Carrito → Checkout → Confirmación de compra; en paralelo, Home ⇄ Mis reservas ⇄ Detalle de reserva. Todas las pantallas comparten la barra inferior de navegación (Catálogo, Buscar, Reservas/Carrito, Perfil).

**Diagrama de navegación — Back office web (Administrador/Encargado/Cajero).** Login → Panel según rol: Administrador ve {Catálogo base, Productos y variantes, Sucursales y empleados, Inventario consolidado, Zonas de entrega, Reportes}; Encargado ve {Recepción de mercadería, Movimientos de inventario, Panel de reservas de su sucursal}; Cajero ve {Punto de caja}. La navegación entre secciones respeta los permisos por rol definidos en CU-04.

**Diagramas construidos en Enterprise Architect.** Bajo `Model / FashionStore / F.T.3 - Diseno / Diseno de CU`: `DIS-02` (secuencia CU-39, 12 mensajes) y `DIS-03` (secuencia CU-54/62/64, 14 mensajes, incluyendo el mensaje asíncrono del webhook de la pasarela); `DIS-04`, `DIS-05`, `DIS-06` (estados de Reserva, Venta y Pago respectivamente, con los códigos reales verificados contra `fashionstore_esquema.sql`). Los dos diagramas de navegación quedan documentados en texto en esta fase; su construcción gráfica en Enterprise Architect se completa en la Fase 2 junto con el resto del diseño de interacción.

### 3.3 Diseño de datos

El diseño de datos traduce las clases de entidad del análisis (sección 2.3) al modelo relacional completo y definitivo: **61 tablas más 2 vistas**, documentado en detalle en `docs/fashionstore_esquema.sql` (fuente ejecutable de referencia, no se ejecuta directamente contra la base — las tablas las crea Alembic a partir de los modelos SQLAlchemy). A diferencia de la sección 2.3, aquí sí se fijan tipos, claves primarias/foráneas, restricciones y las columnas de auditoría transversales.

**Las ocho decisiones de diseño de datos** (ya introducidas en el consolidado técnico, aquí se listan como reglas que todo el modelo de clases de datos respeta):

1. **Producto vs. variante.** `producto` es el concepto comercial (nombre, descripción, categoría); `producto_variante` es la unidad real de negocio (talla + color + precio + código de barras). Stock, reserva y venta siempre referencian `producto_variante.id`, nunca `producto.id`.
2. **Stock por par variante-sucursal, física vs. disponible.** La tabla `stock` tiene `cantidad_fisica` y `cantidad_reservada` como columnas de base, y `cantidad_disponible` como **columna generada** (`cantidad_fisica - cantidad_reservada`), nunca escrita directamente desde el código.
3. **Movimientos de inventario como libro inmutable.** `movimiento_inventario` no admite `UPDATE` ni `DELETE` a nivel de regla de negocio; cada fila guarda `saldo_post` y `costo_promedio_post`, de modo que el stock actual es siempre reconstruible como la suma de sus movimientos.
4. **Una sola tabla de venta con campo canal.** `venta.canal` distingue `digital` de `presencial`; no hay tablas paralelas para cada canal.
5. **Estados como tabla, no enumeración.** `estado_reserva`, `estado_venta`, `estado_pago` son tablas con filas, referenciadas por clave foránea desde `reserva`, `venta` y `pago` respectivamente — ampliar un estado es un `INSERT`, no una migración de esquema.
6. **Atributo `material` desde el arranque**, en `material` y referenciado desde `producto`, requerido por la búsqueda por voz (decisión ya justificada en Parte I).
7. **`tabla_medida` existe desde el inicio**, aunque su caso de uso consumidor (recomendación de talla) quede fuera del alcance de esta fase.
8. **Auditoría y borrado lógico transversales.** Toda tabla de negocio incluye `creado_por`, `creado_en` y `activo`; el borrado es siempre lógico (`activo = false`), nunca `DELETE` físico, salvo en `movimiento_inventario`, `reserva_historial` y tablas de detalle históricas, que por definición nunca se borran ni se desactivan. *Verificado contra el DDL real: la mayoría de las tablas de catálogo, organización y transaccionales aplican el trío completo o el subconjunto que les corresponde (p. ej. `producto` tiene los tres campos; `cliente` y `reserva` solo `creado_en`, por no requerir baja lógica propia; `empleado` y `producto_variante` solo `activo`). No es una inconsistencia: la decisión fija el criterio, y cada tabla aplica de él únicamente lo que su ciclo de vida de negocio necesita.*

**Regla adicional de implementación:** el recálculo de `costo_promedio_post` y la actualización de `cantidad_fisica`/`cantidad_reservada` se ejecutan en la capa de servicio (`inventario.service`), dentro de una transacción de base de datos — deliberadamente **no** mediante triggers de PostgreSQL, para que la regla de negocio sea auditable y verificable con pruebas unitarias de Python, y explicable durante la defensa sin depender de lógica oculta en el motor de base de datos.

**Distribución de tablas por paquete** (mismo agrupamiento que en la Parte I / consolidado, ahora como diagrama de clases de datos):

| Paquete | Tablas (61 + 2 vistas) |
|---|---|
| Seguridad | `rol`, `permiso`, `rol_permiso`, `usuario`, `usuario_rol` |
| Organización | `ciudad`, `sucursal`, `horario_sucursal`, `empleado`, `cliente` |
| Catálogo | `categoria`, `talla`, `color`, `material`, `temporada`, `coleccion`, `producto`, `producto_variante`, `producto_imagen`, `tabla_medida`, `favorito` |
| Abastecimiento | `proveedor`, `producto_proveedor`, `orden_compra`, `orden_compra_detalle`, `recepcion`, `recepcion_detalle` |
| Inventario | `stock`, `tipo_movimiento`, `movimiento_inventario`, `transferencia`, `transferencia_detalle` |
| Reservas | `estado_reserva`, `reserva`, `reserva_detalle`, `reserva_historial` |
| Ventas | `estado_venta`, `promocion`, `promocion_alcance`, `venta`, `venta_detalle`, `carrito`, `carrito_detalle`, `devolucion`, `devolucion_detalle` |
| Pagos | `metodo_pago`, `estado_pago`, `pago`, `transaccion_pasarela` |
| Entregas | `zona_envio`, `regla_tarifa_envio`, `direccion_cliente`, `envio` |
| Probador | `activo_probador`, `probador_generacion`, `sesion_probador` |
| Inteligencia | `historial_navegacion`, `consulta_voz`, `recomendacion` |
| Núcleo (`core`) | `bitacora`, `notificacion` |
| Vistas de apoyo | `vw_inventario_consolidado`, `vw_ventas_detalle` |

**Relaciones clave del núcleo transaccional** (las que materializan las ocho decisiones de diseño): `producto (1) — (N) producto_variante`; `producto_variante (1) — (N) stock (N) — (1) sucursal`; `producto_variante (1) — (N) movimiento_inventario`; `reserva (1) — (N) reserva_detalle (N) — (1) producto_variante`; `venta (1) — (N) venta_detalle (N) — (1) producto_variante`; `venta (1) — (N) pago (1) — (0..1) transaccion_pasarela`; `producto_variante (1) — (0..1) activo_probador`. Cada una de estas relaciones se modela en Enterprise Architect como una asociación con multiplicidad explícita sobre las clases de entidad correspondientes.

**Diagramas construidos en Enterprise Architect.** Bajo `Model / FashionStore / F.T.3 - Diseno / Diseno de Datos`: 61 clases de entidad (todas las tablas del esquema, ninguna omitida) organizadas en 12 diagramas por paquete (`DD-01` Seguridad a `DD-11` Inteligencia y Núcleo, mismo agrupamiento que la tabla de distribución) más `DD-12`, el diagrama de relaciones clave del núcleo transaccional. Sobre `DD-12` se cargaron los **atributos reales completos** (nombre, tipo SQL, PK/FK) de las 21 entidades centrales — `usuario`, `cliente`, `sucursal`, `talla`, `color`, `categoria`, `material`, `producto`, `producto_variante`, `estado_reserva`, `reserva`, `reserva_detalle`, `estado_venta`, `venta`, `venta_detalle`, `estado_pago`, `pago`, `transaccion_pasarela`, `metodo_pago`, `activo_probador` — verificados palabra por palabra contra `fashionstore_esquema.sql`, junto con sus 24 relaciones con multiplicidad explícita. Las 40 tablas restantes (catálogos secundarios, detalle de documentos de abastecimiento/ventas/entregas, tablas de auditoría) están modeladas como clases con estereotipo `«entity»` en su diagrama de paquete correspondiente, sin desarrollar su lista de atributos en esta pasada — ese detalle exhaustivo de las 40 restantes es el trabajo pendiente marcado para la Fase 2 (ver cierre más abajo), ya que no aporta información nueva de diseño más allá de lo que ya fija el DDL.

---

## Cierre de la Fase 1 — Presentación 1 (05/09/2026)

### Qué queda listo

- **Perfil completo**: introducción, objetivos general y específicos, descripción del problema y alcance, con los datos reales del proyecto (sin contenido genérico ni de relleno).
- **Parte I completa**: fundamentación teórica de e-commerce, pasarelas de pago, deliverys, PUDS y UML, cada una conectada explícitamente a una decisión real del proyecto (no como teoría aislada).
- **Depuración de casos de uso, aprobada**: de 79 CU del consolidado a 42 CU de primer nivel + 6 comportamientos transversales `«include»`/`«extend»` correctamente modelados, con la justificación metodológica de cada cambio.
- **F.T.1 Requisitos completo**: catálogo de 7 actores, tabla de priorización, 42 fichas de detalle de CU (precondición, flujo básico, flujo alternativo, postcondición, relaciones), 4 prototipos de interfaz de las pantallas más críticas, y el diagrama de casos de uso construido en Enterprise Architect (`CU-01`, 55 elementos, 58 relaciones).
- **F.T.2 Análisis completo**: análisis de arquitectura, clases de análisis (entidad/control/frontera) para los 6 flujos más representativos, catálogo completo de clases de entidad/control/frontera, y verificación de bajo acoplamiento/alta cohesión de los 13 paquetes — con 4 diagramas construidos en Enterprise Architect (`AN-01` a `AN-04`).
- **F.T.3 Diseño hasta 3.3 completo**: arquitectura lógica (4 capas por paquete) y física (`DIS-01`, diagrama de despliegue real con 8 nodos: clientes, Railway, Vercel, Cloudinary, pasarelas, Groq), diseño de los casos de uso críticos con 2 diagramas de secuencia reales (`DIS-02`, `DIS-03`, con mensajes ordenados y numerados) y 3 diagramas de estado reales verificados contra el esquema (`DIS-04` a `DIS-06`), y diseño de datos completo: **las 61 tablas modeladas como clases** en 12 diagramas por paquete (`DD-01` a `DD-11`) más el diagrama de relaciones clave del núcleo transaccional (`DD-12`) con 21 entidades centrales llevando sus atributos reales completos (tipo SQL, PK/FK) y 24 relaciones con multiplicidad, todo verificado línea por línea contra `fashionstore_esquema.sql`. Durante esta verificación se corrigieron nombres de estado que en un borrador inicial no coincidían con el esquema real (p. ej. `en_prueba`/`completada` en vez de nombres aproximados).
- **Modelo de Enterprise Architect estructurado** en `Model / FashionStore /` con un sub-paquete por flujo de trabajo (F.T.1, F.T.2, F.T.3) y 23 diagramas en total, listo para que la Fase 2 continúe sobre la misma base sin reestructurar nada.

### Qué falta para la Fase 2 (13/09/2026)

Según el reparto ya fijado en el consolidado técnico y la guía de contenidos, la Fase 2 debe entregar el **resto del Diseño detallado** que este documento no cubre, más **API y seguridad**:
- Diagrama de clases de diseño completo (no solo las clases de datos: también las clases de control y frontera con sus operaciones, atributos privados/públicos y visibilidad — hoy solo están nombradas, sin su interfaz operacional).
- Diagramas de comunicación/colaboración con numeración de mensajes (complementando los 2 diagramas de secuencia ya construidos en 3.2).
- Diagrama de componentes (los 13 paquetes como componentes desplegables, con sus interfaces).
- Refinar `DIS-01` (despliegue) con artefactos específicos por nodo y especificaciones de protocolo más detalladas que la vista de alto nivel de esta fase.
- Completar los atributos reales de las 40 tablas restantes del diseño de datos (hoy modeladas solo con su nombre y estereotipo `«entity»`, sin columnas cargadas) — son en su mayoría catálogos secundarios y tablas de detalle cuyo DDL ya existe en `fashionstore_esquema.sql`, falta trasladarlo a la herramienta.
- Los 2 diagramas de navegación (móvil y back office), hoy documentados solo en texto en la sección 3.2.
- Diseño de la API REST (contratos de entrada/salida por endpoint, códigos de estado, convenciones) y diseño de seguridad (flujo JWT completo, control de acceso por permiso, manejo de secretos).
- Diagrama de actividades para al menos los flujos con más de una decisión relevante (ej. atención de reserva con liberación parcial, confirmación de pago con reintento).

No se toca todavía la Fase 3 (implementación, pruebas sobre CU y conclusiones, 20/09) ni la Fase 4 (preparación de la defensa, 22/09), como se acordó al iniciar este trabajo.
