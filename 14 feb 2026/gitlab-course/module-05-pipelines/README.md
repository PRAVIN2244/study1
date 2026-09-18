# Module 05 — Pipelines

## Pipeline Types

### Basic Pipeline

Jobs grouped by stages, stages run sequentially, jobs within a stage run in parallel.

```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script: make build

test-unit:
  stage: test
  script: make test-unit

test-integration:
  stage: test
  script: make test-integration

deploy:
  stage: deploy
  script: make deploy
```

```
build ──▶ test-unit ────────▶ deploy
          test-integration ─┘
```

### DAG Pipeline (Directed Acyclic Graph)

Use `needs` to define explicit dependencies, bypassing stage ordering.

```yaml
stages:
  - build
  - test
  - deploy

build-frontend:
  stage: build
  script: npm run build
  artifacts:
    paths: [dist/]

build-backend:
  stage: build
  script: mvn package
  artifacts:
    paths: [target/]

test-frontend:
  stage: test
  needs: [build-frontend]        # Starts as soon as build-frontend finishes
  script: npm test

test-backend:
  stage: test
  needs: [build-backend]         # Doesn't wait for build-frontend
  script: mvn test

deploy:
  stage: deploy
  needs: [test-frontend, test-backend]
  script: ./deploy.sh
```

```
build-frontend ──▶ test-frontend ──┐
                                    ├──▶ deploy
build-backend ───▶ test-backend ───┘
```

### Merge Request Pipeline

Runs only for merge requests, not branch pushes.

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

test:
  script: npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

deploy:
  script: ./deploy.sh
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Parent-Child Pipelines

Trigger child pipelines from a parent pipeline. Useful for monorepos.

```yaml
# .gitlab-ci.yml (parent)
stages:
  - triggers

trigger-frontend:
  stage: triggers
  trigger:
    include: frontend/.gitlab-ci.yml
    strategy: depend                    # Parent waits for child
  rules:
    - changes:
        - frontend/**/*

trigger-backend:
  stage: triggers
  trigger:
    include: backend/.gitlab-ci.yml
    strategy: depend
  rules:
    - changes:
        - backend/**/*
```

```yaml
# frontend/.gitlab-ci.yml (child)
stages:
  - build
  - test

build:
  stage: build
  image: node:20
  script:
    - cd frontend
    - npm ci && npm run build

test:
  stage: test
  image: node:20
  script:
    - cd frontend
    - npm test
```

### Multi-Project Pipelines

Trigger pipelines in other projects.

```yaml
deploy-microservice:
  stage: deploy
  trigger:
    project: my-group/deployment-project
    branch: main
    strategy: depend
  variables:
    SERVICE_NAME: "my-service"
    IMAGE_TAG: $CI_COMMIT_SHORT_SHA
```

### Dynamic Child Pipelines

Generate pipeline configuration at runtime.

```yaml
generate-config:
  stage: build
  script:
    - python generate-pipeline.py > generated-pipeline.yml
  artifacts:
    paths:
      - generated-pipeline.yml

run-generated:
  stage: test
  trigger:
    include:
      - artifact: generated-pipeline.yml
        job: generate-config
    strategy: depend
```

## Pipeline Configuration

### workflow

Control when pipelines are created:

```yaml
workflow:
  rules:
    # Don't create pipeline for branches with open MRs (avoid duplicates)
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    # Create pipeline for merge requests
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    # Create pipeline for default branch
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    # Create pipeline for tags
    - if: $CI_COMMIT_TAG
```

### include

Split configuration across multiple files:

```yaml
# Include from same project
include:
  - local: '/templates/build.yml'
  - local: '/templates/test.yml'

# Include from another project
include:
  - project: 'my-group/ci-templates'
    ref: main
    file:
      - '/templates/docker-build.yml'
      - '/templates/deploy.yml'

# Include from URL
include:
  - remote: 'https://example.com/ci/template.yml'

# Include GitLab templates
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
```

### extends and YAML anchors

Reuse configuration:

```yaml
# Using extends (preferred)
.test-base:
  image: python:3.12
  before_script:
    - pip install -r requirements.txt
  cache:
    paths:
      - .pip-cache/

test-unit:
  extends: .test-base
  script:
    - pytest tests/unit/

test-integration:
  extends: .test-base
  script:
    - pytest tests/integration/
  services:
    - postgres:16

# Using YAML anchors
.deploy-template: &deploy-template
  image: alpine:latest
  before_script:
    - apk add --no-cache curl

deploy-staging:
  <<: *deploy-template
  script:
    - ./deploy.sh staging
  environment:
    name: staging

deploy-production:
  <<: *deploy-template
  script:
    - ./deploy.sh production
  environment:
    name: production
```

## Environments and Deployments

```yaml
deploy-staging:
  stage: deploy
  script:
    - ./deploy.sh staging
  environment:
    name: staging
    url: https://staging.example.com
    on_stop: stop-staging              # Job to run when stopping
    auto_stop_in: 1 week               # Auto-stop after 1 week

stop-staging:
  stage: deploy
  script:
    - ./teardown.sh staging
  environment:
    name: staging
    action: stop
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH != $CI_DEFAULT_BRANCH

# Dynamic environments (per branch)
deploy-review:
  stage: deploy
  script:
    - ./deploy.sh review-$CI_COMMIT_REF_SLUG
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop-review
    auto_stop_in: 2 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop-review:
  stage: deploy
  script:
    - ./teardown.sh review-$CI_COMMIT_REF_SLUG
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Pipeline Triggers

### API Trigger

```bash
# Create trigger token: Settings → CI/CD → Pipeline triggers

# Trigger pipeline via API
curl -X POST \
  -F "token=<trigger-token>" \
  -F "ref=main" \
  -F "variables[DEPLOY_ENV]=production" \
  "https://gitlab.example.com/api/v4/projects/<project-id>/trigger/pipeline"
```

### Scheduled Pipelines

**CI/CD → Schedules → New schedule**

```
Description: Nightly build
Interval: Custom (0 2 * * *)    # 2 AM daily
Target branch: main
Variables: NIGHTLY=true
```

```yaml
nightly-test:
  script: npm run test:full
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule" && $NIGHTLY == "true"
```

### Pipeline for External Events

```yaml
# Triggered by webhook from external system
external-deploy:
  rules:
    - if: $CI_PIPELINE_SOURCE == "trigger"
  script:
    - echo "Triggered externally with DEPLOY_ENV=$DEPLOY_ENV"
    - ./deploy.sh $DEPLOY_ENV
```

## Pipeline Efficiency

### Interruptible Jobs

Cancel running jobs when a new pipeline starts on the same branch:

```yaml
workflow:
  auto_cancel:
    on_new_commit: interruptible

build:
  interruptible: true              # Can be cancelled
  script: npm run build

deploy:
  interruptible: false             # Never cancel deployments
  script: ./deploy.sh
```

### Resource Groups

Prevent concurrent deployments:

```yaml
deploy-production:
  resource_group: production       # Only one job at a time
  script: ./deploy.sh production

deploy-staging:
  resource_group: staging
  script: ./deploy.sh staging
```

### Retry and Timeout

```yaml
flaky-test:
  script: npm run test:e2e
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure
      - script_failure
  timeout: 30 minutes
```

## Debugging Pipelines

```yaml
# Add debug output
debug-job:
  script:
    - echo "CI_PIPELINE_SOURCE=$CI_PIPELINE_SOURCE"
    - echo "CI_COMMIT_BRANCH=$CI_COMMIT_BRANCH"
    - echo "CI_MERGE_REQUEST_IID=$CI_MERGE_REQUEST_IID"
    - env | sort                   # Print all variables
```

```bash
# Validate .gitlab-ci.yml locally
# CI/CD → Editor → Validate (in GitLab UI)

# Or use the API
curl --header "PRIVATE-TOKEN: <token>" \
  --header "Content-Type: application/json" \
  --data '{"content": "'"$(cat .gitlab-ci.yml)"'"}' \
  "https://gitlab.example.com/api/v4/ci/lint"
```
