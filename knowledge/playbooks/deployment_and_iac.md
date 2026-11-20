---
type: Playbook
title: Deployment, Docker & Cloud IaC
description: Runbook for local Python, Docker Compose, GHCR CI/CD, AWS CloudFormation S3/SQS setup, and GCP Terraform Pub/Sub provisioning.
resource: docker-compose.yml
tags: [docker, cloudformation, terraform, aws, gcp, deployment, ci-cd]
status: stable
generated:
  by: antigravity/v2.0
  at: 2026-11-20T17:15:00Z
---

# Deployment, Docker & Cloud IaC

## 1. Local Python Execution

```bash
cd /Users/happylife/LogSimv2
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # populate required transport & API credentials
python -u log_simulator.py
```

* Starts the interactive CLI menu and spawns the Flask dashboard subprocess on `http://0.0.0.0:5000` (configurable via `DASHBOARD_HOST` / `DASHBOARD_PORT`).
* When launched without a TTY (e.g., `systemd`, Docker detached), `log_simulator.py` automatically falls back to `_run_headless()`, blocking on the Flask dashboard subprocess and handling `SIGTERM`.

---

## 2. Docker & Docker Compose (`Dockerfile`, `docker-compose.yml`)

* **Image**: `python:3.11-slim`, `/app` workdir, installs 19 packages from `requirements.txt`, copies `log_simulator.py`, `config.json`, `modules/`, `integrations/`, `dashboard/`, exposes port `5000`, `CMD ["python", "-u", "log_simulator.py"]`.
* **Compose Service (`logsim`)**:
  * `ports: ["5000:5000"]`, `env_file: .env`, `restart: unless-stopped`, `stdin_open: true`, `tty: true` (attach to CLI with `docker attach`).
  * Named volumes: `logsim-state:/app/state` (beacon targets, Windows event record IDs, `cie_identity_map.json`) and `logsim-cache:/app/domain_cache` (Tranco domain corpus).
  * Optional read-only bind mounts (commented in `docker-compose.yml`): `./config.json:/app/config.json:ro` and `./secrets:/app/secrets:ro` (for `WEC_PFX_PATH` or `GOOGLE_APPLICATION_CREDENTIALS`).
* **`.dockerignore`**: Excludes `.env`, credentials, `docs/`, `terraform/`, `CloudFormation/`, `XSIAM imports/`, caches, and git metadata from the build context.

### CI/CD (`.github/workflows/docker-publish.yml`)
* **Triggers**: Push to `main` and published GitHub releases.
* **Target**: Publishes multi-tagged images (`latest`, git tag, semver, commit SHA) to `ghcr.io/<github.repository>`.
* **Gap**: No automated lint, unit test, or syntax-check workflow exists in `.github/workflows/`.

---

## 3. AWS CloudTrail Ingestion IaC (`CloudFormation/S3LogSim.yaml`)

Deploys the S3 + SQS pipeline for `modules/aws.py` -> Cortex XSIAM:
* **Parameters**: `BucketName` (globally unique), `ExternalId` (UUID for XSIAM cross-account role), `LogRetentionDays` (default `30`).
* **Provisioned Resources**:
  * `S3LogBucket` (all 4 Public Access Block flags enabled) with `s3:ObjectCreated:*` event notification **strictly prefix-filtered to `AWSLogs/`** so plain-text health probes under `logsim-healthcheck/` do not enter SQS and stall XSIAM's gunzip collector.
  * Lifecycle rules expiring `AWSLogs/` after `LogRetentionDays` and `logsim-healthcheck/` after `1` day.
  * `SQSNotificationQueue` (`<BucketName>-sqs-queue`) + `SQSDeadLetterQueue` (`<BucketName>-sqs-dlq`, `maxReceiveCount: 5`, 14-day retention) + `SQSQueuePolicy`.
  * `LogSimulatorIAMUser` (`xsiam-log-simulator-user-<BucketName>`) + access key pair (`s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`, `s3:PutBucketNotification`).
  * `XSIAMIAMRole` (`XSIAM-S3-Collector-Role-<BucketName>`) trusting Palo Alto Networks AWS account `006742885340` via `sts:ExternalId`, granting S3 read + SQS receive/delete.
* **Outputs**: Map `S3BucketName`, `LogSimulatorAccessKeyId`, and `LogSimulatorSecretAccessKey` to `.env`, and configure XSIAM with `SQSQueueURL`, `XSIAMRoleARN`, and `XSIAMRoleExternalId`.

---

## 4. GCP Cloud Audit Ingestion IaC (`terraform/gcp_pubsub/`)

Requires Terraform `>= 1.3.0` and `hashicorp/google >= 5.0.0`.
* **Provisioned Resources (`main.tf`)**:
  * Enables `pubsub.googleapis.com` and `iam.googleapis.com`.
  * Creates Pub/Sub topic `xsiam-audit-logs` (24h retention) and pull subscription `xsiam-logsim-pull` (60s ack deadline, 7-day retention, non-expiring).
  * Creates `logsim-publisher` service account (`roles/pubsub.publisher` + JSON key) and `xsiam-subscriber` service account (`roles/pubsub.subscriber` + `roles/pubsub.viewer` + JSON key).
* **Automated Wrapper (`apply_and_configure.sh`)**:
  ```bash
  cd /Users/happylife/LogSimv2/terraform/gcp_pubsub
  cp terraform.tfvars.example terraform.tfvars   # set project_id
  ./apply_and_configure.sh
  ```
  Runs `terraform init -upgrade && terraform apply`, writes `logsim-publisher-key.json` & `xsiam-subscriber-key.json` (`0600`), and updates `../../.env` with `GCP_PROJECT_ID`, `GCP_PUBSUB_TOPIC`, and inline `GCP_SERVICE_ACCOUNT_KEY_JSON`.
