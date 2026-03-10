FROM python:3.12-slim

RUN pip install --no-cache-dir dbt-postgres

WORKDIR /app

COPY dbt/ /app/

ENV DBT_PROFILES_DIR=/app

CMD ["dbt", "build", "--profiles-dir", "/app", "--select", "staging"]
