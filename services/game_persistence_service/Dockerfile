FROM python:3.11-slim

WORKDIR /app

COPY services/game_persistence_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/game_persistence_service /app/services/game_persistence_service

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.game_persistence_service.main"]
