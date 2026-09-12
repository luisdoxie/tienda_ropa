## 4.1 Selección de plataforma de software

La selección de herramientas no fue libre: el enunciado del examen fija el stack
obligatorio (Python con FastAPI en el backend, Angular en la web, Flutter en el móvil,
PostgreSQL como motor de base de datos y despliegue en la nube). Lo que sí se decidió en
este flujo de trabajo fueron las versiones concretas, las bibliotecas de apoyo y los
proveedores de servicio. La tabla siguiente registra lo que efectivamente quedó instalado
y corriendo, no una intención.

| Capa | Tecnología | Versión | Justificación de la elección |
|---|---|---|---|
| Lenguaje backend | Python | 3.13.0 | Versión fijada en `.python-version` en la raíz del backend para que el entorno local y el de Railway resuelvan la misma, y no aparezcan diferencias de comportamiento entre desarrollo y producción. |
| Framework web | FastAPI | 0.115.6 | Genera la especificación OpenAPI automáticamente a partir de los tipos, lo que da documentación viva de la API sin mantenerla aparte, y valida las entradas antes de que lleguen a la lógica de negocio. |
| ORM | SQLAlchemy | 2.0.36 | Estilo declarativo 2.0 con tipado, y control explícito de la transacción, necesario para las operaciones sobre stock. |
| Validación | Pydantic | 2.13.5 | Integrado con FastAPI. Se usan tres esquemas por entidad (`Crear`, `Actualizar`, `Respuesta`) para que la forma de entrada nunca sea la misma que la de salida. |
| Migraciones | Alembic | 1.14.0 | Único camino autorizado para cambiar el esquema. Ninguna tabla se crea ni se altera a mano. |
| Driver de base de datos | psycopg | 3.2.3 | Versión 3, no psycopg2. Como Railway inyecta `DATABASE_URL` en el formato de psycopg2, `core/config.py` normaliza el prefijo a `postgresql+psycopg://` al arrancar, en vez de exigir que la variable de entorno se escriba distinto en cada entorno. |
| Servidor ASGI | uvicorn | 0.34.0 | Servidor de producción en Railway y servidor de desarrollo con recarga automática en local. |
| Hash de contraseñas | bcrypt | 4.2.1 | Se usa la biblioteca directamente y **no** `passlib`. `passlib` está sin mantenimiento activo y su adaptador rompe con las versiones actuales de `bcrypt`; usarlo habría agregado una capa intermedia frágil sobre una función que se invoca en tres líneas. |
| Tokens | PyJWT | 2.10.1 | Firma y verificación de los tokens de acceso y de refresco. |
| Límite de tráfico | slowapi | 0.1.9 | Aplicado a los endpoints públicos del catálogo, que son los expuestos a tráfico anónimo. |
| Base de datos | PostgreSQL | 17.11 | Se aprovechan columnas generadas, vistas y el bloqueo de fila `SELECT FOR UPDATE`, del que depende la corrección del control de stock. |
| Framework web (cliente) | Angular | 22.1 | Back office y tienda pública. |
| Componentes de interfaz | PrimeNG | 22.1 | Tablas densas, formularios y diálogos ya resueltos, adecuados para las pantallas de gestión. |
| Lenguaje de la web | TypeScript | 6.0.2 | Tipado sobre los contratos de la API. |
| Framework móvil | Flutter / Dart | SDK ^3.12.1 | Una sola base de código, y acceso nativo a la cámara, que el probador virtual necesita. |
| Imágenes | Cloudinary | SDK 1.41.0 | Almacenamiento y transformación de imágenes de producto y de los assets del probador. El `api_secret` no sale nunca del backend. |
| IA de lenguaje | Groq | API | Interpretación de la búsqueda por voz y de los reportes en lenguaje natural. |
| IA generativa | Vertex AI (`google-genai`) | 2.20.0 | Modo generativo del probador virtual. |
| Pasarelas de pago | Libélula y PayPal | Sandbox | Ambas en modo de prueba, sin movimiento de dinero real. |
| Despliegue del backend | Railway | — | Sin Docker: se construye con Nixpacks a partir de `requirements.txt` y `.python-version`. |
| Despliegue de la web | Vercel | — | Publicación del build de Angular. |

**Cumplimiento del requisito de no usar localhost.** El enunciado exige que el sistema
corra en la nube. Ambos despliegues están activos y verificados:

- API: `https://tiendaropa-production-b36a.up.railway.app` — `GET /health` responde 200.
- Web: `https://tienda-ropa-ruby.vercel.app` — la raíz y la ruta pública `/catalogo`
  responden 200.

El endpoint `/health` no devuelve un "ok" fijo: ejecuta un `SELECT 1` contra la base real
y responde 503 si la base no contesta. Railway usa ese endpoint como health check y no
promueve un despliegue a "en línea" hasta que responda 200, de modo que un despliegue con
la base caída no llega a publicarse.

## 4.2 Implementación de la arquitectura del sistema principal

### Estructura en capas

El backend se implementó como un **monolito modular en capas**. La decisión fue deliberada:
un conjunto de microservicios habría multiplicado la complejidad de despliegue sin ningún
beneficio a la escala de este sistema, mientras que un monolito sin división interna habría
hecho imposible sostener la separación entre paquetes que exige el modelo de análisis.

Cada paquete de negocio tiene exactamente los mismos cinco archivos, y cada uno pertenece a
una sola capa:

| Archivo | Capa | Responsabilidad |
|---|---|---|
| `models.py` | Persistencia | Modelos SQLAlchemy: tablas, columnas y relaciones. |
| `schemas.py` | Contrato | Esquemas Pydantic de entrada y salida (`Crear`, `Actualizar`, `Respuesta`). |
| `repository.py` | Acceso a datos | Consultas. Único lugar donde se construyen sentencias sobre las tablas del paquete. |
| `service.py` | Negocio | Reglas, validaciones y coordinación de transacciones. |
| `router.py` | Presentación | Endpoints FastAPI: rutas, códigos de estado y dependencias de permiso. |

Sobre esa estructura se hacen cumplir cuatro reglas:

1. **El router no toca la base de datos.** Su trabajo termina en traducir HTTP a una llamada al service.
2. **El service no sabe de HTTP.** No conoce códigos de estado ni objetos de petición; lanza excepciones de dominio que la capa de presentación traduce.
3. **Un paquete nunca consulta las tablas de otro.** Si `ventas` necesita descontar stock, llama a `inventario.service.registrar_movimiento()`; no ejecuta un `UPDATE` sobre la tabla `stock`. Ésta es la regla que sostiene el bajo acoplamiento verificado en el análisis de paquetes.
4. **Todo CRUD hereda de `core/crud_base.py`.** No se repite código de alta, baja, modificación y listado en trece lugares.

### El núcleo compartido

El paquete `core` no es un paquete de negocio: es el núcleo que los demás reutilizan. Agrupa
14 módulos, entre ellos `config.py` (configuración y variables de entorno), `database.py`
(sesión y sesión por petición), `crud_base.py`, `deps.py` (dependencias de FastAPI, incluida
la paginación), `exceptions.py` (excepciones de dominio y sus manejadores), `security.py`
(hash, tokens y verificación de permisos), `storage.py` (Cloudinary) y `rate_limit.py`.

`crud_base.py` define la clase genérica `CRUDBase[ModeloT, CrearSchemaT, ActualizarSchemaT]`
con las operaciones `listar`, `obtener`, `crear`, `actualizar` y `desactivar`. La última es
la que implementa el **borrado lógico**: ninguna tabla de negocio sufre un `DELETE` físico;
se marca el campo `activo` en falso y las consultas lo filtran. Así se conserva la
trazabilidad histórica, que en ventas e inventario es obligatoria.

### Raíz de composición

`app/main.py` es el único punto donde el sistema se ensambla. Ahí se crea la aplicación
FastAPI, se registran los routers de los trece paquetes en orden de dependencia, y se montan
los aspectos transversales: CORS restringido a los orígenes declarados en configuración,
el limitador de tráfico, los manejadores de excepciones de dominio y el endpoint `/health`.
Ningún paquete se importa a sí mismo dentro de otro para "engancharse": el ensamblado es
explícito y está en un solo archivo.

### Volumen implementado

| Paquete | Líneas | Responsabilidad |
|---|---|---|
| `catalogo` | 2366 | Productos, variantes, imágenes, catálogos simples y catálogo público. |
| `ventas` | 1660 | Venta presencial y compra digital, carrito y promociones. |
| `inventario` | 1110 | Stock por sucursal, movimientos y transferencias. |
| `probador` | 908 | Vestidor virtual: assets, anclajes, sesiones y generación. |
| `inteligencia` | 906 | Búsqueda por voz, historial y recomendador. |
| `abastecimiento` | 835 | Proveedores, órdenes de compra y recepciones. |
| `seguridad` | 802 | Usuarios, roles, permisos y autenticación. |
| `pagos` | 789 | Pasarelas, estados de pago y conciliación. |
| `reservas` | 678 | Reserva de prendas y atención de prueba en sucursal. |
| `organizacion` | 677 | Ciudades, sucursales, empleados y horarios. |
| `entregas` | 579 | Zonas por anillo, direcciones y envíos. |
| `reportes` | 303 | Consultas agregadas para dashboards. |
| `core` | 754 | Núcleo compartido (no es paquete de negocio). |

La API expuesta suma **193 operaciones HTTP sobre 126 rutas**, agrupadas en 38 etiquetas
funcionales. El esquema de datos consta de **61 tablas base y 2 vistas**, creadas por
**17 migraciones de Alembic**; el número de tablas coincide exactamente con el de la
especificación de referencia `docs/fashionstore_esquema.sql`.

### Transacciones sobre stock

Toda operación que afecta existencias corre dentro de una transacción, y la implementación
va más allá de envolverla en un `commit`. `inventario.service.registrar_movimiento()`
obtiene la fila de stock con bloqueo (`SELECT FOR UPDATE` de PostgreSQL, vía
`stock_repo.obtener_o_crear_bloqueado`) antes de calcular el nuevo saldo, de modo que dos
movimientos concurrentes sobre la misma variante y sucursal no puedan pisarse el saldo.
Antes de aplicar el movimiento valida dos invariantes: que el stock físico no quede negativo
y que no quede stock reservado sin respaldo físico.

La función acepta además un parámetro `commit=False`, que usan las operaciones de otros
paquetes que registran varios movimientos como una sola unidad — por ejemplo
`abastecimiento.crear_recepcion()` con varias líneas, o una transferencia entre sucursales.
Si una línea falla, ninguna de las anteriores queda aplicada. Cuando el tipo de movimiento
afecta el costo, se recalcula el costo promedio ponderado con la cantidad y el costo del
ingreso concreto.

### Deuda técnica identificada

Una auditoría interna del código realizada el 09/09/2026 sobre las tres capas
(`docs/auditoria_2026-09-09.txt`) dejó registrados hallazgos que siguen abiertos y que se
documentan acá por honestidad metodológica, no como logros pendientes de maquillar:

- **Condición de carrera en la resolución de pagos** (`pagos/service.py`): la idempotencia está pensada y documentada, pero le falta el bloqueo de fila que sí tiene `inventario.registrar_movimiento()`. Dos confirmaciones concurrentes de la misma pasarela podrían duplicar el efecto de un pago.
- **Falta de guardia contra dos pagos activos** sobre la misma venta: un doble clic o un reintento de red puede iniciar dos pagos para la misma venta.
- **Desvío del patrón por capas en varios routers**: algunos routers llaman directamente al repositorio en vez de pasar por el service, contra la regla 1 declarada arriba.

Los dos primeros son los candidatos naturales a resolver en la siguiente iteración, por
bloqueo explícito de fila, antes de cualquier demostración con pagos reales.

## 4.3 Implementación de la arquitectura del subsistema

Dos paquetes se apartan del patrón CRUD que comparten los demás y constituyen subsistemas
propios, con dependencias externas y flujos asincrónicos. Son los que dan al proyecto su
carácter diferencial.

### Subsistema de probador virtual

Implementado en `backend/app/probador/`, sostiene tres entidades: `ActivoProbador` (el
overlay de la prenda con sus puntos de anclaje), `ProbadorGeneracion` (cada imagen producida
en modo generativo) y `SesionProbador` (el registro de uso, que alimenta al recomendador y a
los reportes).

Opera en **dos modos**, según lo acotado en el alcance del proyecto — solo prendas
superiores masculinas: poleras, camisas y chamarras.

- **Modo espejo (obligatorio, exclusivo de la app Flutter).** Usa `google_mlkit_pose_detection` sobre la cámara del dispositivo: detecta la pose del usuario y superpone el overlay de la prenda alineándolo con los puntos de anclaje marcados previamente por el encargado. El procesamiento ocurre en el teléfono; el backend solo provee el asset validado y registra la sesión.
- **Modo generativo (opcional).** Envía la foto del cliente y la prenda a Vertex AI. Como la generación tarda, no bloquea la respuesta HTTP: el endpoint devuelve de inmediato la generación — cacheada si ya existía una equivalente — y el trabajo real corre en segundo plano mediante `BackgroundTasks`, consultándose después por su identificador.

Dos decisiones de implementación merecen registro. Primero, la **validación de los assets**:
`_validar_png_con_alfa()` abre el archivo con Pillow y verifica que sea un PNG con canal
alfa real, sin confiar en la extensión ni en el `content-type` declarados por el cliente —
un overlay sin transparencia arruinaría la superposición, y un archivo con extensión
falseada es un vector de ataque conocido. Segundo, la función `recomendar_talla()` estima
medidas a partir de estatura y peso mediante una **heurística declarada como tal**: se
documenta explícitamente que no reemplaza una medición real, para que ni el usuario ni el
tribunal la interpreten como una prestación que el sistema no tiene.

### Subsistema de inteligencia

Implementado en `backend/app/inteligencia/`, sostiene `ConsultaVoz`, `HistorialNavegacion`
y `Recomendacion`, y expone tres capacidades:

- **Búsqueda por voz** (`buscar_por_voz`): el texto transcripto se envía a Groq, que lo convierte en filtros estructurados del catálogo (categoría, color, talla, género). La implementación **degrada de forma controlada**: si la clave de Groq no está configurada o el servicio falla, la consulta cae a una búsqueda por texto plano en vez de devolver un error. La funcionalidad se degrada, no se cae.
- **Recomendador** (`obtener_recomendaciones`): trabaja por reglas sobre el historial de navegación, las sesiones del probador y las compras previas del cliente. Selecciona variantes candidatas y luego las colapsa por producto, para que el carrusel no muestre cinco veces la misma prenda en distinto color.
- **Reportes por voz** (`generar_reporte_por_voz`): traduce una pregunta en lenguaje natural a una consulta agregada sobre el paquete de reportes.

### Relación con el sistema principal

Ninguno de los dos subsistemas rompe el aislamiento entre paquetes. `probador` obtiene las
prendas llamando a `catalogo.service` y valida identidad contra `seguridad`; `inteligencia`
consulta los services de `catalogo`, `inventario`, `organizacion`, `probador`, `reportes`,
`seguridad` y `ventas`. En ningún caso acceden a las tablas de otro paquete.

### Diagrama de componentes (COMP-01)

El diagrama `COMP-01` representa los doce paquetes de negocio y el núcleo `core` como
componentes con estereotipo `«subsystem»`, junto con los servicios externos. Sus relaciones
**no fueron dibujadas por criterio estético**: se derivaron una por una de los `import`
reales entre paquetes del código fuente, de modo que el diagrama describe el sistema
construido y no una intención de diseño.

Esa derivación arrojó **33 dependencias directas** entre los doce paquetes. Dibujarlas todas
produce un diagrama correcto pero ilegible: treinta y tres líneas entre doce cajas forman una
maraña en la que no se distingue ninguna relación concreta, y un diagrama que no se puede
leer no cumple su función.

La solución no fue recortar líneas por conveniencia. Como el grafo resultó **acíclico** —lo
que de por sí confirma empíricamente la regla de no admitir dependencias circulares entre
paquetes—, admite una **reducción transitiva**: el subconjunto mínimo de aristas cuya
clausura transitiva es idéntica a la del grafo completo. Calculada sobre el grafo real, las
33 dependencias se reducen a **13 aristas sin perder ninguna relación de alcanzabilidad**.
Si `ventas` depende de `inventario`, el diagrama lo sigue mostrando por el camino
`ventas → reservas → inventario`.

Conviene ser explícito sobre lo que esa reducción sí sacrifica: **una arista del diagrama no
significa necesariamente una llamada directa**. Quién llama a quién de forma directa es lo
que registra la matriz completa más abajo; el diagrama muestra la estructura y el orden de
capas.

[[IMAGEN:COMP-01.png|Figura COMP-01. Diagrama de componentes del backend en siete niveles. Las trece dependencias mostradas son la reducción transitiva del grafo real de treinta y tres; todas apuntan hacia abajo, lo que verifica que no existen ciclos.]]

Los componentes quedan ordenados en siete niveles. Cada uno depende solo de niveles
inferiores, nunca de uno superior ni de un par, y por eso en el diagrama **toda dependencia
apunta hacia abajo**:

| Nivel | Nombre | Componentes |
|---|---|---|
| 6 | Inteligencia | `inteligencia` |
| 5 | Explotación | `reportes`, `pagos`, `entregas` |
| 4 | Transacción | `ventas` |
| 3 | Operación | `reservas`, `abastecimiento` |
| 2 | Recursos | `inventario`, `probador` |
| 1 | Maestros | `catalogo`, `organizacion` |
| 0 | Base | `seguridad` |

La matriz siguiente conserva el detalle completo que el diagrama simplifica: las 33
dependencias directas, tal como aparecen en los `import` del código.

| Componente | Depende directamente de |
|---|---|
| `seguridad` | — (no depende de ningún paquete de negocio) |
| `organizacion` | `seguridad` |
| `catalogo` | `seguridad` |
| `inventario` | `catalogo`, `organizacion` |
| `probador` | `catalogo`, `seguridad` |
| `abastecimiento` | `catalogo`, `inventario`, `organizacion` |
| `reservas` | `catalogo`, `inventario`, `organizacion`, `seguridad` |
| `ventas` | `catalogo`, `inventario`, `organizacion`, `reservas`, `seguridad` |
| `pagos` | `organizacion`, `ventas` |
| `entregas` | `seguridad`, `ventas` |
| `reportes` | `inventario`, `probador`, `reservas`, `ventas` |
| `inteligencia` | `catalogo`, `inventario`, `organizacion`, `probador`, `reportes`, `seguridad`, `ventas` |

Las dependencias hacia servicios externos también se verificaron contra el código y sí se
dibujan todas, porque son pocas y cada una identifica un punto de integración:
`catalogo` y `probador` usan Cloudinary a través de `core/storage.py`, `pagos` es el único
que habla con las pasarelas, `inteligencia` el único que consume Groq y `probador` el único
que invoca Vertex AI. El núcleo `core` concentra el acceso a PostgreSQL mediante SQLAlchemy
y psycopg.

Los clientes Angular y Flutter no se incluyen en COMP-01: su relación con la API y los
protocolos involucrados ya están representados en el diagrama de despliegue `DIS-01`, y
agregarlos acá solo habría restado legibilidad al repetir información existente.
