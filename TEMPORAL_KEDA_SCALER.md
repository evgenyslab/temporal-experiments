# Temporal's Official KEDA Scaler

This project uses Temporal's official KEDA scaler announced in [this blog post](https://temporal.io/blog/announcing-keda-based-auto-scaling-for-temporal-workers).

## Why Use Temporal's Official Scaler?

### ✅ Advantages
- **Direct integration**: KEDA queries Temporal's gRPC API directly
- **No custom code**: No need for metrics exporters or Prometheus
- **Real-time accuracy**: Gets actual task queue backlog from Temporal
- **Production-ready**: Maintained by Temporal team
- **Less infrastructure**: Fewer moving parts

### ❌ Previous Approach (Not Used)
- Custom metrics exporter to expose queue depths
- Prometheus for metric collection
- More services to maintain and debug

## How It Works

```
Workflow creates tasks → Temporal queues them
         ↓
KEDA polls Temporal gRPC API every 15s
         ↓
KEDA calculates: (backlog / targetBacklogPerWorker)
         ↓
KEDA scales workers up/down via K8s API
```

## Configuration

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: cv-worker-scaler
spec:
  scaleTargetRef:
    name: cv-worker
  minReplicaCount: 2
  maxReplicaCount: 20
  triggers:
  - type: temporal-cloud  # Temporal's official scaler
    metadata:
      hostAddress: temporal-frontend:7233
      taskQueue: cv-workers
      namespace: default
      targetBacklogPerWorker: "5"
      enableTLS: "false"
```

## Key Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `hostAddress` | Temporal server gRPC endpoint | `temporal-frontend:7233` |
| `taskQueue` | Queue name to monitor | `cv-workers` |
| `namespace` | Temporal namespace | `default` |
| `targetBacklogPerWorker` | Desired tasks per worker | `"5"` |
| `enableTLS` | Use TLS for connection | `"false"` (local), `"true"` (prod) |

## Scaling Formula

```
desired_workers = ceil(current_backlog / targetBacklogPerWorker)
```

**Example with `targetBacklogPerWorker: "5"`:**
- 0 tasks → 2 workers (minReplicaCount)
- 10 tasks → 2 workers (10/5 = 2)
- 30 tasks → 6 workers (30/5 = 6)
- 100 tasks → 20 workers (100/5 = 20, capped at maxReplicaCount)

## Production Setup with Temporal Cloud

```yaml
triggers:
- type: temporal-cloud
  metadata:
    hostAddress: my-namespace.a2b3c.tmprl.cloud:7233
    namespace: my-namespace.a2b3c
    taskQueue: cv-workers
    targetBacklogPerWorker: "5"
    enableTLS: "true"
  authenticationRef:
    name: keda-trigger-auth-temporal
---
apiVersion: v1
kind: Secret
metadata:
  name: keda-trigger-auth-temporal
type: Opaque
data:
  # Base64-encoded mTLS certificate and key
  tls-cert: <base64-encoded-cert>
  tls-key: <base64-encoded-key>
```

## Monitoring

### Check Current Backlog
```bash
# Via kubectl
kubectl get scaledobject cv-worker-scaler -n temporal-demo -o yaml

# Via Temporal UI
open http://localhost:8233
# Navigate to Task Queues → cv-workers
```

### Watch Scaling Events
```bash
kubectl get events -n temporal-demo --watch | grep ScaledObject
```

### KEDA Metrics
```bash
kubectl get hpa -n temporal-demo
```

## Troubleshooting

### Workers not scaling

1. **Check KEDA can reach Temporal:**
```bash
kubectl logs -n keda deployment/keda-operator | grep temporal
```

2. **Verify ScaledObject is active:**
```bash
kubectl get scaledobject -n temporal-demo
kubectl describe scaledobject cv-worker-scaler -n temporal-demo
```

3. **Check for errors:**
```bash
kubectl get events -n temporal-demo | grep Error
```

### Common Issues

**Issue: "connection refused"**
- Check `hostAddress` is correct
- Verify Temporal service is running
- Check network policies

**Issue: "authentication failed"**
- Verify TLS settings match Temporal config
- Check certificates are valid
- Ensure namespace exists

**Issue: "not scaling fast enough"**
- Reduce `pollingInterval` (default 15s)
- Adjust `targetBacklogPerWorker` lower
- Reduce `cooldownPeriod`

## References

- [Official Blog Post](https://temporal.io/blog/announcing-keda-based-auto-scaling-for-temporal-workers)
- [KEDA Temporal Scaler Docs](https://keda.sh/docs/latest/scalers/temporal/)
- [Temporal Worker Autoscaling Guide](https://docs.temporal.io/production-deployment/worker-autoscaling)
