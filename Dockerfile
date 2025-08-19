# Використовуємо Python 3.10
FROM python:3.10-slim

WORKDIR /app

# Копіюємо файли залежностей і встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту проєкту
COPY . .

# Expose порт (Render автоматично прокидує $PORT)
EXPOSE 10000

# Запуск FastAPI через uvicorn
CMD ["uvicorn", "rss_server:app", "--host", "0.0.0.0", "--port", "10000"]
