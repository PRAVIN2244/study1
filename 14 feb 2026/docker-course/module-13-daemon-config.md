# Module 13: Docker Daemon Configuration Deep Dive

---

## 13.1 What is the Docker Daemon?

The Docker daemon (`dockerd`) is the background process that manages containers, images, networks, and volumes on a host.

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER DAEMON ARCHITECTURE                      │
│                                                              │
│  User types:  docker run nginx                              │
│       │                                                      │
│       ▼                                                      │
│  Docker Client (CLI)                                        │
│       │                                                      │
│       ▼  (REST API over Unix socket or TCP)                 │
│  Docker Daemon (dockerd)                                    │
│       │                                                      │
│       ├── containerd  → manages container lifecycle         │
│       ├── runc        → creates containers (OCI runtime)    │
│       ├── networking  → bridge, overlay, etc.               │
│       ├── storage     → overlay2, volumes                   │
│       └── image mgmt  → pull, build, push                  │
│                                                              │
│  Communication channel:                                     │
│    Local:  /var/run/docker.sock (Unix socket)               │
│    Remote: tcp://host:2376 (TCP with TLS)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 13.2 Docker Daemon Configuration File — daemon.json

The daemon reads its configuration from `/etc/docker/daemon.json`. This file controls storage, networking, logging, security, and more.

### Location

```bash
# Linux
/etc/docker/daemon.json

# macOS (Docker Desktop)
~/.docker/daemon.json

# Windows (Docker Desktop)
C:\ProgramData\docker\config\daemon.json
```

### Creating the File

```bash
# The file does NOT exist by default — you create it
$ sudo vi /etc/docker/daemon.json
```

### Complete daemon.json Reference

```json
{
  "data-root": "/var/lib/docker",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "dns": ["8.8.8.8", "8.8.4.4"],
  "default-address-pools": [
    { "base": "172.20.0.0/16", "size": 24 }
  ],
  "insecure-registries": ["myregistry.local:5000"],
  "registry-mirrors": ["https://mirror.gcr.io"],
  "live-restore": true,
  "debug": false,
  "tls": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert": "/etc/docker/certs/server-cert.pem",
  "tlskey": "/etc/docker/certs/server-key.pem",
  "tlsverify": true,
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"],
  "default-runtime": "runc",
  "userland-proxy": true,
  "iptables": true,
  "ip-forward": true,
  "ip-masq": true
}
```

### Key Options Explained

```
┌──────────────────────┬──────────────────────────────────────────┐
│ Option               │ Purpose                                  │
├──────────────────────┼──────────────────────────────────────────┤
│ data-root            │ Where Docker stores all data             │
│                      │ Default: /var/lib/docker                 │
├──────────────────────┼──────────────────────────────────────────┤
│ storage-driver       │ Filesystem driver for image layers       │
│                      │ Default: overlay2                        │
├──────────────────────┼──────────────────────────────────────────┤
│ log-driver           │ Default logging driver for containers    │
│                      │ Options: json-file, syslog, journald,   │
│                      │ fluentd, awslogs, splunk, none           │
├──────────────────────┼──────────────────────────────────────────┤
│ log-opts             │ Options for the log driver               │
│                      │ max-size: max log file size              │
│                      │ max-file: number of rotated files        │
├──────────────────────┼──────────────────────────────────────────┤
│ dns                  │ DNS servers for containers               │
├──────────────────────┼──────────────────────────────────────────┤
│ insecure-registries  │ Allow HTTP (non-TLS) registries          │
├──────────────────────┼──────────────────────────────────────────┤
│ registry-mirrors     │ Mirror registries for Docker Hub         │
├──────────────────────┼──────────────────────────────────────────┤
│ live-restore         │ Keep containers running during daemon    │
│                      │ restart/upgrade                          │
├──────────────────────┼──────────────────────────────────────────┤
│ debug                │ Enable debug-level logging               │
├──────────────────────┼──────────────────────────────────────────┤
│ hosts                │ Where daemon listens for connections     │
│                      │ Unix socket and/or TCP                   │
├──────────────────────┼──────────────────────────────────────────┤
│ tls / tlsverify      │ Enable TLS / require client certs        │
├──────────────────────┼──────────────────────────────────────────┤
│ default-runtime      │ OCI runtime (runc, crun, kata, gVisor)   │
├──────────────────────┼──────────────────────────────────────────┤
│ userland-proxy       │ Use userland proxy for port forwarding   │
│                      │ (true = docker-proxy, false = iptables)  │
└──────────────────────┴──────────────────────────────────────────┘
```

### Applying Changes

```bash
# After editing daemon.json, restart Docker
$ sudo systemctl restart docker

# Or reload without full restart (some options support this)
$ sudo systemctl reload docker

# Verify the config was applied
$ docker info

# Check for config errors
$ sudo journalctl -u docker.service --no-pager -n 20
```

---

## 13.3 Managing the Docker Service with systemd

```bash
# Start Docker daemon
$ sudo systemctl start docker

# Stop Docker daemon
$ sudo systemctl stop docker

# Restart Docker daemon
$ sudo systemctl restart docker

# Enable Docker to start on boot
$ sudo systemctl enable docker

# Disable auto-start on boot
$ sudo systemctl disable docker

# Check daemon status
$ sudo systemctl status docker

# Output:
# ● docker.service - Docker Application Container Engine
#    Loaded: loaded (/lib/systemd/system/docker.service; enabled)
#    Active: active (running) since Mon 2025-01-15 10:00:00 UTC
#    Main PID: 1234 (dockerd)
#    Tasks: 15
#    Memory: 120.5M
```

### Overriding systemd Unit File

```bash
# View the default unit file
$ sudo systemctl cat docker.service

# Create an override (don't edit the original)
$ sudo systemctl edit docker.service

# This creates: /etc/systemd/system/docker.service.d/override.conf
# Add your overrides:
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2376

# Reload systemd and restart Docker
$ sudo systemctl daemon-reload
$ sudo systemctl restart docker
```

---

## 13.4 Docker Daemon Debug Mode

Debug mode increases log verbosity — useful for troubleshooting daemon issues.

### Enable via daemon.json (Persistent)

```json
{
  "debug": true
}
```

```bash
$ sudo systemctl restart docker
```

### Enable at Runtime (Temporary)

```bash
# Send SIGUSR1 to toggle debug mode without restart
$ sudo kill -SIGUSR1 $(pidof dockerd)

# Verify debug is enabled
$ docker info | grep -i debug
# Debug Mode: true
```

### Reading Debug Logs

```bash
# View daemon logs
$ sudo journalctl -u docker.service -f

# Output with debug enabled:
# level=debug msg="Calling HEAD /_ping"
# level=debug msg="Calling GET /v1.47/containers/json"
# level=debug msg="Calling POST /v1.47/containers/create"

# Filter for errors only
$ sudo journalctl -u docker.service --no-pager | grep -i error
```

---

## 13.5 Changing the Data Root Directory

By default Docker stores everything under `/var/lib/docker`. If your root partition is small, move it.

```bash
# Step 1: Stop Docker
$ sudo systemctl stop docker

# Step 2: Create new directory
$ sudo mkdir -p /mnt/docker-data

# Step 3: Move existing data
$ sudo rsync -aP /var/lib/docker/ /mnt/docker-data/

# Step 4: Configure daemon.json
$ sudo vi /etc/docker/daemon.json
```

```json
{
  "data-root": "/mnt/docker-data"
}
```

```bash
# Step 5: Start Docker
$ sudo systemctl start docker

# Step 6: Verify
$ docker info | grep "Docker Root Dir"
# Docker Root Dir: /mnt/docker-data

# Step 7: After confirming everything works, remove old data
$ sudo rm -rf /var/lib/docker
```

---

## 13.6 Live Restore — Keep Containers Running During Daemon Restart

Without `live-restore`, all containers stop when the daemon restarts. With it, containers keep running.

```json
{
  "live-restore": true
}
```

```bash
# Restart daemon — containers stay running
$ sudo systemctl restart docker

# Verify containers are still up
$ docker ps
# CONTAINER ID   IMAGE   STATUS
# abc123         nginx   Up 2 hours   ← still running!
```

```
┌─────────────────────────────────────────────────────────────┐
│              LIVE RESTORE BEHAVIOR                           │
│                                                              │
│  Without live-restore:                                      │
│    daemon restart → all containers stop → restart them      │
│    Downtime for every daemon upgrade                        │
│                                                              │
│  With live-restore:                                         │
│    daemon restart → containers keep running                 │
│    Daemon reconnects to running containers                  │
│    No downtime for daemon upgrades                          │
│                                                              │
│  Limitations:                                               │
│    ❌ Does NOT work with Swarm mode                         │
│    ❌ Does NOT work across major version upgrades           │
│    ✅ Works for patch/minor daemon upgrades                 │
│    ✅ Works for standalone containers                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 13.7 Configuring Remote Access to Docker Daemon

By default, Docker only listens on a local Unix socket. To manage Docker remotely, enable TCP.

### Without TLS (Insecure — Dev/Lab Only)

```bash
# daemon.json
{
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]
}
```

```bash
# ⚠️  Port 2375 = unencrypted, no authentication
# Anyone who can reach this port has FULL ROOT ACCESS to the host
# NEVER use this in production

# From a remote machine:
$ docker -H tcp://192.168.1.10:2375 ps
```

### With TLS (Secure — Production)

```
┌─────────────────────────────────────────────────────────────┐
│              TLS AUTHENTICATION FLOW                         │
│                                                              │
│  Client                          Server (Daemon)            │
│    │                                │                        │
│    │── presents client cert ──────►│                        │
│    │                                │── verifies against CA │
│    │◄── presents server cert ──────│                        │
│    │── verifies against CA ────────│                        │
│    │                                │                        │
│    │◄═══ Encrypted connection ════►│                        │
│                                                              │
│  Both sides verify each other = Mutual TLS (mTLS)          │
│                                                              │
│  Files needed:                                              │
│    CA cert     (ca.pem)         → trusted authority         │
│    Server cert (server-cert.pem) → daemon identity          │
│    Server key  (server-key.pem)  → daemon private key       │
│    Client cert (cert.pem)        → client identity          │
│    Client key  (key.pem)         → client private key       │
└─────────────────────────────────────────────────────────────┘
```

---

## 13.8 Setting Up TLS for Docker Daemon — Step by Step

### Step 1: Generate CA Key and Certificate

```bash
# Create a directory for certs
$ mkdir -p /etc/docker/certs && cd /etc/docker/certs

# Generate CA private key
$ openssl genrsa -aes256 -out ca-key.pem 4096
# Enter passphrase (remember it)

# Generate CA certificate (valid for 1 year)
$ openssl req -new -x509 -days 365 -key ca-key.pem -sha256 -out ca.pem
# Enter passphrase
# Fill in: Country, State, Org, Common Name (e.g., "Docker CA")
```

### Step 2: Generate Server Key and Certificate

```bash
# Generate server private key
$ openssl genrsa -out server-key.pem 4096

# Create server certificate signing request (CSR)
$ openssl req -subj "/CN=docker-server" -sha256 -new \
    -key server-key.pem -out server.csr

# Allow connections via IP and hostname
$ echo "subjectAltName = DNS:docker-server,IP:192.168.1.10,IP:127.0.0.1" > extfile.cnf
$ echo "extendedKeyUsage = serverAuth" >> extfile.cnf

# Sign the server cert with the CA
$ openssl x509 -req -days 365 -sha256 \
    -in server.csr -CA ca.pem -CAkey ca-key.pem \
    -CAcreateserial -out server-cert.pem \
    -extfile extfile.cnf

# Output:
# Signature ok
# subject=CN = docker-server
```

### Step 3: Generate Client Key and Certificate

```bash
# Generate client private key
$ openssl genrsa -out key.pem 4096

# Create client CSR
$ openssl req -subj "/CN=client" -new -key key.pem -out client.csr

# Mark as client cert
$ echo "extendedKeyUsage = clientAuth" > extfile-client.cnf

# Sign the client cert with the CA
$ openssl x509 -req -days 365 -sha256 \
    -in client.csr -CA ca.pem -CAkey ca-key.pem \
    -CAcreateserial -out cert.pem \
    -extfile extfile-client.cnf
```

### Step 4: Set Permissions and Clean Up

```bash
# Remove CSR files (no longer needed)
$ rm -f server.csr client.csr extfile.cnf extfile-client.cnf

# Set strict permissions
$ chmod 0400 ca-key.pem key.pem server-key.pem
$ chmod 0444 ca.pem server-cert.pem cert.pem

# Final file list:
$ ls -la /etc/docker/certs/
# ca.pem           ← CA certificate (shared)
# ca-key.pem       ← CA private key (keep secure)
# server-cert.pem  ← Server certificate
# server-key.pem   ← Server private key
# cert.pem         ← Client certificate
# key.pem          ← Client private key
```

### Step 5: Configure the Daemon

```json
{
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"],
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert": "/etc/docker/certs/server-cert.pem",
  "tlskey": "/etc/docker/certs/server-key.pem"
}
```

```bash
$ sudo systemctl restart docker
```

### Step 6: Connect from Client

```bash
# Copy client certs to the remote machine
# ca.pem, cert.pem, key.pem

# Connect with TLS
$ docker --tlsverify \
    --tlscacert=ca.pem \
    --tlscert=cert.pem \
    --tlskey=key.pem \
    -H=tcp://192.168.1.10:2376 ps

# Or set environment variables (avoid typing flags every time)
$ export DOCKER_HOST=tcp://192.168.1.10:2376
$ export DOCKER_TLS_VERIFY=1
$ export DOCKER_CERT_PATH=/path/to/certs

$ docker ps   # Now connects to remote daemon with TLS
```

```
┌─────────────────────────────────────────────────────────────┐
│              TLS PORT CONVENTION                             │
│                                                              │
│  Port 2375 = unencrypted (NEVER use in production)          │
│  Port 2376 = TLS encrypted (production standard)            │
│                                                              │
│  --tls       = encrypt traffic (server cert only)           │
│  --tlsverify = encrypt + require client cert (mutual TLS)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 13.9 Insecure Registries

By default Docker requires HTTPS for registry communication. For private registries without TLS (dev/lab), add them to `insecure-registries`.

```json
{
  "insecure-registries": ["myregistry.local:5000", "10.0.0.50:5000"]
}
```

```bash
$ sudo systemctl restart docker

# Now you can push/pull without TLS
$ docker push myregistry.local:5000/myapp:1.0
```

```
┌─────────────────────────────────────────────────────────────┐
│              INSECURE REGISTRY WARNING                       │
│                                                              │
│  ⚠️  insecure-registries disables TLS verification          │
│                                                              │
│  Use ONLY for:                                              │
│    ✅ Local development                                     │
│    ✅ Lab/test environments                                 │
│    ✅ Air-gapped networks                                   │
│                                                              │
│  NEVER use for:                                             │
│    ❌ Production registries                                 │
│    ❌ Registries accessible over the internet               │
└─────────────────────────────────────────────────────────────┘
```

---

## 13.10 Logging Driver Configuration

### Set Default Log Driver for All Containers

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
```

### Override Per Container

```bash
$ docker run -d \
    --log-driver syslog \
    --log-opt syslog-address=udp://logserver:514 \
    nginx
```

### Available Log Drivers

```
┌──────────────┬──────────────────────────────────────────────┐
│ Driver       │ Description                                  │
├──────────────┼──────────────────────────────────────────────┤
│ json-file    │ Default. JSON logs on host filesystem        │
│ syslog       │ Send to syslog daemon                        │
│ journald     │ Send to systemd journal                      │
│ fluentd      │ Send to Fluentd collector                    │
│ awslogs      │ Send to AWS CloudWatch Logs                  │
│ splunk       │ Send to Splunk HTTP Event Collector          │
│ gcplogs      │ Send to Google Cloud Logging                 │
│ gelf         │ Send to Graylog (GELF format)                │
│ none         │ Disable logging (docker logs won't work)     │
└──────────────┴──────────────────────────────────────────────┘
```

### Check Current Log Driver

```bash
# Global default
$ docker info | grep "Logging Driver"
# Logging Driver: json-file

# Per container
$ docker inspect --format='{{.HostConfig.LogConfig.Type}}' my-container
# json-file
```

---

## 13.11 DNS Configuration

```json
{
  "dns": ["8.8.8.8", "8.8.4.4"],
  "dns-search": ["example.com"],
  "dns-opts": ["ndots:2"]
}
```

```bash
# Verify DNS inside a container
$ docker run --rm alpine cat /etc/resolv.conf
# nameserver 8.8.8.8
# nameserver 8.8.4.4
# search example.com
# options ndots:2
```

---

## 13.12 Troubleshooting the Docker Daemon

### Daemon Won't Start

```bash
# Check status
$ sudo systemctl status docker
# Active: failed

# Check logs for errors
$ sudo journalctl -u docker.service --no-pager -n 50

# Common causes:
```

```
┌─────────────────────────────────────────────────────────────┐
│              DAEMON STARTUP FAILURES                         │
│                                                              │
│  Cause 1: Invalid daemon.json                               │
│    Error: "unable to configure the Docker daemon with file  │
│    /etc/docker/daemon.json: invalid character..."           │
│    Fix: Validate JSON syntax                                │
│    $ python3 -c "import json; json.load(open(              │
│        '/etc/docker/daemon.json'))"                         │
│                                                              │
│  Cause 2: Conflicting flags                                 │
│    Error: "unable to configure the Docker daemon with file  │
│    /etc/docker/daemon.json: the following directives are    │
│    specified both as a flag and in the config file: hosts"  │
│    Fix: Use daemon.json OR command-line flags, not both     │
│    for the same option                                      │
│                                                              │
│  Cause 3: Port already in use                               │
│    Error: "listen tcp 0.0.0.0:2376: bind: address already  │
│    in use"                                                  │
│    Fix: $ sudo lsof -i :2376                               │
│                                                              │
│  Cause 4: Storage driver mismatch                           │
│    Error: "driver not supported"                            │
│    Fix: Check OS compatibility or remove old data           │
│                                                              │
│  Cause 5: Disk full                                         │
│    Error: "no space left on device"                         │
│    Fix: $ docker system prune -a                            │
│         $ df -h /var/lib/docker                             │
└─────────────────────────────────────────────────────────────┘
```

### Daemon Running But Commands Fail

```bash
# Error: Cannot connect to the Docker daemon
# Is the docker daemon running?

# Check if socket exists
$ ls -la /var/run/docker.sock
# srw-rw---- 1 root docker ... /var/run/docker.sock

# Check if your user is in the docker group
$ groups
# user sudo docker   ← "docker" must be listed

# If not in docker group:
$ sudo usermod -aG docker $USER
$ newgrp docker   # Apply without logout
```

---

## 13.13 Common daemon.json Configurations

### Development Setup

```json
{
  "debug": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "insecure-registries": ["localhost:5000"],
  "dns": ["8.8.8.8"]
}
```

### Production Setup

```json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  },
  "live-restore": true,
  "userland-proxy": false,
  "default-address-pools": [
    { "base": "172.20.0.0/16", "size": 24 }
  ],
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert": "/etc/docker/certs/server-cert.pem",
  "tlskey": "/etc/docker/certs/server-key.pem",
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"]
}
```

---

## 13.14 Command-Line Flags vs daemon.json

```
┌──────────────────────────────────────────────────────────────┐
│  You can configure the daemon two ways:                      │
│                                                              │
│  1. Command-line flags (in systemd unit file)               │
│     ExecStart=/usr/bin/dockerd --debug --tls                │
│                                                              │
│  2. daemon.json (configuration file)                        │
│     { "debug": true, "tls": true }                          │
│                                                              │
│  ⚠️  RULE: You CANNOT set the same option in both places    │
│     Docker will refuse to start if there's a conflict       │
│                                                              │
│  Best practice:                                             │
│    Use daemon.json for everything                           │
│    Remove flags from systemd unit file                      │
│    Easier to manage, version control, and audit             │
└──────────────────────────────────────────────────────────────┘
```

---

## Module 13 Summary

- Docker daemon (`dockerd`) is configured via `/etc/docker/daemon.json` or command-line flags — never both for the same option
- `data-root` controls where Docker stores all data — move it if root partition is small
- `storage-driver` selects the filesystem driver — `overlay2` is the modern default
- `log-driver` and `log-opts` control container logging — always set `max-size` and `max-file` to prevent disk exhaustion
- `debug: true` enables verbose logging — toggle at runtime with `kill -SIGUSR1`
- `live-restore: true` keeps containers running during daemon restarts — does not work with Swarm mode
- Docker listens on Unix socket by default — enable TCP for remote access
- Port 2375 = unencrypted (dev only), Port 2376 = TLS encrypted (production)
- `--tls` encrypts traffic; `--tlsverify` adds mutual authentication (client must present a cert)
- TLS setup requires: CA cert, server cert+key, client cert+key — all signed by the same CA
- `insecure-registries` allows HTTP registries — use only in dev/lab environments
- `dns` in daemon.json sets DNS servers for all containers
- Use `systemctl` to manage the daemon: start, stop, restart, enable, status
- Override systemd unit with `systemctl edit docker.service` — never edit the original
- Troubleshoot with `journalctl -u docker.service` and `docker info`
- Validate daemon.json syntax before restarting — invalid JSON prevents daemon startup

---

**Previous Module: [Module 12 - Docker Image Optimization](module-12-optimization.md)**

**Next Module: [Module 14 - Docker Content Trust & Image Signing](module-14-content-trust.md)**
