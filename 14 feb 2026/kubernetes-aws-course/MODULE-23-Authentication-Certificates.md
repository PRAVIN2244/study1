# MODULE 23: Authentication, TLS Certificates & KubeConfig

---

## 23.1 Authentication & Certificates

### OIDC Connector in Kubernetes — Authenticate Users via Identity Provider

OIDC (OpenID Connect) lets you authenticate kubectl users via an external identity provider (Azure AD, Google, Okta, Keycloak) instead of managing client certificates manually.

```
┌──────────────────────────────────────────────────────────────┐
│  OIDC Authentication Flow                                    │
│                                                              │
│  1. User runs: kubectl get pods                              │
│  2. kubectl redirects to Identity Provider (IdP) login page  │
│  3. User authenticates (SSO, MFA, etc.)                      │
│  4. IdP returns a JWT token (ID token)                       │
│  5. kubectl sends the JWT token to API Server                │
│  6. API Server validates the JWT:                            │
│     - Checks signature against IdP's public keys             │
│     - Checks token expiry                                    │
│     - Extracts username + groups from claims                 │
│  7. RBAC checks: Does this user/group have permission?       │
│  8. Request proceeds or is denied                            │
│                                                              │
│  User ──► kubectl ──► IdP (login) ──► JWT token              │
│                                          │                   │
│                                          ▼                   │
│                              API Server (validates JWT)      │
│                                          │                   │
│                                          ▼                   │
│                              RBAC (checks permissions)       │
└──────────────────────────────────────────────────────────────┘
```

**Configuring OIDC on the API Server (kubeadm):**

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml (add these flags)
spec:
  containers:
  - command:
    - kube-apiserver
    - --oidc-issuer-url=https://accounts.google.com        # Or Azure AD, Okta, Keycloak
    - --oidc-client-id=my-k8s-cluster                      # OAuth2 client ID
    - --oidc-username-claim=email                           # JWT claim for username
    - --oidc-groups-claim=groups                            # JWT claim for groups
    - --oidc-username-prefix=oidc:                          # Prefix to avoid conflicts
    - --oidc-groups-prefix=oidc:                            # Prefix for groups
```

**Configuring OIDC on EKS:**

```bash
# EKS uses its own OIDC provider for IRSA (pod identity)
# For user authentication, EKS uses aws-iam-authenticator by default
# To add OIDC for user auth, use an identity provider association:

aws eks associate-identity-provider-config \
  --cluster-name my-k8s-cluster \
  --oidc \
  --identity-provider-config \
    identityProviderConfigName=AzureAD,\
    issuerUrl=https://login.microsoftonline.com/<tenant-id>/v2.0,\
    clientId=<app-client-id>,\
    usernameClaim=email,\
    groupsClaim=groups
```

**kubeconfig for OIDC users:**

```yaml
# ~/.kube/config
users:
- name: oidc-user
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: kubectl
      args:
      - oidc-login
      - get-token
      - --oidc-issuer-url=https://accounts.google.com
      - --oidc-client-id=my-k8s-cluster
      - --oidc-client-secret=<secret>
```

```bash
# Install kubelogin (OIDC helper for kubectl)
# For Azure AD:
kubectl krew install oidc-login

# Test authentication
kubectl get pods --user=oidc-user

# Output (if RBAC not configured):
# Error from server (Forbidden): pods is forbidden: User "oidc:user@example.com"
# cannot list resource "pods" in API group "" in the namespace "default"

# Grant permissions via RBAC
kubectl create clusterrolebinding oidc-admin \
  --clusterrole=cluster-admin \
  --user="oidc:user@example.com"
```

**OIDC vs other auth methods:**

| Method | Use Case | Token Expiry | MFA Support |
|---|---|---|---|
| **OIDC** | Enterprise SSO (Azure AD, Okta) | Short-lived (1h) | Yes (via IdP) |
| **Client certificates** | Admin access, CI/CD | Long-lived (1 year) | No |
| **ServiceAccount tokens** | Pod-to-API access | Configurable | No |
| **AWS IAM (EKS)** | AWS-native teams | Session-based | Yes (via AWS) |

**Interview question: What is OIDC in Kubernetes and why use it?**
OIDC (OpenID Connect) allows Kubernetes to authenticate users via external identity providers (Azure AD, Google, Okta) using JWT tokens. The API server validates the JWT signature, extracts username/groups from claims, and passes them to RBAC for authorization. Use OIDC when you want centralized user management, SSO, MFA, and short-lived tokens instead of managing client certificates manually.

### TLS Fundamentals

TLS (Transport Layer Security) secures communication between clients and servers. Understanding TLS is a prerequisite for Kubernetes certificate management.

**Symmetric vs Asymmetric Encryption:**

| | Symmetric | Asymmetric |
|---|---|---|
| **Keys** | One shared key for encrypt + decrypt | Key pair: public key + private key |
| **Speed** | Fast | Slow |
| **Problem** | How to share the key securely? | Solves the key-sharing problem |
| **Use** | Bulk data encryption | Key exchange, authentication |

In practice, TLS uses both: asymmetric encryption to securely exchange a symmetric key, then symmetric encryption for the actual data transfer.

**HTTPS Handshake Flow:**

```
1. Client connects to server (HTTPS)
2. Server sends its certificate (contains public key)
3. Client verifies certificate against trusted CAs
4. Client generates a random symmetric key
5. Client encrypts the symmetric key with server's public key
6. Server decrypts using its private key → both sides now share the symmetric key
7. All subsequent data is encrypted with the symmetric key
```

**One-Way SSL vs Mutual TLS (mTLS):**

The handshake above is **one-way SSL** — only the client verifies the server's identity. The server authenticates the client through other means (username/password, tokens). This is how browsers connect to websites.

In **mutual TLS (mTLS)**, both sides present and verify certificates:

| | One-Way SSL | Mutual TLS (mTLS) |
|---|---|---|
| **Client verifies server** | Yes | Yes |
| **Server verifies client** | No (uses passwords/tokens) | Yes (via client certificate) |
| **Use case** | Browsers → web servers | Service-to-service, B2B, Kubernetes components |
| **Example** | User accessing online banking | API server ↔ kubelet, Istio pod-to-pod |

Kubernetes uses mTLS internally — the API server verifies kubelet certificates, and kubelets verify the API server's certificate. Service meshes like Istio extend mTLS to all pod-to-pod traffic (see [MODULE-35](MODULE-35-Service-Mesh.md)).

**SSH Key Pair — Simpler Example:**

```bash
# Generate an SSH key pair
ssh-keygen -t rsa -b 2048
# Creates: id_rsa (private key) and id_rsa.pub (public key)

# Copy public key to the server
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys   # On the server

# Connect using the private key
ssh -i id_rsa user1@server1
```

The private key stays with you. The public key goes to every server you need access to. Anyone with the public key cannot derive the private key.

**Generating Keys with OpenSSL:**

```bash
# Generate a private key
openssl genrsa -out server.key 2048

# Extract the public key from the private key
openssl rsa -in server.key -pubout > server.pem
```

**Certificate Authorities (CAs):**

A CA is a trusted third party that signs certificates. Browsers ship with pre-installed CA public keys (DigiCert, Let's Encrypt, GlobalSign, etc.). The signing process:

```
1. You generate a private key + CSR (Certificate Signing Request)
2. You send the CSR to a CA
3. CA validates your identity and domain ownership
4. CA signs the certificate with its private key
5. You install the signed certificate on your server
6. Browsers verify the certificate using the CA's public key (pre-installed)
```

```bash
# Generate a CSR
openssl req -new -key server.key -out server.csr \
  -subj "/C=US/ST=CA/O=MyOrg/CN=myapp.example.com"

# Self-sign (for testing — browsers will show a warning)
openssl x509 -req -in server.csr -signkey server.key -out server.crt -days 365
```

For internal systems (corporate apps, Kubernetes clusters), organizations run their own private CA and distribute its public key to all machines.

**Certificate File Naming Conventions:**

| Extension | Contains | Examples |
|---|---|---|
| `.crt`, `.pem` | Public key / certificate | `server.crt`, `ca.pem`, `client.crt` |
| `.key`, `-key.pem` | Private key | `server.key`, `server-key.pem`, `ca.key` |
| `.csr` | Certificate Signing Request | `server.csr` |

Rule of thumb: if the filename contains "key", it's a private key. Everything else (`.crt`, `.pem`) is a certificate or public key.

### Creating Kubernetes TLS Certificates with OpenSSL

This section walks through generating all the certificates a Kubernetes cluster needs, from the CA down to individual component certificates.

#### Step 1: Generate the CA Certificate

The CA is the root of trust. All other certificates are signed by it.

```bash
# 1. Generate CA private key
openssl genrsa -out ca.key 2048

# 2. Create a CSR for the CA
openssl req -new -key ca.key -subj "/CN=KUBERNETES-CA" -out ca.csr

# 3. Self-sign the CA certificate
openssl x509 -req -in ca.csr -signkey ca.key -out ca.crt -days 3650
```

This produces `ca.key` (private — guard carefully) and `ca.crt` (public — distributed to all components).

#### Step 2: Generate Client Certificates

Client certificates authenticate components that connect TO the API server. Each certificate is signed by the CA (not self-signed).

**Admin user:**

```bash
openssl genrsa -out admin.key 2048
openssl req -new -key admin.key -subj "/CN=kube-admin/O=system:masters" -out admin.csr
openssl x509 -req -in admin.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out admin.crt -days 365
```

The `/O=system:masters` group gives this certificate cluster-admin privileges via the built-in ClusterRoleBinding.

**Other client certificates follow the same pattern:**

| Component | CN | O (Group) |
|---|---|---|
| Admin | `kube-admin` | `system:masters` |
| Scheduler | `system:kube-scheduler` | — |
| Controller Manager | `system:kube-controller-manager` | — |
| Kube Proxy | `system:kube-proxy` | — |
| Kubelet (per node) | `system:node:node01` | `system:nodes` |

Kubelet certificates use the `system:node:` prefix so the Node authorizer can identify them. Each node gets its own certificate with its hostname in the CN.

**Using a client certificate to call the API server directly:**

```bash
curl https://kube-apiserver:6443/api/v1/pods \
  --key admin.key \
  --cert admin.crt \
  --cacert ca.crt
```

```json
{
  "kind": "PodList",
  "apiVersion": "v1",
  "items": []
}
```

In practice, these credentials are stored in a kubeconfig file so you don't pass them on every command.

#### Step 3: Generate the API Server Certificate with SANs

The API server is accessed by many names (DNS and IP). All must be listed as Subject Alternative Names (SANs), or TLS verification fails.

Create an OpenSSL config file:

```ini
# openssl-apiserver.cnf
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster.local
IP.1 = 10.96.0.1
IP.2 = 172.17.0.87
```

```bash
openssl genrsa -out apiserver.key 2048
openssl req -new -key apiserver.key -subj "/CN=kube-apiserver" \
  -out apiserver.csr -config openssl-apiserver.cnf
openssl x509 -req -in apiserver.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out apiserver.crt -days 365 \
  -extensions v3_req -extfile openssl-apiserver.cnf
```

If a name or IP is missing from the SAN list, clients connecting via that name get a TLS error.

#### Step 4: ETCD Peer Certificates (HA Clusters)

In multi-node ETCD clusters, each member needs peer certificates for inter-member communication:

```bash
# etcd.yaml excerpt — peer certificate configuration
- --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
- --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
- --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
- --peer-client-cert-auth=true
```

### Inspecting Certificates in an Existing Cluster

When joining a team or troubleshooting, you need to audit the cluster's certificate health.

#### Identifying Certificate Files

**kubeadm clusters** — components run as static pods, certificates in manifests:

```bash
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -E "cert|key|ca"
```

**Manual (non-kubeadm) clusters** — components run as systemd services:

```bash
cat /etc/systemd/system/kube-apiserver.service | grep -E "cert|key|ca"
```

#### Building a Certificate Inventory

For each certificate, record: file path, CN, SANs, issuer, expiry.

```bash
# Quick script to audit all certificates in /etc/kubernetes/pki/
for cert in /etc/kubernetes/pki/*.crt /etc/kubernetes/pki/etcd/*.crt; do
  echo "=== $cert ==="
  openssl x509 -in "$cert" -noout -subject -issuer -dates 2>/dev/null
  echo
done
```

```
=== /etc/kubernetes/pki/apiserver.crt ===
subject=CN = kube-apiserver
issuer=CN = kubernetes
notBefore=Apr 17 10:00:00 2024 GMT
notAfter=Apr 17 10:00:00 2025 GMT

=== /etc/kubernetes/pki/ca.crt ===
subject=CN = kubernetes
issuer=CN = kubernetes
notBefore=Apr 17 10:00:00 2024 GMT
notAfter=Apr 14 10:00:00 2034 GMT

=== /etc/kubernetes/pki/etcd/server.crt ===
subject=CN = controlplane
issuer=CN = etcd-ca
notBefore=Apr 17 10:00:00 2024 GMT
notAfter=Apr 17 10:00:00 2025 GMT
```

#### Troubleshooting with Logs

**kubeadm clusters** — use `crictl` (or `docker` on older clusters):

```bash
# When kubectl is down, check container status directly
crictl ps -a | grep -E "kube-apiserver|etcd"

# View logs
crictl logs <container-id> 2>&1 | tail -20
```

**Non-kubeadm clusters** — use `journalctl`:

```bash
journalctl -u etcd.service -l --no-pager | tail -20
```

Common TLS errors in logs:

| Error Message | Cause | Fix |
|---|---|---|
| `tls: bad certificate` | Client cert not signed by expected CA | Check `--trusted-ca-file` points to correct CA |
| `certificate signed by unknown authority` | Wrong CA file referenced | Ensure `--etcd-cafile` uses ETCD's CA, not cluster CA |
| `no such file or directory` | Wrong certificate path in manifest | Verify file exists with `ls`, fix path in manifest |
| `x509: certificate has expired` | Certificate past its validity | Run `kubeadm certs renew all` |

### Kubernetes Certificate Infrastructure

Kubernetes uses TLS certificates extensively for authentication and secure communication between components.

```
┌──────────────────────────────────────────────────────────────┐
│  Certificate Types in Kubernetes                             │
│                                                              │
│  1. Cluster CA Certificate                                   │
│     └── Root of trust — signs all other certificates         │
│     └── Located at /etc/kubernetes/pki/ca.crt (kubeadm)      │
│                                                              │
│  2. Server Certificates (presented by servers)               │
│     ├── API Server cert    → clients verify API server       │
│     ├── etcd server cert   → API server verifies etcd        │
│     └── kubelet cert       → API server verifies kubelet     │
│                                                              │
│  3. Client Certificates (presented by clients)               │
│     ├── kubectl user cert  → API server authenticates user   │
│     ├── kubelet client cert→ API server authenticates kubelet│
│     ├── scheduler cert     → API server authenticates sched. │
│     └── controller-mgr cert→ API server authenticates ctrl-m │
│                                                              │
│  All signed by the same Cluster CA                           │
└──────────────────────────────────────────────────────────────┘
```

**Per-component certificate pairs:**

| Component | Role | Certificate | Key |
|---|---|---|---|
| **Cluster CA** | Root of trust | `ca.crt` | `ca.key` |
| **ETCD CA** | ETCD root of trust | `etcd/ca.crt` | `etcd/ca.key` |
| **API Server** | Server | `apiserver.crt` | `apiserver.key` |
| **ETCD Server** | Server | `etcd/server.crt` | `etcd/server.key` |
| **Kubelet** | Server | `kubelet.crt` | `kubelet.key` |
| **Admin (kubectl)** | Client | `admin.crt` | `admin.key` |
| **Scheduler** | Client | `scheduler.crt` | `scheduler.key` |
| **Controller Manager** | Client | `controller-manager.crt` | `controller-manager.key` |
| **Kube Proxy** | Client | `kube-proxy.crt` | `kube-proxy.key` |
| **API Server → ETCD** | Client | `apiserver-etcd-client.crt` | `apiserver-etcd-client.key` |
| **API Server → Kubelet** | Client | `apiserver-kubelet-client.crt` | `apiserver-kubelet-client.key` |

The API server is unique — it acts as both a **server** (clients like kubectl, scheduler, controller-manager connect to it) and a **client** (it connects to ETCD and kubelet). This is why it has separate certificate pairs for each role.

**Certificate Authorities:** Kubernetes clusters use at least one CA. ETCD can optionally use its own separate CA (`etcd/ca.crt`) for additional isolation. All component certificates must be signed by the appropriate CA — cluster components by the cluster CA, ETCD components by the ETCD CA.

```bash
# View cluster certificates (kubeadm clusters)
ls /etc/kubernetes/pki/

# Output:
# ca.crt              ca.key               ← Cluster CA
# apiserver.crt       apiserver.key        ← API Server certificate
# apiserver-kubelet-client.crt             ← API Server → kubelet client cert
# front-proxy-ca.crt  front-proxy-ca.key   ← Front proxy CA
# etcd/ca.crt         etcd/server.crt      ← etcd certificates
# sa.key              sa.pub               ← Service account signing key

# Check certificate expiration
kubeadm certs check-expiration

# Output:
# CERTIFICATE                EXPIRES                  RESIDUAL TIME
# admin.conf                 Jan 15, 2026 12:00 UTC   364d
# apiserver                  Jan 15, 2026 12:00 UTC   364d
# controller-manager.conf    Jan 15, 2026 12:00 UTC   364d
# etcd-server                Jan 15, 2026 12:00 UTC   364d

# Renew all certificates
kubeadm certs renew all
```

#### Inspecting Certificate Details with OpenSSL

Use `openssl x509` to examine any certificate's issuer, subject, SANs, and validity:

```bash
# Inspect the API server certificate
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout
```

```
Certificate:
  Data:
    Issuer: CN = kubernetes
    Subject: CN = kube-apiserver
    Validity
      Not Before: Apr 17 10:00:00 2024 GMT
      Not After : Apr 17 10:00:00 2025 GMT
    X509v3 Subject Alternative Name:
      DNS:controlplane, DNS:kubernetes, DNS:kubernetes.default,
      DNS:kubernetes.default.svc, DNS:kubernetes.default.svc.cluster.local,
      IP Address:10.96.0.1, IP Address:10.46.98.9
```

Key observations:
- **Issuer: CN = kubernetes** — signed by the cluster CA
- **Subject: CN = kube-apiserver** — identifies this as the API server cert
- **SAN list** — all names/IPs the API server is reachable at. If a name is missing (e.g., `kube-master`), clients using that name will get TLS errors
- **Validity** — API server certs are typically valid for 1 year

```bash
# Inspect the ETCD server certificate
openssl x509 -in /etc/kubernetes/pki/etcd/server.crt -text -noout
```

```
Certificate:
  Data:
    Issuer: CN = etcd-ca
    Subject: CN = controlplane
    Validity
      Not Before: Apr 17 10:00:00 2024 GMT
      Not After : Apr 17 10:00:00 2025 GMT
```

Note: ETCD uses its own CA (`etcd-ca`), separate from the cluster CA (`kubernetes`).

```bash
# Inspect the root CA certificate (valid for ~10 years)
openssl x509 -in /etc/kubernetes/pki/ca.crt -text -noout | grep -A2 "Validity"
#   Validity
#     Not Before: Apr 17 10:00:00 2024 GMT
#     Not After : Apr 14 10:00:00 2034 GMT
```

#### API Server Certificate Flags

The kube-apiserver manifest maps certificate flags to specific communication channels:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml (certificate-related flags)
spec:
  containers:
  - command:
    - kube-apiserver
    # --- API Server's own serving certificate ---
    - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
    - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
    # --- CA used to verify client certificates ---
    - --client-ca-file=/etc/kubernetes/pki/ca.crt
    # --- Certificates for API Server → ETCD communication ---
    - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
    - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
    - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
    # --- Certificates for API Server → Kubelet communication ---
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
    - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
    # --- Front proxy certificates (for aggregation layer) ---
    - --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt
    - --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key
    - --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt
```

#### ETCD Server Certificate Flags

```yaml
# /etc/kubernetes/manifests/etcd.yaml (certificate-related flags)
spec:
  containers:
  - command:
    - etcd
    # --- ETCD's own serving certificate ---
    - --cert-file=/etc/kubernetes/pki/etcd/server.crt
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    # --- CA used to verify client certificates ---
    - --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --client-cert-auth=true
    # --- Peer-to-peer certificates (multi-node etcd) ---
    - --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
    - --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
    - --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
```

**Certificate overview:**

| Component | Certificate File | Key File | Issuer |
|---|---|---|---|
| Cluster CA | `/etc/kubernetes/pki/ca.crt` | `/etc/kubernetes/pki/ca.key` | Self-signed |
| API Server (serving) | `/etc/kubernetes/pki/apiserver.crt` | `/etc/kubernetes/pki/apiserver.key` | kubernetes |
| API Server → ETCD | `/etc/kubernetes/pki/apiserver-etcd-client.crt` | `/etc/kubernetes/pki/apiserver-etcd-client.key` | etcd-ca |
| API Server → Kubelet | `/etc/kubernetes/pki/apiserver-kubelet-client.crt` | `/etc/kubernetes/pki/apiserver-kubelet-client.key` | kubernetes |
| ETCD Server | `/etc/kubernetes/pki/etcd/server.crt` | `/etc/kubernetes/pki/etcd/server.key` | etcd-ca |
| ETCD CA | `/etc/kubernetes/pki/etcd/ca.crt` | `/etc/kubernetes/pki/etcd/ca.key` | Self-signed |
| Front Proxy | `/etc/kubernetes/pki/front-proxy-client.crt` | `/etc/kubernetes/pki/front-proxy-client.key` | front-proxy-ca |

#### Lab: Troubleshooting Certificate Issues

A common scenario: after modifying control plane manifests, `kubectl` stops working.

**Step 1: kubectl fails**

```bash
kubectl get pods
# The connection to the server controlplane:6443 was refused -
#   did you specify the right host or port?
```

**Step 2: Check if the API server container is running**

```bash
# On kubeadm clusters, use crictl (or docker on older clusters)
crictl ps -a | grep kube-apiserver
# Shows the container is restarting or exited

crictl logs <container-id> 2>&1 | tail -20
# error while dialing TCP 127.0.0.1:2379
```

Port 2379 is ETCD. The API server can't connect to ETCD.

**Step 3: Check ETCD logs**

```bash
crictl ps -a | grep etcd
crictl logs <etcd-container-id> 2>&1 | tail -10
# open /etc/kubernetes/pki/etcd/server-certificate.crt: no such file or directory
```

The ETCD manifest references a wrong certificate filename.

**Step 4: Fix the ETCD manifest**

```bash
ls /etc/kubernetes/pki/etcd/
# ca.crt  ca.key  healthcheck-client.crt  healthcheck-client.key
# peer.crt  peer.key  server.crt  server.key

# The correct file is server.crt, not server-certificate.crt
vi /etc/kubernetes/manifests/etcd.yaml
# Fix: --cert-file=/etc/kubernetes/pki/etcd/server.crt
```

After saving, kubelet detects the manifest change and restarts the ETCD pod. The API server then reconnects.

```bash
# Wait ~30 seconds for pods to restart, then verify
kubectl get nodes
# NAME           STATUS   ROLES           AGE   VERSION
# controlplane   Ready    control-plane   41m   v1.30.0
```

⚠️ If you see `certificate signed by unknown authority` in API server logs, check that `--etcd-cafile` points to `/etc/kubernetes/pki/etcd/ca.crt` (ETCD's CA), not the cluster CA.

**How certificate authentication works:**

```
1. User presents client certificate to API Server
2. API Server checks: Is this cert signed by the Cluster CA?
3. API Server extracts: CN (Common Name) = username, O (Organization) = group
4. RBAC checks: Does this user/group have permission for the requested action?
```

| Certificate Field | Kubernetes Mapping | Example |
|---|---|---|
| `CN` (Common Name) | Username | `/CN=adam` → user "adam" |
| `O` (Organization) | Group | `/O=eng` → group "eng" |
| `O` (multiple) | Multiple groups | `/O=eng/O=devops` → groups "eng" and "devops" |

### Authenticating a User with Certificates

Step-by-step process to create a Kubernetes user via X.509 certificates:

```bash
# 1. Create a private key
openssl genrsa -out adam.key 2048

# 2. Create a Certificate Signing Request (CSR)
openssl req -new -key adam.key -out adam.csr -subj "/CN=adam/O=eng"

# 3. Base64-encode the CSR
cat adam.csr | base64 | tr -d '\n'
```

```yaml
# 4. Create a CertificateSigningRequest in Kubernetes
# adam-csr.yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: adamcsr
spec:
  request: <base64-encoded-CSR>
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400    # 1 day
  usages:
  - client auth
```

```bash
kubectl apply -f adam-csr.yaml

kubectl get csr
# Output:
# NAME      AGE   SIGNERNAME                            REQUESTOR           REQUESTEDDURATION   CONDITION
# adamcsr   10s   kubernetes.io/kube-apiserver-client   admin@example.com   24h                 Pending

# 5. Approve the CSR
kubectl certificate approve adamcsr
# certificatesigningrequest.certificates.k8s.io/adamcsr approved

kubectl get csr
# Output:
# NAME      AGE   SIGNERNAME                            REQUESTOR           REQUESTEDDURATION   CONDITION
# adamcsr   30s   kubernetes.io/kube-apiserver-client   admin@example.com   24h                 Approved,Issued

# 6. Export the signed certificate
kubectl get csr adamcsr -o jsonpath='{.status.certificate}' | base64 -d > adam.crt

# 7. Add user to kubeconfig
kubectl config set-credentials adam \
  --client-key=adam.key \
  --client-certificate=adam.crt \
  --embed-certs=true
kubectl config set-context adam --cluster=minikube --user=adam

# 8. Test — user has no permissions yet
kubectl auth can-i list pods --as adam
# Output: no
```

Then create a Role and RoleBinding (see examples above) to grant permissions to the user.

```bash
# After binding a role:
kubectl get pods --as adam                    # Works (if role allows)
kubectl get pods -n kube-system --as adam     # Fails (role is namespace-scoped)
```

**Who signs the certificate?** The Controller Manager handles all CSR operations via two built-in controllers:

- **CSR-Approving** — auto-approves CSRs that meet certain criteria (e.g., kubelet bootstrap)
- **CSR-Signing** — signs approved CSRs using the CA key pair

The Controller Manager needs access to the CA files to sign certificates:

```bash
cat /etc/kubernetes/manifests/kube-controller-manager.yaml | grep cluster-signing
#   --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
#   --cluster-signing-key-file=/etc/kubernetes/pki/ca.key
```

**Denying a CSR:**

```bash
kubectl certificate deny baduser-csr
# certificatesigningrequest.certificates.k8s.io/baduser-csr denied

# Delete a CSR
kubectl delete csr baduser-csr
```

---

## 23.2 KubeConfig — Managing Cluster Access


The kubeconfig file (`~/.kube/config`) stores connection details for one or more clusters. Instead of passing `--server`, `--client-certificate`, and `--client-key` on every `kubectl` command, kubeconfig organizes these into three sections:

```yaml
# ~/.kube/config
apiVersion: v1
kind: Config
current-context: dev-cluster

clusters:
- name: dev-cluster
  cluster:
    server: https://dev-controlplane:6443
    certificate-authority-data: <base64-ca-cert>
- name: prod-cluster
  cluster:
    server: https://prod-controlplane:6443
    certificate-authority-data: <base64-ca-cert>

users:
- name: dev-admin
  user:
    client-certificate-data: <base64-client-cert>
    client-key-data: <base64-client-key>
- name: prod-admin
  user:
    client-certificate-data: <base64-client-cert>
    client-key-data: <base64-client-key>

contexts:
- name: dev-cluster
  context:
    cluster: dev-cluster
    user: dev-admin
    namespace: default
- name: prod-cluster
  context:
    cluster: prod-cluster
    user: prod-admin
    namespace: production
```

**The three sections:**

| Section | What it stores | Key fields |
|---|---|---|
| `clusters` | API server endpoints + CA certs | `server`, `certificate-authority-data` |
| `users` | Authentication credentials | `client-certificate-data`, `client-key-data`, `token` |
| `contexts` | Cluster + user + namespace combinations | `cluster`, `user`, `namespace` |

A **context** links a cluster to a user and optionally a default namespace. `current-context` determines which context `kubectl` uses by default.

**Managing contexts:**

```bash
# View kubeconfig
kubectl config view

# View only the current context
kubectl config current-context
# Output: dev-cluster

# List all contexts
kubectl config get-contexts
# Output:
# CURRENT   NAME           CLUSTER        AUTHINFO      NAMESPACE
# *         dev-cluster    dev-cluster    dev-admin     default
#           prod-cluster   prod-cluster   prod-admin    production

# Switch to a different context
kubectl config use-context prod-cluster
# Output: Switched to context "prod-cluster".

# Set default namespace for current context
kubectl config set-context --current --namespace=kube-system
```

**Building a kubeconfig imperatively:**

```bash
# Add a cluster
kubectl config set-cluster my-cluster \
  --server=https://controlplane:6443 \
  --certificate-authority=/etc/kubernetes/pki/ca.crt

# Add user credentials
kubectl config set-credentials admin \
  --client-certificate=/etc/kubernetes/pki/admin.crt \
  --client-key=/etc/kubernetes/pki/admin.key

# Create a context linking cluster + user
kubectl config set-context admin@my-cluster \
  --cluster=my-cluster \
  --user=admin \
  --namespace=default

# Switch to the new context
kubectl config use-context admin@my-cluster
```

**Using a non-default kubeconfig:**

```bash
# Specify a different kubeconfig file
kubectl get nodes --kubeconfig=/root/my-custom-config

# Merge multiple kubeconfig files
export KUBECONFIG=~/.kube/config:/root/other-config
kubectl config get-contexts    # Shows contexts from both files
```

**Troubleshooting kubeconfig issues:**

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on port 9999 | Wrong port in `clusters[].cluster.server` | Change to `:6443` (default API server port) |
| `certificate signed by unknown authority` | Wrong CA cert or missing `certificate-authority-data` | Verify CA matches the cluster's `/etc/kubernetes/pki/ca.crt` |
| `Unauthorized` | Wrong client cert/key or expired token | Regenerate credentials, check cert expiry with `openssl x509 -in cert.crt -noout -dates` |
| `no configuration has been provided` | Missing kubeconfig file | Set `KUBECONFIG` env var or copy to `~/.kube/config` |

> **CKA Exam Tip:** Kubeconfig troubleshooting questions typically involve a wrong server port (e.g., 9999 instead of 6443) or a wrong cluster name. Use `kubectl config view` to inspect the file and compare the `server` field against the actual API server address.

---

