# Orchestration

Poetry project for authoring Airflow DAGs for the data platform.

## Quick start

```bash
poetry env use python3.12
poetry install
```

## Layout

- `dags/` Airflow DAG definitions
- `lib/` custom Airflow Python modules (operators, hooks, shared helpers)

## Deploy to local Airflow

From repo root:

```bash
make airflow-dags-sync
make airflow-install
```

`airflow-dags-sync` creates/updates the `airflow-local-dags` ConfigMap from files in `orchestration/dags`.

## Notes

- This project is configured with `package-mode = false` because DAG authoring does not require building a Python package.
