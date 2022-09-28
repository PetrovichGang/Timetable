#! /usr/bin/env sh
set -e

cd /api
#exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000 app.app:app
exec uvicorn --host 0.0.0.0 --port 3000 app.app:app