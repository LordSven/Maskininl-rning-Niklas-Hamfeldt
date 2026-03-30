#!/usr/bin/env bash

echo "Starting app..."
gunicorn app:server --bind 0.0.0.0:$PORT