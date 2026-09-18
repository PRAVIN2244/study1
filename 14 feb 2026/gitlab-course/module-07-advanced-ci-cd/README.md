# Module 07 — Advanced CI/CD

## Review Apps

Automatically deploy a temporary environment for each merge request.

```yaml
deploy-review:
  stage: deploy
  image: alpine/helm:latest
  script:
    - helm upgrade --install review-$CI_COMMIT_REF_SLUG ./helm/app \
        --namespace review \
        --set image.tag=$CI_COMMIT_SHORT_SHA \
        --set ingress.host=$CI_COMMIT_REF_SLUG.review.example.com
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop-review
    auto_stop_in: 3 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop-review:
  stage: deploy
  image: alpine/helm:latest
  script:
    - helm uninstall review-$CI_COMMIT_REF_SLUG --namespace review
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Canary Deployments

Deploy to a subset of production before full rollout.

```yaml
deploy-canary:
  stage: deploy
  script:
    - kubectl set image deployment/myapp-canary \
        myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA \
        --namespace production
    - kubectl scale deployment/myapp-canary --replicas=1 --namespace production
  environment:
    name: production
    url: https://example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual

verify-canary:
  stage: deploy
  needs: [deploy-canary]
  script:
    - ./scripts/canary-health-check.sh
    - sleep 300  # Monitor for 5 minutes
    - ./scripts/check-error-rate.sh
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-production:
  stage: deploy
  needs: [verify-canary]
  script:
    - kubectl set image deployment/myapp \
        myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA \
        --namespace production
    - kubectl rollout status deployment/myapp --namespace production --timeout=300s
    - kubectl scale deployment/myapp-canary --replicas=0 --namespace production
  environment:
    name: production
    url: https://example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

## Blue-Green Deployments

```yaml
variables:
  ACTIVE_COLOR: ""

determine-color:
  stage: prepare
  script:
    - |
      CURRENT=$(kubectl get svc myapp-active -n production -o jsonpath='{.spec.selector.color}')
      if [ "$CURRENT" = "blue" ]; then
        echo "DEPLOY_COLOR=green" >> deploy.env
      else
        echo "DEPLOY_COLOR=blue" >> deploy.env
      fi
  artifacts:
    reports:
      dotenv: deploy.env

deploy-inactive:
  stage: deploy
  needs: [determine-color]
  script:
    - kubectl set image deployment/myapp-$DEPLOY_COLOR \
        myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA \
        --namespace production
    - kubectl rollout status deployment/myapp-$DEPLOY_COLOR --timeout=300s
  environment:
    name: production-$DEPLOY_COLOR

switch-traffic:
  stage: deploy
  needs: [deploy-inactive]
  script:
    - kubectl patch svc myapp-active -n production \
        -p "{\"spec\":{\"selector\":{\"color\":\"$DEPLOY_COLOR\"}}}"
  environment:
    name: production
  when: manual
```

## Feature Flags

GitLab has built-in feature flags (requires Premium/Ultimate, or use Unleash).

```yaml
# Using environment variables as simple feature flags
deploy:
  script:
    - |
      if [ "$FEATURE_NEW_UI" = "true" ]; then
        echo "Deploying with new UI enabled"
        helm upgrade myapp ./helm --set features.newUI=true
      else
        helm upgrade myapp ./helm --set features.newUI=false
      fi
```

## Matrix Builds

Run the same job with different variable combinations:

```yaml
test:
  stage: test
  image: $IMAGE
  parallel:
    matrix:
      - IMAGE: ["python:3.10", "python:3.11", "python:3.12"]
        DB: ["postgres:14", "postgres:16"]
  services:
    - name: $DB
      alias: db
  script:
    - pip install -r requirements.txt
    - pytest
```

This creates 6 jobs (3 Python versions x 2 DB versions).

## Release Management

### Semantic Versioning Pipeline

```yaml
stages:
  - test
  - build
  - release

test:
  stage: test
  script: npm test

build:
  stage: build
  script:
    - npm run build
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

release:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  script:
    - echo "Creating release for $CI_COMMIT_TAG"
  release:
    tag_name: $CI_COMMIT_TAG
    name: "Release $CI_COMMIT_TAG"
    description: "Release notes for $CI_COMMIT_TAG"
    assets:
      links:
        - name: "Docker Image"
          url: "https://$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
          link_type: "image"
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
```

### Auto-Generate Changelog

```yaml
release:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  script:
    - |
      # Generate changelog from commits since last tag
      PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
      if [ -n "$PREV_TAG" ]; then
        CHANGELOG=$(git log ${PREV_TAG}..HEAD --pretty=format:"- %s (%h)" --no-merges)
      else
        CHANGELOG=$(git log --pretty=format:"- %s (%h)" --no-merges)
      fi
      echo "$CHANGELOG" > changelog.md
  release:
    tag_name: $CI_COMMIT_TAG
    description: ./changelog.md
  rules:
    - if: $CI_COMMIT_TAG
```

## GitOps with GitLab

```yaml
stages:
  - build
  - update-manifests

build-and-push:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

update-k8s-manifests:
  stage: update-manifests
  image: alpine:latest
  needs: [build-and-push]
  before_script:
    - apk add --no-cache git
  script:
    - git clone https://gitlab-ci-token:${GITOPS_TOKEN}@gitlab.example.com/infra/k8s-manifests.git
    - cd k8s-manifests
    - "sed -i 's|image: .*|image: ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}|' apps/myapp/deployment.yaml"
    - git config user.email "ci@example.com"
    - git config user.name "GitLab CI"
    - git add .
    - git commit -m "Update myapp to ${CI_COMMIT_SHORT_SHA}"
    - git push
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

## CI/CD Components (Reusable Templates)

GitLab CI/CD Components (GitLab 17+):

```yaml
# In a component project: templates/build.yml
spec:
  inputs:
    image:
      default: node:20
    build_command:
      default: npm run build

---
build:
  image: $[[ inputs.image ]]
  script:
    - $[[ inputs.build_command ]]
  artifacts:
    paths:
      - dist/
```

```yaml
# Using the component
include:
  - component: gitlab.example.com/templates/build@1.0.0
    inputs:
      image: node:20-alpine
      build_command: npm ci && npm run build
```

## Pipeline Optimization Tips

1. **Use `needs` for DAG pipelines** — don't wait for unrelated jobs
2. **Cache dependencies** — use `cache:key:files` with lockfiles
3. **Use `interruptible: true`** — cancel outdated pipelines
4. **Shallow clone** — `GIT_DEPTH: 1` for faster checkout
5. **Use `rules:changes`** — skip jobs when relevant files haven't changed
6. **Parallelize tests** — use `parallel` keyword to split test suites
7. **Use `resource_group`** — prevent concurrent deployments
8. **Minimize artifact size** — use `expire_in` and `exclude`
9. **Use parent-child pipelines** — for monorepos
10. **Pre-build Docker images** — with all dependencies baked in

```yaml
# Optimization example
variables:
  GIT_DEPTH: 1                     # Shallow clone
  FF_USE_FASTZIP: "true"           # Faster artifact compression
  ARTIFACT_COMPRESSION_LEVEL: "fast"
  CACHE_COMPRESSION_LEVEL: "fast"

test:
  interruptible: true
  parallel: 4                      # Split into 4 parallel jobs
  script:
    - npm run test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  cache:
    key:
      files: [package-lock.json]
    paths: [node_modules/]
    policy: pull
```
