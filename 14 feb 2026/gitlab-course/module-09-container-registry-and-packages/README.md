# Module 09 — Container Registry and Packages

## Container Registry

GitLab includes a built-in Docker container registry.

### Enable Container Registry (Self-Hosted)

```ruby
# /etc/gitlab/gitlab.rb
registry_external_url 'https://registry.example.com'

# Or use the same domain with a port
# registry_external_url 'https://gitlab.example.com:5050'

# SSL certificates (if not using Let's Encrypt)
registry_nginx['ssl_certificate'] = "/etc/gitlab/ssl/registry.crt"
registry_nginx['ssl_certificate_key'] = "/etc/gitlab/ssl/registry.key"
```

```bash
sudo gitlab-ctl reconfigure
```

### Using the Container Registry

```bash
# Login to registry
docker login registry.example.com
# Username: your-gitlab-username
# Password: personal access token (with read_registry, write_registry scopes)

# Or use CI/CD variables (in pipeline)
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# Build and push
docker build -t registry.example.com/group/project:latest .
docker push registry.example.com/group/project:latest

# Pull
docker pull registry.example.com/group/project:latest
```

### Container Registry in CI/CD

```yaml
variables:
  IMAGE: $CI_REGISTRY_IMAGE

build-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker build -t $IMAGE:latest .
    - docker push $IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $IMAGE:latest

# Using Kaniko (no Docker-in-Docker needed)
build-kaniko:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.22.0-debug
    entrypoint: [""]
  script:
    - |
      /kaniko/executor \
        --context $CI_PROJECT_DIR \
        --dockerfile $CI_PROJECT_DIR/Dockerfile \
        --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA \
        --destination $CI_REGISTRY_IMAGE:latest \
        --cache=true \
        --cache-repo=$CI_REGISTRY_IMAGE/cache
```

### Multi-Architecture Images

```yaml
build-multiarch:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: 1
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker buildx create --use
  script:
    - docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA \
        --push .
```

### Cleanup Policies

**Settings → Packages and registries → Container registry → Cleanup policies**

```
Expiration policy:
  Enabled: Yes
  Expiration interval: 90 days
  Number of tags to keep: 5
  Tags with names matching: .*
  Tags to exclude: latest, stable, v*
```

```bash
# Manual cleanup via API
curl --request DELETE \
  --header "PRIVATE-TOKEN: <token>" \
  "https://gitlab.example.com/api/v4/projects/<id>/registry/repositories/<repo_id>/tags/<tag_name>"

# Bulk delete old tags
curl --request DELETE \
  --header "PRIVATE-TOKEN: <token>" \
  --data "name_regex_delete=.*" \
  --data "keep_n=5" \
  --data "older_than=30d" \
  "https://gitlab.example.com/api/v4/projects/<id>/registry/repositories/<repo_id>/tags"
```

## Package Registry

GitLab can host packages for multiple formats.

### Supported Package Types

| Format | Language/Tool |
|--------|--------------|
| **npm** | JavaScript/Node.js |
| **Maven** | Java |
| **PyPI** | Python |
| **NuGet** | .NET |
| **Composer** | PHP |
| **Conan** | C/C++ |
| **Helm** | Kubernetes |
| **Go** | Go modules |
| **Generic** | Any file |
| **Terraform** | Terraform modules |

### npm Registry

```bash
# Configure .npmrc
echo "@myorg:registry=https://gitlab.example.com/api/v4/projects/<project-id>/packages/npm/
//gitlab.example.com/api/v4/projects/<project-id>/packages/npm/:_authToken=<token>" > .npmrc

# Publish
npm publish

# Install
npm install @myorg/my-package
```

```yaml
# CI/CD publish
publish-npm:
  stage: deploy
  image: node:20
  script:
    - echo "@${CI_PROJECT_ROOT_NAMESPACE}:registry=https://${CI_SERVER_HOST}/api/v4/projects/${CI_PROJECT_ID}/packages/npm/" > .npmrc
    - echo "//${CI_SERVER_HOST}/api/v4/projects/${CI_PROJECT_ID}/packages/npm/:_authToken=${CI_JOB_TOKEN}" >> .npmrc
    - npm publish
  rules:
    - if: $CI_COMMIT_TAG
```

### Maven Registry

```xml
<!-- pom.xml -->
<repositories>
  <repository>
    <id>gitlab-maven</id>
    <url>https://gitlab.example.com/api/v4/projects/${project.id}/packages/maven</url>
  </repository>
</repositories>

<distributionManagement>
  <repository>
    <id>gitlab-maven</id>
    <url>https://gitlab.example.com/api/v4/projects/${project.id}/packages/maven</url>
  </repository>
</distributionManagement>
```

```yaml
# CI/CD publish
publish-maven:
  stage: deploy
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn deploy -s ci_settings.xml
  rules:
    - if: $CI_COMMIT_TAG
```

### PyPI Registry

```bash
# Configure pip
pip install --index-url https://__token__:<token>@gitlab.example.com/api/v4/projects/<id>/packages/pypi/simple my-package
```

```yaml
# CI/CD publish
publish-pypi:
  stage: deploy
  image: python:3.12
  script:
    - pip install twine build
    - python -m build
    - TWINE_PASSWORD=${CI_JOB_TOKEN} TWINE_USERNAME=gitlab-ci-token
      python -m twine upload
      --repository-url https://${CI_SERVER_HOST}/api/v4/projects/${CI_PROJECT_ID}/packages/pypi
      dist/*
  rules:
    - if: $CI_COMMIT_TAG
```

### Helm Chart Registry

```bash
# Package chart
helm package ./my-chart

# Push to GitLab
curl --request POST \
  --form "chart=@my-chart-1.0.0.tgz" \
  --user "<username>:<token>" \
  "https://gitlab.example.com/api/v4/projects/<id>/packages/helm/api/stable/charts"

# Add as Helm repo
helm repo add my-project \
  https://gitlab.example.com/api/v4/projects/<id>/packages/helm/stable \
  --username <username> --password <token>

# Install
helm install my-release my-project/my-chart
```

### Generic Package Registry

Store any file type:

```yaml
upload-binary:
  stage: deploy
  script:
    - |
      curl --header "JOB-TOKEN: $CI_JOB_TOKEN" \
        --upload-file build/myapp-linux-amd64 \
        "https://${CI_SERVER_HOST}/api/v4/projects/${CI_PROJECT_ID}/packages/generic/myapp/${CI_COMMIT_TAG}/myapp-linux-amd64"

download-binary:
  stage: deploy
  script:
    - |
      curl --header "JOB-TOKEN: $CI_JOB_TOKEN" \
        --output myapp \
        "https://${CI_SERVER_HOST}/api/v4/projects/${CI_PROJECT_ID}/packages/generic/myapp/1.0.0/myapp-linux-amd64"
```

## Dependency Proxy

Cache upstream container images to reduce external pulls and improve reliability.

### Enable

**Group → Settings → Packages and registries → Dependency Proxy → Enable**

### Usage

```bash
# Instead of:
docker pull docker.io/library/node:20

# Use:
docker pull gitlab.example.com/my-group/dependency_proxy/containers/node:20
```

```yaml
# In .gitlab-ci.yml
build:
  image: ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/node:20
  services:
    - name: ${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}/postgres:16
      alias: db
  script:
    - npm ci && npm test
```

Benefits:
- Avoids Docker Hub rate limits
- Faster pulls (cached locally)
- Builds work even if Docker Hub is down
- Reduces external network traffic
