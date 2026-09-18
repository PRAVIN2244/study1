# Module 08 — Security and Compliance

## GitLab Security Scanning Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  SAST    │  │  DAST    │  │Dependency │  │Container│ │
│  │ (Static) │  │(Dynamic) │  │ Scanning  │  │Scanning │ │
│  └────┬─────┘  └────┬─────┘  └────┬──────┘  └───┬────┘ │
│       │              │              │              │      │
│       └──────────────┴──────────────┴──────────────┘      │
│                          │                                │
│                 ┌────────▼────────┐                       │
│                 │ Security Report │                       │
│                 │ (MR Widget)     │                       │
│                 └────────┬────────┘                       │
│                          │                                │
│                 ┌────────▼────────┐                       │
│                 │ Security        │                       │
│                 │ Dashboard       │                       │
│                 └─────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## SAST (Static Application Security Testing)

Analyzes source code for vulnerabilities without running the application.

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

# Override defaults
sast:
  variables:
    SAST_EXCLUDED_PATHS: "spec,test,tests,tmp"
    SEARCH_MAX_DEPTH: 4
```

Supported languages: C/C++, Go, Java, JavaScript/TypeScript, Python, Ruby, PHP, C#, Scala, and more.

### Custom SAST Configuration

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

variables:
  SAST_EXCLUDED_ANALYZERS: "eslint,bandit"

semgrep-sast:
  variables:
    SEMGREP_RULES: >-
      p/owasp-top-ten
      p/r2c-security-audit
```

## DAST (Dynamic Application Security Testing)

Tests running applications for vulnerabilities (requires a deployed app).

```yaml
include:
  - template: Security/DAST.gitlab-ci.yml

dast:
  variables:
    DAST_WEBSITE: "https://staging.example.com"
    DAST_FULL_SCAN_ENABLED: "true"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### DAST with Authentication

```yaml
dast:
  variables:
    DAST_WEBSITE: "https://staging.example.com"
    DAST_AUTH_URL: "https://staging.example.com/login"
    DAST_USERNAME: "test-user"
    DAST_PASSWORD_FIELD: "password"
    DAST_USERNAME_FIELD: "username"
  before_script:
    - export DAST_PASSWORD=$DAST_TEST_PASSWORD  # From CI/CD variables
```

## Dependency Scanning

Scans project dependencies for known vulnerabilities.

```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

dependency_scanning:
  variables:
    DS_EXCLUDED_PATHS: "test/"
```

Supports: npm, pip, Maven, Gradle, Bundler, Composer, Go modules, NuGet.

## Container Scanning

Scans Docker images for OS-level vulnerabilities.

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

container_scanning:
  variables:
    CS_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    CS_SEVERITY_THRESHOLD: "HIGH"
```

## Secret Detection

Scans commits for accidentally committed secrets (API keys, passwords, tokens).

```yaml
include:
  - template: Security/Secret-Detection.gitlab-ci.yml

secret_detection:
  variables:
    SECRET_DETECTION_HISTORIC_SCAN: "true"  # Scan full history
```

## License Compliance

Detect and manage software licenses in dependencies.

```yaml
include:
  - template: Security/License-Scanning.gitlab-ci.yml

license_scanning:
  variables:
    LICENSE_FINDER_CLI_OPTS: "--decisions-file=.license-decisions.yml"
```

## Complete Security Pipeline

```yaml
stages:
  - build
  - test
  - security
  - deploy

include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml

variables:
  CS_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CS_IMAGE .
    - docker push $CS_IMAGE

test:
  stage: test
  script:
    - npm ci
    - npm test

# Security jobs are auto-configured by the included templates
# They run in the 'test' stage by default

deploy:
  stage: deploy
  script:
    - ./deploy.sh
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

## Merge Request Approvals

### Approval Rules

**Settings → Merge Requests → Approval rules**

```
Rule: Security Review
  Approvers: @security-team
  Approvals required: 1
  Target branch: main

Rule: Code Review
  Approvers: @dev-team
  Approvals required: 2
  Target branch: All branches
```

### Code Owners

```
# CODEOWNERS file (in repository root)

# Default owners
* @dev-team

# Frontend
/frontend/ @frontend-team
*.js @frontend-team
*.tsx @frontend-team

# Backend
/backend/ @backend-team
*.go @backend-team

# Infrastructure
/terraform/ @infra-team @security-team
Dockerfile @infra-team

# Security-sensitive files
/auth/ @security-team
*.pem @security-team
```

## Protected Branches and Tags

### Protected Branches

**Settings → Repository → Protected branches**

| Branch | Allowed to merge | Allowed to push | Allowed to force push |
|--------|-----------------|-----------------|----------------------|
| `main` | Maintainers | No one | No |
| `release/*` | Maintainers | Maintainers | No |
| `develop` | Developers+ | Developers+ | No |

### Protected Tags

**Settings → Repository → Protected tags**

```
Tag pattern: v*
Allowed to create: Maintainers
```

## Compliance Framework

### Compliance Pipeline (Ultimate)

Force all projects in a group to include specific CI/CD configuration:

```yaml
# compliance-pipeline.yml (in compliance project)
include:
  - project: '$CI_PROJECT_PATH'
    file: '.gitlab-ci.yml'

# Mandatory security scans
compliance-sast:
  stage: test
  extends: .sast-template
  rules:
    - when: always

compliance-secret-detection:
  stage: test
  extends: .secret-detection-template
  rules:
    - when: always

# Mandatory approval gate
compliance-gate:
  stage: deploy
  script:
    - echo "Compliance checks passed"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Audit Events

Track security-relevant actions:

**Admin Area → Monitoring → Audit Events**

Tracked events include:
- User login/logout
- Permission changes
- Project/group creation/deletion
- Protected branch changes
- Runner registration
- CI/CD variable changes
- Merge request approvals

```bash
# Query audit events via API
curl --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.example.com/api/v4/audit_events?created_after=2024-01-01"
```

## Security Best Practices

1. **Enable all relevant security scanners** in CI/CD
2. **Require MR approvals** from security team for sensitive paths
3. **Use CODEOWNERS** to enforce review requirements
4. **Protect main branches** — no direct pushes
5. **Use protected variables** for production secrets
6. **Enable secret detection** to catch leaked credentials
7. **Set up compliance frameworks** for regulated environments
8. **Review security dashboard** regularly
9. **Auto-remediate** — enable dependency update bots
10. **Audit trail** — monitor and alert on security events
