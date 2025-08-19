FROM python:3.11-alpine as builder

# Install system dependencies for building wheels
RUN apk add --no-cache build-base libffi-dev

WORKDIR /code

# Copy only dependency files first (better for caching)
COPY pyproject.toml poetry.lock ./

# Install Poetry and export requirements
RUN pip install --no-cache-dir pip==23.3.1 poetry==1.6.1 \
 && poetry export -f requirements.txt --output requirements.txt --without-hashes

# Install project dependencies into a separate folder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
 && pip uninstall -y poetry \
 && rm -f requirements.txt

# Copy app source
COPY alembic.ini .env ./src /code/

# ---------------- Runner ----------------
FROM python:3.11-alpine as runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/code/src:${PYTHONPATH}"

# Create user
RUN addgroup -S app && adduser -S app -G app

WORKDIR /code

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local
COPY --from=builder /code /code

RUN apk add --no-cache curl

# Healthcheck (make sure your app actually runs on :80!)
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:80/healthcheck || exit 1

USER app

# Use a startup script instead of chaining in ENTRYPOINT
ENTRYPOINT ["sh", "-c", "python main.py migrate && exec python main.py run"]
