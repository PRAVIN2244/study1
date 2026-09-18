# Module 15: Docker Secrets in Swarm

---

## 15.1 The Problem — How Do You Pass Secrets to Containers?

Applications need secrets: database passwords, API keys, TLS certificates. Passing them insecurely creates risk.

```
┌─────────────────────────────────────────────────────────────┐
│              INSECURE SECRET METHODS                         │
│                                                              │
│  ❌ Baked into image (Dockerfile ENV or COPY .env)          │
│     Anyone with the image can extract the secret            │
│     docker history shows ENV values                         │
│     Secrets persist in image layers forever                 │
│                                                              │
│  ❌ Environment variables (-e flag)                         │
│     Visible in docker inspect output                        │
│     Visible in /proc/<pid>/environ inside container         │
│     Logged by many frameworks                               │
│     Visible in docker-compose.yml (checked into git)        │
│                                                              │
│  ❌ Volume-mounted files from host                          │
│     In Swarm, containers land on ANY node                   │
│     You'd need to copy secret files to EVERY node           │
│     Manual, error-prone, hard to rotate                     │
│                                                              │
│  ✅ Docker Secrets (Swarm)                                  │
│     Encrypted at rest and in transit                        │
│     Mounted as in-memory files inside containers            │
│     Only accessible to services that need them              │
│     Managed centrally by Swarm managers                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 15.2 What Are Docker Secrets?

Docker Secrets is a Swarm-mode feature that securely stores and distributes sensitive data to services.

```
┌─────────────────────────────────────────────────────────────┐
│              HOW DOCKER SECRETS WORK                         │
│                                                              │
│  1. Secret created → stored in Swarm's Raft log             │
│     (encrypted at rest on manager nodes)                    │
│                                                              │
│  2. Service granted access to secret                        │
│                                                              │
│  3. Swarm sends secret to worker node running the task      │
│     (encrypted in transit via mutual TLS)                   │
│                                                              │
│  4. Secret mounted as a file inside the container           │
│     at /run/secrets/<secret_name>                           │
│     (in-memory tmpfs — never written to disk on worker)     │
│                                                              │
│  5. When service is removed or secret revoked,              │
│     the file is unmounted from the container                │
│                                                              │
│  ⚠️  Requires Swarm mode (docker swarm init)               │
│  ⚠️  Only works with Swarm services, not docker run        │
└─────────────────────────────────────────────────────────────┘
```

---

## 15.3 Creating Secrets

### From a String (Command Line)

```bash
# Create a secret from a string
$ echo "MyS3cur3P@ssw0rd" | docker secret create db_password -

# Output:
# k9f2m3n4o5p6q7r8s9t0

# The "-" at the end means "read from stdin"
```

### From a File

```bash
# Create a file with the secret
$ echo "MyS3cur3P@ssw0rd" > password.txt

# Create secret from file
$ docker secret create db_password password.txt

# Output:
# a1b2c3d4e5f6g7h8i9j0

# Delete the file — secret is now stored in Swarm
$ rm password.txt
```

### From a Certificate File

```bash
# Store a TLS certificate as a secret
$ docker secret create site_cert server-cert.pem

# Store a TLS key as a secret
$ docker secret create site_key server-key.pem
```

---

## 15.4 Managing Secrets

```bash
# List all secrets
$ docker secret ls

# Output:
# ID                          NAME           CREATED          UPDATED
# a1b2c3d4e5f6g7h8i9j0       db_password    2 minutes ago    2 minutes ago
# k9f2m3n4o5p6q7r8s9t0       db_username    5 minutes ago    5 minutes ago

# Inspect a secret (metadata only — value is NEVER shown)
$ docker secret inspect db_password

# Output:
# [
#     {
#         "ID": "a1b2c3d4e5f6g7h8i9j0",
#         "Version": { "Index": 15 },
#         "CreatedAt": "2025-01-15T10:00:00Z",
#         "UpdatedAt": "2025-01-15T10:00:00Z",
#         "Spec": {
#             "Name": "db_password"
#         }
#     }
# ]

# ⚠️  Notice: The actual secret VALUE is NOT in the output
# Docker never exposes secret values through the API

# Remove a secret
$ docker secret rm db_password

# Output:
# db_password

# ⚠️  Cannot remove a secret that is in use by a service
# Error: secret 'db_password' is in use by the following services: web
```

---

## 15.5 Using Secrets in Services

### Create a Service with a Secret

```bash
# Create secrets first
$ echo "admin" | docker secret create db_user -
$ echo "S3cur3P@ss" | docker secret create db_pass -

# Create a service that uses the secrets
$ docker service create \
    --name mydb \
    --secret db_user \
    --secret db_pass \
    -e POSTGRES_USER_FILE=/run/secrets/db_user \
    -e POSTGRES_PASSWORD_FILE=/run/secrets/db_pass \
    postgres:16

# Secrets are mounted at /run/secrets/<secret_name>
```

### Verify Secrets Inside the Container

```bash
# Find the container
$ docker service ps mydb
# ID        NAME     NODE       STATE
# abc123    mydb.1   worker-1   Running

# Exec into the container (on the node where it runs)
$ docker exec -it mydb.1.abc123 sh

# List secrets
$ ls /run/secrets/
# db_user  db_pass

# Read a secret
$ cat /run/secrets/db_user
# admin

$ cat /run/secrets/db_pass
# S3cur3P@ss

# Check it's in-memory (tmpfs)
$ mount | grep secrets
# tmpfs on /run/secrets type tmpfs (ro,relatime)
# ✅ Read-only tmpfs — never touches disk
```

---

## 15.6 Secret Mount Options

### Custom Target Path

```bash
# Mount secret at a custom path inside the container
$ docker service create \
    --name web \
    --secret source=site_cert,target=/etc/nginx/ssl/cert.pem \
    --secret source=site_key,target=/etc/nginx/ssl/key.pem,mode=0400 \
    nginx

# source = secret name in Swarm
# target = file path inside container
# mode   = file permissions (default: 0444 = read-only for all)
```

### Permissions

```
┌──────────────────┬──────────────────────────────────────────┐
│ Option           │ Meaning                                  │
├──────────────────┼──────────────────────────────────────────┤
│ target           │ File path inside container               │
│                  │ Default: /run/secrets/<name>             │
├──────────────────┼──────────────────────────────────────────┤
│ uid              │ Owner user ID (default: 0 = root)        │
├──────────────────┼──────────────────────────────────────────┤
│ gid              │ Owner group ID (default: 0 = root)       │
├──────────────────┼──────────────────────────────────────────┤
│ mode             │ File permissions in octal                │
│                  │ Default: 0444 (read-only for everyone)   │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 15.7 Adding and Removing Secrets from Running Services

```bash
# Add a secret to an existing service
$ docker service update --secret-add new_secret myservice

# Remove a secret from a service
$ docker service update --secret-rm old_secret myservice

# ⚠️  Updating secrets causes service tasks to be restarted
# Swarm performs a rolling update to apply the change
```

---

## 15.8 Secrets in Docker Compose (Stack Deploy)

Secrets work with `docker stack deploy` using compose YAML files.

### Using Pre-Created Secrets (External)

```yaml
# docker-compose.yml
version: "3.8"

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER_FILE: /run/secrets/db_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_pass
    secrets:
      - db_user
      - db_pass
    deploy:
      replicas: 1

secrets:
  db_user:
    external: true    # Secret already exists in Swarm
  db_pass:
    external: true
```

```bash
# Create secrets first
$ echo "admin" | docker secret create db_user -
$ echo "S3cur3P@ss" | docker secret create db_pass -

# Deploy the stack
$ docker stack deploy -c docker-compose.yml myapp

# Verify
$ docker stack services myapp
$ docker service ps myapp_db
```

### Using File-Based Secrets (Created by Stack)

```yaml
# docker-compose.yml
version: "3.8"

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER_FILE: /run/secrets/db_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_pass
    secrets:
      - db_user
      - db_pass
    deploy:
      replicas: 1

  app:
    image: myapp:1.0
    secrets:
      - source: db_pass
        target: /app/config/db_password
        mode: 0400
    deploy:
      replicas: 3

secrets:
  db_user:
    file: ./secrets/db_user.txt     # Read from local file
  db_pass:
    file: ./secrets/db_pass.txt
```

```bash
# Create secret files
$ mkdir secrets
$ echo "admin" > secrets/db_user.txt
$ echo "S3cur3P@ss" > secrets/db_pass.txt

# Deploy
$ docker stack deploy -c docker-compose.yml myapp

# Stack creates the secrets automatically from the files
```

---

## 15.9 Real-World Example — Web App with Database Secrets

```yaml
# docker-compose.yml
version: "3.8"

services:
  web:
    image: myapp:2.0
    ports:
      - "8080:3000"
    secrets:
      - db_password
      - api_key
    environment:
      DB_HOST: db
      DB_USER: appuser
      DB_PASSWORD_FILE: /run/secrets/db_password
      API_KEY_FILE: /run/secrets/api_key
    deploy:
      replicas: 3
    depends_on:
      - db

  db:
    image: mysql:8.0
    secrets:
      - db_password
      - db_root_password
    environment:
      MYSQL_DATABASE: appdb
      MYSQL_USER: appuser
      MYSQL_PASSWORD_FILE: /run/secrets/db_password
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/db_root_password
    volumes:
      - db-data:/var/lib/mysql
    deploy:
      replicas: 1

volumes:
  db-data:

secrets:
  db_password:
    external: true
  db_root_password:
    external: true
  api_key:
    external: true
```

```bash
# Create all secrets
$ echo "AppP@ssw0rd" | docker secret create db_password -
$ echo "R00tP@ssw0rd" | docker secret create db_root_password -
$ echo "sk-abc123def456" | docker secret create api_key -

# Deploy
$ docker stack deploy -c docker-compose.yml production
```

---

## 15.10 Reading Secrets in Application Code

Applications read secrets from files, not environment variables.

### Node.js

```javascript
const fs = require('fs');

// Read secret from file
const dbPassword = fs.readFileSync('/run/secrets/db_password', 'utf8').trim();

const connection = mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: dbPassword
});
```

### Python

```python
import os

def read_secret(secret_name):
    secret_path = f'/run/secrets/{secret_name}'
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            return f.read().strip()
    # Fallback to environment variable
    return os.environ.get(secret_name.upper())

db_password = read_secret('db_password')
```

### The _FILE Convention

Many official Docker images (MySQL, PostgreSQL, MariaDB) support the `_FILE` suffix convention:

```
┌─────────────────────────────────────────────────────────────┐
│              THE _FILE CONVENTION                            │
│                                                              │
│  Instead of:                                                │
│    MYSQL_ROOT_PASSWORD=mysecret     ← value directly        │
│                                                              │
│  Use:                                                       │
│    MYSQL_ROOT_PASSWORD_FILE=/run/secrets/db_root_password   │
│                                                              │
│  The image's entrypoint script reads the file and sets      │
│  the variable internally. You never expose the value        │
│  in environment variables or docker inspect output.         │
│                                                              │
│  Images supporting _FILE:                                   │
│    ✅ mysql, mariadb, postgres                              │
│    ✅ mongo, redis (some versions)                          │
│    ❌ Most custom images (you implement it yourself)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 15.11 Secret Rotation

Secrets are immutable — you cannot update a secret's value. To rotate, create a new secret and update the service.

```bash
# Step 1: Create new secret with new value
$ echo "NewP@ssw0rd2025" | docker secret create db_password_v2 -

# Step 2: Update service to use new secret
$ docker service update \
    --secret-rm db_password \
    --secret-add source=db_password_v2,target=db_password \
    myapp_web

# target=db_password keeps the same filename inside the container
# Application doesn't need to change — same path, new value

# Step 3: Remove old secret (after all services are updated)
$ docker secret rm db_password
```

---

## 15.12 Secrets vs Configs — When to Use Which

```
┌──────────────────┬──────────────────────────────────────────┐
│ Feature          │ Secrets              │ Configs            │
├──────────────────┼──────────────────────┼────────────────────┤
│ Encryption       │ ✅ At rest + transit │ ❌ Not encrypted   │
│ Storage          │ Raft log (encrypted) │ Raft log (plain)   │
│ Mount type       │ tmpfs (in-memory)    │ Regular file       │
│ Default perms    │ 0444 (read-only)     │ 0444 (read-only)   │
│ Default path     │ /run/secrets/<name>  │ /<name>            │
│ Inspectable      │ ❌ Value hidden      │ ✅ Value visible   │
│ Max size         │ 500 KB               │ 500 KB             │
│ Use for          │ Passwords, keys,     │ Config files,      │
│                  │ tokens, certs        │ nginx.conf, etc.   │
└──────────────────┴──────────────────────┴────────────────────┘
```

---

## 15.13 Common Errors and Troubleshooting

### Error 1: "This node is not a swarm manager"

```bash
# Error: This node is not a swarm manager

# CAUSE: Secrets require Swarm mode
# Fix: Initialize Swarm
$ docker swarm init
```

### Error 2: "secret is in use"

```bash
# Error: Error response from daemon: secret 'db_password' is in use

# CAUSE: A service is using this secret
# Fix: Remove the secret from the service first
$ docker service update --secret-rm db_password myservice
$ docker secret rm db_password
```

### Error 3: Secret File Empty Inside Container

```bash
# Secret file exists but is empty

# CAUSE: Newline or encoding issue when creating secret
# Fix: Use printf instead of echo (avoids trailing newline)
$ printf "MyPassword" | docker secret create db_password -

# Or use echo -n
$ echo -n "MyPassword" | docker secret create db_password -
```

### Error 4: Application Can't Read Secret

```bash
# Permission denied reading /run/secrets/db_password

# CAUSE: Container runs as non-root user, secret owned by root
# Fix: Set uid/gid when mounting
$ docker service create \
    --secret source=db_password,target=/run/secrets/db_password,uid=1000,gid=1000 \
    myapp
```

---

## Module 15 Summary

- Docker Secrets securely stores and distributes sensitive data to Swarm services
- Secrets are encrypted at rest (Raft log) and in transit (mutual TLS between nodes)
- Secrets are mounted as in-memory files at `/run/secrets/<name>` — never written to disk on workers
- Create secrets from strings (`echo "value" | docker secret create name -`) or files (`docker secret create name file.txt`)
- `docker secret ls` lists secrets; `docker secret inspect` shows metadata but never the value
- Grant secrets to services with `--secret` flag or `secrets:` in compose YAML
- Use `_FILE` environment variable convention with official images (MySQL, PostgreSQL)
- Secrets are immutable — rotate by creating a new secret and updating the service
- In compose YAML, secrets can be `external: true` (pre-created) or `file:` (created by stack)
- Custom mount paths, permissions, and ownership via `source`, `target`, `mode`, `uid`, `gid`
- Secrets only work in Swarm mode — not with standalone `docker run`
- Use Secrets for passwords, keys, tokens, certs; use Configs for non-sensitive configuration files
- Max secret size is 500 KB
- Use `printf` or `echo -n` to avoid trailing newlines in secret values

---

**Previous Module: [Module 14 - Docker Content Trust](module-14-content-trust.md)**

**Next Module: [Module 16 - Linux Network Namespaces Deep Dive](module-16-network-namespaces.md)**
