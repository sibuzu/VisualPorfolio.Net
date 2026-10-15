#!/bin/sh
set -eu

mkdir -p /app/data/reports
chmod 1777 /app/data/reports
exec runuser -u strategyreport -- "$@"
