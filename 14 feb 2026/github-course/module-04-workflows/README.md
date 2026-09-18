# Module 04 — Workflows

## Workflow Patterns

### Matrix Strategy

Run the same job with different configurations:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        exclude:
          - os: macos-latest
            node-version: 18
        include:
          - os: ubuntu-latest
            node-version: 20
            coverage: true
      fail-fast: false               # Don't cancel other jobs on failure
      max-parallel: 4                # Limit concurrent jobs

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
      - if: matrix.coverage
        run: npm run test:coverage
```

This creates 8 jobs (3 OS x 3 Node versions - 1 exclusion).

### Reusable Workflows

Define a workflow that can be called from other workflows.

```yaml
# .github/workflows/reusable-build.yml
name: Reusable Build

on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '20'
      environment:
        required: true
        type: string
    secrets:
      deploy-key:
        required: true
    outputs:
      image-tag:
        description: "Built image tag"
        value: ${{ jobs.build.outputs.tag }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      tag: ${{ steps.meta.outputs.tag }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci && npm run build
      - id: meta
        run: echo "tag=${{ github.sha }}" >> $GITHUB_OUTPUT
      - run: ./deploy.sh ${{ inputs.environment }}
        env:
          DEPLOY_KEY: ${{ secrets.deploy-key }}
```

```yaml
# .github/workflows/ci.yml (caller)
name: CI

on:
  push:
    branches: [main]

jobs:
  build-staging:
    uses: ./.github/workflows/reusable-build.yml
    with:
      environment: staging
      node-version: '20'
    secrets:
      deploy-key: ${{ secrets.STAGING_DEPLOY_KEY }}

  build-production:
    needs: build-staging
    uses: ./.github/workflows/reusable-build.yml
    with:
      environment: production
    secrets:
      deploy-key: ${{ secrets.PROD_DEPLOY_KEY }}

  notify:
    needs: build-production
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deployed ${{ needs.build-production.outputs.image-tag }}"
```

### Cross-Repository Reusable Workflows

```yaml
# Call workflow from another repository
jobs:
  deploy:
    uses: my-org/shared-workflows/.github/workflows/deploy.yml@main
    with:
      environment: production
    secrets: inherit                 # Pass all secrets
```

## Environments

### Environment Configuration

**Settings → Environments → New environment**

```
Environment: production
├── Protection rules:
│   ├── Required reviewers: @team-leads (up to 6)
│   ├── Wait timer: 30 minutes
│   └── Deployment branches: main only
├── Environment secrets:
│   ├── AWS_ACCESS_KEY_ID
│   └── AWS_SECRET_ACCESS_KEY
└── Environment variables:
    ├── API_URL: https://api.example.com
    └── CLUSTER: prod-cluster
```

### Using Environments

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - run: ./deploy.sh
        env:
          API_URL: ${{ vars.API_URL }}           # Environment variable
          AWS_KEY: ${{ secrets.AWS_ACCESS_KEY_ID }} # Environment secret

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production                           # Requires approval
      url: https://example.com
    steps:
      - run: ./deploy.sh
```

## Caching

### actions/cache

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Cache npm dependencies
      - uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            npm-${{ runner.os }}-

      - run: npm ci
      - run: npm run build
```

### Built-in Caching (setup-* actions)

```yaml
# Node.js
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'                     # Automatic caching

# Python
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'

# Go
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true

# Java/Maven
- uses: actions/setup-java@v4
  with:
    distribution: 'temurin'
    java-version: '17'
    cache: 'maven'
```

### Docker Layer Caching

```yaml
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Artifacts

### Upload and Download

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7
          if-no-files-found: error

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - run: ls -la dist/
      - run: ./deploy.sh
```

### Multiple Artifacts

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: |
            test-results/
            coverage/
          retention-days: 14
```

## Concurrency Control

```yaml
# Cancel previous runs on the same branch
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Per-environment concurrency (don't cancel deployments)
jobs:
  deploy:
    concurrency:
      group: deploy-production
      cancel-in-progress: false      # Queue instead of cancel
```

## Workflow Composition Patterns

### Monorepo Pattern

```yaml
name: Monorepo CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      infra: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            frontend:
              - 'frontend/**'
            backend:
              - 'backend/**'
            infra:
              - 'terraform/**'

  frontend:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test && npm run build

  backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - run: go test ./... && go build ./cmd/server
```

### Release Pattern

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - goos: linux
            goarch: amd64
          - goos: linux
            goarch: arm64
          - goos: darwin
            goarch: amd64
          - goos: darwin
            goarch: arm64
          - goos: windows
            goarch: amd64
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: |
          GOOS=${{ matrix.goos }} GOARCH=${{ matrix.goarch }} \
          go build -o myapp-${{ matrix.goos }}-${{ matrix.goarch }} ./cmd/myapp
      - uses: actions/upload-artifact@v4
        with:
          name: binary-${{ matrix.goos }}-${{ matrix.goarch }}
          path: myapp-*

  release:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          merge-multiple: true

      - uses: softprops/action-gh-release@v2
        with:
          files: myapp-*
          generate_release_notes: true
```

### GitOps Pattern

```yaml
name: GitOps Deploy

on:
  push:
    branches: [main]

jobs:
  build-push:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ github.sha }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

  update-manifests:
    needs: build-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: my-org/k8s-manifests
          token: ${{ secrets.GITOPS_TOKEN }}

      - name: Update image tag
        run: |
          sed -i "s|image: ghcr.io/.*|image: ghcr.io/${{ github.repository }}:${{ github.sha }}|" \
            apps/myapp/deployment.yaml

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "Update myapp to ${{ github.sha }}"
          git push
```

## Workflow Debugging

```yaml
# Enable debug logging
# Set secret: ACTIONS_STEP_DEBUG = true
# Set secret: ACTIONS_RUNNER_DEBUG = true

# Or use tmate for interactive debugging
- uses: mxschmitt/action-tmate@v3
  if: failure()
  with:
    limit-access-to-actor: true
```

```bash
# Re-run with debug logging
gh run rerun <run-id> --debug
```
