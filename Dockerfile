# ---------------- Builder ----------------
FROM python:3.11-alpine as builder

# Install system deps needed to build Python packages
RUN apk add --no-cache build-base libffi-dev

WORKDIR /code

# Copy dependency files first (better caching)
COPY pyproject.toml poetry.lock ./

# Install Poetry (use modern version that supports package-mode)
RUN pip install --no-cache-dir pip==23.3.1 poetry==1.8.3 \
 && poetry export -f requirements.txt --output requirements.txt --without-hashes

# Install dependencies into /install (isolated folder)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
 && rm -f requirements.txt

# Copy project files
COPY alembic.ini .env ./src /code/


# ---------------- Runner ----------------
FROM python:3.11-alpine as runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/code/src:${PYTHONPATH}"

# Add non-root user
RUN addgroup -S app && adduser -S app -G app

WORKDIR /code

# Copy installed dependencies + app code
COPY --from=builder /install /usr/local
COPY --from=builder /code /code

# Extra tools
RUN apk add --no-cache curl

# Healthcheck (ensure your app actually binds to :80)
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:80/healthcheck || exit 1

USER app

# Run migrations then start the app
ENTRYPOINT ["sh", "-c", "python main.py migrate && exec python main.py run"]
