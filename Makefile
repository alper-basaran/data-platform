.PHONY: help create teardown airflow-db-init airflow-install airflow-dags-sync airflow-rbac-apply jobs-build-load jobs-build-load-force airflow-uninstall kubernetes minio-create postgres-create check-env

.DEFAULT_GOAL := help

ifneq (,$(wildcard .env))
include .env
endif

K8S_CLUSTER_NAME := data-platform
KIND_CONFIG := platform/cluster/kind-config.yaml
STORAGECLASS_MANIFEST := platform/cluster/storageclass.yaml
MINIO_MANIFEST := platform/minio/deployment.yaml
MINIO_EXTRACT_POLICY := platform/minio/minio-extract-policy.json
MINIO_LOAD_POLICY := platform/minio/minio-load-policy.json
POSTGRES_MANIFEST := platform/postgres/deployment.yaml
AIRFLOW_HELM_VALUES := platform/airflow/values.yaml
AIRFLOW_SA_MANIFEST := platform/airflow/serviceAccount.yaml
ORCHESTRATION_DAGS_DIR := orchestration/dags
AIRFLOW_DAGS_CONFIGMAP := airflow-local-dags
PLATFORM_NAMESPACE := platform
PIPELINES_NAMESPACE := pipelines
SECRETS_SCOPE := "ns-secrets"
WIKIPEDIA_EXTRACT_JOB_DIR := jobs/extract/wikipedia
WIKIPEDIA_EXTRACT_JOB_IMAGE := job-wikipedia-extract:latest
WIKIPEDIA_LOAD_JOB_DIR := jobs/load/wikipedia
WIKIPEDIA_LOAD_JOB_IMAGE := job-wikipedia-load:latest
WIKIPEDIA_TRANSFORM_JOB_IMAGE := job-wikipedia-transform:latest
DBT_PROJECT_DIR := dbt
MINIO_BUCKET := landing


# SECRET VALUES for DEMO - to be injected securely via a secret backend in CD pipeline
MINIO_ROOT_USER ?=
MINIO_ROOT_PW ?=
PG_ADMIN_USER ?=
PG_ADMIN_PW ?=
PG_LOAD_USER ?=
PG_LOAD_PW ?=
PG_DBT_USER ?=
PG_DBT_PW ?=
PG_MIGRATION_USER ?=
PG_MIGRATION_PW ?=
AIRFLOW_METADATA_USER ?=
AIRFLOW_METADATA_PASSWORD ?=
AIRFLOW_METADATA_HOST := postgres.$(PLATFORM_NAMESPACE)
AIRFLOW_METADATA_PORT := 5432
AIRFLOW_METADATA_DB ?=
AIRFLOW_METADATA_SSLMODE ?=
AIRFLOW_WEB_USER ?=
AIRFLOW_WEB_PW ?=
AIRFLOW_WEB_FIRST_NAME ?=
AIRFLOW_WEB_LAST_NAME ?=
AIRFLOW_WEB_EMAIL ?=
MINIO_EXTRACT_USER ?=
MINIO_EXTRACT_TOKEN ?=
MINIO_LOAD_USER ?=
MINIO_LOAD_TOKEN ?=
MINIO_ENDPOINT_URL := http://minio.$(PLATFORM_NAMESPACE):9000

REQUIRED_ENV_VARS := \
	MINIO_ROOT_USER MINIO_ROOT_PW \
	PG_ADMIN_USER PG_ADMIN_PW \
	PG_LOAD_USER PG_LOAD_PW \
	PG_DBT_USER PG_DBT_PW \
	PG_MIGRATION_USER PG_MIGRATION_PW \
	AIRFLOW_METADATA_USER AIRFLOW_METADATA_PASSWORD AIRFLOW_METADATA_DB AIRFLOW_METADATA_SSLMODE \
	AIRFLOW_WEB_USER AIRFLOW_WEB_PW AIRFLOW_WEB_FIRST_NAME AIRFLOW_WEB_LAST_NAME AIRFLOW_WEB_EMAIL \
	MINIO_EXTRACT_USER MINIO_EXTRACT_TOKEN MINIO_LOAD_USER MINIO_LOAD_TOKEN

export $(REQUIRED_ENV_VARS)

SECRET_ARGS := \
	--from-literal=MINIO_ROOT=$(MINIO_ROOT_USER) \
	--from-literal=MINIO_ROOT_PW=$(MINIO_ROOT_PW) \
	--from-literal=PG_USER=$(PG_ADMIN_USER) \
	--from-literal=PG_PASSWORD=$(PG_ADMIN_PW) \
	--from-literal=PG_LOAD_USER=$(PG_LOAD_USER) \
	--from-literal=PG_LOAD_PW=$(PG_LOAD_PW) \
	--from-literal=PG_MIGRATION_USER=$(PG_MIGRATION_USER) \
	--from-literal=PG_MIGRATION_PW=$(PG_MIGRATION_PW) \
	--from-literal=PG_AIRFLOW_USER=$(AIRFLOW_METADATA_USER) \
	--from-literal=PG_AIRFLOW_PW=$(AIRFLOW_METADATA_PASSWORD) \
	--from-literal=PG_AIRFLOW_DB=$(AIRFLOW_METADATA_DB) \
	--from-literal=PG_DBT_USER=$(PG_DBT_USER) \
	--from-literal=PG_DBT_PW=$(PG_DBT_PW) \
	--from-literal=MINIO_ENDPOINT_URL=$(MINIO_ENDPOINT_URL) \
	--from-literal=MINIO_EXTRACT_USER=$(MINIO_EXTRACT_USER) \
	--from-literal=MINIO_EXTRACT_TOKEN=$(MINIO_EXTRACT_TOKEN) \
	--from-literal=MINIO_LOAD_USER=$(MINIO_LOAD_USER) \
	--from-literal=MINIO_LOAD_TOKEN=$(MINIO_LOAD_TOKEN)	

help:
	@echo "Available targets:"
	@echo "  make create             Create local kind cluster and deploy platform components"
	@echo "  make kubernetes         Create local kind cluster, namespaces, and demo secrets"
	@echo "  make minio-create       Deploy and initialize MinIO in the platform namespace"
	@echo "  make postgres-create    Deploy Postgres in the platform namespace"
	@echo "  make teardown           Delete local kind cluster"
	@echo "  make jobs-build-load    Build and load Wikipedia extract/load/transform job images into kind"
	@echo "  make jobs-build-load-force  Force rebuild (no cache) and load Wikipedia extract/load/transform images"
	@echo "  make airflow-install    Install or upgrade Airflow Helm release"
	@echo "  make airflow-dags-sync  Sync local DAGs into Airflow ConfigMap"
	@echo "  make airflow-uninstall  Uninstall Airflow Helm release"
	
	@echo "URLS and credentials for accessing services from host after 'make create':"	
	@echo "   - Airflow UI: http://localhost:8080 (user: $(AIRFLOW_WEB_USER), pass: $(AIRFLOW_WEB_PW))"
	@echo "   - MinIO API: http://localhost:9000 (user: $(MINIO_ROOT_USER), pass: $(MINIO_ROOT_PW))"
	@echo "   - MinIO UI:  http://localhost:9001 (user: $(MINIO_ROOT_USER), pass: $(MINIO_ROOT_PW))"
	@echo "   - Postgres:  http://localhost:5432 (admin: $(PG_ADMIN_USER)/$(PG_ADMIN_PW), db: postgres)"
	@echo ""
	@echo "⚠️ Note: If any localhost port is already in use, update hostPort mappings in $(KIND_CONFIG) and recreate the kind cluster."

check-env:
	@missing=0; \
	for var in $(REQUIRED_ENV_VARS); do \
		if [ -z "$${!var}" ]; then \
			echo "❌ Missing required environment variable: $$var"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 1 ]; then \
		echo "ℹ️  Create a .env from .env.example and fill all required values."; \
		exit 1; \
	fi

create: check-env
	# KIND + bootstrap
	@$(MAKE) kubernetes
	
	
	# MINIO
	@$(MAKE) minio-create

	# POSTGRES
	@$(MAKE) postgres-create

	# JOB IMAGES (for Airflow KubernetesPodOperator)
	# @$(MAKE) jobs-build-load
	
	# AIRFLOW
	@$(MAKE) airflow-install	

	# DBT
	
	@echo ""
	@echo "✅ Platform is ready. Access services from host:"
	@echo "   - Airflow UI: http://localhost:8080 (user: $(AIRFLOW_WEB_USER), pass: $(AIRFLOW_WEB_PW))"
	@echo "   - MinIO API: http://localhost:9000 (user: $(MINIO_ROOT_USER), pass: $(MINIO_ROOT_PW))"
	@echo "   - MinIO UI:  http://localhost:9001 (user: $(MINIO_ROOT_USER), pass: $(MINIO_ROOT_PW))"
	@echo "   - Postgres:  localhost:5432 (admin: $(PG_ADMIN_USER)/$(PG_ADMIN_PW), db: postgres)"
	@echo ""
	@echo "ℹ️ Note: If any localhost port is already in use, update hostPort mappings in $(KIND_CONFIG) and recreate the kind cluster."


kubernetes: check-env
	# KIND cluster
	@echo "⏳ Creating kind cluster '$(K8S_CLUSTER_NAME)'..."
	kind delete cluster --name $(K8S_CLUSTER_NAME) || true
	kind create cluster --name $(K8S_CLUSTER_NAME) --config $(KIND_CONFIG)
	@echo "⏳ Applying ephemeral StorageClass..."
	kubectl apply -f $(STORAGECLASS_MANIFEST) || true

	# Namespaces & Secrets
	@echo "⏳ Creating secrets for platform namespace..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	kubectl create namespace $(PLATFORM_NAMESPACE) || true

	# SECRETS: For demonstration purposes only
	# In prod setup, a secret backend like HashiCorp Vault or AWS Secrets Manager needs to be used to manage secrets securely.
	kubectl -n $(PLATFORM_NAMESPACE) create secret generic $(SECRETS_SCOPE) $(SECRET_ARGS) || true

	kubectl create namespace $(PIPELINES_NAMESPACE) || true
	kubectl -n $(PIPELINES_NAMESPACE) create secret generic $(SECRETS_SCOPE) $(SECRET_ARGS) || true


minio-create:
	@echo "⏳ Creating minio deployment in cluster '$(K8S_CLUSTER_NAME)'..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	kubectl apply -f $(MINIO_MANIFEST) -n $(PLATFORM_NAMESPACE)
	@echo "⏳ Waiting for MinIO to be ready..."
	@until kubectl -n $(PLATFORM_NAMESPACE) get pods -l app=minio -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; do \
		echo "⏳ MinIO is not ready yet. Waiting..."; \
		sleep 10; \
	done
	@echo "⏳ Copying MinIO extract policy into pod..."
	kubectl -n $(PLATFORM_NAMESPACE) exec -i deployment/minio -- /bin/sh -c 'cat > /tmp/minio-extract-policy.json' < $(MINIO_EXTRACT_POLICY)
	@echo "⏳ Copying MinIO load policy into pod..."
	kubectl -n $(PLATFORM_NAMESPACE) exec -i deployment/minio -- /bin/sh -c 'cat > /tmp/minio-load-policy.json' < $(MINIO_LOAD_POLICY)
	@echo "⏳ Initializing MinIO users, policy, and bucket..."
	kubectl -n $(PLATFORM_NAMESPACE) exec -it deployment/minio -- /bin/sh -c '\
		/usr/bin/mc alias set minio http://localhost:9000 $(MINIO_ROOT_USER) $(MINIO_ROOT_PW) && \
		/usr/bin/mc mb minio/$(MINIO_BUCKET) && \
		/usr/bin/mc admin user add minio $(MINIO_EXTRACT_USER) $(MINIO_EXTRACT_TOKEN) && \
		/usr/bin/mc admin policy create minio extract-policy /tmp/minio-extract-policy.json && \
		/usr/bin/mc admin policy attach minio extract-policy --user $(MINIO_EXTRACT_USER) && \
		/usr/bin/mc admin user add minio $(MINIO_LOAD_USER) $(MINIO_LOAD_TOKEN) && \
		/usr/bin/mc admin policy create minio load-policy /tmp/minio-load-policy.json && \
		/usr/bin/mc admin policy attach minio load-policy --user $(MINIO_LOAD_USER)'
	@echo "✅ MinIO setup complete. MinIO should be accessible at http://localhost:9001"


postgres-create:
	@echo "⏳ Creating postgres deployment..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	kubectl apply -f $(POSTGRES_MANIFEST) -n $(PLATFORM_NAMESPACE)
	@echo "✅ Postgres available inside cluster at postgres.$(PLATFORM_NAMESPACE):5432"


jobs-build-load:
	@echo "⏳ Building and loading Wikipedia extract/load/transform job images..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	@echo "⏳ Building $(WIKIPEDIA_EXTRACT_JOB_IMAGE) from $(WIKIPEDIA_EXTRACT_JOB_DIR)"
	docker build -t "$(WIKIPEDIA_EXTRACT_JOB_IMAGE)" "$(WIKIPEDIA_EXTRACT_JOB_DIR)"
	@echo "⏳ Loading $(WIKIPEDIA_EXTRACT_JOB_IMAGE) into kind cluster $(K8S_CLUSTER_NAME)"
	kind load docker-image "$(WIKIPEDIA_EXTRACT_JOB_IMAGE)" --name $(K8S_CLUSTER_NAME)
	@echo "⏳ Building $(WIKIPEDIA_LOAD_JOB_IMAGE) from $(WIKIPEDIA_LOAD_JOB_DIR)"
	docker build -t "$(WIKIPEDIA_LOAD_JOB_IMAGE)" "$(WIKIPEDIA_LOAD_JOB_DIR)"
	@echo "⏳ Loading $(WIKIPEDIA_LOAD_JOB_IMAGE) into kind cluster $(K8S_CLUSTER_NAME)"
	kind load docker-image "$(WIKIPEDIA_LOAD_JOB_IMAGE)" --name $(K8S_CLUSTER_NAME)
	@echo "⏳ Building $(WIKIPEDIA_TRANSFORM_JOB_IMAGE) from repository root Docker context"
	docker build -t "$(WIKIPEDIA_TRANSFORM_JOB_IMAGE)" -f "$(DBT_PROJECT_DIR)/Dockerfile" .
	@echo "⏳ Loading $(WIKIPEDIA_TRANSFORM_JOB_IMAGE) into kind cluster $(K8S_CLUSTER_NAME)"
	kind load docker-image "$(WIKIPEDIA_TRANSFORM_JOB_IMAGE)" --name $(K8S_CLUSTER_NAME)
	@echo "✅ Wikipedia extract/load/transform job images built and loaded"


jobs-build-load-force:
	@echo "⏳ Force rebuilding and loading Wikipedia extract/load/transform job images (no cache)..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	@echo "⏳ Removing old host images if present..."
	docker image rm -f "$(WIKIPEDIA_EXTRACT_JOB_IMAGE)" "$(WIKIPEDIA_LOAD_JOB_IMAGE)" "$(WIKIPEDIA_TRANSFORM_JOB_IMAGE)" || true
	@echo "⏳ Building $(WIKIPEDIA_EXTRACT_JOB_IMAGE) from $(WIKIPEDIA_EXTRACT_JOB_DIR) with --no-cache"
	docker build --no-cache -t "$(WIKIPEDIA_EXTRACT_JOB_IMAGE)" "$(WIKIPEDIA_EXTRACT_JOB_DIR)"
	@echo "⏳ Loading $(WIKIPEDIA_EXTRACT_JOB_IMAGE) into kind cluster $(K8S_CLUSTER_NAME)"
	kind load docker-image "$(WIKIPEDIA_EXTRACT_JOB_IMAGE)" --name $(K8S_CLUSTER_NAME)
	@echo "⏳ Building $(WIKIPEDIA_LOAD_JOB_IMAGE) from $(WIKIPEDIA_LOAD_JOB_DIR) with --no-cache"
	docker build --no-cache -t "$(WIKIPEDIA_LOAD_JOB_IMAGE)" "$(WIKIPEDIA_LOAD_JOB_DIR)"
	@echo "⏳ Loading $(WIKIPEDIA_LOAD_JOB_IMAGE) into kind cluster $(K8S_CLUSTER_NAME)"
	kind load docker-image "$(WIKIPEDIA_LOAD_JOB_IMAGE)" --name $(K8S_CLUSTER_NAME)
	@echo "⏳ Building $(WIKIPEDIA_TRANSFORM_JOB_IMAGE) from repository root Docker context with --no-cache"
	docker build --no-cache -t "$(WIKIPEDIA_TRANSFORM_JOB_IMAGE)" -f "$(DBT_PROJECT_DIR)/Dockerfile" .
	@echo "⏳ Loading $(WIKIPEDIA_TRANSFORM_JOB_IMAGE) into kind cluster $(K8S_CLUSTER_NAME)"
	kind load docker-image "$(WIKIPEDIA_TRANSFORM_JOB_IMAGE)" --name $(K8S_CLUSTER_NAME)
	@echo "✅ Force rebuild complete. Fresh job images loaded into kind"

airflow-install:
	@echo "⏳ Installing/upgrading Airflow Helm release..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	kubectl apply -f $(AIRFLOW_SA_MANIFEST)			
	helm repo add apache-airflow https://airflow.apache.org || true
	helm repo update
	@$(MAKE) jobs-build-load
	@$(MAKE) airflow-dags-sync
	kubectl -n $(PLATFORM_NAMESPACE) create secret generic airflow-secrets \
		--from-literal=connection=postgresql+psycopg2://$(AIRFLOW_METADATA_USER):$(AIRFLOW_METADATA_PASSWORD)@$(AIRFLOW_METADATA_HOST):$(AIRFLOW_METADATA_PORT)/$(AIRFLOW_METADATA_DB)?sslmode=$(AIRFLOW_METADATA_SSLMODE) \
		--from-literal=username=$(AIRFLOW_WEB_USER) \
		--from-literal=password=$(AIRFLOW_WEB_PW) \
		--from-literal=firstName=$(AIRFLOW_WEB_FIRST_NAME) \
		--from-literal=lastName=$(AIRFLOW_WEB_LAST_NAME) \
		--from-literal=email=$(AIRFLOW_WEB_EMAIL) \
		--dry-run=client -o yaml | kubectl apply -f -
	
	@echo "⏳ Waiting for Postgres deployment to be ready..."
	kubectl -n $(PLATFORM_NAMESPACE) rollout status deployment/postgres --timeout=180s
	@echo "✅ Postgres ready. Airflow DB bootstrap is handled by Postgres init scripts"
	
	helm upgrade --install airflow apache-airflow/airflow \
		-n $(PLATFORM_NAMESPACE) \
		--timeout 20m \
		-f $(AIRFLOW_HELM_VALUES)
	@echo "✅ Airflow deployed. UI should be available at http://localhost:8080"


airflow-dags-sync:
	@echo "⏳ Syncing local DAGs from $(ORCHESTRATION_DAGS_DIR) to ConfigMap $(AIRFLOW_DAGS_CONFIGMAP)..."
	kubectl config use-context kind-$(K8S_CLUSTER_NAME)
	@test -d $(ORCHESTRATION_DAGS_DIR)
	kubectl -n $(PLATFORM_NAMESPACE) create configmap $(AIRFLOW_DAGS_CONFIGMAP) \
		--from-file=$(ORCHESTRATION_DAGS_DIR) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "✅ DAG ConfigMap updated"
	


airflow-uninstall:
	@echo "⏳ Uninstalling Airflow Helm release..."
	helm uninstall airflow -n $(PLATFORM_NAMESPACE) || true
	@echo "✅ Airflow release removed"


teardown:
	@echo "⏳ Deleting kind cluster '$(K8S_CLUSTER_NAME)'..."
	kind delete cluster --name $(K8S_CLUSTER_NAME)
	@echo "⏳ Removing local Docker job images..."
	docker image rm -f "$(WIKIPEDIA_EXTRACT_JOB_IMAGE)" "$(WIKIPEDIA_LOAD_JOB_IMAGE)" "$(WIKIPEDIA_TRANSFORM_JOB_IMAGE)" || true
	@echo "✅ Done."

