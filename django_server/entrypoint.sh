#!/bin/sh
set -e

python manage.py migrate --noinput
# 8 MiB covers the app's own limits (10K char message + 5 MB decoded image,
# ~6.7 MB base64) with headroom — without this, Daphne buffers an incoming
# frame fully in memory before ChatConsumer's own validation ever runs, so a
# malicious multi-GB frame is a free memory-exhaustion hit.
exec daphne \
    --websocket-max-message-size 8388608 \
    --websocket-max-frame-size 8388608 \
    -b 0.0.0.0 -p 8000 django_server.asgi:application
