# Module 13 — Kubernetes Automation with Python

Kubernetes orchestrates containerized applications across clusters of machines. Python can automate Kubernetes operations — deploying applications, scaling services, monitoring pods, managing configurations, and building custom operators.

---

## Prerequisites

```bash
pip install kubernetes
```

```python
from kubernetes import client, config

# Load kubeconfig (uses ~/.kube/config by default)
config.load_kube_config()

v1 = client.CoreV1Api()
print("Connected to Kubernetes cluster")
```

**For in-cluster use** (when your script runs inside a Kubernetes pod):

```python
config.load_incluster_config()
```

---

## Listing Resources

### Listing Pods

```python
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

pods = v1.list_namespaced_pod(namespace="default")

print(f"{'NAME':<40} {'STATUS':<12} {'RESTARTS':<10} {'AGE'}")
print("-" * 75)

for pod in pods.items:
    name = pod.metadata.name
    status = pod.status.phase
    restarts = sum(cs.restart_count for cs in (pod.status.container_statuses or []))
    age = pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M")
    print(f"{name:<40} {status:<12} {restarts:<10} {age}")
```

**Output (example):**

```
NAME                                     STATUS       RESTARTS   AGE
web-app-7d4f8b6c9-abc12                 Running      0          2024-01-15 08:00
web-app-7d4f8b6c9-def34                 Running      0          2024-01-15 08:00
api-server-5c8d7e9f1-ghi56              Running      2          2024-01-14 12:30
redis-cache-0                            Running      0          2024-01-10 06:00
```

### Listing All Pods Across Namespaces

```python
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

pods = v1.list_pod_for_all_namespaces()

print(f"Total pods: {len(pods.items)}\n")

# Group by namespace
by_namespace = {}
for pod in pods.items:
    ns = pod.metadata.namespace
    if ns not in by_namespace:
        by_namespace[ns] = []
    by_namespace[ns].append(pod)

for ns, ns_pods in sorted(by_namespace.items()):
    running = sum(1 for p in ns_pods if p.status.phase == "Running")
    print(f"  {ns}: {len(ns_pods)} pods ({running} running)")
```

**Output (example):**

```
Total pods: 23

  default: 5 pods (5 running)
  kube-system: 12 pods (12 running)
  monitoring: 3 pods (3 running)
  ingress-nginx: 3 pods (3 running)
```

### Listing Services

```python
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

services = v1.list_namespaced_service(namespace="default")

for svc in services.items:
    name = svc.metadata.name
    svc_type = svc.spec.type
    ports = ", ".join(f"{p.port}/{p.protocol}" for p in (svc.spec.ports or []))
    cluster_ip = svc.spec.cluster_ip
    print(f"  {name}: {svc_type} ({cluster_ip}) ports=[{ports}]")
```

### Listing Deployments

```python
from kubernetes import client, config

config.load_kube_config()
apps_v1 = client.AppsV1Api()

deployments = apps_v1.list_namespaced_deployment(namespace="default")

for dep in deployments.items:
    name = dep.metadata.name
    replicas = dep.spec.replicas
    ready = dep.status.ready_replicas or 0
    image = dep.spec.template.spec.containers[0].image
    print(f"  {name}: {ready}/{replicas} ready ({image})")
```

**Output (example):**

```
  web-app: 3/3 ready (myapp:2.1.0)
  api-server: 2/2 ready (api:1.5.0)
  worker: 1/1 ready (worker:1.0.0)
```

---

## Creating Resources

### Creating a Deployment

```python
from kubernetes import client, config

config.load_kube_config()
apps_v1 = client.AppsV1Api()

deployment = client.V1Deployment(
    metadata=client.V1ObjectMeta(name="web-app"),
    spec=client.V1DeploymentSpec(
        replicas=3,
        selector=client.V1LabelSelector(
            match_labels={"app": "web-app"}
        ),
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": "web-app"}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="web",
                        image="nginx:latest",
                        ports=[client.V1ContainerPort(container_port=80)],
                        resources=client.V1ResourceRequirements(
                            requests={"cpu": "100m", "memory": "128Mi"},
                            limits={"cpu": "500m", "memory": "256Mi"}
                        )
                    )
                ]
            )
        )
    )
)

result = apps_v1.create_namespaced_deployment(
    namespace="default",
    body=deployment
)

print(f"Deployment created: {result.metadata.name}")
```

### Creating from YAML

Often it is easier to load a YAML file than to build objects in Python:

```python
from kubernetes import client, config, utils
import yaml

config.load_kube_config()
k8s_client = client.ApiClient()

# Load YAML file
with open("deployment.yaml", "r") as f:
    manifest = yaml.safe_load(f)

# Apply it
try:
    utils.create_from_dict(k8s_client, manifest)
    print(f"Created: {manifest['kind']}/{manifest['metadata']['name']}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Scaling Deployments

```python
from kubernetes import client, config

config.load_kube_config()
apps_v1 = client.AppsV1Api()

def scale_deployment(name, replicas, namespace="default"):
    """Scale a deployment to the specified number of replicas."""
    # Get current state
    deployment = apps_v1.read_namespaced_deployment(name, namespace)
    current = deployment.spec.replicas
    
    if current == replicas:
        print(f"  {name} already at {replicas} replicas")
        return
    
    # Scale
    deployment.spec.replicas = replicas
    apps_v1.patch_namespaced_deployment(name, namespace, deployment)
    
    direction = "up" if replicas > current else "down"
    print(f"  Scaled {name} {direction}: {current} -> {replicas}")

# Usage:
scale_deployment("web-app", 5)
scale_deployment("api-server", 3)
```

**Output:**

```
  Scaled web-app up: 3 -> 5
  Scaled api-server up: 2 -> 3
```

---

## Monitoring and Health Checks

### Pod Health Monitor

```python
from kubernetes import client, config
import time

config.load_kube_config()
v1 = client.CoreV1Api()

def check_pod_health(namespace="default"):
    """Check health of all pods in a namespace."""
    pods = v1.list_namespaced_pod(namespace=namespace)
    
    healthy = 0
    unhealthy = []
    
    for pod in pods.items:
        name = pod.metadata.name
        phase = pod.status.phase
        
        if phase == "Running":
            # Check container statuses
            all_ready = all(
                cs.ready for cs in (pod.status.container_statuses or [])
            )
            if all_ready:
                healthy += 1
            else:
                unhealthy.append({"name": name, "reason": "Containers not ready"})
        elif phase in ("Pending", "Unknown"):
            unhealthy.append({"name": name, "reason": f"Phase: {phase}"})
        elif phase == "Failed":
            unhealthy.append({"name": name, "reason": "Pod failed"})
    
    total = len(pods.items)
    print(f"\nPod Health: {healthy}/{total} healthy")
    
    if unhealthy:
        print("\nUnhealthy pods:")
        for pod in unhealthy:
            print(f"  [!!] {pod['name']}: {pod['reason']}")
    
    return healthy == total

# Usage:
is_healthy = check_pod_health("default")
```

### Auto-Recovery: Restart Failed Pods

```python
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

def restart_failed_pods(namespace="default", dry_run=True):
    """Delete failed pods so their controllers recreate them."""
    pods = v1.list_namespaced_pod(namespace=namespace)
    restarted = []
    
    for pod in pods.items:
        if pod.status.phase == "Failed":
            name = pod.metadata.name
            if dry_run:
                print(f"  [DRY RUN] Would delete failed pod: {name}")
            else:
                v1.delete_namespaced_pod(name, namespace)
                print(f"  Deleted failed pod: {name}")
            restarted.append(name)
        
        # Check for CrashLoopBackOff
        for cs in (pod.status.container_statuses or []):
            if cs.restart_count > 5:
                name = pod.metadata.name
                if dry_run:
                    print(f"  [DRY RUN] Would delete crash-looping pod: {name} "
                          f"({cs.restart_count} restarts)")
                else:
                    v1.delete_namespaced_pod(name, namespace)
                    print(f"  Deleted crash-looping pod: {name}")
                restarted.append(name)
                break
    
    if not restarted:
        print("  No failed pods found.")
    
    return restarted

# Usage:
restart_failed_pods("default", dry_run=True)
```

---

## Rolling Updates

```python
from kubernetes import client, config
import time

config.load_kube_config()
apps_v1 = client.AppsV1Api()

def rolling_update(name, new_image, namespace="default"):
    """Update a deployment's container image and monitor the rollout."""
    # Get current deployment
    deployment = apps_v1.read_namespaced_deployment(name, namespace)
    old_image = deployment.spec.template.spec.containers[0].image
    
    print(f"Updating {name}: {old_image} -> {new_image}")
    
    # Update the image
    deployment.spec.template.spec.containers[0].image = new_image
    apps_v1.patch_namespaced_deployment(name, namespace, deployment)
    
    # Monitor rollout
    print("Monitoring rollout...")
    for i in range(60):    # Wait up to 60 seconds
        deployment = apps_v1.read_namespaced_deployment(name, namespace)
        status = deployment.status
        
        ready = status.ready_replicas or 0
        desired = deployment.spec.replicas
        updated = status.updated_replicas or 0
        
        print(f"  [{i+1}s] Ready: {ready}/{desired}, Updated: {updated}/{desired}")
        
        if ready == desired and updated == desired:
            print(f"\nRollout complete!")
            return True
        
        time.sleep(1)
    
    print(f"\nRollout timed out!")
    return False

# Usage:
# rolling_update("web-app", "myapp:2.0.0")
```

---

## Working with ConfigMaps and Secrets

### Creating a ConfigMap

```python
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

configmap = client.V1ConfigMap(
    metadata=client.V1ObjectMeta(name="app-config"),
    data={
        "DATABASE_HOST": "db.example.com",
        "DATABASE_PORT": "5432",
        "LOG_LEVEL": "info",
        "app.conf": "server.port=8080\nserver.host=0.0.0.0\n"
    }
)

v1.create_namespaced_config_map(namespace="default", body=configmap)
print("ConfigMap created: app-config")
```

### Creating a Secret

```python
from kubernetes import client, config
import base64

config.load_kube_config()
v1 = client.CoreV1Api()

# Secrets must be base64-encoded
secret = client.V1Secret(
    metadata=client.V1ObjectMeta(name="app-secrets"),
    type="Opaque",
    data={
        "db-password": base64.b64encode(b"supersecret").decode("utf-8"),
        "api-key": base64.b64encode(b"key-12345").decode("utf-8"),
    }
)

v1.create_namespaced_secret(namespace="default", body=secret)
print("Secret created: app-secrets")
```

---

## Practical Example: Namespace Auditor

```python
from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

def audit_namespace(namespace):
    """Audit a Kubernetes namespace for common issues."""
    print(f"\nNamespace Audit: {namespace}")
    print("=" * 50)
    findings = []
    
    # Check pods
    pods = v1.list_namespaced_pod(namespace=namespace)
    failed_pods = [p for p in pods.items if p.status.phase in ("Failed", "Unknown")]
    pending_pods = [p for p in pods.items if p.status.phase == "Pending"]
    
    if failed_pods:
        findings.append(f"[!!] {len(failed_pods)} failed pod(s)")
    if pending_pods:
        findings.append(f"[!] {len(pending_pods)} pending pod(s)")
    
    # Check for pods without resource limits
    for pod in pods.items:
        for container in pod.spec.containers:
            if not container.resources or not container.resources.limits:
                findings.append(
                    f"[!] Pod {pod.metadata.name}/{container.name}: "
                    f"no resource limits set"
                )
    
    # Check for crash-looping containers
    for pod in pods.items:
        for cs in (pod.status.container_statuses or []):
            if cs.restart_count > 3:
                findings.append(
                    f"[!!] Pod {pod.metadata.name}: "
                    f"{cs.restart_count} restarts (possible crash loop)"
                )
    
    # Check deployments
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
    for dep in deployments.items:
        ready = dep.status.ready_replicas or 0
        desired = dep.spec.replicas
        if ready < desired:
            findings.append(
                f"[!!] Deployment {dep.metadata.name}: "
                f"only {ready}/{desired} replicas ready"
            )
        if desired == 1:
            findings.append(
                f"[!] Deployment {dep.metadata.name}: "
                f"only 1 replica (no high availability)"
            )
    
    # Print results
    print(f"Pods: {len(pods.items)}")
    print(f"Deployments: {len(deployments.items)}")
    
    if findings:
        print(f"\nFindings ({len(findings)}):")
        for f in findings:
            print(f"  {f}")
    else:
        print("\nNo issues found!")

# Usage:
# audit_namespace("default")
# audit_namespace("production")
```

---

## Exercises

**Exercise 1:** Write a script that lists all pods across all namespaces and shows which ones are not in "Running" state.

**Exercise 2:** Write a script that monitors a deployment's rollout status and sends a notification when it completes or fails.

**Exercise 3:** Build a CLI tool with subcommands: `pods` (list pods), `scale` (scale a deployment), `restart` (restart failed pods), and `audit` (run namespace audit).

**Exercise 4:** Write a script that backs up all ConfigMaps and Secrets in a namespace to YAML files.

---

## Common Mistakes

### 1. Not Handling API Errors

```python
from kubernetes.client.rest import ApiException

try:
    pod = v1.read_namespaced_pod("my-pod", "default")
except ApiException as e:
    if e.status == 404:
        print("Pod not found")
    else:
        print(f"API error: {e.status} - {e.reason}")
```

### 2. Not Setting Resource Limits

Always set CPU and memory requests/limits on containers. Without them, a single pod can consume all cluster resources.

### 3. Using Default Namespace for Everything

Organize workloads into namespaces (e.g., `production`, `staging`, `monitoring`). This improves security and resource management.

### 4. Not Waiting for Rollouts

After updating a deployment, wait for the rollout to complete before declaring success. Check `ready_replicas == desired_replicas`.

---

## Summary

| Task | API | Method |
|------|-----|--------|
| List pods | `CoreV1Api` | `list_namespaced_pod()` |
| List deployments | `AppsV1Api` | `list_namespaced_deployment()` |
| Create deployment | `AppsV1Api` | `create_namespaced_deployment()` |
| Scale deployment | `AppsV1Api` | `patch_namespaced_deployment()` |
| Delete pod | `CoreV1Api` | `delete_namespaced_pod()` |
| Create ConfigMap | `CoreV1Api` | `create_namespaced_config_map()` |
| Create Secret | `CoreV1Api` | `create_namespaced_secret()` |
| Get logs | `CoreV1Api` | `read_namespaced_pod_log()` |

---

[Previous: Module 12 — Docker Automation](12-docker-automation.md) | [Next: Module 14 — AWS Automation](14-aws-automation-using-boto3.md)
