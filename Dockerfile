FROM python:3.12-slim AS builder

# Evita archivos .pyc y buffers raros
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y \
    # Instala herramientas básicas para compilar librerías nativas de Python
    build-essential \
    libpq-dev \
    curl \  
    # Elimina paquetes descargados que ya no se necesitan
    && apt-get clean \

    # Borra el caché del índice de paquetes para reducir el tamaño de la imagen
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt