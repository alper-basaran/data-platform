# TODO: This DAG is intended for local testing and validation of Airflow's integration with Kubernetes. It is not meant for production use.
# TODO: This is a minimal smoke-test DAG to validate that Airflow is correctly set up and can run a KubernetesPodOperator task. 
# TODO: Abstract away secret passing, and return code handling into dedicated libraries
# TODO: Ideally, pod returns 0, 1 or 2, where 0 = success, 1 = retryable error, 2 = non-retryable error. This allows us to leverage Airflow's retry mechanism for transient issues.

from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret


SECRETS_SCOPE = "ns-secrets"
K8S_NAMESPACE = "pipelines"
IMAGE_TAG = "job-github-extract"
IMAGE_VERSION = "latest"

secrets = [
    Secret(deploy_type="env", deploy_target="APPCONF__S3_ENDPOINT_URL",secret=SECRETS_SCOPE,key="MINIO_ENDPOINT_URL"),
    Secret(deploy_type="env", deploy_target="APPCONF__S3_ACCESS_KEY",secret=SECRETS_SCOPE,key="MINIO_EXTRACT_USER"),
    Secret(deploy_type="env", deploy_target="APPCONF__S3_SECRET_KEY",secret=SECRETS_SCOPE,key="MINIO_EXTRACT_TOKEN")
]

with DAG(
    dag_id="github_data_model",
    description="A DAG to run the GitHub data ingestion and modeling jobs on a daily basis",
    schedule="@daily",
    start_date=datetime(2026, 3, 1),
    catchup=False,
    tags=["smoke-test"],
) as dag:
    start = EmptyOperator(task_id="start")
    run_extract = KubernetesPodOperator(
        task_id="run_extract",
        name="run-extract",
        namespace=K8S_NAMESPACE,
        image=f"{IMAGE_TAG}:{IMAGE_VERSION}",
        image_pull_policy="Never",
        secrets=secrets,
        in_cluster=True,
        get_logs=True,
        is_delete_operator_pod=True,
    )
    done = EmptyOperator(task_id="done")

    start >> run_extract >> done
