# Module 19: Raft Consensus & Swarm High Availability

---

## 19.1 Why Consensus Matters in a Cluster

In a Docker Swarm cluster, multiple manager nodes share responsibility for the cluster state. They must agree on:

- Which services exist and their desired state
- Which nodes are available
- Where tasks should be scheduled
- The current leader

Without a consensus algorithm, managers could disagree, leading to split-brain scenarios and data corruption.

```
┌─────────────────────────────────────────────────────────────┐
│              THE CONSENSUS PROBLEM                           │
│                                                              │
│  3 managers must agree on cluster state:                    │
│                                                              │
│  Manager 1: "web service has 3 replicas"                    │
│  Manager 2: "web service has 3 replicas"                    │
│  Manager 3: "web service has 5 replicas"  ← disagrees!     │
│                                                              │
│  Which is correct? How do they resolve this?                │
│  Answer: Raft consensus algorithm                           │
│                                                              │
│  Raft ensures:                                              │
│    • One leader makes decisions                             │
│    • Majority must agree before changes are committed       │
│    • All managers eventually have the same state            │
└─────────────────────────────────────────────────────────────┘
```

---

## 19.2 What is Raft?

Raft is a consensus algorithm that ensures a group of nodes agree on a shared state, even when some nodes fail.

Docker Swarm uses Raft to replicate the cluster state across all manager nodes.

```
┌─────────────────────────────────────────────────────────────┐
│              RAFT KEY CONCEPTS                               │
│                                                              │
│  Leader:                                                    │
│    One manager is elected leader                            │
│    Leader handles all write operations                      │
│    Leader replicates changes to followers                   │
│                                                              │
│  Followers:                                                 │
│    Other managers are followers (Reachable)                 │
│    They receive replicated state from the leader            │
│    They can become leader if current leader fails           │
│                                                              │
│  Log:                                                       │
│    Ordered sequence of state changes                        │
│    Replicated across all managers                           │
│    Changes are committed only when majority acknowledges    │
│                                                              │
│  Term:                                                      │
│    A period of time with one leader                         │
│    New election = new term                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 19.3 How Raft Works in Docker Swarm

### Write Operation Flow

```
┌─────────────────────────────────────────────────────────────┐
│              RAFT WRITE FLOW                                 │
│                                                              │
│  1. Client sends command to leader:                         │
│     "docker service scale web=5"                            │
│                                                              │
│  2. Leader appends to its log:                              │
│     Entry: {term:3, index:42, cmd:"scale web=5"}           │
│                                                              │
│  3. Leader replicates entry to followers:                   │
│     Leader → Manager 2: "append entry 42"                  │
│     Leader → Manager 3: "append entry 42"                  │
│                                                              │
│  4. Followers acknowledge:                                  │
│     Manager 2 → Leader: "ACK entry 42"                     │
│     Manager 3 → Leader: "ACK entry 42"                     │
│                                                              │
│  5. Leader commits when MAJORITY acknowledges:              │
│     3 managers, 2 ACKs (leader + 1 follower) = majority    │
│     Entry 42 is committed                                  │
│                                                              │
│  6. Leader applies the change and responds to client        │
│                                                              │
│  7. Followers apply committed entries                       │
└─────────────────────────────────────────────────────────────┘
```

### Leader Election

```
┌─────────────────────────────────────────────────────────────┐
│              LEADER ELECTION                                 │
│                                                              │
│  1. Leader sends heartbeats to followers periodically       │
│                                                              │
│  2. If a follower doesn't receive heartbeat within          │
│     election timeout → it becomes a CANDIDATE               │
│                                                              │
│  3. Candidate increments term and requests votes:           │
│     "I'm running for leader in term 4"                     │
│                                                              │
│  4. Other managers vote (one vote per term):                │
│     Manager 2 → Candidate: "You have my vote"              │
│     Manager 3 → Candidate: "You have my vote"              │
│                                                              │
│  5. Candidate with majority votes becomes leader            │
│     (In a 3-node cluster: needs 2 votes)                   │
│                                                              │
│  6. New leader starts sending heartbeats                    │
│                                                              │
│  Election is fast — typically completes in milliseconds     │
└─────────────────────────────────────────────────────────────┘
```

---

## 19.4 Quorum — The Magic Number

**Quorum** is the minimum number of managers that must be available for the cluster to function. It's calculated as:

```
Quorum = (N / 2) + 1    (where N = total managers, integer division)
```

```
┌──────────────────┬──────────┬──────────┬───────────────────┐
│ Total Managers   │ Quorum   │ Fault    │ Can Lose          │
│ (N)              │ (N/2+1)  │Tolerance │                   │
├──────────────────┼──────────┼──────────┼───────────────────┤
│ 1                │ 1        │ 0        │ None — no HA      │
│ 2                │ 2        │ 0        │ None — avoid this │
│ 3                │ 2        │ 1        │ 1 manager         │
│ 4                │ 3        │ 1        │ 1 manager         │
│ 5                │ 3        │ 2        │ 2 managers        │
│ 6                │ 4        │ 2        │ 2 managers        │
│ 7                │ 4        │ 3        │ 3 managers        │
└──────────────────┴──────────┴──────────┴───────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│              KEY OBSERVATIONS                                │
│                                                              │
│  1. Always use ODD numbers of managers (3, 5, 7)            │
│     Even numbers waste a node without improving tolerance   │
│     3 managers: lose 1 → still works                       │
│     4 managers: lose 1 → still works (same as 3!)          │
│                                                              │
│  2. Recommended: 3 or 5 managers                            │
│     3 = good for most clusters                              │
│     5 = large production clusters                           │
│     7 = maximum recommended (more adds latency)            │
│                                                              │
│  3. More managers = more latency                            │
│     Every write must be replicated to majority              │
│     7+ managers slows down cluster operations               │
│                                                              │
│  4. 2 managers is WORSE than 1                              │
│     If 1 fails, you lose quorum (need 2, have 1)           │
│     With 1 manager, at least it works until it fails        │
└─────────────────────────────────────────────────────────────┘
```

---

## 19.5 What Happens When Quorum is Lost?

```
┌─────────────────────────────────────────────────────────────┐
│              QUORUM LOSS SCENARIO                            │
│                                                              │
│  5-manager cluster (quorum = 3):                            │
│                                                              │
│  Normal:                                                    │
│    M1(Leader) M2(Reachable) M3(Reachable) M4 M5            │
│    Quorum: 5/5 ✅                                           │
│                                                              │
│  Lose 1 manager:                                            │
│    M1(Leader) M2(Reachable) ❌M3 M4 M5                     │
│    Quorum: 4/5 ✅ (4 ≥ 3)                                  │
│                                                              │
│  Lose 2 managers:                                           │
│    M1(Leader) M2(Reachable) ❌M3 ❌M4 M5                   │
│    Quorum: 3/5 ✅ (3 ≥ 3)                                  │
│                                                              │
│  Lose 3 managers:                                           │
│    M1 M2 ❌M3 ❌M4 ❌M5                                    │
│    Quorum: 2/5 ❌ (2 < 3) — QUORUM LOST                   │
│                                                              │
│  When quorum is lost:                                       │
│    ❌ Cannot create/update/remove services                  │
│    ❌ Cannot scale services                                 │
│    ❌ Cannot add/remove nodes                               │
│    ✅ Existing containers KEEP RUNNING                      │
│    ✅ Existing tasks continue to serve traffic              │
│                                                              │
│  The cluster is "frozen" — no new decisions can be made     │
│  But running workloads are NOT affected                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 19.6 Recovering from Quorum Loss

### Option 1: Bring Failed Managers Back Online

```bash
# Best option — restore the failed nodes
# Once quorum is restored, cluster resumes normal operation

# Check node status
$ docker node ls
# ID        HOSTNAME    STATUS    AVAILABILITY    MANAGER STATUS
# abc       manager-1   Ready     Active          Leader
# def       manager-2   Ready     Active          Reachable
# ghi       manager-3   Down      Active          Unreachable  ← fix this
```

### Option 2: Force New Cluster (Last Resort)

```bash
# If managers cannot be recovered, force a new cluster
# from a single remaining manager

# On the surviving manager:
$ docker swarm init --force-new-cluster

# This:
#   1. Creates a new single-manager cluster
#   2. Preserves existing services and tasks
#   3. Old managers become invalid
#   4. Workers need to rejoin

# Then add new managers:
$ docker swarm join-token manager
# Use the token to join new manager nodes
```

---

## 19.7 Swarm High Availability Architecture

### Recommended Production Setup

```
┌─────────────────────────────────────────────────────────────┐
│              PRODUCTION HA ARCHITECTURE                      │
│                                                              │
│  Managers (3 or 5):                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │Manager 1 │  │Manager 2 │  │Manager 3 │                 │
│  │ Leader   │  │Reachable │  │Reachable │                 │
│  │ Drain    │  │ Drain    │  │ Drain    │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│       │              │              │                       │
│       └──────────────┼──────────────┘                       │
│                      │                                      │
│  Workers (N):        │                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Worker 1  │  │Worker 2  │  │Worker 3  │  │Worker N  │  │
│  │ Active   │  │ Active   │  │ Active   │  │ Active   │  │
│  │ Tasks    │  │ Tasks    │  │ Tasks    │  │ Tasks    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                              │
│  Best practices:                                            │
│    • Drain managers — don't run workloads on them           │
│    • Spread managers across availability zones              │
│    • Use odd number of managers (3 or 5)                    │
│    • Monitor manager health                                 │
│    • Backup Swarm state regularly                           │
└─────────────────────────────────────────────────────────────┘
```

### Spreading Managers Across Zones

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-ZONE DEPLOYMENT                           │
│                                                              │
│  Zone A          Zone B          Zone C                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │Manager 1 │   │Manager 2 │   │Manager 3 │               │
│  │Worker 1  │   │Worker 2  │   │Worker 3  │               │
│  │Worker 4  │   │Worker 5  │   │Worker 6  │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│                                                              │
│  If Zone A goes down:                                       │
│    Lost: Manager 1, Worker 1, Worker 4                     │
│    Remaining: 2 managers (quorum maintained)                │
│    Cluster continues operating                              │
│                                                              │
│  ⚠️  Never put all managers in the same zone               │
└─────────────────────────────────────────────────────────────┘
```

---

## 19.8 Manager Node Operations

### Promote a Worker to Manager

```bash
$ docker node promote worker-2
# Node worker-2 promoted to a manager in the swarm.

$ docker node ls
# worker-2   Ready   Active   Reachable   ← now a manager
```

### Demote a Manager to Worker

```bash
$ docker node demote manager-3
# Manager manager-3 demoted in the swarm.

# ⚠️  Cannot demote the last manager
# ⚠️  Cannot demote if it would break quorum
```

### Drain a Manager (Prevent Workloads)

```bash
$ docker node update --availability drain manager-1

# Existing tasks on manager-1 are rescheduled to workers
# No new tasks will be placed on manager-1
# Manager still participates in Raft consensus
```

---

## 19.9 Monitoring Swarm Health

```bash
# Check cluster health
$ docker node ls
# Look for:
#   STATUS = Ready (all nodes)
#   MANAGER STATUS = Leader (exactly one)
#   MANAGER STATUS = Reachable (other managers)
#   No "Down" or "Unreachable" nodes

# Check Raft status
$ docker info | grep -A5 "Swarm"
# Swarm: active
#  NodeID: abc123
#  Is Manager: true
#  ClusterID: def456
#  Managers: 3
#  Nodes: 6

# Check if current node is the leader
$ docker node inspect self --format='{{.ManagerStatus.Leader}}'
# true  or  false
```

---

## 19.10 Swarm State Backup

The Swarm state is stored in `/var/lib/docker/swarm/` on manager nodes.

```bash
# Stop Docker on the manager (to get consistent backup)
$ sudo systemctl stop docker

# Backup the Swarm directory
$ sudo tar czf swarm-backup-$(date +%Y%m%d).tar.gz /var/lib/docker/swarm/

# Start Docker again
$ sudo systemctl start docker

# Store backup offsite
$ scp swarm-backup-*.tar.gz backup-server:/backups/
```

### Restore from Backup

```bash
# Stop Docker
$ sudo systemctl stop docker

# Remove current Swarm state
$ sudo rm -rf /var/lib/docker/swarm

# Restore from backup
$ sudo tar xzf swarm-backup-20250115.tar.gz -C /

# Reinitialize from backup
$ sudo systemctl start docker
$ docker swarm init --force-new-cluster
```

---

## 19.11 Common Errors and Troubleshooting

### Error 1: "rpc error: code = Unknown desc = The swarm does not have a leader"

```bash
# CAUSE: Quorum lost — not enough managers available
# Fix Option 1: Bring failed managers back online
# Fix Option 2: Force new cluster
$ docker swarm init --force-new-cluster
```

### Error 2: "manager stopped: can't determine current Raft status"

```bash
# CAUSE: Raft log corruption or disk issue
# Fix: Check disk space and filesystem health
$ df -h /var/lib/docker
$ sudo journalctl -u docker.service --no-pager -n 50
```

### Error 3: Node Shows "Unreachable" for Extended Period

```bash
# CAUSE: Network partition or node failure
# Fix: Check network connectivity between managers
$ ping manager-2
$ telnet manager-2 2377

# If node is permanently lost, remove it
$ docker node rm --force manager-2
# Then add a replacement manager
```

---

## Module 19 Summary

- Docker Swarm uses the **Raft consensus algorithm** to maintain consistent cluster state across managers
- One manager is the **Leader** (handles writes); others are **Followers/Reachable** (replicate state)
- **Quorum** = (N/2) + 1 — the minimum managers needed for the cluster to function
- Always use **odd numbers** of managers: 3 (tolerates 1 failure), 5 (tolerates 2), 7 (tolerates 3)
- 2 managers is worse than 1 — losing either breaks quorum
- More than 7 managers adds latency without meaningful benefit
- When quorum is lost: existing containers keep running, but no new operations are possible
- Recover quorum by restoring failed managers or using `docker swarm init --force-new-cluster`
- **Drain** managers to prevent workloads from running on control-plane nodes
- Spread managers across availability zones for zone-level fault tolerance
- Backup Swarm state from `/var/lib/docker/swarm/` on manager nodes
- Monitor with `docker node ls` — watch for Down/Unreachable status
- Leader election happens automatically when the current leader fails — typically completes in milliseconds
- Every write operation requires majority acknowledgment before it's committed

---

**Previous Module: [Module 18 - Storage Drivers](module-18-storage-drivers.md)**

**Next Module: [Module 20 - Docker Security Deep Dive](module-20-security-deep-dive.md)**
