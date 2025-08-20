FROM public.ecr.aws/docker/library/python:3.13-slim as builder

COPY ./poetry.lock ./pyproject.toml ./private_key.pem ./private_key_cloudfront.pem /code/
COPY ./src /code
COPY ./.env /code/.env

WORKDIR /code

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main --no-root && \
    pip uninstall -y poetry

# Second stage: runner
FROM public.ecr.aws/docker/library/python:3.13-slim AS runner

# Install runtime dependencies (using apt-get)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    bash && \
    apt-get install -y libpq-dev

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "/code/src:${PYTHONPATH}"

COPY --from=builder /code /code
COPY --from=builder /usr/local /usr/local

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 CMD ["curl", "-f", "http://localhost:${APP_PORT}/healthcheck"]

RUN groupadd -r app && useradd -r -g app app && \
    chmod -R 755 /code && chown -R app:app /code
USER app

WORKDIR /code
CMD ["/bin/sh", "-c", "python main.py migrate && python main.py run"]
