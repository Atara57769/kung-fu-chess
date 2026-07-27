FROM python:3.11-slim

WORKDIR /app

COPY services/matchmaking_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/matchmaking_service /app/services/matchmaking_service

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.matchmaking_service.main"]
