FROM apache/airflow:3.1.7

USER root

COPY orchestration /opt/airflow/orchestration

RUN chown -R airflow:0 /opt/airflow/orchestration \
    && chmod -R g+rwX /opt/airflow/orchestration

USER airflow
