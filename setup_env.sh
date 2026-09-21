#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3.11}"

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --no-deps kaggle-environments==1.32.2
.venv/bin/python -m pip install \
  jsonschema \
  'numpy>=2.0' \
  pytest \
  requests \
  termcolor

.venv/bin/python -c \
  'import kaggle_environments as ke; assert ke.__version__ == "1.32.2", ke.__version__; print(ke.__version__)'

