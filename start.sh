#!/bin/sh

echo "[ENTRYPOINT] USE_TLS=$USE_TLS"
echo "[ENTRYPOINT] CERT_FILE=$CERT_FILE"
echo "[ENTRYPOINT] KEY_FILE=$KEY_FILE"

if [ "$USE_TLS" = "true" ]; then
    if [ ! -f "$CERT_FILE" ]; then
        echo "[ERROR] TLS certificate file not found: $CERT_FILE"
        exit 1
    fi

    if [ ! -f "$KEY_FILE" ]; then
        echo "[ERROR] TLS key file not found: $KEY_FILE"
        exit 1
    fi

    echo "[INFO] TLS files found. Starting with HTTPS..."
    exec uvicorn main:app --host 0.0.0.0 --port 3083 --ssl-keyfile "$KEY_FILE" --ssl-certfile "$CERT_FILE"
else
    echo "[INFO] Starting without TLS (HTTP only)..."
    exec uvicorn main:app --host 0.0.0.0 --port 3083
fi
