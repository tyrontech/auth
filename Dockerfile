# =========================================================================
# Etapa 1: Builder
# =========================================================================
FROM python:3.12-slim AS builder

# Evita archivos .pyc y buffers raros
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias necesarias solo para compilar wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

# Instalar dependencias Python en un prefijo aislado
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =========================================================================
# Etapa 2: Runtime
# =========================================================================
FROM python:3.12-slim

# Variables de entorno estándar
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar solo dependencias de runtime necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias ya compiladas
COPY --from=builder /install /usr/local

# Copiar código fuente
COPY src src
ENV PYTHONPATH=/app/src

# =========================================================================
# Copiar y configurar Entrypoint
# =========================================================================
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# =========================================================================
# Exponer puerto
# =========================================================================
EXPOSE 8000

# =========================================================================
# Entrypoint + Comando por defecto
# =========================================================================
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "src/main.py"]