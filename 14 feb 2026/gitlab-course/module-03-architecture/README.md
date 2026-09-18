# Module 03 — GitLab Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        GitLab Server                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Nginx   │  │  Puma    │  │ Sidekiq  │  │  Gitaly  │   │
│  │ (Proxy)  │  │ (Rails)  │  │ (Workers)│  │ (Git RPC)│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│  ┌────▼──────────────▼──────────────▼──────────────▼─────┐  │
│  │                    Internal Bus                        │  │
│  └────┬──────────────┬──────────────┬──────────────┬─────┘  │
│       │              │              │              │         │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  │
│  │PostgreSQL│  │  Redis   │  │  Object  │  │Container │  │
│  │(Database)│  │ (Cache)  │  │ Storage  │  │ Registry │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
         │
         │  ┌──────────┐  ┌──────────┐  ┌──────────┐
         └──│ Runner 1 │  │ Runner 2 │  │ Runner N │
            │ (CI/CD)  │  │ (CI/CD)  │  │ (CI/CD)  │
            └──────────┘  └──────────┘  └──────────┘
```

## Core Components

### Nginx

- Reverse proxy and static file server
- Terminates SSL/TLS
- Routes requests to Puma (web) or Workhorse (uploads/downloads)
- Listens on ports 80/443

### GitLab Workhorse

- Go-based smart reverse proxy
- Handles large HTTP requests (file uploads, Git over HTTP)
- Offloads long-running requests from Puma
- Manages artifact uploads/downloads

```
Client ──▶ Nginx ──▶ Workhorse ──▶ Puma (Rails)
                         │
                         ├──▶ Gitaly (Git operations)
                         └──▶ Object Storage (uploads)
```

### Puma (Application Server)

- Ruby on Rails application server (replaced Unicorn)
- Handles API requests, web UI, webhooks
- Multi-threaded with worker processes
- Default: 4 workers, 4 threads each

### Sidekiq (Background Jobs)

- Processes asynchronous tasks:
  - Email delivery
  - Repository cleanup
  - CI/CD pipeline processing
  - Webhook delivery
  - Import/export operations
- Uses Redis as job queue

### Gitaly

- Go service for Git repository access
- All Git operations go through Gitaly (no direct disk access)
- Supports clustering (Praefect) for HA
- Communicates via gRPC

```
Puma/Workhorse ──gRPC──▶ Gitaly ──▶ Git repositories on disk
                              │
                         /var/opt/gitlab/git-data/repositories/
                         ├── @hashed/
                         │   ├── ab/cd/abcd1234.git
                         │   └── ef/gh/efgh5678.git
                         └── @snippets/
```

### PostgreSQL

- Primary data store for:
  - Users, groups, projects
  - Issues, merge requests, comments
  - CI/CD pipeline metadata
  - Application settings
- Bundled with Omnibus (can use external)

### Redis

- In-memory data store for:
  - Sidekiq job queue
  - Session data
  - Caching (Rails cache, repository cache)
  - Real-time features (Action Cable)

### Object Storage

- Stores binary data:
  - CI/CD artifacts
  - LFS objects
  - Uploads (avatars, attachments)
  - Container registry layers
  - Packages
- Supports: local disk, S3, GCS, Azure Blob

## Request Flow

### Web Request (View Project)

```
1. Browser → Nginx (port 443)
2. Nginx → Workhorse
3. Workhorse → Puma (Rails)
4. Puma:
   ├── Queries PostgreSQL (project data)
   ├── Queries Redis (cached data)
   ├── Calls Gitaly (repository info)
   └── Returns HTML response
5. Response flows back: Puma → Workhorse → Nginx → Browser
```

### Git Push

```
1. git push → SSH (port 22) or HTTPS (port 443)
2. GitLab Shell (SSH) or Workhorse (HTTPS)
3. Authentication check (PostgreSQL)
4. Gitaly receives objects
5. Gitaly writes to repository on disk
6. Post-receive hook triggers:
   ├── Sidekiq: Process CI/CD pipeline
   ├── Sidekiq: Send webhooks
   ├── Sidekiq: Update merge request
   └── Redis: Invalidate caches
```

### CI/CD Pipeline Execution

```
1. Push event triggers pipeline
2. Sidekiq creates pipeline record (PostgreSQL)
3. Pipeline jobs enter queue (Redis)
4. Runner polls for jobs (HTTP API)
5. Runner receives job:
   ├── Clones repository (via Gitaly)
   ├── Executes job steps
   ├── Uploads artifacts (via Workhorse → Object Storage)
   └── Reports status (HTTP API → PostgreSQL)
6. Pipeline status updates in UI (Action Cable via Redis)
```

## Directory Structure (Omnibus)

```
/etc/gitlab/
├── gitlab.rb                    # Main configuration
├── gitlab-secrets.json          # Encryption keys
└── ssl/                         # SSL certificates

/var/opt/gitlab/
├── git-data/                    # Git repositories
│   └── repositories/
│       └── @hashed/             # Hashed storage
├── gitlab-rails/
│   ├── shared/
│   │   ├── artifacts/           # CI/CD artifacts
│   │   ├── lfs-objects/         # Git LFS
│   │   ├── packages/            # Package registry
│   │   └── uploads/             # User uploads
│   └── etc/
├── postgresql/
│   └── data/                    # Database files
├── redis/
│   └── dump.rdb                 # Redis snapshot
├── nginx/
│   └── conf/                    # Nginx configs
├── gitaly/                      # Gitaly data
├── gitlab-workhorse/
└── backups/                     # Backup files

/var/log/gitlab/
├── nginx/
├── puma/
├── sidekiq/
├── gitaly/
├── postgresql/
├── redis/
└── gitlab-workhorse/
```

## Scaling Architecture

### Single Server (Small: up to 1,000 users)

All components on one machine.

### Horizontal Scaling (Medium: 1,000-10,000 users)

```
┌──────────┐     ┌──────────┐
│ Load     │────▶│ GitLab 1 │──┐
│ Balancer │────▶│ GitLab 2 │──┤
└──────────┘     └──────────┘  │
                               │
                    ┌──────────▼──────────┐
                    │ Shared Services     │
                    │ ├── PostgreSQL (HA) │
                    │ ├── Redis Sentinel  │
                    │ ├── Gitaly Cluster  │
                    │ └── Object Storage  │
                    └─────────────────────┘
```

### Reference Architecture (Large: 10,000+ users)

```
Load Balancer
├── GitLab Rails (multiple nodes)
├── Sidekiq (dedicated nodes)
├── Gitaly Cluster (Praefect + Gitaly nodes)
├── PostgreSQL (Patroni HA cluster)
├── Redis (Sentinel cluster)
├── Object Storage (S3/GCS)
└── Runners (autoscaling fleet)
```

## Gitaly Cluster (Praefect)

For repository HA and redundancy:

```
                    ┌──────────┐
                    │ Praefect │  (Router/coordinator)
                    │ (Go)     │
                    └────┬─────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
       ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
       │ Gitaly  │  │ Gitaly  │  │ Gitaly  │
       │ Node 1  │  │ Node 2  │  │ Node 3  │
       │(primary)│  │(replica)│  │(replica)│
       └─────────┘  └─────────┘  └─────────┘

- Writes go to primary, replicated to secondaries
- Reads can be served by any node
- Automatic failover if primary goes down
- Requires PostgreSQL for Praefect metadata
```
