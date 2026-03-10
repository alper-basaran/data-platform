# dbt - Wikipedia Page Activity Models

This dbt project transforms raw Wikipedia events from PostgreSQL using a staging layer:

- `staging`: cleaning and standardization of raw records.

## Model layout

- `models/staging/stg_wikipedia_page_events.sql`

## Source configuration

By default, source is read from:
- database: `wikipedia`
- schema: `public`
- table: `wikipedia_page_events`

If needed, override via env vars:

- `DBT_PG_HOST` (default: `localhost`)
- `DBT_PG_PORT` (default: `5432`)
- `DBT_PG_USER` (default: `dbt`)
- `DBT_PG_PASSWORD` (default: `dbtpassword`)
- `DBT_PG_DATABASE` (default: `wikipedia`)
- `DBT_PG_SCHEMA` (default: `public`)
- `DBT_SOURCE_SCHEMA` (default: `public`)
- `DBT_SOURCE_TABLE` (default: `wikipedia_page_events`)

## Run locally

From the `dbt/` folder:

```bash
export DBT_PROFILES_DIR=$(pwd)
dbt debug

dbt deps

dbt run --select staging+
dbt test --select staging+
```

## Run via Airflow (dockerized)

The DAG `wikipedia_page_activity_data_model` includes a `run_transform` task that runs dbt inside Kubernetes using image `job-wikipedia-transform:latest`.

The image is built from `dbt/Dockerfile` at repository root.

To refresh and load the image into kind:

```bash
make jobs-build-load
make airflow-dags-sync
```
