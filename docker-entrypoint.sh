#!/bin/bash
# Salir inmediatamente si un comando falla
set -e

# --- Definir rutas para las llaves desde variables de entorno ---
PRIVATE_KEY_PATH="${PRIVATE_KEY_PATH:-./keys/ed25519_private.pem}"
PUBLIC_KEY_PATH="${PUBLIC_KEY_PATH:-./keys/ed25519_public.pem}"

# --- Comprobar si la llave privada NO existe ---
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo "🔑 Llave privada no encontrada. Generando un nuevo par de llaves Ed25519..."

    # Crear el directorio si no existe
    mkdir -p ./keys

    # Generar la llave privada
    openssl genpkey -algorithm Ed25519 -out "$PRIVATE_KEY_PATH"

    # Extraer la llave pública de la privada
    openssl pkey -in "$PRIVATE_KEY_PATH" -pubout -out "$PUBLIC_KEY_PATH"

    # Ajustar permisos para que solo el propietario pueda leer la llave privada
    chmod 600 "$PRIVATE_KEY_PATH"

    echo "✅ Llaves generadas correctamente."
else
    echo "🔑 Llaves encontradas. Omitiendo generación."
fi

# --- Ejecutar el comando principal del contenedor ---
# "$@" toma todos los argumentos pasados al script y los ejecuta.
# Por ejemplo, el 'command' de tu docker-compose.yml.
exec "$@"
