# MODULE 16: ConfigMaps, Secrets & Environment Variables

---

## 16.1 Environment Variables & ConfigMaps

### Setting Environment Variables in Pods

Environment variables can be set directly in the pod spec, from ConfigMaps, or from Secrets.

**In Docker:**

```bash
docker run -e APP_COLOR=pink simple-webapp-color
```

**In Kubernetes — hard-coded values:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp-color
spec:
  containers:
  - name: simple-webapp-color
    image: simple-webapp-color
    ports:
    - containerPort: 8080
    env:
    - name: APP_COLOR
      value: pink
    - name: APP_MODE
      value: prod
```

This works but becomes hard to maintain when managing many pods across environments (dev, staging, production). ConfigMaps solve this by centralizing configuration.

**Three ways to set environment variables:**

```yaml
# Method 1: Plain key-value (hard-coded)
env:
- name: APP_COLOR
  value: pink

# Method 2: From a ConfigMap
env:
- name: APP_COLOR
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: APP_COLOR

# Method 3: From a Secret
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: app-secrets
      key: password
```

Use Method 1 for values that never change. Use Method 2 for configuration that varies between environments. Use Method 3 for sensitive data (passwords, API keys, tokens).

**Method 4: From the Downward API (Pod/Node metadata)**

The Downward API exposes pod and node metadata as environment variables or files — without querying the API server. Use `fieldRef` for metadata fields and `resourceFieldRef` for container resource limits.

```yaml
# downward-api-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-demo
  labels:
    app: demo
spec:
  containers:
  - name: app
    image: busybox:1
    command: ["sh", "-c", "env | grep -E 'MY_|NODE_' && sleep 3600"]
    env:
    # Pod metadata via fieldRef
    - name: MY_POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: MY_POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: MY_POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName
    # Container resource limits via resourceFieldRef
    - name: MY_CPU_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: limits.cpu
    - name: MY_MEM_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: limits.memory
    resources:
      limits:
        cpu: "500m"
        memory: "128Mi"
```

```bash
kubectl apply -f downward-api-env.yaml
kubectl logs downward-demo
# MY_POD_NAME=downward-demo
# MY_POD_NAMESPACE=default
# MY_POD_IP=10.244.1.5
# NODE_NAME=node01
# MY_CPU_LIMIT=1
# MY_MEM_LIMIT=134217728
```

**Available `fieldRef` fields:**

| Field Path | Value |
|---|---|
| `metadata.name` | Pod name |
| `metadata.namespace` | Pod namespace |
| `metadata.uid` | Pod UID |
| `metadata.labels['<KEY>']` | Specific label value |
| `metadata.annotations['<KEY>']` | Specific annotation value |
| `spec.nodeName` | Node the pod is scheduled on |
| `spec.serviceAccountName` | ServiceAccount name |
| `status.podIP` | Pod IP address |
| `status.hostIP` | Node IP address |

**Available `resourceFieldRef` fields:** `requests.cpu`, `requests.memory`, `limits.cpu`, `limits.memory`, `requests.ephemeral-storage`, `limits.ephemeral-storage`.

**Downward API as volume files** — useful when you need labels/annotations (which can change dynamically):

```yaml
# downward-api-volume.yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-volume
  labels:
    app: demo
    version: v2
spec:
  containers:
  - name: app
    image: busybox:1
    command: ["sh", "-c", "cat /etc/podinfo/labels && sleep 3600"]
    volumeMounts:
    - name: podinfo
      mountPath: /etc/podinfo
  volumes:
  - name: podinfo
    downwardAPI:
      items:
      - path: "labels"
        fieldRef:
          fieldPath: metadata.labels
      - path: "annotations"
        fieldRef:
          fieldPath: metadata.annotations
```

> **CKA Exam Tip:** The Downward API is commonly tested in multi-container pod questions where one container needs the pod name or node name as an environment variable. The pattern is always `env.valueFrom.fieldRef.fieldPath`.

### ConfigMaps — Centralizing Configuration

ConfigMaps store non-sensitive configuration data as key-value pairs.

**What ConfigMaps are for:** Database hostnames, port numbers, log levels, feature flags, configuration files — anything that changes between environments but isn't secret.

**Three ways to consume ConfigMaps in pods:**
1. **Environment variables** — individual keys or all keys at once (`env` / `envFrom`)
2. **Volume mounts** — keys become files in a directory
3. **Command-line arguments** — reference ConfigMap values in container commands

**Key behavior:**
- ConfigMaps are namespace-scoped
- Maximum size: 1 MB
- When mounted as a volume, changes to the ConfigMap are reflected in the pod (with a delay of ~30-60 seconds)
- When used as environment variables, changes require a pod restart

**Common mistake:** Forgetting that environment variables from ConfigMaps are set at pod creation time. If you update the ConfigMap, existing pods don't see the change until restarted. Volume-mounted ConfigMaps update automatically.

**Organizing ConfigMaps by component:**

| ConfigMap Name | Description | Sample Data |
|----------------|-------------|-------------|
| `app-config` | Application settings | `APP_COLOR: blue`, `APP_MODE: prod` |
| `mysql-config` | MySQL configuration | `port: 3306`, `max_allowed_packet: 128M` |
| `redis-config` | Redis configuration | `port: 6379`, `rdb-compression: yes` |

Name ConfigMaps descriptively — you reference these names when associating them with pods.

### Creating ConfigMaps

```bash
# Method 1: From literal values
kubectl create configmap app-config \
  --from-literal=DATABASE_HOST=postgres.default.svc.cluster.local \
  --from-literal=DATABASE_PORT=5432 \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100

# Output:
# configmap/app-config created

# Method 2: From a file
cat > app.properties << 'EOF'
database.host=postgres.default.svc.cluster.local
database.port=5432
log.level=info
max.connections=100
EOF

kubectl create configmap app-config-file --from-file=app.properties

# Method 3: From YAML (declarative)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-yaml
data:
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  DATABASE_PORT: "5432"
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"

  # Multi-line config file
  nginx.conf: |
    server {
      listen 80;
      server_name example.com;
      location / {
        proxy_pass http://backend:8080;
      }
    }
EOF

# List ConfigMaps
kubectl get configmaps

# Output:
# NAME               DATA   AGE
# app-config         4      2m
# app-config-file    1      1m
# app-config-yaml    5      30s

# View ConfigMap details
kubectl describe configmap app-config

# Output:
# Name:         app-config
# Namespace:    default
# Labels:       <none>
# Annotations:  <none>
#
# Data
# ====
# DATABASE_HOST:
# ----
# postgres.default.svc.cluster.local
# DATABASE_PORT:
# ----
# 5432
# LOG_LEVEL:
# ----
# info
# MAX_CONNECTIONS:
# ----
# 100
#
# Events:  <none>

# View as YAML
kubectl get configmap app-config-yaml -o yaml

# Output:
# apiVersion: v1
# kind: ConfigMap
# metadata:
#   name: app-config-yaml
# data:
#   DATABASE_HOST: postgres.default.svc.cluster.local
#   DATABASE_PORT: "5432"
#   LOG_LEVEL: info
#   MAX_CONNECTIONS: "100"
#   nginx.conf: |
#     server {
#       listen 80;
#       ...
```

### Using ConfigMaps in Pods

```yaml
# configmap-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-config
spec:
  containers:
  - name: app
    image: nginx:1.25
    
    # Method 1: Individual environment variables
    env:
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config-yaml
          key: DATABASE_HOST
    - name: DB_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config-yaml
          key: DATABASE_PORT

    # Method 2: All keys as environment variables
    envFrom:
    - configMapRef:
        name: app-config-yaml

    # Method 3: Mount as files
    volumeMounts:
    - name: config-volume
      mountPath: /etc/nginx/conf.d
    - name: all-config
      mountPath: /etc/app-config

  volumes:
  # Mount specific key as file
  - name: config-volume
    configMap:
      name: app-config-yaml
      items:
      - key: nginx.conf
        path: default.conf    # File name in the mount path

  # Mount all keys as files
  - name: all-config
    configMap:
      name: app-config-yaml
```

```bash
kubectl apply -f configmap-pod.yaml

# Verify environment variables
kubectl exec app-with-config -- env | grep DB_

# Output:
# DB_HOST=postgres.default.svc.cluster.local
# DB_PORT=5432

# Verify mounted files
kubectl exec app-with-config -- ls /etc/app-config/

# Output:
# DATABASE_HOST
# DATABASE_PORT
# LOG_LEVEL
# MAX_CONNECTIONS
# nginx.conf

kubectl exec app-with-config -- cat /etc/app-config/DATABASE_HOST

# Output:
# postgres.default.svc.cluster.local

kubectl exec app-with-config -- cat /etc/nginx/conf.d/default.conf

# Output:
# server {
#   listen 80;
#   server_name example.com;
#   location / {
#     proxy_pass http://backend:8080;
#   }
# }
```

**Quick ConfigMap from file with selective mounting:**

```bash
# Create a config file and load it as a ConfigMap
kubectl create configmap mymap --from-file=sample.conf

# Inspect the ConfigMap
kubectl get cm
kubectl describe configmaps mymap
kubectl get configmap mymap -o yaml
```

```yaml
# deploy-with-configmap.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mydeployments
spec:
  replicas: 1
  selector:
    matchLabels:
      name: deployment
  template:
    metadata:
      labels:
        name: deployment
    spec:
      containers:
      - name: c00
        image: ubuntu
        command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
        volumeMounts:
        - name: appconfig
          mountPath: "/tmp/config"
      volumes:
      - name: appconfig
        configMap:
          name: mymap
          items:
          - key: sample.conf       # Key name from the ConfigMap
            path: sample.conf      # File name at the mount path
```

### Lab: Environment Variables and ConfigMaps

**Exercise 1: Inspect and change a pod's environment variable**

```bash
# Check the current env var
kubectl describe pod webapp-color | grep -A2 "Environment"
```

```
Environment:
  APP_COLOR:  pink
```

```bash
# Edit the pod to change APP_COLOR to green
kubectl edit pod webapp-color
# Change value: pink → value: green, save
```

Pods are immutable — the edit is saved to a temp file. Force-replace:

```bash
kubectl replace --force -f /tmp/kubectl-edit-3135302771.yaml
```

```
pod "webapp-color" deleted
pod/webapp-color replaced
```

```bash
# Verify the change
kubectl describe pod webapp-color | grep APP_COLOR
```

```
APP_COLOR:  green
```

**Exercise 2: Switch from hard-coded env to ConfigMap**

```bash
# Create a ConfigMap
kubectl create configmap webapp-config-map --from-literal=APP_COLOR="darkblue"

# Verify
kubectl describe cm webapp-config-map
```

```
Data
====
APP_COLOR:
----
darkblue
```

Edit the pod to replace `env` with `envFrom`:

```yaml
# Before (hard-coded)
env:
- name: APP_COLOR
  value: green

# After (from ConfigMap)
envFrom:
- configMapRef:
    name: webapp-config-map
```

```bash
kubectl replace --force -f /tmp/kubectl-edit-192529677.yaml
```

```
pod "webapp-color" deleted
pod/webapp-color replaced
```

The pod now reads `APP_COLOR` from the ConfigMap. Updating the ConfigMap and restarting the pod changes the color without editing the pod spec.

---

## 16.2 Secrets — Sensitive Data

Secrets store sensitive data like passwords, tokens, and TLS certificates. They are base64-encoded (not encrypted by default).

**Why Secrets exist — the hardcoding problem:**

Consider a Python web application connecting to MySQL with credentials in the code:

```python
# BAD — credentials hardcoded in application code
mysql.connector.connect(host="mysql", database="mysql",
                        user="root", password="paswrd")
```

You might move these values to a ConfigMap, but ConfigMaps store data in plain text — visible to anyone with API access. Passwords, API keys, and tokens should never go in ConfigMaps. Kubernetes Secrets provide a separate mechanism for sensitive data, with base64 encoding and tighter access controls.

**Important security notes:**
- Secrets are base64-encoded, NOT encrypted. Anyone with API access can decode them.
- In etcd, Secrets are stored in plaintext by default. Enable encryption at rest for production clusters.
- On EKS, AWS encrypts etcd data at rest using AWS KMS.
- For production, use AWS Secrets Manager or HashiCorp Vault with the Secrets Store CSI Driver.
- Secret size limit: each Secret object must be <= 1 MB.

**Secrets vs ConfigMaps:**

| Feature | ConfigMap | Secret |
|---|---|---|
| Data type | Non-sensitive config | Sensitive data |
| Encoding | Plain text | Base64-encoded |
| Mount mode | Read-write | Read-only by default (mode 0644) |
| Use for | DB host, log level, feature flags | Passwords, API keys, TLS certs |

**Three ways to consume Secrets in pods** (same as ConfigMaps):
1. Environment variables (`env` with `secretKeyRef`)
2. Volume mounts (keys become files, mounted read-only)
3. `envFrom` to inject all keys as environment variables

### Creating Secrets

```bash
# Method 1: From literal values
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='S3cur3P@ssw0rd!'

# Output:
# secret/db-credentials created

# Method 2: From files
touch certificate; echo "YOUCANSEEME" > password.txt
kubectl create secret generic mypasswd --from-file=password.txt
kubectl create secret generic mycert --from-file=certificate

# Method 3: From TLS certificate files
kubectl create secret tls tls-secret \
  --cert=tls.crt \
  --key=tls.key

# Method 3: From YAML
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
type: Opaque
data:
  # Values must be base64-encoded
  API_KEY: YWJjZGVmMTIzNDU2    # echo -n "abcdef123456" | base64
  API_SECRET: c2VjcmV0MTIz      # echo -n "secret123" | base64
stringData:
  # stringData accepts plain text (auto-encoded)
  DATABASE_URL: "postgresql://admin:password@postgres:5432/mydb"
EOF

# List secrets
kubectl get secrets

# Output:
# NAME             TYPE     DATA   AGE
# db-credentials   Opaque   2      10m
# api-keys         Opaque   3      5m

# Describe secret (shows metadata but hides values)
kubectl describe secret db-credentials

# Output:
# Name:         db-credentials
# Namespace:    default
# Labels:       <none>
# Annotations:  <none>
#
# Type:  Opaque
#
# Data
# ====
# password:  16 bytes
# username:  5 bytes

# View secret with encoded values
kubectl get secret db-credentials -o yaml

# Output:
# apiVersion: v1
# kind: Secret
# metadata:
#   name: db-credentials
# type: Opaque
# data:
#   password: UzNjdXIzUEBzc3cwcmQh
#   username: YWRtaW4=

# Decode a secret value
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 -d

# Output:
# S3cur3P@ssw0rd!
```

Note: `kubectl describe secret` shows the byte count but not the actual values — useful for verifying a secret exists without exposing its contents.

### Using Secrets in Pods

```yaml
# secret-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-secrets
spec:
  containers:
  - name: app
    image: nginx:1.25

    # Method 1: Individual environment variables
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password

    # Method 2: All keys as environment variables
    envFrom:
    - secretRef:
        name: api-keys

    # Method 3: Mount as files
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true

  volumes:
  - name: secret-volume
    secret:
      secretName: db-credentials
      defaultMode: 0400    # Read-only for owner
```

```bash
kubectl apply -f secret-pod.yaml

# Verify
kubectl exec app-with-secrets -- env | grep DB_

# Output:
# DB_USERNAME=admin
# DB_PASSWORD=S3cur3P@ssw0rd!

kubectl exec app-with-secrets -- cat /etc/secrets/password

# Output:
# S3cur3P@ssw0rd!
```

### Step-by-Step: Creating and Using a Secret for MySQL

Storing a database password in a Secret is safer and more flexible than putting it directly in a Pod definition or container image.

**Step 1: Base64-encode the password**

```bash
# On Mac/Linux
echo -n 'dbpassword11' | base64
# Output: ZGJwYXNzd29yZDEx

# Or use an online tool: https://www.base64encode.org
```

⚠️ Always use `echo -n` (no newline). Without `-n`, the encoded value includes a trailing newline character, which causes authentication failures.

**Step 2: Create the Secret manifest**

```yaml
# 08-Kubernetes-Secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-db-password
type: Opaque
data:
  # Output of: echo -n 'dbpassword11' | base64
  db-password: ZGJwYXNzd29yZDEx
```

`type: Opaque` means the contents are unstructured from Kubernetes's point of view. It can contain arbitrary key-value pairs. This is the most common Secret type.

**Step 3: Reference the Secret in MySQL Deployment**

```yaml
# In the MySQL container spec:
env:
  - name: MYSQL_ROOT_PASSWORD
    valueFrom:
      secretKeyRef:
        name: mysql-db-password    # Name of the Secret object
        key: db-password           # Key within the Secret's data
```

**Step 4: Reference the same Secret in the User Management Microservice**

```yaml
# In the UMS (User Management Microservice) container spec:
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: mysql-db-password    # Same Secret, same key
        key: db-password
```

Both Deployments reference the same Secret. When you rotate the password, update the Secret once and restart both Deployments.

**Step 5: Deploy and test**

```bash
# Create all objects
kubectl apply -f kube-manifests/

# List pods
kubectl get pods

# Access application
# http://<WorkerNode-Public-IP>:31231/usermgmt/health-status

# Verify the secret exists
kubectl get secret mysql-db-password -o yaml

# Decode the secret value
kubectl get secret mysql-db-password -o jsonpath='{.data.db-password}' | base64 -d
# Output: dbpassword11
```

**Step 6: Clean up**

```bash
kubectl delete -f kube-manifests/
kubectl get pods
kubectl get sc,pvc,pv
```

### Secret Types

| Type | Description | Example |
|---|---|---|
| `Opaque` | Generic unstructured key-value pairs (default type) | Passwords, API keys |
| `kubernetes.io/tls` | TLS certificate + key | HTTPS certificates |
| `kubernetes.io/dockerconfigjson` | Docker registry credentials | ECR pull secrets |
| `kubernetes.io/service-account-token` | Service account token | Auto-generated |

**`Opaque` explained:** From Kubernetes's point of view, the contents of an Opaque Secret are unstructured — it can contain arbitrary key-value pairs. Kubernetes does not validate or interpret the data. This is the default type when you don't specify `type`.

**Secret size limit:** Each Secret object must be <= 1 MB.

**Deployment with multiple volume-mounted secrets:**

```yaml
# deploy-with-secrets.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mydeployments
spec:
  replicas: 1
  selector:
    matchLabels:
      name: deployment
  template:
    metadata:
      labels:
        name: deployment
    spec:
      containers:
      - name: c00
        image: ubuntu
        command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
        volumeMounts:
        - name: passwdsecret
          mountPath: "/tmp/passwd"       # Mounted as read-only by default
        - name: certificate
          mountPath: "/tmp/certs"
      volumes:
      - name: passwdsecret
        secret:
          secretName: mypasswd
      - name: certificate
        secret:
          secretName: mycert
```

**Secret value as environment variable:**

```yaml
# env-secret-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: myenvsecret
spec:
  containers:
  - name: c1
    image: centos
    command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
    env:
    - name: MYDBPASSWD
      valueFrom:
        secretKeyRef:
          name: mypasswd
          key: password.txt
```

### Encrypting Secrets at Rest in etcd

By default, Secrets are stored **unencrypted** in etcd. Anyone with etcd access can read all Secrets in plain text. For non-managed clusters (kubeadm, bare-metal), you must configure encryption at rest manually. On managed services (EKS, GKE, AKS), etcd encryption is handled automatically.

**Step 0: Check if encryption at rest is already enabled:**

```bash
# Check the API server process for the encryption flag
ps aux | grep kube-api | grep encryption-provider-config

# Or check the static pod manifest directly
grep encryption-provider-config /etc/kubernetes/manifests/kube-apiserver.yaml
```

If neither returns output, encryption at rest is not configured.

**Installing etcdctl (if not available):**

```bash
# Ubuntu/Debian
apt-get install etcd-client

# Verify installation — use API v3
ETCDCTL_API=3 etcdctl version
```

**Step 1: Create an EncryptionConfiguration file:**

```yaml
# /etc/kubernetes/enc/enc.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <base64-encoded-32-byte-key>
  - identity: {}    # Fallback: allows reading unencrypted secrets
```

Generate a 32-byte encryption key:

```bash
head -c 32 /dev/urandom | base64
```

**Provider options:**

| Provider | Encryption | Strength | Notes |
|---|---|---|---|
| `identity` | None | N/A | Default — stores in plain text |
| `aescbc` | AES-CBC | Strong | Recommended for most clusters |
| `aesgcm` | AES-GCM | Strong | Faster, but key must be rotated frequently |
| `secretbox` | XSalsa20+Poly1305 | Strong | Modern, fast |
| `kms` | External KMS | Strongest | Delegates to AWS KMS, GCP KMS, etc. |

Provider order matters: the **first** provider is used for encryption, all listed providers are tried for decryption. Always list `identity` last as a fallback to read pre-existing unencrypted secrets.

**Step 2: Configure the API server to use the encryption config:**

Edit the kube-apiserver static pod manifest:

```bash
vi /etc/kubernetes/manifests/kube-apiserver.yaml
```

Add the flag and volume mount:

```yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --encryption-provider-config=/etc/kubernetes/enc/enc.yaml   # Add this
    # ... other flags
    volumeMounts:
    - name: enc
      mountPath: /etc/kubernetes/enc
      readOnly: true
  volumes:
  - name: enc
    hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
```

The API server restarts automatically after saving the manifest.

**Step 3: Encrypt existing secrets:**

New secrets are encrypted automatically. To encrypt existing secrets, re-write them:

```bash
kubectl get secrets -A -o json | kubectl replace -f -
```

**Step 4: Verify encryption is working:**

```bash
# Read a secret directly from etcd (requires etcdctl)
ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/my-secret | hexdump -C
```

If encryption is working, the output shows encrypted binary data prefixed with `k8s:enc:aescbc:v1:key1`. Without encryption, you'd see the secret values in plain text.

> **CKA Exam Tip:** You may be asked to enable encryption at rest. The steps are: create the EncryptionConfiguration file, add `--encryption-provider-config` to the API server manifest, and verify with etcdctl. Remember that `identity` provider means no encryption.

### AWS Secrets Manager Integration

For production, use AWS Secrets Manager with the Secrets Store CSI Driver.

```bash
# Install Secrets Store CSI Driver
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver \
  --namespace kube-system \
  --set syncSecret.enabled=true

# Install AWS provider
kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```

```yaml
# aws-secret-provider.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-secrets
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/database/credentials"
        objectType: "secretsmanager"
        jmesPath:
          - path: username
            objectAlias: db_username
          - path: password
            objectAlias: db_password
  secretObjects:
  - secretName: db-creds-k8s
    type: Opaque
    data:
    - objectName: db_username
      key: username
    - objectName: db_password
      key: password
```

```yaml
# Pod using AWS Secrets Manager
apiVersion: v1
kind: Pod
metadata:
  name: app-with-aws-secrets
spec:
  serviceAccountName: secrets-sa    # Needs IRSA with SecretsManager access
  containers:
  - name: app
    image: nginx:1.25
    envFrom:
    - secretRef:
        name: db-creds-k8s
    volumeMounts:
    - name: secrets-store
      mountPath: /mnt/secrets
      readOnly: true
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets
```

### Updating a Secret (Password Rotation)

Multiple ways to update a Secret value in a running cluster:

**Method 1: kubectl edit (interactive)**

```bash
# Opens the Secret in your default editor
kubectl edit secret db-credentials

# The values are base64-encoded in the editor
# To get the new base64 value:
echo -n 'NewP@ssw0rd!' | base64
# Output: TmV3UEBzc3cwcmQh

# Replace the old base64 value with the new one in the editor, save and exit
```

**Method 2: kubectl create --dry-run + replace (scripted)**

```bash
# Best for automation — recreates the Secret with new values
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='NewP@ssw0rd!' \
  --dry-run=client -o yaml | kubectl apply -f -

# Output:
# secret/db-credentials configured

# Verify the update
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
# Output: NewP@ssw0rd!
```

**Method 3: kubectl patch (single field)**

```bash
# Update just the password field
kubectl patch secret db-credentials -p \
  "{\"data\":{\"password\":\"$(echo -n 'NewP@ssw0rd!' | base64)\"}}"

# Output:
# secret/db-credentials patched
```

**Method 4: Export, edit, re-apply**

```bash
# Export current Secret
kubectl get secret db-credentials -o yaml > current-secret.yaml

# Edit the file — update the base64-encoded password
# Then re-apply
kubectl apply -f current-secret.yaml

# Clean up the exported file (contains sensitive data!)
rm current-secret.yaml
```

**What happens to running pods after a Secret update?**

| Mount Type | Behavior | Action Needed |
|---|---|---|
| Volume mount (`volumeMounts`) | Auto-updated within ~1 minute (kubelet sync period) | App must re-read the file |
| Environment variable (`env.valueFrom.secretKeyRef`) | NOT updated until pod restart | Restart pods: `kubectl rollout restart deployment/<name>` |
| Projected volume | Auto-updated within ~1 minute | App must re-read the file |

```bash
# Force pods to pick up new env-based secrets
kubectl rollout restart deployment/myapp

# Output:
# deployment.apps/myapp restarted

kubectl rollout status deployment/myapp

# Output:
# deployment "myapp" successfully rolled out
```

**Interview question: How do you update a password in a Kubernetes Secret?**
Use `kubectl create secret --dry-run=client -o yaml | kubectl apply -f -` for scripted updates, or `kubectl edit secret` for interactive changes. Values must be base64-encoded. If pods use the secret as environment variables, they must be restarted (`kubectl rollout restart`) to pick up changes. Volume-mounted secrets auto-update within ~1 minute.

---

### Sealed Secrets — Encrypted Secrets for GitOps

Standard Kubernetes Secrets are base64-encoded (not encrypted), so you can't safely commit them to Git. Sealed Secrets (by Bitnami) solve this by encrypting secrets client-side so only the cluster can decrypt them.

**How it works:**

```
Developer                          Cluster
─────────                          ───────
                                   ┌──────────────────────┐
kubectl create secret              │  Sealed Secrets      │
  --dry-run -o yaml                │  Controller          │
       │                           │  (has private key)   │
       ▼                           └──────────┬───────────┘
┌──────────────┐                              │
│ Secret YAML  │──► kubeseal ──► SealedSecret │
│ (plaintext)  │    (encrypts    (safe to     │
│ NEVER commit │     with pub    commit to    │
│ to Git)      │     key)        Git)         │
└──────────────┘                     │        │
                                     ▼        ▼
                              Git repo → Controller decrypts
                                         → creates K8s Secret
```

**Install Sealed Secrets controller:**

```bash
# Install the controller in the cluster
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update

helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system

# Install kubeseal CLI
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.5/kubeseal-0.24.5-linux-amd64.tar.gz
tar -xvzf kubeseal-0.24.5-linux-amd64.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

**Create a Sealed Secret:**

```bash
# Step 1: Create a regular secret (don't apply it)
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='S3cur3P@ss!' \
  --namespace production \
  --dry-run=client -o yaml > secret.yaml

# Step 2: Encrypt it with kubeseal
kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# Step 3: Commit the sealed secret to Git (safe!)
cat sealed-secret.yaml
```

**Output (sealed-secret.yaml):**

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  encryptedData:
    username: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEq...
    password: AgCtr8OJSWK+PiTySYZZA9rO43cGDEq...
  template:
    metadata:
      name: db-credentials
      namespace: production
```

```bash
# Step 4: Apply the sealed secret
kubectl apply -f sealed-secret.yaml

# The controller decrypts it and creates a regular Secret
kubectl get secret db-credentials -n production
# NAME              TYPE     DATA   AGE
# db-credentials    Opaque   2      5s
```

**When to use each approach:**

| Approach | Use When |
|----------|----------|
| **Sealed Secrets** | GitOps workflows where secrets must be in Git |
| **External Secrets Operator** | Secrets live in AWS Secrets Manager / Vault and sync to K8s |
| **Vault Agent Sidecar** | Dynamic secrets, fine-grained access policies, audit logging |
| **K8s Secrets + encryption at rest** | Simple setups without GitOps |

---

### Get Secrets at Runtime from HashiCorp Vault

Instead of storing secrets in Kubernetes Secret objects (base64-encoded, stored in etcd), inject them at runtime from HashiCorp Vault.

```
┌──────────────────────────────────────────────────────────────┐
│  Vault Integration Methods                                   │
│                                                              │
│  Method 1: Vault Agent Sidecar Injector                      │
│  ┌──────────────────┐                                        │
│  │  Pod              │                                       │
│  │  ┌────────────┐  │    ┌─────────┐                         │
│  │  │  App        │  │    │  Vault  │                         │
│  │  │  Container  │  │    │  Server │                         │
│  │  └─────▲──────┘  │    └────▲────┘                         │
│  │        │ reads    │         │                              │
│  │  ┌─────┴──────┐  │         │ authenticates                │
│  │  │  Vault     │──┼─────────┘ + fetches secrets            │
│  │  │  Agent     │  │                                        │
│  │  │  (sidecar) │  │  Writes secrets to shared volume       │
│  │  └────────────┘  │  at /vault/secrets/                    │
│  └──────────────────┘                                        │
│                                                              │
│  Method 2: Secrets Store CSI Driver + Vault Provider         │
│  (Already covered in §5.5 — mount secrets as volumes)        │
│                                                              │
│  Method 3: External Secrets Operator                         │
│  (Syncs Vault secrets → K8s Secrets automatically)           │
└──────────────────────────────────────────────────────────────┘
```

**Method 1: Vault Agent Sidecar Injector (most common)**

```bash
# Step 1: Install Vault via Helm
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --namespace vault --create-namespace \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"

# Step 2: Verify Vault is running
kubectl get pods -n vault

# Output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# vault-0                                 1/1     Running   0          2m
# vault-agent-injector-5b8f4d7c9-abc12    1/1     Running   0          2m

# Step 3: Configure Vault (store a secret)
kubectl exec -n vault vault-0 -- vault kv put secret/myapp/config \
  db_username="admin" \
  db_password="SuperSecret123" \
  api_key="sk-abc123def456"

# Step 4: Enable Kubernetes auth in Vault
kubectl exec -n vault vault-0 -- vault auth enable kubernetes

kubectl exec -n vault vault-0 -- vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"

# Step 5: Create a Vault policy
kubectl exec -n vault vault-0 -- vault policy write myapp-policy - <<EOF
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF

# Step 6: Create a Vault role linked to K8s service account
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp-sa \
  bound_service_account_namespaces=default \
  policies=myapp-policy \
  ttl=1h
```

```yaml
# Step 7: Deploy app with Vault annotations
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
      annotations:
        vault.hashicorp.com/agent-inject: "true"                    # Enable sidecar
        vault.hashicorp.com/role: "myapp"                           # Vault role
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"  # Secret path
        vault.hashicorp.com/agent-inject-template-config: |         # Template format
          {{- with secret "secret/data/myapp/config" -}}
          export DB_USERNAME="{{ .Data.data.db_username }}"
          export DB_PASSWORD="{{ .Data.data.db_password }}"
          export API_KEY="{{ .Data.data.api_key }}"
          {{- end }}
    spec:
      serviceAccountName: myapp-sa
      containers:
      - name: app
        image: myapp:v1.0
        command: ["sh", "-c", "source /vault/secrets/config && exec myapp"]
```

```bash
kubectl apply -f myapp-deployment.yaml

# Verify secrets are injected
kubectl exec deploy/myapp -c app -- cat /vault/secrets/config

# Output:
# export DB_USERNAME="admin"
# export DB_PASSWORD="SuperSecret123"
# export API_KEY="sk-abc123def456"

# The pod has 2 containers: app + vault-agent (sidecar)
kubectl get pods -l app=myapp

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE
# myapp-7b8c9d6e8-abc12    2/2     Running   0          30s
#                          ^^^
#                          2 containers: app + vault-agent
```

**Vault vs Kubernetes Secrets vs AWS Secrets Manager:**

| Feature | K8s Secrets | AWS Secrets Manager | HashiCorp Vault |
|---|---|---|---|
| **Storage** | etcd (base64) | AWS managed | Self-hosted or HCP |
| **Encryption at rest** | Optional (EncryptionConfig) | Always (KMS) | Always |
| **Rotation** | Manual | Automatic | Automatic |
| **Audit** | K8s audit logs | CloudTrail | Vault audit logs |
| **Dynamic secrets** | No | No | Yes (DB creds on demand) |
| **Access control** | RBAC | IAM policies | Vault policies |
| **Best for** | Simple configs | AWS-native apps | Multi-cloud, strict compliance |

**Interview question: How do you get secrets at runtime from Vault in Kubernetes?**
Use the Vault Agent Sidecar Injector. Install Vault via Helm with `injector.enabled=true`. Configure Kubernetes auth in Vault, create a policy and role linked to a K8s ServiceAccount. Annotate pods with `vault.hashicorp.com/agent-inject` annotations — the injector automatically adds a sidecar that authenticates to Vault, fetches secrets, and writes them to `/vault/secrets/` as files. The app reads secrets from files, not environment variables, and Vault Agent auto-renews them.

### External Secrets Operator (ESO) — Sync External Secrets to Kubernetes

The External Secrets Operator syncs secrets from external providers (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager, Azure Key Vault) into Kubernetes Secret objects automatically.

**How it works:**

```
┌──────────────────────┐     ┌──────────────────────┐
│  External Provider   │     │  Kubernetes Cluster   │
│  (AWS Secrets Mgr,   │     │                      │
│   Vault, GCP, Azure) │     │  ExternalSecret CRD  │
│                      │◄────│  (defines what to    │
│  secret/db-password  │     │   sync and where)    │
│  = "S3cur3P@ss!"     │     │         │            │
└──────────────────────┘     │         ▼            │
                             │  K8s Secret object   │
                             │  (auto-created and   │
                             │   kept in sync)      │
                             └──────────────────────┘
```

**Install External Secrets Operator:**

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace
```

**Step 1: Create a SecretStore (connection to the external provider):**

```yaml
# secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        secretRef:
          accessKeyIDSecretRef:
            name: aws-credentials
            key: access-key-id
          secretAccessKeySecretRef:
            name: aws-credentials
            key: secret-access-key
```

**Step 2: Create an ExternalSecret (defines what to sync):**

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  refreshInterval: 1h              # Sync every hour
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: db-secret                 # K8s Secret name to create
    creationPolicy: Owner           # ESO owns the Secret lifecycle
  data:
  - secretKey: username             # Key in the K8s Secret
    remoteRef:
      key: prod/db/credentials      # Key in AWS Secrets Manager
      property: username            # JSON property within the secret
  - secretKey: password
    remoteRef:
      key: prod/db/credentials
      property: password
```

```bash
kubectl apply -f secret-store.yaml
kubectl apply -f external-secret.yaml

# Verify the ExternalSecret synced successfully
kubectl get externalsecret -n production
# NAME              STORE                  REFRESH   STATUS         READY
# db-credentials    aws-secrets-manager    1h        SecretSynced   True

# The K8s Secret was auto-created
kubectl get secret db-secret -n production
# NAME        TYPE     DATA   AGE
# db-secret   Opaque   2      30s

# Use it in a pod like any other Secret
kubectl get secret db-secret -n production -o jsonpath='{.data.password}' | base64 -d
# S3cur3P@ss!
```

**For Vault as the provider:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "http://vault.vault:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
```

**When to use ESO vs Vault Agent Sidecar:**

| Feature | External Secrets Operator | Vault Agent Sidecar |
|---------|--------------------------|---------------------|
| **How secrets arrive** | Synced into K8s Secret objects | Injected as files in pod filesystem |
| **Pod modification** | None — pods use standard K8s Secrets | Sidecar container added to every pod |
| **Refresh** | Periodic sync (configurable interval) | Real-time via Vault Agent |
| **Dynamic secrets** | No (syncs static values) | Yes (Vault generates on demand) |
| **Best for** | Teams already using K8s Secrets in manifests | Strict security requiring no K8s Secret objects |

### Lab: Working with Kubernetes Secrets

**Exercise 1: Inspect the default service account secret**

```bash
kubectl get secrets
```

```
NAME                  TYPE                                  DATA   AGE
default-token-cr4sr   kubernetes.io/service-account-token   3      7m
```

```bash
kubectl describe secret default-token-cr4sr
```

```
Name:         default-token-cr4sr
Namespace:    default
Type:         kubernetes.io/service-account-token

Data
====
ca.crt:     570 bytes
namespace:  7 bytes
token:      eyJhbGciOiJSUzI1NiIs...
```

This secret is auto-generated for the default service account. It contains three data fields: `ca.crt` (cluster CA certificate), `namespace`, and `token` (authentication token).

**Exercise 2: Diagnose a failing application**

A web application can't connect to MySQL:

```bash
kubectl get pods
```

```
NAME         READY   STATUS    RESTARTS   AGE
webapp-pod   1/1     Running   0          26s
mysql        1/1     Running   0          26s
```

Accessing the app shows:

```
Environment Variables: DB_Host=Not Set; DB_Database=Not Set; DB_User=Not Set; DB_Password=Not Set;
2003: Can't connect to MySQL server on 'localhost:3306' (111 Connection refused)
```

The database credentials haven't been provided. Create a secret:

```bash
# Check available secret subcommands
kubectl create secret --help
```

```
Available Commands:
  docker-registry   Create a secret for use with a Docker registry
  generic           Create a secret from a local file, directory, or literal value
  tls               Create a TLS secret
```

```bash
# Create the database credentials secret
kubectl create secret generic db-secret \
  --from-literal=DB_Host=sql01 \
  --from-literal=DB_User=root \
  --from-literal=DB_Password=password123
```

```bash
kubectl get secrets
```

```
NAME                  TYPE                                  DATA   AGE
default-token-cr4sr   kubernetes.io/service-account-token   3      12m
db-secret             Opaque                                3      6s
```

**Exercise 3: Configure the pod to use the secret**

```bash
kubectl edit pod webapp-pod
```

Add `envFrom` to the container spec:

```yaml
spec:
  containers:
  - name: webapp
    image: kodekloud/simple-webapp-mysql
    envFrom:
    - secretRef:
        name: db-secret
```

Since pods are immutable, force-replace:

```bash
kubectl replace --force -f /tmp/kubectl-edit-webapp.yaml
```

```
pod "webapp-pod" deleted
pod/webapp-pod replaced
```

Verify the application now connects:

```
Environment Variables: DB_Host=sql01; DB_Database=Not Set; DB_User=root; DB_Password=password123;
Successfully connected to the MySQL database.
```

The `DB_Host`, `DB_User`, and `DB_Password` are now loaded from the secret. `DB_Database` is still "Not Set" because it wasn't included in the secret — add it with `kubectl edit secret` or recreate the secret if needed.

### Real-World Secrets Example — MySQL + User Management Microservice

A complete multi-file application using Secrets for database credentials. This demonstrates how Secrets, ConfigMaps, PVCs, Deployments, and Services work together.

**File 1: StorageClass** — EBS dynamic provisioning:

```yaml
# 01-storage-class.yml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
```

**File 2: PVC** — Request 4Gi EBS volume:

```yaml
# 02-persistent-volume-claim.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-mysql-pv-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
```

**File 3: ConfigMap** — Database initialization script:

```yaml
# 03-UserManagement-ConfigMap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: usermanagement-dbcreation-script
data:
  mysql_usermgmt.sql: |-
    DROP DATABASE IF EXISTS usermgmt;
    CREATE DATABASE usermgmt;
```

**File 4: MySQL Deployment** — Uses Secret for root password, mounts PVC and ConfigMap:

```yaml
# 04-mysql-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  strategy:
    type: Recreate       # Delete old pod before creating new (required for RWO volumes)
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:5.6
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-db-password
                  key: db-password       # Reads password from Secret
          ports:
            - containerPort: 3306
              name: mysql
          volumeMounts:
            - name: mysql-persistent-storage
              mountPath: /var/lib/mysql
            - name: usermanagement-dbcreation-script
              mountPath: /docker-entrypoint-initdb.d   # MySQL runs .sql files here on first start
      volumes:
        - name: mysql-persistent-storage
          persistentVolumeClaim:
            claimName: ebs-mysql-pv-claim
        - name: usermanagement-dbcreation-script
          configMap:
            name: usermanagement-dbcreation-script
```

**File 5: MySQL Headless Service** — ClusterIP: None for direct pod IP access:

```yaml
# 05-mysql-clusterip-service.yml
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
  clusterIP: None    # Headless — clients connect directly via pod IP
```

**File 6: User Management Microservice** — Init container waits for MySQL, includes probes and resource limits:

```yaml
# 06-UserManagementMicroservice-Deployment-Service.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: usermgmt-microservice
  labels:
    app: usermgmt-restapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: usermgmt-restapp
  template:
    metadata:
      labels:
        app: usermgmt-restapp
    spec:
      initContainers:
        - name: init-db
          image: busybox:1.31
          command: ['sh', '-c', 'echo -e "Checking for the availability of MySQL Server deployment"; while ! nc -z mysql 3306; do sleep 1; printf "-"; done; echo -e "  >> MySQL DB Server has started";']
      containers:
        - name: usermgmt-restapp
          image: stacksimplify/kube-usermanagement-microservice:1.0.0
          ports:
            - containerPort: 8095
          env:
            - name: DB_HOSTNAME
              value: "mysql"
            - name: DB_PORT
              value: "3306"
            - name: DB_NAME
              value: "usermgmt"
            - name: DB_USERNAME
              value: "root"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-db-password
                  key: db-password
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - nc -z localhost 8095
            initialDelaySeconds: 60
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /usermgmt/health-status
              port: 8095
            initialDelaySeconds: 60
            periodSeconds: 10
          resources:
            requests:
              cpu: "500m"
              memory: "128Mi"
            limits:
              cpu: "1000m"
              memory: "500Mi"
```

**File 7: NodePort Service** — Exposes the microservice externally:

```yaml
# 07-UserManagement-Service.yml
apiVersion: v1
kind: Service
metadata:
  name: usermgmt-restapp-service
  labels:
    app: usermgmt-restapp
spec:
  type: NodePort
  selector:
    app: usermgmt-restapp
  ports:
    - port: 8095
      targetPort: 8095
      nodePort: 31231
```

**File 8: Secret** — Database password (base64-encoded):

```yaml
# 08-Kubernetes-Secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-db-password
type: Opaque
data:
  db-password: ZGJwYXNzd29yZDEx    # echo -n "dbpassword11" | base64
```

**Deploy and test:**

```bash
# Create all objects
kubectl apply -f kube-manifests/

# Watch pods — init container runs first, then app container
kubectl get pods -w

# Describe pod to see init container details
kubectl describe pod <usermgmt-microservice-xxxxxx>

# Access application
# http://<WorkerNode-Public-IP>:31231/usermgmt/health-status

# Verify storage
kubectl get sc,pvc,pv

# Clean up
kubectl delete -f kube-manifests/
kubectl get pods
kubectl get sc,pvc,pv
```

---

