# Auth Service

Authentication service built with FastAPI: Google OAuth2 login and JWT access/refresh tokens.

## Features

- Google OAuth2 login with CSRF protection (`state`)
- JWT access tokens and refresh tokens with rotation
- PostgreSQL for users, OAuth connections and refresh tokens
- OAuth `state` stored in memory (dev) or Redis (production)
- Configuration validated at startup (database, Redis, settings)

## Architecture

Hexagonal architecture. Dependencies point inwards, towards the domain.

```
src/
├── main.py            # FastAPI app, lifespan, CORS, /health
├── container.py       # Composition root + dependency providers
├── config/            # Settings (.env) and startup validation
├── domain/            # Entities and ports (interfaces)
├── application/       # Use cases and DTOs
├── infrastructure/    # Database, repositories, JWT, Redis, Google
└── presentation/      # API routes and HTTP dependencies
```

- `domain` knows nothing about FastAPI or SQLAlchemy.
- `application` orchestrates use cases through ports.
- `infrastructure` implements those ports.
- `container.py` is the only place where everything is wired together.

## Requirements

- Docker and Docker Compose, or Python 3.12+ with PostgreSQL and Redis
- Google OAuth credentials (client ID and secret)

## Configuration

Create a `.env` file in the project root:

```env
# Database
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=auth_db

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback/google

# JWT
SECRET_KEY=change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
APP_ENV=development
DEBUG=true

# OAuth state store: memory | redis
STATE_STORE_BACKEND=memory
# REDIS_URL=redis://redis:6379/0
```

`.env` and `keys/` are git-ignored: they never leave your machine.

## Running

With Docker:

```bash
docker compose up --build
```

Locally:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

The API is available at `http://localhost:8000`. Interactive docs at `/docs` when `DEBUG=true`.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Service health check |
| GET | `/api/auth/login/google` | Redirects to the Google consent screen |
| GET | `/api/auth/callback/google` | Google callback; creates/logs in the user and returns tokens |
| POST | `/api/auth/refresh` | Exchanges a refresh token for a new token pair |

## Authentication flow

1. The client calls `/api/auth/login/google` and is redirected to Google.
2. Google redirects back to `/api/auth/callback/google` with a `code` and the `state`.
3. The service validates the `state`, exchanges the code for a Google token and reads the user profile.
4. The user and the OAuth connection are created if they do not exist yet.
5. The response contains an access token and a refresh token.
6. When the access token expires, the client calls `/api/auth/refresh`. The old refresh token is revoked and a new pair is issued.
