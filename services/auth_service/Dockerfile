FROM python:3.11-slim

WORKDIR /app

COPY services/auth_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/auth_service /app/services/auth_service

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.auth_service.main"]
