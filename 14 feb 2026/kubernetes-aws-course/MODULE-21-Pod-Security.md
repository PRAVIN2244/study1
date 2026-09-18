# MODULE 21: Pod Security — SecurityContext & Pod Security Standards

---

## 21.1 Pod Security

### Docker Security Fundamentals

Understanding Docker security is a prerequisite for Kubernetes SecurityContext. Docker uses Linux namespaces for process isolation and Linux capabilities to restrict root privileges.

**Process isolation:** Containers share the host kernel but run in separate namespaces. A process inside a container sees itself as PID 1, but on the host it has a different PID:

```bash
# Start a container
docker run ubuntu sleep 3600

# Inside the container:
ps aux
# USER   PID  COMMAND
# root     1  sleep 3600       ← PID 1 inside the container

# On the host:
ps aux | grep sleep
# root  3816  sleep 3600       ← Different PID on the host
```

**User privileges:** By default, containers run as root. This is a security risk — even though Docker restricts root capabilities, it's best to run as a non-root user:

```bash
# Method 1: Override at runtime
docker run --user=1000 ubuntu sleep 3600

# Method 2: Set in the Dockerfile
# FROM ubuntu
# USER 1000
docker build -t my-ubuntu-image .
docker run my-ubuntu-image sleep 3600

# Verify — process runs as user 1000, not root
ps aux
# USER   PID  COMMAND
# 1000     1  sleep 3600
```

**Linux capabilities:** Docker's root user is not the same as the host's root. Docker drops many Linux capabilities by default (e.g., `SYS_ADMIN`, `NET_ADMIN`). You can add or remove capabilities:

```bash
# Add a specific capability
docker run --cap-add=MAC_ADMIN ubuntu

# Drop a specific capability
docker run --cap-drop=CHOWN ubuntu

# Run with ALL capabilities (dangerous — use only for debugging)
docker run --privileged ubuntu
```

These Docker concepts map directly to Kubernetes SecurityContext fields:

| Docker | Kubernetes SecurityContext |
|---|---|
| `docker run --user=1000` | `securityContext.runAsUser: 1000` |
| `USER 1000` in Dockerfile | `securityContext.runAsNonRoot: true` |
| `docker run --cap-add=NET_ADMIN` | `securityContext.capabilities.add: ["NET_ADMIN"]` |
| `docker run --cap-drop=ALL` | `securityContext.capabilities.drop: ["ALL"]` |
| `docker run --privileged` | `securityContext.privileged: true` |

### Security Context

Kubernetes SecurityContext can be set at the **pod level** (applies to all containers) or the **container level** (overrides pod-level). Capabilities can only be set at the container level.

**Pod-level settings** — apply to all containers unless overridden:
- `runAsUser`, `runAsGroup`, `fsGroup`, `runAsNonRoot`, `seccompProfile`, `supplementalGroups`, `sysctls`

**Container-level settings** — override pod-level for that specific container:
- All pod-level fields plus: `capabilities`, `allowPrivilegeEscalation`, `readOnlyRootFilesystem`, `privileged`, `procMount`

**Capabilities can ONLY be set at the container level** — setting them at the pod level is invalid.

```yaml
# secure-pod.yaml — pod-level security context
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:1.25
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
```

**Verifying immutability — writes are blocked even in privileged mode:**

```bash
# Attempt to install packages inside the container — fails
kubectl exec -ti secure-app -- apt update
# E: List directory /var/lib/apt/lists/partial is missing. - Acquire (30: Read-only file system)

# Attempt to write a file — fails
kubectl exec -ti secure-app -- touch /etc/test
# touch: cannot touch '/etc/test': Read-only file system

# Writing to mounted emptyDir volumes still works (by design)
kubectl exec -ti secure-app -- touch /tmp/test    # OK
```

> `readOnlyRootFilesystem: true` blocks writes even if the container runs as privileged. The emptyDir volumes provide controlled write access only where needed.

#### Pod-Level vs Container-Level Override

When both pod-level and container-level security contexts are set, the **container-level wins** for that container. Other containers still inherit the pod-level settings.

```yaml
# multi-container-security.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-security
spec:
  securityContext:
    runAsUser: 1000          # Pod-level: all containers run as user 1000
  containers:
  - name: web
    image: ubuntu
    command: ["sleep", "4800"]
    # No container-level securityContext → inherits runAsUser: 1000

  - name: sidecar
    image: ubuntu
    command: ["sleep", "4800"]
    securityContext:
      runAsUser: 2000        # Container-level override → runs as user 2000
```

```bash
kubectl apply -f multi-container-security.yaml

# Verify which user each container runs as
kubectl exec multi-security -c web -- whoami
# Output: 1000    (inherited from pod-level)

kubectl exec multi-security -c web -- id
# Output: uid=1000 gid=0(root) groups=0(root)

kubectl exec multi-security -c sidecar -- whoami
# Output: 2000    (container-level override)

kubectl exec multi-security -c sidecar -- id
# Output: uid=2000 gid=0(root) groups=0(root)
```

#### Adding Capabilities at Container Level

```yaml
# cap-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: cap-test
spec:
  containers:
  - name: app
    image: ubuntu
    command: ["sleep", "3600"]
    securityContext:
      capabilities:
        add: ["SYS_TIME", "NET_ADMIN"]
        drop: ["CHOWN"]
```

```bash
kubectl apply -f cap-pod.yaml

# Verify capabilities inside the container
kubectl exec cap-test -- cat /proc/1/status | grep -i cap
# CapPrm: 00000000aa0435fb
# CapEff: 00000000aa0435fb

# Attempting to set capabilities at pod level is invalid:
# spec.securityContext.capabilities — this field does NOT exist at pod level
```

#### Lab: Security Contexts

This lab walks through checking which user a container runs as, changing the user ID, and adding Linux capabilities.

**Step 1: Check the current user**

```bash
kubectl get pods
# NAME             READY   STATUS    RESTARTS   AGE
# ubuntu-sleeper   1/1     Running   0          7m

kubectl exec ubuntu-sleeper -- whoami
# root
```

The container runs as root by default (no `securityContext` set).

**Step 2: Change the user ID to 1010**

Pods are immutable — you can't change `securityContext` on a running pod. Export, edit, delete, and recreate:

```bash
# Export current pod spec
kubectl get pod ubuntu-sleeper -o yaml > ubuntu-sleeper.yaml
```

Edit the file to add `securityContext` at the pod level:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper
spec:
  securityContext:
    runAsUser: 1010
  containers:
  - name: ubuntu
    image: ubuntu
    command: ["sleep", "4800"]
```

```bash
# Delete and recreate
kubectl delete pod ubuntu-sleeper --force
# pod "ubuntu-sleeper" force deleted

kubectl apply -f ubuntu-sleeper.yaml
# pod/ubuntu-sleeper created

# Verify
kubectl exec ubuntu-sleeper -- whoami
# 1010

kubectl exec ubuntu-sleeper -- id
# uid=1010 gid=0(root) groups=0(root)
```

**Step 3: Multi-container pod — which user runs where?**

Given this pod definition:

```yaml
# multi-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-pod
spec:
  securityContext:
    runAsUser: 1001              # Pod-level default
  containers:
  - name: web
    image: ubuntu
    command: ["sleep", "5000"]
    securityContext:
      runAsUser: 1002            # Container-level override
  - name: sidecar
    image: ubuntu
    command: ["sleep", "5000"]
                                 # No container-level → inherits pod-level
```

- **web** container runs as user **1002** (container-level overrides pod-level)
- **sidecar** container runs as user **1001** (inherits pod-level)

**Step 4: Add SYS_TIME capability**

Update the pod to run as root and add the `SYS_TIME` capability. Capabilities are container-level only:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper
spec:
  containers:
  - name: ubuntu
    image: ubuntu
    command: ["sleep", "4800"]
    securityContext:
      capabilities:
        add: ["SYS_TIME"]
```

```bash
kubectl delete pod ubuntu-sleeper --force
kubectl apply -f ubuntu-sleeper.yaml

# Verify — no runAsUser means root
kubectl exec ubuntu-sleeper -- whoami
# root
```

**Step 5: Add NET_ADMIN capability alongside SYS_TIME**

```yaml
    securityContext:
      capabilities:
        add: ["SYS_TIME", "NET_ADMIN"]
```

```bash
kubectl delete pod ubuntu-sleeper --force
kubectl apply -f ubuntu-sleeper.yaml

# Verify capabilities
kubectl exec ubuntu-sleeper -- cat /proc/1/status | grep Cap
# CapPrm: 00000000aa0c35fb
# CapEff: 00000000aa0c35fb
```

The edit-delete-recreate pattern (`kubectl get pod -o yaml > file.yaml` → edit → `kubectl delete --force` → `kubectl apply -f`) is the standard workflow for modifying immutable pod fields like `securityContext`, `containers`, and `volumes`.

### Host Access Restrictions

Pods can request access to the host's namespaces and filesystem. In production, these should be blocked unless explicitly required (e.g., monitoring agents).

**Fields to restrict:**

| Field | What It Does | Risk | When Needed |
|-------|-------------|------|-------------|
| `hostPID: true` | Pod sees all processes on the host | Can inspect/kill host processes | Node monitoring agents |
| `hostIPC: true` | Pod shares host's IPC namespace | Can access shared memory of other processes | Legacy IPC-dependent apps |
| `hostNetwork: true` | Pod uses the host's network stack | Bypasses network policies, can bind to any port | CNI plugins, kube-proxy |
| `hostPath` volumes | Mounts host filesystem into the pod | Can read/write any file on the node | Log collection (read-only) |
| `privileged: true` | Full access to all host devices and capabilities | Equivalent to root on the host | Device plugins, storage drivers |

**Secure pod spec — block all host access:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  hostPID: false          # Don't share host PID namespace
  hostIPC: false          # Don't share host IPC namespace
  hostNetwork: false      # Don't use host network
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      privileged: false              # Not privileged
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      runAsUser: 1000
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    # No hostPath volumes
```

**Enforcing these restrictions cluster-wide:**

Use Pod Security Admission (PSA) with the `restricted` profile — it blocks all of the above by default:

```bash
kubectl label namespace production pod-security.kubernetes.io/enforce=restricted
```

Or use OPA/Gatekeeper/Kyverno policies to block specific fields. See MODULE-30 for admission controller details.

---

### Pod Security Standards (PSS)

```bash
# Enforce security standards at namespace level
kubectl label namespace production pod-security.kubernetes.io/enforce=restricted
kubectl label namespace production pod-security.kubernetes.io/warn=restricted
kubectl label namespace production pod-security.kubernetes.io/audit=restricted

# Levels: privileged, baseline, restricted
```

### Runtime Classes & Container Sandboxing

By default, containers share the host kernel via `runc` (the standard OCI runtime). For stronger isolation, Kubernetes supports alternative runtimes through the RuntimeClass API:

| Runtime | Tool | Isolation Level | How It Works |
|---|---|---|---|
| **runc** | Default | Standard (namespaces + cgroups) | Containers share the host kernel directly |
| **gVisor (runsc)** | Google | High (user-space kernel) | Intercepts syscalls via a user-space kernel — containers never touch the host kernel |
| **Kata Containers** | OpenStack | Highest (lightweight VM) | Each container runs inside a dedicated micro-VM with its own kernel |

**gVisor architecture — Sentry and Gofer:**

```
┌─────────────────────────────────────────┐
│  Container (application)                │
│         │ syscalls                       │
│         ▼                               │
│  ┌─────────────┐    file I/O   ┌──────┐ │
│  │   Sentry    │──────────────►│Gofer │ │
│  │ (user-space │               │(file │ │
│  │   kernel)   │               │proxy)│ │
│  └──────┬──────┘               └──┬───┘ │
│         │ limited syscalls        │      │
│         ▼                         ▼      │
│  ┌──────────────────────────────────────┐│
│  │         Host Linux Kernel            ││
│  └──────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

- **Sentry** — a user-space kernel that intercepts and handles syscalls from the container. It implements only a subset of Linux syscalls, reducing the attack surface compared to the full kernel
- **Gofer** — a file proxy process. When the container needs file access, Sentry delegates to Gofer instead of making direct kernel calls
- **Network stack** — gVisor uses its own network stack, so containers never interact with the host's network code directly

**Kata Containers — hardware virtualization requirement:**

Kata runs each container inside a lightweight VM, which requires hardware virtualization support (Intel VT-x / AMD-V). This creates a limitation in cloud environments:
- Cloud instances are already VMs, so Kata requires **nested virtualization** (a VM inside a VM)
- Most cloud providers don't support nested virtualization (AWS does not; GCP supports it with manual configuration)
- Kata works best on **bare-metal servers** or cloud instances with dedicated hardware (e.g., AWS bare metal instances)

**Container execution flow:**

```
kubectl run → kubelet → CRI (containerd) → containerd-shim → runtime → container
                                                                │
                                                    ┌───────────┼───────────┐
                                                    │           │           │
                                                   runc       runsc       kata
                                                 (default)   (gVisor)   (Kata VM)
```

**Configuring RuntimeClass in Kubernetes:**

```yaml
# Step 1: Create a RuntimeClass
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc          # Must match the handler name configured in containerd
---
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata-runtime
```

```yaml
# Step 2: Use the RuntimeClass in a pod
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-pod
spec:
  runtimeClassName: gvisor    # Run this pod with gVisor instead of runc
  containers:
  - name: app
    image: nginx
```

```bash
# Check available RuntimeClasses
kubectl get runtimeclass

# Verify which runtime a pod is using
kubectl get pod sandboxed-pod -o jsonpath='{.spec.runtimeClassName}'

# Verify gVisor isolation — the container process should NOT be visible on the host
# SSH to the node, then:
pgrep -a nginx
# No output = gVisor is sandboxing the process (it runs inside gVisor's user-space kernel)
# With runc, you would see the nginx process in the host's process list
```

**When to use sandboxed runtimes:**

| Scenario | Recommended Runtime |
|---|---|
| Trusted internal workloads | runc (default) |
| Running untrusted or third-party code | gVisor or Kata |
| Multi-tenant clusters with strict isolation | Kata Containers |
| Compliance requiring kernel-level separation | Kata Containers |
| Reducing syscall attack surface | gVisor |

> gVisor adds ~10-20% overhead for syscall-heavy workloads. Kata Containers add VM startup latency (~100-200ms). Use only where the isolation benefit justifies the cost.

### Seccomp (Secure Computing)

Seccomp is a Linux kernel feature that restricts which system calls (syscalls) a process can invoke. Linux has 435+ syscalls, but most applications need only a small subset. Allowing unrestricted syscall access increases the attack surface — the [Dirty COW vulnerability (CVE-2016-5195)](https://en.wikipedia.org/wiki/Dirty_COW) exploited the `ptrace` syscall to escalate privileges and escape containers.

**Verify Seccomp support on your kernel:**

```bash
grep -i seccomp /boot/config-$(uname -r)
# CONFIG_HAVE_ARCH_SECCOMP_FILTER=y
# CONFIG_SECCOMP_FILTER=y
# CONFIG_SECCOMP=y
```

**Analyzing syscalls with strace:**

Even simple commands invoke many syscalls. Use `strace -c` to see which ones:

```bash
strace -c touch /tmp/error.log
# % time  seconds  usecs/call  calls  errors  syscall
# ------  -------  ----------  -----  ------  --------
#  0.00   0.000000      0        1       0     execve
#  0.00   0.000000      0        3       0     openat
#  0.00   0.000000      0        6       0     close
#  0.00   0.000000      0        5       0     mmap
#  0.00   0.000000      0        4       0     mprotect
#  0.00   0.000000      0        3       0     brk
#  ...
# 100.00  0.000000     32        3     total
```

#### Seccomp Modes

| Mode | Name | Behavior |
|---|---|---|
| **0** | Disabled | No syscall filtering |
| **1** | Strict | Only `read`, `write`, `exit`, `sigreturn` allowed |
| **2** | Filter | Custom profile defines which syscalls are allowed/denied |

Check a running container's Seccomp mode:

```bash
# Inside a container
cat /proc/1/status | grep Seccomp
# Seccomp:  2    ← Filter mode (profile active)
```

#### Seccomp Profiles (JSON)

Seccomp profiles are JSON files with three key elements:

1. **`architectures`** — supported CPU architectures
2. **`syscalls`** — array of syscall names and their actions
3. **`defaultAction`** — what to do with syscalls not explicitly listed

**Whitelist profile** — deny by default, allow only listed syscalls (more secure):

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_X32"
  ],
  "syscalls": [
    {
      "names": [
        "execve", "close", "brk", "arch_prctl",
        "mmap", "mprotect", "openat", "read", "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

**Blacklist profile** — allow by default, deny only listed syscalls (less secure, easier to implement):

```json
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
  "syscalls": [
    {
      "names": ["ptrace", "mount", "reboot", "kexec_load"],
      "action": "SCMP_ACT_ERRNO"
    }
  ]
}
```

> Whitelist profiles are preferred for production. Blacklist profiles risk overlooking dangerous syscalls.

#### Docker's Default Seccomp Profile

Docker automatically applies a default Seccomp filter (mode 2) that blocks ~60 dangerous syscalls including `ptrace`, `mount`, `reboot`, `clock_settime`, and `kexec_load`. This is why changing the system time inside a container fails:

```bash
docker run -it --rm docker/whalesay /bin/sh
# date -s '19 APR 2012 22:00:00'
# date: cannot set date: Operation not permitted
```

#### Custom Seccomp Profiles with Docker

Apply a custom profile using `--security-opt`:

```bash
# Run with a custom profile that blocks mkdir
docker run -it --rm --security-opt seccomp=/root/custom.json docker/whalesay /bin/sh
# mkdir test
# mkdir: can't create directory 'test': Operation not permitted

# Disable Seccomp entirely (not recommended)
docker run -it --rm --security-opt seccomp=unconfined docker/whalesay /bin/sh
```

#### Seccomp in Kubernetes

Apply Seccomp profiles to pods via `securityContext.seccompProfile`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault    # Use the container runtime's default profile
  containers:
  - name: app
    image: nginx
```

The `type` field accepts:
- `RuntimeDefault` — container runtime's built-in profile (recommended baseline)
- `Localhost` — custom profile from the node's filesystem (specify path in `localhostProfile`)
- `Unconfined` — no Seccomp filtering (not recommended)

```yaml
# Custom Seccomp profile from the node
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/custom.json    # Relative to kubelet's seccomp directory
```

> The Pod Security Standard `restricted` level requires `seccompProfile` to be set to `RuntimeDefault` or `Localhost`. Pods without a Seccomp profile will be rejected in namespaces enforcing the restricted standard.

### AppArmor

AppArmor is a Linux Security Module (LSM) that confines applications to a limited set of resources — specific files, directories, network access, and Linux capabilities. While Seccomp restricts *which syscalls* a process can make, AppArmor controls *which resources* those syscalls can access. They complement each other.

| Mechanism | Controls | Example |
|---|---|---|
| **Seccomp** | Which syscalls are allowed | Block `mkdir`, `mount`, `ptrace` |
| **AppArmor** | Which resources syscalls can access | Allow `write` but only to `/tmp/**`, deny writes to `/etc/**` |
| **Capabilities** | Which privileged operations are allowed | Drop `NET_RAW`, `SYS_ADMIN` |

#### Verifying AppArmor on Nodes

AppArmor must be enabled on every node where profiled pods will run:

```bash
# Check if the AppArmor service is running
systemctl status apparmor

# Verify the kernel module is loaded (must return "Y")
cat /sys/module/apparmor/parameters/enabled
# Y

# List all loaded profiles and their modes
cat /sys/kernel/security/apparmor/profiles
# docker-default (enforce)
# /usr/sbin/tcpdump (enforce)
# /usr/sbin/ntpd (enforce)
# ...

# Detailed status — profiles, modes, and confined processes
aa-status
# apparmor module is loaded.
# 12 profiles are loaded.
# 12 profiles are in enforce mode.
#     docker-default
#     /sbin/dhclient
#     ...
# 0 profiles are in complain mode.
# 11 processes have profiles defined.
# 11 processes are in enforce mode.
```

#### Profile Modes

| Mode | Behavior |
|---|---|
| **Enforce** | Rules are enforced — violations are blocked and logged |
| **Complain** | Violations are allowed but logged as warnings (useful for testing new profiles) |
| **Unconfined** | No restrictions, no logging |

#### Writing AppArmor Profiles

Profiles are plain text files that define what an application can and cannot do:

```
# /etc/apparmor.d/apparmor-deny-write
# Deny all file writes across the entire filesystem
profile apparmor-deny-write flags=(attach_disconnected) {
    file,              # Allow general file access
    deny /** w,        # Then deny write to everything under /
}
```

```
# /etc/apparmor.d/apparmor-deny-remount-root
# Prevent remounting root filesystem
profile apparmor-deny-remount-root flags=(attach_disconnected) {
    deny mount options=(ro, remount) -> /,
}
```

**Loading profiles:**

```bash
# Load a new profile (enforce mode)
apparmor_parser /etc/apparmor.d/apparmor-deny-write

# Reload a modified profile
apparmor_parser -r /etc/apparmor.d/apparmor-deny-write

# Load in complain mode (for testing)
apparmor_parser -C /etc/apparmor.d/apparmor-deny-write

# Verify it's loaded
aa-status | grep apparmor-deny-write
# apparmor-deny-write (enforce)
```

#### Generating Profiles with aa-genprof

Instead of writing profiles by hand, use `aa-genprof` to generate profiles interactively by observing an application's actual behavior:

```bash
# Install AppArmor utilities
apt-get install -y apparmor-utils
```

**Example — profiling a script that writes to `/opt/app/data`:**

```bash
#!/bin/bash
# /root/add_data.sh
data_directory=/opt/app/data
mkdir -p "${data_directory}"
echo "=> File created at $(date)" | tee "${data_directory}/create.log"
```

**Step 1: Start the profiler:**

```bash
aa-genprof /root/add_data.sh
# Writing updated profile for /root/add_data.sh.
# Setting /root/add_data.sh to complain mode!
# ...
# [(S)can system log for AppArmor events] / (F)inish
```

**Step 2: In a separate terminal, run the application:**

```bash
./add_data.sh
# => File created at Mon Mar 12 03:29:22 UTC 2021
```

**Step 3: Back in the profiler, press `S` to scan.** The tool presents each observed access and asks whether to allow or deny:

```
Profile:  /root/add_data.sh
Execute:  /usr/bin/mkdir
Severity: unknown
(I)nherit / (C)hild / (P)rofile / (N)amed / (U)nconfined / (X) ix On / (D)eny / Abo(r)t / (F)inish
```

For each prompt, choose:
- `I` (Inherit) — allow the child process to run under the parent's profile (typical for `mkdir`, `tee`, `date`)
- `A` (Allow) — permit the file/resource access
- `D` (Deny) — block access to resources the application doesn't need

**Step 4: Save and finish.** Press `S` to save, then `F` to finish. The profile is set to enforce mode automatically.

**Generated profile (stored in `/etc/apparmor.d/`):**

```
#include <tunables/global>

/root/add_data.sh {
    #include <abstractions/base>
    #include <abstractions/bash>
    #include <abstractions/consoles>

    deny owner /proc/filesystems r,
    /root/add_data.sh r,
    /usr/bin/bash ix,
    /usr/bin/date mrix,
    /usr/bin/mkdir mrix,
    /usr/bin/tee mrix,
    owner /opt/app/ rw,
    owner /opt/app/data/ w,
    owner /opt/app/data/create.log w,
}
```

The profile permits only the exact files and executables the script used during profiling. If the script is modified to write to `/opt/create.log` instead of `/opt/app/data/create.log`, AppArmor blocks it:

```bash
./add_data.sh
# tee: /opt/create.log: Permission denied
```

#### Managing Profiles

```bash
# Load a profile
apparmor_parser /etc/apparmor.d/my-profile

# Reload after editing
apparmor_parser -r /etc/apparmor.d/my-profile

# Disable a profile
ln -s /etc/apparmor.d/my-profile /etc/apparmor.d/disable/
apparmor_parser -R /etc/apparmor.d/my-profile

# Verify current state
aa-status
```

#### AppArmor in Kubernetes

AppArmor support was introduced in Kubernetes v1.4. Requirements for using AppArmor on pods:

1. AppArmor kernel module enabled on the node
2. The profile loaded on every node where the pod might be scheduled
3. Container runtime supports AppArmor (Docker, containerd, CRI-O all do)

**Applying a profile to a pod (current API — securityContext):**

Starting from Kubernetes v1.30 (GA), AppArmor profiles are specified via `securityContext.appArmorProfile`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper
spec:
  securityContext:
    appArmorProfile:
      type: Localhost
      localhostProfile: apparmor-deny-write    # Must be loaded on the node
  containers:
  - name: ubuntu-sleeper
    image: ubuntu
    command: ["sh", "-c", "echo 'Sleeping for an hour!' && sleep 1h"]
```

The `type` field accepts:
- `RuntimeDefault` — use the container runtime's default profile (e.g., Docker's `docker-default`)
- `Localhost` — use a profile loaded on the node (specify name in `localhostProfile`)
- `Unconfined` — no AppArmor profile applied

**Legacy annotation-based approach (pre-v1.30):**

Before GA, AppArmor was configured via pod annotations. This still works but is deprecated:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper
  annotations:
    # Format: container.apparmor.security.beta.kubernetes.io/<container-name>: localhost/<profile-name>
    container.apparmor.security.beta.kubernetes.io/ubuntu-sleeper: localhost/apparmor-deny-write
spec:
  containers:
  - name: ubuntu-sleeper
    image: ubuntu
    command: ["sh", "-c", "echo 'Sleeping for an hour!' && sleep 1h"]
```

**Testing the profile:**

```bash
kubectl apply -f ubuntu-sleeper.yaml

# Verify the pod is running
kubectl logs ubuntu-sleeper
# Sleeping for an hour!

# Test the deny-write rule — should fail
kubectl exec -ti ubuntu-sleeper -- touch /tmp/test
# touch: cannot touch '/tmp/test': Permission denied
# command terminated with exit code 1
```

**Per-container profiles** — set `appArmorProfile` at the container level to apply different profiles to different containers in the same pod:

```yaml
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: nginx-profile
  - name: sidecar
    image: fluentd
    securityContext:
      appArmorProfile:
        type: RuntimeDefault
```

> AppArmor profiles must be loaded on every node before pod creation. Use a DaemonSet or node provisioning scripts to distribute profiles across the cluster. If a pod is scheduled to a node without the required profile, it will fail to start.

