#!/bin/bash

cd "$(dirname "$0")"

set -a
source ../agents_and_backend/.env
set +a

export PYTHONPATH="${PYTHONPATH}:$(pwd)/../agents_and_backend/src"

uvicorn main:app --host 0.0.0.0 --port 8102 --reload
