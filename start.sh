#!/bin/bash
# Запуск FastAPI через uvicorn на Render
uvicorn rss_server:app --host 0.0.0.0 --port $PORT
