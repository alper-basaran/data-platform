FROM python:3.12-slim

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false 
RUN poetry install --no-root --only main --no-interaction --no-ansi -vv


COPY src/ /app/src/

RUN poetry install --only-root --no-interaction --no-ansi -vv

CMD ["app_main"]
