# Module 14: Docker Content Trust & Image Signing

---

## 14.1 The Problem — How Do You Know an Image Hasn't Been Tampered With?

When you pull an image from a registry, you trust that:
1. The image was published by who it claims to be
2. The image hasn't been modified in transit
3. The image hasn't been replaced by a malicious version

Without verification, any of these can be violated.

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE SUPPLY CHAIN ATTACKS                      │
│                                                              │
│  Attack 1: Man-in-the-Middle                                │
│    Registry ──[attacker modifies image]──► Client           │
│    Client receives a tampered image                         │
│                                                              │
│  Attack 2: Compromised Registry                             │
│    Attacker gains access to registry                        │
│    Replaces legitimate image with malicious one             │
│                                                              │
│  Attack 3: Replay Attack                                    │
│    Attacker serves an old, vulnerable version               │
│    Client thinks it's getting the latest                    │
│                                                              │
│  Solution: Docker Content Trust (DCT)                       │
│    Cryptographically sign images                            │
│    Verify signatures before running                         │
│    Reject unsigned or tampered images                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 14.2 What is Docker Content Trust (DCT)?

Docker Content Trust provides **cryptographic signing and verification** of images. When enabled, Docker will only pull and run **signed images**.

DCT uses **The Update Framework (TUF)** via a component called **Notary**.

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER CONTENT TRUST COMPONENTS                 │
│                                                              │
│  Notary Server                                              │
│    Stores signed metadata (signatures, keys, timestamps)    │
│    Docker Hub has a built-in Notary server                  │
│                                                              │
│  Notary Client                                              │
│    Built into Docker CLI                                    │
│    Signs images during push                                 │
│    Verifies signatures during pull                          │
│                                                              │
│  Keys:                                                      │
│    Root Key      → Master key (offline, most important)     │
│    Repository Key → Signs specific image repositories       │
│    Timestamp Key  → Ensures freshness (prevents replays)    │
│    Snapshot Key   → Signs collection of all tags            │
└─────────────────────────────────────────────────────────────┘
```

---

## 14.3 Enabling Docker Content Trust

### Enable with Environment Variable

```bash
# Enable DCT for the current shell session
$ export DOCKER_CONTENT_TRUST=1

# Now ALL docker pull and docker push commands require signatures
$ docker pull nginx:latest
# Pull (1 of 1): Pulling from library/nginx
# Digest: sha256:abc123...
# Status: Image is up to date for nginx:latest
# Tagging nginx@sha256:abc123... as nginx:latest
# ✅ Signature verified

# Try pulling an unsigned image
$ docker pull someuser/unsigned-image:latest
# Error: remote trust data does not exist
# ❌ Blocked — image is not signed
```

### Disable DCT

```bash
# Disable for the session
$ export DOCKER_CONTENT_TRUST=0

# Or unset the variable
$ unset DOCKER_CONTENT_TRUST

# Or override for a single command
$ DOCKER_CONTENT_TRUST=0 docker pull someuser/unsigned-image:latest
```

---

## 14.4 Signing an Image — Step by Step

### First-Time Signing (Key Generation)

```bash
# Enable DCT
$ export DOCKER_CONTENT_TRUST=1

# Tag your image
$ docker tag myapp:1.0 myregistry/myapp:1.0

# Push (this triggers signing)
$ docker push myregistry/myapp:1.0

# First time: Docker generates keys
# You will be prompted to create passphrases:

# Enter passphrase for new root key with ID abc1234:
# (Enter a strong passphrase — this is your MASTER key)

# Enter passphrase for new repository key with ID def5678:
# (Enter a passphrase for this specific repository)

# Finished initializing "myregistry/myapp"
# Successfully signed myregistry/myapp:1.0
```

### Where Keys Are Stored

```bash
$ ls ~/.docker/trust/private/
# abc1234.key   ← Root key
# def5678.key   ← Repository key

$ ls ~/.docker/trust/tuf/
# myregistry/myapp/   ← Trust metadata for this repo
```

```
┌─────────────────────────────────────────────────────────────┐
│              KEY MANAGEMENT                                  │
│                                                              │
│  Root Key (~/.docker/trust/private/root_keys/)              │
│    ⚠️  MOST IMPORTANT KEY                                   │
│    • Created once, used to sign other keys                  │
│    • Store OFFLINE (USB drive, hardware security module)    │
│    • If compromised, attacker can sign anything             │
│    • If lost, you lose control of your signed images        │
│                                                              │
│  Repository Key (~/.docker/trust/private/)                  │
│    • One per image repository                               │
│    • Used for day-to-day signing                            │
│    • Can be rotated if compromised                          │
│                                                              │
│  Timestamp Key (managed by Notary server)                   │
│    • Auto-rotated                                           │
│    • Ensures metadata freshness                             │
│                                                              │
│  Snapshot Key (managed by Notary server)                    │
│    • Signs the collection of all tags                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 14.5 Pulling Signed Images

```bash
$ export DOCKER_CONTENT_TRUST=1

# Pull a signed image — works
$ docker pull nginx:1.25
# Pull (1 of 1): Pulling from library/nginx
# abc123: Pull complete
# Digest: sha256:...
# Status: Downloaded newer image for nginx:1.25
# Tagging nginx@sha256:... as nginx:1.25

# Pull an unsigned image — blocked
$ docker pull randomuser/untrusted:latest
# Error: remote trust data does not exist for
#   docker.io/randomuser/untrusted
# ❌ Pull rejected

# Pull by digest (bypasses tag-based trust)
$ docker pull nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
# ✅ Works — digest is content-addressable (tamper-proof by nature)
```

---

## 14.6 DCT with docker run

```bash
$ export DOCKER_CONTENT_TRUST=1

# Run a signed image — works
$ docker run -d nginx:1.25
# ✅ Signature verified, container starts

# Run an unsigned image — blocked
$ docker run -d randomuser/untrusted:latest
# Error: remote trust data does not exist
# ❌ Container does NOT start
```

---

## 14.7 Inspecting Trust Data

```bash
# View signing information for an image
$ docker trust inspect --pretty nginx:1.25

# Output:
# Signatures for nginx:1.25
#
# SIGNED TAG   DIGEST                    SIGNERS
# 1.25         abc123def456...           docker-content-trust
#
# List of signers and their keys for nginx:1.25
#
# SIGNER              KEYS
# docker-content-trust abc1234

# View all signed tags for a repository
$ docker trust inspect --pretty nginx

# Output:
# SIGNED TAG   DIGEST                    SIGNERS
# latest       abc123...                 docker-content-trust
# 1.25         def456...                 docker-content-trust
# 1.24         ghi789...                 docker-content-trust
```

---

## 14.8 Key Delegation — Team Signing

In organizations, multiple people need to sign images. DCT supports **delegation** — granting signing rights to team members.

```bash
# Add a signer (delegate)
$ docker trust signer add --key teammate-pub.pem teammate myregistry/myapp

# teammate can now sign images for myregistry/myapp
# They need their own private key to sign

# Remove a signer
$ docker trust signer remove teammate myregistry/myapp

# List signers
$ docker trust inspect --pretty myregistry/myapp
```

```
┌─────────────────────────────────────────────────────────────┐
│              DELEGATION WORKFLOW                             │
│                                                              │
│  Admin (has root key):                                      │
│    1. Creates repository trust                              │
│    2. Adds signers (delegates)                              │
│    3. Stores root key offline                               │
│                                                              │
│  Developer (has delegation key):                            │
│    1. Builds image                                          │
│    2. Signs with their delegation key                       │
│    3. Pushes signed image                                   │
│                                                              │
│  CI/CD Pipeline:                                            │
│    1. Builds image                                          │
│    2. Signs with pipeline delegation key                    │
│    3. Pushes to registry                                    │
│    4. Deployment only accepts signed images                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 14.9 Key Rotation

If a key is compromised, rotate it:

```bash
# Rotate the repository key
$ docker trust key generate new-repo-key
$ docker trust signer add --key new-repo-key.pub new-signer myregistry/myapp

# Remove the compromised signer
$ docker trust signer remove compromised-signer myregistry/myapp

# Root key rotation requires re-initializing trust
# This is why root keys should be stored offline
```

---

## 14.10 DCT in CI/CD Pipelines

```bash
# In your CI/CD pipeline:

# Step 1: Set environment variables
export DOCKER_CONTENT_TRUST=1
export DOCKER_CONTENT_TRUST_REPOSITORY_PASSPHRASE=$REPO_KEY_PASSPHRASE

# Step 2: Build the image
docker build -t myregistry/myapp:$CI_COMMIT_SHA .

# Step 3: Push (automatically signs)
docker push myregistry/myapp:$CI_COMMIT_SHA

# Step 4: In deployment, DCT ensures only signed images run
export DOCKER_CONTENT_TRUST=1
docker pull myregistry/myapp:$CI_COMMIT_SHA
# ✅ Verified and deployed
```

---

## 14.11 DCT vs Cosign — Comparison

```
┌──────────────────┬──────────────────────────────────────────┐
│ Feature          │ DCT (Notary)       │ Cosign (Sigstore)  │
├──────────────────┼────────────────────┼────────────────────┤
│ Built into Docker│ ✅ Yes             │ ❌ Separate tool   │
│ Key management   │ Manual (offline)   │ Keyless option     │
│ Transparency log │ ❌ No              │ ✅ Rekor           │
│ OCI support      │ Docker images only │ Any OCI artifact   │
│ Adoption         │ Docker ecosystem   │ Kubernetes/CNCF    │
│ DCA exam topic   │ ✅ Yes             │ ❌ No              │
│ Complexity       │ Higher             │ Lower              │
└──────────────────┴────────────────────┴────────────────────┘

DCT is the Docker-native solution and the DCA exam topic.
Cosign is the modern industry standard for Kubernetes environments.
```

---

## 14.12 Common Errors and Troubleshooting

### Error 1: "remote trust data does not exist"

```bash
# Error when pulling with DCT enabled:
# Error: remote trust data does not exist for docker.io/someuser/image

# CAUSE: Image is not signed
# Fix Option 1: Disable DCT for this pull
$ DOCKER_CONTENT_TRUST=0 docker pull someuser/image:latest

# Fix Option 2: Use a signed image instead
$ docker pull nginx:1.25   # Official images are signed
```

### Error 2: "could not find necessary signing keys"

```bash
# Error: could not find necessary signing keys

# CAUSE: Repository key is missing from ~/.docker/trust/
# Fix: Re-import the key or generate a new one
$ docker trust key load --name mykey private-key.pem
```

### Error 3: "passphrase is incorrect"

```bash
# Error: passphrase is incorrect

# CAUSE: Wrong passphrase for root or repository key
# Fix: Use the correct passphrase
# If forgotten, you need to re-initialize trust for the repository
```

---

## Module 14 Summary

- Docker Content Trust (DCT) provides cryptographic signing and verification of images
- Enable with `export DOCKER_CONTENT_TRUST=1` — all pull/push/run operations require signatures
- DCT uses Notary (based on The Update Framework) to manage trust metadata
- First push with DCT enabled generates root key and repository key — protect the root key offline
- Signed images include: publisher identity, content integrity, and freshness guarantees
- `docker trust inspect --pretty` shows signing information for an image
- Key delegation allows team members to sign images without sharing the root key
- `docker trust signer add/remove` manages signing delegation
- In CI/CD, set `DOCKER_CONTENT_TRUST_REPOSITORY_PASSPHRASE` for automated signing
- Pulling by digest (`@sha256:...`) is inherently tamper-proof — content-addressable
- DCT blocks unsigned images from being pulled or run when enabled
- Root key compromise is catastrophic — store offline, rotate if needed
- DCT is the DCA exam topic; Cosign/Sigstore is the modern Kubernetes-native alternative

---

**Previous Module: [Module 13 - Docker Daemon Configuration](module-13-daemon-config.md)**

**Next Module: [Module 15 - Docker Secrets in Swarm](module-15-secrets.md)**
