# Module 21: Docker Enterprise — UCP, DTR, RBAC

---

## 21.1 What is Docker Enterprise?

Docker Enterprise (now Mirantis Kubernetes Engine / Mirantis Secure Registry) was Docker's commercial platform for managing containerized applications at scale.

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER ENTERPRISE COMPONENTS                    │
│                                                              │
│  Docker Enterprise Engine                                   │
│    Commercial Docker Engine with support and certifications │
│    Same CLI as Docker CE, with enterprise features          │
│                                                              │
│  Universal Control Plane (UCP)                              │
│    Web-based management UI for Docker clusters              │
│    Manages both Swarm and Kubernetes workloads              │
│    RBAC, user management, deployment policies               │
│                                                              │
│  Docker Trusted Registry (DTR)                              │
│    Private image registry with security scanning            │
│    Image signing, promotion policies                        │
│    Integrates with UCP for access control                   │
│                                                              │
│  ⚠️  Note: Docker Enterprise was acquired by Mirantis      │
│  in 2019. UCP → Mirantis Kubernetes Engine (MKE)           │
│  DTR → Mirantis Secure Registry (MSR)                      │
│  The DCA exam still references the Docker Enterprise names  │
└─────────────────────────────────────────────────────────────┘
```

---

## 21.2 Docker Enterprise Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER ENTERPRISE ARCHITECTURE                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  UCP (Universal Control Plane)                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │ Web UI     │  │ REST API   │  │ CLI (bundle)│    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  │                                                      │   │
│  │  ┌────────────────────────────────────────────┐     │   │
│  │  │  Orchestration: Swarm + Kubernetes          │     │   │
│  │  │  RBAC Engine                                │     │   │
│  │  │  Certificate Authority                      │     │   │
│  │  └────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┼──────────────────────────────┐    │
│  │  Docker EE Nodes     │                              │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │    │
│  │  │Manager 1│  │Manager 2│  │Manager 3│            │    │
│  │  └─────────┘  └─────────┘  └─────────┘            │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │    │
│  │  │Worker 1 │  │Worker 2 │  │Worker 3 │            │    │
│  │  └─────────┘  └─────────┘  └─────────┘            │    │
│  └─────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┼──────────────────────────────┐    │
│  │  DTR (Docker Trusted Registry)                      │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐   │    │
│  │  │ DTR Node 1 │  │ DTR Node 2 │  │ DTR Node 3 │   │    │
│  │  │ (replica)  │  │ (replica)  │  │ (replica)  │   │    │
│  │  └────────────┘  └────────────┘  └────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 21.3 Universal Control Plane (UCP)

### What UCP Provides

```
┌─────────────────────────────────────────────────────────────┐
│              UCP FEATURES                                    │
│                                                              │
│  Cluster Management:                                        │
│    • Web UI for managing Swarm and Kubernetes               │
│    • Add/remove nodes                                       │
│    • View cluster health and resource usage                 │
│                                                              │
│  Application Deployment:                                    │
│    • Deploy Swarm services and stacks                       │
│    • Deploy Kubernetes pods and deployments                 │
│    • Rolling updates and rollbacks                          │
│                                                              │
│  Security:                                                  │
│    • Role-Based Access Control (RBAC)                       │
│    • LDAP/AD integration                                    │
│    • Client certificate bundles                             │
│    • Image signing enforcement                              │
│                                                              │
│  Monitoring:                                                │
│    • Container logs and metrics                             │
│    • Node health monitoring                                 │
│    • Resource utilization dashboards                        │
└─────────────────────────────────────────────────────────────┘
```

### Installing UCP

```bash
# Prerequisites:
#   Docker Enterprise Engine installed on all nodes
#   Manager node with at least 8GB RAM, 6GB disk

# Install UCP on the first manager
$ docker container run --rm -it --name ucp \
    -v /var/run/docker.sock:/var/run/docker.sock \
    docker/ucp:3.2.13 install \
    --host-address 192.168.1.10 \
    --interactive

# Prompts:
#   Admin username: admin
#   Admin password: ********
#   Additional aliases: (optional)

# Output:
# INFO[0000] Verifying your system is compatible with UCP
# INFO[0010] Pulling required images
# INFO[0120] UCP instance is up and running
# INFO[0120] Access your UCP console at https://192.168.1.10

# Access the web UI at https://<manager-ip>
# Login with admin credentials
```

### Adding Nodes to UCP

```bash
# From UCP web UI: Admin → Nodes → Add Node
# Or from CLI:

# Get the join token
$ docker swarm join-token worker
# docker swarm join --token SWMTKN-1-abc123... 192.168.1.10:2377

# On the new node:
$ docker swarm join --token SWMTKN-1-abc123... 192.168.1.10:2377

# The node appears in UCP automatically
```

---

## 21.4 UCP Client Bundle

The client bundle allows you to manage UCP from your local Docker CLI instead of the web UI.

```bash
# Download the client bundle from UCP:
# UCP Web UI → User Profile → Client Bundles → Generate Client Bundle

# Or via API:
$ AUTHTOKEN=$(curl -sk -d '{"username":"admin","password":"pass"}' \
    https://ucp-host/auth/login | jq -r .auth_token)

$ curl -sk -H "Authorization: Bearer $AUTHTOKEN" \
    https://ucp-host/api/clientbundle -o bundle.zip

# Extract the bundle
$ unzip bundle.zip -d ucp-bundle
$ cd ucp-bundle

# Source the environment
$ eval "$(<env.sh)"

# Now your Docker CLI talks to UCP
$ docker node ls
# Shows all nodes in the UCP cluster

$ docker service ls
# Shows all services managed by UCP

# The bundle contains:
#   ca.pem          → UCP CA certificate
#   cert.pem        → Client certificate
#   key.pem         → Client private key
#   cert.pub        → Client public key
#   env.sh          → Environment variables (DOCKER_HOST, DOCKER_TLS_VERIFY, etc.)
#   kube.yml        → Kubernetes config (for kubectl)
```

---

## 21.5 Docker Trusted Registry (DTR)

### What DTR Provides

```
┌─────────────────────────────────────────────────────────────┐
│              DTR FEATURES                                    │
│                                                              │
│  Image Storage:                                             │
│    • Private image registry                                 │
│    • Image replication across DTR replicas                  │
│    • Storage backends: local, S3, Azure Blob, GCS          │
│                                                              │
│  Security:                                                  │
│    • Image vulnerability scanning                           │
│    • Image signing and verification                         │
│    • Immutable tags (prevent overwriting)                   │
│    • Image promotion policies                               │
│                                                              │
│  Access Control:                                            │
│    • Per-repository permissions                             │
│    • Team-based access                                      │
│    • Integrates with UCP RBAC                               │
│                                                              │
│  High Availability:                                         │
│    • Multiple DTR replicas                                  │
│    • Shared storage backend                                 │
│    • Automatic failover                                     │
└─────────────────────────────────────────────────────────────┘
```

### Installing DTR

```bash
# DTR must be installed on a UCP worker node (not manager)
# Prerequisites: UCP already running

$ docker run -it --rm \
    docker/dtr:2.8.8 install \
    --ucp-node worker-1 \
    --ucp-url https://192.168.1.10 \
    --ucp-username admin \
    --ucp-password ********

# Output:
# INFO[0000] Validating UCP cert
# INFO[0010] Pulling required images
# INFO[0120] DTR is running at https://worker-1

# Access DTR web UI at https://<worker-ip>
```

### Using DTR

```bash
# Login to DTR
$ docker login dtr.example.com
# Username: admin
# Password: ********

# Tag and push an image
$ docker tag myapp:1.0 dtr.example.com/myorg/myapp:1.0
$ docker push dtr.example.com/myorg/myapp:1.0

# Pull an image
$ docker pull dtr.example.com/myorg/myapp:1.0

# DTR web UI shows:
#   Repository: myorg/myapp
#   Tags: 1.0
#   Vulnerability scan results
#   Image layers and size
```

### DTR Image Scanning

```bash
# Enable scanning in DTR:
# DTR Web UI → System → Security → Enable Scanning

# Scan results show:
#   Critical: 0
#   Major: 2
#   Minor: 5
#   Components with vulnerabilities listed
#   Fixed versions available

# Create a promotion policy:
# DTR Web UI → Repository → Policies → New Promotion Policy
#   Source: dev/myapp
#   Target: prod/myapp
#   Criteria: No critical vulnerabilities
#   Auto-promote when criteria met
```

---

## 21.6 Role-Based Access Control (RBAC)

UCP RBAC controls who can do what on which resources.

### RBAC Components

```
┌─────────────────────────────────────────────────────────────┐
│              RBAC MODEL                                      │
│                                                              │
│  Subject (WHO)                                              │
│    • User: individual account                               │
│    • Team: group of users                                   │
│    • Organization: group of teams                           │
│                                                              │
│  Role (WHAT they can do)                                    │
│    • None: no access                                        │
│    • View Only: read-only access                            │
│    • Restricted Control: operate but not admin              │
│    • Scheduler: schedule workloads                          │
│    • Full Control: complete access                          │
│                                                              │
│  Resource Set (WHERE — which resources)                     │
│    • Collection: logical grouping of resources              │
│    • /: root collection (everything)                        │
│    • /production: production resources                      │
│    • /staging: staging resources                            │
│    • /shared: shared resources                              │
│                                                              │
│  Grant = Subject + Role + Resource Set                      │
│  "Team DevOps has Full Control on /production"              │
└─────────────────────────────────────────────────────────────┘
```

### Built-in Roles

```
┌──────────────────────┬──────────────────────────────────────┐
│ Role                 │ Permissions                          │
├──────────────────────┼──────────────────────────────────────┤
│ None                 │ No access to resources               │
│ View Only            │ View containers, services, nodes     │
│                      │ Cannot create, modify, or delete     │
├──────────────────────┼──────────────────────────────────────┤
│ Restricted Control   │ View + create/manage containers      │
│                      │ Cannot change node settings           │
│                      │ Cannot access other users' resources │
├──────────────────────┼──────────────────────────────────────┤
│ Scheduler            │ Schedule containers on nodes          │
│                      │ Used for CI/CD service accounts      │
├──────────────────────┼──────────────────────────────────────┤
│ Full Control         │ Complete access to all operations    │
│                      │ Create, modify, delete anything      │
│                      │ Manage users and teams               │
└──────────────────────┴──────────────────────────────────────┘
```

### Creating Grants

```
┌─────────────────────────────────────────────────────────────┐
│              GRANT EXAMPLES                                  │
│                                                              │
│  Grant 1:                                                   │
│    Subject: Team "developers"                               │
│    Role: Restricted Control                                 │
│    Collection: /staging                                     │
│    Effect: Developers can deploy to staging                 │
│                                                              │
│  Grant 2:                                                   │
│    Subject: Team "ops"                                      │
│    Role: Full Control                                       │
│    Collection: /production                                  │
│    Effect: Ops team manages production                      │
│                                                              │
│  Grant 3:                                                   │
│    Subject: User "ci-bot"                                   │
│    Role: Scheduler                                          │
│    Collection: /staging                                     │
│    Effect: CI/CD can deploy to staging                      │
│                                                              │
│  Grant 4:                                                   │
│    Subject: Team "security"                                 │
│    Role: View Only                                          │
│    Collection: /                                            │
│    Effect: Security team can audit everything               │
└─────────────────────────────────────────────────────────────┘
```

### Creating via UCP Web UI

```
UCP Web UI → Access Control → Grants → Create Grant

Step 1: Select Subject
  → Organizations & Teams → Select team

Step 2: Select Role
  → Choose from built-in or custom roles

Step 3: Select Resource Set
  → Choose collection (e.g., /production)

→ Create
```

---

## 21.7 Collections — Organizing Resources

Collections are logical groupings of Docker resources (containers, services, volumes, networks, secrets).

```
┌─────────────────────────────────────────────────────────────┐
│              COLLECTION HIERARCHY                            │
│                                                              │
│  / (root)                                                   │
│  ├── /production                                            │
│  │   ├── /production/web-tier                               │
│  │   ├── /production/api-tier                               │
│  │   └── /production/data-tier                              │
│  ├── /staging                                               │
│  │   ├── /staging/web-tier                                  │
│  │   └── /staging/api-tier                                  │
│  ├── /development                                           │
│  └── /shared                                                │
│      └── /shared/monitoring                                 │
│                                                              │
│  Resources are placed in collections by labels:             │
│    com.docker.ucp.access.label = /production/web-tier       │
│                                                              │
│  Grants on parent collections cascade to children:          │
│    Full Control on /production → includes all sub-collections│
└─────────────────────────────────────────────────────────────┘
```

### Deploying to a Collection

```bash
# Deploy a service to a specific collection
$ docker service create \
    --name web \
    --label com.docker.ucp.access.label=/production/web-tier \
    --replicas 3 \
    nginx

# In Compose/Stack:
services:
  web:
    image: nginx
    labels:
      com.docker.ucp.access.label: "/production/web-tier"
```

---

## 21.8 LDAP / Active Directory Integration

UCP can authenticate users against an external LDAP or Active Directory server.

```
┌─────────────────────────────────────────────────────────────┐
│              LDAP INTEGRATION FLOW                           │
│                                                              │
│  User logs into UCP                                         │
│       │                                                      │
│       ▼                                                      │
│  UCP checks: Is this a local user?                          │
│       │ No                                                   │
│       ▼                                                      │
│  UCP queries LDAP/AD server                                 │
│       │                                                      │
│       ▼                                                      │
│  LDAP authenticates user                                    │
│       │                                                      │
│       ▼                                                      │
│  UCP maps LDAP groups → UCP teams                           │
│       │                                                      │
│       ▼                                                      │
│  User gets permissions based on team grants                 │
└─────────────────────────────────────────────────────────────┘
```

### Configuration

```
UCP Web UI → Admin Settings → Authentication & Authorization

LDAP Settings:
  LDAP Server URL:     ldap://ldap.example.com:389
  Reader DN:           cn=reader,dc=example,dc=com
  Reader Password:     ********

  User Search:
    Base DN:           ou=users,dc=example,dc=com
    Username Attribute: uid
    Full Name:         cn
    Filter:            (objectClass=person)

  Group Search (optional):
    Base DN:           ou=groups,dc=example,dc=com
    Group Attribute:   cn
    Member Attribute:  member
    Filter:            (objectClass=groupOfNames)

  Sync Interval:       1 hour

  → Enable LDAP
  → Test Connection
  → Save
```

### LDAP Group to UCP Team Mapping

```
┌──────────────────────┬──────────────────────────────────────┐
│ LDAP Group           │ UCP Team                             │
├──────────────────────┼──────────────────────────────────────┤
│ cn=developers        │ Organization: engineering            │
│                      │ Team: developers                     │
├──────────────────────┼──────────────────────────────────────┤
│ cn=ops               │ Organization: engineering            │
│                      │ Team: ops                            │
├──────────────────────┼──────────────────────────────────────┤
│ cn=security          │ Organization: security               │
│                      │ Team: auditors                       │
└──────────────────────┴──────────────────────────────────────┘

When a user in LDAP group "developers" logs in:
  → Automatically added to UCP team "developers"
  → Gets permissions from that team's grants
  → No manual user creation needed
```

---

## 21.9 Kubernetes in Docker Enterprise

UCP supports both Swarm and Kubernetes orchestration on the same cluster.

```bash
# Deploy with Kubernetes using the client bundle
$ cd ucp-bundle
$ eval "$(<env.sh)"

# Use kubectl (configured by the bundle)
$ kubectl get nodes
# NAME        STATUS   ROLES    AGE   VERSION
# manager-1   Ready    master   10d   v1.20.11
# worker-1    Ready    <none>   10d   v1.20.11
# worker-2    Ready    <none>   10d   v1.20.11

# Deploy a pod
$ kubectl run nginx --image=nginx --port=80

# Deploy from YAML
$ kubectl apply -f deployment.yaml

# UCP manages both Swarm services and Kubernetes workloads
# RBAC applies to both orchestrators
```

### Choosing Orchestrator per Node

```bash
# Set a node to run only Kubernetes workloads
# UCP Web UI → Nodes → Select Node → Details
#   Orchestrator: Kubernetes

# Set a node to run only Swarm workloads
#   Orchestrator: Swarm

# Set a node to run both (mixed mode)
#   Orchestrator: Mixed
```

---

## 21.10 DTR Access Control — Users, Organizations, Teams, and Repositories

DTR has its own access control layer for managing who can push, pull, and administer images.

### DTR Access Control Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│              DTR ACCESS CONTROL MODEL                        │
│                                                              │
│  Organization (e.g., "engineering")                         │
│    └── Team (e.g., "backend-devs")                          │
│          └── Members (individual users)                     │
│                                                              │
│  Repository (e.g., "engineering/api-server")                │
│    └── Permissions granted to teams                         │
│          Read-Only, Read-Write, or Admin                    │
│                                                              │
│  Flow:                                                      │
│    1. Admin creates an Organization                         │
│    2. Admin creates Teams within the Organization           │
│    3. Admin adds Users to Teams                             │
│    4. Admin creates Repositories under the Organization    │
│    5. Admin grants Teams access to Repositories            │
└─────────────────────────────────────────────────────────────┘
```

### Creating Organizations and Teams

```
DTR Web UI → Organizations → New Organization
  Name: engineering
  → Create

DTR Web UI → Organizations → engineering → Teams → New Team
  Name: backend-devs
  → Create

DTR Web UI → Organizations → engineering → Teams → backend-devs → Members
  → Add User → select users → Add
```

### Repository Permissions

```
┌──────────────────────┬──────────────────────────────────────┐
│ Permission Level     │ What It Allows                       │
├──────────────────────┼──────────────────────────────────────┤
│ Read-Only            │ Pull images only                     │
├──────────────────────┼──────────────────────────────────────┤
│ Read-Write           │ Pull and push images                 │
├──────────────────────┼──────────────────────────────────────┤
│ Admin                │ Pull, push, and manage repository    │
│                      │ settings (webhooks, scanning, etc.)  │
└──────────────────────┴──────────────────────────────────────┘
```

### Granting Team Access to a Repository

```
DTR Web UI → Repositories → engineering/api-server → Permissions
  → Add Team → backend-devs → Read-Write
  → Save
```

### Repository Visibility

```
┌──────────────────────┬──────────────────────────────────────┐
│ Visibility           │ Who Can See/Pull                     │
├──────────────────────┼──────────────────────────────────────┤
│ Public               │ Any authenticated DTR user           │
├──────────────────────┼──────────────────────────────────────┤
│ Private              │ Only users/teams with explicit       │
│                      │ permissions                          │
└──────────────────────┴──────────────────────────────────────┘
```

### Working with DTR from the CLI

```bash
# Login to DTR
$ docker login dtr.example.com
# Username: developer1
# Password: ********
# Login Succeeded

# Tag an image for DTR
$ docker tag myapp:1.0 dtr.example.com/engineering/api-server:1.0

# Push to DTR
$ docker push dtr.example.com/engineering/api-server:1.0

# Pull from DTR
$ docker pull dtr.example.com/engineering/api-server:1.0

# ⚠️  Push will fail if your user/team doesn't have
#     Read-Write or Admin permission on the repository
```

### Immutable Tags

Immutable tags prevent overwriting a published image tag — once pushed, the tag cannot be replaced.

```
DTR Web UI → Repositories → engineering/api-server → Settings
  → Immutability: ON

# Now pushing the same tag again fails:
$ docker push dtr.example.com/engineering/api-server:1.0
# Error: tag 1.0 is immutable and cannot be overwritten
```

---

## 21.11 Common Errors and Troubleshooting

### Error 1: UCP Web UI Not Accessible

```bash
# Check UCP containers
$ docker ps --filter name=ucp
# All UCP containers should be running

# Check UCP logs
$ docker logs ucp-controller

# Common fix: Restart UCP
$ docker container run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    docker/ucp:3.2.13 restart
```

### Error 2: DTR Push Fails with "unauthorized"

```bash
# CAUSE: Not logged in or insufficient permissions
# Fix: Login to DTR
$ docker login dtr.example.com

# Check repository permissions in DTR web UI
# Ensure your user/team has push access to the repository
```

### Error 3: LDAP Users Can't Login

```bash
# Check LDAP connectivity from UCP
# UCP Web UI → Admin Settings → Authentication → Test Connection

# Common causes:
#   Wrong Base DN
#   Wrong username attribute (uid vs sAMAccountName)
#   Firewall blocking LDAP port (389 or 636)
#   Reader DN doesn't have search permissions
```

---

## 21.11 DTR Image Scanning

DTR includes a built-in vulnerability scanner that inspects OS packages,
libraries, and dependencies in container images.

### Enabling Image Scanning

```
# Enable scanning in DTR:
# DTR Web UI → System → Security → Enable Scanning → ON

# DTR pulls vulnerability data from the US National Vulnerability
# Database (NVD) by default. You can also upload a custom database
# file for air-gapped environments.

# After enabling, click "Sync Database" to download the latest
# vulnerability definitions.
```

> **Note:** Image scanning requires DTR v2.6 or later. Check your
> version under System → Settings.

### Running Scans

```
# Manual scan:
# DTR Web UI → Repositories → Select repo → Tags tab
# Click "Start a Scan" next to the tag you want to analyze

# Automatic scan on push:
# DTR Web UI → Repositories → Select repo → Settings
# Toggle "Scan on Push" → ON
# Every new tag pushed to this repository is scanned automatically
```

### Scan Modes

```
┌──────────────┬──────────────────────────────────────────────────┐
│ Scan Mode    │ Description                                      │
├──────────────┼──────────────────────────────────────────────────┤
│ Manual       │ Start each scan yourself via the UI or API       │
│ On Push      │ Scans run automatically when a new tag is pushed │
└──────────────┴──────────────────────────────────────────────────┘
```

> **Warning:** Enabling "On Push" scanning increases resource usage
> and may impact registry performance during peak push events.

### Scan Report Severity Levels

```
┌──────────┬──────────────────────────────────────────────────────┐
│ Severity │ Description                                          │
├──────────┼──────────────────────────────────────────────────────┤
│ Critical │ Highest impact — immediate remediation needed         │
│ Major    │ Significant risk — plan to upgrade/patch              │
│ Minor    │ Low risk — monitor and remediate as needed            │
└──────────┴──────────────────────────────────────────────────────┘
```

### Example: Vulnerable Dockerfile

```dockerfile
FROM alpine:3.10

ENV NODE_VERSION=8.9.4
ENV YARN_VERSION=1.3.2

RUN addgroup -g 1000 node \
 && adduser -u 1000 -G node -s /bin/sh node \
 && apk add --no-cache --virtual .build-deps \
      yarn curl gnupg tar

CMD ["node"]
```

```
# After scanning, DTR might report:
#   NODE_VERSION=8.9.4 → 3 Critical vulnerabilities (CVE-2019-xxxx)
#   YARN_VERSION=1.3.2 → 1 Major vulnerability
#   curl package → 2 Minor vulnerabilities
#
# The report shows:
#   - Affected component and version
#   - CVE identifier
#   - Fixed version (if available)
#   - Severity classification
#
# Action: Update to patched versions and rebuild the image
```

### Real-World Use Case

```
# CI/CD pipeline with DTR scanning:
#
# 1. Developer pushes code → CI builds Docker image
# 2. CI pushes image to DTR dev repository
# 3. DTR "Scan on Push" triggers automatic vulnerability scan
# 4. If Critical vulnerabilities found → pipeline fails, team notified
# 5. If scan passes → image is promoted to staging repository
# 6. QA tests run against staging
# 7. On approval → image promoted to production repository
```

---

## 21.12 DTR Image Promotions

Image promotion ensures the same Docker image artifact moves through
dev → test → staging → production without rebuilding.

### Why Promotion Matters

```
# WITHOUT promotion (traditional approach):
#
#   Dev: Build image v1.2.3 → test → pass
#   Test: Rebuild image v1.2.3 → test → pass
#   Staging: Rebuild image v1.2.3 → test → pass
#   Prod: Rebuild image v1.2.3 → deploy
#
# Problem: Each rebuild may pull different base image layers,
# updated OS packages, or newer dependency versions.
# The image in production is NOT the same one tested in dev.

# WITH DTR promotion:
#
#   Dev: Build image v1.2.3 → push to dev/myapp → test → pass
#   Test: Promote SAME image to test/myapp → test → pass
#   Staging: Promote SAME image to staging/myapp → test → pass
#   Prod: Promote SAME image to prod/myapp → deploy
#
# The image digest (sha256) is identical across all environments.
```

### Traditional vs Promotion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  TRADITIONAL PIPELINE (risky)                                   │
│                                                                 │
│  Dev ──build──► Test ──build──► Stage ──build──► Prod           │
│  (v1)          (v1?)           (v1??)          (v1???)          │
│                                                                 │
│  Each stage rebuilds — version drift risk at every step         │
├─────────────────────────────────────────────────────────────────┤
│  DTR PROMOTION PIPELINE (safe)                                  │
│                                                                 │
│  Dev ──build──► Test ──promote──► Stage ──promote──► Prod       │
│  (sha256:abc)  (sha256:abc)     (sha256:abc)      (sha256:abc) │
│                                                                 │
│  Same digest everywhere — guaranteed consistency                │
└─────────────────────────────────────────────────────────────────┘
```

### Configuring Promotion Policies

```
# DTR Web UI → Repositories → Select repo → Promotions tab
# Click "New Promotion Policy"

# Configuration options:
#
# ┌─────────────────┬──────────────────────────────────────────────┐
# │ Setting         │ Description                                  │
# ├─────────────────┼──────────────────────────────────────────────┤
# │ Source trigger   │ Tag name or digest that starts promotion    │
# │ Condition        │ Matching rule: equals, starts with, regex   │
# │ Target registry  │ Destination repository (same or different)  │
# └─────────────────┴──────────────────────────────────────────────┘

# Example: Promote all tags starting with "v1.2." from dev to test
#   Source: dev/myapp
#   Condition: Tag starts with "v1.2."
#   Target: test/myapp
#
# Any image pushed to dev/myapp with tag v1.2.x is automatically
# copied to test/myapp with the same tag.
```

### Promotion with Vulnerability Scanning

```
# Combine scanning with promotion for automated quality gates:
#
# 1. Enable "Scan on Push" for dev/myapp
# 2. Create promotion policy:
#      Source: dev/myapp
#      Criteria: No critical vulnerabilities
#      Target: prod/myapp
#
# Flow:
#   Push image → auto-scan → 0 critical vulns → auto-promote to prod
#   Push image → auto-scan → 2 critical vulns → promotion blocked
```

### Real-World Use Case

```
# E-commerce company with 4 environments:
#
# 1. Developer pushes myapp:v2.1.0 to dtr.company.com/dev/myapp
# 2. DTR scans the image automatically (Scan on Push)
# 3. Scan passes (0 critical, 1 minor) → promotion policy triggers
# 4. DTR copies image to dtr.company.com/qa/myapp:v2.1.0
# 5. QA team runs integration tests against qa/myapp:v2.1.0
# 6. QA approves → manual promotion to staging/myapp:v2.1.0
# 7. Load testing passes → promote to prod/myapp:v2.1.0
#
# At every stage, `docker inspect` shows the same image digest:
#   sha256:a1b2c3d4e5f6...
```

---

## 21.13 DTR Garbage Collection

When you delete an image tag in DTR, only the tag reference is removed.
The underlying layers remain on disk. Garbage collection (GC) reclaims
storage by deleting unreferenced layers.

### Why Garbage Collection Is Needed

```
# Image layers are shared across multiple images and tags.
# Example:
#
#   myapp:v1.0 uses layers: A, B, C, D
#   myapp:v2.0 uses layers: A, B, C, E
#
# If you delete tag v1.0:
#   - Tag "v1.0" is removed from the registry metadata
#   - Layers A, B, C are still referenced by v2.0 — kept
#   - Layer D is now unreferenced — candidate for GC
#   - Disk space is NOT freed until GC runs
```

### Configuring Garbage Collection

```
# DTR Web UI → System → Garbage Collection
# Choose a schedule:
#
# ┌─────────────────┬──────────────────────────────────────────────┐
# │ Schedule Option │ Description                                  │
# ├─────────────────┼──────────────────────────────────────────────┤
# │ Interval        │ Run GC at a recurring interval (e.g., daily) │
# │ Until done      │ Full scan — delete all unreferenced layers   │
# │ Fixed duration  │ Run GC for a specified number of minutes     │
# │ Never           │ Disable GC — disk usage grows indefinitely   │
# └─────────────────┴──────────────────────────────────────────────┘
```

### Garbage Collection Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  DTR GARBAGE COLLECTION PROCESS                                 │
│                                                                 │
│  Step 1: READ-ONLY MODE                                         │
│    DTR blocks image pushes and modifications                    │
│    Image pulls remain allowed                                   │
│                                                                 │
│  Step 2: MARKING                                                │
│    DTR scans all layers and identifies unreferenced ones        │
│    Layers still referenced by any tag are preserved             │
│                                                                 │
│  Step 3: DELETION                                               │
│    DTR deletes marked (unreferenced) layers                     │
│    Disk space is reclaimed                                      │
│                                                                 │
│  Step 4: NORMAL MODE                                            │
│    DTR resumes accepting pushes and modifications               │
└─────────────────────────────────────────────────────────────────┘
```

> **Warning:** Garbage collection is CPU- and I/O-intensive. Schedule
> it during off-peak hours (maintenance windows) to minimize impact
> on registry operations.

### Real-World Use Case

```
# CI/CD pipeline pushes 50+ images per day to DTR.
# After 6 months, DTR storage is at 85% capacity.
#
# Analysis:
#   - 12,000 image tags exist
#   - 8,000 are old dev/test tags no longer needed
#   - Deleting tags frees 0 bytes (layers still on disk)
#
# Solution:
#   1. Delete old tags via DTR UI or API
#   2. Schedule GC: System → Garbage Collection → "Until done"
#   3. Plan a maintenance window (GC blocks pushes)
#   4. After GC completes: storage drops from 85% to 40%
#   5. Set recurring GC: "Interval" → every Sunday at 2 AM
```

---

## Module 21 Summary

- Docker Enterprise consists of Docker EE Engine, UCP (management), and DTR (registry)
- Docker Enterprise was acquired by Mirantis — UCP is now MKE, DTR is now MSR
- **UCP** provides web UI, REST API, and CLI access for managing Docker clusters
- UCP supports both Swarm and Kubernetes orchestration on the same cluster
- **Client bundles** allow managing UCP from local Docker CLI and kubectl
- **DTR** is a private registry with vulnerability scanning, image signing, and promotion policies
- DTR runs on UCP worker nodes (not managers) and supports HA with multiple replicas
- **RBAC** controls access using Subjects (users/teams), Roles (permissions), and Resource Sets (collections)
- Built-in roles: None, View Only, Restricted Control, Scheduler, Full Control
- **Collections** organize resources hierarchically — grants on parent collections cascade to children
- Resources are placed in collections using the `com.docker.ucp.access.label` label
- **LDAP/AD integration** allows external authentication — LDAP groups map to UCP teams
- Users authenticated via LDAP get permissions from their team's grants automatically
- **DTR image scanning** detects vulnerabilities in OS packages, libraries, and dependencies
- Scan modes: Manual (on-demand) and On Push (automatic on every push)
- Scan reports classify findings as Critical, Major, or Minor severity
- **DTR image promotions** move the same image digest through dev → test → staging → prod without rebuilding
- Promotion policies trigger automatically based on tag patterns and scan results
- Combine scanning + promotion for automated quality gates (block promotion on critical vulns)
- **DTR garbage collection** reclaims disk space by deleting unreferenced layers
- Deleting a tag does NOT free disk space — GC must run to remove orphaned layers
- GC puts DTR in read-only mode (pushes blocked, pulls allowed) during execution
- Schedule GC during maintenance windows — it is CPU- and I/O-intensive
- **DTR access control**: Organizations → Teams → Members; Repositories grant Read-Only, Read-Write, or Admin to teams
- Repository visibility: Public (any authenticated user) or Private (explicit permissions only)
- **Immutable tags** in DTR prevent overwriting published images — once pushed, a tag cannot be replaced

---

**Previous Module: [Module 20 - Docker Security Deep Dive](module-20-security-deep-dive.md)**

**Next Module: [Module 22 - Disaster Recovery](module-22-disaster-recovery.md)**
