FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY core/ core/
COPY api/ api/
COPY coldguard_cli.py .
COPY data/raw/ data/raw/

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# Default: run the CLI help. Override with: uvicorn api.main:app --host 0.0.0.0
ENTRYPOINT ["python", "coldguard_cli.py"]
CMD ["--help"]
