FROM python:3.12-slim
WORKDIR /app
# Fail fast at startup unless SECRET_KEY is passed in (e.g. docker run -e SECRET_KEY=...).
ENV APP_ENV=production

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user. /data is where docker-compose mounts the SQLite volume;
# creating it here owned by appuser means a new named volume starts out writable.
RUN useradd --create-home appuser && mkdir /data && chown -R appuser /app /data
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
