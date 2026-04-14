# LH Mapeo — API FastAPI

API REST para la aplicación de mapeo de plantas de La Hornilla. Migrada de Flask a FastAPI v3.0.

---

## Estructura

```
API_FASTAPI/
├── main.py               # App principal, CORS, registro de routers
├── auth.py               # JWT helpers: tokens, verificación, dependency
├── config.py             # Variables de entorno (DB, JWT, Cloud SQL)
├── db.py                 # Conexión PyMySQL con soporte Cloud Run / local
├── requirements.txt      # Dependencias
├── Dockerfile            # Imagen python:3.11-slim, puerto 8080
└── routers/
    ├── auth.py           # Login, refresh, cambio de clave/sucursal, registro
    ├── usuarios.py       # Perfil, sucursales y apps por usuario (admin)
    ├── cuarteles.py      # CRUD cuarteles + filtros por sucursal/ceco/variedad
    ├── hileras.py        # CRUD hileras + creación en lote
    ├── plantas.py        # CRUD plantas
    ├── variedades.py     # CRUD variedades
    ├── especies.py       # CRUD especies
    ├── tipoplanta.py     # Tipos de planta (solo lectura para el app)
    ├── registromapeo.py  # Sesiones de mapeo: crear, avanzar, finalizar, progreso
    ├── registros.py      # Registros individuales de plantas mapeadas
    ├── estadocatastro.py # Estados de catastro (solo lectura)
    └── opciones.py       # Sucursales del usuario, datos generales
```

---

## Stack

| Componente | Versión |
|---|---|
| Python | 3.11 |
| FastAPI | 0.111.0 |
| Uvicorn | 0.30.0 |
| PyMySQL | 1.1.1 |
| python-jose[cryptography] | 3.3.0 |
| passlib[bcrypt] | 1.7.4 |
| python-dotenv | 1.0.1 |

---

## Configuración

### Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `CLOUD_SQL_HOST` | IP instancia Cloud SQL | 34.41.120.220 |
| `CLOUD_SQL_USER` | Usuario DB | UserApp |
| `CLOUD_SQL_PASSWORD` | Contraseña DB | — |
| `CLOUD_SQL_DB` | Nombre DB | lahornilla_base_normalizada |
| `CLOUD_SQL_CONNECTION_NAME` | Para socket Unix en Cloud Run | gestion-la-hornilla:us-central1:gestion-la-hornilla |
| `JWT_SECRET_KEY` | Clave JWT | Inicio01* |
| `K_SERVICE` | Detecta entorno Cloud Run automáticamente | — |

La conexión a DB usa **socket Unix** cuando está en Cloud Run (`K_SERVICE` presente), IP directa en local.

### Correr en local

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

Documentación interactiva disponible en `http://localhost:8080/docs`.

---

## Autenticación

JWT con HS256. Dos tokens:

- **access_token** — expira en 12 horas. Se envía en header `Authorization: Bearer <token>`.
- **refresh_token** — expira en 30 días. Se usa para renovar el access_token sin re-login.

El claim `"type": "refresh"` diferencia los refresh tokens de los access tokens.

Todos los endpoints excepto `/api/auth/login` y `/api/auth/register` requieren autenticación.

---

## Endpoints

### Auth — `/api/auth`

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/login` | Login con usuario/clave. Retorna access_token + refresh_token + datos usuario |
| POST | `/refresh` | Renueva access_token usando refresh_token en header Bearer |
| POST | `/register` | Registrar usuario nuevo |
| POST | `/cambiar-clave` | Cambiar clave del usuario autenticado |
| POST | `/cambiar-sucursal` | Cambiar sucursal activa del usuario autenticado |

**Respuesta de login:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "usuario": "jperez",
  "nombre_completo": "Juan Pérez González",
  "id_sucursal": 3,
  "sucursal_nombre": "El Monte",
  "id_rol": 3,
  "id_perfil": 1
}
```

---

### Usuarios — `/api/usuarios` _(requiere perfil admin id_perfil=3)_

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Listar todos los usuarios |
| GET | `/perfil` | Perfil del usuario autenticado |
| PUT | `/perfil` | Actualizar nombre/correo del perfil |
| GET | `/sucursal` | Sucursal activa del usuario (id) |
| GET | `/sucursal-activa` | Sucursal activa del usuario |
| POST | `/sucursal-activa` | Actualizar sucursal activa |
| GET | `/sucursales` | Todas las sucursales (admin) |
| GET | `/apps` | Todas las apps (admin) |
| GET | `/{id}/sucursales-permitidas` | Sucursales asignadas a un usuario |
| POST | `/{id}/sucursales-permitidas` | Asignar sucursales a un usuario |
| DELETE | `/{id}/sucursales-permitidas` | Remover sucursales de un usuario |
| GET | `/{id}/apps-permitidas` | Apps asignadas a un usuario |
| POST | `/{id}/apps-permitidas` | Asignar apps a un usuario |
| DELETE | `/{id}/apps-permitidas` | Remover apps de un usuario |

---

### Cuarteles — `/api/cuarteles`

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Todos los cuarteles |
| GET | `/activos` | Activos con nombre de ceco y sucursal |
| GET | `/catastro-finalizado` | Solo cuarteles con id_estadocatastro=2 |
| GET | `/sucursal/{id}` | Cuarteles activos de una sucursal |
| GET | `/ceco/{id}` | Cuarteles de un ceco |
| GET | `/variedad/{id}` | Cuarteles de una variedad |
| GET | `/buscar/{nombre}` | Búsqueda por nombre (LIKE) |
| GET | `/{id}` | Cuartel por ID |
| POST | `/` | Crear cuartel |
| PUT | `/{id}` | Actualizar cuartel |
| DELETE | `/{id}` | Soft delete (id_estado=0, fecha_baja) |

**Campos cuartel:** id, id_ceco, nombre, id_variedad, superficie, ano_plantacion, dsh, deh, id_propiedad, id_portainjerto, subdivisionesplanta, id_estado, fecha_baja, id_estadoproductivo, n_hileras, id_estadocatastro, id_tiposubdivision

---

### Hileras — `/api/hileras`

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Todas las hileras |
| GET | `/con-cuartel` | Hileras con nombre de cuartel |
| GET | `/cuartel/{id}` | Hileras de un cuartel |
| GET | `/cuartel/{id}/con-info` | Hileras de un cuartel con nombre |
| GET | `/numero/{n}` | Hileras por número |
| GET | `/{id}` | Hilera por ID |
| POST | `/` | Crear hilera individual |
| POST | `/agregar-multiples` | Crear N hileras en lote para un cuartel |
| PUT | `/{id}` | Actualizar hilera |
| DELETE | `/{id}` | Eliminar hilera |

---

### Plantas — `/api/plantas`

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Todas las plantas |
| GET | `/hilera/{id}` | Plantas de una hilera |
| GET | `/ubicacion/{ubicacion}` | Búsqueda por ubicación (LIKE) |
| GET | `/numero/{n}` | Plantas por número |
| GET | `/{id}` | Planta por ID |
| POST | `/` | Crear planta |
| PUT | `/{id}` | Actualizar planta |
| DELETE | `/{id}` | Eliminar planta |

---

### Registros de Mapeo (sesiones) — `/api/registromapeo`

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Todas las sesiones |
| GET | `/estadisticas` | Totales por estado |
| GET | `/temporada/{id}` | Sesiones de una temporada |
| GET | `/cuartel/{id}` | Sesiones de un cuartel |
| GET | `/estado/{id}` | Sesiones por estado |
| GET | `/{id}` | Sesión por ID |
| GET | `/{id}/progreso` | Progreso por hilera de una sesión |
| POST | `/` | Crear sesión de mapeo |
| PUT | `/{id}` | Actualizar sesión |
| PUT | `/{id}/finalizar` | Finalizar sesión (estado=2, fecha_termino) |
| PUT | `/{id}/hilera/{id}/estado` | Estado calculado de una hilera |
| DELETE | `/{id}` | Eliminar sesión |

**Body para crear sesión:**
```json
{
  "id_temporada": 1,
  "id_cuartel": 5,
  "fecha_inicio": "2025-08-01",
  "id_estado": 1
}
```

**Estados de sesión:** 1=en progreso, 2=finalizado, 3=pausado

---

### Registros individuales — `/api/registros`

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Todos los registros |
| GET | `/evaluador/{id}` | Por evaluador |
| GET | `/planta/{id}` | Por planta |
| GET | `/hilera/{id}` | Por hilera (con info de planta y tipo) |
| GET | `/mapeo/{id}` | Por sesión de mapeo |
| GET | `/{id}` | Registro por ID |
| POST | `/` | Crear registro (UUID generado en backend) |
| PUT | `/{id}` | Actualizar registro |
| DELETE | `/{id}` | Eliminar registro |

**Body para crear registro:**
```json
{
  "id_planta": 123,
  "id_tipoplanta": 2,
  "imagen": null,
  "id_mapeo": "uuid-de-la-sesion"
}
```

---

### Otros routers

| Prefijo | Descripción |
|---|---|
| `/api/variedades` | CRUD variedades (nombre, id_especie, id_forma, id_color) |
| `/api/especies` | CRUD especies (nombre, caja_equivalente) |
| `/api/tipoplanta` | Solo lectura: tipos de planta por empresa o búsqueda |
| `/api/estadocatastro` | Solo lectura: estados de catastro |
| `/api/opciones` | Sucursales del usuario, datos generales (labores, unidades, tipoCecos) |

---

## Base de datos

**Instancia:** gestion-la-hornilla (Cloud SQL, MySQL, us-central1)
**DB:** lahornilla_base_normalizada

### Tablas principales

| Tabla | Descripción |
|---|---|
| `general_dim_usuario` | Usuarios de la app |
| `general_dim_sucursal` | Sucursales |
| `general_dim_ceco` | Centros de costo |
| `general_dim_cuartel` | Cuarteles (campo agrícola) |
| `general_dim_hilera` | Hileras dentro de un cuartel |
| `general_dim_planta` | Plantas dentro de una hilera |
| `general_dim_variedad` | Variedades de plantas |
| `general_dim_especie` | Especies |
| `mapeo_dim_tipoplanta` | Tipos de planta para mapeo |
| `mapeo_dim_estadocatastro` | Estados de catastro |
| `mapeo_fact_registromapeo` | Sesiones de mapeo (por cuartel) |
| `mapeo_fact_registro` | Registros individuales (por planta) |
| `usuario_pivot_sucursal_usuario` | Sucursales permitidas por usuario |
| `usuario_pivot_app_usuario` | Apps permitidas por usuario |

**Acceso a app Mapeo:** el usuario debe tener `id_app=5` en `usuario_pivot_app_usuario`.

---

## Despliegue

Cloud Run (us-central1), conectado a Cloud SQL via socket Unix.
Repo: pendiente de configurar GitHub Actions para CI/CD.
