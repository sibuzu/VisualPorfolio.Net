#!/bin/sh
set -eu

mkdir -p /app/data/db /app/data/reports
exec "$@"
