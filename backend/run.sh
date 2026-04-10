#!/bin/bash

cd "$(dirname "$0")"

# Ativar virtualenv
source ../.venv/bin/activate

cd api

set -a
source ../.env
set +a

export PYTHONPATH="${PYTHONPATH}:$(pwd)/../agents"

uvicorn main:app --host 0.0.0.0 --port 8101 --reload