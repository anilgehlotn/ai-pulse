#!/bin/sh
# Start the API. Platforms like Render run this without a shell wrapper, so the sequence lives here.
# set -e: stop if seeding fails. exec: uvicorn becomes PID 1 and receives stop signals.
set -e
python -m app.seed --if-empty
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
