# Module 11: Container Orchestration and Docker Swarm

---

## 11.1 Recap — What Docker Does on a Single Machine

Docker allows you to:

- Create containers
- Run applications inside containers
- Manage containers on a **single machine**

```bash
$ docker run nginx
# Runs nginx container on YOUR machine
```

Standalone Docker (one daemon on one machine) is fine for:

```
✅ Dev work
✅ Smoke tests
✅ docker-compose on a single host
```

But in **QA/Stage/Prod** you usually need:

```
- Many containers across many machines
- Monitoring, scaling, failover
- Load balancing
- Rolling updates
```

Docker daemon manages containers **only on one machine**.

---

## 11.2 The Problem — Single Machine Limits

### Resource Constraints

```
┌─────────────────────────────────────────────────────────────┐
│              SINGLE MACHINE LIMITS                           │
│                                                              │
│  Machine specs:                                             │
│    RAM = 12 GB                                              │
│    Each container needs = 4 GB                              │
│                                                              │
│  Max containers possible:                                   │
│    12 / 4 = 3 containers (theoretically)                    │
│    But OS uses RAM, so maybe only 2 containers              │
│                                                              │
│  If you need 5 containers:                                  │
│    ❌ Cannot create all on one machine                      │
│    ✅ You need MULTIPLE machines                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.3 Problems Without Orchestration

Suppose you have 4 machines and need 5 containers:

```
Machine A    Machine B    Machine C    Machine D
```

### Problem 1: Manual Container Creation

You must manually login to each machine:

```bash
$ ssh machine1
$ docker run nginx

$ ssh machine2
$ docker run nginx

# Imagine doing this for 100 machines.
# Impossible to manage manually.
```

### Problem 2: Machine Failure

```
┌─────────────────────────────────────────────────────────────┐
│              MACHINE FAILURE                                 │
│                                                              │
│  Before crash:                                              │
│    Machine A → 2 containers                                 │
│    Machine B → 2 containers                                 │
│    Machine C → 1 container                                  │
│    Total = 5 containers ✅                                  │
│                                                              │
│  Machine B crashes:                                         │
│    Machine A → 2 containers                                 │
│    Machine B → ❌ DOWN                                      │
│    Machine C → 1 container                                  │
│    Total = 3 containers ❌ (required = 5)                   │
│                                                              │
│  You must manually detect failure and recreate containers.  │
└─────────────────────────────────────────────────────────────┘
```

### Problem 3: Container Health Monitoring

```bash
$ docker ps

# Output:
# CONTAINER ID   STATUS
# abc123         Up 5 minutes

# Container is "running" but application inside may be BROKEN.
# Docker alone cannot manage health across multiple machines.
```

### Problem 4: Load Balancing

Without orchestration:
- No automatic load balancing
- Manual configuration required
- Users must know which machine to connect to

### Problem 5: Scaling Containers

```
Initially need:  5 containers
Later need:     20 containers

Manual creation is slow and error-prone.
```

---

## 11.4 Solution — Container Orchestration

### Definition

Container orchestration is **automated management of containers across multiple machines**.

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT ORCHESTRATION PROVIDES                      │
│                                                              │
│  1. Automatic Container Placement                           │
│     You say: "I need 10 containers"                         │
│     Orchestration decides: which machine, where to place    │
│                                                              │
│  2. Automatic Healing                                       │
│     Container crashes → orchestration creates new one       │
│                                                              │
│  3. Scaling                                                 │
│     5 → 20 containers automatically                         │
│                                                              │
│  4. Load Balancing                                          │
│     Traffic distributed across containers automatically     │
│                                                              │
│  5. Rolling Updates                                         │
│     Update version 1 → version 2 without downtime           │
│     Orchestration replaces containers gradually             │
│                                                              │
│  6. Service Discovery / Load Balancing                      │
│     Containers find each other by service name              │
│     Traffic distributed automatically                       │
│                                                              │
│  7. Central Control                                         │
│     Manage everything from manager node(s)                  │
└─────────────────────────────────────────────────────────────┘
```

### What Orchestration Provides (Summary)

```
Scheduling       → places containers automatically on available nodes
Desired state    → you declare "I want N containers", it keeps N running
Self-healing     → if a task/container fails → auto replacement
Scaling          → change replicas up/down quickly
Rolling updates  → deploy gradually; rollback restores previous state
Service discovery→ containers find each other by name
Load balancing   → traffic distributed across replicas
Central control  → manage from manager node(s)
```

### Orchestration Tools

```
┌──────────────────────┬──────────────────────┐
│    Docker Swarm      │    Kubernetes         │
├──────────────────────┼──────────────────────┤
│ Built into Docker    │ Separate platform     │
│ Simple to set up     │ More complex          │
│ Good for small/mid   │ Industry standard     │
│ Native Docker CLI    │ kubectl CLI           │
│ Limited features     │ Full-featured         │
└──────────────────────┴──────────────────────┘

This module focuses on Docker Swarm.
```

---

## 11.5 What is Docker Swarm?

Docker Swarm is Docker's **built-in orchestration tool**.

It allows:
- Multiple machines to work as a **single cluster**
- Managed from **one machine** (the manager)

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER SWARM                                    │
│                                                              │
│  Docker Swarm = cluster of Docker hosts                     │
│                                                              │
│  Without Swarm:                                             │
│    Each machine is independent                              │
│    You manage each one separately                           │
│                                                              │
│  With Swarm:                                                │
│    All machines form ONE cluster                            │
│    You manage everything from ONE machine (manager)         │
│    Containers are distributed automatically                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.6 Cluster Concept

A **cluster** is a group of machines working together.

```
              Cluster
        -------------------
        |    |    |    |
       Node Node Node Node

Each machine = Node
```

---

## 11.7 Types of Nodes

### Manager Node

The manager **controls** the cluster.

Responsibilities:
- Accept commands from user
- Schedule containers on nodes
- Monitor cluster health
- Manage workers

### Worker Node

Workers **run** containers.

Responsibilities:
- Run containers (tasks)
- Report status to manager

```
┌─────────────────────────────────────────────────────────────┐
│              SWARM NODE TYPES                                │
│                                                              │
│           Manager Node                                      │
│          (control center)                                   │
│               │                                              │
│      ┌────────┼────────┐                                    │
│      │        │        │                                    │
│   Worker1  Worker2  Worker3                                 │
│      │        │        │                                    │
│  Container Container Container                              │
│                                                              │
│  Manager assigns tasks.                                     │
│  Workers run containers.                                    │
└─────────────────────────────────────────────────────────────┘
```

### Real-World Analogy

```
Company structure:

  CEO        → Manager Node
  Manager    → Manager Node
  Employees  → Worker Nodes
  Tasks      → Containers
  Project    → Service

Manager assigns work.
Employees do work.
```

---

## 11.8 Important Terms

### Node

A **node** is a machine in the swarm.

```
Machine 1 → Node
Machine 2 → Node
Machine 3 → Node
```

### Service

A **service** defines the desired state:
- Container image
- Number of containers (replicas)
- Ports
- Volumes
- Environment variables

```
Service = nginx, replicas = 3
Means: create 3 nginx containers
```

### Task

A **task** is an individual container instance.

```
Service: nginx (replicas = 3)

Tasks:
  Task 1 → nginx container on worker-1
  Task 2 → nginx container on worker-2
  Task 3 → nginx container on worker-3
```

### Concept Map

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE → TASK → CONTAINER                      │
│                                                              │
│  Service (desired state definition)                         │
│     │                                                        │
│     ├── Task 1 → Container (on worker-1)                    │
│     ├── Task 2 → Container (on worker-2)                    │
│     └── Task 3 → Container (on worker-3)                    │
│                                                              │
│  Service defines WHAT to run                                │
│  Tasks are HOW MANY to run                                  │
│  Containers are WHERE they run                              │
└─────────────────────────────────────────────────────────────┘
```

### Summary Table

```
┌──────────────┬──────────────────────────────────────┐
│ Concept      │ Meaning                              │
├──────────────┼──────────────────────────────────────┤
│ Node         │ Machine in the swarm                 │
│ Manager      │ Controls the cluster                 │
│ Worker       │ Runs containers                      │
│ Service      │ Defines desired state (image,        │
│              │ replicas, ports)                     │
│ Task         │ Individual container instance         │
│ Swarm        │ The cluster itself                   │
└──────────────┴──────────────────────────────────────┘
```

---

## 11.9 Swarm Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              SWARM ARCHITECTURE                              │
│                                                              │
│              Manager Node                                   │
│             (control center)                                │
│                  │                                           │
│         ┌────────┼────────┐                                 │
│         │        │        │                                 │
│      Worker1  Worker2  Worker3                              │
│         │        │        │                                 │
│     Container Container Container                           │
│                                                              │
│  Manager assigns tasks.                                     │
│  Workers run containers.                                    │
│                                                              │
│  All nodes communicate over port 2377.                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.10 Swarm Initialization Commands

### Check Swarm Status

```bash
$ docker info

# Output (look for):
# Swarm: inactive     ← swarm not enabled
# Swarm: active       ← swarm is running
```

### Initialize Swarm

```bash
$ docker swarm init

# Output:
# Swarm initialized: current node is now a manager.
#
# To add a worker to this swarm, run the following command:
#   docker swarm join --token SWMTKN-1-abc123... 192.168.1.10:2377

# This machine becomes the MANAGER.
```

### Join Worker to Swarm

Run on each worker machine:

```bash
$ docker swarm join --token SWMTKN-1-abc123... 192.168.1.10:2377

# Output:
# This node joined a swarm as a worker.
```

### View Nodes in Cluster

```bash
$ docker node ls

# Output:
# ID          HOSTNAME    STATUS   AVAILABILITY   MANAGER STATUS
# abc123 *    manager1    Ready    Active         Leader
# def456      worker1     Ready    Active
# ghi789      worker2     Ready    Active

# * = current node
# Leader = this is the active manager
```

---

## 11.11 Creating and Managing Services

### Create a Service

```bash
$ docker service create --name web --replicas 3 nginx

# Creates:
#   Service name: web
#   Image: nginx
#   Replicas: 3 containers
```

### Create Service with Port Mapping

```bash
$ docker service create --name web --replicas 3 -p 8080:80 nginx

# Exposes:
#   Container port 80 → Host port 8080
#   Accessible on ANY node at port 8080
```

### List Services

```bash
$ docker service ls

# Output:
# ID        NAME   MODE        REPLICAS   IMAGE          PORTS
# abc123    web    replicated  3/3        nginx:latest   *:8080->80/tcp

# REPLICAS 3/3 means:
#   desired: 3
#   running: 3
```

### Interpreting REPLICAS

```
┌─────────────────────────────────────────────────────────────┐
│              REPLICAS INTERPRETATION                         │
│                                                              │
│  3/3 = desired 3, running 3 → all healthy ✅               │
│  1/3 = desired 3, running 1 → two missing ⚠️               │
│        Swarm is trying to recover or failing to schedule    │
│  0/3 = desired 3, running 0 → all failed ❌                │
│        Image pull issue, no resources, or node drained      │
│                                                              │
│  Check why with: docker service ps <service>                │
│  Look for tasks in "Rejected" or "Failed" state             │
└─────────────────────────────────────────────────────────────┘
```

### Check Service Tasks (Where Containers Run)

```bash
$ docker service ps web

# Output:
# ID      NAME    IMAGE          NODE       DESIRED STATE  CURRENT STATE
# xyz1    web.1   nginx:latest   worker-1   Running        Running 10s ago
# xyz2    web.2   nginx:latest   worker-2   Running        Running 10s ago
# xyz3    web.3   nginx:latest   worker-3   Running        Running 10s ago

# Shows which node runs which container.
```

---

## 11.12 Scaling Services

### Scale Up

```bash
$ docker service scale web=5

# Output:
# web scaled to 5

$ docker service ls
# REPLICAS 5/5

$ docker service ps web
# web.1   worker-1   Running
# web.2   worker-2   Running
# web.3   worker-3   Running
# web.4   worker-1   Running
# web.5   worker-2   Running

# Swarm distributes containers across available nodes.
```

### Scale Down

```bash
$ docker service scale web=2

# Swarm automatically stops/removes 3 tasks to match desired state.
# REPLICAS 2/2
```

### Create Service with Replicas Directly

Instead of creating then scaling:

```bash
# Create with 3 replicas immediately
$ docker service create --name web --replicas 3 -p 8080:80 nginx

# ✅ Creates 3 containers immediately
```

---

## 11.13 Load Balancing

User sends request → Manager routes to worker nodes → Containers handle request.

```
┌─────────────────────────────────────────────────────────────┐
│              SWARM LOAD BALANCING                            │
│                                                              │
│  User → any-node:8080 → Swarm routes → Container           │
│                                                              │
│  Requests distributed automatically across replicas.        │
│                                                              │
│  Request 1 → web.1 (worker-1)                              │
│  Request 2 → web.2 (worker-2)                              │
│  Request 3 → web.3 (worker-3)                              │
│  Request 4 → web.1 (round-robin repeats)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.14 Rolling Updates

Update application image without downtime:

```bash
$ docker service update --image nginx:1.17 web

# What happens:
#   Swarm stops old containers GRADUALLY
#   Swarm starts new containers with new image
#   No downtime — containers replaced one at a time

$ docker service ls
# IMAGE column now shows: nginx:1.17

$ docker service ps web
# You'll see:
#   Old tasks: Shutdown
#   New tasks: Running
```

---

## 11.15 Container Failure Recovery (Self-Healing)

```
┌─────────────────────────────────────────────────────────────┐
│              AUTOMATIC RECOVERY                              │
│                                                              │
│  Before crash:                                              │
│    Replicas: 3/3 ✅                                         │
│                                                              │
│  Container crashes:                                         │
│    Swarm detects failure                                    │
│    Swarm creates new container automatically                │
│                                                              │
│  After recovery:                                            │
│    Replicas: 3/3 ✅                                         │
│                                                              │
│  No manual intervention needed.                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.16 Removing a Service

```bash
$ docker service rm web

# Deletes the service AND all its tasks (containers) across the cluster.
# You do NOT need to know which node the containers are on.
```

---

## 11.17 Complete Workflow Example

```bash
# Step 1: Create swarm
$ docker swarm init

# Step 2: Join workers
$ docker swarm join --token SWMTKN-1-abc123... 192.168.1.10:2377

# Step 3: Create service
$ docker service create --name web --replicas 3 -p 8080:80 nginx

# Step 4: Check service
$ docker service ls
$ docker service ps web

# Step 5: Scale service
$ docker service scale web=10

# Step 6: Update image
$ docker service update --image nginx:1.17 web

# Step 7: Remove service
$ docker service rm web
```

---

## 11.18 Key Advantages of Docker Swarm

```
┌─────────────────────────────────────────────────────────────┐
│              SWARM ADVANTAGES                                │
│                                                              │
│  ✅ Automatic scaling                                       │
│  ✅ Automatic recovery (self-healing)                       │
│  ✅ Load balancing (routing mesh)                           │
│  ✅ Centralized control (manage from one node)              │
│  ✅ Easy deployment (one command)                           │
│  ✅ Rolling updates (zero downtime)                         │
│  ✅ Built into Docker (no extra installation)               │
└─────────────────────────────────────────────────────────────┘
```

---



## 11.19 Swarm Mode — Standalone vs Swarm

Docker has two operating modes:

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER OPERATING MODES                          │
│                                                              │
│  Standalone mode (default):                                 │
│    One Docker daemon controls only itself                   │
│    docker run, docker ps, etc. work                         │
│    docker node ls → ERROR (not a swarm manager)             │
│    docker service create → ERROR                            │
│                                                              │
│  Swarm mode:                                                │
│    Docker daemons joined into a cluster                     │
│    All standalone commands still work                       │
│    PLUS: docker node, docker service, docker stack          │
└─────────────────────────────────────────────────────────────┘
```

### How to Verify Swarm Status

```bash
$ docker info

# Look for:
# Swarm: inactive    → no swarm features available
# Swarm: active      → swarm features enabled

# Swarm-only commands (docker node ls, docker service ...)
# work ONLY when Swarm: active
```

---

## 11.20 Viewing Cluster Nodes — docker node ls

```bash
# Run ONLY on a manager node
$ docker node ls

# Output:
# ID                            HOSTNAME     STATUS  AVAILABILITY  MANAGER STATUS
# 9q... *                       manager-1    Ready   Active        Leader
# jm...                         worker-1     Ready   Active
# kp...                         worker-2     Ready   Active
# aq...                         worker-3     Ready   Active
```

### Column Meanings

```
┌──────────────────┬──────────────────────────────────────────┐
│ Column           │ Meaning                                  │
├──────────────────┼──────────────────────────────────────────┤
│ ID               │ Unique node ID (* = current node)        │
│ HOSTNAME         │ Machine name                             │
│ STATUS           │ Ready = reachable/healthy                │
│                  │ Down = not reachable                     │
│ AVAILABILITY     │ Active = can receive tasks               │
│                  │ Drain = will NOT receive tasks            │
│ MANAGER STATUS   │ (blank) = worker                         │
│                  │ Leader = active manager leader            │
│                  │ Reachable = backup manager                │
└──────────────────┴──────────────────────────────────────────┘
```

**Important:** `docker node ls` works only on manager nodes. Workers cannot list nodes.

---

## 11.21 Manager vs Worker vs Leader vs Reachable

Swarm nodes are either **Worker** or **Manager**.

Among manager nodes:
- Exactly **one** is the **Leader**
- Other managers are **Reachable** (backup leaders)

```
┌─────────────────────────────────────────────────────────────┐
│              NODE ROLES                                      │
│                                                              │
│  Managers:                                                  │
│    [Leader]     ← only one at a time                        │
│    [Reachable]  ← eligible to become leader                 │
│    [Reachable]  ← eligible to become leader                 │
│                                                              │
│  Workers:                                                   │
│    [Worker]     ← runs containers only                      │
│    [Worker]     ← runs containers only                      │
│                                                              │
│  "Manager" does NOT mean "Leader"                           │
│  Manager = eligible to become leader                        │
│  Leader = the one currently in charge                       │
└─────────────────────────────────────────────────────────────┘
```

### Why Multiple Managers? — High Availability

If the leader goes down, a reachable manager becomes leader automatically.

```
Before leader crash:
  manager-1 = Leader
  manager-2 = Reachable

After leader crash:
  manager-1 = (down)
  manager-2 = Leader        ← automatic election

When manager-1 returns:
  manager-1 = Reachable     ← becomes backup
  manager-2 = Leader        ← stays leader
```

---

## 11.22 Promoting Workers to Manager

```bash
# Run on the leader manager:
$ docker node promote worker-2

# Now docker node ls shows:
# worker-2 → manager with status: Reachable
# Existing leader stays: Leader
```

**Important nuance:**
- "Manager" doesn't mean leader
- It means the node is **eligible** to become leader
- Only one leader exists at any time

---

## 11.23 Inspect a Service

```bash
# Default output (JSON)
$ docker service inspect web

# Pretty output (human-readable)
$ docker service inspect --pretty web

# Shows: service name, image, replicas, ports, update policy, networks
```

---

## 11.24 Task ID vs Container ID

`docker service ps web` shows **Task IDs**, not container IDs.

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE → TASK → CONTAINER                      │
│                                                              │
│  Service: defines desired state                             │
│     └── Task: replica (has Task ID)                         │
│            └── Container: actual runtime unit (Container ID)│
│                                                              │
│  To get container ID from task:                             │
│  $ docker inspect <task_id>                                 │
│  → shows which node + container ID                          │
│                                                              │
│  Then on that node:                                         │
│  $ docker ps → match the container ID                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.25 Prevent Running Containers on Manager — Drain

### Why Drain the Manager?

Managers handle orchestration (scheduling, state, RAFT consensus). Running heavy workloads on the manager risks control-plane instability.

```bash
$ docker node update --availability drain manager-1

# docker node ls now shows:
# AVAILABILITY = Drain for manager-1
```

### What Drain Does

```
┌─────────────────────────────────────────────────────────────┐
│              DRAIN BEHAVIOR                                  │
│                                                              │
│  1. No NEW tasks scheduled on this node                     │
│  2. Existing tasks are MOVED to other nodes                 │
│  3. Replica count maintained                                │
│                                                              │
│  Active = schedule tasks here                               │
│  Drain  = evacuate / do not schedule here                   │
│                                                              │
│  Example:                                                   │
│    Before drain: manager-1 running web.3                    │
│    After drain:  web.3 moved to worker-2                    │
│    Replicas still 3/3                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.26 Rolling Update — Detailed

```bash
# Update service image
$ docker service update --image nginx:1.17 web

# Keeps same service name, ports, replicas
# Replaces old containers GRADUALLY with new image
# Zero/low downtime

# Verify:
$ docker service ls
# IMAGE: nginx:1.17

$ docker service ps web
# Old tasks: Shutdown
# New tasks: Running (nginx:1.17)
```

---

## 11.27 End-to-End Lab Flow

```bash
# Step 1: Create service with 3 replicas
$ docker service create --name web --replicas 3 -p 8080:80 nginx:latest

# Step 2: Confirm
$ docker service ls
$ docker service ps web

# Step 3: Scale up to 6
$ docker service scale web=6

# Step 4: Drain manager
$ docker node update --availability drain manager-1

# Step 5: Rolling update
$ docker service update --image nginx:1.17 web

# Step 6: Remove service
$ docker service rm web
```

---

## 11.28 Rollback in Docker Swarm

### Why Rollback is Needed

When you update a service to a new image version:
- Swarm stops old containers gradually
- Swarm starts new containers with new image
- If the new image is **broken/corrupted** or doesn't start:
  - Fewer replicas running
  - Downtime
  - "Stuck" deployment

Every deployment needs rollback capability.

### Manual Rollback

```bash
$ docker service update --rollback web

# Reverts the service to its PREVIOUS specification:
#   Previous image tag
#   Previous settings (update policy, configs, etc.)
#   Maintains replica count (desired state stays the same)

# Verify:
$ docker service ls
# Before rollback: nginx:1.17
# After rollback:  nginx:latest (previous image)
```

### Automatic Rollback (Failure Action)

Instead of manually rolling back, tell Swarm to rollback automatically on failure:

```bash
$ docker service update \
    --update-failure-action rollback \
    --image nginx:1.17 \
    web

# If Swarm can't bring new tasks to a healthy running state:
#   → automatically triggers rollback to previous stable version
```

---

## 11.29 Service Modes — Replicated vs Global

### Replicated Mode (Default)

You specify exact number of replicas. Swarm maintains exactly N tasks.

```bash
$ docker service create --name web --replicas 3 nginx

# Service maintains: 3/3
# If one fails → Swarm replaces it
```

### Global Mode

You do **not** specify replicas. Swarm runs **exactly 1 task per eligible node**.

```bash
$ docker service create --name agent --mode global nginx

# If you have 5 active worker nodes → 5 tasks run
# Add one node → automatically becomes 6 tasks
# Remove a node → drops back accordingly
```

### When to Use Global Mode

```
┌─────────────────────────────────────────────────────────────┐
│              GLOBAL MODE USE CASES                           │
│                                                              │
│  "Agent on every node" scenarios:                           │
│                                                              │
│  ✅ Log collectors (Logstash / Filebeat / Fluentd)          │
│  ✅ Monitoring agents (node exporter, Datadog agent)        │
│  ✅ Security agents                                         │
│  ✅ Host-level metrics collectors                           │
│                                                              │
│  Global mode is perfect when you need exactly ONE           │
│  instance per machine, regardless of cluster size.          │
└─────────────────────────────────────────────────────────────┘
```

### Global Mode with Drain/Unreachable Nodes

```
Nodes:
  worker-1  Ready Active     ✅ gets global task
  worker-2  Ready Active     ✅ gets global task
  manager   Ready Drain      ❌ no global task
  worker-3  Unreachable      ❌ no global task

Global service tasks = 2
```

### Replicated vs Global Comparison

```
┌──────────────────┬──────────────────────────────────────────┐
│ Replicated       │ Global                                   │
├──────────────────┼──────────────────────────────────────────┤
│ --replicas N     │ --mode global                            │
│ You choose count │ 1 per eligible node                      │
│ Default mode     │ Must specify explicitly                  │
│ App workloads    │ Agent/monitoring workloads               │
│ Can scale up/down│ Scales with cluster size                 │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 11.30 Stack — Declarative Deployment Using Compose YAML

### Why Stacks Exist

Running commands manually (imperative) is not practical in real deployments. Instead, define services in a YAML file and deploy it.

### What is a Stack?

A **stack** is a collection of services deployed together.

```
Stack
 ├── service A
 ├── service B
 └── service C
```

### Example Swarm Compose File

```yaml
# docker-compose.yml (Swarm-style with deploy:)
version: "3.8"

services:
  demo_web:
    image: nginx:latest
    ports:
      - "8080:80"
    deploy:
      mode: replicated
      replicas: 2
```

**Important notes:**
- `deploy:` section is used by Swarm, not regular `docker-compose up`
- If `mode: global`, you do NOT set `replicas`

### Deploy the Stack

```bash
$ docker stack deploy -c docker-compose.yml testweb

# Where:
#   -c docker-compose.yml = compose file path
#   testweb = stack name (you choose)

# Output:
# Creating network testweb_default
# Creating service testweb_demo_web
```

### View Stacks and Services

```bash
# List stacks
$ docker stack ls
# NAME      SERVICES   ORCHESTRATOR
# testweb   1          Swarm

# List services inside a stack
$ docker stack services testweb
# ID        NAME              MODE        REPLICAS   IMAGE
# abc123    testweb_demo_web  replicated  2/2        nginx:latest

# List tasks (containers) in a stack
$ docker stack ps testweb
# Shows which node each task runs on
```

**Stack is a "wrapper" for services. Services are the actual units that run tasks.**

---

## 11.31 Swarm Self-Healing Demo

### Desired State

Service wants 2 replicas. Swarm ensures **always 2 tasks running**.

```
Service: web (replicas=2)

worker-1: web.1
worker-2: web.2
```

### If You Kill a Container Manually

```bash
# On the node where container is running:
$ docker rm -f <container_id>

# What happens next:
#   1. Swarm detects task is missing/failed
#   2. Swarm creates a new replacement container automatically
#   3. Service returns to 2/2

# Verify:
$ docker service ls
# REPLICAS: 2/2 ✅

$ docker service ps web
# Shows old task as "Shutdown" and new task as "Running"
```

**Orchestration is not just creation — it's continuous maintenance of desired state.**

---

## 11.32 Swarm Load Balancing — Ingress Routing Mesh

### The Problem Without Swarm

If a container runs on machine B, you must use machine B's IP. With multiple replicas, you need external load balancing.

### What Swarm Provides: Routing Mesh

When you publish a port for a service, that port becomes available on **every node**. Traffic to any node on that port is routed internally to a running task.

This is called **ingress routing mesh**.

### Example

```bash
$ docker service create --name web --replicas 3 -p 8080:80 nginx

# Even if tasks run only on worker-2 and worker-3:
# You can access from ANY node:
#   node1:8080 ✅
#   node2:8080 ✅
#   node3:8080 ✅
# Swarm forwards traffic to an active replica.
```

### Round-Robin Behavior

```
┌─────────────────────────────────────────────────────────────┐
│              INGRESS ROUTING MESH                            │
│                                                              │
│  Client → Node(any):8080 → Swarm routing mesh → Task       │
│                                                              │
│  Request 1 → web.1 (worker-1)                              │
│  Request 2 → web.2 (worker-2)                              │
│  Request 3 → web.3 (worker-3)                              │
│  Request 4 → web.1 (round-robin repeats)                   │
│                                                              │
│  Every node listens on published port.                      │
│  Swarm routes to any healthy replica.                       │
└─────────────────────────────────────────────────────────────┘
```

### External Load Balancer in Production

```
┌─────────────────────────────────────────────────────────────┐
│              PRODUCTION SETUP                                │
│                                                              │
│  External LB (AWS ALB/NLB, F5, etc.)                       │
│         │                                                    │
│         ▼                                                    │
│  Swarm Nodes (any node:8080)                                │
│         │                                                    │
│         ▼                                                    │
│  Routing Mesh → Tasks                                       │
│                                                              │
│  You don't need to know:                                    │
│    - Which node hosts the container                         │
│    - Which container port mapping is where                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.33 Docker Config in Swarm

### Why Docker Config Exists

Images should contain common app artifacts only. Environment-specific values (DB endpoints, feature flags, etc.) should be injected at runtime.

**Problems with naive approaches:**

```
┌─────────────────────────────────────────────────────────────┐
│  ❌ Environment variables                                   │
│     Can't hold large config files (multi-line, structured)  │
│                                                              │
│  ❌ Volume mounts                                           │
│     Require copying config files to EVERY node manually     │
│     In Swarm, containers can land on ANY node               │
│     You don't know which node in advance                    │
│                                                              │
│  ✅ Docker Config                                           │
│     Store config in Swarm's distributed state               │
│     Swarm injects it into containers at runtime             │
│     Works regardless of which node the container lands on   │
└─────────────────────────────────────────────────────────────┘
```

Similar to Kubernetes ConfigMap.

### Create a Config

```bash
# Create a config file
$ echo "db.host=qa-db.local" > sample.conf

# Store it in Swarm
$ docker config create test_config sample.conf

# List configs
$ docker config ls
# ID          NAME          CREATED AT
# abc123      test_config   2 minutes ago
```

### Use Config in a Service

```bash
$ docker service create \
    --name web \
    --config source=test_config,target=/tmp/sample.conf \
    -p 8080:80 \
    nginx

# Meaning:
#   Take swarm config named "test_config"
#   Mount it inside container as /tmp/sample.conf
```

### Verify Config Inside Container

```bash
# Find where it runs
$ docker service ps web

# Go to that node and exec
$ docker exec -it <container_id> sh
$ ls /tmp
$ cat /tmp/sample.conf
# Output: db.host=qa-db.local

# ✅ Swarm injected the file
```

### Config via Compose YAML (Stack)

```yaml
version: "3.8"

services:
  web:
    image: nginx:latest
    configs:
      - source: test_config
        target: /tmp/sample.conf
    ports:
      - "8080:80"

configs:
  test_config:
    external: true
    # external: true means config already exists in swarm
    # (created earlier via docker config create)
    # stack just references it
```

---

## 11.34 Health Checks in Swarm

### Why Health Checks Matter

Swarm knows if a container is **running**. But running does NOT mean **healthy**.

```
Container is UP → but app inside CRASHED
Service is effectively BROKEN
Docker status shows "Up" but app returns errors
```

Health checks tell Swarm how to verify app health **inside** the container.

### How It Works

You define:
- A **command** (test)
- **interval** — how often to run it
- **timeout** — max time the command can take
- **retries** — how many failures before unhealthy
- **start_period** — grace time before checks begin

If test returns:
- `0` → healthy
- non-zero → unhealthy

If unhealthy consistently → Swarm restarts/replaces the task.

### Health Check YAML Example

```yaml
services:
  app:
    image: nginx:latest
    deploy:
      replicas: 2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 60s
```

### Parameter Meanings

```
┌──────────────────┬──────────────────────────────────────────┐
│ Parameter        │ Meaning                                  │
├──────────────────┼──────────────────────────────────────────┤
│ test             │ Command to run inside container          │
│ interval         │ How often to run the check               │
│ timeout          │ Max time the command can take             │
│ retries          │ Failures allowed before "unhealthy"      │
│ start_period     │ Grace time before checks begin           │
└──────────────────┴──────────────────────────────────────────┘
```

### Why start_period is Important

```
┌─────────────────────────────────────────────────────────────┐
│              START PERIOD                                     │
│                                                              │
│  Problem:                                                   │
│    App takes 40 seconds to start                            │
│    Health check begins immediately                          │
│    First few checks FAIL                                    │
│    Swarm thinks container is bad                            │
│    Restarts it repeatedly                                   │
│    App NEVER stabilizes                                     │
│                                                              │
│  Solution:                                                  │
│    start_period: 60s                                        │
│    Health checks begin only AFTER 60 seconds                │
│    App has time to initialize                               │
└─────────────────────────────────────────────────────────────┘
```

### Failing Health Check Behavior

```yaml
# If health check command is invalid:
healthcheck:
  test: ["CMD", "no_such_command"]

# Result:
#   Always fails
#   Swarm keeps trying to restart/replace tasks
#   Service stuck — tasks constantly restarting

# Diagnose with:
$ docker service ps <service>
$ docker inspect <task_or_container_id>
```

---

## 11.35 Big Picture Diagram — Everything Together

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE SWARM ARCHITECTURE                     │
│                                                              │
│                External Load Balancer (optional)            │
│                          │                                   │
│                     any-node:8080                            │
│                          │                                   │
│                  Swarm Routing Mesh (ingress)                │
│                  /         │          \                      │
│              web.1       web.2       web.3                   │
│            (worker1)   (worker2)   (worker3)                │
│                                                              │
│  Service defines desired state:                             │
│    - image: nginx                                           │
│    - replicas: 3                                            │
│    - ports: 8080->80                                        │
│    - configs: injected from swarm storage                   │
│    - healthcheck: verify app inside container               │
│    - update/rollback policies: safe deployments             │
│                                                              │
│  Swarm Cluster:                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Manager Nodes (Control)                           │     │
│  │    Leader: manager-1                               │     │
│  │    Reachable: manager-2                            │     │
│  │    Reachable: manager-3                            │     │
│  │                                                    │     │
│  │  Worker Nodes (Run tasks)                          │     │
│  │    worker-1  worker-2  worker-3                    │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  If a task fails → Swarm recreates it automatically.        │
│  If leader fails → Reachable becomes Leader automatically.  │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.36 Command Cheat Sheet

### Cluster / Nodes

```bash
# Check swarm status
$ docker info

# Initialize swarm
$ docker swarm init

# Join as worker
$ docker swarm join --token <token> <manager-ip>:2377

# List nodes (manager only)
$ docker node ls

# Promote worker to manager
$ docker node promote <node>

# Set node to drain (stop scheduling tasks)
$ docker node update --availability drain <node>

# Set node back to active
$ docker node update --availability active <node>
```

### Services

```bash
# Create service
$ docker service create --name web --replicas 3 -p 8080:80 nginx

# List services
$ docker service ls

# List tasks and placement
$ docker service ps <service>

# Scale replicas
$ docker service scale <service>=N

# Inspect service (human-readable)
$ docker service inspect --pretty <service>

# Rolling update
$ docker service update --image <image:tag> <service>

# Rollback to previous version
$ docker service update --rollback <service>

# Update with auto-rollback on failure
$ docker service update --update-failure-action rollback --image <image:tag> <service>

# Delete service
$ docker service rm <service>
```

### Stacks

```bash
# Deploy stack from compose file
$ docker stack deploy -c docker-compose.yml <stack-name>

# List stacks
$ docker stack ls

# List services in stack
$ docker stack services <stack-name>

# List tasks in stack
$ docker stack ps <stack-name>

# Remove stack
$ docker stack rm <stack-name>
```

### Config

```bash
# Create config
$ docker config create <name> <file>

# List configs
$ docker config ls

# Use config in service
$ docker service create --config source=<name>,target=<path> ...

# Inspect config
$ docker config inspect <name>

# Remove config
$ docker config rm <name>
```

---

## 11.37 Docker Swarm Interview Questions

```
┌──────────────────────────────────────────────────────────────┐
│  DOCKER SWARM INTERVIEW Q&A                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Q: What is Docker Swarm?                                   │
│  A: Docker Swarm is Docker's native container orchestration │
│     tool that allows managing multiple Docker hosts as a    │
│     single cluster and deploying containers across them.    │
│                                                              │
│  Q: What is the difference between a container and a        │
│     service?                                                │
│  A: Container = single running instance.                    │
│     Service = defines desired state and number of           │
│     containers (replicas). Swarm maintains the desired      │
│     state automatically.                                    │
│                                                              │
│  Q: What is a manager node?                                 │
│  A: Manager controls the cluster, accepts commands,         │
│     schedules containers, and monitors cluster health.      │
│     One manager is the Leader; others are Reachable.        │
│                                                              │
│  Q: What is a worker node?                                  │
│  A: Worker executes containers (tasks) assigned by the      │
│     manager. Workers cannot manage the cluster.             │
│                                                              │
│  Q: What happens if the leader manager goes down?           │
│  A: A Reachable manager is automatically elected as the     │
│     new Leader. This is high availability.                  │
│                                                              │
│  Q: What is the difference between replicated and global    │
│     service modes?                                          │
│  A: Replicated = you specify exact replica count.           │
│     Global = exactly 1 task per eligible node.              │
│     Global is used for agents/monitoring on every node.     │
│                                                              │
│  Q: What is the ingress routing mesh?                       │
│  A: Published ports are available on EVERY node. Traffic    │
│     to any node is routed to a running task via             │
│     round-robin load balancing.                             │
│                                                              │
│  Q: How do you rollback a failed update?                    │
│  A: docker service update --rollback <service>              │
│     Or set --update-failure-action rollback for automatic   │
│     rollback on failure.                                    │
│                                                              │
│  Q: What is drain availability?                             │
│  A: Drain means no new tasks will be scheduled on that      │
│     node, and existing tasks are moved elsewhere.           │
│     Used for managers or maintenance.                       │
│                                                              │
│  Q: What is a stack in Docker Swarm?                        │
│  A: A stack is a collection of services deployed from a     │
│     compose YAML file using docker stack deploy.            │
│     It's the declarative way to deploy in Swarm.            │
│                                                              │
│  Q: What is Docker Config?                                  │
│  A: Docker Config stores configuration files in the swarm  │
│     and injects them into containers at runtime.            │
│     Similar to Kubernetes ConfigMap.                        │
│                                                              │
│  Q: Why are health checks important in Swarm?               │
│  A: Container running ≠ app healthy. Health checks verify  │
│     the application inside the container is working.        │
│     Swarm replaces unhealthy tasks automatically.           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 11.38 Debugging Health Check Failures

```bash
# Step 1: View tasks and their states
$ docker service ps <service>
# Look for tasks in "Failed" or "Rejected" state
# Look for tasks constantly restarting

# Step 2: Inspect a specific task or container
$ docker inspect <task-id-or-container-id>
# Check "Status" and "Health" fields

# Step 3: Common causes
```

```
┌─────────────────────────────────────────────────────────────┐
│              HEALTH CHECK DEBUGGING                          │
│                                                              │
│  Problem: Tasks constantly restarting                        │
│                                                              │
│  Cause 1: Health check command doesn't exist                │
│    test: ["CMD", "no_such_command"]                         │
│    Fix: Use a valid command (curl, wget, etc.)              │
│                                                              │
│  Cause 2: start_period too short                            │
│    App takes 40s to start, checks begin immediately         │
│    Early checks fail → Swarm restarts → never stabilizes   │
│    Fix: Set start_period > typical startup time             │
│                                                              │
│  Cause 3: timeout too short                                 │
│    Health check command takes longer than timeout           │
│    Fix: Increase timeout value                              │
│                                                              │
│  Cause 4: App genuinely unhealthy                           │
│    Fix: Check app logs, fix the application                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.39 One-Page Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│              SWARM MENTAL MODEL                              │
│                                                              │
│  You declare state (Service / Stack YAML)                   │
│         │                                                    │
│         ▼                                                    │
│  Swarm schedules tasks on nodes                             │
│         │                                                    │
│         ▼                                                    │
│  Tasks create containers                                    │
│         │                                                    │
│         ▼                                                    │
│  Swarm keeps desired replica count                          │
│         │                                                    │
│         ▼                                                    │
│  Health checks validate app health                          │
│         │                                                    │
│         ▼                                                    │
│  Ingress routing mesh load-balances traffic                 │
│         │                                                    │
│         ▼                                                    │
│  Updates deploy gradually; rollback restores previous state │
│         │                                                    │
│         ▼                                                    │
│  Configs inject env-specific files cleanly                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.40 Swarm Auto Lock

Docker Swarm stores two keys on manager nodes: the TLS key (for inter-node communication) and the Raft log encryption key (for cluster state). By default these are stored unencrypted on disk. Auto-lock encrypts them with a separate unlock key.

### Why Auto Lock?

```
┌─────────────────────────────────────────────────────────────┐
│              SWARM KEY SECURITY                              │
│                                                              │
│  Without auto-lock:                                         │
│    TLS key and Raft key stored in plaintext on disk         │
│    If someone gains access to the manager's filesystem,     │
│    they can read all secrets and impersonate the node       │
│                                                              │
│  With auto-lock:                                            │
│    Keys are encrypted with an unlock key                    │
│    When Docker restarts, you must provide the unlock key    │
│    Without it, the manager cannot rejoin the Swarm          │
└─────────────────────────────────────────────────────────────┘
```

### Enable Auto Lock

```bash
# Initialize a new Swarm with auto-lock enabled
$ docker swarm init --autolock

# Output includes the unlock key:
# Swarm initialized: current node is now a manager.
# To unlock a swarm manager after it restarts, run the
# `docker swarm unlock` command and provide the following key:
#     SWMKEY-1-WkRhReFlKxiLsJQmzruH3gYfYPNOKz9pSah1o26ic1o
# Please remember to store this key in a password manager.

# Enable auto-lock on an existing Swarm
$ docker swarm update --autolock=true

# Disable auto-lock
$ docker swarm update --autolock=false
```

### Using Auto Lock

```bash
# After Docker restarts on a manager:
$ sudo systemctl restart docker

# Try any Swarm command:
$ docker node ls
# Error response from daemon: Swarm is encrypted and needs
# to be unlocked before it can be used.

# Unlock the Swarm:
$ docker swarm unlock
# Please enter unlock key: SWMKEY-1-WkRhReFlKxiLsJQmzruH3gYfYPNOKz9pSah1o26ic1o

# Now Swarm commands work again
$ docker node ls
# ID        HOSTNAME    STATUS    MANAGER STATUS
# abc123    manager-1   Ready     Leader
```

### Retrieve and Rotate the Unlock Key

```bash
# View the current unlock key
$ docker swarm unlock-key
# SWMKEY-1-WkRhReFlKxiLsJQmzruH3gYfYPNOKz9pSah1o26ic1o

# Rotate the unlock key (generates a new one)
$ docker swarm unlock-key --rotate
# Successfully rotated manager unlock key.
# To unlock a swarm manager after it restarts, run the
# `docker swarm unlock` command and provide the following key:
#     SWMKEY-1-NewKeyHere...

# ⚠️  Store the new key securely — the old key no longer works
```

---

## 11.41 Swarm Update Parallelism

By default, Swarm updates one task at a time during rolling updates. You can control how many tasks are updated simultaneously and the delay between batches.

```bash
# Update 3 tasks at a time with 10-second delay between batches
$ docker service update \
    --update-parallelism 3 \
    --update-delay 10s \
    --image nginx:1.26 web

# --update-parallelism: number of tasks updated simultaneously
# --update-delay: wait time between updating batches
# Default parallelism: 1 (one at a time)
# Default delay: 0s
```

### Update Order

```bash
# start-first: start new task before stopping old one (less downtime)
$ docker service update --update-order start-first --image nginx:1.26 web

# stop-first: stop old task before starting new one (default)
$ docker service update --update-order stop-first --image nginx:1.26 web
```

### In Compose/Stack YAML

```yaml
services:
  web:
    image: nginx:1.26
    deploy:
      replicas: 10
      update_config:
        parallelism: 3
        delay: 10s
        order: start-first
        failure_action: rollback
      rollback_config:
        parallelism: 2
        delay: 5s
        order: stop-first
```

```
┌──────────────────────┬──────────────────────────────────────┐
│ Option               │ Description                          │
├──────────────────────┼──────────────────────────────────────┤
│ parallelism          │ Tasks updated at once (0 = all)      │
│ delay                │ Wait between batches                 │
│ order                │ start-first or stop-first            │
│ failure_action       │ pause, continue, or rollback         │
│ monitor              │ Time to watch for failure after      │
│                      │ update (e.g., 5s)                    │
│ max_failure_ratio    │ Fraction of tasks that can fail      │
│                      │ before the update is paused          │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 11.42 Swarm Node Labels and Placement Constraints

Node labels let you tag nodes with metadata (e.g., `disk=ssd`, `zone=us-east-1a`). Placement constraints use these labels to control where services run.

### Adding Labels to Nodes

```bash
# Add a label to a node
$ docker node update --label-add disk=ssd worker-1
$ docker node update --label-add zone=us-east-1a worker-1
$ docker node update --label-add zone=us-east-1b worker-2
$ docker node update --label-add env=production worker-3

# View labels on a node
$ docker node inspect --format '{{.Spec.Labels}}' worker-1
# map[disk:ssd zone:us-east-1a]

# Remove a label
$ docker node update --label-rm disk worker-1
```

### Placement Constraints

Constraints restrict which nodes a service can run on.

```bash
# Run only on worker nodes (not managers)
$ docker service create --name web \
    --constraint 'node.role==worker' \
    --replicas 3 nginx

# Run only on nodes with SSD storage
$ docker service create --name db \
    --constraint 'node.labels.disk==ssd' \
    --replicas 1 postgres

# Run only on a specific node
$ docker service create --name monitoring \
    --constraint 'node.hostname==manager-1' \
    --mode global prometheus

# Multiple constraints (AND logic — all must match)
$ docker service create --name api \
    --constraint 'node.role==worker' \
    --constraint 'node.labels.zone==us-east-1a' \
    --replicas 2 myapi:1.0

# Exclude a node (not-equal)
$ docker service create --name web \
    --constraint 'node.hostname!=manager-1' \
    --replicas 3 nginx
```

### Built-in Constraint Keys

```
┌──────────────────────┬──────────────────────────────────────┐
│ Key                  │ Description                          │
├──────────────────────┼──────────────────────────────────────┤
│ node.id              │ Node ID                              │
│ node.hostname        │ Node hostname                        │
│ node.role            │ manager or worker                    │
│ node.platform.os     │ linux or windows                     │
│ node.platform.arch   │ x86_64, aarch64, etc.                │
│ node.labels.<key>    │ Custom labels set by admin           │
│ engine.labels.<key>  │ Labels from Docker Engine config     │
└──────────────────────┴──────────────────────────────────────┘
```

### Placement Preferences (Spread)

Placement preferences distribute tasks evenly across a label value. Unlike constraints (which filter), preferences spread tasks.

```bash
# Spread tasks evenly across availability zones
$ docker service create --name web \
    --replicas 6 \
    --placement-pref 'spread=node.labels.zone' \
    nginx

# If you have 3 zones with 2 nodes each:
#   zone=us-east-1a: 2 tasks
#   zone=us-east-1b: 2 tasks
#   zone=us-east-1c: 2 tasks
```

### In Compose/Stack YAML

```yaml
services:
  web:
    image: nginx
    deploy:
      replicas: 6
      placement:
        constraints:
          - node.role == worker
          - node.labels.env == production
        preferences:
          - spread: node.labels.zone
```

### Real-World Example

```
┌─────────────────────────────────────────────────────────────┐
│              PLACEMENT STRATEGY                              │
│                                                              │
│  Scenario: 3 zones, 2 workers per zone                     │
│                                                              │
│  Zone A              Zone B              Zone C             │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐       │
│  │worker-1  │       │worker-3  │       │worker-5  │       │
│  │zone=a    │       │zone=b    │       │zone=c    │       │
│  │disk=ssd  │       │disk=hdd  │       │disk=ssd  │       │
│  └──────────┘       └──────────┘       └──────────┘       │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐       │
│  │worker-2  │       │worker-4  │       │worker-6  │       │
│  │zone=a    │       │zone=b    │       │zone=c    │       │
│  │disk=hdd  │       │disk=ssd  │       │disk=hdd  │       │
│  └──────────┘       └──────────┘       └──────────┘       │
│                                                              │
│  Service: database                                          │
│    Constraint: node.labels.disk==ssd                        │
│    Preference: spread=node.labels.zone                      │
│    Replicas: 3                                              │
│                                                              │
│  Result:                                                    │
│    worker-1 (zone=a, ssd) → 1 task                         │
│    worker-4 (zone=b, ssd) → 1 task                         │
│    worker-5 (zone=c, ssd) → 1 task                         │
│    Evenly spread across zones, only on SSD nodes            │
└─────────────────────────────────────────────────────────────┘
```

---

## 11.43 Swarm Security: mTLS, Join Token Rotation, and CA Management

Docker Swarm encrypts all control plane traffic with mutual TLS (mTLS)
by default. Understanding how to manage certificates and tokens is
essential for production security.

### Mutual TLS (mTLS) — Automatic Encryption

```
# When you run docker swarm init, Swarm automatically:
#   1. Creates a self-signed Certificate Authority (CA)
#   2. Generates a TLS certificate for the manager node
#   3. Signs the certificate with the CA
#   4. Configures all node-to-node communication to use mTLS
#
# Every node that joins the swarm:
#   - Receives a TLS certificate signed by the swarm CA
#   - Uses it to authenticate and encrypt all communication
#   - Certificates are rotated automatically (default: 90 days)
#
# You do NOT need to configure TLS manually — Swarm handles it.
```

### Viewing and Rotating the CA Certificate

```bash
# View current CA certificate details
$ docker swarm ca
# Shows the PEM-encoded CA certificate

# View certificate expiry and rotation settings
$ docker info | grep -A 5 "Swarm"
# CA Configuration:
#   Expiry Duration: 3 months
#   Force Rotate: 0

# Rotate the CA certificate (generates a new CA)
$ docker swarm ca --rotate
# All node certificates are re-signed with the new CA
# Existing nodes continue to work — rotation is seamless

# Set a custom certificate rotation interval
$ docker swarm update --cert-expiry 720h
# 720h = 30 days (default is 2160h = 90 days)
# Shorter intervals are more secure but increase overhead
```

### Join Token Rotation

```bash
# Join tokens control which nodes can join the swarm.
# If a token is compromised, an attacker could add rogue nodes.

# View current join tokens
$ docker swarm join-token worker
# To add a worker: docker swarm join --token SWMTKN-1-abc... 192.168.1.1:2377

$ docker swarm join-token manager
# To add a manager: docker swarm join --token SWMTKN-1-xyz... 192.168.1.1:2377

# Rotate the worker join token (invalidates the old one)
$ docker swarm join-token --rotate worker
# New token generated — old token no longer works
# Existing nodes are NOT affected (they're already joined)

# Rotate the manager join token
$ docker swarm join-token --rotate manager

# Best practice: Rotate tokens after:
#   - A team member leaves the organization
#   - A token may have been exposed in logs or chat
#   - Periodically (e.g., monthly) as part of security hygiene
```

### Swarm Security Summary

```
┌──────────────────────┬──────────────────────────────────────────┐
│ Feature              │ Purpose                                  │
├──────────────────────┼──────────────────────────────────────────┤
│ mTLS (automatic)     │ Encrypts all node-to-node communication │
│ CA rotation          │ Refreshes the root certificate authority │
│ Cert expiry config   │ Controls how often node certs renew     │
│ Join token rotation  │ Invalidates old tokens to prevent       │
│                      │ unauthorized nodes from joining          │
│ Autolock             │ Encrypts Raft logs on disk (see 11.40)  │
│ Overlay encryption   │ Encrypts data plane traffic (--opt      │
│                      │ encrypted on overlay network creation)   │
└──────────────────────┴──────────────────────────────────────────┘
```

---

## Module 11 Summary

- Standalone Docker is fine for dev/smoke tests; **QA/Stage/Prod** needs orchestration
- **Container orchestration** provides scheduling, desired state, self-healing, scaling, service discovery, and load balancing
- **Docker Swarm** is Docker's built-in orchestration tool — no extra installation
- **Cluster** = group of machines (nodes) working together
- **Manager nodes** control the cluster; **worker nodes** run containers
- Among managers: one **Leader**, others are **Reachable** (backup leaders)
- **Service** defines desired state (image, replicas, ports); **tasks** are individual containers
- REPLICAS `3/3` = all healthy; `1/3` = two missing, Swarm recovering
- `docker swarm init` creates a swarm; `docker swarm join` adds workers
- `docker service create --replicas N` creates N containers distributed across nodes
- `docker service scale web=5` scales up/down — Swarm handles placement
- **Self-healing**: if a container crashes, Swarm recreates it automatically
- **Rolling updates**: `docker service update --image` replaces containers gradually
- **Rollback**: `docker service update --rollback` reverts to previous version
- **Replicated mode** = exact replica count; **Global mode** = 1 per node (for agents)
- **Drain** prevents tasks on a node — used for managers or maintenance
- **Ingress routing mesh** makes published ports available on every node with round-robin
- **Stacks** deploy services declaratively from compose YAML files
- **Docker Config** injects configuration files into containers at runtime
- **Docker Config** solves the problem of volumes not working well in Swarm (containers land on any node)
- **Health checks** verify app health inside containers; Swarm replaces unhealthy tasks
- `start_period` gives slow-starting apps time to initialize before health checks begin
- Debug health failures with `docker service ps` and `docker inspect`
- **Auto-lock** encrypts Swarm keys at rest — requires unlock key after daemon restart (`docker swarm unlock`)
- **Update parallelism** controls how many tasks update simultaneously (`--update-parallelism N`)
- **Update order**: `start-first` (less downtime) or `stop-first` (default)
- **Node labels** tag nodes with metadata (`docker node update --label-add key=value`)
- **Placement constraints** filter which nodes a service runs on (`--constraint 'node.labels.disk==ssd'`)
- **Placement preferences** spread tasks evenly across a label (`--placement-pref 'spread=node.labels.zone'`)
- **Mental model**: declare state → schedule → create → maintain → health check → load balance → update/rollback → inject config

---

**Previous Module: [Module 10 - Advanced Topics](module-10-advanced.md)**

**Next Module: [Module 12 - Docker Image Optimization](module-12-optimization.md)**
