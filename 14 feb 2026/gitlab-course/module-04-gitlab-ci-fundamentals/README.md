# Module 04 — GitLab CI Fundamentals

## Overview

GitLab CI/CD is configured via a `.gitlab-ci.yml` file in the repository root. When you push code, GitLab detects this file and runs the defined pipeline.

## Basic .gitlab-ci.yml

```yaml
# Define stages (order matters)
stages:
  - build
  - test
  - deploy

# Job: build the application
build-job:
  stage: build
  script:
    - echo "Building the application..."
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/

# Job: run tests
test-job:
  stage: test
  script:
    - npm ci
    - npm test

# Job: deploy to production
deploy-job:
  stage: deploy
  script:
    - echo "Deploying to production..."
    - ./deploy.sh
  only:
    - main
```

## Stages

Stages define the order of execution. Jobs in the same stage run in parallel.

```yaml
stages:
  - build      # All build jobs run first
  - test       # Then all test jobs (in parallel)
  - deploy     # Then all deploy jobs

# Execution flow:
# build-app ──┐
#             ├──▶ unit-tests ──┐
#             │    lint ────────┤
#             │    security ────┤
#             │                 ├──▶ deploy-staging ──▶ deploy-prod
```

## Jobs

A job is the basic unit of execution. Each job runs in a fresh environment.

```yaml
job-name:
  stage: test                    # Which stage this job belongs to
  image: node:20-alpine          # Docker image to use
  tags:                          # Which runner to use
    - docker
  variables:                     # Job-level variables
    NODE_ENV: test
  before_script:                 # Run before main script
    - npm ci
  script:                        # Main commands (required)
    - npm test
    - npm run lint
  after_script:                  # Run after main script (even on failure)
    - echo "Cleanup..."
  artifacts:                     # Files to keep after job
    paths:
      - coverage/
    reports:
      junit: report.xml
    expire_in: 1 week
  cache:                         # Files to cache between runs
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
  rules:                         # When to run this job
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: false           # Pipeline fails if this job fails
  timeout: 30 minutes            # Job timeout
  retry: 2                       # Retry on failure
```

## Variables

### Predefined Variables

| Variable | Description |
|----------|-------------|
| `CI_COMMIT_SHA` | Full commit hash |
| `CI_COMMIT_SHORT_SHA` | Short commit hash (8 chars) |
| `CI_COMMIT_BRANCH` | Branch name |
| `CI_COMMIT_TAG` | Tag name (if tagged) |
| `CI_COMMIT_REF_NAME` | Branch or tag name |
| `CI_COMMIT_REF_SLUG` | URL-safe branch/tag name |
| `CI_COMMIT_MESSAGE` | Full commit message |
| `CI_PIPELINE_ID` | Pipeline ID |
| `CI_PIPELINE_SOURCE` | What triggered the pipeline |
| `CI_PROJECT_NAME` | Project name |
| `CI_PROJECT_PATH` | Full project path (group/project) |
| `CI_PROJECT_URL` | Project URL |
| `CI_JOB_ID` | Job ID |
| `CI_JOB_NAME` | Job name |
| `CI_JOB_STAGE` | Stage name |
| `CI_REGISTRY` | Container registry URL |
| `CI_REGISTRY_IMAGE` | Project's registry image path |
| `CI_MERGE_REQUEST_IID` | MR number (merge request pipelines) |
| `CI_DEFAULT_BRANCH` | Default branch name |
| `GITLAB_USER_LOGIN` | Username who triggered pipeline |

### Custom Variables

```yaml
# Global variables
variables:
  APP_NAME: "my-app"
  DEPLOY_ENV: "staging"

# Job-level variables (override global)
deploy:
  variables:
    DEPLOY_ENV: "production"
  script:
    - echo "Deploying $APP_NAME to $DEPLOY_ENV"
```

### Protected and Masked Variables

Set in **Settings → CI/CD → Variables**:

| Option | Effect |
|--------|--------|
| **Protected** | Only available on protected branches/tags |
| **Masked** | Hidden in job logs (value must meet masking requirements) |
| **Environment scope** | Available only for specific environments |

```yaml
deploy:
  script:
    # $DB_PASSWORD is set in CI/CD settings (masked + protected)
    - echo "Connecting to database..."
    - ./deploy.sh --db-pass=$DB_PASSWORD
```

## Artifacts

Files produced by a job that can be used by subsequent jobs or downloaded.

```yaml
build:
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - dist/                    # Directory to keep
      - build/output.json        # Specific file
    exclude:
      - dist/**/*.map            # Exclude source maps
    expire_in: 1 week            # Auto-delete after 1 week
    when: always                 # Keep even on failure (default: on_success)

test:
  stage: test
  script:
    - npm test -- --coverage
  artifacts:
    reports:
      junit: junit-report.xml           # Test results in MR
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura.xml     # Coverage in MR diff
    paths:
      - coverage/
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/' # Extract coverage from log

deploy:
  stage: deploy
  script:
    # Artifacts from 'build' stage are automatically available
    - ls dist/
    - ./deploy.sh
```

## Cache

Cache persists between pipeline runs to speed up jobs (e.g., dependencies).

```yaml
# Global cache
cache:
  key: ${CI_COMMIT_REF_SLUG}      # Cache per branch
  paths:
    - node_modules/
    - .npm/

# Job-specific cache
test:
  cache:
    key:
      files:
        - package-lock.json       # Cache key based on lockfile hash
    paths:
      - node_modules/
    policy: pull                  # Only download, don't upload

build:
  cache:
    key:
      files:
        - package-lock.json
    paths:
      - node_modules/
    policy: pull-push             # Download and upload (default)
```

**Cache vs Artifacts:**

| Feature | Cache | Artifacts |
|---------|-------|-----------|
| Purpose | Speed up jobs (dependencies) | Pass files between stages |
| Persistence | Best-effort, may be cleared | Guaranteed within pipeline |
| Scope | Across pipelines | Within a pipeline |
| Storage | Runner-local or distributed | GitLab server |

## Rules (Conditional Execution)

`rules` replaces the older `only/except` syntax.

```yaml
# Run on merge requests
test:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# Run on main branch only
deploy-prod:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# Run on tags
release:
  rules:
    - if: $CI_COMMIT_TAG

# Run when specific files change
backend-test:
  rules:
    - changes:
        - backend/**/*
        - shared/**/*

# Complex rules
deploy:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual                    # Manual trigger on main
      allow_failure: true             # Pipeline doesn't wait
    - if: $CI_COMMIT_BRANCH == "develop"
      when: always                    # Auto-run on develop
    - when: never                     # Skip for everything else

# Using variables in rules
scan:
  rules:
    - if: $SKIP_SCAN == "true"
      when: never
    - when: always
```

## Services

Additional Docker containers linked to the job container (databases, caches, etc.).

```yaml
test:
  image: python:3.12
  services:
    - name: postgres:16
      alias: db
      variables:
        POSTGRES_DB: test_db
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
    - name: redis:7-alpine
      alias: cache
  variables:
    DATABASE_URL: "postgresql://test:test@db:5432/test_db"
    REDIS_URL: "redis://cache:6379"
  script:
    - pip install -r requirements.txt
    - pytest
```

## Complete Example: Full-Stack Application

```yaml
stages:
  - install
  - lint
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "20"

# Reusable template
.node-base:
  image: node:${NODE_VERSION}-alpine
  cache:
    key:
      files:
        - package-lock.json
    paths:
      - node_modules/

install:
  extends: .node-base
  stage: install
  script:
    - npm ci
  artifacts:
    paths:
      - node_modules/
    expire_in: 1 hour

lint:
  extends: .node-base
  stage: lint
  needs: [install]
  script:
    - npm run lint

unit-tests:
  extends: .node-base
  stage: test
  needs: [install]
  script:
    - npm test -- --coverage
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
  coverage: '/Statements\s*:\s*(\d+\.?\d*)%/'

integration-tests:
  extends: .node-base
  stage: test
  needs: [install]
  services:
    - postgres:16
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    DATABASE_URL: "postgresql://test:test@postgres:5432/test"
  script:
    - npm run test:integration

build:
  extends: .node-base
  stage: build
  needs: [lint, unit-tests]
  script:
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

deploy-staging:
  stage: deploy
  needs: [build, integration-tests]
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - ./deploy.sh staging
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy-production:
  stage: deploy
  needs: [build, integration-tests]
  image: alpine:latest
  script:
    - ./deploy.sh production
  environment:
    name: production
    url: https://example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```
