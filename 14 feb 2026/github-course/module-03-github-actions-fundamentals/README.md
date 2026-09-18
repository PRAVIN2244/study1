# Module 03 — GitHub Actions Fundamentals

## Overview

GitHub Actions is GitHub's built-in CI/CD platform. Workflows are defined in YAML files stored in `.github/workflows/`.

```
Repository
└── .github/
    └── workflows/
        ├── ci.yml           # CI pipeline
        ├── deploy.yml       # Deployment pipeline
        └── release.yml      # Release pipeline
```

## Workflow Structure

```yaml
# .github/workflows/ci.yml

name: CI Pipeline                    # Workflow name (shown in UI)

on:                                  # Trigger events
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:                                 # Workflow-level environment variables
  NODE_VERSION: '20'

jobs:                                # Define jobs
  build:                             # Job ID
    name: Build Application          # Job display name
    runs-on: ubuntu-latest           # Runner type
    steps:                           # Job steps
      - name: Checkout code
        uses: actions/checkout@v4    # Use an action

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install dependencies
        run: npm ci                  # Run a command

      - name: Build
        run: npm run build

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: build                     # Depends on build job
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - run: npm ci
      - run: npm test
```

## Trigger Events (on)

### Push and Pull Request

```yaml
on:
  push:
    branches:
      - main
      - 'release/**'
    tags:
      - 'v*'
    paths:
      - 'src/**'
      - 'package.json'
    paths-ignore:
      - '**.md'
      - 'docs/**'

  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

  pull_request_target:               # Runs in context of base branch
    types: [opened, synchronize]
```

### Schedule (Cron)

```yaml
on:
  schedule:
    - cron: '0 2 * * *'             # Daily at 2 AM UTC
    - cron: '0 */6 * * *'           # Every 6 hours
```

### Manual Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - staging
          - production
      version:
        description: 'Version to deploy'
        required: true
        type: string
        default: 'latest'
      dry_run:
        description: 'Dry run mode'
        type: boolean
        default: false
```

```yaml
# Use inputs in jobs
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying ${{ inputs.version }} to ${{ inputs.environment }}"
      - if: ${{ !inputs.dry_run }}
        run: ./deploy.sh ${{ inputs.environment }}
```

### Other Events

```yaml
on:
  release:
    types: [published]

  issues:
    types: [opened, labeled]

  workflow_run:                      # After another workflow completes
    workflows: ["CI"]
    types: [completed]

  repository_dispatch:               # External webhook trigger
    types: [deploy]
```

## Jobs

### Job Configuration

```yaml
jobs:
  build:
    runs-on: ubuntu-latest           # Runner
    timeout-minutes: 30              # Job timeout
    continue-on-error: false         # Fail workflow if job fails
    concurrency:                     # Prevent concurrent runs
      group: build-${{ github.ref }}
      cancel-in-progress: true

    permissions:                     # GITHUB_TOKEN permissions
      contents: read
      packages: write
      pull-requests: write

    environment:                     # Deployment environment
      name: production
      url: https://example.com

    defaults:
      run:
        working-directory: ./app     # Default working directory
        shell: bash                  # Default shell

    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
```

### Job Dependencies

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  build:
    needs: [lint, test]              # Runs after both lint and test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

  deploy:
    needs: build                     # Runs after build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

```
lint ──┐
       ├──▶ build ──▶ deploy
test ──┘
```

### Job Outputs

```yaml
jobs:
  version:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.get-version.outputs.version }}
    steps:
      - id: get-version
        run: echo "version=$(cat VERSION)" >> $GITHUB_OUTPUT

  build:
    needs: version
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building version ${{ needs.version.outputs.version }}"
```

## Steps

### Using Actions

```yaml
steps:
  # Action from GitHub marketplace
  - uses: actions/checkout@v4

  # Action with inputs
  - uses: actions/setup-node@v4
    with:
      node-version: '20'
      cache: 'npm'

  # Action from another repository
  - uses: owner/repo@v1

  # Action from a specific commit
  - uses: owner/repo@abc123

  # Local action (in same repo)
  - uses: ./.github/actions/my-action
```

### Running Commands

```yaml
steps:
  # Single command
  - run: echo "Hello World"

  # Multi-line command
  - run: |
      echo "Line 1"
      echo "Line 2"
      npm ci
      npm test

  # Named step
  - name: Build application
    run: npm run build

  # With working directory
  - name: Build backend
    run: mvn package
    working-directory: ./backend

  # With specific shell
  - name: PowerShell step
    run: Write-Host "Hello"
    shell: pwsh

  # With environment variables
  - name: Deploy
    run: ./deploy.sh
    env:
      API_KEY: ${{ secrets.API_KEY }}
      ENVIRONMENT: production
```

### Conditional Steps

```yaml
steps:
  - name: Deploy to production
    if: github.ref == 'refs/heads/main'
    run: ./deploy.sh production

  - name: Deploy to staging
    if: github.ref == 'refs/heads/develop'
    run: ./deploy.sh staging

  - name: Comment on PR
    if: github.event_name == 'pull_request'
    run: echo "This is a PR"

  - name: Run on failure
    if: failure()
    run: echo "Previous step failed"

  - name: Always run
    if: always()
    run: echo "Cleanup"

  - name: Run on success
    if: success()
    run: echo "All good"

  - name: Conditional on output
    if: steps.check.outputs.changed == 'true'
    run: npm run build
```

## Variables and Secrets

### Environment Variables

```yaml
# Workflow level
env:
  APP_NAME: my-app

jobs:
  build:
    # Job level
    env:
      NODE_ENV: production
    steps:
      - name: Build
        # Step level
        env:
          API_URL: https://api.example.com
        run: |
          echo "App: $APP_NAME"
          echo "Env: $NODE_ENV"
          echo "API: $API_URL"
```

### Secrets

Set in **Settings → Secrets and variables → Actions**

```yaml
steps:
  - name: Deploy
    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    run: aws s3 sync dist/ s3://my-bucket/

  - name: Docker login
    run: echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
```

### GitHub Context Variables

| Context | Description |
|---------|-------------|
| `github.sha` | Commit SHA |
| `github.ref` | Full ref (refs/heads/main) |
| `github.ref_name` | Short ref (main) |
| `github.event_name` | Event that triggered workflow |
| `github.actor` | User who triggered workflow |
| `github.repository` | owner/repo |
| `github.workspace` | Workspace directory path |
| `github.run_id` | Unique workflow run ID |
| `github.run_number` | Run number for this workflow |
| `github.token` | Auto-generated GITHUB_TOKEN |
| `runner.os` | Runner OS (Linux, Windows, macOS) |

## Services (Sidecar Containers)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379
```

## Complete Example

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm test
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - name: Deploy
        run: echo "Deploying to production..."
```
