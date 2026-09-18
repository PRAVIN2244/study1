# Module 20: Docker Security Deep Dive

---

## 20.1 Docker Security Layers

Docker security is built on multiple Linux kernel features working together.

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER SECURITY LAYERS                          │
│                                                              │
│  Layer 1: Namespaces                                        │
│    Isolate what the container can SEE                       │
│    PID, NET, MNT, UTS, IPC, USER namespaces                │
│                                                              │
│  Layer 2: Control Groups (cgroups)                          │
│    Limit what the container can USE                         │
│    CPU, memory, I/O, network bandwidth                     │
│                                                              │
│  Layer 3: Linux Capabilities                                │
│    Limit what the container can DO                          │
│    Fine-grained root privilege control                      │
│                                                              │
│  Layer 4: Seccomp                                           │
│    Limit which SYSTEM CALLS the container can make          │
│    Blocks dangerous syscalls                                │
│                                                              │
│  Layer 5: AppArmor / SELinux                                │
│    Mandatory Access Control (MAC)                           │
│    Restricts file access, network, capabilities             │
│                                                              │
│  Layer 6: Read-only filesystem + no-new-privileges          │
│    Prevents runtime privilege escalation                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 20.2 Linux Capabilities — Fine-Grained Root Control

Root has ~40 capabilities. Docker drops most of them by default, keeping only what containers typically need.

### Default Capabilities (Docker Keeps These)

```
┌──────────────────────┬──────────────────────────────────────┐
│ Capability           │ What It Allows                       │
├──────────────────────┼──────────────────────────────────────┤
│ CHOWN                │ Change file ownership                │
│ DAC_OVERRIDE         │ Bypass file permission checks        │
│ FSETID               │ Set file SUID/SGID bits              │
│ FOWNER               │ Bypass ownership checks              │
│ MKNOD                │ Create special files                  │
│ NET_RAW              │ Use raw sockets (ping)               │
│ SETGID               │ Set group ID                         │
│ SETUID               │ Set user ID                          │
│ SETFCAP              │ Set file capabilities                │
│ SETPCAP              │ Modify process capabilities          │
│ NET_BIND_SERVICE     │ Bind to ports below 1024             │
│ SYS_CHROOT           │ Use chroot                           │
│ KILL                 │ Send signals to processes            │
│ AUDIT_WRITE          │ Write to audit log                   │
└──────────────────────┴──────────────────────────────────────┘
```

### Dropped Capabilities (Docker Removes These)

```
┌──────────────────────┬──────────────────────────────────────┐
│ Capability           │ What It Would Allow                  │
├──────────────────────┼──────────────────────────────────────┤
│ SYS_ADMIN            │ Mount filesystems, load modules      │
│ SYS_PTRACE           │ Trace/debug other processes          │
│ SYS_MODULE           │ Load kernel modules                  │
│ SYS_RAWIO            │ Direct I/O access                    │
│ SYS_TIME             │ Change system clock                  │
│ NET_ADMIN            │ Configure network interfaces         │
│ SYS_BOOT             │ Reboot the system                    │
│ MAC_ADMIN            │ Change MAC configuration             │
│ LINUX_IMMUTABLE      │ Set immutable file flags             │
└──────────────────────┴──────────────────────────────────────┘
```

### Managing Capabilities

```bash
# Drop ALL capabilities, add back only what's needed
$ docker run -d \
    --cap-drop ALL \
    --cap-add NET_BIND_SERVICE \
    nginx

# Drop a specific capability
$ docker run -d --cap-drop NET_RAW nginx
# Container can't use ping (requires NET_RAW)

# Add a capability (not in default set)
$ docker run -d --cap-add SYS_PTRACE myapp
# Allows strace/debugging inside container

# Check capabilities inside a container
$ docker exec mycontainer cat /proc/1/status | grep Cap
# CapPrm: 00000000a80425fb
# CapEff: 00000000a80425fb

# Decode capabilities
$ docker exec mycontainer capsh --decode=00000000a80425fb
```

### The --privileged Flag

```
┌─────────────────────────────────────────────────────────────┐
│              ⚠️  --privileged IS DANGEROUS                   │
│                                                              │
│  $ docker run --privileged myapp                            │
│                                                              │
│  This gives the container:                                  │
│    ✅ ALL Linux capabilities                                │
│    ✅ Access to ALL host devices (/dev/*)                   │
│    ✅ Ability to mount filesystems                          │
│    ✅ Ability to load kernel modules                        │
│    ✅ Effectively ROOT on the HOST                          │
│                                                              │
│  Use ONLY for:                                              │
│    • Docker-in-Docker (DinD) builds                        │
│    • Hardware access (GPU, USB)                             │
│    • System-level debugging                                │
│                                                              │
│  NEVER use in production workloads                          │
│  Instead: use --cap-add for specific capabilities          │
└─────────────────────────────────────────────────────────────┘
```

---

## 20.3 Seccomp — System Call Filtering

Seccomp (Secure Computing Mode) restricts which Linux system calls a container can make. Docker applies a default seccomp profile that blocks ~44 dangerous syscalls.

### Default Seccomp Profile

```bash
# Docker applies a default profile automatically
# View the default profile
$ docker info | grep -i seccomp
# Security Options: seccomp

# The default profile blocks syscalls like:
#   mount        → prevents mounting filesystems
#   reboot       → prevents rebooting the host
#   swapon/off   → prevents swap manipulation
#   clock_settime → prevents changing system time
#   init_module  → prevents loading kernel modules
#   delete_module → prevents unloading kernel modules
#   acct         → prevents process accounting
```

### Custom Seccomp Profile

```bash
# Create a custom profile (JSON)
$ cat custom-seccomp.json
```

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept", "bind", "clone", "close", "connect",
        "execve", "exit", "exit_group", "fcntl", "fork",
        "fstat", "getpid", "listen", "mmap", "open",
        "openat", "read", "recvfrom", "sendto", "socket",
        "stat", "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```bash
# Run with custom profile
$ docker run -d \
    --security-opt seccomp=custom-seccomp.json \
    myapp

# Disable seccomp entirely (NOT recommended)
$ docker run -d --security-opt seccomp=unconfined myapp
```

### Seccomp Actions

```
┌──────────────────────┬──────────────────────────────────────┐
│ Action               │ Behavior                             │
├──────────────────────┼──────────────────────────────────────┤
│ SCMP_ACT_ALLOW       │ Allow the syscall                    │
│ SCMP_ACT_ERRNO       │ Block and return error               │
│ SCMP_ACT_KILL        │ Kill the process immediately         │
│ SCMP_ACT_TRAP        │ Send SIGSYS signal                   │
│ SCMP_ACT_LOG         │ Allow but log the syscall            │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 20.4 AppArmor — Mandatory Access Control

AppArmor confines programs to a limited set of resources. Docker loads a default AppArmor profile for containers.

### Default Docker AppArmor Profile

```bash
# Check if AppArmor is active
$ docker info | grep -i apparmor
# Security Options: apparmor

# View the default profile
$ cat /etc/apparmor.d/docker-default
# Or check loaded profiles
$ sudo aa-status | grep docker
# docker-default (enforce)

# The default profile:
#   Prevents writing to /proc and /sys
#   Prevents mounting filesystems
#   Prevents accessing raw devices
#   Allows normal application operations
```

### Custom AppArmor Profile

```bash
# Create a custom profile
$ sudo vi /etc/apparmor.d/docker-custom
```

```
#include <tunables/global>

profile docker-custom flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow network access
  network,

  # Allow reading most files
  / r,
  /** r,

  # Allow writing to /tmp and /app
  /tmp/** rw,
  /app/** rw,

  # Deny writing to sensitive paths
  deny /etc/** w,
  deny /usr/** w,
  deny /proc/** w,
  deny /sys/** w,
}
```

```bash
# Load the profile
$ sudo apparmor_parser -r /etc/apparmor.d/docker-custom

# Run container with custom profile
$ docker run -d \
    --security-opt apparmor=docker-custom \
    myapp

# Disable AppArmor for a container (NOT recommended)
$ docker run -d --security-opt apparmor=unconfined myapp
```

---

## 20.5 SELinux — Security-Enhanced Linux

SELinux is an alternative to AppArmor, used primarily on RHEL/CentOS/Fedora.

```bash
# Check SELinux status
$ getenforce
# Enforcing / Permissive / Disabled

# Docker applies SELinux labels to containers automatically
# when SELinux is enabled

# Run with specific SELinux label
$ docker run -d --security-opt label=level:s0:c100,c200 myapp

# Disable SELinux for a container
$ docker run -d --security-opt label=disable myapp

# Volume mount with SELinux
$ docker run -d -v /data:/data:z myapp    # shared label
$ docker run -d -v /data:/data:Z myapp    # private label
```

```
┌─────────────────────────────────────────────────────────────┐
│              APPARMOR vs SELINUX                             │
│                                                              │
│  AppArmor:                                                  │
│    Used on: Ubuntu, Debian, SUSE                            │
│    Model: Path-based (rules reference file paths)           │
│    Complexity: Simpler to write profiles                    │
│    Docker: Default profile loaded automatically             │
│                                                              │
│  SELinux:                                                   │
│    Used on: RHEL, CentOS, Fedora                            │
│    Model: Label-based (rules reference security labels)     │
│    Complexity: More complex but more granular               │
│    Docker: Labels applied automatically                     │
│                                                              │
│  Both provide Mandatory Access Control (MAC)                │
│  Docker supports both — uses whichever is on the host       │
└─────────────────────────────────────────────────────────────┘
```

---

## 20.6 User Namespaces — Remapping Root

By default, root inside a container is root on the host (UID 0). User namespaces remap container UIDs to unprivileged host UIDs.

```
┌─────────────────────────────────────────────────────────────┐
│              USER NAMESPACE REMAPPING                        │
│                                                              │
│  Without user namespaces:                                   │
│    Container root (UID 0) = Host root (UID 0)              │
│    If container escapes → full host root access             │
│                                                              │
│  With user namespaces:                                      │
│    Container root (UID 0) = Host user (UID 100000)          │
│    If container escapes → unprivileged host user            │
│    Cannot read /etc/shadow, cannot install packages         │
└─────────────────────────────────────────────────────────────┘
```

### Enabling User Namespace Remapping

```bash
# Configure in daemon.json
$ sudo vi /etc/docker/daemon.json
```

```json
{
  "userns-remap": "default"
}
```

```bash
# Docker creates a subordinate UID/GID mapping
$ sudo systemctl restart docker

# Check the mapping
$ cat /etc/subuid
# dockremap:100000:65536

$ cat /etc/subgid
# dockremap:100000:65536

# Meaning:
#   Container UID 0 → Host UID 100000
#   Container UID 1 → Host UID 100001
#   ... up to 65536 UIDs

# Verify
$ docker run --rm alpine id
# uid=0(root) gid=0(root)   ← looks like root inside

# But on the host:
$ ps aux | grep "alpine"
# 100000  ... /bin/sh   ← running as UID 100000 on host
```

### Limitations

```
┌─────────────────────────────────────────────────────────────┐
│  User namespace limitations:                                │
│    ❌ Cannot use --privileged                               │
│    ❌ Cannot share host PID/network namespace               │
│    ❌ Some volume permissions may need adjustment           │
│    ❌ Not compatible with all storage drivers               │
│    ✅ Works with overlay2                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 20.7 The --no-new-privileges Flag

Prevents processes inside the container from gaining additional privileges through SUID binaries or capability escalation.

```bash
$ docker run -d --security-opt no-new-privileges myapp

# What this prevents:
#   A non-root process cannot use SUID binaries to become root
#   Even if /usr/bin/passwd has SUID bit set, it won't escalate

# Example without no-new-privileges:
$ docker run --rm alpine sh -c "ls -la /usr/bin/passwd"
# -rwsr-xr-x  ... /usr/bin/passwd   ← SUID bit set
# A process could use this to escalate to root

# With no-new-privileges:
# SUID bit is ignored — process stays at current privilege level
```

---

## 20.8 Read-Only Root Filesystem

```bash
$ docker run -d \
    --read-only \
    --tmpfs /tmp:rw,size=50m \
    --tmpfs /var/run:rw \
    --tmpfs /var/cache:rw \
    myapp

# --read-only: Container filesystem is immutable
# --tmpfs: Writable directories in RAM for temp files

# If the app tries to write to the filesystem:
# Error: Read-only file system

# Benefits:
#   Prevents malware from writing to disk
#   Prevents config tampering
#   Forces proper use of volumes for persistent data
```

---

## 20.9 Docker Daemon Security

### Protecting the Docker Socket

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER SOCKET SECURITY                          │
│                                                              │
│  /var/run/docker.sock gives FULL control over Docker        │
│  Anyone with access to the socket can:                      │
│    • Create privileged containers                           │
│    • Mount the host filesystem                              │
│    • Access all containers and images                       │
│    • Effectively become root on the host                    │
│                                                              │
│  Protection:                                                │
│    1. Restrict docker group membership                      │
│    2. Never mount the socket into containers                │
│       (unless absolutely necessary, e.g., CI/CD)           │
│    3. Use TLS for remote access (Module 13)                │
│    4. Use authorization plugins for fine-grained control    │
└─────────────────────────────────────────────────────────────┘
```

### Swarm Mutual TLS

Docker Swarm automatically configures mutual TLS between all nodes.

```bash
# Swarm auto-generates:
#   CA certificate
#   Node certificates (one per node)
#   Automatic certificate rotation

# Check certificate expiry
$ docker info | grep "CA Configuration"
# Expiry Duration: 3 months
# Force Rotate: 0

# Rotate certificates manually
$ docker swarm ca --rotate

# Change rotation interval
$ docker swarm update --cert-expiry 720h   # 30 days
```

---

## 20.10 Security Scanning in CI/CD

```bash
# Trivy — scan image for vulnerabilities
$ trivy image --severity HIGH,CRITICAL myapp:1.0

# Output:
# myapp:1.0 (debian 12.4)
# Total: 5 (HIGH: 3, CRITICAL: 2)
#
# ┌──────────┬──────────────┬──────────┬───────────┬──────────┐
# │ Library  │ Vulnerability│ Severity │ Installed │ Fixed    │
# ├──────────┼──────────────┼──────────┼───────────┼──────────┤
# │ openssl  │ CVE-2024-xxx │ CRITICAL │ 3.0.11    │ 3.0.13   │
# │ curl     │ CVE-2024-yyy │ HIGH     │ 8.4.0     │ 8.5.0    │
# └──────────┴──────────────┴──────────┴───────────┴──────────┘

# Fail CI pipeline on HIGH/CRITICAL
$ trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:1.0
# Exit code 1 = vulnerabilities found → pipeline fails

# Scan Dockerfile for best practice violations
$ hadolint Dockerfile
# Dockerfile:3 DL3008 Pin versions in apt-get install
# Dockerfile:7 DL3009 Delete apt-get lists after installing
```

---

## 20.11 Production Security Checklist

```
┌──────────────────────────────────────────────────────────────┐
│  DOCKER SECURITY CHECKLIST                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Image Security:                                            │
│  ☐ Use official or verified base images                     │
│  ☐ Pin image versions (never use :latest in prod)           │
│  ☐ Scan images for CVEs in CI/CD pipeline                   │
│  ☐ Use minimal base images (alpine, distroless, scratch)    │
│  ☐ Never store secrets in images                            │
│  ☐ Use multi-stage builds to exclude build tools            │
│  ☐ Sign images with DCT or Cosign                          │
│                                                              │
│  Container Runtime:                                         │
│  ☐ Run as non-root user (USER instruction)                  │
│  ☐ Drop all capabilities, add back only needed ones         │
│  ☐ Use --read-only filesystem                               │
│  ☐ Set --no-new-privileges                                  │
│  ☐ Never use --privileged                                   │
│  ☐ Set memory and CPU limits                                │
│  ☐ Use Docker secrets for sensitive data                    │
│                                                              │
│  Host Security:                                             │
│  ☐ Keep Docker Engine updated                               │
│  ☐ Restrict docker group membership                         │
│  ☐ Enable TLS for remote daemon access                      │
│  ☐ Use user namespace remapping                             │
│  ☐ Enable seccomp (default profile at minimum)              │
│  ☐ Enable AppArmor or SELinux                               │
│  ☐ Configure log rotation                                   │
│                                                              │
│  Network Security:                                          │
│  ☐ Use user-defined bridge networks                         │
│  ☐ Separate frontend/backend networks                       │
│  ☐ Never expose database ports publicly                     │
│  ☐ Use encrypted overlay networks for sensitive traffic     │
│  ☐ Bind to 127.0.0.1 for local-only services               │
│                                                              │
│  Swarm Security:                                            │
│  ☐ Rotate certificates regularly                            │
│  ☐ Use Docker secrets (not env vars) for passwords          │
│  ☐ Drain manager nodes                                      │
│  ☐ Use encrypted overlay networks                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 20.12 Common Errors and Troubleshooting

### Error 1: "Permission denied" with Read-Only Filesystem

```bash
# Error: Read-only file system
# CAUSE: App tries to write to filesystem with --read-only

# Fix: Add tmpfs mounts for writable directories
$ docker run -d --read-only \
    --tmpfs /tmp:rw \
    --tmpfs /var/log:rw \
    myapp
```

### Error 2: "Operation not permitted" After Dropping Capabilities

```bash
# Error: Operation not permitted
# CAUSE: App needs a capability that was dropped

# Fix: Identify which capability is needed
$ docker run --rm --cap-drop ALL myapp
# Check error message for the operation that failed

# Add back the specific capability
$ docker run --rm --cap-drop ALL --cap-add NET_BIND_SERVICE myapp
```

### Error 3: Container Killed by Seccomp

```bash
# Error: Container exits immediately with signal 31 (SIGSYS)
# CAUSE: App uses a syscall blocked by seccomp profile

# Debug: Run with seccomp logging
$ docker run -d --security-opt seccomp=unconfined myapp
# If it works → seccomp is blocking a needed syscall

# Find which syscall: use strace
$ docker run --rm --cap-add SYS_PTRACE --security-opt seccomp=unconfined \
    myapp strace -f -o /tmp/trace myapp
```

---

## 20.8 Container Incident Response

When a container is suspected of being compromised, follow this
procedure to contain the threat, preserve evidence, and recover.

### Step-by-Step Incident Response

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTAINER INCIDENT RESPONSE PROCEDURE                         │
│                                                                 │
│  Step 1: DETECT                                                │
│    Identify the compromised container via:                      │
│    - Monitoring alerts (unusual CPU, network, processes)        │
│    - Log anomalies (unexpected commands, outbound connections)  │
│    - Security scanner alerts (Falco, Sysdig, Aqua)             │
│                                                                 │
│  Step 2: ISOLATE                                               │
│    Disconnect the container from all networks immediately       │
│    Do NOT stop or remove it — preserve evidence                │
│                                                                 │
│  Step 3: INVESTIGATE                                           │
│    Inspect processes, network connections, filesystem changes   │
│    Export the container filesystem for forensic analysis        │
│                                                                 │
│  Step 4: CONTAIN                                               │
│    Stop the container after evidence is collected               │
│    Rotate all secrets and credentials the container had access  │
│                                                                 │
│  Step 5: RECOVER                                               │
│    Deploy a clean container from a known-good image             │
│    Patch the vulnerability that was exploited                   │
│                                                                 │
│  Step 6: POST-MORTEM                                           │
│    Document the incident, root cause, and remediation           │
│    Update security policies and monitoring rules                │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Isolate — Commands

```bash
# Disconnect the container from ALL networks (stops communication)
$ docker network disconnect bridge compromised-container
$ docker network disconnect myapp-network compromised-container

# Verify isolation — container should have no networks
$ docker inspect --format '{{json .NetworkSettings.Networks}}' compromised-container
# {}

# Alternative: Disconnect all networks programmatically
$ for net in $(docker inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' compromised-container); do
    docker network disconnect "$net" compromised-container
done
```

### Step 3: Investigate — Commands

```bash
# Check running processes inside the container
$ docker top compromised-container
# Look for unexpected processes (crypto miners, reverse shells)

# Check network connections (before isolation)
$ docker exec compromised-container ss -tlnp
$ docker exec compromised-container ss -anp

# Check filesystem changes (what was modified since image creation)
$ docker diff compromised-container
# A /tmp/malware.sh        ← suspicious added file
# C /etc/passwd             ← modified file
# A /root/.ssh/authorized_keys  ← attacker added SSH key

# Export the container filesystem for offline forensic analysis
$ docker export compromised-container -o evidence-$(date +%Y%m%d).tar

# Save container logs
$ docker logs compromised-container > container-logs-$(date +%Y%m%d).txt 2>&1

# Inspect container metadata (env vars, mounts, capabilities)
$ docker inspect compromised-container > container-inspect-$(date +%Y%m%d).json
```

### Step 4: Contain

```bash
# Stop the container (after evidence is preserved)
$ docker stop compromised-container

# Rotate all secrets the container had access to
# Docker Swarm secrets:
$ echo "new-password" | docker secret create db_password_v2 -
$ docker service update --secret-rm db_password --secret-add db_password_v2 myservice

# Rotate API keys, tokens, and certificates
# Update in your secrets manager (Vault, AWS Secrets Manager, etc.)
```

### Runtime Security Tools

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Tool             │ Description                                  │
├──────────────────┼──────────────────────────────────────────────┤
│ Falco            │ CNCF runtime security. Detects anomalous     │
│                  │ behavior using kernel syscall monitoring.     │
│                  │ Alerts on: unexpected shells, network         │
│                  │ connections, file access, privilege changes.  │
├──────────────────┼──────────────────────────────────────────────┤
│ Sysdig           │ Container visibility and security platform.  │
│                  │ Deep syscall-level inspection. Captures       │
│                  │ container activity for forensic analysis.     │
│                  │ Commercial product with open-source roots.    │
├──────────────────┼──────────────────────────────────────────────┤
│ Aqua Security    │ Full container security platform. Image       │
│                  │ scanning, runtime protection, compliance.     │
│                  │ Enforces policies on allowed images/actions.  │
├──────────────────┼──────────────────────────────────────────────┤
│ Trivy            │ Open-source vulnerability scanner. Scans      │
│                  │ images, filesystems, and IaC configs.         │
│                  │ Fast, no database setup required.             │
└──────────────────┴──────────────────────────────────────────────┘
```

```bash
# Run Falco to detect anomalous container behavior
$ docker run --rm -i -t \
    --privileged \
    -v /var/run/docker.sock:/host/var/run/docker.sock \
    -v /proc:/host/proc:ro \
    falcosecurity/falco:latest

# Falco alerts on events like:
#   "Shell spawned in a container" (unexpected bash/sh)
#   "Outbound connection to C2 server"
#   "Sensitive file read" (/etc/shadow, /etc/passwd)
#   "Container privilege escalation"

# Run Sysdig for container inspection
$ docker run --rm -i -t \
    --privileged \
    -v /var/run/docker.sock:/var/run/docker.sock \
    sysdig/sysdig

# Inside sysdig, filter by container:
# sysdig container.name=myapp
# sysdig -c topprocs_net container.name=myapp
```

---

## Module 20 Summary

- Docker security is layered: namespaces, cgroups, capabilities, seccomp, AppArmor/SELinux
- **Capabilities**: Docker drops dangerous capabilities by default; use `--cap-drop ALL --cap-add <needed>` for least privilege
- **--privileged** gives full host access — never use in production; use specific `--cap-add` instead
- **Seccomp** filters system calls — Docker's default profile blocks ~44 dangerous syscalls
- Custom seccomp profiles allow fine-grained syscall control per application
- **AppArmor** (Ubuntu/Debian) and **SELinux** (RHEL/CentOS) provide Mandatory Access Control
- Docker loads default AppArmor/SELinux profiles automatically
- **User namespaces** remap container root (UID 0) to an unprivileged host UID — limits escape damage
- **--no-new-privileges** prevents SUID-based privilege escalation inside containers
- **--read-only** makes the container filesystem immutable — use `--tmpfs` for writable temp directories
- The Docker socket (`/var/run/docker.sock`) grants full host control — restrict access carefully
- Swarm uses automatic mutual TLS between nodes — certificates rotate automatically
- Scan images with Trivy/Grype in CI/CD — fail pipelines on HIGH/CRITICAL CVEs
- Lint Dockerfiles with hadolint for best practice violations
- Follow the security checklist: non-root, minimal capabilities, read-only FS, secrets, scanning, TLS
- **Incident response**: detect → isolate (disconnect networks) → investigate (docker diff, export) → contain → recover → post-mortem
- Runtime security tools: **Falco** (syscall monitoring), **Sysdig** (deep inspection), **Aqua** (full platform), **Trivy** (scanning)

---

**Previous Module: [Module 19 - Raft Consensus & Swarm HA](module-19-raft-consensus.md)**

**Next Module: [Module 21 - Docker Enterprise — UCP, DTR, RBAC](module-21-docker-enterprise.md)**
