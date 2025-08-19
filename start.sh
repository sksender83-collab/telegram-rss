#!/bin/bash

# Безкінечний цикл для автоматичного перезапуску
while true; do
    echo "Запускаю rss_server.py..."
    python3 rss_server.py
    echo "rss_server.py завершився, перезапускаю через 5 секунд..."
    sleep 5
done
