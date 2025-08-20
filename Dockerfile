FROM public.ecr.aws/docker/library/python:3.12-slim as builder

COPY ./poetry.lock ./pyproject.toml ./private_key.pem ./private_key_cloudfront.pem /code/
COPY ./src /code/src
COPY ./.env /code/.env

WORKDIR /code
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root && \
    pip uninstall -y poetry


# runner
FROM public.ecr.aws/docker/library/python:3.12-slim AS runner
RUN apt-get update && apt-get install -y --no-install-recommends curl bash && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/code/src:${PYTHONPATH}"

COPY --from=builder /code /code
COPY --from=builder /usr/local /usr/local

# (If your app uses uvicorn --reload, make sure it watches "src" from /code)
# HEALTHCHECK assumes APP_PORT is set from the environment
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD ["curl","-f","http://localhost:${APP_PORT}/healthcheck"]

RUN groupadd -r app && useradd -r -g app app && \
    chmod -R 755 /code && chown -R app:app /code
USER app

WORKDIR /code
CMD ["/bin/sh","-c","python main.py migrate && python main.py run"]
