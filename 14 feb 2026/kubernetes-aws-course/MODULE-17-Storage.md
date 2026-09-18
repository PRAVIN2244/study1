# MODULE 17: Storage — Volumes, PV/PVC & StorageClass

---

## 17.1 Storage in Kubernetes

Containers are ephemeral — when a container restarts, all data is lost. Kubernetes provides volume abstractions to persist data.

**Key concepts:**
- **Volumes are Pod-level** — defined in the Pod spec, shared between containers in the same Pod
- **Volume lifecycle** depends on the type: `emptyDir` dies with the Pod, `hostPath` persists on the node, `PersistentVolume` persists independently
- **Two-step process** to use a volume: (1) define it in `volumes`, (2) mount it in `volumeMounts`

**Volume types at a glance:**

| Type | Scope | Persists after Pod deletion? | Use case |
|---|---|---|---|
| `emptyDir` | Pod | No | Sharing data between containers in a Pod |
| `hostPath` | Node | Yes (on that node) | Accessing node-level files (logs, Docker socket) |
| `PersistentVolume` | Cluster | Yes | Databases, stateful applications |
| `configMap` | Cluster | N/A (read-only) | Configuration files |
| `secret` | Cluster | N/A (read-only) | Credentials, certificates |

**Real-life analogy:** Think of containers as hotel guests. Without volumes, when they check out (restart), the room is cleaned (data lost). Volumes are like a personal locker at the hotel — data persists regardless of room changes.

```
┌──────────────────────────────────────────────────────┐
│  KUBERNETES STORAGE HIERARCHY                         │
│                                                      │
│  StorageClass (gp3, io2, efs)                        │
│       │                                              │
│       ▼                                              │
│  PersistentVolume (PV) — The actual disk             │
│       │                                              │
│       ▼                                              │
│  PersistentVolumeClaim (PVC) — Request for storage   │
│       │                                              │
│       ▼                                              │
│  Pod → volumeMounts → Container filesystem           │
└──────────────────────────────────────────────────────┘
```

---

## 17.2 Volume Types

### Volume Sharing — Two Meanings (Common Interview Confusion)

"How do pods share a volume?" has two different answers depending on context:

```
┌──────────────────────────────────────────────────────────────┐
│  Meaning 1: Containers in the SAME Pod share a volume        │
│  ─────────────────────────────────────────────────────────── │
│  ✅ Easy — use emptyDir or any volume type                   │
│  All containers in a pod can mount the same volume           │
│  Common pattern: sidecar writes logs, main container serves  │
│                                                              │
│  Pod                                                         │
│  ┌──────────┐  ┌──────────┐                                  │
│  │ Container │  │ Container │                                 │
│  │ A (app)   │  │ B (sidecar)│                                │
│  └─────┬─────┘  └─────┬─────┘                                │
│        │               │                                     │
│        └───────┬───────┘                                     │
│                ▼                                             │
│         emptyDir: {}     ← Shared volume, same pod           │
│                                                              │
│  Meaning 2: DIFFERENT Pods share the same volume             │
│  ─────────────────────────────────────────────────────────── │
│  ⚠️ Depends on access mode of the storage                    │
│                                                              │
│  ReadWriteOnce (RWO) — Only ONE node can mount               │
│  └── Multiple pods on the SAME node can share it             │
│  └── Pods on DIFFERENT nodes CANNOT share it                 │
│  └── Used by: EBS, Azure Disk, GCE PD                        │
│                                                              │
│  ReadWriteMany (RWX) — Multiple nodes can mount              │
│  └── Any pod on any node can read/write                      │
│  └── Used by: EFS, Azure Files, NFS, CephFS                  │
│                                                              │
│  ReadOnlyMany (ROX) — Multiple nodes can mount read-only     │
│  └── Used by: ConfigMaps, shared config data                 │
└──────────────────────────────────────────────────────────────┘
```

| Scenario | Volume Type | Access Mode | Works? |
|---|---|---|---|
| 2 containers in same pod | `emptyDir` | N/A | ✅ Always works |
| 2 pods on same node | PVC with EBS | RWO | ✅ Works (same node) |
| 2 pods on different nodes | PVC with EBS | RWO | ❌ Fails (EBS is single-node) |
| 2 pods on different nodes | PVC with EFS | RWX | ✅ Works (EFS is multi-node) |
| 3 replicas of a Deployment | PVC with EBS | RWO | ⚠️ Only works if all on same node |
| 3 replicas of a Deployment | PVC with EFS | RWX | ✅ All replicas share the volume |

**Real-life use cases for volume sharing:**
- Sidecar writes logs → main container serves them (or log collector ships them)
- Init container downloads artifacts/config → main container uses them
- Adapter container transforms data format → main container reads transformed data

### emptyDir — Temporary Shared Storage

Exists as long as the Pod exists. Shared between containers in the same Pod.

```yaml
# emptydir-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-volume-pod
spec:
  containers:
  - name: writer
    image: busybox
    command: ['sh', '-c', 'while true; do echo "$(date) - Log entry" >> /data/log.txt; sleep 5; done']
    volumeMounts:
    - name: shared-data
      mountPath: /data

  - name: reader
    image: busybox
    command: ['sh', '-c', 'tail -f /data/log.txt']
    volumeMounts:
    - name: shared-data
      mountPath: /data

  volumes:
  - name: shared-data
    emptyDir: {}           # Created when Pod starts, deleted when Pod dies
```

```bash
kubectl apply -f emptydir-pod.yaml

# Check the reader container sees the writer's data
kubectl logs shared-volume-pod -c reader

# Output:
# Mon Jan 15 10:00:00 UTC 2024 - Log entry
# Mon Jan 15 10:00:05 UTC 2024 - Log entry
# Mon Jan 15 10:00:10 UTC 2024 - Log entry
```

**Verifying shared volumes between containers:**

```bash
# Create files from each container and verify cross-visibility
kubectl exec shared-volume-pod -c writer -- touch /data/from-writer
kubectl exec shared-volume-pod -c reader -- touch /data/from-reader

# Both containers see all files
kubectl exec shared-volume-pod -c writer -- ls /data
# Output: from-reader  from-writer  log.txt

kubectl exec shared-volume-pod -c reader -- ls /data
# Output: from-reader  from-writer  log.txt
```

### hostPath — Node's Filesystem

Mounts a file or directory from the host node's filesystem. Use with caution.

```yaml
# hostpath-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ['sh', '-c', 'cat /host-logs/syslog']
    volumeMounts:
    - name: host-logs
      mountPath: /host-logs
      readOnly: true

  volumes:
  - name: host-logs
    hostPath:
      path: /var/log
      type: Directory
```

⚠️ **hostPath is a security risk in production. Pods can access the host filesystem. Use PersistentVolumes instead.**

### Example: Persisting Data with hostPath

A pod generates a random number and writes it to a file. Without a volume, the data is lost when the pod terminates:

```yaml
# random-number.yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-number-generator
spec:
  containers:
  - name: alpine
    image: alpine
    command: ["/bin/sh", "-c"]
    args: ["shuf -i 0-100 -n 1 >> /opt/number.out;"]
    volumeMounts:
    - mountPath: /opt
      name: data-volume
  volumes:
  - name: data-volume
    hostPath:
      path: /data
      type: Directory
```

The file `/opt/number.out` inside the container maps to `/data/number.out` on the host node. After the pod completes, the data persists on the node at `/data/`.

### Docker Volumes vs Kubernetes Volumes

| | Docker | Kubernetes |
|---|---|---|
| **Ephemeral by default** | Container writable layer lost on removal | Pod filesystem lost on termination |
| **Named volumes** | `docker run -v mydata:/var/lib/mysql` | `emptyDir`, `hostPath` in pod spec |
| **Persistent storage** | Volume drivers (Rex-Ray, local) | PersistentVolume + PersistentVolumeClaim |
| **Cloud storage** | `--volume-driver rexray/ebs` | CSI drivers (ebs.csi.aws.com) |
| **Scope** | Single host | Cluster-wide (PV/PVC) |

### Volume Storage Options

`hostPath` works for single-node clusters but fails in multi-node environments (each node has a different `/data` directory). For production, use external storage:

| Storage Option | Use Case | Volume Type |
|---|---|---|
| hostPath | Single-node testing | `hostPath` |
| AWS EBS | Block storage (single-AZ) | PVC with `ebs.csi.aws.com` StorageClass |
| AWS EFS | Shared file storage (multi-AZ) | PVC with `efs.csi.aws.com` StorageClass |
| Azure Disk | Block storage on Azure | PVC with `disk.csi.azure.com` |
| GCE Persistent Disk | Block storage on GCP | PVC with `pd.csi.storage.gke.io` |
| NFS | Shared storage (on-prem) | `nfs` volume or CSI driver |

**Legacy inline volume syntax (pre-CSI, deprecated):**

```yaml
# Old way — avoid in new clusters
volumes:
- name: data
  awsElasticBlockStore:
    volumeID: vol-0123456789abcdef0
    fsType: ext4
```

Use PVC + StorageClass instead — it's portable, supports dynamic provisioning, and works with CSI.

---

## 17.3 Persistent Volumes (PV) & Persistent Volume Claims (PVC)

**Concept:** Instead of configuring storage in every pod definition, administrators create a centralized pool of storage as PersistentVolumes. Users then request storage by creating PersistentVolumeClaims. This separates storage provisioning (admin) from storage consumption (developer).

```
Admin creates PVs (storage pool)     Users create PVCs (storage requests)
┌──────────┐  ┌──────────┐          ┌──────────┐
│ PV 10Gi  │  │ PV 50Gi  │          │ PVC 5Gi  │──── binds to ──→ PV 10Gi
│ RWO      │  │ RWX      │          │ RWO      │
│ Available│  │ Available│          └──────────┘
└──────────┘  └──────────┘
```

**PV-to-PVC binding criteria:** Kubernetes matches a PVC to a PV based on:
1. **Sufficient capacity** — PV must have >= requested storage (a 50Gi PV can satisfy a 5Gi PVC, but the extra 45Gi is wasted — no other PVC can use it)
2. **Access modes** — must match (RWO PVC won't bind to RWX-only PV)
3. **Storage class** — must match (or both must have none)
4. **Labels/selectors** — if the PVC has a `selector`, only PVs with matching labels are considered

If no PV matches, the PVC stays in **Pending** state until a suitable PV is created.

**PV status transitions:**

| Status | Meaning |
|---|---|
| `Available` | PV is ready, not yet bound to any PVC |
| `Bound` | PV is bound to a PVC |
| `Released` | PVC was deleted, but PV still has data (Retain policy) |
| `Failed` | Automatic reclamation failed |

**Creating a simple PV with hostPath (testing only):**

```yaml
# pv-vol1.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-vol1
spec:
  accessModes:
    - ReadWriteOnce
  capacity:
    storage: 1Gi
  hostPath:
    path: /tmp/data
```

```bash
kubectl create -f pv-vol1.yaml
# persistentvolume/pv-vol1 created

kubectl get pv
# NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   AGE
# pv-vol1   1Gi        RWO            Retain           Available           5s
```

**Reclaim policies — what happens to the PV when its PVC is deleted:**

| Policy | Behavior | Use Case |
|---|---|---|
| `Retain` | PV keeps data, moves to `Released` status. Admin must manually clean up. | Production databases — prevent accidental data loss |
| `Delete` | PV and underlying storage are deleted automatically | Dev/test environments, ephemeral data |
| `Recycle` | Data is scrubbed (`rm -rf /volume/*`), PV becomes `Available` again | ⚠️ Deprecated — use dynamic provisioning instead |

```bash
# Delete a PVC
kubectl delete pvc myclaim

# With Retain policy, PV moves to Released:
kubectl get pv
# NAME      CAPACITY   STATUS     CLAIM             AGE
# pv-vol1   1Gi        Released   default/myclaim   10m
```

### AWS EBS Storage Classes

```bash
# Check available storage classes
kubectl get storageclass

# Output:
# NAME            PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      AGE
# gp2 (default)   kubernetes.io/aws-ebs   Delete          WaitForFirstConsumer   5d
```

```yaml
# Create a gp3 StorageClass (faster, cheaper than gp2)
# storageclass-gp3.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Delete           # Delete EBS volume when PVC is deleted
volumeBindingMode: WaitForFirstConsumer  # Create volume in same AZ as pod
allowVolumeExpansion: true      # Allow resizing
```

```bash
kubectl apply -f storageclass-gp3.yaml

kubectl get storageclass

# Output:
# NAME            PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      AGE
# gp2             kubernetes.io/aws-ebs   Delete          WaitForFirstConsumer   5d
# gp3 (default)   ebs.csi.aws.com         Delete          WaitForFirstConsumer   30s
```

### Creating a PersistentVolumeClaim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-pvc
spec:
  accessModes:
    - ReadWriteOnce          # Can be mounted by one node
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi
```

```bash
kubectl apply -f pvc.yaml

kubectl get pvc

# Output:
# NAME           STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data-pvc   Pending                                      gp3            30s
# (Pending because WaitForFirstConsumer — waits for a pod to use it)
```

### Using PVC in a Pod

```yaml
# pod-with-pvc.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-storage
spec:
  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: app-data
      mountPath: /usr/share/nginx/html
    ports:
    - containerPort: 80

  volumes:
  - name: app-data
    persistentVolumeClaim:
      claimName: app-data-pvc
```

```bash
kubectl apply -f pod-with-pvc.yaml

# Now the PVC is bound
kubectl get pvc

# Output:
# NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data-pvc   Bound    pvc-abc12345-def6-7890-ghij-klmnopqrstuv   20Gi       RWO            gp3            2m

# Check the PV that was auto-created
kubectl get pv

# Output:
# NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                  STORAGECLASS
# pvc-abc12345-def6-7890-ghij-klmnopqrstuv   20Gi       RWO            Delete           Bound    default/app-data-pvc   gp3

# Write data to the volume
kubectl exec app-with-storage -- sh -c 'echo "Persistent data!" > /usr/share/nginx/html/index.html'

# Delete and recreate the pod — data persists!
kubectl delete pod app-with-storage
kubectl apply -f pod-with-pvc.yaml
kubectl exec app-with-storage -- cat /usr/share/nginx/html/index.html

# Output:
# Persistent data!
```

### Static PersistentVolume (Manual Provisioning)

When not using dynamic provisioning via StorageClasses, you can manually create a PV pointing to an existing volume:

```yaml
# static-pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: myebsvol
spec:
  capacity:
    storage: 2Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  awsElasticBlockStore:
    volumeID: vol-0b94763bce4acb22c    # Existing EBS volume ID
    fsType: ext4
```

```yaml
# static-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myebsvolclaim
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

```yaml
# deploy-with-pv.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pvdeploy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mypv
  template:
    metadata:
      labels:
        app: mypv
    spec:
      containers:
      - name: shell
        image: centos
        command: ["/bin/bash", "-c", "sleep 10000"]
        volumeMounts:
        - name: mypd
          mountPath: "/tmp/persistent"
      volumes:
      - name: mypd
        persistentVolumeClaim:
          claimName: myebsvolclaim
```

```bash
kubectl apply -f static-pv.yaml
kubectl apply -f static-pvc.yaml
kubectl apply -f deploy-with-pv.yaml

kubectl get pv
kubectl get pvc
kubectl describe pv myebsvol
kubectl describe pvc myebsvolclaim
```

### Access Modes

| Mode | Abbreviation | Description | AWS Support |
|---|---|---|---|
| ReadWriteOnce | RWO | Single node read/write | EBS (gp2, gp3, io2) |
| ReadOnlyMany | ROX | Multiple nodes read-only | EFS |
| ReadWriteMany | RWX | Multiple nodes read/write | EFS |

### Volume Expansion

```bash
# Expand a PVC (StorageClass must have allowVolumeExpansion: true)
kubectl patch pvc app-data-pvc -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

# Output:
# persistentvolumeclaim/app-data-pvc patched

kubectl get pvc app-data-pvc

# Output:
# NAME           STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data-pvc   Bound    pvc-...  50Gi       RWO            gp3            10m
```

### Lab: Persistent Volumes and Persistent Volume Claims

This lab walks through persisting application logs using hostPath, then migrating to PV/PVC, including troubleshooting access mode mismatches.

**Step 1: View logs in the pod (no volume)**

```bash
kubectl exec webapp -- cat /log/app.log
# [2024-01-15 10:00:00] INFO: Application started
# [2024-01-15 10:00:05] INFO: Processing request...
```

Logs exist only inside the container. Deleting the pod loses them.

**Step 2: Add a hostPath volume to persist logs**

```yaml
# webapp-with-volume.yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
  - name: event-simulator
    image: kodekloud/event-simulator
    env:
    - name: LOG_HANDLERS
      value: file
    volumeMounts:
    - name: log-volume
      mountPath: /log
  volumes:
  - name: log-volume
    hostPath:
      path: /var/log/webapp
```

```bash
# Pods are immutable — delete and recreate
kubectl replace --force -f webapp-with-volume.yaml
# pod "webapp" deleted
# pod/webapp replaced

# Verify logs persist on the host
cat /var/log/webapp/app.log
```

**Step 3: Create a PersistentVolume**

```yaml
# pv-log.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-log
spec:
  capacity:
    storage: 100Mi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /pv/log
```

```bash
kubectl create -f pv-log.yaml

kubectl get pv
# NAME     CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      AGE
# pv-log   100Mi      RWX            Retain           Available   3s
```

**Step 4: Create a PVC — access mode mismatch**

```yaml
# pvc-log.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: claim-log-1
spec:
  accessModes:
    - ReadWriteOnce       # ← Mismatch! PV is ReadWriteMany
  resources:
    requests:
      storage: 50Mi
```

```bash
kubectl create -f pvc-log.yaml

kubectl get pvc
# NAME          STATUS    VOLUME   CAPACITY   ACCESS MODES   AGE
# claim-log-1   Pending                                      5s

kubectl get pv
# NAME     CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      AGE
# pv-log   100Mi      RWX            Retain           Available   2m
```

The PVC stays Pending because `ReadWriteOnce` doesn't match the PV's `ReadWriteMany`.

**Step 5: Fix the access mode**

Update `pvc-log.yaml` to use `ReadWriteMany`:

```yaml
  accessModes:
    - ReadWriteMany       # ← Now matches the PV
```

```bash
kubectl replace --force -f pvc-log.yaml

kubectl get pvc
# NAME          STATUS   VOLUME   CAPACITY   ACCESS MODES   AGE
# claim-log-1   Bound    pv-log   100Mi      RWX            5s
```

The PVC binds to the PV. Note the PVC requested 50Mi but got 100Mi — the PV's full capacity is allocated.

**Step 6: Update the pod to use the PVC**

```yaml
  volumes:
  - name: log-volume
    persistentVolumeClaim:
      claimName: claim-log-1      # Replace hostPath with PVC
```

```bash
kubectl replace --force -f webapp-with-pvc.yaml

# Verify logs are written to the PV's backing path
cat /pv/log/app.log
```

**Step 7: Verify reclaim policy behavior**

```bash
kubectl delete pvc claim-log-1

kubectl get pv pv-log
# NAME     CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS     CLAIM                 AGE
# pv-log   100Mi      RWX            Retain           Released   default/claim-log-1   10m
```

With `Retain` policy, the PV moves to `Released` — data is preserved but the PV cannot be rebound to a new PVC without admin intervention.

**PVC stuck in Terminating:** If you delete a PVC while a Pod is still using it, the PVC enters `Terminating` state but is not actually removed — Kubernetes applies a `kubernetes.io/pvc-protection` finalizer that blocks deletion until no Pod references the PVC. Delete the Pod first, then the PVC will be removed:

```bash
kubectl delete pvc claim-log-1
# PVC stays in Terminating...

kubectl get pvc
# NAME          STATUS        VOLUME   AGE
# claim-log-1   Terminating   pv-log   10m

# Delete the pod that mounts it
kubectl delete pod webapp

# PVC is now fully deleted, PV moves to Released
kubectl get pv pv-log
# NAME     STATUS     RECLAIM POLICY   AGE
# pv-log   Released   Retain           15m
```

---

## 17.4 Amazon EFS (Elastic File System) — Shared Storage

EFS provides ReadWriteMany (RWX) access — multiple pods across multiple nodes can read/write simultaneously.

```bash
# Install EFS CSI Driver
helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver/
helm repo update

helm install aws-efs-csi-driver aws-efs-csi-driver/aws-efs-csi-driver \
  --namespace kube-system \
  --set controller.serviceAccount.create=false \
  --set controller.serviceAccount.name=efs-csi-controller-sa
```

```yaml
# efs-storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-0123456789abcdef0    # Your EFS filesystem ID
  directoryPerms: "700"
```

```yaml
# efs-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
spec:
  accessModes:
    - ReadWriteMany          # Multiple pods can write!
  storageClassName: efs-sc
  resources:
    requests:
      storage: 5Gi
```

```yaml
# Multiple pods sharing the same EFS volume
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shared-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shared-app
  template:
    metadata:
      labels:
        app: shared-app
    spec:
      containers:
      - name: app
        image: nginx:1.25
        volumeMounts:
        - name: shared-data
          mountPath: /shared
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-data    # All 3 replicas share this volume
```

---

## 17.5 Container Storage Interface (CSI) — Deep Dive

CSI is a standard interface that allows Kubernetes to work with any storage system without building storage drivers into the Kubernetes codebase.

### The Three Kubernetes Interfaces: CRI, CNI, CSI

Kubernetes uses three standardized interfaces to decouple its core from runtime, networking, and storage implementations:

| Interface | Full Name | Purpose | Examples |
|---|---|---|---|
| **CRI** | Container Runtime Interface | Standardizes container runtimes | containerd, CRI-O |
| **CNI** | Container Networking Interface | Standardizes networking plugins | Calico, Cilium, AWS VPC-CNI |
| **CSI** | Container Storage Interface | Standardizes storage drivers | AWS EBS CSI, EFS CSI, Portworx |

Each follows the same pattern: Kubernetes defines a spec, vendors implement plugins that conform to it, and Kubernetes communicates with them via gRPC. CSI is not Kubernetes-specific — Cloud Foundry and Mesos also implement it.

**CSI-supported storage vendors include:** AWS EBS, AWS EFS, Azure Disk, Azure Files, Google Persistent Disk, Portworx, Dell EMC (PowerMax, PowerStore, Unity, Isilon), NetApp (Trident), Nutanix, HPE, Hitachi, Pure Storage, Ceph (Rook), NFS, and many more.

### What Problem Does CSI Solve?

Before CSI, every storage driver (AWS EBS, GCE PD, NFS, Ceph) was compiled directly into the Kubernetes binary. Adding a new storage system required modifying Kubernetes source code and waiting for a release. CSI decouples storage from Kubernetes — vendors ship their own drivers as pods.

```
┌──────────────────────────────────────────────────────────────┐
│  Before CSI (in-tree)                                        │
│                                                              │
│  Kubernetes Binary                                           │
│  ┌──────────────────────────────────────────────────┐        │
│  │  kubelet  +  AWS EBS code  +  GCE PD code  +    │        │
│  │  NFS code  +  Ceph code  +  Azure Disk code     │        │
│  └──────────────────────────────────────────────────┘        │
│  Problem: Kubernetes binary grows, vendor lock-in,           │
│           slow release cycles for storage fixes              │
│                                                              │
│  After CSI (out-of-tree)                                     │
│                                                              │
│  Kubernetes Binary          CSI Driver Pods                  │
│  ┌──────────────┐          ┌──────────────────┐              │
│  │  kubelet     │◄────────►│  ebs.csi.aws.com │              │
│  │  (CSI spec)  │  gRPC    │  (DaemonSet)     │              │
│  └──────────────┘          └──────────────────┘              │
│                            ┌──────────────────┐              │
│                            │  efs.csi.aws.com │              │
│                            │  (DaemonSet)     │              │
│                            └──────────────────┘              │
│  Benefit: Independent releases, any vendor can build a       │
│           driver, Kubernetes stays lean                       │
└──────────────────────────────────────────────────────────────┘
```

### CSI Architecture — How It Works Internally

A CSI driver runs as pods in your cluster with three components:

```
┌─────────────────────────────────────────────────────────────┐
│  CSI Driver Components                                       │
│                                                              │
│  1. Controller Plugin (Deployment, 1-2 replicas)             │
│     ├── csi-provisioner   → Creates/deletes volumes          │
│     ├── csi-attacher      → Attaches volumes to nodes        │
│     ├── csi-resizer       → Expands volumes                  │
│     ├── csi-snapshotter   → Creates volume snapshots         │
│     └── driver container  → Vendor-specific logic            │
│                                                              │
│  2. Node Plugin (DaemonSet, runs on every node)              │
│     ├── node-driver-registrar → Registers driver with kubelet│
│     └── driver container      → Mounts/unmounts volumes      │
│                                                              │
│  3. CSIDriver Object (cluster-scoped)                        │
│     └── Tells Kubernetes about driver capabilities           │
└─────────────────────────────────────────────────────────────┘
```

### What Happens When a PVC Is Created (CSI Flow)

```
Step 1: User creates PVC
        ↓
Step 2: csi-provisioner sidecar watches for unbound PVCs
        ↓
Step 3: csi-provisioner calls CSI driver's CreateVolume() via gRPC
        ↓
Step 4: CSI driver calls AWS API → aws ec2 create-volume
        ↓
Step 5: CSI driver returns volume ID to csi-provisioner
        ↓
Step 6: csi-provisioner creates a PV object bound to the PVC
        ↓
Step 7: Pod is scheduled to a node
        ↓
Step 8: csi-attacher calls CSI driver's ControllerPublishVolume()
        ↓
Step 9: CSI driver calls AWS API → aws ec2 attach-volume
        ↓
Step 10: kubelet calls CSI driver's NodeStageVolume() → formats disk
         ↓
Step 11: kubelet calls CSI driver's NodePublishVolume() → mounts to pod
```

### Installing the AWS EBS CSI Driver

```bash
# The EBS CSI driver replaces the in-tree AWS EBS provisioner
# Required for EKS 1.23+ (in-tree driver deprecated)

# Step 1: Create IAM role for the CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster my-k8s-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

# Step 2: Install the EBS CSI driver as an EKS add-on
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster my-k8s-cluster \
  --service-account-role-arn arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole \
  --force

# Step 3: Verify the driver is running
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver

# Output:
# NAME                                  READY   STATUS    RESTARTS   AGE
# ebs-csi-controller-5b8f4d7c9-abc12   6/6     Running   0          2m
# ebs-csi-controller-5b8f4d7c9-def34   6/6     Running   0          2m
# ebs-csi-node-g7h8i                   3/3     Running   0          2m    ← DaemonSet (one per node)
# ebs-csi-node-j9k0l                   3/3     Running   0          2m
# ebs-csi-node-m1n2o                   3/3     Running   0          2m

# Step 4: Check the CSIDriver object
kubectl get csidriver

# Output:
# NAME              ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY   TOKENREQUESTS   REQUIRESREPUBLISH   MODES        AGE
# ebs.csi.aws.com   true             false            false             <unset>         false               Persistent   2m
# efs.csi.aws.com   false            false            false             <unset>         false               Persistent   5d
```

### Alternative: Manual IAM Policy for EBS CSI Driver

If not using IRSA, you can attach the IAM policy directly to the worker node IAM role:

**Step 1: Create IAM Policy**

Go to AWS Console → IAM → Policies → Create Policy → JSON tab:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AttachVolume",
        "ec2:CreateSnapshot",
        "ec2:CreateTags",
        "ec2:CreateVolume",
        "ec2:DeleteSnapshot",
        "ec2:DeleteTags",
        "ec2:DeleteVolume",
        "ec2:DescribeInstances",
        "ec2:DescribeSnapshots",
        "ec2:DescribeTags",
        "ec2:DescribeVolumes",
        "ec2:DetachVolume"
      ],
      "Resource": "*"
    }
  ]
}
```

Name the policy `Amazon_EBS_CSI_Driver`.

**Step 2: Find the worker node IAM role**

```bash
kubectl -n kube-system describe configmap aws-auth
# Look for rolearn in the output:
# rolearn: arn:aws:iam::180789647333:role/eksctl-eksdemo1-nodegroup-eksdemo-NodeInstanceRole-IJN07ZKXAWNN
```

Go to AWS Console → IAM → Roles → search for `eksctl-eksdemo1-nodegroup` → Permissions → Attach Policies → search for `Amazon_EBS_CSI_Driver` → Attach.

**Step 3: Deploy EBS CSI Driver via kubectl**

```bash
# Deploy the EBS CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"

# Verify
kubectl get pods -n kube-system | grep ebs
# ebs-csi-controller-0   2/2     Running   0   2m
# ebs-csi-node-abcdef    2/2     Running   0   2m
```

⚠️ When deleting the cluster, remove the custom IAM policy from the worker node role first. Otherwise the CloudFormation stack deletion may hang.

### CSI Driver Comparison

| Driver | Provisioner | Access Modes | Use Case |
|---|---|---|---|
| **EBS CSI** | `ebs.csi.aws.com` | ReadWriteOnce | Block storage, databases, single-pod volumes |
| **EFS CSI** | `efs.csi.aws.com` | ReadWriteMany | Shared file storage, multi-pod access |
| **FSx CSI** | `fsx.csi.aws.com` | ReadWriteMany | High-performance computing, ML workloads |
| **Secrets Store CSI** | `secrets-store.csi.k8s.io` | ReadOnlyMany | Mount AWS Secrets Manager/SSM as volumes |

### Secrets Store CSI Driver — Mount Secrets as Files

Instead of creating Kubernetes Secrets, mount secrets directly from AWS Secrets Manager:

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
# secret-provider-class.yaml
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
            objectAlias: db-username
          - path: password
            objectAlias: db-password
```

```yaml
# pod-with-secrets-store.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-secrets
spec:
  serviceAccountName: app-sa    # Must have IAM role with SecretsManager access
  containers:
  - name: app
    image: myapp:1.0
    volumeMounts:
    - name: secrets
      mountPath: /mnt/secrets
      readOnly: true
  volumes:
  - name: secrets
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets
```

```bash
# Verify secrets are mounted
kubectl exec app-with-secrets -- ls /mnt/secrets

# Output:
# db-username
# db-password

kubectl exec app-with-secrets -- cat /mnt/secrets/db-username

# Output:
# admin
```

### Azure Disk CSI Example (AKS)

On AKS, the Azure Disk CSI driver is pre-installed. The flow is identical to AWS — only the provisioner and parameters differ:

```yaml
# azure-storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-csi
provisioner: disk.csi.azure.com       # Azure Disk CSI driver
parameters:
  skuName: Premium_LRS                # Premium SSD (alternatives: Standard_LRS, StandardSSD_LRS)
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

```yaml
# azure-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: managed-csi
  resources:
    requests:
      storage: 20Gi
```

```yaml
# azure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo
spec:
  containers:
  - name: app
    image: nginx:1.27
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

```bash
kubectl apply -f azure-storageclass.yaml
kubectl apply -f azure-pvc.yaml
kubectl apply -f azure-pod.yaml

kubectl get pvc

# Output:
# NAME       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data   Bound    pvc-2a8b2c40-6c3f-4a8c-9c3a-6c8a0f0f9a1b   20Gi       RWO            managed-csi    1m

kubectl get pv

# Output:
# NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM              STORAGECLASS
# pvc-2a8b2c40-6c3f-4a8c-9c3a-6c8a0f0f9a1b   20Gi       RWO            Delete           Bound    default/app-data   managed-csi
```

### CSI Volume Snapshots

CSI supports creating point-in-time snapshots of volumes for backup and restore:

```yaml
# snapshot-class.yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com              # Or disk.csi.azure.com for AKS
deletionPolicy: Delete
```

```yaml
# snapshot.yaml — Create a snapshot of an existing PVC
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: app-data-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: app-data    # PVC to snapshot
```

```bash
kubectl apply -f snapshot-class.yaml
kubectl apply -f snapshot.yaml

kubectl get volumesnapshot

# Output:
# NAME                READYTOUSE   SOURCEPVC   RESTORESIZE   SNAPSHOTCLASS    AGE
# app-data-snapshot   true         app-data    20Gi          csi-snapclass    30s
```

```yaml
# restore-from-snapshot.yaml — Create a new PVC from the snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-restored
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi
  dataSource:
    name: app-data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

```bash
kubectl apply -f restore-from-snapshot.yaml

kubectl get pvc app-data-restored

# Output:
# NAME                STATUS   VOLUME         CAPACITY   ACCESS MODES   STORAGECLASS
# app-data-restored   Bound    pvc-xyz789     20Gi       RWO            gp3
```

### CSI Real-Life Use Cases

| Use Case | CSI Driver | Why CSI |
|---|---|---|
| **Databases on K8s** (Postgres, MySQL, MongoDB) | EBS CSI / Azure Disk CSI | Dynamic provisioning, per-pod volumes via StatefulSet |
| **Shared state** across pods | EFS CSI / Azure Files CSI | ReadWriteMany access for multi-pod workloads |
| **Backup/restore** | Any CSI with snapshot support | VolumeSnapshot for point-in-time backups |
| **Secrets from cloud vaults** | Secrets Store CSI | Mount AWS Secrets Manager / Azure Key Vault as files |
| **ML training data** | FSx CSI / Azure NetApp Files | High-throughput shared storage for GPU workloads |
| **Compliance** (encrypted at rest) | EBS CSI with `encrypted: true` | Automatic encryption via StorageClass parameters |

### Common CSI Errors

| Error | Cause | Fix |
|---|---|---|
| `waiting for a volume to be created` | CSI driver not installed or IAM role missing | Install driver, check IAM permissions |
| `AttachVolume.Attach failed` | EBS volume in different AZ than node | Use StorageClass with `volumeBindingMode: WaitForFirstConsumer` |
| `FailedMount: rpc error` | Node plugin not running on the node | Check `kubectl get pods -n kube-system -l app=ebs-csi-node` |
| `could not create volume` | Exceeded AWS EBS volume limit per instance | Check instance type limits, clean up unused volumes |
| `volume already attached to another node` | EBS is ReadWriteOnce, can't attach to 2 nodes | Use EFS for multi-node access, or ensure pod is on same node |

**Interview question: What is CSI and why was it introduced?**
CSI (Container Storage Interface) is a standard API that lets storage vendors write drivers as independent pods instead of compiling them into Kubernetes. It was introduced to decouple storage from the Kubernetes release cycle, allow any vendor to provide storage without modifying Kubernetes source code, and keep the Kubernetes binary lean. CSI also enables features like volume snapshots, volume expansion, and topology-aware scheduling that weren't possible with in-tree drivers.

---

## 17.6 StorageClass & Dynamic Provisioning — Deep Dive

A StorageClass defines a "class" of storage — the provisioner, parameters, and reclaim policy. When a PVC references a StorageClass, Kubernetes automatically provisions a volume (dynamic provisioning) instead of requiring an admin to pre-create PVs.

### Static vs Dynamic Provisioning

```
┌─────────────────────────────────────────────────────────────┐
│  Static Provisioning (Manual)                                │
│                                                              │
│  Admin creates PV ──► User creates PVC ──► Kubernetes binds  │
│  (pre-existing volume)                                       │
│                                                              │
│  Problem: Admin must pre-create volumes for every request    │
│                                                              │
│  Dynamic Provisioning (Automatic)                            │
│                                                              │
│  Admin creates StorageClass                                  │
│       ↓                                                      │
│  User creates PVC with storageClassName                      │
│       ↓                                                      │
│  Kubernetes calls CSI driver → creates volume automatically  │
│       ↓                                                      │
│  PV is auto-created and bound to PVC                         │
│                                                              │
│  Benefit: Self-service, no admin bottleneck                  │
└─────────────────────────────────────────────────────────────┘
```

### StorageClass YAML — Line by Line

```yaml
# storageclass-gp3.yaml
apiVersion: storage.k8s.io/v1       # StorageClass API group
kind: StorageClass
metadata:
  name: gp3                         # Name referenced by PVCs
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"   # Makes this the default
provisioner: ebs.csi.aws.com        # Which CSI driver creates volumes
parameters:
  type: gp3                         # AWS EBS volume type (gp3, gp2, io2, st1, sc1)
  fsType: ext4                      # Filesystem type (ext4, xfs)
  encrypted: "true"                 # Encrypt volume at rest
  iops: "3000"                      # Provisioned IOPS (gp3 baseline: 3000)
  throughput: "125"                 # Throughput in MiB/s (gp3 baseline: 125)
reclaimPolicy: Delete               # Delete EBS volume when PVC is deleted
                                    # Retain = keep volume (for production databases)
volumeBindingMode: WaitForFirstConsumer  # Don't create volume until pod is scheduled
                                         # Prevents AZ mismatch (volume in us-east-1a, pod in us-east-1b)
allowVolumeExpansion: true           # Allow PVC resize without recreating
```

**Each field explained:**

| Field | What It Does | Why It Matters |
|---|---|---|
| `provisioner` | Identifies the CSI driver that creates volumes | Must match an installed CSI driver |
| `parameters.type` | AWS EBS volume type | gp3 is cheaper and faster than gp2 |
| `parameters.encrypted` | Enables encryption at rest | Required for compliance (HIPAA, SOC2) |
| `reclaimPolicy: Delete` | Deletes the underlying volume when PVC is deleted | Use `Retain` for databases to prevent data loss |
| `reclaimPolicy: Retain` | Keeps the volume even after PVC deletion | Admin must manually clean up |
| `volumeBindingMode: WaitForFirstConsumer` | Delays volume creation until a pod needs it | Ensures volume is in the same AZ as the pod |
| `volumeBindingMode: Immediate` | Creates volume immediately when PVC is created | Can cause AZ mismatch errors |
| `allowVolumeExpansion` | Allows increasing PVC size | Cannot shrink — only grow |

### Dynamic Provisioning in Action

```bash
# Step 1: Create the StorageClass
kubectl apply -f storageclass-gp3.yaml

kubectl get storageclass

# Output:
# NAME            PROVISIONER       RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
# gp2 (default)   kubernetes.io/aws-ebs   Delete    WaitForFirstConsumer   false                  30d
# gp3             ebs.csi.aws.com         Delete    WaitForFirstConsumer   true                   5s

# Step 2: Create a PVC referencing the StorageClass
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3          # References our StorageClass
  resources:
    requests:
      storage: 20Gi
EOF

kubectl get pvc app-data

# Output (WaitForFirstConsumer — stays Pending until a pod uses it):
# NAME       STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data   Pending                                      gp3            5s

# Step 3: Create a pod that uses the PVC
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data
EOF

# Step 4: Now the PVC binds and a PV is auto-created
kubectl get pvc app-data

# Output:
# NAME       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data   Bound    pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   20Gi       RWO            gp3            30s

kubectl get pv

# Output:
# NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM              STORAGECLASS
# pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   20Gi       RWO            Delete           Bound    default/app-data   gp3

# The PV was auto-created by the CSI driver — no admin intervention needed
```

### Expanding a PVC (Volume Resize)

```bash
# Only works if StorageClass has allowVolumeExpansion: true
kubectl patch pvc app-data -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

# Output:
# persistentvolumeclaim/app-data patched

kubectl get pvc app-data

# Output:
# NAME       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# app-data   Bound    pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   50Gi       RWO            gp3            5m

# Note: The pod may need to be restarted for filesystem resize to take effect
# For EBS, online resize works without pod restart on EKS 1.24+
```

### StorageClass Comparison for AWS

| StorageClass | Volume Type | IOPS | Throughput | Use Case |
|---|---|---|---|---|
| `gp3` | General Purpose SSD | 3,000 baseline (up to 16,000) | 125 MiB/s (up to 1,000) | Default for most workloads |
| `gp2` | General Purpose SSD | 3 IOPS/GiB (burst to 3,000) | 128-250 MiB/s | Legacy, use gp3 instead |
| `io2` | Provisioned IOPS SSD | Up to 64,000 | Up to 1,000 MiB/s | Databases needing guaranteed IOPS |
| `st1` | Throughput Optimized HDD | N/A | Up to 500 MiB/s | Big data, log processing |
| `sc1` | Cold HDD | N/A | Up to 250 MiB/s | Infrequent access, archival |
| `efs-sc` | NFS (EFS) | Elastic | Elastic | Shared storage (ReadWriteMany) |

### Default StorageClass

**Think of a StorageClass as a template for dynamic PV provisioning.** It standardizes storage tiers (fast SSD, cheap HDD, encrypted, replicated) so developers just request a PVC and get the right storage without knowing the backend details.

```bash
# Check which StorageClass is default
kubectl get sc

# Output:
# NAME            PROVISIONER       RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
# gp2 (default)   kubernetes.io/aws-ebs   Delete    WaitForFirstConsumer   false                  30d
# gp3             ebs.csi.aws.com         Delete    WaitForFirstConsumer   true                   5d
# efs-sc          efs.csi.aws.com         Delete    Immediate              false                  5d

# The one marked (default) is used when a PVC omits storageClassName

# Set a new default using kubectl annotate
kubectl annotate sc gp3 storageclass.kubernetes.io/is-default-class=true

# Or using kubectl patch (equivalent)
kubectl patch storageclass gp3 -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Remove old default
kubectl annotate sc gp2 storageclass.kubernetes.io/is-default-class-
# (trailing dash removes the annotation)
```

**Interview question: What is the difference between static and dynamic provisioning?**
Static provisioning requires an admin to manually create PVs before users can claim them. Dynamic provisioning uses a StorageClass to automatically create PVs when a PVC is created — the CSI driver calls the cloud API to provision the actual storage. Dynamic provisioning is the standard in production because it's self-service and eliminates the admin bottleneck.

**Interview question: Why use `WaitForFirstConsumer` instead of `Immediate`?**
`Immediate` creates the volume as soon as the PVC is created, but the volume might end up in a different AZ than where the pod gets scheduled. `WaitForFirstConsumer` delays volume creation until the pod is scheduled, ensuring the volume is in the same AZ as the node. This prevents `AttachVolume` errors.

**Static vs Dynamic Provisioning:**
- **Static Provisioning** — Admin manually creates an EBS volume, then creates a PersistentVolume (PV) referencing it. The PVC binds to the pre-created PV.
- **Dynamic Provisioning** — PVC references a StorageClass. Kubernetes automatically creates the EBS volume and PV when the PVC is created. No admin intervention needed.

### Tiered Storage Classes

You can create multiple StorageClasses to offer different performance tiers. Developers choose the tier by specifying `storageClassName` in their PVC:

```yaml
# silver — standard disk, no replication
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: silver
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-standard
  replication-type: none
```

```yaml
# gold — SSD disk, no replication
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gold
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
  replication-type: none
```

```yaml
# platinum — SSD disk with regional replication
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: platinum
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
  replication-type: regional-pd
```

On AWS, the equivalent tiers would use `ebs.csi.aws.com` with `type: gp3` (standard), `type: io2` (high IOPS), etc.

### No-Provisioner StorageClass (Local Storage)

A StorageClass with `kubernetes.io/no-provisioner` does not support dynamic provisioning — PVs must be created manually. This is used for local storage (node-attached disks):

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

PVCs referencing this class will only bind to manually-created PVs. `WaitForFirstConsumer` ensures the PV is on the same node where the pod gets scheduled.

### Lab: Storage Classes

This lab walks through listing storage classes, creating a PVC with `WaitForFirstConsumer`, deploying a pod to trigger binding, and creating a new StorageClass.

**Step 1: List existing storage classes**

```bash
kubectl get sc
# NAME                          PROVISIONER                    RECLAIMPOLICY   VOLUMEBINDINGMODE      AGE
# local-path (default)          rancher.io/local-path          Delete          WaitForFirstConsumer   15m
# local-storage                 kubernetes.io/no-provisioner   Delete          WaitForFirstConsumer   6s
# portworx-io-priority-high     kubernetes.io/portworx-volume  Delete          Immediate              6s
```

Key observations:
- `local-storage` uses `no-provisioner` — no dynamic provisioning
- `local-path` uses `WaitForFirstConsumer` — delays binding until a pod uses the PVC
- `portworx-io-priority-high` uses `Immediate` — binds as soon as PVC is created

**Step 2: Check existing PVs**

```bash
kubectl get pv
# NAME       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      STORAGECLASS    AGE
# local-pv   500Mi      RWO            Retain           Available   local-storage   2m
```

**Step 3: Create a PVC**

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: local-storage
```

```bash
kubectl create -f pvc.yaml

kubectl get pvc
# NAME        STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS    AGE
# local-pvc   Pending                                      local-storage   4s
```

The PVC is Pending despite a matching PV existing. Why?

```bash
kubectl describe pvc local-pvc | grep -A2 Events
# Events:
#   Normal  WaitForFirstConsumer  persistentvolume-controller
#     waiting for first consumer to be created before binding
```

`WaitForFirstConsumer` delays binding until a pod actually uses this PVC.

**Step 4: Deploy a pod to trigger binding**

```yaml
# nginx.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    volumeMounts:
    - mountPath: /var/www/html
      name: local-pvc-volume
  volumes:
  - name: local-pvc-volume
    persistentVolumeClaim:
      claimName: local-pvc
```

```bash
kubectl create -f nginx.yaml

# Wait a few seconds, then check
kubectl get pvc
# NAME        STATUS   VOLUME     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
# local-pvc   Bound    local-pv   500Mi      RWO            local-storage   5m
```

The pod triggered the binding — PVC is now Bound.

**Step 5: Create a new StorageClass with delayed binding**

```yaml
# delayed-volume-sc.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: delayed-volume-sc
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

```bash
kubectl create -f delayed-volume-sc.yaml

kubectl get sc
# NAME                          PROVISIONER                    VOLUMEBINDINGMODE      AGE
# local-path (default)          rancher.io/local-path          WaitForFirstConsumer   26m
# local-storage                 kubernetes.io/no-provisioner   WaitForFirstConsumer   10m
# portworx-io-priority-high     kubernetes.io/portworx-volume  Immediate              10m
# delayed-volume-sc             kubernetes.io/no-provisioner   WaitForFirstConsumer   3s
```

### MySQL with AWS EBS — Complete Walkthrough

This walkthrough deploys MySQL with persistent EBS storage, a ConfigMap for database initialization, and a headless service.

**Key concept:** `volumes` maps storage to the Pod level. `volumeMounts` maps storage to the container level. A volume must be defined in `volumes` before it can be referenced in `volumeMounts`.

#### File 1: StorageClass

```yaml
# 01-storage-class.yml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc                              # Referenced by PVCs
provisioner: ebs.csi.aws.com                 # AWS EBS CSI driver
volumeBindingMode: WaitForFirstConsumer       # Volume created only when a pod is scheduled
```

- `provisioner: ebs.csi.aws.com` — tells Kubernetes to use the AWS EBS CSI driver
- `volumeBindingMode: WaitForFirstConsumer` — delays volume creation until a pod needs it (ensures same AZ)

```bash
kubectl apply -f 01-storage-class.yml
kubectl get sc
# NAME      PROVISIONER       RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION
# ebs-sc    ebs.csi.aws.com   Delete          WaitForFirstConsumer   false
```

#### File 2: PersistentVolumeClaim

```yaml
# 02-persistent-volume-claim.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-mysql-pv-claim                   # Referenced by the Deployment
spec:
  accessModes:
    - ReadWriteOnce                           # Volume mounted by a single node
  storageClassName: ebs-sc                    # Uses the EBS StorageClass
  resources:
    requests:
      storage: 4Gi                            # Request 4GB of EBS storage
```

```bash
kubectl apply -f 02-persistent-volume-claim.yml
kubectl get pvc
# NAME                 STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# ebs-mysql-pv-claim   Pending   ...      ...        RWO            ebs-sc         10s
```

Status is `Pending` because `WaitForFirstConsumer` — the volume is created only when a pod uses this PVC.

#### File 3: ConfigMap (Database Init Script)

```yaml
# 03-UserManagement-ConfigMap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: usermanagement-dbcreation-script
data:
  mysql_usermgmt.sql: |-                      # Key = filename, value = SQL script
    DROP DATABASE IF EXISTS usermgmt;
    CREATE DATABASE usermgmt;
```

This SQL script is mounted into the MySQL container at `/docker-entrypoint-initdb.d/`. MySQL automatically executes any `.sql` files in this directory on first startup.

```bash
kubectl apply -f 03-UserManagement-ConfigMap.yml
kubectl get configmap
# NAME                               DATA   AGE
# usermanagement-dbcreation-script   1      5s
```

#### File 4: MySQL Deployment

```yaml
# 04-mysql-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1                                 # Single MySQL instance
  selector:
    matchLabels:
      app: mysql
  strategy:
    type: Recreate                            # Delete old pod before creating new (required for RWO volumes)
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
              value: dbpassword11             # Root password (use Secrets in production)
          ports:
            - containerPort: 3306
              name: mysql
          volumeMounts:                       # Maps volumes to container paths
            - name: mysql-persistent-storage
              mountPath: /var/lib/mysql        # MySQL data directory → persisted on EBS
            - name: usermanagement-dbcreation-script
              mountPath: /docker-entrypoint-initdb.d  # MySQL auto-runs .sql files here
      volumes:                                # Maps storage to the Pod
        - name: mysql-persistent-storage
          persistentVolumeClaim:
            claimName: ebs-mysql-pv-claim      # References the PVC (File 2)
        - name: usermanagement-dbcreation-script
          configMap:
            name: usermanagement-dbcreation-script  # References the ConfigMap (File 3)
```

**`strategy: Recreate`** is used because EBS volumes are `ReadWriteOnce` — only one pod can mount the volume at a time. RollingUpdate would try to start a new pod while the old one still has the volume attached, causing a Multi-Attach error.

**What happens on startup:**
1. MySQL pod starts, mounts the EBS volume at `/var/lib/mysql`
2. MySQL detects the volume is empty (first run) and initializes
3. MySQL executes `/docker-entrypoint-initdb.d/mysql_usermgmt.sql` from the ConfigMap
4. The `usermgmt` database is created
5. MySQL listens on port 3306

```bash
kubectl apply -f 04-mysql-deployment.yml
kubectl get pods
# NAME              READY   STATUS    RESTARTS   AGE
# mysql-xxxxx       1/1     Running   0          3m

# Check logs to verify DB creation
kubectl logs <mysql-pod-name>
# ... Executing '/docker-entrypoint-initdb.d/mysql_usermgmt.sql'
# ... Database 'usermgmt' created successfully.
```

#### File 5: MySQL Headless Service

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
  clusterIP: None                             # Headless service — uses Pod IP directly
```

**`clusterIP: None` (headless service):**
- DNS queries for `mysql` return the pod IP directly instead of a ClusterIP
- Other pods connect directly to the MySQL pod's IP
- Useful for stateful applications where you need stable, direct pod connections

**When to use `clusterIP: None`:**
- ✅ Databases (MySQL, PostgreSQL, MongoDB) — direct pod-to-pod connection
- ✅ StatefulSets — stable DNS-based discovery per pod
- ❌ Do NOT use for services that need external access (use NodePort or LoadBalancer instead)

```bash
kubectl apply -f 05-mysql-clusterip-service.yml
kubectl get svc
# NAME    TYPE        CLUSTER-IP   PORT(S)    AGE
# mysql   ClusterIP   None         3306/TCP   30s
```

#### Deploy Everything and Verify

```bash
# Apply all manifests
kubectl apply -f kube-manifests/

# Verify all resources
kubectl get sc          # StorageClass
kubectl get pvc         # PVC should be Bound
kubectl get pv          # PV auto-created by CSI driver
kubectl get pods        # MySQL pod running
kubectl get svc         # Headless service
```

#### Connect to MySQL and Verify

```bash
# Launch a temporary MySQL client pod
kubectl run -it --rm --image=mysql:5.6 --restart=Never mysql-client -- mysql -h mysql -pdbpassword11

# Inside the MySQL shell:
mysql> SHOW DATABASES;
# +--------------------+
# | Database           |
# +--------------------+
# | information_schema |
# | mysql              |
# | performance_schema |
# | sys                |
# | usermgmt           |  ← Created from ConfigMap
# +--------------------+

mysql> exit
```

| Command Flag | Purpose |
|---|---|
| `kubectl run -it` | Interactive terminal |
| `--rm` | Delete the pod after exiting |
| `--image=mysql:5.6` | Use MySQL 5.6 client image |
| `--restart=Never` | Don't restart the pod |
| `mysql -h mysql` | Connect to the `mysql` headless service |
| `-pdbpassword11` | Password (no space after `-p`) |

#### Summary Table

| Component | File | Purpose |
|---|---|---|
| StorageClass | `01-storage-class.yml` | Defines EBS-backed dynamic provisioning |
| PVC | `02-persistent-volume-claim.yml` | Requests 4Gi EBS volume |
| ConfigMap | `03-UserManagement-ConfigMap.yml` | SQL script to create `usermgmt` database |
| Deployment | `04-mysql-deployment.yml` | Runs MySQL with persistent volume and init script |
| Service | `05-mysql-clusterip-service.yml` | Headless service for direct pod access |

Data persists even if the MySQL pod restarts — the EBS volume is independent of the pod lifecycle.

#### File 6: User Management Microservice Deployment

```yaml
# 06-UserManagementMicroservice-Deployment.yml
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
      containers:
        - name: usermgmt-restapp
          image: stacksimplify/kube-usermanagement-microservice:1.0.0
          ports:
            - containerPort: 8095
          env:
            - name: DB_HOSTNAME
              value: "mysql"            # Headless service name from File 5
            - name: DB_PORT
              value: "3306"
            - name: DB_NAME
              value: "usermgmt"         # Database created by ConfigMap
            - name: DB_USERNAME
              value: "root"
            - name: DB_PASSWORD
              value: "dbpassword11"     # Use Secrets in production
```

**Environment variables for database connectivity:**

| Variable | Value | Purpose |
|---|---|---|
| `DB_HOSTNAME` | `mysql` | Headless service name — resolves to MySQL pod IP |
| `DB_PORT` | `3306` | MySQL port |
| `DB_NAME` | `usermgmt` | Database created by the ConfigMap init script |
| `DB_USERNAME` | `root` | MySQL root user |
| `DB_PASSWORD` | `dbpassword11` | Root password (use Secrets in production) |

⚠️ **Problem observation:** If you deploy all manifests at once, the User Management pod may restart multiple times because MySQL isn't ready yet. The microservice tries to connect to the database on startup and fails. Solution: use an **initContainer** (covered in Module 3) to wait for MySQL before starting the main container.

#### File 7: User Management NodePort Service

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
      nodePort: 31231           # Externally accessible on this port
```

```bash
kubectl get svc
# NAME                       TYPE        CLUSTER-IP      PORT(S)          AGE
# mysql                      ClusterIP   None            3306/TCP         50s
# usermgmt-restapp-service   NodePort    10.100.200.50   8095:31231/TCP   20s
```

#### Deploy and Test the Full Application

```bash
# Deploy all 7 manifests
kubectl apply -f kube-manifests/

# List pods — watch for MySQL to be ready first
kubectl get pods

# Check microservice logs (wait for DB connection)
kubectl logs -f <usermgmt-microservice-pod-name>

# Verify storage
kubectl get sc,pvc,pv

# Get service info
kubectl get svc

# Get worker node public IP
kubectl get nodes -o wide

# Access health status
# http://<EKS-WorkerNode-Public-IP>:31231/usermgmt/health-status
```

**Expected workflow:**
1. MySQL pod starts with persistent storage, `usermgmt` database is created from ConfigMap
2. User Management Microservice starts and connects to MySQL via the headless service (`mysql`)
3. Microservice is exposed externally via NodePort (31231)
4. Access the REST API via `<Node-IP>:31231`

#### Test API Endpoints

**Using curl:**

```bash
# Health Status
curl http://<Node-IP>:31231/usermgmt/health-status

# Create User
curl -X POST http://<Node-IP>:31231/usermgmt/user \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin1",
    "email": "admin@example.com",
    "role": "ROLE_ADMIN",
    "enabled": true,
    "firstname": "fname1",
    "lastname": "lname1",
    "password": "Pass@123"
  }'

# List All Users
curl http://<Node-IP>:31231/usermgmt/users

# Update User
curl -X PUT http://<Node-IP>:31231/usermgmt/user \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin1",
    "email": "admin@example.com",
    "role": "ROLE_ADMIN",
    "enabled": true,
    "firstname": "fname2",
    "lastname": "lname2",
    "password": "Pass@123"
  }'

# Delete User
curl -X DELETE http://<Node-IP>:31231/usermgmt/user/admin1
```

**Using Postman:**

1. Download Postman: https://www.postman.com/downloads/
2. Import the collection file `AWS-EKS-Masterclass-Microservices.postman_collection.json`
3. Create an environment:
   - Name: `UMS-NodePort`
   - Variable: `url` = `http://<WorkerNode-Public-IP>:31231`
4. Select the environment and test each endpoint

**API endpoints summary:**

| Endpoint | Method | URL |
|---|---|---|
| Health Status | GET | `{{url}}/usermgmt/health-status` |
| Create User | POST | `{{url}}/usermgmt/user` |
| List Users | GET | `{{url}}/usermgmt/users` |
| Update User | PUT | `{{url}}/usermgmt/user` |
| Delete User | DELETE | `{{url}}/usermgmt/user/<username>` |

#### Verify Users in MySQL Database

```bash
# Connect to MySQL
kubectl run -it --rm --image=mysql:5.6 --restart=Never mysql-client -- mysql -h mysql -u root -pdbpassword11

# Inside MySQL shell:
mysql> show schemas;
mysql> use usermgmt;
mysql> show tables;
mysql> select * from users;
mysql> exit
```

#### Clean Up

```bash
kubectl delete -f kube-manifests/
kubectl get pods
kubectl get sc,pvc,pv
```

#### Complete Application Summary

| Component | File | Purpose |
|---|---|---|
| StorageClass | `01-storage-class.yml` | EBS dynamic provisioning |
| PVC | `02-persistent-volume-claim.yml` | Requests 4Gi EBS volume |
| ConfigMap | `03-UserManagement-ConfigMap.yml` | SQL script to create `usermgmt` database |
| MySQL Deployment | `04-mysql-deployment.yml` | MySQL with persistent volume and init script |
| MySQL Service | `05-mysql-clusterip-service.yml` | Headless service for direct pod access |
| UMS Deployment | `06-UserManagementMicroservice-Deployment.yml` | REST API microservice connecting to MySQL |
| UMS Service | `07-UserManagement-Service.yml` | NodePort service for external access (31231) |

---


## 17.7 Industry Example: WordPress on EKS with Persistent Storage

```yaml
# wordpress-deployment.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
stringData:
  MYSQL_ROOT_PASSWORD: "MyR00tP@ss!"
  MYSQL_DATABASE: "wordpress"
  MYSQL_USER: "wp_user"
  MYSQL_PASSWORD: "WpP@ss123!"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: wordpress-config
data:
  WORDPRESS_DB_HOST: "mysql-service"
  WORDPRESS_DB_NAME: "wordpress"
---
# MySQL PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi
---
# WordPress PVC (shared uploads)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wordpress-pvc
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 10Gi
---
# MySQL StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql-service
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
        envFrom:
        - secretRef:
            name: mysql-secret
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
      volumes:
      - name: mysql-data
        persistentVolumeClaim:
          claimName: mysql-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
  - port: 3306
---
# WordPress Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wordpress
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      containers:
      - name: wordpress
        image: wordpress:6.4-php8.2-apache
        ports:
        - containerPort: 80
        envFrom:
        - configMapRef:
            name: wordpress-config
        env:
        - name: WORDPRESS_DB_USER
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: MYSQL_USER
        - name: WORDPRESS_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: MYSQL_PASSWORD
        volumeMounts:
        - name: wordpress-uploads
          mountPath: /var/www/html/wp-content/uploads
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
      volumes:
      - name: wordpress-uploads
        persistentVolumeClaim:
          claimName: wordpress-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: wordpress-service
spec:
  type: LoadBalancer
  selector:
    app: wordpress
  ports:
  - port: 80
    targetPort: 80
```

---

## 17.8 Common Errors & Troubleshooting

### Error: PVC stuck in Pending
```bash
kubectl describe pvc my-pvc

# Common causes:
# 1. No StorageClass exists
#    Fix: kubectl get storageclass
#
# 2. EBS CSI driver not installed
#    Fix: Install aws-ebs-csi-driver addon
#
# 3. WaitForFirstConsumer — PVC waits for a pod
#    Fix: Create a pod that uses the PVC
#
# 4. Insufficient permissions
#    Fix: Check IAM role for EBS CSI driver
```

### Error: Pod stuck in ContainerCreating (volume issue)
```bash
kubectl describe pod my-pod

# Look for events like:
# "Unable to attach or mount volumes"
# "Multi-Attach error for volume"

# Cause: EBS volume attached to another node (RWO)
# Fix: Delete the old pod first, or use EFS for RWX
```

### Error: Secret not found
```bash
# Cause: Secret doesn't exist or wrong namespace
kubectl get secrets -n <namespace>

# Fix: Create the secret in the correct namespace
kubectl create secret generic my-secret --from-literal=key=value -n <namespace>
```

---

## 17.9 Module 5 Exercises

### Exercise 1: ConfigMap and Secret
```bash
# 1. Create a ConfigMap with app settings
kubectl create configmap myapp-config --from-literal=APP_COLOR=blue --from-literal=APP_MODE=production

# 2. Create a Secret with credentials
kubectl create secret generic myapp-secret --from-literal=DB_PASS=secret123

# 3. Create a pod using both
kubectl run myapp --image=busybox --dry-run=client -o yaml > myapp-pod.yaml
# Edit to add env from configmap and secret, then apply

# 4. Verify
kubectl exec myapp -- env | grep -E "APP_|DB_"
```

### Exercise 2: Persistent Volume
```bash
# 1. Create a PVC
# 2. Create a pod that writes to the PVC
# 3. Delete the pod
# 4. Create a new pod with the same PVC
# 5. Verify data persists
```

---

**Next Module: Advanced Scheduling, Scaling & RBAC →**
