FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY src/ ./src/
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists \
    && pip install --no-cache-dir -r requirements.txt
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"
EXPOSE 8080
CMD ["python", "src/server.py"]
