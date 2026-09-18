# MODULE 32: etcd Operations & Disaster Recovery

---

## 32.1 etcd Operations & Disaster Recovery

### etcd Backup

etcd stores all cluster state. Regular backups are essential for disaster recovery.

```bash
# Create a snapshot backup
sudo ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-backup-$(date +%Y%m%d).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify the backup
sudo ETCDCTL_API=3 etcdctl snapshot status /tmp/etcd-backup-*.db --write-table

# Output:
# +----------+----------+------------+------------+
# |   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
# +----------+----------+------------+------------+
# | 3e5a0b2c |   145892 |       1247 |     5.2 MB |
# +----------+----------+------------+------------+
```

### etcd Restore

**Step 1: Restore the snapshot to a new data directory**

The restore command does not need to contact a running etcd — it reads the snapshot file directly:

```bash
ETCDCTL_API=3 etcdctl snapshot restore /opt/snapshot-pre-boot.db \
  --data-dir=/var/lib/etcd-from-backup

# Output:
# 2024-01-15 10:54:34.669639 I | mvcc: restore compact to 2377
# 2024-01-15 10:54:34.676896 I | etcdserver/membership: added member 8e9e05c52164694d [http://localhost:2380] to cluster cdf818194e3a8c32
```

**Step 2: Update the etcd static pod manifest to use the new data directory**

Edit `/etc/kubernetes/manifests/etcd.yaml` — change the `hostPath` for the `etcd-data` volume to point to the restored directory:

```yaml
# BEFORE (in etcd.yaml volumes section):
volumes:
  - hostPath:
      path: /var/lib/etcd            # ← original data directory
      type: DirectoryOrCreate
    name: etcd-data

# AFTER:
volumes:
  - hostPath:
      path: /var/lib/etcd-from-backup  # ← restored data directory
      type: DirectoryOrCreate
    name: etcd-data
```

The kubelet detects the manifest change and automatically restarts the etcd pod. No need to manually stop/start the API server — the kubelet handles the static pod lifecycle.

**Step 3: Wait for the etcd pod to restart and verify**

```bash
# Watch the etcd pod restart
kubectl get pods -n kube-system --watch

# Output:
# NAME                                   READY   STATUS    RESTARTS   AGE
# etcd-controlplane                      0/1     Pending   0          5s
# etcd-controlplane                      1/1     Running   0          12s
# kube-apiserver-controlplane            1/1     Running   0          37m
# kube-controller-manager-controlplane   1/1     Running   1          37m

# Verify restored resources
kubectl get deployments
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# blue   3/3     3            3           18s
# red    2/2     2            2           18s
```

⚠️ If the etcd pod fails to reach Running (e.g., liveness probe failures), delete the pod to force a restart: `kubectl delete pod etcd-controlplane -n kube-system`

### Automated Backup with CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etcd-backup
  namespace: kube-system
spec:
  schedule: "0 */6 * * *"    # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          hostNetwork: true
          containers:
          - name: backup
            image: bitnami/etcd:3.5
            command: ["/bin/sh", "-c"]
            args:
            - |
              etcdctl snapshot save /backup/etcd-$(date +%Y%m%d-%H%M).db \
                --endpoints=https://127.0.0.1:2379 \
                --cacert=/etc/kubernetes/pki/etcd/ca.crt \
                --cert=/etc/kubernetes/pki/etcd/server.crt \
                --key=/etc/kubernetes/pki/etcd/server.key
            volumeMounts:
            - name: etcd-certs
              mountPath: /etc/kubernetes/pki/etcd
              readOnly: true
            - name: backup-dir
              mountPath: /backup
          volumes:
          - name: etcd-certs
            hostPath:
              path: /etc/kubernetes/pki/etcd
          - name: backup-dir
            hostPath:
              path: /opt/etcd-backups
          restartPolicy: OnFailure
          nodeSelector:
            node-role.kubernetes.io/control-plane: ""
          tolerations:
          - key: node-role.kubernetes.io/control-plane
            effect: NoSchedule
```

### Backup Candidates — What to Back Up

There are two categories of data to protect:

1. **Resource configurations** — Deployments, Services, ConfigMaps, Secrets, PVCs, etc.
2. **Persistent data** — etcd (cluster state), PersistentVolumes (application data)

### Three Approaches to Backing Up Resource Configurations

**Approach 1: Declarative (Source Control)**

If all resources are created from YAML files stored in Git, the repository itself is the backup. This is the preferred approach — just re-apply from source control.

```bash
# Restore everything from Git
kubectl apply -f ./manifests/ --recursive
```

⚠️ This only works if ALL resources are created declaratively. Objects created with `kubectl create`, `kubectl run`, or `kubectl expose` won't be in Git.

**Approach 2: Imperative (Query the API Server)**

Export all resource configurations from the running cluster:

```bash
# Back up all resources across all namespaces
kubectl get all --all-namespaces -o yaml > all-resources-backup.yaml

# More targeted backups
kubectl get deployments -A -o yaml > deployments-backup.yaml
kubectl get services -A -o yaml > services-backup.yaml
kubectl get configmaps -A -o yaml > configmaps-backup.yaml
kubectl get secrets -A -o yaml > secrets-backup.yaml
kubectl get pvc -A -o yaml > pvcs-backup.yaml
```

⚠️ `kubectl get all` doesn't actually get ALL resources — it misses ConfigMaps, Secrets, Roles, RoleBindings, etc. Use targeted commands or tools like [ARK/Velero](#velero-backup-and-restore) for complete backups.

**Approach 3: etcd Snapshot (Cluster State)**

Back up etcd directly — this captures everything since etcd stores all cluster state:

```bash
# Already covered above — etcdctl snapshot save
ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

**Why `ETCDCTL_API=3`?** etcdctl supports both API v2 and v3. Kubernetes uses etcd v3 API. Setting this environment variable ensures you use the correct API version. Without it, commands may silently use v2 and produce empty or incorrect results.

**Comparison of the three approaches:**

| Approach | Pros | Cons |
|---|---|---|
| Declarative (Git) | Version history, review process, GitOps-ready | Only works if everything is in Git |
| Imperative (API query) | Captures imperatively-created resources | `kubectl get all` is incomplete; exports contain runtime fields |
| etcd snapshot | Complete cluster state, single command | Restores everything (can't selectively restore); requires etcd access |

### Velero — Backup and Restore

[Velero](https://velero.io/) (formerly Heptio ARK) is the standard tool for Kubernetes backup and restore. It backs up both resource configurations and persistent volume data.

**What Velero does:**
- Backs up Kubernetes resources (all API objects) to object storage (S3, GCS, Azure Blob)
- Snapshots PersistentVolumes using cloud provider snapshot APIs
- Supports scheduled backups, retention policies, and namespace-level restores
- Migrates resources between clusters

```bash
# Install Velero CLI
brew install velero   # macOS
# or download from https://github.com/vmware-tanzu/velero/releases

# Install Velero in the cluster (AWS example)
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.9.0 \
  --bucket my-velero-backups \
  --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1 \
  --secret-file ./credentials-velero

# Create a one-time backup
velero backup create my-backup

# Create a backup of a specific namespace
velero backup create my-backup --include-namespaces production

# Schedule daily backups with 7-day retention
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --ttl 168h

# List backups
velero backup get

# Restore from backup
velero restore create --from-backup my-backup

# Restore only a specific namespace
velero restore create --from-backup my-backup --include-namespaces production
```

### Stacked vs External etcd Topology

etcd can be deployed in two topologies. The backup and restore procedure differs depending on which one your cluster uses.

**Stacked etcd** — etcd runs as a static pod on the control plane node (the default with `kubeadm init`):

```bash
# How to identify stacked etcd:
# 1. An etcd pod exists in kube-system
kubectl get pods -n kube-system | grep etcd
# etcd-controlplane   1/1   Running   0   55m

# 2. The API server's --etcd-servers points to localhost
kubectl describe pod kube-apiserver-controlplane -n kube-system | grep etcd-servers
# --etcd-servers=https://127.0.0.1:2379
```

- Backup/restore: Use `etcdctl` on the control plane node with certs from `/etc/kubernetes/pki/etcd/`
- Configuration: Static pod manifest at `/etc/kubernetes/manifests/etcd.yaml`
- To change data directory after restore: edit the `hostPath` in `etcd.yaml`

**External etcd** — etcd runs as a systemd service on a separate server:

```bash
# How to identify external etcd:
# 1. No etcd pod in kube-system
kubectl get pods -n kube-system | grep etcd
# (no output)

# 2. The API server's --etcd-servers points to an external IP
kubectl describe pod kube-apiserver-controlplane -n kube-system | grep etcd-servers
# --etcd-servers=https://192.33.162.21:2379
```

- Backup/restore: SSH into the external etcd server, use `etcdctl` with certs from that server
- Configuration: systemd service file at `/etc/systemd/system/etcd.service`
- To change data directory after restore: edit `--data-dir` in the service file, then `systemctl daemon-reload && systemctl restart etcd`

**Comparison:**

| Aspect | Stacked etcd | External etcd |
|---|---|---|
| Where etcd runs | Control plane node (static pod) | Separate dedicated server(s) |
| Config location | `/etc/kubernetes/manifests/etcd.yaml` | `/etc/systemd/system/etcd.service` |
| Cert location | `/etc/kubernetes/pki/etcd/` | Varies (e.g., `/etc/etcd/pki/`) |
| Restart method | kubelet auto-restarts on manifest change | `systemctl daemon-reload && systemctl restart etcd` |
| Pros | Simpler setup, fewer servers | Isolates etcd failures from control plane |
| Cons | etcd competes for resources with API server | More infrastructure to manage |

### Lab: Multi-Cluster etcd Backup and Restore

**Scenario:** You manage two clusters from a student/bastion node. Cluster1 uses stacked etcd. Cluster2 uses external etcd. Back up cluster1's etcd and restore cluster2 from an existing backup.

```bash
# === STEP 1: Verify environment ===

# Check available clusters in kubeconfig
kubectl config view
# apiVersion: v1
# clusters:
# - cluster:
#     server: https://cluster1-controlplane:6443
#   name: cluster1
# - cluster:
#     server: https://192.33.162.10:6443
#   name: cluster2
# current-context: cluster1

# Switch between clusters
kubectl config use-context cluster1
kubectl config use-context cluster2
```

```bash
# === STEP 2: Identify etcd topology for each cluster ===

# Cluster1 — stacked etcd (etcd pod exists)
kubectl config use-context cluster1
kubectl get pods -n kube-system | grep etcd
# etcd-cluster1-controlplane   1/1   Running   0   55m

# Cluster2 — external etcd (no etcd pod, external endpoint)
kubectl config use-context cluster2
kubectl get pods -n kube-system | grep etcd
# (no output)

kubectl describe pod kube-apiserver-cluster2-controlplane -n kube-system | grep etcd-servers
# --etcd-servers=https://192.33.162.21:2379
```

```bash
# === STEP 3: Back up cluster1 (stacked etcd) ===

# SSH into the control plane node
ssh cluster1-controlplane

# Find the data directory and cert paths
kubectl describe pod etcd-cluster1-controlplane -n kube-system | grep -E "data-dir|cert-file|ca-file|key-file"

# Take the snapshot
ETCDCTL_API=3 etcdctl snapshot save /opt/cluster1.db \
  --endpoints=https://192.33.162.8:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
# Snapshot saved at /opt/cluster1.db

exit  # back to student node

# Copy snapshot to student node
scp cluster1-controlplane:/opt/cluster1.db /opt/cluster1.db
```

```bash
# === STEP 4: Restore cluster2 (external etcd) ===

# Copy the backup to the external etcd server
scp /opt/cluster2.db etcd-server:/root/

# SSH into the external etcd server
ssh etcd-server

# Restore to a new data directory
ETCDCTL_API=3 etcdctl snapshot restore /root/cluster2.db \
  --data-dir=/var/lib/etcd-data-new

# Set ownership (external etcd runs as the 'etcd' user, not root)
chown -R etcd:etcd /var/lib/etcd-data-new

# Update the systemd service file to use the new data directory
sudo vi /etc/systemd/system/etcd.service
# Change: --data-dir=/var/lib/etcd → --data-dir=/var/lib/etcd-data-new

# Restart etcd
sudo systemctl daemon-reload
sudo systemctl restart etcd

exit  # back to student node
```

```bash
# === STEP 5: Verify the restore ===

kubectl config use-context cluster2
kubectl get pods -n kube-system
# NAME                                             READY   STATUS    RESTARTS   AGE
# kube-apiserver-cluster2-controlplane             1/1     Running   0          79m
# kube-controller-manager-cluster2-controlplane    1/1     Running   0          79m
# kube-scheduler-cluster2-controlplane             1/1     Running   0          79m

# Verify restored resources
kubectl get deployments
kubectl get services
```

⚠️ After restoring external etcd, you may need to restart the kubelet on the control plane node (`ssh cluster2-controlplane && systemctl restart kubelet`) if the API server doesn't reconnect automatically.

---

## 32.2 Backup & Disaster Recovery Strategy

### RTO and RPO

Two metrics define your disaster recovery requirements:

| Metric | Full Name | Meaning | Example |
|---|---|---|---|
| **RTO** | Recovery Time Objective | Maximum acceptable downtime after a failure | "We must be back online within 1 hour" |
| **RPO** | Recovery Point Objective | Maximum acceptable data loss measured in time | "We can afford to lose at most 5 minutes of data" |

```
Timeline:
  ◄──── RPO ────►                    ◄──── RTO ────►
  Last backup     Data loss window    Failure    Recovery complete
  ─────┼──────────────────────────────┼───────────┼──────►
       10:00 AM                       10:30 AM   11:30 AM
       
  RPO = 30 min (data since last backup is lost)
  RTO = 1 hour (time to restore service)
```

**How RTO/RPO drive backup decisions:**

| RPO Target | Backup Strategy | Example |
|---|---|---|
| < 1 minute | Synchronous replication (multi-AZ database, etcd cluster) | RDS Multi-AZ, etcd 3-node cluster |
| 5-15 minutes | Frequent automated snapshots | Velero schedule every 15 min, EBS snapshots |
| 1-24 hours | Daily backups | etcd CronJob backup, nightly pg_dump |
| > 24 hours | Weekly/manual backups | Manual etcd snapshot before upgrades |

### Backup Strategies

| Strategy | What It Backs Up | Storage | Restore Speed | Use Case |
|---|---|---|---|---|
| **Full backup** | Everything, every time | High | Fast (single restore) | Weekly baseline |
| **Incremental** | Only changes since last backup (any type) | Low | Slower (chain of backups needed) | Frequent backups with low storage |
| **Differential** | Changes since last full backup | Medium | Medium (full + one differential) | Balance of speed and storage |
| **Snapshot** | Point-in-time copy of a volume | Varies | Fast | EBS snapshots, etcd snapshots |

**The 3-2-1 rule:**

```
3 copies of your data
2 different storage media (e.g., EBS + S3)
1 copy offsite (e.g., different AWS region)
```

**Real-life example — Kubernetes cluster backup strategy:**

```
┌─────────────────────────────────────────────────────┐
│  What to back up          How                Where   │
│  ─────────────────        ──────────────     ─────── │
│  etcd (cluster state)     etcdctl snapshot    S3     │
│  K8s resources (YAML)     Velero              S3     │
│  PersistentVolumes        EBS snapshots       AWS    │
│  Application databases    pg_dump CronJob     S3     │
│  Git repos (IaC)          Already in Git      GitHub │
│  Secrets/certs            Sealed Secrets      Git    │
└─────────────────────────────────────────────────────┘
```

### Database Backup as Kubernetes CronJobs

For stateful applications running in Kubernetes, back up databases using CronJobs that run dump commands and upload to S3.

**PostgreSQL backup CronJob:**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"    # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password
            command:
            - /bin/sh
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d-%H%M)
              pg_dump -h postgres-service -U admin mydb > /backup/pg-${TIMESTAMP}.sql
              # Upload to S3
              apt-get update -qq && apt-get install -y -qq awscli > /dev/null
              aws s3 cp /backup/pg-${TIMESTAMP}.sql s3://my-backups/postgres/
              echo "Backup completed: pg-${TIMESTAMP}.sql"
            volumeMounts:
            - name: backup-vol
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup-vol
            emptyDir: {}
```

**MySQL backup CronJob:**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mysql-backup
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: mysql:8.0
            env:
            - name: MYSQL_PWD
              valueFrom:
                secretKeyRef:
                  name: mysql-credentials
                  key: password
            command:
            - /bin/sh
            - -c
            - |
              mysqldump -h mysql-service -u root --all-databases > /backup/mysql-$(date +%Y%m%d).sql
              echo "MySQL backup completed"
          restartPolicy: OnFailure
```

**MongoDB backup CronJob:**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mongo-backup
spec:
  schedule: "0 4 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: mongo:7.0
            command:
            - /bin/sh
            - -c
            - |
              mongodump --host mongo-service --out /backup/mongo-$(date +%Y%m%d)
              echo "MongoDB backup completed"
            volumeMounts:
            - name: backup-vol
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup-vol
            persistentVolumeClaim:
              claimName: backup-pvc
```

### Disaster Recovery Testing

Backups are worthless if they can't be restored. Test regularly.

**Restore validation checklist:**

| # | Test | Command | Expected Result |
|---|---|---|---|
| 1 | etcd snapshot integrity | `etcdctl snapshot status backup.db --write-table` | Hash, revision, total keys displayed |
| 2 | etcd restore to temp cluster | `etcdctl snapshot restore backup.db --data-dir=/tmp/test-restore` | Restore completes without errors |
| 3 | Velero backup completeness | `velero backup describe my-backup --details` | Phase: Completed, 0 errors |
| 4 | Velero restore to test namespace | `velero restore create --from-backup my-backup --namespace-mappings prod:test-restore` | Resources created in test-restore namespace |
| 5 | Database restore | `psql -U admin -d testdb < backup.sql && psql -U admin -d testdb -c "SELECT count(*) FROM users"` | Row count matches expected |

**Automated restore testing with CI/CD:**

```yaml
# GitHub Actions workflow — test backup restore weekly
name: DR Restore Test
on:
  schedule:
    - cron: '0 6 * * 0'    # Every Sunday at 6 AM
jobs:
  test-restore:
    runs-on: ubuntu-latest
    steps:
    - name: Download latest backup from S3
      run: aws s3 cp s3://my-backups/postgres/latest.sql backup.sql

    - name: Start test PostgreSQL
      run: |
        docker run -d --name test-pg \
          -e POSTGRES_PASSWORD=test \
          -e POSTGRES_DB=testdb \
          postgres:15

    - name: Restore and validate
      run: |
        sleep 5
        docker exec -i test-pg psql -U postgres -d testdb < backup.sql
        ROWS=$(docker exec test-pg psql -U postgres -d testdb -t -c "SELECT count(*) FROM users")
        echo "Restored $ROWS rows"
        if [ "$ROWS" -lt 1 ]; then echo "RESTORE FAILED" && exit 1; fi

    - name: Notify on failure
      if: failure()
      run: |
        curl -X POST "$SLACK_WEBHOOK" \
          -d '{"text":"DR restore test FAILED — check backup integrity"}'
```

### Chaos Engineering for Kubernetes

Chaos engineering deliberately injects failures into a running system to verify that it recovers correctly. Instead of waiting for production outages, you simulate them in a controlled way.

**Why chaos engineering matters for DR:**

| Traditional DR Testing | Chaos Engineering |
|---|---|
| Restore from backup to a test cluster | Kill pods, nodes, and network in a live cluster |
| Tests backup integrity | Tests application resilience and self-healing |
| Done quarterly/annually | Done continuously (automated) |
| Validates data recovery | Validates HPA, PDB, circuit breakers, retries |

**LitmusChaos — Kubernetes-native chaos engineering:**

```bash
# Install LitmusChaos
kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v3.0.0.yaml

# Verify installation
kubectl get pods -n litmus
# NAME                                    READY   STATUS    RESTARTS   AGE
# litmus-server-0                         1/1     Running   0          2m
# litmus-auth-server-7b8c9d6e8-abc12      1/1     Running   0          2m

# Install chaos experiments
kubectl apply -f https://hub.litmuschaos.io/api/chaos/3.0.0?file=charts/generic/experiments.yaml -n litmus
```

**Example 1: Pod delete experiment — verify self-healing:**

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: pod-delete-test
  namespace: default
spec:
  appinfo:
    appns: default
    applabel: app=nginx
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-delete
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "30"           # Kill pods for 30 seconds
        - name: CHAOS_INTERVAL
          value: "10"           # Every 10 seconds
        - name: FORCE
          value: "false"
```

```bash
kubectl apply -f pod-delete-test.yaml

# Watch pods being killed and recreated
kubectl get pods -l app=nginx -w
# NAME                     READY   STATUS        RESTARTS   AGE
# nginx-7b8c9d6e8-abc12    1/1     Terminating   0          5m
# nginx-7b8c9d6e8-def34    1/1     Running       0          3s    ← self-healed

# Check experiment result
kubectl get chaosresult pod-delete-test-pod-delete -o jsonpath='{.status.experimentStatus.verdict}'
# Pass
```

**Example 2: Node drain experiment — verify PDB and rescheduling:**

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: node-drain-test
spec:
  appinfo:
    appns: default
    applabel: app=nginx
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
  - name: node-drain
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "60"
        - name: TARGET_NODE
          value: "worker-1"
```

**Example 3: Network chaos — simulate DNS failure:**

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: dns-chaos-test
spec:
  appinfo:
    appns: default
    applabel: app=my-api
    appkind: deployment
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-dns-error
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: "30"
        - name: TARGET_HOSTNAMES
          value: "database-service.default.svc.cluster.local"
```

**Common chaos experiments and what they validate:**

| Experiment | What It Tests | Expected Behavior |
|---|---|---|
| `pod-delete` | Self-healing via Deployment controller | New pod created within seconds |
| `node-drain` | PDB enforcement, pod rescheduling | Pods move to other nodes, PDB prevents all pods dying |
| `pod-cpu-hog` | HPA scaling under CPU pressure | HPA scales up replicas |
| `pod-memory-hog` | OOMKill handling, resource limits | Pod restarted, alerts fired |
| `pod-network-loss` | Circuit breaker, retry logic | Service degrades gracefully, no cascade failure |
| `pod-dns-error` | DNS failure handling | App retries or returns cached response |
| `node-cpu-hog` | Cluster Autoscaler | New node added to handle load |

**Real-life use case:** An e-commerce platform runs weekly chaos experiments in staging. `pod-delete` on the payment service confirmed that the Deployment controller recreates pods in <5 seconds. `pod-network-loss` between the cart and inventory services revealed that the cart service had no retry logic — it crashed instead of returning a cached response. This was fixed before it caused a production outage.

> Start chaos engineering in staging with `pod-delete` (safest experiment). Graduate to network chaos and node failures once your team is comfortable. Never run chaos experiments without monitoring and alerting in place — you need to observe the system's response.

### Backup Security

**Encryption:**

```bash
# Encrypt backups before uploading to S3
etcdctl snapshot save /tmp/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Encrypt with GPG before upload
gpg --symmetric --cipher-algo AES256 /tmp/etcd-backup.db
aws s3 cp /tmp/etcd-backup.db.gpg s3://my-backups/etcd/ --sse AES256

# S3 server-side encryption (all objects encrypted at rest)
aws s3api put-bucket-encryption --bucket my-backups \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms"}}]}'
```

**Immutable backups (ransomware protection):**

S3 Object Lock prevents backup deletion or modification for a retention period:

```bash
# Enable Object Lock on the bucket (must be set at bucket creation)
aws s3api create-bucket --bucket my-immutable-backups \
  --object-lock-enabled-for-bucket

# Upload with retention (GOVERNANCE mode — admins can override; COMPLIANCE — nobody can)
aws s3api put-object \
  --bucket my-immutable-backups \
  --key etcd-backup-20240115.db \
  --body /tmp/etcd-backup.db \
  --object-lock-mode GOVERNANCE \
  --object-lock-retain-until-date 2025-01-15T00:00:00Z
```

**Retention policies with S3 lifecycle rules:**

```json
{
  "Rules": [{
    "ID": "BackupRetention",
    "Prefix": "backups/",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 30,
      "StorageClass": "GLACIER"
    }],
    "Expiration": {
      "Days": 365
    }
  }]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-backups \
  --lifecycle-configuration file://lifecycle.json
```

This moves backups to Glacier after 30 days (cheaper storage) and deletes them after 365 days.

**Access control for backups:**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject"],
    "Resource": "arn:aws:s3:::my-backups/*",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalTag/team": "platform"
      }
    }
  }, {
    "Effect": "Deny",
    "Action": ["s3:DeleteObject"],
    "Resource": "arn:aws:s3:::my-backups/*",
    "Principal": "*"
  }]
}
```

> Deny `s3:DeleteObject` for all principals to prevent accidental or malicious backup deletion. Only the lifecycle rule should expire old backups.

---

