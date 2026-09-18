# MODULE 25: Helm — The Kubernetes Package Manager

---

## 25.1 Helm — The Kubernetes Package Manager

Helm packages Kubernetes manifests into reusable **charts**. Think of it as `apt` or `yum` for Kubernetes.

**Real-life analogy:** Instead of buying individual ingredients and following a recipe (writing YAML files), Helm is like ordering a meal kit — everything is pre-packaged and configured, you just customize the portions (values).

### Helm Concepts

| Concept | Description |
|---|---|
| **Chart** | A package of Kubernetes manifests (templates + values) |
| **Release** | An installed instance of a chart |
| **Repository** | A collection of charts (like Docker Hub for images) |
| **Values** | Configuration parameters to customize a chart |

### Basic Helm Commands

```bash
# Add a chart repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Output:
# "bitnami" has been added to your repositories
# Hang tight while we grab the latest from your chart repositories...
# Update Complete. ⎈Happy Helming!⎈

# Search for charts
helm search repo nginx

# Output:
# NAME                  CHART VERSION   APP VERSION   DESCRIPTION
# bitnami/nginx         15.4.4          1.25.3        NGINX Open Source for Kubernetes
# bitnami/nginx-ingress 9.9.2           1.25.3        NGINX Ingress Controller

# Show chart details
helm show values bitnami/nginx | head -50

# Install a chart
helm install my-nginx bitnami/nginx \
  --namespace web \
  --create-namespace \
  --set replicaCount=3 \
  --set service.type=LoadBalancer

# Output:
# NAME: my-nginx
# LAST DEPLOYED: Mon Jan 15 10:00:00 2024
# NAMESPACE: web
# STATUS: deployed
# REVISION: 1

# List installed releases
helm list -A

# Output:
# NAME       NAMESPACE   REVISION   UPDATED                   STATUS     CHART          APP VERSION
# my-nginx   web         1          2024-01-15 10:00:00       deployed   nginx-15.4.4   1.25.3

# Get release status
helm status my-nginx -n web

# Upgrade a release
helm upgrade my-nginx bitnami/nginx \
  --namespace web \
  --set replicaCount=5 \
  --set resources.requests.cpu=200m

# Output:
# Release "my-nginx" has been upgraded. Happy Helming!
# REVISION: 2

# View release history
helm history my-nginx -n web

# Output:
# REVISION   UPDATED                    STATUS       CHART          APP VERSION   DESCRIPTION
# 1          Mon Jan 15 10:00:00 2024   superseded   nginx-15.4.4   1.25.3       Install complete
# 2          Mon Jan 15 10:30:00 2024   deployed     nginx-15.4.4   1.25.3       Upgrade complete

# Rollback to previous revision
helm rollback my-nginx 1 -n web

# Output:
# Rollback was a success! Happy Helming!

# Uninstall a release
helm uninstall my-nginx -n web

# Output:
# release "my-nginx" uninstalled
```

### Inspecting Releases and Finding Chart Versions

**`helm get` — inspect a deployed release:**

```bash
# View the rendered Kubernetes manifests for a release
helm get manifest my-nginx -n web

# Output: the actual YAML applied to the cluster (Deployment, Service, ConfigMap, etc.)
# Useful for finding which image a release uses:
helm get manifest my-nginx -n web | grep "image:"

# View the values used for a release (user-supplied overrides)
helm get values my-nginx -n web

# Output:
# USER-SUPPLIED VALUES:
# replicaCount: 3
# service:
#   type: LoadBalancer

# View ALL values (including defaults from the chart)
helm get values my-nginx -n web --all

# View everything about a release (hooks, manifest, notes, values)
helm get all my-nginx -n web
```

| Subcommand | What it shows |
|---|---|
| `helm get manifest` | Rendered K8s YAML applied to cluster |
| `helm get values` | User-supplied value overrides |
| `helm get values --all` | All values including chart defaults |
| `helm get notes` | Post-install notes (usage instructions) |
| `helm get hooks` | Lifecycle hooks (pre-install, post-upgrade, etc.) |
| `helm get all` | Everything above combined |

**`helm search` — find chart versions:**

```bash
# Search for a chart (shows latest version only)
helm search repo nginx

# Output:
# NAME                  CHART VERSION   APP VERSION   DESCRIPTION
# bitnami/nginx         18.1.15         1.27.0        NGINX Open Source for Kubernetes

# Show ALL available versions of a chart
helm search repo nginx --versions

# Output:
# NAME            CHART VERSION   APP VERSION   DESCRIPTION
# bitnami/nginx   18.1.15         1.27.0        NGINX Open Source...
# bitnami/nginx   18.1.14         1.27.0        NGINX Open Source...
# bitnami/nginx   18.1.5          1.25.5        NGINX Open Source...
# bitnami/nginx   15.4.4          1.25.3        NGINX Open Source...
# ...

# Search with a version constraint
helm search repo nginx --version ">=18.0.0"
```

**Upgrading to a specific chart version:**

```bash
# Upgrade a release to a specific chart version
helm upgrade my-nginx bitnami/nginx --version 18.1.15 -n web

# Combine with value overrides
helm upgrade my-nginx bitnami/nginx --version 18.1.15 -n web \
  --set replicaCount=3

# Always update repos first to fetch latest chart metadata
helm repo update && helm upgrade my-nginx bitnami/nginx --version 18.1.15 -n web
```

> **CKA Exam Tip:** A common exam pattern is: list releases (`helm list -A`), inspect manifests (`helm get manifest`), update repos (`helm repo update`), find the target version (`helm search repo --versions`), then upgrade (`helm upgrade --version`).

### Creating Your Own Helm Chart

```bash
# Create a new chart
helm create my-webapp

# Output directory structure:
# my-webapp/
# ├── Chart.yaml          # Chart metadata
# ├── values.yaml         # Default configuration values
# ├── charts/             # Dependencies
# ├── templates/          # Kubernetes manifest templates
# │   ├── deployment.yaml
# │   ├── service.yaml
# │   ├── ingress.yaml
# │   ├── hpa.yaml
# │   ├── serviceaccount.yaml
# │   ├── _helpers.tpl    # Template helpers
# │   ├── NOTES.txt       # Post-install notes
# │   └── tests/
# │       └── test-connection.yaml
# └── .helmignore
```

```yaml
# Chart.yaml
apiVersion: v2
name: my-webapp
description: A web application chart
type: application
version: 0.1.0          # Chart version
appVersion: "1.0.0"     # Application version
```

```yaml
# values.yaml
replicaCount: 3

image:
  repository: 123456789.dkr.ecr.us-east-1.amazonaws.com/my-webapp
  tag: "v1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: alb
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

env:
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  LOG_LEVEL: "info"
```

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-webapp.fullname" . }}
  labels:
    {{- include "my-webapp.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "my-webapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-webapp.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: 80
        env:
        {{- range $key, $value := .Values.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
```

```bash
# Test template rendering (dry-run)
helm template my-webapp ./my-webapp --values ./my-webapp/values.yaml

# Install your chart
helm install my-webapp ./my-webapp \
  --namespace production \
  --create-namespace

# Install with custom values file
helm install my-webapp ./my-webapp \
  -f production-values.yaml \
  --namespace production

# Package chart for distribution
helm package my-webapp

# Output:
# Successfully packaged chart and saved it to: /home/user/my-webapp-0.1.0.tgz
```

### Validating and Testing Charts

```bash
# Lint a chart — checks for errors and best practices
helm lint ./my-webapp

# Output:
# ==> Linting ./my-webapp
# [INFO] Chart.yaml: icon is recommended
# 1 chart(s) linted, 0 chart(s) failed

# Lint with specific values to catch template errors
helm lint ./my-webapp -f production-values.yaml

# Render templates locally without installing (dry-run)
helm template my-webapp ./my-webapp --values ./my-webapp/values.yaml

# Install with an auto-generated release name (useful for testing)
helm install --generate-name ./my-webapp

# Output:
# NAME: my-webapp-1706123456
# LAST DEPLOYED: Thu Jan 25 10:00:00 2024
# NAMESPACE: default
# STATUS: deployed

# Dry-run install to see what would be applied without actually installing
helm install my-webapp ./my-webapp --dry-run
```

| Command | Purpose |
|---|---|
| `helm lint` | Validate chart structure and templates |
| `helm template` | Render templates locally (no cluster needed) |
| `helm install --dry-run` | Simulate install against cluster (validates API resources) |
| `helm install --generate-name` | Install with auto-generated release name |

### Helm Diff Plugin

The `helm-diff` plugin shows what would change before you apply an upgrade — like `kubectl diff` but for Helm releases.

```bash
# Install the plugin
helm plugin install https://github.com/databus23/helm-diff

# Show what would change in an upgrade (without applying)
helm diff upgrade my-nginx bitnami/nginx \
  --values values.yaml \
  -n web

# Output (color-coded):
# default, web, Deployment (apps) has changed:
#   spec:
#     replicas:
# -     3
# +     5
#     template:
#       spec:
#         containers:
#         - image:
# -           nginx:1.25.3
# +           nginx:1.25.4

# Only show changes, suppress unchanged resources
helm diff upgrade my-nginx bitnami/nginx --values values.yaml -n web --suppress-secrets
```

**Why this matters:** Without `helm diff`, you run `helm upgrade` blind — you don't know what will change until it's applied. In production, always diff before upgrading.

### Helm --atomic and --wait Flags

| Flag | What It Does | When to Use |
|------|-------------|-------------|
| `--atomic` | Auto-rollback if upgrade fails (implies `--wait`) | Production deployments — prevents half-applied upgrades |
| `--wait` | Wait for all resources to be ready before marking success | CI/CD pipelines — ensures deployment is healthy |
| `--timeout` | How long to wait for resources to become ready | Slow-starting apps (default: 5m) |
| `--cleanup-on-fail` | Delete new resources on failed upgrade | Prevent orphaned resources |

```bash
# Production-safe upgrade: auto-rollback on failure, wait for readiness
helm upgrade --install my-release ./chart \
  --atomic \
  --timeout 10m \
  --values prod-values.yaml \
  -n production

# If any pod fails readiness within 10 minutes, Helm automatically
# rolls back to the previous release version

# Output on failure:
# Error: UPGRADE FAILED: release my-release failed, and has been rolled back
# due to atomic being set
```

### Helm Best Practices

| Practice | Why |
|----------|-----|
| Store values files in Git | Version-controlled, auditable configuration |
| Always run `helm diff` before upgrading | See exactly what will change |
| Use `--atomic` in production | Auto-rollback prevents broken deployments |
| Pin chart versions in CI/CD (`--version 15.4.4`) | Prevent unexpected chart updates |
| Use `helm template` to render locally before applying | Catch template errors without touching the cluster |
| Separate values files per environment (`dev.yaml`, `prod.yaml`) | Same chart, different configuration |
| Use `helm get values` to audit what's deployed | Verify actual vs expected configuration |

---

