#!/bin/bash
# Безкінечний цикл для автоматичного перезапуску скрипта у разі падіння
while true; do
    python3 rss_server.py
    echo "Скрипт впав. Перезапуск через 5 секунд..."
    sleep 5
done
