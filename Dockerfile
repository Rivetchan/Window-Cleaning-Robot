FROM python:3.11-slim

LABEL maintainer="rivet@robot.com"
LABEL description="Robot Pembersih Kaca Backend API"
LABEL version="2.1.0"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs data

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Jakarta
ENV PYTHONPATH=/app

EXPOSE 7080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7080"]