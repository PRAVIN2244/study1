# MODULE 31: Security Hardening & Network Security

---

## 31.1 Security Hardening

### Security Primitives Overview

Kubernetes security operates at multiple layers:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Host Security                                 │
│  • Disable root access                                  │
│  • Disable password-based SSH, use key-based auth only  │
│  • Minimize installed packages, apply security patches  │
│                                                         │
│  Layer 2: API Server Access Control                     │
│  • Authentication (WHO can access?)                     │
│    → Certificates, tokens, LDAP, ServiceAccounts        │
│  • Authorization (WHAT can they do?)                    │
│    → RBAC, ABAC, Node, Webhook                          │
│                                                         │
│  Layer 3: TLS Between Components                        │
│  • All component-to-component traffic is encrypted      │
│    → API Server ↔ etcd                                  │
│    → API Server ↔ kubelet                               │
│    → API Server ↔ kube-proxy                            │
│    → API Server ↔ controller-manager                    │
│    → API Server ↔ scheduler                             │
│                                                         │
│  Layer 4: Network Policies                              │
│  • Control pod-to-pod traffic                           │
│  • Default deny + explicit allow                        │
│                                                         │
│  Layer 5: Pod Security                                  │
│  • Pod Security Standards (restricted/baseline)         │
│  • SecurityContext, read-only root filesystem            │
│  • Image scanning, supply chain verification            │
└─────────────────────────────────────────────────────────┘
```

A compromised host exposes the entire cluster. A misconfigured API server allows unauthorized access. Missing TLS allows traffic interception. Missing network policies allow lateral movement. Security must be applied at every layer.

### Cluster Security Checklist

| Area | Action | Priority |
|---|---|---|
| **Hosts** | Disable root access, SSH key-only auth, minimize packages | High |
| **API Server** | Enable audit logging | High |
| **etcd** | Encrypt data at rest | High |
| **Kubelet** | Disable anonymous auth, Webhook authorization, disable read-only port | High |
| **Docker Daemon** | TLS encryption, certificate-based client auth | High |
| **RBAC** | Principle of least privilege, no cluster-admin for apps | High |
| **Network** | Default-deny NetworkPolicies in all namespaces | High |
| **Pods** | Enforce Pod Security Standards (restricted) | High |
| **Images** | Scan images for vulnerabilities (Trivy, Snyk) | High |
| **Secrets** | Use external secret managers (AWS Secrets Manager, Vault) | High |
| **CIS Compliance** | Run kube-bench regularly, remediate failures | High |
| **Dashboard** | ClusterIP only, token auth, least-privilege RBAC | High |
| **Nodes** | Minimize OS packages, auto-update security patches | Medium |
| **Admission** | Use OPA/Gatekeeper for policy enforcement | Medium |
| **Supply chain** | Sign and verify container images (Cosign, Notary) | Medium |
| **Binaries** | Verify checksums of downloaded Kubernetes binaries | Medium |

### Securing Node Metadata

Node metadata contains detailed information about every node in the cluster. Understanding what it exposes is the first step to securing it.

#### What Node Metadata Contains

```bash
# View all metadata for a node
kubectl describe node node01
```

| Component | What It Exposes | Example |
|---|---|---|
| **Node Name** | Unique identifier | `node01`, `ip-10-0-1-100.ec2.internal` |
| **Labels** | Grouping info (region, instance type, OS) | `region: us-east-1`, `kubernetes.io/arch: amd64` |
| **Annotations** | CNI config, CRI socket, internal state | Flannel VNI/MAC, containerd socket path |
| **System Info** | Machine ID, System UUID, Boot ID | Unique hardware identifiers |
| **OS / Kernel** | OS image, kernel version | `Ubuntu 22.04.4 LTS`, `5.15.0-1065-gcp` |
| **Runtime Versions** | Container runtime, kubelet, kube-proxy | `containerd://1.6.26`, `v1.30.0` |
| **Addresses** | Internal IP, external IP, hostname | `10.0.1.100`, `54.23.45.67` |
| **Conditions** | Node health status | `Ready`, `MemoryPressure`, `DiskPressure`, `PIDPressure` |
| **Capacity** | CPU, memory, pods, ephemeral storage | `cpu: 4`, `memory: 16Gi`, `pods: 110` |
| **Taints** | Scheduling restrictions | `dedicated=production:NoSchedule` |
| **Pod CIDR** | Pod IP range assigned to this node | `10.244.1.0/24` |
| **Provider ID** | Cloud-specific instance ID | `aws:///us-east-1a/i-0abc123def456` |

```yaml
# Example: System Info exposed by kubectl get node -o yaml
System Info:
  Machine ID:                 69ee5c89434f4d5baea262a6ecc698fe
  System UUID:                8ab83d3f-465d-36a9-6ec2-b7e9e7ad6a45
  Boot ID:                    8059e764-a637-45f0-abd9-36e9a366e719
  Kernel Version:             5.15.0-1065-gcp
  OS Image:                   Ubuntu 22.04.4 LTS
  Operating System:           linux
  Architecture:               amd64
  Container Runtime Version:  containerd://1.6.26
  Kubelet Version:            v1.30.0
  Kube-Proxy Version:         v1.30.0
```

```yaml
# Example: Flannel annotations (CNI internal state)
Annotations:
  flannel.alpha.coreos.com/backend-data: '{"VNI":1,"VtepMAC":"a2:bd:8e:41:63:65"}'
  flannel.alpha.coreos.com/backend-type: vxlan
  flannel.alpha.coreos.com/public-ip: 192.168.87.255
```

#### Why This Data Is Sensitive

If an attacker gains read access to node metadata, they can:

| Risk | How | Impact |
|---|---|---|
| **Improper workload scheduling** | Remove taints from production nodes | Non-critical pods land on secure nodes, causing resource contention |
| **Version-specific exploits** | Read kubelet/kernel versions | Target known CVEs for that exact version |
| **Network mapping** | List internal IPs of all nodes | Build a network map for lateral movement or DDoS |
| **Compliance violations** | Expose kernel versions, OS details | Breach GDPR, HIPAA, or SOC2 audit requirements |

**What an attacker can extract:**

```bash
# Kubelet version — find version-specific exploits
kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.kubeletVersion}'
# v1.29.2  v1.29.2  v1.29.1

# Internal IPs — map the network
kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'
# 10.0.1.100  10.0.2.101  10.0.3.102

# Kernel versions — find OS-level vulnerabilities
kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.kernelVersion}'
# 5.4.0-1041-aws  5.4.0-1041-aws

# Remove a taint — schedule unauthorized workloads on a protected node
kubectl taint nodes node-1 dedicated=production:NoSchedule-
# node/node-1 untainted
```

**Protection strategies:**

| Strategy | Implementation |
|---|---|
| **RBAC** | Restrict `get`/`list` on `nodes` to cluster admins only. Regular users and service accounts should not have node-level access |
| **Node isolation** | Use taints + tolerations to reserve nodes for specific workloads. Prevent taint removal via admission controllers |
| **Network policies** | Restrict pod-to-node communication. Block access to the kubelet API (port 10250) from application pods |
| **Audit logging** | Enable API server audit logs to track who reads or modifies node metadata |
| **Regular patching** | Keep kubelet and OS packages updated to minimize the window for version-specific exploits |

```yaml
# RBAC: Restrict node access to admins only
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
---
# Bind only to cluster-admin group, not to developers
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: node-reader-binding
subjects:
- kind: Group
  name: cluster-admins
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

> **EKS relevance:** On EKS, node metadata also includes the EC2 instance metadata service (IMDS). Pods can reach `169.254.169.254` to retrieve IAM credentials. Use IMDSv2 (hop limit = 1) and block IMDS access via NetworkPolicy to prevent credential theft from pods.

### Pod Security Standards

```bash
# Enforce restricted security standard on a namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted
```

### Secure Pod Configuration

```yaml
# Production-hardened pod spec
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  automountServiceAccountToken: false    # Don't mount SA token unless needed
  securityContext:
    runAsNonRoot: true                   # Container must run as non-root
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: my-app:1.0.0@sha256:abc123   # Pin image by digest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true       # Prevent writes to container filesystem
      capabilities:
        drop:
        - ALL                            # Drop all Linux capabilities
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
```

### Minimizing Base Image Footprint

Smaller images have fewer packages, fewer vulnerabilities, and faster pull times. Choose the smallest base image that meets your application's needs:

| Base Image | Size | Packages | Use Case |
|---|---|---|---|
| `ubuntu` | ~77MB | Full OS (apt, bash, coreutils) | Development, debugging |
| `alpine` | ~7MB | Minimal (apk, busybox) | Production services |
| `distroless` | ~2-20MB | App runtime only (no shell, no package manager) | Hardened production |
| `scratch` | 0MB | Nothing — you provide everything | Statically compiled Go/Rust binaries |

**Vulnerability comparison (Trivy scan):**

```bash
trivy image httpd
# httpd (debian 10.8) — Total: 124 (LOW: 88, MEDIUM: 9, HIGH: 25, CRITICAL: 2)

trivy image httpd:alpine
# httpd:alpine (alpine 3.12.4) — Total: 0
```

**Best practices:**

- Use `-alpine` or `-slim` image variants in production
- Use [Google distroless images](https://github.com/GoogleContainerTools/distroless) for maximum hardening — no shell means attackers can't `exec` into the container
- Remove unnecessary tools (`curl`, `wget`, `apt`) from production images — they can be used for data exfiltration
- Don't store data inside containers — use volumes or external services
- Build separate images for dev (with debug tools) and production (minimal)
- Use multi-stage builds to keep build tools out of the final image:

```dockerfile
# Multi-stage build — build tools stay in stage 1, only the binary ships
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /myapp

FROM gcr.io/distroless/static-debian12
COPY --from=builder /myapp /myapp
ENTRYPOINT ["/myapp"]
# Final image: ~5MB, no shell, no package manager
```

### Image Scanning with Trivy

**What are CVEs?** Common Vulnerabilities and Exposures — a standardized database of known security flaws. Each CVE gets a unique ID (e.g., CVE-2020-8169) and a severity score (CVSS 0–10):

| Score | Severity | Action |
|---|---|---|
| 0.0 | None | Informational |
| 0.1–3.9 | Low | Monitor |
| 4.0–6.9 | Medium | Plan fix |
| 7.0–8.9 | High | Fix soon |
| 9.0–10.0 | Critical | Fix immediately |

**Installing Trivy (Debian/Ubuntu):**

```bash
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install trivy
```

**Scanning images:**

```bash
# Basic scan
trivy image nginx:1.25

# Filter by severity
trivy image --severity HIGH,CRITICAL my-app:latest

# Ignore vulnerabilities without a fix available
trivy image --ignore-unfixed nginx:1.25

# Scan a saved tar archive
docker save nginx:1.25 > nginx.tar
trivy image --input nginx.tar

# Scan running cluster
trivy k8s --report summary cluster
```

**Best practices for image scanning:**
- Rescan images periodically — new CVEs are published daily
- Integrate Trivy into CI/CD pipelines to block builds with critical vulnerabilities
- Use admission controllers to reject images that haven't been scanned
- Maintain an internal registry of pre-scanned, approved images
- Compare base image variants: `httpd` (Debian, 124 vulns) vs `httpd:alpine` (0 vulns)

### Static Analysis with kubesec

kubesec scans Kubernetes YAML manifests for security risks *before* deployment — catching issues that admission controllers would only find at runtime.

```bash
# Install and scan locally
kubesec scan pod.yaml

# Or use the hosted API
curl -sSX POST --data-binary @"pod.yaml" https://v2.kubesec.io/scan

# Run as a local server
kubesec http 8080 &
curl -sSX POST --data-binary @"pod.yaml" http://localhost:8080/scan
```

**Example output (score: -30):**

```json
{
  "object": "Pod/sample-pod.default",
  "score": -30,
  "scoring": {
    "critical": [{
      "id": "Privileged",
      "selector": "containers[].securityContext.privileged == true",
      "reason": "Privileged containers can allow almost complete system access."
    }]
  },
  "advise": [{
    "id": "ServiceAccountName",
    "selector": "spec.serviceAccountName",
    "reason": "Using service accounts restricts Kubernetes API access.",
    "points": 3
  }]
}
```

kubesec checks for: privileged containers, `runAsUser: 0`, missing resource limits, hostPath volumes, missing AppArmor/Seccomp profiles, and missing service account restrictions. A negative score indicates security concerns that should be addressed before deployment.

### Software Bill of Materials (SBOM)

An SBOM is a machine-readable inventory of all components, libraries, and dependencies in a container image. SBOMs enable vulnerability tracking, license compliance, and supply chain auditing.

**Generating an SBOM with Syft:**

```bash
# Generate SBOM for a container image
syft nginx -o spdx-json > nginx-sbom-spdx.json
syft nginx -o cyclonedx-json > nginx-sbom-cdx.json

# Generate SBOM with Trivy
trivy image --format spdx-json nginx > nginx-sbom.json
```

**Two standard formats:**

| | SPDX | CycloneDX |
|---|---|---|
| **Focus** | Licensing and legal compliance | Security and vulnerability tracking |
| **Maintained by** | Linux Foundation | OWASP |
| **Output formats** | JSON, RDF, tag-value | JSON, XML |
| **Strengths** | Detailed license data, file-level tracking, relationship mapping | Lightweight, vulnerability lists, dependency graphs |
| **Use when** | Legal/compliance audits, open-source license review | Security scanning, CI/CD pipeline integration |

**Using SBOMs in a security workflow:**

1. Generate SBOM at image build time in CI/CD
2. Store SBOM alongside the image (e.g., in OCI registry as an artifact)
3. Scan SBOM against vulnerability databases (e.g., `grype nginx-sbom-cdx.json`)
4. Block deployment if critical vulnerabilities are found (via admission controller)

> SBOMs are increasingly required by compliance frameworks (US Executive Order 14028, NIST). Generating them at build time costs nothing and provides an audit trail for every deployed image.

### Cosign — Container Image Signing and Verification

Cosign (part of the Sigstore project) signs container images cryptographically so you can verify that an image hasn't been tampered with and was built by a trusted pipeline.

**Why sign images:**
- Prevents deploying images modified by attackers (supply chain attacks)
- Proves an image was built by your CI/CD pipeline
- Required by compliance frameworks (SLSA, NIST)

**Install Cosign:**

```bash
# Install via Go
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# Or download binary
curl -LO https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
chmod +x cosign-linux-amd64
sudo mv cosign-linux-amd64 /usr/local/bin/cosign
```

**Generate a key pair and sign an image:**

```bash
# Generate a key pair (creates cosign.key and cosign.pub)
cosign generate-key-pair

# Sign an image after building and pushing it
cosign sign --key cosign.key myregistry.com/myapp:v1.0.0

# Output:
# Pushing signature to: myregistry.com/myapp:sha256-abc123.sig
```

**Verify an image before deploying:**

```bash
cosign verify --key cosign.pub myregistry.com/myapp:v1.0.0

# Output (success):
# Verification for myregistry.com/myapp:v1.0.0 --
# The following checks were performed on each of these signatures:
#   - The cosign claims were validated
#   - The signatures were verified against the specified public key

# Output (failure — tampered or unsigned):
# Error: no matching signatures
```

**Keyless signing with Sigstore (no key management needed):**

```bash
# Uses OIDC identity (GitHub Actions, Google, etc.) — no private key to manage
cosign sign myregistry.com/myapp:v1.0.0

# Verify with keyless
cosign verify myregistry.com/myapp:v1.0.0 \
  --certificate-identity=user@example.com \
  --certificate-oidc-issuer=https://accounts.google.com
```

**Enforce signed images in Kubernetes with an admission controller:**

```yaml
# Kyverno policy — block unsigned images
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  rules:
  - name: verify-cosign-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "myregistry.com/*"
      attestors:
      - entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
```

**CI/CD integration (GitHub Actions):**

```yaml
# In your build pipeline — sign after push
- name: Sign image with Cosign
  run: |
    cosign sign --key env://COSIGN_PRIVATE_KEY \
      ${{ env.REGISTRY }}/${{ env.IMAGE }}:${{ github.sha }}
  env:
    COSIGN_PRIVATE_KEY: ${{ secrets.COSIGN_PRIVATE_KEY }}
    COSIGN_PASSWORD: ${{ secrets.COSIGN_PASSWORD }}
```

**Supply chain security pipeline:**

```
Build image → Trivy scan → Sign with Cosign → Push to registry
                                                      │
                                              Kubernetes cluster
                                                      │
                                              Admission controller
                                              verifies signature
                                                      │
                                              ✅ Deploy (signed)
                                              ❌ Reject (unsigned/tampered)
```

> **Cross-reference:** Trivy scanning → Section 31.5; Kyverno policies → MODULE-30; SBOM generation → Section above

### Runtime Syscall Tracing with Tracee

Tracee is an open-source runtime security tool from Aqua Security that uses eBPF (Extended Berkeley Packet Filter) to trace system calls in containers. eBPF runs programs directly in kernel space without modifying the kernel or loading kernel modules, enabling low-overhead monitoring of OS-level activity.

**Where Tracee fits in the security pipeline:**

| Phase | Tool | What It Does |
|---|---|---|
| Build time | Trivy, kubesec | Scan images and manifests for known vulnerabilities |
| Deploy time | Admission controllers | Block non-compliant workloads |
| **Runtime** | **Tracee** | Detect suspicious syscall activity in running containers |

#### Running Tracee as a Docker Container

Tracee needs access to kernel headers (to compile the eBPF program), the host PID namespace, and privileged mode:

```bash
docker run --name tracee --rm --privileged --pid=host \
  -v /lib/modules/:/lib/modules:ro \
  -v /usr/src:/usr/src:ro \
  -v /tmp/tracee:/tmp/tracee \
  aquasec/tracee:0.4.0 --trace comm=ls
```

| Mount / Flag | Purpose |
|---|---|
| `--privileged` | Required for eBPF syscall tracing |
| `--pid=host` | See host processes, not just container processes |
| `/lib/modules:ro` | Kernel headers for eBPF compilation |
| `/usr/src:ro` | Additional kernel header dependencies |
| `/tmp/tracee` | Persist compiled eBPF program between runs |

#### Tracing Modes

**Trace a specific command:**

```bash
docker run --name tracee --rm --privileged --pid=host \
  -v /lib/modules/:/lib/modules:ro \
  -v /usr/src:/usr/src:ro \
  -v /tmp/tracee:/tmp/tracee \
  aquasec/tracee:0.4.0 --trace comm=ls
```

Sample output:

```
TIME(s)      UID    COMM    PID    TID    RET    EVENT
1263.457188  0      ls      27461  27461  -2     openat
1263.457218  0      ls      27461  27461  -2     openat
1263.457238  0      ls      27461  27461  0      openat
```

**Trace all new processes on the host:**

```bash
docker run --name tracee --rm --privileged --pid=host \
  -v /lib/modules/:/lib/modules:ro \
  -v /usr/src:/usr/src:ro \
  -v /tmp/tracee:/tmp/tracee \
  aquasec/tracee:0.4.0 --trace pid=new
```

**Trace syscalls from new containers only:**

```bash
# Terminal 1: Start Tracee
docker run --name tracee --rm --privileged --pid=host \
  -v /lib/modules/:/lib/modules:ro \
  -v /usr/src:/usr/src:ro \
  -v /tmp/tracee:/tmp/tracee \
  aquasec/tracee:0.4.0 --trace container=new

# Terminal 2: Launch a container — Tracee captures its syscalls
docker run ubuntu echo hi
```

Tracee's terminal shows all syscalls generated by the new container, including `execve`, `openat`, `write`, and `exit_group`.

> Tracee is a detection tool, not a prevention tool. It identifies suspicious activity at runtime. For enforcement, pair it with AppArmor profiles (MODULE 21) or Seccomp profiles to restrict what containers can do.

### Docker Daemon Security

The Docker daemon runs as root and controls all containers on a host. An unsecured daemon can allow attackers to delete containers and volumes, run malicious containers with host access, or gain root on the host system.

**Risks of an unsecured Docker daemon:**

| Risk | Impact |
|---|---|
| Delete containers/volumes | Service disruption, data loss |
| Run privileged containers | Root access to host, lateral movement |
| Access host filesystem | Read secrets, SSH keys, credentials |
| Cryptocurrency mining | Resource theft, increased cloud costs |

#### Host Hardening (Prerequisites)

Before configuring Docker, secure the host:

```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Enforce SSH key-based authentication
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd

# Close unused ports (example: allow only SSH + Docker)
sudo ufw allow 22/tcp
sudo ufw allow 2376/tcp
sudo ufw enable
```

#### Host Firewall with UFW

UFW (Uncomplicated Firewall) is a front-end for iptables that simplifies firewall rule management on Ubuntu/Debian nodes.

**Inspect open ports before configuring:**

```bash
netstat -an | grep -w LISTEN
# tcp   0   0  0.0.0.0:22     0.0.0.0:*   LISTEN
# tcp   0   0  0.0.0.0:80     0.0.0.0:*   LISTEN
# tcp   0   0  0.0.0.0:10250  0.0.0.0:*   LISTEN   ← kubelet
```

**Set default policies — allow outbound, deny inbound:**

```bash
ufw default allow outgoing
ufw default deny incoming
```

**Add source-specific rules:**

```bash
# Allow SSH only from a jump server
ufw allow from 172.16.238.5 to any port 22 proto tcp

# Allow HTTP from an internal subnet (CIDR notation)
ufw allow from 172.16.100.0/28 to any port 80 proto tcp

# Explicitly deny a port (even though default is deny — documents intent)
ufw deny 8080

# Enable the firewall
ufw enable
```

**Manage rules:**

```bash
# View active rules
ufw status
# Status: active
# To          Action   From
# 22/tcp      ALLOW    172.16.238.5
# 80/tcp      ALLOW    172.16.100.0/28
# 8080        DENY     Anywhere

# Delete a rule
ufw delete deny 8080

# Delete by rule number
ufw status numbered
ufw delete 3
```

> On Kubernetes nodes, ensure kubelet (10250), kube-proxy (10256), and any NodePort range (30000–32767) are allowed from the appropriate sources. Overly restrictive firewall rules can break cluster communication.

#### Exposing the Docker Daemon Remotely

By default, Docker listens only on a Unix socket (`/var/run/docker.sock`), restricting access to local users. For remote administration, bind to a TCP interface:

```json
// /etc/docker/daemon.json
{
  "hosts": ["tcp://192.168.1.10:2375"]
}
```

⚠️ **Port 2375 is unencrypted and unauthenticated.** Never expose it on a public interface. Always use TLS (port 2376).

#### Enabling TLS Encryption

TLS encrypts traffic between Docker client and daemon. The daemon listens on port 2376 when TLS is enabled:

```json
// /etc/docker/daemon.json
{
  "hosts": ["tcp://192.168.1.10:2376"],
  "tls": true,
  "tlscert": "/var/docker/server.pem",
  "tlskey": "/var/docker/serverkey.pem"
}
```

TLS alone encrypts traffic but does not verify client identity. Any client can connect.

#### Certificate-Based Client Authentication

To restrict access to clients with valid CA-signed certificates, enable `tlsverify`:

```json
// /etc/docker/daemon.json — production configuration
{
  "hosts": ["tcp://192.168.1.10:2376"],
  "tls": true,
  "tlscert": "/var/docker/server.pem",
  "tlskey": "/var/docker/serverkey.pem",
  "tlsverify": true,
  "tlscacert": "/var/docker/cacert.pem"
}
```

**Certificate setup process:**

```
1. Generate a CA key pair (ca.pem, ca-key.pem)
2. Generate server certificate signed by CA (server.pem, serverkey.pem)
3. Generate client certificate signed by CA (client.pem, clientkey.pem)
4. Configure daemon with CA cert + server cert + tlsverify
5. Distribute client cert + CA cert to authorized users only
```

**Client-side configuration:**

```bash
# Option 1: Environment variables
export DOCKER_TLS_VERIFY=true
export DOCKER_HOST="tcp://192.168.1.10:2376"
docker ps    # Uses certs from ~/.docker/ automatically

# Option 2: Explicit flags
docker --tlsverify \
  --tlscacert=/path/to/cacert.pem \
  --tlscert=/path/to/client.pem \
  --tlskey=/path/to/clientkey.pem \
  -H tcp://192.168.1.10:2376 ps
```

Docker automatically detects certificates stored in `~/.docker/` (`ca.pem`, `cert.pem`, `key.pem`).

**Docker daemon security summary:**

| Setting | Default | Secure Value | Purpose |
|---|---|---|---|
| Listening interface | Unix socket only | TCP with TLS | Remote access |
| Port | N/A | 2376 (not 2375) | TLS-encrypted port |
| `tls` | false | true | Encrypt traffic |
| `tlsverify` | false | true | Require client certificates |
| `tlscacert` | — | CA certificate path | Verify client certs against CA |

> **EKS relevance:** On EKS, node configuration is managed by AWS. Docker daemon security applies to self-managed clusters or CI/CD build servers running Docker.

### Kubelet Security

The kubelet runs on every node and manages pod lifecycle. It exposes an API that, if unsecured, allows attackers to list pods, execute commands in containers, and access node-level data.

#### Kubelet API Ports

| Port | Purpose | Default Access |
|---|---|---|
| **10250** | Full kubelet API (pods, exec, logs, metrics) | Anonymous allowed |
| **10255** | Read-only API (metrics, healthz) | Unauthenticated |

```bash
# Without security — anyone with network access can list pods
curl -sk https://localhost:10250/pods/

# Read-only port — no auth required
curl -s http://localhost:10255/metrics
```

#### 1. Disable Anonymous Authentication

By default, unauthenticated requests are treated as `system:anonymous`. Disable this:

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false
```

Or via command-line flag:

```bash
# kubelet.service
ExecStart=/usr/local/bin/kubelet \
  --anonymous-auth=false \
  ...
```

#### 2. Enable Certificate-Based Authentication

Configure the kubelet to verify client certificates against the cluster CA:

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
```

The kube-apiserver authenticates to the kubelet using its kubelet client certificate:

```bash
# kube-apiserver flags
--kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
--kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
```

#### 3. Set Authorization Mode to Webhook

By default, kubelet authorization is `AlwaysAllow`. Change to `Webhook` so the kubelet delegates authorization decisions to the API server:

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authorization:
  mode: Webhook
```

With Webhook mode, the kubelet sends a SubjectAccessReview to the API server for every request. Only users/service accounts with appropriate RBAC permissions can access the kubelet API.

#### 4. Disable the Read-Only Port

Port 10255 serves metrics without authentication. Disable it:

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
readOnlyPort: 0
```

#### KubeletConfiguration vs Command-Line Flags

Starting with Kubernetes v1.10, most kubelet parameters moved from command-line flags to a configuration file. If the same parameter is set in both, the command-line flag takes precedence.

```bash
# View the running kubelet configuration
ps -aux | grep kubelet | grep -- --config
# --config=/var/lib/kubelet/config.yaml

# Inspect the config file
cat /var/lib/kubelet/config.yaml
```

| Parameter | CLI Flag | Config File Field |
|---|---|---|
| Anonymous auth | `--anonymous-auth=false` | `authentication.anonymous.enabled: false` |
| Client CA | `--client-ca-file=/path/ca.crt` | `authentication.x509.clientCAFile` |
| Authorization | `--authorization-mode=Webhook` | `authorization.mode: Webhook` |
| Read-only port | `--read-only-port=0` | `readOnlyPort: 0` |
| Static pod path | `--pod-manifest-path=/etc/kubernetes/manifests` | `staticPodPath` |

#### Kubelet Security Checklist

```yaml
# Hardened kubelet configuration
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false          # Reject unauthenticated requests
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
  webhook:
    enabled: true
authorization:
  mode: Webhook             # Delegate to API server
readOnlyPort: 0             # Disable unauthenticated metrics
rotateCertificates: true    # Auto-rotate kubelet certificates
protectKernelDefaults: true # Fail if kernel params don't match defaults
```

> **EKS relevance:** On EKS managed node groups, kubelet configuration is handled by AWS. Anonymous auth is disabled and Webhook authorization is enabled by default. For self-managed nodes, you must configure these settings yourself.

### Verifying Platform Binaries

Before deploying a Kubernetes cluster, verify that downloaded binaries have not been tampered with during transit. Every official release includes SHA-512 checksums on the [Kubernetes GitHub release page](https://github.com/kubernetes/kubernetes/releases).

#### Why Verify?

An attacker with network access could intercept download requests and replace genuine binaries with malicious ones. Since every file has a unique checksum, even a single byte change produces a completely different hash.

#### Verification Steps

```bash
# 1. Download the binary
curl https://dl.k8s.io/v1.30.0/kubernetes.tar.gz -L -o kubernetes.tar.gz

# 2. Generate the checksum locally
# macOS / Linux:
shasum -a 512 kubernetes.tar.gz

# Linux alternative:
sha512sum kubernetes.tar.gz

# 3. Compare with the hash on the release page
# The output must EXACTLY match the published hash.
# A mismatch indicates the file may have been tampered with.
```

| OS | Command | Notes |
|---|---|---|
| macOS / Linux | `shasum -a 512 <file>` | Available on most systems by default |
| Linux | `sha512sum <file>` | Part of `coreutils` |

#### Verifying Individual Component Binaries

You can also verify individual binaries (kubectl, kubeadm, kubelet):

```bash
# Download kubectl and its checksum
curl -LO "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl.sha256"

# Verify (Linux)
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
# Expected output: kubectl: OK
```

> **Production practice:** Automate binary verification in your CI/CD pipeline or infrastructure-as-code tooling. Never deploy binaries that fail checksum validation.

### CIS Benchmarks & kube-bench

The **Center for Internet Security (CIS)** is a nonprofit organization focused on enhancing cybersecurity through community-driven best practices. CIS publishes security benchmarks across 25+ technology categories — operating systems, cloud platforms, network devices, server software, and container orchestration platforms including Kubernetes.

The Kubernetes CIS Benchmark is a set of recommendations for hardening cluster components. **kube-bench** (by Aqua Security) automates checking your cluster against these benchmarks.

#### CIS-CAT (Configuration Assessment Tool)

CIS also provides **CIS-CAT Pro**, an automated assessment tool that compares your system's configuration against CIS benchmarks and generates an HTML report showing:
- Which checks passed and failed
- Scores per category (access control, network, services, filesystems, logging)
- Specific remediation steps for each failure

> CIS-CAT is a commercial tool. For Kubernetes-specific automated checks, kube-bench (open source) is the standard choice.

#### What CIS Benchmarks Cover

| Section | Components Checked |
|---|---|
| 1. Control Plane | API server, controller-manager, scheduler, etcd |
| 2. etcd | Authentication, encryption, peer communication |
| 3. Control Plane Configuration | RBAC, audit logging, admission controllers |
| 4. Worker Nodes | Kubelet configuration, file permissions |
| 5. Policies | Pod security, network policies, secrets management |

Each check has a status:

| Status | Meaning |
|---|---|
| **PASS** | Configuration meets the benchmark |
| **FAIL** | Configuration does not meet the benchmark |
| **WARN** | Manual verification required |
| **INFO** | Informational (no pass/fail) |

#### Installing and Running kube-bench

```bash
# Method 1: Run as a container
docker run --pid=host -v /etc:/etc:ro -v /var:/var:ro \
  -t aquasec/kube-bench:latest run --targets=master

# Method 2: Run as a Kubernetes Job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench

# Method 3: Install binary directly
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.7.3/kube-bench_0.7.3_linux_amd64.tar.gz | tar xz
sudo mv kube-bench /usr/local/bin/

# Run against master node
kube-bench run --targets=master

# Run against worker node
kube-bench run --targets=node

# Run all checks
kube-bench run
```

#### Reading kube-bench Output

```
[INFO] 1 Control Plane Security Configuration
[INFO] 1.1 Control Plane Node Configuration Files
[PASS] 1.1.1 Ensure that the API server pod specification file permissions are set to 644 or more restrictive
[PASS] 1.1.2 Ensure that the API server pod specification file ownership is set to root:root
[FAIL] 1.1.3 Ensure that the controller manager pod specification file permissions are set to 644 or more restrictive
[PASS] 1.1.4 Ensure that the controller manager pod specification file ownership is set to root:root

== Remediations master ==
1.1.3 Run the below command on the control plane node:
chmod 644 /etc/kubernetes/manifests/kube-controller-manager.yaml

== Summary master ==
45 checks PASS
10 checks FAIL
8 checks WARN
0 checks INFO
```

#### Common CIS Remediation Examples

```bash
# Fix file permissions on control plane manifests
chmod 644 /etc/kubernetes/manifests/kube-apiserver.yaml
chmod 644 /etc/kubernetes/manifests/kube-controller-manager.yaml
chmod 644 /etc/kubernetes/manifests/kube-scheduler.yaml
chmod 644 /etc/kubernetes/manifests/etcd.yaml

# Fix ownership
chown root:root /etc/kubernetes/manifests/*.yaml

# Fix kubelet config permissions
chmod 644 /var/lib/kubelet/config.yaml

# Verify etcd data directory permissions
chmod 700 /var/lib/etcd
chown etcd:etcd /var/lib/etcd
```

#### Automating CIS Checks with a CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: kube-bench-scan
  namespace: kube-system
spec:
  schedule: "0 2 * * 1"    # Weekly on Monday at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          hostPID: true
          containers:
          - name: kube-bench
            image: aquasec/kube-bench:v0.7.3
            command: ["kube-bench", "run", "--json"]
            volumeMounts:
            - name: etc
              mountPath: /etc
              readOnly: true
            - name: var
              mountPath: /var
              readOnly: true
          volumes:
          - name: etc
            hostPath:
              path: /etc
          - name: var
            hostPath:
              path: /var
          restartPolicy: Never
```

> **EKS relevance:** AWS manages the control plane on EKS, so master node checks don't apply. Run kube-bench with `--targets=node` on worker nodes. AWS publishes its own EKS CIS Benchmark. Use `kube-bench run --benchmark eks-1.2.0` for EKS-specific checks.

### Cluster Penetration Testing with Kube-hunter

Kube-hunter is an open-source tool from Aqua Security that scans Kubernetes clusters for security vulnerabilities from an attacker's perspective. While kube-bench checks configuration compliance, kube-hunter actively probes for exploitable weaknesses.

**kube-bench vs kube-hunter:**

| Tool | Approach | What It Checks | When to Use |
|---|---|---|---|
| **kube-bench** | Configuration audit | CIS Benchmark compliance (static checks) | After cluster setup, before production |
| **kube-hunter** | Penetration test | Exploitable vulnerabilities (active probing) | Regularly in staging, carefully in production |
| **Trivy** | Image scanning | CVEs in container images | CI/CD pipeline, before deployment |

**Running kube-hunter:**

```bash
# Option 1: Run from outside the cluster (remote scan)
pip install kube-hunter
kube-hunter --remote <cluster-api-endpoint>

# Option 2: Run as a pod inside the cluster (internal scan)
kubectl run kube-hunter --image=aquasec/kube-hunter \
  --restart=Never -- --pod

# Option 3: Run as a Job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: kube-hunter
spec:
  template:
    spec:
      containers:
      - name: kube-hunter
        image: aquasec/kube-hunter
        command: ["kube-hunter"]
        args: ["--pod"]
      restartPolicy: Never
EOF

# View results
kubectl logs job/kube-hunter
```

**Sample output:**

```
Vulnerabilities
+--------+----------------------+----------------------+----------+
| ID     | Location             | Vulnerability        | Severity |
+--------+----------------------+----------------------+----------+
| KHV002 | 10.0.1.5:10250       | Kubelet API exposed  | high     |
| KHV005 | 10.0.1.5:10255       | Read-only Kubelet    | medium   |
|        |                      | port open            |          |
| KHV007 | 10.0.1.5:2379        | etcd accessible      | critical |
| KHV024 | 10.0.1.5:6443        | Dashboard exposed    | high     |
| KHV050 | Pod: kube-hunter     | Access to pod        | low      |
|        |                      | service account      |          |
+--------+----------------------+----------------------+----------+
```

**Common findings and fixes:**

| Finding | Severity | Fix |
|---|---|---|
| Kubelet API exposed (anonymous auth) | High | Set `--anonymous-auth=false` in kubelet config |
| Read-only Kubelet port open | Medium | Set `--read-only-port=0` |
| etcd accessible without TLS | Critical | Enable TLS client auth for etcd |
| Dashboard exposed publicly | High | Remove NodePort/LoadBalancer, use `kubectl proxy` |
| Service account token mounted | Low | Set `automountServiceAccountToken: false` |
| API server allows anonymous access | High | Set `--anonymous-auth=false` on API server |

```bash
# Run kube-hunter in active mode (attempts actual exploits — staging only!)
kube-hunter --remote <endpoint> --active

# Generate JSON report for CI/CD integration
kube-hunter --pod --report json > /tmp/kube-hunter-report.json
```

> Run kube-hunter in passive mode in production (default). Active mode attempts real exploits and can disrupt services — use only in staging or test clusters. Schedule regular scans as a CronJob and alert on new findings.

### Kubernetes Dashboard — Deployment & Security

The Kubernetes Dashboard is a web-based UI for monitoring and managing cluster resources. It can display sensitive data including Secrets, so proper security is essential.

⚠️ **Security incident:** In 2018, Tesla's Kubernetes dashboard was left publicly accessible without authentication. Attackers used it to deploy cryptocurrency mining containers on Tesla's AWS infrastructure.

#### Deploying the Dashboard

```bash
# Deploy the recommended configuration
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Verify deployment
kubectl get all -n kubernetes-dashboard

# Output:
# NAME                                             READY   STATUS    RESTARTS   AGE
# pod/dashboard-metrics-scraper-7b8c9d6e8-abc12    1/1     Running   0          30s
# pod/kubernetes-dashboard-6c75f9d8b-xyz34         1/1     Running   0          30s
#
# NAME                                TYPE        CLUSTER-IP      PORT(S)
# service/dashboard-metrics-scraper   ClusterIP   10.96.45.123    8000/TCP
# service/kubernetes-dashboard        ClusterIP   10.96.78.234    443/TCP
```

The dashboard service is `ClusterIP` by default — accessible only from within the cluster.

#### Accessing the Dashboard

**Method 1: kubectl proxy (recommended for individual access)**

```bash
kubectl proxy
# Starting to serve on 127.0.0.1:8001

# Access in browser:
# http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

**Method 2: kubectl port-forward**

```bash
kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443
# Access: https://localhost:8443
```

**Method 3: NodePort (development only)**

```bash
kubectl -n kubernetes-dashboard edit svc kubernetes-dashboard
# Change type: ClusterIP → type: NodePort
# Access: https://<node-ip>:<node-port>
```

⚠️ **Never expose the dashboard via LoadBalancer or NodePort in production** without additional authentication (OAuth2 Proxy, OIDC).

#### Dashboard Authentication

The dashboard login screen accepts two authentication methods:

**Token-based authentication:**

```bash
# Create a service account for dashboard access
kubectl create serviceaccount dashboard-admin -n kubernetes-dashboard

# Bind it to cluster-admin (full access — use cautiously)
kubectl create clusterrolebinding dashboard-admin-binding \
  --clusterrole=cluster-admin \
  --serviceaccount=kubernetes-dashboard:dashboard-admin

# Generate a token
kubectl create token dashboard-admin -n kubernetes-dashboard --duration=8h
# Copy the token and paste it into the dashboard login screen
```

**For read-only access, bind to a restricted ClusterRole instead:**

```bash
kubectl create clusterrolebinding dashboard-viewer-binding \
  --clusterrole=view \
  --serviceaccount=kubernetes-dashboard:dashboard-admin
```

**Kubeconfig-based authentication:**

Create a kubeconfig file with the service account token and upload it to the dashboard login screen.

#### Dashboard Security Checklist

| Setting | Recommendation |
|---|---|
| Service type | Keep as ClusterIP |
| Access method | `kubectl proxy` or `port-forward` |
| Authentication | Require token or kubeconfig login |
| RBAC | Bind dashboard SA to least-privilege role |
| Network | NetworkPolicy to restrict access to dashboard namespace |
| Skip login | Never enable `--enable-skip-login` in production |

> **EKS relevance:** The Kubernetes Dashboard is not installed by default on EKS. AWS recommends using the AWS Console or `kubectl` for cluster management. If you deploy the dashboard on EKS, follow the same security practices above.

---

## 31.2 Kubernetes Network Security — Deep Dive

Network security in Kubernetes operates at multiple layers. This section consolidates all network security mechanisms.

### Network Security Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 7: Application Security                               │
│  ├── mTLS (Istio/Linkerd service mesh)                       │
│  ├── JWT/OAuth2 authentication                               │
│  └── API Gateway rate limiting                               │
│                                                              │
│  Layer 4: Transport Security                                 │
│  ├── NetworkPolicy (pod-to-pod firewall)                     │
│  ├── Encryption in transit (mTLS, WireGuard)                 │
│  └── Service mesh PeerAuthentication                         │
│                                                              │
│  Layer 3: Network Security                                   │
│  ├── CNI plugin enforcement (Calico, Cilium)                 │
│  ├── AWS Security Groups for Pods                            │
│  └── VPC subnet isolation                                    │
│                                                              │
│  Infrastructure: Node Security                               │
│  ├── Node firewall (iptables, security groups)               │
│  ├── API Server access control                               │
│  └── etcd encryption at rest                                 │
└──────────────────────────────────────────────────────────────┘
```

### 1. Default-Deny NetworkPolicy (Foundation)

By default, all pods can communicate with all other pods. The first step is to deny all traffic and then allow only what's needed.

```yaml
# default-deny-all.yaml — Apply to EVERY namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}          # Applies to ALL pods in namespace
  policyTypes:
  - Ingress
  - Egress
  ingress: []              # Deny all incoming
  egress: []               # Deny all outgoing
```

```bash
kubectl apply -f default-deny-all.yaml

# Now ALL pods in "production" are isolated — no traffic in or out
# You must explicitly allow each communication path
```

### 2. Allow Only Required Traffic

```yaml
# allow-frontend-to-backend.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
      protocol: TCP
---
# allow-backend-to-database.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-database
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - port: 5432
---
# allow-dns-egress.yaml — All pods need DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

```bash
kubectl apply -f allow-frontend-to-backend.yaml
kubectl apply -f allow-backend-to-database.yaml
kubectl apply -f allow-dns-egress.yaml

# Verify: frontend → backend works
kubectl exec -n production deploy/frontend -- curl -s --max-time 3 http://backend:8080/health
# Output: {"status":"ok"}

# Verify: frontend → database is blocked
kubectl exec -n production deploy/frontend -- curl -s --max-time 3 http://database:5432
# Output: curl: (28) Connection timed out
```

### 3. Encryption in Transit

```
┌──────────────────────────────────────────────────────────────┐
│  Without encryption:                                         │
│  Pod A ──── plain text ────► Pod B                           │
│  Anyone on the network can sniff traffic                     │
│                                                              │
│  With mTLS (Istio):                                          │
│  Pod A ──► Envoy sidecar ──── TLS 1.3 ────► Envoy ──► Pod B │
│  Traffic encrypted, identity verified via certificates       │
│                                                              │
│  With WireGuard (Calico/Cilium):                             │
│  Pod A ──── WireGuard tunnel ────► Pod B                     │
│  Node-to-node encryption at kernel level                     │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Enable WireGuard encryption with Calico
kubectl patch felixconfiguration default --type='merge' -p '{"spec":{"wireguardEnabled":true}}'

# Verify WireGuard is active
kubectl get nodes -o yaml | grep -A1 wireguard

# Output:
# projectcalico.org/WireguardPublicKey: <base64-key>

# Enable WireGuard with Cilium
cilium config set enable-wireguard true
```

### 4. AWS Security Groups for Pods (EKS)

On EKS with VPC-CNI, you can assign AWS Security Groups directly to pods:

```yaml
# security-group-policy.yaml
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata:
  name: database-sg
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  securityGroups:
    groupIds:
    - sg-0123456789abcdef0    # AWS Security Group ID
    - sg-0987654321fedcba0
```

```bash
# The pod gets an ENI with the specified security groups
# This allows fine-grained AWS-level network control

kubectl apply -f security-group-policy.yaml

# Verify: Check the pod's network interface
kubectl describe pod -n production -l app=database | grep -A2 "Annotations"

# Output:
# Annotations: vpc.amazonaws.com/pod-eni: [{"eniId":"eni-abc123","ifAddress":"10.0.1.50",...}]
```

### 5. API Server Access Control

```bash
# Restrict API server access to specific CIDR blocks
# In EKS:
aws eks update-cluster-config \
  --name my-k8s-cluster \
  --resources-vpc-config endpointPublicAccess=true,publicAccessCidrs="203.0.113.0/24",endpointPrivateAccess=true

# Enable API server audit logging
# Audit logs record who did what, when, and from where
# On EKS, enable via:
eksctl utils update-cluster-logging \
  --enable-types=audit \
  --cluster=my-k8s-cluster \
  --approve
```

### Network Security Checklist

| # | Action | Layer | Tool |
|---|---|---|---|
| 1 | Default-deny NetworkPolicy in every namespace | L4 | NetworkPolicy |
| 2 | Allow only required pod-to-pod traffic | L4 | NetworkPolicy |
| 3 | Allow DNS egress for all pods | L4 | NetworkPolicy |
| 4 | Enable encryption in transit | L4 | Istio mTLS or WireGuard |
| 5 | Restrict API server access | Infra | EKS public access CIDRs |
| 6 | Enable audit logging | Infra | EKS audit logs |
| 7 | Use Security Groups for Pods | L3 | VPC-CNI SecurityGroupPolicy |
| 8 | Scan for open ports | L4 | `kubectl get svc` (no unneeded NodePorts) |
| 9 | Block egress to internet (where not needed) | L4 | NetworkPolicy egress rules |
| 10 | Use private endpoints for AWS services | Infra | VPC Endpoints |
| 11 | Runtime monitoring for anomalous behavior | Runtime | Falco, Sysdig, Aqua |

### Falco — Runtime Threat Detection

Falco is an open-source runtime security tool (CNCF project) that detects anomalous behavior in containers and Kubernetes. It uses kernel-level system call monitoring (via eBPF or kernel module) to detect threats in real-time.

**What Falco detects:**

| Threat | Example | Falco Rule |
|--------|---------|-----------|
| Shell spawned in container | Attacker runs `bash` inside a pod | `Terminal shell in container` |
| Sensitive file read | Process reads `/etc/shadow` or `/etc/passwd` | `Read sensitive file untrusted` |
| Unexpected outbound connection | Container connects to a crypto mining pool | `Unexpected outbound connection` |
| Binary written to disk | Malware downloaded and saved | `Write below binary dir` |
| Privilege escalation | Process uses `setuid` or `setgid` | `Non sudo setuid` |
| Namespace breakout attempt | Container accesses host filesystem | `Contact K8s API Server From Container` |

**Install Falco on Kubernetes:**

```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.config.slack.webhookurl="https://hooks.slack.com/services/XXX"
```

Falco runs as a DaemonSet on every node, monitoring system calls from all containers.

**How Falco works:**

```
┌──────────────────────────────────────────────┐
│  Node                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Pod A   │  │  Pod B   │  │  Pod C   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │         │
│       ▼              ▼              ▼         │
│  ┌─────────────────────────────────────────┐  │
│  │  Linux Kernel (system calls)            │  │
│  └────────────────┬────────────────────────┘  │
│                   │                           │
│  ┌────────────────▼────────────────────────┐  │
│  │  Falco (eBPF probe / kernel module)     │  │
│  │  - Captures syscalls                    │  │
│  │  - Matches against rules                │  │
│  │  - Generates alerts                     │  │
│  └────────────────┬────────────────────────┘  │
└───────────────────┼───────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Falcosidekick         │
        │  → Slack, PagerDuty,   │
        │    Elasticsearch, etc. │
        └───────────────────────┘
```

**Custom Falco rule — detect kubectl exec into production pods:**

```yaml
# custom-rules.yaml
- rule: Shell Spawned in Production Container
  desc: Detect shell spawned in a production namespace container
  condition: >
    spawned_process and
    container and
    proc.name in (bash, sh, zsh, csh) and
    k8s.ns.name = "production"
  output: >
    Shell spawned in production container
    (user=%user.name pod=%k8s.pod.name ns=%k8s.ns.name
     container=%container.name shell=%proc.name
     parent=%proc.pname cmdline=%proc.cmdline)
  priority: WARNING
  tags: [container, shell, production]
```

```bash
# Apply custom rules
helm upgrade falco falcosecurity/falco \
  --namespace falco \
  --set-file customRules."custom-rules\.yaml"=custom-rules.yaml
```

**Sample Falco alert output:**

```
10:23:45.123456789: Warning Shell spawned in production container
  (user=root pod=webapp-7d8f9-abc12 ns=production
   container=webapp shell=bash parent=runc cmdline=bash)
```

**Falco vs other runtime security tools:**

| Tool | Approach | Strengths | Limitations |
|------|----------|-----------|-------------|
| **Falco** | eBPF/kernel module syscall monitoring | Open-source, CNCF, real-time, low overhead | Rules need tuning to reduce false positives |
| **Tracee** | eBPF syscall tracing | Aqua Security, detailed event capture | Less mature rule ecosystem |
| **Sysdig** | Commercial (Falco-based) | Enterprise features, compliance, UI | Paid |
| **Tetragon** | eBPF (Cilium project) | Kernel-level enforcement (not just detection) | Newer, smaller community |

> **Cross-reference:** Tracee → Section 31.4; Seccomp/AppArmor (preventive controls) → MODULE-21

**Why this matters — stopping lateral movement:**
Without NetworkPolicies, a compromised pod can freely communicate with every other pod in the cluster. An attacker who gains access to one service can reach databases, internal APIs, and secrets stores. Default-deny + explicit allow forces an attacker to break through each policy boundary separately, limiting the blast radius of a breach.

**Interview question: How do you secure network communication in Kubernetes?**
Start with default-deny NetworkPolicies in every namespace, then explicitly allow required traffic paths. This stops lateral movement — a compromised pod can only reach explicitly allowed services. Enable encryption in transit using a service mesh (Istio mTLS) or CNI-level encryption (Calico/Cilium WireGuard). On EKS, use Security Groups for Pods for AWS-level network control. Restrict API server access to known CIDRs and enable audit logging. Block unnecessary egress traffic to prevent data exfiltration.

---

