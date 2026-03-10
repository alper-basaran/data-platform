# TODO: Abstract away secret passing, and return code handling into a custom operator that can be reused across jobs.
# This will reduce boilerplate and ensure consistency in how we handle secrets and job outcomes across different DAGs and tasks.
# TODO: Ideally, pod returns 0, 1 or 2, where 0 = success, 1 = retryable error, 2 = non-retryable error. This allows us to leverage Airflow's retry mechanism for transient issues.

from datetime import datetime, timedelta, timezone
from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret


SECRETS_SCOPE = "ns-secrets"
K8S_NAMESPACE = "pipelines"
EXTRACT_IMAGE_TAG = "job-wikipedia-extract"
LOAD_IMAGE_TAG = "job-wikipedia-load"
TRANSFORM_IMAGE_TAG = "job-wikipedia-transform"
IMAGE_VERSION = "latest"
# TODO: Use versioning for image

with DAG(
    dag_id="wikipedia_page_activity_data_model",
    description="A DAG to run the Wikipedia data ingestion and modeling jobs on an hourly basis",
    schedule=timedelta(hours=1),
    start_date=datetime(2026, 3, 8, 0, 0, 0, tzinfo=timezone.utc),    
    end_date=datetime(2026, 3, 8, 0, 0, 0, tzinfo=timezone.utc) + timedelta(hours=3),# limit to 3 runs for demo
    max_active_runs=1,
    catchup=True,    
    tags=["API_SOURCE", "WIKIPEDIA"],
) as dag:
    
    start = EmptyOperator(task_id="start")
    
    run_extract = KubernetesPodOperator(
        task_id="run_extract",
        name="run-extract",
        namespace=K8S_NAMESPACE,
        image=f"{EXTRACT_IMAGE_TAG}:{IMAGE_VERSION}",
        image_pull_policy="Never",
        depends_on_past=True,
        secrets=[
            Secret(deploy_type="env", deploy_target="APPCONF__S3_ENDPOINT_URL",secret=SECRETS_SCOPE,key="MINIO_ENDPOINT_URL"),
            Secret(deploy_type="env", deploy_target="APPCONF__S3_ACCESS_KEY",secret=SECRETS_SCOPE,key="MINIO_EXTRACT_USER"),
            Secret(deploy_type="env", deploy_target="APPCONF__S3_SECRET_KEY",secret=SECRETS_SCOPE,key="MINIO_EXTRACT_TOKEN")
        ],
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=True,
        env_vars={
            "APPCONF__S3_BUCKET": "landing",
            "APPCONF__RAW_FOLDER": "wikipedia/events",
            "APPCONF__BASE_URL": "https://en.wikipedia.org/w/api.php",
            "APPCONF__INTERVAL_START": "{{ data_interval_start }}",
            "APPCONF__INTERVAL_END": "{{ data_interval_start + macros.timedelta(hours=1) }}",
            "APPCONF__API_PAGE_SIZE": "200",
            "APPCONF__MAX_PAGES_PER_INTERVAL": "50",
            "APPCONF__API_RATE_LIMIT_PER_SECOND": "5",
        }
    )
    
    run_load = KubernetesPodOperator(
        task_id="run_load",
        name="run-load",
        namespace=K8S_NAMESPACE,
        image=f"{LOAD_IMAGE_TAG}:{IMAGE_VERSION}",
        image_pull_policy="Never",
        depends_on_past=True,
        secrets=[
            Secret(deploy_type="env", deploy_target="APPCONF__S3_ENDPOINT_URL", secret=SECRETS_SCOPE, key="MINIO_ENDPOINT_URL"),
            Secret(deploy_type="env", deploy_target="APPCONF__S3_ACCESS_KEY", secret=SECRETS_SCOPE, key="MINIO_LOAD_USER"),
            Secret(deploy_type="env", deploy_target="APPCONF__S3_SECRET_KEY", secret=SECRETS_SCOPE, key="MINIO_LOAD_TOKEN"),
            Secret(deploy_type="env", deploy_target="APPCONF__PG_USER", secret=SECRETS_SCOPE, key="PG_LOAD_USER"),
            Secret(deploy_type="env", deploy_target="APPCONF__PG_PASSWORD", secret=SECRETS_SCOPE, key="PG_LOAD_PW"),
        ],
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=True,
        env_vars={
            "APPCONF__S3_BUCKET": "landing",
            "APPCONF__RAW_FOLDER": "wikipedia/events",
            "APPCONF__INTERVAL_START": "{{ data_interval_start }}",
            "APPCONF__PG_HOST": "postgres.platform",
            "APPCONF__PG_PORT": "5432",
            "APPCONF__PG_DB": "wikipedia",
        },
    )

    run_transform = KubernetesPodOperator(
        task_id="run_transform",
        name="run-transform",
        namespace=K8S_NAMESPACE,
        image=f"{TRANSFORM_IMAGE_TAG}:{IMAGE_VERSION}",
        image_pull_policy="Never",
        depends_on_past=True,
        secrets=[
            Secret(deploy_type="env", deploy_target="DBT_PG_USER", secret=SECRETS_SCOPE, key="PG_DBT_USER"),
            Secret(deploy_type="env", deploy_target="DBT_PG_PASSWORD", secret=SECRETS_SCOPE, key="PG_DBT_PW"),
        ],
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=True,
        env_vars={
            "DBT_PG_HOST": "postgres.platform",
            "DBT_PG_PORT": "5432",
            "DBT_PG_DATABASE": "wikipedia",
            "DBT_PG_SCHEMA": "public",
            "DBT_SOURCE_SCHEMA": "public",
            "DBT_SOURCE_TABLE": "wikipedia_page_changes",
            "DBT_THREADS": "4",
        },
    )

    done = EmptyOperator(task_id="done")

    start >> run_extract >> run_load >> run_transform >> done
