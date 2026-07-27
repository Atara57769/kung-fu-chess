FROM python:3.11-slim

WORKDIR /app

COPY services/game_server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/game_server /app/services/game_server

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.game_server.main"]
