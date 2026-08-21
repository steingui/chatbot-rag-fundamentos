#!/bin/bash
exec python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 10000
