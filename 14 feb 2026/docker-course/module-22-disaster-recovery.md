# Module 22: Disaster Recovery

---

## 22.1 Why Disaster Recovery Matters

In production, failures happen: disk corruption, node crashes, network partitions, accidental deletions. Without a DR plan, you lose cluster state, services, and data.

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT CAN GO WRONG                               │
│                                                              │
│  Swarm Cluster:                                             │
│    • All manager nodes fail simultaneously                  │
│    • Raft log corruption                                    │
│    • Accidental docker swarm leave --force on managers      │
│                                                              │
│  UCP:                                                       │
│    • UCP database corruption                                │
│    • Failed UCP upgrade                                     │
│    • Certificate expiry                                     │
│                                                              │
│  DTR:                                                       │
│    • Image storage corruption                               │
│    • Metadata database failure                              │
│    • Failed DTR upgrade                                     │
│                                                              │
│  Data:                                                      │
│    • Volume data loss                                       │
│    • Accidental docker volume prune                         │
│    • Host disk failure                                      │
│                                                              │
│  DR Plan = Backup + Tested Restore Procedure                │
└─────────────────────────────────────────────────────────────┘
```

---

## 22.2 Docker Swarm Disaster Recovery

### Worker Node Failure

When a worker node goes offline, Swarm automatically reschedules its tasks to healthy workers. When the failed node returns, it becomes eligible for new tasks but existing tasks are **not** rebalanced by default.

```bash
# Force rebalance a service across all available nodes
$ docker service update --force web

# This restarts all tasks in the web service,
# distributing them evenly across available nodes
```

### Manager Node Quorum Scenarios

Swarm managers rely on Raft consensus. A majority (quorum) must be active for administrative operations.

```
┌──────────────────┬──────────┬──────────────────────────────────┐
│ Cluster Setup    │ Quorum   │ Impact When a Manager Fails      │
├──────────────────┼──────────┼──────────────────────────────────┤
│ Single manager   │ 1        │ Admin operations stop.           │
│                  │          │ Worker tasks keep running.       │
├──────────────────┼──────────┼──────────────────────────────────┤
│ Three managers   │ 2        │ One failure tolerated.           │
│                  │          │ Full functionality remains.      │
├──────────────────┼──────────┼──────────────────────────────────┤
│ Five managers    │ 3        │ Two failures tolerated.          │
│                  │          │ Full functionality remains.      │
└──────────────────┴──────────┴──────────────────────────────────┘
```

**Scenario 1: Single manager fails**

```bash
# Admin operations (adding nodes, updating services) are blocked
# Worker containers continue serving traffic

# Recovery: restart the manager or promote a worker
$ docker node promote <worker-node>
```

**Scenario 2: One of three managers fails**

```bash
# Quorum (2 of 3) remains — cluster stays fully functional
# On recovery, the failed manager rejoins automatically
# if Docker was intact on that node
```

**Scenario 3: Two of three managers fail (quorum lost)**

```bash
# Administrative operations halt completely
# Existing containers keep running but cannot be managed

# Option A: Restore the failed managers

# Option B: Bootstrap a new cluster on the remaining node
$ docker swarm init --force-new-cluster

# This preserves:
#   ✅ Service definitions
#   ✅ Networks, configs, secrets
#   ✅ Worker registrations

# Then add new managers to rebuild quorum
$ docker node promote <worker-node>
```

### What to Backup

The Swarm state is stored in `/var/lib/docker/swarm/` on manager nodes.

```
┌─────────────────────────────────────────────────────────────┐
│  /var/lib/docker/swarm/                                     │
│  ├── certificates/     ← TLS certs for node communication  │
│  │   ├── swarm-node.crt                                    │
│  │   ├── swarm-node.key                                    │
│  │   └── swarm-root-ca.crt                                 │
│  ├── raft/             ← Raft consensus log                 │
│  │   └── wal/          ← Write-ahead log entries           │
│  ├── state.json        ← Current node state                │
│  └── worker/           ← Worker-specific state             │
│                                                              │
│  The Raft database captures:                                │
│    • Cluster membership and node roles                     │
│    • Service definitions (image, replicas, ports)           │
│    • Overlay network configurations                        │
│    • Secrets and configs (encrypted)                       │
│    • TLS certificates and keys                             │
└─────────────────────────────────────────────────────────────┘
```

### Backup Procedure

```bash
# ⚠️  Run on a NON-LEADER manager to avoid triggering
#     a Raft re-election during the backup

# Step 1: Stop Docker on the manager (for consistent backup)
$ sudo systemctl stop docker

# While Docker is stopped:
#   ❌ Swarm API is unavailable on this node
#   ✅ Worker containers continue running
#   ✅ Other managers handle cluster operations

# Step 2: Backup the Swarm directory
$ sudo tar czf /backup/swarm-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    /var/lib/docker/swarm/

# Step 3: Start Docker again
$ sudo systemctl start docker

# Step 4: Verify backup
$ ls -lh /backup/swarm-backup-*.tar.gz
# -rw-r--r-- 1 root root 2.5M Jan 15 12:00 swarm-backup-20250115-120000.tar.gz

# Step 5: Copy backup offsite
$ scp /backup/swarm-backup-*.tar.gz backup-server:/backups/docker/
```

### Auto-Lock and the Unlock Key

If Swarm auto-locking is enabled (`docker swarm update --autolock=true`), the Raft database is encrypted with an unlock key. This key is stored **outside** `/var/lib/docker/swarm/` and must be backed up separately.

```bash
# View the current unlock key
$ docker swarm unlock-key
# SWMKEY-1-abc123def456...

# ⚠️  Store this key in a password manager or secure vault
# Without it, you cannot restore an auto-locked Swarm
```

### Automated Backup Script

```bash
#!/bin/bash
# swarm-backup.sh — Run on a NON-LEADER manager via cron

BACKUP_DIR="/backup/swarm"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

# Lock to prevent concurrent backups
exec 200>/tmp/swarm-backup.lock
flock -n 200 || { echo "Backup already running"; exit 1; }

echo "$(date): Starting Swarm backup"

# Stop Docker for consistent backup
systemctl stop docker

# Create backup
tar czf "$BACKUP_DIR/swarm-$DATE.tar.gz" /var/lib/docker/swarm/

# Start Docker
systemctl start docker

# Wait for Swarm to stabilize
sleep 10
docker node ls > /dev/null 2>&1 && echo "Swarm healthy after backup" || echo "WARNING: Swarm not healthy"

# Clean old backups
find "$BACKUP_DIR" -name "swarm-*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "$(date): Backup complete: swarm-$DATE.tar.gz"
```

```bash
# Add to cron (daily at 2 AM)
$ sudo crontab -e
0 2 * * * /opt/scripts/swarm-backup.sh >> /var/log/swarm-backup.log 2>&1
```

### Restore Procedure

```bash
# Scenario: All managers lost, restoring from backup

# Step 1: Install Docker on a new node and stop the engine
$ sudo systemctl stop docker

# Step 2: Ensure /var/lib/docker/swarm is empty, then extract backup
$ sudo rm -rf /var/lib/docker/swarm
$ sudo tar xzf /backup/swarm-backup-20250115-120000.tar.gz -C /

# Step 3: Start Docker
$ sudo systemctl start docker

# Step 4: Reinitialize the cluster from this node
$ docker swarm init --force-new-cluster

# Output:
# Swarm initialized: current node is now a manager.
# This preserves:
#   ✅ All service definitions
#   ✅ All secrets and configs
#   ✅ All network definitions
#   ✅ All overlay networks

# You now have a single-manager Swarm with the previous state

# Step 5: Add new manager nodes to restore HA
$ docker swarm join-token manager
# Use the token to join additional managers

# Or promote existing workers
$ docker node promote <worker-node>

# Step 6: Add worker nodes
$ docker swarm join-token worker
# Workers need to rejoin the new cluster

# Step 7: Verify
$ docker node ls
$ docker service ls
$ docker secret ls
```

---

## 22.3 UCP Backup and Restore

### What UCP Backup Captures

```
┌──────────────────────┬──────────────────────────────────────┐
│ Component            │ Description                          │
├──────────────────────┼──────────────────────────────────────┤
│ UCP Configuration    │ Enterprise license, Client CA        │
│                      │ bundles, certificates & keys         │
├──────────────────────┼──────────────────────────────────────┤
│ Access Controls      │ Teams, users, roles, grants          │
├──────────────────────┼──────────────────────────────────────┤
│ etcd Objects         │ Kubernetes declarative objects        │
│                      │ (Pods, Deployments, ReplicaSets,     │
│                      │ ConfigMaps, Secrets)                 │
├──────────────────────┼──────────────────────────────────────┤
│ UCP Volumes          │ Named volumes managed by UCP         │
├──────────────────────┼──────────────────────────────────────┤
│ Monitoring Data      │ Metrics and logs collected by UCP    │
└──────────────────────┴──────────────────────────────────────┘

⚠️  UCP does NOT back up Docker Swarm services, configs, or
    overlay networks. Use Swarm backup tools for those (22.2).
```

### UCP Backup — CLI Method

```bash
# Run the official UCP image in backup mode
$ docker container run --rm \
    --log-driver none \
    --name ucp-backup \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /tmp:/backup \
    docker/ucp:3.2.5 backup \
    --file /backup/ucp-backup.tar \
    --passphrase "YourStrongPass" \
    --include-logs=false

# --file:           output archive path
# --passphrase:     encrypts the backup (required for restore)
# --include-logs:   include container logs (default: true, set false to reduce size)
# --log-driver none: prevents backup container from generating logs

# Verify backup
$ ls -lh /tmp/ucp-backup.tar
```

### UCP Backup — Web UI Method

```
UCP Web UI → Admin Settings → Backup
  → Click "Start Backup"
  → Set a passphrase
  → Monitor progress
  → Download the backup archive
```

### UCP Restore

```bash
# Step 1: Uninstall any existing UCP
$ docker container run --rm -it \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    docker/ucp:3.2.5 uninstall

# Step 2: Restore from backup
$ docker container run --rm -i \
    --name ucp-restore \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /tmp:/backup \
    docker/ucp:3.2.5 restore \
    --passphrase "YourStrongPass" \
    < /tmp/ucp-backup.tar

# During restore you can choose to:
#   • Reuse the same Swarm cluster
#   • Provision a new Swarm cluster
#   • Restore onto a standalone Docker host
#     (UCP initializes Swarm automatically)
```

### UCP Backup Key Considerations

```
┌──────────────────────┬──────────────────────────────────────┐
│ Topic                │ Details                              │
├──────────────────────┼──────────────────────────────────────┤
│ Single Operation     │ Only one UCP backup or restore can   │
│                      │ run at a time                        │
├──────────────────────┼──────────────────────────────────────┤
│ Cluster Version      │ Restore target MUST match the        │
│                      │ backup's Docker Enterprise/UCP       │
│                      │ version                              │
├──────────────────────┼──────────────────────────────────────┤
│ Swarm Workloads      │ UCP backups EXCLUDE Docker Swarm     │
│                      │ services, configs, and networks      │
├──────────────────────┼──────────────────────────────────────┤
│ Failed Cluster       │ You CANNOT back up a cluster that    │
│                      │ has already failed — prepare backups │
│                      │ in advance                           │
├──────────────────────┼──────────────────────────────────────┤
│ Restore Destinations │ Original Swarm cluster, new cluster, │
│                      │ or standalone Docker host            │
└──────────────────────┴──────────────────────────────────────┘

⚠️  Always verify that your passphrase and backup archive
    are accessible before starting a restore.
```

---

## 22.4 DTR Backup and Restore

DTR has two separate components to protect: **metadata** (database) and **image data** (storage).

### DTR High Availability Architecture

A single-replica DTR using local filesystem storage provides no redundancy. For fault tolerance:

```
┌─────────────────────────────────────────────────────────────┐
│              DTR HA ARCHITECTURE                             │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ DTR      │  │ DTR      │  │ DTR      │                 │
│  │ Replica 1│  │ Replica 2│  │ Replica 3│                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│       │              │              │                       │
│       └──────────────┼──────────────┘                       │
│                      │                                      │
│  ┌───────────────────┴───────────────────────┐             │
│  │  DTR-OL (Private Overlay Network)         │             │
│  │  Connects DTR replicas for replication    │             │
│  └───────────────────┬───────────────────────┘             │
│                      │                                      │
│  ┌───────────────────┴───────────────────────┐             │
│  │  External Object Store (S3 / GCS / Azure) │             │
│  │  Stores image layers (fault-tolerant)     │             │
│  └───────────────────────────────────────────┘             │
│                                                              │
│  Requirements:                                              │
│    • Minimum 3 DTR replicas for quorum                     │
│    • Private overlay network connecting replicas           │
│    • External object store for image layers                │
│                                                              │
│  ⚠️  Local filesystem storage on individual replicas       │
│     is NOT fault-tolerant. Always use an external          │
│     object store for image data at scale.                  │
└─────────────────────────────────────────────────────────────┘
```

### What to Backup in DTR

Even with image layers safely stored in S3, you must preserve DTR's metadata:

```
┌──────────────────────────┬──────────────────────────────────┐
│ Metadata Category        │ Description                      │
├──────────────────────────┼──────────────────────────────────┤
│ Configuration settings   │ Registry config, storage drivers │
├──────────────────────────┼──────────────────────────────────┤
│ Repository definitions   │ Namespaces, repository tags      │
├──────────────────────────┼──────────────────────────────────┤
│ Access control policies  │ User/team permissions, LDAP/AD   │
├──────────────────────────┼──────────────────────────────────┤
│ Image signing data       │ Docker Content Trust keys        │
├──────────────────────────┼──────────────────────────────────┤
│ Vulnerability scan       │ Scan results and policy configs  │
│ reports                  │                                  │
├──────────────────────────┼──────────────────────────────────┤
│ TLS certificates & keys  │ Registry TLS assets              │
└──────────────────────────┴──────────────────────────────────┘
```

### DTR Metadata Backup

Run the DTR backup container against any existing replica to generate a tar archive of all metadata:

```bash
$ docker run --rm docker/dtr backup \
    --ucp-url $UCP_URL \
    --ucp-ca-cert-path $CA_PATH \
    --ucp-username $USERNAME \
    --ucp-password $PASSWORD \
    --existing-replica-id $REPLICA_ID \
    > dtr-metadata-backup.tar

# --ucp-url:              UCP management URL
# --ucp-ca-cert-path:     Path to UCP CA certificate
# --ucp-username/password: UCP admin credentials
# --existing-replica-id:   ID of any running DTR replica
```

### DTR Image Data Backup

Image data backup depends on your storage backend:

```bash
# If using local storage:
$ sudo tar czf /backup/dtr-images-$(date +%Y%m%d).tar.gz \
    /var/lib/docker/volumes/dtr-registry-*

# If using S3:
#   Images are already in S3 — ensure S3 versioning is enabled
#   Backup the S3 bucket separately (or rely on S3 durability)

# If using Azure Blob Storage:
#   Use Azure backup/replication features

# If using NFS:
#   Backup the NFS share using your NFS backup tools
```

### DTR Restore

```bash
# Step 1: Destroy existing DTR containers to clean up state
$ docker run --rm -it docker/dtr destroy \
    --ucp-url $UCP_URL \
    --ucp-insecure-tls

# Step 2: (If needed) Rehydrate image layers in your object store
#   Re-upload to S3 if the bucket was lost
#   Restore local storage from tar backup if using local FS

# Step 3: Import the metadata backup
$ docker run --rm -i docker/dtr restore \
    < dtr-metadata-backup.tar

# Step 4: Re-deploy additional replicas and confirm quorum
#   Add DTR replicas via UCP or CLI
#   Verify all replicas are healthy
```

### DTR Restore — Full Walkthrough (Local Storage)

```bash
# Step 1: Install a fresh DTR replica
$ docker run -it --rm \
    docker/dtr:2.8.8 install \
    --ucp-node worker-1 \
    --ucp-url https://ucp-host \
    --ucp-username admin \
    --ucp-password ********

# Step 2: Restore metadata
$ docker run -i --rm \
    docker/dtr:2.8.8 restore \
    --ucp-url https://ucp-host \
    --ucp-username admin \
    --ucp-password ******** \
    --existing-replica-id abc123 \
    < /backup/dtr-metadata-20250115.tar

# Step 3: Restore image data (local storage)
$ sudo tar xzf /backup/dtr-images-20250115.tar.gz -C /

# Step 4: Verify
# Access DTR web UI
# Check repositories and images are present
# Run a test pull
$ docker pull dtr.example.com/myorg/myapp:1.0
```

---

## 22.5 Volume Backup and Restore

### Backup a Named Volume

```bash
# Use a temporary container to tar the volume contents
$ docker run --rm \
    -v mydata:/source:ro \
    -v $(pwd):/backup \
    alpine tar czf /backup/mydata-$(date +%Y%m%d).tar.gz -C /source .

# Verify
$ ls -lh mydata-*.tar.gz
```

### Restore a Named Volume

```bash
# Create the volume (if it doesn't exist)
$ docker volume create mydata

# Restore from backup
$ docker run --rm \
    -v mydata:/target \
    -v $(pwd):/backup:ro \
    alpine tar xzf /backup/mydata-20250115.tar.gz -C /target

# Verify
$ docker run --rm -v mydata:/data alpine ls /data
```

### Database-Specific Backups

```bash
# PostgreSQL
$ docker exec db pg_dump -U postgres mydb > /backup/mydb-$(date +%Y%m%d).sql

# Restore
$ docker exec -i db psql -U postgres mydb < /backup/mydb-20250115.sql

# MySQL
$ docker exec db mysqldump -u root -p mydb > /backup/mydb-$(date +%Y%m%d).sql

# Restore
$ docker exec -i db mysql -u root -p mydb < /backup/mydb-20250115.sql

# MongoDB
$ docker exec db mongodump --out /backup/dump
$ docker cp db:/backup/dump ./mongo-backup-$(date +%Y%m%d)

# Restore
$ docker cp ./mongo-backup-20250115 db:/backup/dump
$ docker exec db mongorestore /backup/dump
```

---

## 22.6 DR Planning Checklist

```
┌──────────────────────────────────────────────────────────────┐
│  DISASTER RECOVERY CHECKLIST                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Backup Schedule:                                           │
│  ☐ Swarm state: daily (on one manager)                      │
│  ☐ UCP: daily                                               │
│  ☐ DTR metadata: daily                                      │
│  ☐ DTR images: depends on storage backend                   │
│  ☐ Application volumes: per RPO requirements                │
│  ☐ Database dumps: per RPO requirements                     │
│                                                              │
│  Backup Storage:                                            │
│  ☐ Store backups offsite (different datacenter/cloud)       │
│  ☐ Encrypt backups at rest                                  │
│  ☐ Retain backups per policy (e.g., 30 days)               │
│  ☐ Test backup integrity regularly                          │
│                                                              │
│  Restore Testing:                                           │
│  ☐ Test Swarm restore quarterly                             │
│  ☐ Test UCP restore quarterly                               │
│  ☐ Test DTR restore quarterly                               │
│  ☐ Test volume restore monthly                              │
│  ☐ Document restore procedures                              │
│  ☐ Measure RTO (Recovery Time Objective)                    │
│                                                              │
│  High Availability (Prevention):                            │
│  ☐ 3 or 5 Swarm managers across availability zones         │
│  ☐ Multiple DTR replicas                                    │
│  ☐ Replicated storage backend for DTR                       │
│  ☐ Database replication for application data                │
│  ☐ External load balancer for UCP and DTR                   │
│                                                              │
│  Documentation:                                             │
│  ☐ Backup procedures documented and accessible              │
│  ☐ Restore procedures documented and tested                 │
│  ☐ Contact list for DR scenarios                            │
│  ☐ Runbooks for common failure scenarios                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 22.7 DR Scenarios and Recovery Steps

```
┌──────────────────────┬──────────────────────────────────────┐
│ Scenario             │ Recovery Steps                       │
├──────────────────────┼──────────────────────────────────────┤
│ Single worker fails  │ Swarm reschedules tasks to other     │
│                      │ workers automatically                │
│                      │ Replace node and rejoin              │
│                      │ Force rebalance: docker service      │
│                      │   update --force <service>           │
│                      │ No restore needed                    │
├──────────────────────┼──────────────────────────────────────┤
│ Single manager fails │ Other managers maintain quorum       │
│                      │ Replace failed node, rejoin cluster  │
│                      │ Or promote a worker                  │
│                      │ No restore needed                    │
├──────────────────────┼──────────────────────────────────────┤
│ Quorum lost          │ Restore Swarm from backup            │
│ (majority of         │ docker swarm init --force-new-cluster│
│ managers down)       │ Rejoin workers and new managers      │
├──────────────────────┼──────────────────────────────────────┤
│ All managers lost    │ Restore Swarm from backup on new host│
│                      │ docker swarm init --force-new-cluster│
│                      │ Restore UCP from backup              │
│                      │ Rejoin all nodes                     │
├──────────────────────┼──────────────────────────────────────┤
│ UCP corruption       │ Uninstall UCP (docker/ucp uninstall)│
│                      │ Restore from UCP backup with         │
│                      │   passphrase                         │
│                      │ Can restore to same cluster, new     │
│                      │   cluster, or standalone host        │
│                      │ Verify users, teams, grants          │
├──────────────────────┼──────────────────────────────────────┤
│ DTR data loss        │ Destroy existing DTR containers      │
│                      │ Rehydrate image layers (S3/local)    │
│                      │ Restore metadata from backup         │
│                      │ Re-deploy additional replicas        │
│                      │ Confirm quorum membership            │
├──────────────────────┼──────────────────────────────────────┤
│ Volume data loss     │ Restore from volume backup           │
│                      │ Or restore from database dump        │
│                      │ Restart affected services            │
└──────────────────────┴──────────────────────────────────────┘
```

### Docker Enterprise DR Summary Table

```
┌────────────────┬──────────────────────────┬──────────────────────────┐
│ Component      │ Backup Target            │ Tool / Storage           │
├────────────────┼──────────────────────────┼──────────────────────────┤
│ Swarm          │ Raft logs (nodes,        │ tar /var/lib/docker/swarm│
│                │ services, overlay nets,  │ on a non-leader manager  │
│                │ secrets, configs)        │                          │
├────────────────┼──────────────────────────┼──────────────────────────┤
│ UCP            │ UCP config, access       │ docker/ucp backup        │
│                │ controls, etcd objects,  │ (CLI or Web UI)          │
│                │ certificates             │                          │
├────────────────┼──────────────────────────┼──────────────────────────┤
│ DTR (images)   │ Container image layers   │ External Object Store    │
│                │                          │ (S3, GCS, Azure Blob)    │
├────────────────┼──────────────────────────┼──────────────────────────┤
│ DTR (metadata) │ Config, repos, ACLs,     │ docker/dtr backup        │
│                │ scans, TLS, signing keys │                          │
└────────────────┴──────────────────────────┴──────────────────────────┘
```

---

## Module 22 Summary

- DR planning requires regular backups, offsite storage, and tested restore procedures
- **Worker node failure**: Swarm reschedules tasks automatically; use `docker service update --force` to rebalance
- **Manager quorum loss**: use `docker swarm init --force-new-cluster` on a surviving manager or restore from backup
- **Swarm backup**: tar `/var/lib/docker/swarm/` on a **non-leader** manager — contains services, secrets, configs, certs, Raft log
- Stop Docker before backing up Swarm state for consistency; other managers handle operations during the backup
- If auto-lock is enabled, back up the Swarm unlock key separately — it's stored outside `/var/lib/docker/swarm/`
- **Swarm restore**: extract backup to new host, `docker swarm init --force-new-cluster`, promote workers or add new managers
- **UCP backup**: `docker/ucp backup` via CLI or Web UI — captures config, RBAC, etcd objects, certificates
- UCP backups are encrypted with a passphrase — store the passphrase securely
- UCP backups **exclude** Swarm services, configs, and overlay networks — back those up separately
- UCP restore target **must** match the backup's Docker Enterprise/UCP version
- UCP can restore to the same cluster, a new cluster, or a standalone Docker host
- Only one UCP backup or restore can run at a time; you cannot back up a cluster that has already failed
- **DTR HA**: use 3+ replicas on a private overlay network with an external object store (S3/GCS/Azure) for image layers
- Local filesystem storage on individual DTR replicas is **not** fault-tolerant
- **DTR metadata backup**: `docker/dtr backup` — captures config, repos, ACLs, scan results, signing keys, TLS certs
- **DTR image backup**: depends on storage backend — S3 versioning, NFS backup, or local tar
- **DTR restore**: destroy existing containers → rehydrate image layers → restore metadata → re-deploy replicas
- **Volume backup**: use temporary containers with tar to archive volume contents
- **Database backup**: use native tools (pg_dump, mysqldump, mongodump) for application-consistent backups
- Automate backups with cron scripts and retention policies
- Test restores regularly — an untested backup is not a backup
- HA prevents most failures: 3+ managers across zones, DTR replicas, replicated storage
- Document all procedures and keep runbooks accessible

---

**Previous Module: [Module 21 - Docker Enterprise](module-21-docker-enterprise.md)**

**Next Module: [Module 23 - Kubernetes Fundamentals](module-23-kubernetes-fundamentals.md)**
