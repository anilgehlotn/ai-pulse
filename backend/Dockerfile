FROM python:3.12-slim
WORKDIR /app
# Fail fast at startup unless SECRET_KEY is passed in (e.g. docker run -e SECRET_KEY=...).
ENV APP_ENV=production

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The start script must be executable inside the image, whatever the file mode was on disk.
# sed strips Windows line endings in case the repo was checked out on Windows.
RUN sed -i 's/\r$//' start.sh && chmod 755 start.sh

# Run as an unprivileged user. /data is where docker-compose mounts the SQLite volume;
# creating it here owned by appuser means a new named volume starts out writable.
RUN useradd --create-home appuser && mkdir /data && chown -R appuser /app /data
USER appuser

# PORT is set by hosting platforms such as Render; 8000 otherwise.
EXPOSE 8000
# Seeds an empty database, then starts the API. Platforms must not override this command.
CMD ["./start.sh"]
