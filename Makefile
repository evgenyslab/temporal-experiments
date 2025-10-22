.PHONY: help cluster-create cluster-delete install-deps docker-build deploy

CLUSTER_NAME := temporal-demo
NAMESPACE := temporal-demo
DATASET_ID ?= 123
COUNT ?= 10
START_ID ?= 1
WORKFLOW_COUNT_ARG ?=

help:
	@echo "Temporal + KEDA Demo - Available Commands"
	@echo ""
	@echo "Cluster Management:"
	@echo "  make cluster-create    - Create Kind cluster"
	@echo "  make cluster-delete    - Delete Kind cluster"
	@echo ""
	@echo "Installation:"
	@echo "  make install-deps      - Install Temporal + KEDA + Ingress"
	@echo "  make install-temporal  - Install Temporal"
	@echo "  make install-keda      - Install KEDA"
	@echo "  make install-ingress   - Install NGINX Ingress Controller"
	@echo ""
	@echo "Development:"
	@echo "  make docker-build      - Build all Docker images"
	@echo "  make docker-load       - Load images into Kind"
	@echo "  make deploy            - Deploy all resources"
	@echo "  make redeploy          - Rebuild and redeploy"
	@echo ""
	@echo "Monitoring:"
	@echo "  make watch-workers     - Watch all workers"
	@echo "  make watch-cv          - Watch CV workers"
	@echo "  make logs-cv           - CV worker logs"
	@echo "  make temporal-ui       - Open Temporal UI"
	@echo ""
	@echo "Testing:"
	@echo "  make trigger-workflow  - Trigger single workflow"
	@echo "  make trigger-n         - Trigger N workflows (COUNT=10 START_ID=1 WORKFLOW_COUNT_ARG=)"

cluster-create:
	@echo "Creating Kind cluster..."
	kind create cluster --name $(CLUSTER_NAME) --config kind-config.yaml
	@echo "Cluster created successfully!"

cluster-delete:
	@echo "Deleting Kind cluster..."
	kind delete cluster --name $(CLUSTER_NAME)

cluster-status:
	kubectl cluster-info --context kind-$(CLUSTER_NAME)

install-deps: install-temporal install-keda install-ingress

install-temporal:
	@echo "Installing Temporal..."
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/00-namespace.yaml
	kubectl apply -f k8s/01-temporal.yaml
	@echo "Waiting for Postgres to be ready..."
	@bash -c 'until kubectl get pod -l app=postgres -n $(NAMESPACE) 2>/dev/null | grep -q postgres; do sleep 1; done'
	kubectl wait --for=condition=ready pod -l app=postgres -n $(NAMESPACE) --timeout=300s
	@echo "Waiting for Temporal to be ready..."
	@bash -c 'until kubectl get pod -l app=temporal -n $(NAMESPACE) 2>/dev/null | grep -q temporal; do sleep 1; done'
	kubectl wait --for=condition=ready pod -l app=temporal -n $(NAMESPACE) --timeout=300s
	@echo "Waiting for Temporal UI to be ready..."
	@bash -c 'until kubectl get pod -l app=temporal-ui -n $(NAMESPACE) 2>/dev/null | grep -q temporal-ui; do sleep 1; done'
	kubectl wait --for=condition=ready pod -l app=temporal-ui -n $(NAMESPACE) --timeout=300s

install-keda:
	@echo "Installing KEDA..."
	kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.18.0/keda-2.18.0.yaml
	@echo "Waiting for KEDA to be ready..."
	kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=120s

install-ingress:
	@echo "Installing NGINX Ingress Controller..."
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	@echo "Waiting for Ingress Controller to be ready..."
	kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s
	@echo "Patching Ingress Controller to use NodePort 30080 and 30443..."
	kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec":{"type":"NodePort","ports":[{"name":"http","port":80,"protocol":"TCP","targetPort":"http","nodePort":30080},{"name":"https","port":443,"protocol":"TCP","targetPort":"https","nodePort":30443}]}}'
	@echo "Ingress Controller ready!"

docker-build:
	@echo "Building Docker images..."
	docker build -f docker/Dockerfile.workflow -t temporal-workflow-worker:latest .
	docker build -f docker/Dockerfile.api -t temporal-api-worker:latest .
	docker build -f docker/Dockerfile.cv -t temporal-cv-worker:latest .
	docker build -f docker/Dockerfile.ml -t temporal-ml-worker:latest .
	@echo "Images built successfully!"

docker-load:
	@echo "Loading images into Kind..."
	kind load docker-image temporal-workflow-worker:latest --name $(CLUSTER_NAME)
	kind load docker-image temporal-api-worker:latest --name $(CLUSTER_NAME)
	kind load docker-image temporal-cv-worker:latest --name $(CLUSTER_NAME)
	kind load docker-image temporal-ml-worker:latest --name $(CLUSTER_NAME)
	@echo "Images loaded successfully!"

deploy:
	@echo "Deploying all resources..."
	kubectl apply -f k8s/02-workflow-worker.yaml
	kubectl apply -f k8s/03-api-worker.yaml
	kubectl apply -f k8s/04-cv-worker.yaml
	kubectl apply -f k8s/05-ml-worker.yaml
	kubectl apply -f k8s/06-keda-scaledobjects.yaml
	kubectl apply -f k8s/07-temporal-ingress.yaml
	@echo "Deployment complete!"

redeploy: docker-build docker-load
	@echo "Restarting deployments..."
	kubectl rollout restart deployment -n $(NAMESPACE)
	kubectl rollout status deployment -n $(NAMESPACE) --timeout=180s

wait:
	@echo "Waiting for all pods to be ready..."
	kubectl wait --for=condition=ready pod --all -n $(NAMESPACE) --timeout=300s

watch-workers:
	watch -n 2 'kubectl get pods -n $(NAMESPACE) -l worker-type'

watch-cv:
	watch -n 2 'kubectl get pods -n $(NAMESPACE) -l app=cv-worker'

logs-cv:
	kubectl logs -f -n $(NAMESPACE) -l app=cv-worker --tail=50

logs-workflow:
	kubectl logs -f -n $(NAMESPACE) -l app=workflow-worker --tail=50

logs-ml:
	kubectl logs -f -n $(NAMESPACE) -l app=ml-worker --tail=50

keda-logs:
	kubectl logs -f -n keda -l app=keda-operator --tail=50

temporal-ui:
	@echo "Temporal UI is available at http://temporal.local"
	@echo "(Make sure 'temporal.local' is added to your /etc/hosts file)"
	@echo ""
	@echo "To add it, run: sudo sh -c 'echo \"127.0.0.1 temporal.local\" >> /etc/hosts'"
	@echo ""
	@echo "If you prefer port-forwarding, run: kubectl port-forward -n $(NAMESPACE) svc/temporal-ui 8080:8080"

trigger-workflow:
	@echo "Triggering workflow for dataset $(DATASET_ID)..."
	kubectl run trigger-$(DATASET_ID) --rm -i --restart=Never \
		--image=temporal-workflow-worker:latest \
		-n $(NAMESPACE) \
		--image-pull-policy=Never \
		--env="DATASET_ID=$(DATASET_ID)" \
		-- python scripts/trigger_from_cluster.py $(DATASET_ID)

trigger-load:
	@echo "Triggering 10 workflows for load test..."
	@for i in {1..10}; do \
		$(MAKE) trigger-workflow DATASET_ID=$$i & \
	done
	@wait
	@echo "All workflows triggered!"

trigger-n:
	@echo "Triggering $(COUNT) workflows starting from ID $(START_ID)..."
	@if [ -n "$(WORKFLOW_COUNT_ARG)" ]; then \
		echo "Each workflow will receive count argument: $(WORKFLOW_COUNT_ARG)"; \
		kubectl run trigger-n-$(COUNT)-$(START_ID) --rm -i --restart=Never \
			--image=temporal-workflow-worker:latest \
			-n $(NAMESPACE) \
			--image-pull-policy=Never \
			-- python scripts/trigger_n_workflows.py $(COUNT) $(START_ID) $(WORKFLOW_COUNT_ARG); \
	else \
		kubectl run trigger-n-$(COUNT)-$(START_ID) --rm -i --restart=Never \
			--image=temporal-workflow-worker:latest \
			-n $(NAMESPACE) \
			--image-pull-policy=Never \
			-- python scripts/trigger_n_workflows.py $(COUNT) $(START_ID); \
	fi

clean:
	kubectl delete -f k8s/ --ignore-not-found=true

full-reset: clean cluster-delete cluster-create install-deps docker-build docker-load deploy
