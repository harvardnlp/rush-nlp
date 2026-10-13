#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

.venv/bin/python site.py
exec .venv/bin/python -m http.server 4000 --bind 127.0.0.1 --directory docs
