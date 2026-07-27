FROM python:3.11-slim

WORKDIR /app

COPY services/rooms_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY server /app/server
COPY services/rooms_service /app/services/rooms_service

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.rooms_service.main"]
