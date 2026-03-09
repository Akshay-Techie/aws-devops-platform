# 🚀 Project-05: Future MLOps Architect — AWS DevOps Platform

> **Author:** Akshay Kumar Prasad (akshaytechie)
> **AWS Region:** ap-south-1 (Mumbai)
> **Stack:** Flask → Docker → ECR → Terraform → Kubernetes → Helm → Jenkins → Prometheus → Grafana → Loki

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Full Workflow](#full-workflow)
- [Component Details](#component-details)
- [Setup Guide](#setup-guide)
- [Jenkins CI/CD Pipeline](#jenkins-cicd-pipeline)
- [Monitoring Stack](#monitoring-stack)
- [Log Aggregation](#log-aggregation)
- [URLs & Access](#urls--access)
- [Common Commands](#common-commands)

---

## 🌟 Overview

This project builds a **production-grade MLOps/DevOps platform** on AWS from scratch. Every push to GitHub automatically tests, builds, containerizes, and deploys the application to a Kubernetes cluster — with full monitoring and log aggregation.

### What this project demonstrates:
- Infrastructure as Code (Terraform)
- Container orchestration (Kubernetes via kubeadm)
- CI/CD automation (Jenkins)
- Observability (Prometheus + Grafana + Loki)
- GitOps workflow

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER                                 │
│                    (Local Ubuntu VBox)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ git push
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GITHUB                                   │
│                   github.com/<your-username>/<repo>             │
└──────────────────────────┬──────────────────────────────────────┘
                           │ webhook
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JENKINS CI/CD                                  │
│                   (Local Ubuntu VBox)                            │
│  Stage 1: Checkout → Stage 2: Test → Stage 3: Build             │
│  Stage 4: Push ECR → Stage 5: K8s Secret → Stage 6: Helm Deploy │
│  Stage 7: Smoke Test                                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
┌─────────────────────┐    ┌─────────────────────────────────────┐
│      AWS ECR        │    │           AWS INFRASTRUCTURE         │
│  Docker Image Store │    │         (Terraform managed)          │
│  :1, :2, :3 ...     │    │                                      │
└─────────────────────┘    │  ┌──────────────────────────────┐   │
                           │  │           VPC                 │   │
                           │  │  ┌─────────┐  ┌──────────┐  │   │
                           │  │  │ Public  │  │ Private  │  │   │
                           │  │  │ Subnet  │  │  Subnet  │  │   │
                           │  │  └────┬────┘  └──────────┘  │   │
                           │  │       │                       │   │
                           │  │  ┌────▼──────────────────┐  │   │
                           │  │  │         ALB            │  │   │
                           │  │  │  (Load Balancer)       │  │   │
                           │  │  └────┬───────────────────┘  │   │
                           │  │       │ port 30080            │   │
                           │  │  ┌────▼──────────────────┐  │   │
                           │  │  │   KUBERNETES CLUSTER   │  │   │
                           │  │  │  Master Node           │  │   │
                           │  │  │  Worker Node           │  │   │
                           │  │  │                        │  │   │
                           │  │  │  ┌──────┐  ┌──────┐  │  │   │
                           │  │  │  │ Pod1 │  │ Pod2 │  │  │   │
                           │  │  │  │Flask │  │Flask │  │  │   │
                           │  │  │  └──────┘  └──────┘  │  │   │
                           │  │  │                        │  │   │
                           │  │  │  MONITORING NAMESPACE  │  │   │
                           │  │  │  Prometheus  Grafana   │  │   │
                           │  │  │  Alertmanager  Loki    │  │   │
                           │  │  │  Promtail              │  │   │
                           │  │  └────────────────────────┘  │   │
                           │  └──────────────────────────────┘   │
                           └─────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
Project-05/
│
├── Docker/                          # Flask Application
│   └── app/
│       ├── app.py                   # Main Flask application
│       │                            # Endpoints: / /health /info /api/v1/predict /metrics
│       ├── test_app.py              # pytest unit tests
│       ├── requirements.txt         # Python dependencies
│       │                            # flask, gunicorn, prometheus-flask-exporter
│       ├── Dockerfile               # Multi-stage Docker build
│       ├── index.html               # Futuristic website UI
│       ├── .env.example             # Environment variables reference (copy to .env)
│       └── .dockerignore            # Files excluded from Docker build
│
├── Jenkins/
│   └── Jenkinsfile                  # 7-stage CI/CD pipeline definition
│                                    # Checkout→Test→Build→ECR→Secret→Deploy→Smoke
│
├── terraform/
│   ├── environments/
│   │   └── prod/
│   │       ├── main.tf              # Root module — wires all modules together
│   │       ├── variables.tf         # Variable declarations
│   │       ├── outputs.tf           # ALB DNS, EC2 IPs, VPC ID outputs
│   │       └── terraform.tfvars     # ⚠️ YOUR values go here — gitignored, never commit
│   │
│   └── modules/
│       ├── vpc/                     # VPC, IGW, Subnets, NAT, Route Tables
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── security-groups/         # ALB SG, Master SG, Worker SG
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── ec2/                     # IAM Role, Key Pair, Master+Worker EC2
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── alb/                     # ALB, Target Group, HTTP Listener
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       └── ecr/                     # ECR Repository
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
│
├── helm/
│   └── <your-app-name>/             # Helm chart for Flask app
│       ├── Chart.yaml               # Chart metadata
│       ├── values.yaml              # Default values (image, replicas, ports)
│       └── templates/
│           ├── deployment.yaml      # K8s Deployment — 2 replicas
│           └── service.yaml         # K8s Service — NodePort 30080
│
├── kubernetes/                      # Raw K8s manifests (reference)
│
├── .gitignore                       # Ignores terraform.tfvars, .env, __pycache__
└── README.md                        # This file
```

---

## ⚠️ Before You Start

Copy the example files and fill in your own values — **never commit real credentials**:

```bash
cp Docker/app/.env.example Docker/app/.env
cp terraform/environments/prod/terraform.tfvars.example terraform/environments/prod/terraform.tfvars
```

Your `.gitignore` should always include:

```
*.tfvars
.env
*.pem
*.key
**/__pycache__/
.terraform/
```

---

## 🔄 Full Workflow

### Phase 1 — Code

```
1. Developer writes code locally
2. Code is pushed to GitHub:
   git add .
   git commit -m "feat: new feature"
   git push origin main
```

### Phase 2 — CI/CD (Jenkins Auto-Triggered)

```
GitHub push → webhook → Jenkins picks up in seconds

Stage 1: CHECKOUT
  └── Jenkins clones latest code from GitHub

Stage 2: TEST
  └── pip install -r requirements.txt
  └── pytest test_app.py -v
  └── If ANY test fails → pipeline stops (fail fast)

Stage 3: BUILD DOCKER IMAGE
  └── docker build -t <account-id>.dkr.ecr.<region>.amazonaws.com/<repo>:BUILD_NUMBER
  └── Each build gets a unique tag (:1, :2, :3 ...)
  └── Enables rollback to any previous version

Stage 4: PUSH TO ECR
  └── aws ecr get-login-password | docker login
  └── docker push image to AWS ECR

Stage 5: UPDATE ECR SECRET
  └── ECR tokens expire every 12 hours
  └── kubectl delete secret ecr-secret
  └── kubectl create secret docker-registry ecr-secret (fresh token)

Stage 6: DEPLOY WITH HELM
  └── helm upgrade --install <release-name>
  └── --set image.tag=BUILD_NUMBER (deploys exact build)
  └── --rollback-on-failure (auto rollback if pods crash)
  └── --timeout 120s (wait for pods to be Ready)

Stage 7: SMOKE TEST
  └── sleep 20 (pods need time to start)
  └── curl ALB /health endpoint
  └── If 200 OK → pipeline SUCCESS
  └── If not   → pipeline FAILURE

POST ACTIONS:
  └── SUCCESS: log success message
  └── FAILURE: helm rollback to last working version
  └── ALWAYS:  docker image prune (cleanup disk)
```

### Phase 3 — Running in Kubernetes

```
Helm deploys → Kubernetes schedules pods on Worker node

Pod 1 (Flask) ─────────────────────────────────────────┐
Pod 2 (Flask) ─────────────────────────────────────────┤
                                                         ▼
                                              Service (NodePort 30080)
                                                         │
                                              ALB (port 80)
                                                         │
                                              Internet Users
```

### Phase 4 — Monitoring

```
Every 15 seconds:
  Prometheus scrapes /metrics from Flask pods
  Prometheus scrapes node metrics (CPU/RAM/Disk)
  Prometheus scrapes K8s metrics (pods/deployments)

Grafana reads from Prometheus → shows dashboards:
  - Node Exporter Full (host metrics)
  - Kubernetes Cluster Overview
  - Kubernetes Pod Metrics

Promtail runs on every node:
  Reads all pod logs from /var/log/containers/
  Ships logs to Loki every few seconds

Grafana reads from Loki → search and filter logs in real time
```

---

## 🔧 Component Details

### Flask Application Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves futuristic HTML website |
| `/health` | GET | Health check for K8s probes and ALB |
| `/info` | GET | System info, hostname, K8s env vars |
| `/api/v1/predict` | GET | Demo ML prediction |
| `/api/v1/predict` | POST | ML prediction with custom features |
| `/metrics` | GET | Prometheus metrics (auto-exposed) |
| `/metrics-demo` | GET | Request counters |

### Terraform Resources (28 total)

| Module | Resources |
|--------|-----------|
| VPC | VPC, IGW, 2 public subnets, 2 private subnets, NAT GW, route tables |
| Security Groups | ALB SG (80/443), Master SG (6443/2379/10250), Worker SG (NodePort/kubelet) |
| EC2 | IAM role, key pair, master EC2 (t3.medium), worker EC2 (t3.medium) |
| ALB | ALB, target group (port 30080), HTTP listener |
| ECR | ECR repository |

### Kubernetes Cluster

| Component | Details |
|-----------|---------|
| Bootstrap | kubeadm v1.29.15 |
| CNI | Calico v3.27.0 |
| Nodes | 1 Master + 1 Worker (t3.medium) |
| Runtime | containerd (SystemdCgroup=true) |

### Monitoring Stack

| Tool | NodePort | Purpose |
|------|----------|---------|
| Prometheus | 30090 | Metrics collection and storage |
| Grafana | 30030 | Dashboards and visualization |
| Alertmanager | 30903 | Alert routing and notifications |
| Loki | 30310 | Log aggregation and storage |
| Promtail | DaemonSet | Log collection from all pods |
| Node Exporter | DaemonSet | Host-level metrics |
| kube-state-metrics | ClusterIP | Kubernetes object metrics |

---

## 🚀 Setup Guide

### Prerequisites

```bash
# Tools needed on your local machine:
git
docker
aws cli       # configured with your credentials (aws configure)
terraform
kubectl
helm
jenkins
ngrok         # for GitHub webhook tunnel
```

### Step 1 — Clone and Configure

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

Fill in your `terraform.tfvars`:

```hcl
# terraform/environments/prod/terraform.tfvars  ← DO NOT COMMIT THIS FILE

aws_region          = "ap-south-1"          # your preferred AWS region
aws_account_id      = "123456789012"        # your 12-digit AWS account ID
project_name        = "your-project-name"
environment         = "prod"
vpc_cidr            = "10.0.0.0/16"
key_pair_name       = "your-key-pair-name"  # key pair already in AWS
instance_type       = "t3.medium"
ecr_repository_name = "your-ecr-repo-name"
```

### Step 2 — Build and Push Docker Image

```bash
cd Docker/app

# Build
docker build -t <your-app>:1.0 .

# Authenticate to ECR
aws ecr get-login-password --region <region> | \
    docker login --username AWS --password-stdin \
    <your-account-id>.dkr.ecr.<region>.amazonaws.com

# Tag and push
docker tag <your-app>:1.0 \
    <your-account-id>.dkr.ecr.<region>.amazonaws.com/<your-repo>:1.0

docker push <your-account-id>.dkr.ecr.<region>.amazonaws.com/<your-repo>:1.0
```

### Step 3 — Provision Infrastructure with Terraform

```bash
cd terraform/environments/prod
terraform init
terraform validate
terraform plan
terraform apply
# Note the output values: ALB DNS, master IP, worker IP
```

### Step 4 — Bootstrap Kubernetes

```bash
# Run on BOTH master and worker nodes
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo crictl config --set runtime-endpoint=unix:///run/containerd/containerd.sock
```

```bash
# Run on MASTER only
sudo kubeadm init \
    --pod-network-cidr=192.168.0.0/16 \
    --apiserver-advertise-address=<master-private-ip> \
    --kubernetes-version=v1.29.15

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install Calico CNI
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

```bash
# Run on WORKER only — use the token printed by kubeadm init above
sudo kubeadm join <master-private-ip>:6443 \
    --token <token-from-init-output> \
    --discovery-token-ca-cert-hash sha256:<hash-from-init-output>
```

### Step 5 — Deploy Application with Helm

```bash
# Create ECR pull secret (K8s needs this to pull your image)
kubectl create secret docker-registry ecr-secret \
    --docker-server=<your-account-id>.dkr.ecr.<region>.amazonaws.com \
    --docker-username=AWS \
    --docker-password=$(aws ecr get-login-password --region <region>) \
    --namespace=default

# Deploy with Helm
helm install <your-app> ./helm/<your-chart>

# Verify
kubectl get pods
kubectl get svc
```

### Step 6 — Install Monitoring Stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Required for bare-metal kubeadm — provides a default StorageClass
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.26/deploy/local-path-storage.yaml
kubectl patch storageclass local-path \
    -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Install stack
helm install prometheus prometheus-community/prometheus \
    --namespace monitoring --create-namespace --values prometheus-values.yaml

helm install grafana grafana/grafana \
    --namespace monitoring --values grafana-values.yaml

helm install loki grafana/loki \
    --namespace monitoring --values loki-values.yaml

helm install promtail grafana/promtail \
    --namespace monitoring --values promtail-values.yaml
```

---

## 🔁 Jenkins CI/CD Pipeline

### Prerequisites on Jenkins Machine

```
java 17+
jenkins
docker          (jenkins user added to docker group)
aws cli
kubectl         (kubeconfig pointing to your cluster)
helm
```

### Jenkins Credentials to Configure

Go to **Jenkins → Manage Jenkins → Credentials** and add:

| Credential ID | Type | Description |
|---------------|------|-------------|
| `AWS_ACCESS_KEY_ID` | Secret text | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Secret text | Your AWS secret key |
| `AWS_ACCOUNT_ID` | Secret text | Your 12-digit AWS account ID |
| `github-credentials` | Username/Password | GitHub username + Personal Access Token |

> **Never hardcode credentials in the Jenkinsfile.** Always reference credential IDs and let Jenkins inject them at runtime.

### GitHub Webhook Setup

```
1. Run:   ngrok http 8080
2. Copy the public HTTPS URL (e.g. https://xxxx.ngrok-free.app)
3. GitHub repo → Settings → Webhooks → Add webhook
   Payload URL:  https://xxxx.ngrok-free.app/github-webhook/
   Content type: application/json
   Trigger:      Just the push event
4. Keep the ngrok terminal open while working
```

---

## 📊 Monitoring Stack

### Grafana Dashboards (import by ID)

| Dashboard | ID | Shows |
|-----------|----|-------|
| Node Exporter Full | 1860 | CPU, RAM, Disk, Network per node |
| Kubernetes Cluster | 6417 | Pod count, deployments, node health |
| Kubernetes Pod Metrics | 747 | Per-pod CPU, memory, network |

> Grafana login credentials are set in your `grafana-values.yaml`. Change the default password after first login.

### Useful Prometheus Queries (PromQL)

```promql
# All scrape targets status
up

# HTTP requests per second
rate(flask_http_request_total[5m])

# Node CPU usage %
100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Available memory %
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100

# Running pod count
kube_pod_status_phase{phase="Running"}
```

---

## 📜 Log Aggregation (Loki)

### Useful LogQL Queries

```logql
# All app pod logs
{namespace="default"}

# Errors only
{namespace="default"} |= "ERROR"

# Health check hits
{namespace="default"} |= "/health"

# All monitoring stack logs
{namespace="monitoring"}

# ML prediction logs
{namespace="default"} |= "predict"
```

---

## 🌐 URLs & Access

> Replace placeholders with your actual values from `terraform output` after apply.

| Service | URL |
|---------|-----|
| Flask App (ALB) | `http://<your-alb-dns-name>` |
| Flask App (Direct) | `http://<worker-public-ip>:30080` |
| Health Check | `http://<worker-public-ip>:30080/health` |
| ML Prediction | `http://<worker-public-ip>:30080/api/v1/predict` |
| Prometheus | `http://<worker-public-ip>:30090` |
| Grafana | `http://<worker-public-ip>:30030` |
| Alertmanager | `http://<worker-public-ip>:30903` |
| Jenkins | `http://localhost:8080` |

---

## 🛠️ Common Commands

### Kubernetes

```bash
kubectl get nodes
kubectl get pods --all-namespaces
kubectl get svc --all-namespaces
kubectl logs -f deployment/<your-app>
kubectl scale deployment <your-app> --replicas=3
kubectl exec -it <pod-name> -- /bin/sh
```

### Helm

```bash
helm list --all-namespaces
helm status <release-name>
helm history <release-name>
helm rollback <release-name> <revision-number>
helm upgrade <release-name> ./helm/<chart> --set image.tag=<tag>
```

### Terraform

```bash
terraform plan       # preview changes
terraform apply      # provision infrastructure
terraform output     # show IPs, DNS names, etc.
terraform destroy    # tear everything down
```

### SSH Access

```bash
# Master node
ssh -i "<your-key.pem>" ubuntu@<master-public-ip>

# Worker node
ssh -i "<your-key.pem>" ubuntu@<worker-public-ip>
```

---

## 🏆 What This Project Demonstrates

```
✅ Infrastructure as Code    — Terraform (28 resources)
✅ Containerization          — Docker multi-stage build
✅ Container Registry        — AWS ECR
✅ Container Orchestration   — Kubernetes (kubeadm)
✅ Package Management        — Helm charts
✅ Load Balancing            — AWS ALB
✅ CI/CD Pipeline            — Jenkins (7 stages)
✅ Automated Testing         — pytest
✅ Metrics Monitoring        — Prometheus + Grafana
✅ Alert Management          — Alertmanager
✅ Log Aggregation           — Loki + Promtail
✅ GitOps Workflow           — Push to deploy
✅ Auto Rollback             — On deployment failure
```

---

*Future MLOps Architect | Project-05 | Author → Akshay Kumar Prasad*