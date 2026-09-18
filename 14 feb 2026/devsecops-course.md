# ══════════════════════════════════════════════════════════════
#                  DEVSECOPS — COMPLETE COURSE
# ══════════════════════════════════════════════════════════════

---

## COURSE OVERVIEW

```
Course Title  : DevSecOps — Security-Integrated Software Delivery
Level         : Beginner → Intermediate
Duration      : 16 hours (4 Modules × 4 hours)
Prerequisites : Basic Linux, Git, Docker, CI/CD awareness
Delivery      : Theory + Hands-On Labs + Pipeline Projects
```

---

## COURSE MAP

```
MODULE 1                    MODULE 2                    MODULE 3                    MODULE 4
Core Security               Code & Dependency           Container & Image           End-to-End
Concepts                    Security                    Security                    Pipeline
─────────────               ─────────────               ─────────────               ─────────────
├─ Unit 1.1                 ├─ Unit 2.1                 ├─ Unit 3.1                 ├─ Unit 4.1
│  Application              │  Static Analysis          │  Image Scanning           │  Pipeline
│  Security Testing         │  with SonarQube           │  with Trivy               │  Architecture
│  ├─ L1: SAST vs DAST      │  ├─ L1: Quality Gate      │  ├─ L1: Trivy Scanning    │  ├─ L1: Stage Design
│  ├─ L2: False Pos/Neg     │  ├─ L2: Quality Profile   │  ├─ L2: CIS Benchmarks   │  ├─ L2: Fail/Pass
│  └─ L3: Shift Left        │  └─ L3: Hardcoded Keys    │  └─ L3: Docker Bench     │  │  Criteria
│                           │                           │                           │  └─ L3: Notifications
├─ Unit 1.2                 ├─ Unit 2.2                 ├─ Unit 3.2                 │
│  Dependency &             │  Secret Scanning          │  Image Hardening          ├─ Unit 4.2
│  Composition              │  & Pre-commit             │  & Optimization           │  Complete
│  ├─ L1: SCA               │  ├─ L1: Talisman Setup    │  ├─ L1: Hardening         │  Jenkinsfile
│  ├─ L2: SBOM              │  ├─ L2: .talismanrc       │  ├─ L2: Base Image        │  ├─ L1: 9-Stage
│  └─ L3: VAPT              │  └─ L3: History Rewrite   │  │  Selection             │  │  Pipeline
│                           │                           │  ├─ L3: Optimization      │  ├─ L2: Jenkins
├─ Unit 1.3                 ├─ Unit 2.3                 │  └─ L4: Verification      │  │  Plugins
│  Vulnerability            │  Dependency               │                           │  └─ L3: Post Actions
│  Classification           │  Analysis                 ├─ Unit 3.3                 │
│  ├─ L1: CWE/CVE/CVSS     │  ├─ L1: OWASP Dep-Check   │  OS Patching              ├─ Unit 4.3
│  └─ L2: OWASP Top 10     │  ├─ L2: Maven Plugin      │  & Maintenance            │  Decision Matrix
│                           │  └─ L3: Suppressions      │  ├─ L1: Patch Process     │  & Best Practices
├─ Unit 1.4                 │                           │  ├─ L2: Automated         │  ├─ L1: Tool Matrix
│  Cryptography &           ├─ Unit 2.4                 │  │  Patching Pipeline     │  ├─ L2: Remediation
│  Certificates             │  Pipeline Failure         │  └─ L3: CIS Standards     │  │  Playbook
│  ├─ L1: PKI               │  Handling                 │                           │  └─ L3: Best
│  ├─ L2: Sym vs Asym       │  ├─ L1: Talisman Fails    │                           │     Practices
│  ├─ L3: TLS Certs         │  ├─ L2: SonarQube Fails   │                           │
│  └─ L4: SSL Termination   │  ├─ L3: Trivy Fails       │                           │
│                           │  └─ L4: Remediation Flow  │                           │
```

---

## LESSON FORMAT

Every lesson follows this standardized structure:

```
┌─────────────────────────────────────────────────────────┐
│  LESSON TITLE                                           │
├─────────────────────────────────────────────────────────┤
│  Objective     : What you will learn                    │
│  Duration      : Estimated time                         │
│  Prerequisites : What you need before starting          │
├─────────────────────────────────────────────────────────┤
│  CONCEPT       : Theory and explanation                 │
│  HANDS-ON      : Commands, code, and expected output    │
│  BEST PRACTICE : Do's and don'ts                        │
│  ASSESSMENT    : Verify your understanding              │
└─────────────────────────────────────────────────────────┘
```

---
---

# ══════════════════════════════════════════════════════════════
#  MODULE 1 — CORE SECURITY CONCEPTS
# ══════════════════════════════════════════════════════════════

```
Module   : 1
Title    : Core Security Concepts
Duration : 4 hours
Units    : 4
Lessons  : 11
Goal     : Understand foundational security terminology, testing
           methodologies, vulnerability classification, and
           cryptographic primitives used across DevSecOps.
```

---

## Unit 1.1 — Application Security Testing

> **Unit Objective:** Differentiate between static and dynamic testing,
> understand false results, and apply the Shift Left model.

---

### Lesson 1: SAST vs DAST

```
Objective     : Compare static and dynamic application security testing
Duration      : 25 min
Prerequisites : None
```

#### CONCEPT

| Aspect | SAST (Static) | DAST (Dynamic) |
|--------|---------------|----------------|
| **When** | On source code, during development | At runtime, on running application |
| **How** | Analyzes code without executing | Sends HTTP requests, analyzes responses |
| **Finds** | SQL injection patterns, hardcoded secrets, buffer overflows | Runtime vulns, auth issues, misconfigs |
| **False Positives** | Higher (no runtime context) | Lower (tests real behavior) |
| **Tools** | SonarQube, Semgrep, Checkmarx | OWASP ZAP, Burp Suite, Nikto |

#### HANDS-ON

**SAST Example — SonarQube detects SQL injection:**

```java
// BAD: SQL Injection — SAST will flag this
String query = "SELECT * FROM users WHERE id = '" + userId + "'";
Statement stmt = connection.createStatement();
ResultSet rs = stmt.executeQuery(query);

// GOOD: Parameterized query
String query = "SELECT * FROM users WHERE id = ?";
PreparedStatement stmt = connection.prepareStatement(query);
stmt.setString(1, userId);
ResultSet rs = stmt.executeQuery();
```

**DAST Example — OWASP ZAP baseline scan:**

```bash
$ docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://target-app:8080

# Output:
# WARN-NEW: X-Frame-Options Header Not Set [10020]
# WARN-NEW: Server Leaks Version Information [10036]
# FAIL-NEW: SQL Injection [40018]
```

#### BEST PRACTICE

- Use both SAST and DAST — they find different classes of issues
- SAST runs in CI (no deployment needed); DAST runs post-deployment
- Map each tool to OWASP Top 10 categories it covers

#### ASSESSMENT

1. Which testing type requires a running application?
2. Name one vulnerability SAST can find but DAST cannot.
3. Why does SAST produce more false positives than DAST?

---

### Lesson 2: False Positive vs False Negative

```
Objective     : Identify and manage false results from security tools
Duration      : 15 min
Prerequisites : Lesson 1
```

#### CONCEPT

| Term | Meaning | Risk |
|------|---------|------|
| **False Positive** | Tool reports a vulnerability that doesn't exist | Wastes time, causes alert fatigue |
| **False Negative** | Tool misses a real vulnerability | Breach goes undetected |

#### HANDS-ON

```java
// SonarQube suppression for a confirmed false positive
@SuppressWarnings("java:S2068") // False positive: not a hardcoded password
private static final String PASSWORD_FIELD_NAME = "password";
```

#### BEST PRACTICE

- Tune rules to reduce false positives (SonarQube Quality Profiles)
- Layer SAST + DAST + SCA to minimize false negatives
- Maintain suppression lists with documented justification
- Review suppressions quarterly — context may change

#### ASSESSMENT

1. Which is more dangerous: false positive or false negative? Why?
2. How do you suppress a false positive in SonarQube?

---

### Lesson 3: Shift Left Approach

```
Objective     : Apply the Shift Left model to embed security early in SDLC
Duration      : 20 min
Prerequisites : Lessons 1–2
```

#### CONCEPT

Move security testing as early as possible in the software delivery lifecycle.

```
Traditional:    Code → Build → Test → Deploy → [Security Audit] → Production
Shift Left:     [Security] → Code → [Security] → Build → [Security] → Deploy → Production
```

#### HANDS-ON

| Phase | Security Activity | Tool |
|-------|-------------------|------|
| IDE / Pre-commit | Secret scanning, linting | Talisman, ESLint security plugin |
| Commit / PR | SAST, dependency check | SonarQube, OWASP Dep-Check |
| Build | Container scanning, SBOM | Trivy, Syft |
| Deploy | DAST, IaC scanning | OWASP ZAP, Checkov |
| Runtime | WAF, monitoring | AWS WAF, Datadog |

#### BEST PRACTICE

- Developers should get security feedback in their IDE or PR, not after deployment
- Cheapest scans first (Talisman < SonarQube < Trivy)
- Automate everything — manual gates slow delivery

#### ASSESSMENT

1. Draw a Shift Left pipeline with at least 4 security checkpoints.
2. Why is it cheaper to find a bug in the IDE than in production?

---

## Unit 1.2 — Dependency & Composition Analysis

> **Unit Objective:** Understand how third-party dependencies introduce risk,
> generate SBOMs, and differentiate VA from PT.

---

### Lesson 1: SCA (Software Composition Analysis)

```
Objective     : Scan project dependencies for known CVEs
Duration      : 20 min
Prerequisites : Unit 1.1
```

#### CONCEPT

Your code may be secure, but importing `log4j 2.14.1` inherits CVE-2021-44228 (Log4Shell, CVSS 10.0). SCA tools scan your dependency tree against vulnerability databases.

**Tools:** OWASP Dependency-Check, Snyk, Dependabot, npm audit

#### HANDS-ON

```bash
# npm audit — SCA for Node.js
$ npm audit

# found 3 vulnerabilities (1 low, 1 moderate, 1 critical)
# ┌───────────────┬──────────────────────────────────────────┐
# │ Critical      │ Prototype Pollution in lodash            │
# ├───────────────┼──────────────────────────────────────────┤
# │ Package       │ lodash                                   │
# │ Patched in    │ >=4.17.21                                │
# └───────────────┴──────────────────────────────────────────┘

$ npm audit fix
```

```bash
# OWASP Dependency-Check (Java/Maven)
$ mvn org.owasp:dependency-check-maven:check
# Generates: target/dependency-check-report.html
```

#### BEST PRACTICE

- Run SCA in every CI build
- Set a CVSS threshold (e.g., fail on >= 7.0)
- Use Dependabot or Renovate for automated dependency updates
- Pin dependency versions in production (no `^` or `~`)

#### ASSESSMENT

1. What is the difference between SCA and SAST?
2. Your `npm audit` shows a critical CVE. What are your two options?

---

### Lesson 2: SBOM (Software Bill of Materials)

```
Objective     : Generate and consume SBOMs for vulnerability tracking
Duration      : 15 min
Prerequisites : Lesson 1
```

#### CONCEPT

A machine-readable inventory of every component in your software — libraries, versions, licenses, transitive dependencies. Required by US Executive Order 14028 for government software.

**Formats:** CycloneDX, SPDX
**Tools:** Syft (generate), Grype (scan)

#### HANDS-ON

```bash
# Generate SBOM with Syft
$ syft dir:./my-app -o cyclonedx-json > sbom.json

# Output (abbreviated):
# {
#   "bomFormat": "CycloneDX",
#   "components": [
#     { "name": "express", "version": "4.18.2", "purl": "pkg:npm/express@4.18.2" },
#     { "name": "lodash",  "version": "4.17.21", "purl": "pkg:npm/lodash@4.17.21" }
#   ]
# }

# Scan SBOM for vulnerabilities
$ grype sbom:sbom.json

# NAME      VERSION   VULNERABILITY   SEVERITY
# lodash    4.17.21   CVE-2021-23337  High
```

#### BEST PRACTICE

- Generate SBOM for every release and store alongside artifacts
- When a new CVE drops, search SBOMs to answer: "Do we use this library?"
- Include SBOMs in container image labels or OCI annotations

#### ASSESSMENT

1. What problem does an SBOM solve that SCA alone does not?
2. Name two SBOM formats.

---

### Lesson 3: VAPT (Vulnerability Assessment & Penetration Testing)

```
Objective     : Differentiate VA from PT and know when to use each
Duration      : 15 min
Prerequisites : None
```

#### CONCEPT

| Aspect | Vulnerability Assessment (VA) | Penetration Testing (PT) |
|--------|-------------------------------|--------------------------|
| **Goal** | Identify and list vulnerabilities | Exploit vulnerabilities to prove impact |
| **Approach** | Automated scanning | Manual + automated exploitation |
| **Output** | List of CVEs with severity | Proof-of-concept exploits, attack paths |
| **Frequency** | Continuous / weekly | Quarterly / annually |

#### BEST PRACTICE

- VA is automated and continuous (in pipeline)
- PT is periodic and manual (by security team or third party)
- PT findings should feed back into SAST/DAST rules

#### ASSESSMENT

1. Can VA replace PT? Why or why not?
2. Which one belongs in a CI/CD pipeline?

---

## Unit 1.3 — Vulnerability Classification

> **Unit Objective:** Use CWE, CVE, and CVSS to classify and prioritize
> vulnerabilities. Understand the OWASP Top 10.

---

### Lesson 1: CWE vs CVE vs CVSS

```
Objective     : Classify vulnerabilities using industry standards
Duration      : 20 min
Prerequisites : Unit 1.2
```

#### CONCEPT

| Term | What It Is | Example |
|------|-----------|---------|
| **CWE** (Common Weakness Enumeration) | A category/type of vulnerability | CWE-89: SQL Injection |
| **CVE** (Common Vulnerabilities and Exposures) | A specific vulnerability in a specific product | CVE-2021-44228: Log4Shell |
| **CVSS** (Common Vulnerability Scoring System) | A severity score (0.0–10.0) | Log4Shell: 10.0 (Critical) |

**Relationship:**

```
CWE-502 (Deserialization of Untrusted Data)    ← weakness category
  └── CVE-2021-44228 (Log4Shell in Log4j)      ← specific instance
        └── CVSS: 10.0 (Critical)              ← severity score
```

**CVSS Ranges:**

| Score | Severity |
|-------|----------|
| 0.0 | None |
| 0.1–3.9 | Low |
| 4.0–6.9 | Medium |
| 7.0–8.9 | High |
| 9.0–10.0 | Critical |

#### BEST PRACTICE

- Use CVSS to prioritize remediation (Critical/High first)
- Map findings to CWE categories to identify systemic weaknesses
- Track CVEs in a vulnerability management system

#### ASSESSMENT

1. A tool reports CWE-79. What type of vulnerability is this?
2. CVE-2021-44228 has CVSS 10.0. What does this mean for your SLA?

---

### Lesson 2: OWASP Top 10 (2021)

```
Objective     : Map OWASP Top 10 categories to DevSecOps tools
Duration      : 20 min
Prerequisites : Lesson 1
```

#### CONCEPT

| Rank | Category | Example |
|------|----------|---------|
| A01 | Broken Access Control | IDOR, privilege escalation |
| A02 | Cryptographic Failures | Weak encryption, plaintext passwords |
| A03 | Injection | SQL injection, XSS |
| A04 | Insecure Design | Missing threat modeling |
| A05 | Security Misconfiguration | Default credentials, open S3 |
| A06 | Vulnerable Components | Libraries with known CVEs |
| A07 | Auth Failures | Weak passwords, missing MFA |
| A08 | Software & Data Integrity | Unsigned updates, CI/CD tampering |
| A09 | Logging & Monitoring Failures | No audit trail |
| A10 | SSRF | Server-side request forgery |

#### HANDS-ON

**Tool-to-OWASP mapping:**

```
A01 (Access Control)     → DAST (ZAP), manual PT
A03 (Injection)          → SAST (SonarQube), DAST (ZAP)
A05 (Misconfiguration)   → Checkov, CIS Benchmarks
A06 (Vulnerable Deps)    → SCA (OWASP Dep-Check, npm audit)
A08 (Integrity)          → Signed commits, SBOM, image signing
```

#### BEST PRACTICE

- Use OWASP Top 10 as a checklist when selecting security tools
- Ensure your pipeline covers at least A01, A03, A05, A06, A08
- Review annually — OWASP updates the list every 3–4 years

#### ASSESSMENT

1. Which OWASP category does SCA address?
2. Name a tool that covers A05 (Security Misconfiguration).

---

## Unit 1.4 — Cryptography & Certificates

> **Unit Objective:** Understand PKI, encryption types, TLS certificates,
> and SSL termination patterns.

---

### Lesson 1: PKI (Public Key Infrastructure)

```
Objective     : Understand the trust chain in PKI
Duration      : 15 min
Prerequisites : None
```

#### CONCEPT

```
┌─────────────────────────────────────────────┐
│                    CA                        │
│          (Certificate Authority)             │
│     Issues & signs certificates              │
└──────────────┬──────────────────────────────┘
               │ signs
┌──────────────▼──────────────────────────────┐
│           Certificate                        │
│   Contains: Public Key + Identity + Expiry   │
│   Signed by: CA's private key                │
└──────────────┬──────────────────────────────┘
               │ used by
┌──────────────▼──────────────────────────────┐
│         Server / Client                      │
│   Presents certificate during TLS handshake  │
└─────────────────────────────────────────────┘
```

#### HANDS-ON

```bash
# Generate a self-signed certificate (dev/testing only)
$ openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
  -days 365 -nodes -subj "/CN=myapp.local"

# View certificate details
$ openssl x509 -in cert.pem -text -noout

# Output (abbreviated):
# Issuer: CN = myapp.local
# Validity
#     Not Before: Jan  1 00:00:00 2024 GMT
#     Not After : Jan  1 00:00:00 2025 GMT
# Subject: CN = myapp.local
# Public Key Algorithm: rsaEncryption (4096 bit)
```

#### BEST PRACTICE

- Use Let's Encrypt for free, automated certificates in production
- Never use self-signed certificates in production
- Automate renewal (certs expire every 90 days with Let's Encrypt)

#### ASSESSMENT

1. What role does the CA play in PKI?
2. Why should you not use self-signed certificates in production?

---

### Lesson 2: Symmetric vs Asymmetric Encryption

```
Objective     : Understand how TLS combines both encryption types
Duration      : 15 min
Prerequisites : Lesson 1
```

#### CONCEPT

| Aspect | Symmetric | Asymmetric |
|--------|-----------|------------|
| **Keys** | One shared key for encrypt + decrypt | Key pair: public (encrypt) + private (decrypt) |
| **Speed** | Fast | 100–1000x slower |
| **Use Case** | Bulk data encryption (AES) | Key exchange, digital signatures (RSA, ECDSA) |
| **Problem** | How to share the key securely? | Solved — public key is public |

#### HANDS-ON

**How TLS uses both:**

```
1. Client → Server: "Hello, I support TLS 1.3"
2. Server → Client: Certificate (contains public key)
3. Client: Verifies certificate against CA
4. Client: Generates random symmetric key
5. Client → Server: Symmetric key encrypted with server's public key  ← ASYMMETRIC
6. Both sides now have the symmetric key
7. All further communication encrypted with symmetric key              ← SYMMETRIC
```

#### BEST PRACTICE

- Asymmetric solves the key-exchange problem; symmetric handles bulk data
- Use TLS 1.3 (disable TLS 1.0, 1.1)
- Use strong cipher suites (ECDHE + AES-GCM)

#### ASSESSMENT

1. Why doesn't TLS use asymmetric encryption for all data?
2. What problem does asymmetric encryption solve that symmetric cannot?

---

### Lesson 3: TLS Certificates

```
Objective     : Inspect and validate TLS certificates
Duration      : 10 min
Prerequisites : Lessons 1–2
```

#### HANDS-ON

```bash
# Check a website's TLS certificate
$ openssl s_client -connect google.com:443 -servername google.com 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates

# Output:
# subject=CN = *.google.com
# issuer=C = US, O = Google Trust Services LLC, CN = GTS CA 1C3
# notBefore=Dec  4 08:36:00 2023 GMT
# notAfter=Feb 26 08:35:59 2024 GMT
```

#### BEST PRACTICE

- Monitor certificate expiry with alerting (e.g., Prometheus blackbox exporter)
- Use Certificate Transparency logs to detect unauthorized certificates
- Prefer wildcard certs (`*.example.com`) to reduce management overhead

#### ASSESSMENT

1. How do you check when a TLS certificate expires?
2. What happens if a certificate expires in production?

---

### Lesson 4: SSL Termination at Load Balancer

```
Objective     : Configure SSL termination at the load balancer layer
Duration      : 15 min
Prerequisites : Lessons 1–3
```

#### CONCEPT

```
                    HTTPS (encrypted)           HTTP (plaintext)
Client  ──────────►  Load Balancer  ──────────►  Backend Servers
                    (SSL Termination)            (in private subnet)
                    Has TLS certificate           No certificate needed
```

**Why?**
- Reduces CPU load on application servers
- Centralizes certificate management
- Backend servers in a private VPC don't need TLS (traffic is internal)

#### HANDS-ON

```hcl
# Terraform — ALB with SSL termination
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Backend target group uses HTTP (port 80)
resource "aws_lb_target_group" "app" {
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
}
```

#### BEST PRACTICE

- SSL termination at LB is standard for most workloads
- For compliance requiring end-to-end encryption: use SSL passthrough or re-encrypt
- Use AWS ACM for free, auto-renewing certificates on ALB

#### ASSESSMENT

1. Why do backend servers not need TLS when using SSL termination?
2. When would you use SSL passthrough instead of termination?

---
---

