# Temporal + KEDA Auto-Scaling Demo

Local development setup with Temporal workflows, multiple worker types, and KEDA-based auto-scaling running on Kind (Kubernetes in Docker).

## Project Structure

```
temporal-keda-demo/
├── README.md
├── requirements.txt
├── Makefile
├── QUICKSTART.md
├── TEMPORAL_KEDA_SCALER.md
├── kind-config.yaml
├── workflows/
│   └── dataset_workflow.py
├── activities/
│   ├── __init__.py
│   ├── api_activities.py
│   ├── storage_activities.py
│   ├── cv_activities.py
│   └── ml_activities.py
├── workers/
│   ├── workflow_worker.py
│   ├── api_worker.py
│   ├── cv_worker.py
│   └── ml_worker.py
├── scripts/
│   └── trigger_workflow.py
├── docker/
│   ├── Dockerfile.workflow
│   ├── Dockerfile.api
│   ├── Dockerfile.cv
│   └── Dockerfile.ml
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-temporal.yaml
    ├── 02-workflow-worker.yaml
    ├── 03-api-worker.yaml
    ├── 04-cv-worker.yaml
    ├── 05-ml-worker.yaml
    └── 06-keda-scaledobjects.yaml
```

## Prerequisites

- Docker Desktop
- Kind: `brew install kind` (Mac) or download from https://kind.sigs.k8s.io
- kubectl: `brew install kubectl`
- Python 3.11+

## Quick Start

```bash
# 1. Create Kind cluster
make cluster-create

# 2. Install Temporal and KEDA
make install-deps

# 3. Build and load Docker images (no metrics exporter needed!)
make docker-build
make docker-load

# 4. Deploy all components
make deploy

# 5. Wait for everything to be ready
make wait

# 6. Trigger a workflow
make trigger-workflow DATASET_ID=123

# 7. Watch workers auto-scale
make watch-workers

# 8. View Temporal UI
make temporal-ui
```

## Detailed Commands

### Cluster Management
```bash
make cluster-create    # Create Kind cluster
make cluster-delete    # Delete Kind cluster
make cluster-status    # Check cluster status
```

### Installation
```bash
make install-deps      # Install Temporal + KEDA
make install-temporal  # Install only Temporal
make install-keda      # Install only KEDA
```

### Development
```bash
make docker-build      # Build all Docker images
make docker-load       # Load images into Kind
make deploy            # Deploy all K8s resources
make redeploy          # Rebuild, reload, and redeploy
```

### Monitoring
```bash
make watch-workers     # Watch worker pod scaling
make watch-cv          # Watch CV workers specifically
make logs-cv           # Tail CV worker logs
make logs-workflow     # Tail workflow worker logs
make temporal-ui       # Open Temporal UI (localhost:8233)
make keda-logs         # View KEDA operator logs
```

### Testing
```bash
make trigger-workflow DATASET_ID=123    # Trigger single workflow
make trigger-load                        # Trigger 10 workflows for load test
```

### Cleanup
```bash
make clean             # Remove all K8s resources
make cluster-delete    # Delete entire cluster
```

## Architecture

### Workers
- **Workflow Worker**: Orchestrates workflows (lightweight)
- **API Worker**: Calls external APIs, lists S3 files
- **CV Worker**: Heavy computer vision processing (auto-scales 2-20 replicas)
- **ML Worker**: Machine learning inference (auto-scales 1-10 replicas)

### Auto-Scaling
Uses Temporal's official KEDA scaler (`temporal-cloud` trigger type):
- KEDA directly queries Temporal's gRPC API for task queue backlog
- CV workers: Scale when backlog > 5 tasks per worker
- ML workers: Scale when backlog > 3 tasks per worker
- No custom metrics exporter needed!

### Workflow Example
1. Get dataset metadata (API worker)
2. List S3 files (API worker)
3. **Fan-out**: Process each file (CV workers - auto-scales!)
4. **Fan-out**: Analyze each result (ML workers - auto-scales!)

## Configuration

### Adjust Scaling Thresholds
Edit `k8s/06-keda-scaledobjects.yaml`:
```yaml
targetBacklogPerWorker: "5"  # Tasks per worker before scaling
maxReplicaCount: 20          # Maximum workers
```

### Adjust Worker Resources
Edit worker deployment files:
```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
```

## Troubleshooting

### Workers not scaling
```bash
# Check KEDA logs
make keda-logs

# Check if KEDA can reach Temporal
kubectl exec -n keda deployment/keda-operator -- nslookup temporal-frontend.temporal-demo.svc.cluster.local

# Manually check queue depth
kubectl exec -n temporal-demo deployment/workflow-worker -- \
  python -c "import asyncio; from temporalio.client import Client; \
  asyncio.run(Client.connect('temporal-frontend:7233').get_task_queue_worker_count('cv-workers'))"
```

### Temporal not accessible
```bash
# Check Temporal pods
kubectl get pods -n temporal-demo

# Port-forward Temporal
kubectl port-forward -n temporal-demo svc/temporal-frontend 7233:7233
```

### Images not loading
```bash
# Verify images in Kind
docker exec -it temporal-demo-control-plane crictl images

# Reload images
make docker-load
```

## Local Development Tips

1. **Fast iteration**: Use `make redeploy` to rebuild and redeploy
2. **Watch scaling**: Keep `make watch-cv` running in a terminal
3. **Check logs**: Use `make logs-cv` to debug worker issues
4. **Temporal UI**: Access at http://localhost:8233 to see workflows

## Production Considerations

For production deployment:
1. Use Temporal Cloud or properly configured Temporal cluster with authentication
2. Enable TLS in KEDA scaler configuration (`enableTLS: "true"`)
3. Add mTLS certificates for Temporal authentication
4. Use proper container registry (ECR, GCR, etc.)
5. Add resource limits and requests based on actual workload
6. Set up proper observability (Datadog, Grafana, etc.)
7. Use managed K8s (EKS, GKE, AKS)
8. Configure HPA based on both queue depth AND resource utilization

### Using with Temporal Cloud
```yaml
triggers:
- type: temporal-cloud
  metadata:
    hostAddress: namespace.account.tmprl.cloud:7233
    namespace: your-namespace.account
    taskQueue: cv-workers
    targetBacklogPerWorker: "5"
    enableTLS: "true"
  authenticationRef:
    name: keda-trigger-auth-temporal
```

## License

MIT
