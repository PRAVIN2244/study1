# Module 08 — Packages and Registry

## GitHub Packages Overview

GitHub Packages hosts software packages alongside your source code.

| Registry | Format | URL |
|----------|--------|-----|
| **Container (GHCR)** | Docker/OCI | `ghcr.io` |
| **npm** | Node.js | `npm.pkg.github.com` |
| **Maven** | Java | `maven.pkg.github.com` |
| **Gradle** | Java | `maven.pkg.github.com` |
| **NuGet** | .NET | `nuget.pkg.github.com` |
| **RubyGems** | Ruby | `rubygems.pkg.github.com` |

## GitHub Container Registry (GHCR)

### Authentication

```bash
# Login with PAT
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# In GitHub Actions (automatic)
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### Build and Push

```yaml
name: Build Container

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Multi-Architecture Build

```yaml
- uses: docker/setup-qemu-action@v3
- uses: docker/setup-buildx-action@v3

- uses: docker/build-push-action@v5
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ghcr.io/${{ github.repository }}:latest
```

### Package Visibility

```bash
# Set package visibility via API
# Packages inherit repository visibility by default

# Make public
curl -X PATCH \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/user/packages/container/my-image" \
  -d '{"visibility":"public"}'
```

### Pull Images

```bash
# Public packages (no auth needed)
docker pull ghcr.io/owner/image:tag

# Private packages
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/owner/image:tag

# In Kubernetes
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=USERNAME \
  --docker-password=$GITHUB_TOKEN
```

## npm Registry

### Configure

```bash
# .npmrc
@my-org:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

### Publish

```yaml
# package.json
{
  "name": "@my-org/my-package",
  "version": "1.0.0",
  "publishConfig": {
    "registry": "https://npm.pkg.github.com"
  }
}
```

```yaml
# Workflow
name: Publish npm Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://npm.pkg.github.com'
          scope: '@my-org'
      - run: npm ci
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Install

```bash
# Configure npm to use GitHub Packages for @my-org scope
echo "@my-org:registry=https://npm.pkg.github.com" >> .npmrc
echo "//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}" >> .npmrc

npm install @my-org/my-package
```

## Maven Registry

### Configure

```xml
<!-- pom.xml -->
<distributionManagement>
  <repository>
    <id>github</id>
    <name>GitHub Packages</name>
    <url>https://maven.pkg.github.com/OWNER/REPO</url>
  </repository>
</distributionManagement>
```

```xml
<!-- ~/.m2/settings.xml -->
<settings>
  <servers>
    <server>
      <id>github</id>
      <username>USERNAME</username>
      <password>${GITHUB_TOKEN}</password>
    </server>
  </servers>
</settings>
```

### Publish

```yaml
name: Publish Maven Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      - run: mvn deploy
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## NuGet Registry

### Publish

```yaml
name: Publish NuGet Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0'
      - run: dotnet pack --configuration Release
      - run: dotnet nuget push "**/*.nupkg" \
          --source "https://nuget.pkg.github.com/OWNER/index.json" \
          --api-key ${{ secrets.GITHUB_TOKEN }}
```

### Install

```bash
dotnet nuget add source \
  "https://nuget.pkg.github.com/OWNER/index.json" \
  --name github \
  --username USERNAME \
  --password $GITHUB_TOKEN

dotnet add package My.Package --source github
```

## Package Management

### Delete Packages

```bash
# Delete a package version via API
curl -X DELETE \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/user/packages/container/my-image/versions/12345"

# List package versions
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/user/packages/container/my-image/versions"
```

### Cleanup Old Packages

```yaml
name: Cleanup Old Packages

on:
  schedule:
    - cron: '0 0 * * 0'             # Weekly

jobs:
  cleanup:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/delete-package-versions@v5
        with:
          package-name: 'my-image'
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: true
```

## Package Security

1. **Use GITHUB_TOKEN** — scoped to the repository, auto-expires
2. **Set package visibility** appropriately (public vs private)
3. **Enable Dependabot** for packages you consume
4. **Sign packages** when possible
5. **Use immutable tags** — don't overwrite existing versions
6. **Scan container images** before publishing
7. **Set retention policies** — clean up old versions

```yaml
# Scan before push
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'

- name: Upload scan results
  uses: github/codeql-action/upload-sarif@v3
  if: always()
  with:
    sarif_file: 'trivy-results.sarif'
```
