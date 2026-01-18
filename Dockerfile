FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY scripts /app/scripts

RUN sed -i 's/\r$//' /app/scripts/docker_entrypoint.sh \
    && sed -i '1s/^\xEF\xBB\xBF//' /app/scripts/docker_entrypoint.sh \
    && chmod +x /app/scripts/docker_entrypoint.sh

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[test]

EXPOSE 8000

CMD ["/app/scripts/docker_entrypoint.sh"]
