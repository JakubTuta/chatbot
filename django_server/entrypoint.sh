#!/bin/sh
set -e

python manage.py migrate --noinput

exec daphne \
    --websocket-max-message-size 8388608 \
    --websocket-max-frame-size 8388608 \
    -b 0.0.0.0 -p 8000 django_server.asgi:application
