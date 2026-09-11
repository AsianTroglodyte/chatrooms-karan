#!/usr/bin/env sh
set -e

flask db upgrade
gunicorn app:app --bind 0.0.0.0:8000
