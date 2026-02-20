# Auth Service — Documentación de presentación

## Resumen ejecutivo

**Auth Service** es un microservicio de autenticación que permite a aplicaciones web y móviles autenticar usuarios mediante **Google OAuth 2.0** y gestionar sesiones con **JWT** (access + refresh tokens). Está pensado para integrarse como backend de autenticación en proyectos que necesiten “Login con Google” y renovación de tokens de forma segura.

---

## Objetivos del proyecto

- Ofrecer **autenticación con Google** (OAuth 2.0) lista para integrar.
- Emitir **JWT** (access token y refresh token) con rotación de refresh tokens.
- Mantener una **arquitectura limpia** (dominio, aplicación, infraestructura, presentación) para facilitar pruebas y evolución.
- Ser **configurable** (variables de entorno) y **desplegable** con PostgreSQL y, opcionalmente, Redis para el estado OAuth.

---

## Stack tecnológico

| Componente        | Tecnología                          |
|------------------|-------------------------------------|
| API              | **FastAPI**                         |
| Base de datos    | **PostgreSQL** (async con asyncpg)  |
| ORM              | **SQLAlchemy 2.0** (async)          |
| OAuth 2.0        | **Authlib** + **Google OAuth**      |
| Tokens           | **JWT** (HS256)                     |
| Estado OAuth     | **Memoria** o **Redis**             |
| Configuración    | **Pydantic Settings** (.env)        |
| Servidor         | **Uvicorn**                         |

---

## Arquitectura

El proyecto sigue una **arquitectura en capas** con inyección de dependencias y un **Composition Root** centralizado.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTACIÓN (API)                           │
│  FastAPI · Endpoints /api/auth/* · Dependencias (deps)          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     APLICACIÓN (Use cases)                       │
│  AuthenticateWithGoogle · RefreshTokens · DTOs · Excepciones     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     DOMINIO                                      │
│  Entidades (User, OAuthConnection, RefreshToken…) · Puertos      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     INFRAESTRUCTURA                              │
│  Repositorios SQLAlchemy · GoogleOAuthProvider · JWT · Redis      │
└─────────────────────────────────────────────────────────────────┘
```

- **Dominio**: entidades y contratos (puertos) sin dependencias de frameworks.
- **Aplicación**: casos de uso, DTOs y reglas de negocio.
- **Infraestructura**: implementaciones concretas (DB, OAuth, JWT, Redis).
- **Presentación**: controladores HTTP que delegan en use cases inyectados por el **Container**.

El **Container** (`container.py`) actúa como Composition Root: crea engine DB, state store, JWT, proveedor OAuth y factories de repositorios y use cases. La API solo conoce los puertos y las funciones de dependencia expuestas por el container.

---

## Flujos principales

### 1. Login con Google

1. Cliente llama a **GET** `/api/auth/login/google`.
2. El servidor genera un `state` (anti-CSRF), lo guarda en el state store (memoria o Redis) y redirige al usuario a la pantalla de consentimiento de Google.
3. El usuario autoriza en Google; Google redirige a **GET** `/api/auth/callback/google?code=…&state=…`.
4. El servidor valida `state`, intercambia `code` por tokens con Google, obtiene el perfil del usuario y:
   - Crea o actualiza el **User** y la **OAuthConnection** en la base de datos.
   - Genera **access_token** y **refresh_token** (JWT), persiste el refresh token (hash) y devuelve **AuthResponse** (user + tokens).

### 2. Renovación de tokens (refresh)

1. Cliente envía **POST** `/api/auth/refresh` con `{ "refresh_token": "…" }`.
2. El servidor valida el JWT, busca el refresh token (por hash) en base de datos, comprueba que no esté revocado y que no haya expirado.
3. Emite un nuevo par **access_token** + **refresh_token** (rotación) y puede invalidar el refresh token anterior según la política del use case.

---

## API expuesta

| Método | Ruta                      | Descripción                                      |
|--------|---------------------------|--------------------------------------------------|
| GET    | `/api/auth/login/google`  | Redirige a Google OAuth (inicio de login).      |
| GET    | `/api/auth/callback/google` | Callback de Google; devuelve user + tokens.   |
| POST   | `/api/auth/refresh`       | Intercambia refresh token por nuevos tokens.   |
| GET    | `/health`                 | Health check (status + env).                     |
| GET    | `/docs`                   | Swagger UI (solo si `DEBUG=true`).               |
| GET    | `/redoc`                  | ReDoc (solo si `DEBUG=true`).                    |

---

## Estructura del proyecto

```
auth/
├── src/
│   ├── main.py                 # FastAPI app, lifespan, CORS, rutas
│   ├── container.py            # Composition Root, ContainerManager, deps
│   ├── config/
│   │   ├── settings.py         # Variables de entorno (Pydantic)
│   │   └── validation.py      # Validación de configuración
│   ├── domain/
│   │   ├── entities/          # User, OAuthConnection, RefreshToken…
│   │   └── ports/             # Interfaces (repositorios, OAuth, JWT, state store)
│   ├── application/
│   │   ├── use_cases/         # AuthenticateWithGoogle, RefreshTokens
│   │   ├── dtos/              # AuthResponse, RefreshRequest…
│   │   └── exceptions.py
│   ├── infrastructure/
│   │   ├── database/          # Engine, session, modelos SQLAlchemy
│   │   ├── repositories/      # Implementaciones de repositorios
│   │   ├── providers/         # GoogleOAuthProvider
│   │   └── services/          # JWT, state store (memoria/Redis)
│   └── presentation/
│       └── api/v1/endpoints/  # auth.py (router de auth)
├── docs/
│   └── PRESENTACION.md        # Este documento
├── requirements.txt
└── .env.example               # (recomendado) Ejemplo de variables
```

---

## Configuración y despliegue

- **Variables críticas** (ejemplo en `.env`):
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REDIRECT_URI` (p. ej. `http://localhost:8000/api/auth/callback/google`)
  - `DB_*` (host, port, user, password, name) para PostgreSQL
  - `SECRET_KEY` para JWT (en producción usar valor seguro)
  - Opcional: `STATE_STORE_BACKEND=redis` y `REDIS_URL` para estado OAuth en Redis

- **Arranque** (desde la raíz del proyecto, con `src` como working directory o `PYTHONPATH`):
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```
  O bien `python main.py` si está configurado en `main.py`.

- **Requisitos**: Python 3.x, PostgreSQL, y Redis solo si se usa state store en Redis.

---

## Seguridad

- **State OAuth**: se usa un `state` aleatorio almacenado en memoria o Redis para evitar ataques CSRF en el flujo OAuth.
- **Refresh tokens**: se almacenan hasheados en base de datos; se soporta rotación en el endpoint de refresh.
- **JWT**: access token con expiración corta; refresh token con expiración larga (p. ej. 7 días), configurable.
- **CORS**: orígenes permitidos configurables vía `ALLOWED_ORIGINS`.
- **Documentación**: Swagger/ReDoc solo habilitados cuando `DEBUG=true`.

---

## Próximos pasos posibles

- Añadir más proveedores OAuth (GitHub, Microsoft, etc.) implementando el mismo puerto `IOAuthProvider`.
- Endpoint de logout (revocación de refresh token).
- Rate limiting y auditoría de intentos de login/refresh.
- Métricas y trazabilidad (OpenTelemetry, Prometheus).
- Documentar un `.env.example` y un docker-compose mínimo (app + PostgreSQL + Redis opcional).

---

## Resumen

**Auth Service** es un backend de autenticación listo para integrar, con **Google OAuth 2.0** y **JWT** (access + refresh), diseñado con **arquitectura en capas** y **Composition Root** para mantener el código testeable y extensible. La configuración se hace por entorno (`.env`) y se puede desplegar con PostgreSQL y, opcionalmente, Redis para el estado OAuth en entornos distribuidos.
