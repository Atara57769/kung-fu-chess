FROM python:3.11-slim

WORKDIR /app

COPY services/api_gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/api_gateway /app/services/api_gateway

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.api_gateway.main"]
