FROM python:3.11-slim

WORKDIR /app

COPY services/websocket_gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/websocket_gateway /app/services/websocket_gateway

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.websocket_gateway.main"]
