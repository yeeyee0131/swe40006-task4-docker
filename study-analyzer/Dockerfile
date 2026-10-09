FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home appuser

COPY analyzer.py .

USER appuser

ENTRYPOINT ["python", "/app/analyzer.py"]