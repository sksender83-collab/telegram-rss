# Використовуємо офіційний Python 3.10
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render підхоплює $PORT
CMD ["uvicorn", "rss_server:app", "--host", "0.0.0.0", "--port", "$PORT"]
