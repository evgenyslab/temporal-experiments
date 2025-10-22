# Quick Start Guide

## Setup (5 minutes)

```bash
# 1. Navigate to project
cd temporal-keda-demo

# 2. Create Kind cluster
make cluster-create

# 3. Install Temporal and KEDA
make install-deps

# 4. Build and deploy
make docker-build
make docker-load
make deploy

# 5. Wait for everything to be ready
make wait
```

## Test the System

### Terminal 1: Watch workers auto-scale
```bash
make watch-cv
```

You should see output like:
```
NAME                          READY   STATUS    RESTARTS   AGE
cv-worker-5d8c9f4b7-abc123    1/1     Running   0          30s
cv-worker-5d8c9f4b7-def456    1/1     Running   0          30s
```

### Terminal 2: Trigger a workflow
```bash
# Trigger single workflow
make trigger-workflow DATASET_ID=123

# OR trigger multiple workflows to see scaling
make trigger-load
```

### Terminal 3: Watch the Temporal UI
```bash
make temporal-ui
# Then open http://localhost:8233 in your browser
```

## What to Observe

1. **Initial State**: 2 CV workers, 1 ML worker
2. **After Trigger**: Watch CV workers scale up to handle 20 files
3. **Processing**: Each CV task takes 10-30 seconds (simulated)
4. **ML Phase**: After CV completes, ML workers scale up
5. **Completion**: Workers scale back down after ~60 seconds (cooldown)

## Key Files to Explore

- `workflows/dataset_workflow.py` - Main workflow orchestration
- `activities/cv_activities.py` - CV processing simulation
- `k8s/06-keda-scaledobjects.yaml` - Auto-scaling configuration using Temporal's official scaler
- No custom metrics exporter needed - KEDA queries Temporal directly!

## Troubleshooting

### Workers not starting
```bash
kubectl get pods -n temporal-demo
kubectl logs -n temporal-demo -l app=cv-worker
```

### KEDA not scaling
```bash
# Check KEDA logs
make keda-logs

# Check metrics
kubectl get scaledobject -n temporal-demo
```

### Can't connect to Temporal
```bash
# Forward Temporal port
kubectl port-forward -n temporal-demo svc/temporal-frontend 7233:7233
```

### CSRF token errors in Temporal UI (Safari)
If you see "missing csrf token in request header" errors when trying to cancel/terminate workflows in Safari:

**Solution**: The configuration has been updated to allow insecure CSRF cookies for local development. If you still see errors:

1. **Clear Safari cookies**: Safari → Settings → Privacy → Manage Website Data → Remove All
2. **Disable "Prevent Cross-Site Tracking"**: Safari → Settings → Privacy → Uncheck "Prevent cross-site tracking"
3. **Try a different browser**: Chrome or Firefox typically work without issues
4. **Hard refresh**: Cmd+Shift+R to clear cached resources

The issue is caused by Safari's strict third-party cookie blocking. The updated config includes:
- `TEMPORAL_CSRF_COOKIE_INSECURE: "true"` - Allows cookies over HTTP for local dev
- `TEMPORAL_CORS_ORIGINS: "http://localhost:8080"` - Configures CORS properly

## Next Steps

1. **Modify scaling thresholds** in `k8s/06-keda-scaledobjects.yaml`
2. **Add real CV/ML libraries** to Dockerfiles
3. **Adjust processing times** in activities to test different scenarios
4. **Add more worker types** by copying the cv-worker pattern
5. **Explore KEDA scaler options** - authentication, TLS, etc.

## Clean Up

```bash
# Remove all resources
make clean

# Or delete entire cluster
make cluster-delete
```
