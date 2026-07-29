FROM python:3.11-slim

WORKDIR /app

COPY services/observability_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/observability_service /app/services/observability_service

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["python", "-m", "services.observability_service.main"]
