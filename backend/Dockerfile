FROM python:3.12-slim
WORKDIR /app
# Fail fast at startup unless SECRET_KEY is passed in (e.g. docker run -e SECRET_KEY=...).
ENV APP_ENV=production

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user that can only write to /app (the SQLite file lives there).
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
