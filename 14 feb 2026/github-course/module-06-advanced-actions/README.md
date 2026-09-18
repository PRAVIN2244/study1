# Module 06 — Advanced Actions

## Custom Actions

Three types of custom actions:

| Type | Language | Use Case |
|------|----------|----------|
| **JavaScript** | Node.js | Fast startup, API calls, text processing |
| **Docker** | Any | Custom environments, complex tooling |
| **Composite** | YAML | Combine existing actions and scripts |

## Composite Actions

Combine multiple steps into a reusable action.

```yaml
# .github/actions/setup-and-build/action.yml
name: 'Setup and Build'
description: 'Install dependencies and build the project'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  build-command:
    description: 'Build command to run'
    required: false
    default: 'npm run build'

outputs:
  build-path:
    description: 'Path to build output'
    value: ${{ steps.build.outputs.path }}

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Install dependencies
      shell: bash
      run: npm ci

    - name: Build
      id: build
      shell: bash
      run: |
        ${{ inputs.build-command }}
        echo "path=dist" >> $GITHUB_OUTPUT

    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: build-output
        path: dist/
```

```yaml
# Usage in workflow
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-and-build
        with:
          node-version: '20'
          build-command: 'npm run build:prod'
```

## JavaScript Actions

```
my-action/
├── action.yml          # Action metadata
├── index.js            # Entry point
├── package.json
├── node_modules/       # Must be committed (or use ncc)
└── dist/               # Compiled output (if using ncc)
```

```yaml
# action.yml
name: 'PR Comment'
description: 'Add a comment to a pull request'
inputs:
  message:
    description: 'Comment message'
    required: true
  github-token:
    description: 'GitHub token'
    required: true
    default: ${{ github.token }}
outputs:
  comment-id:
    description: 'ID of the created comment'
runs:
  using: 'node20'
  main: 'dist/index.js'
```

```javascript
// index.js
const core = require('@actions/core');
const github = require('@actions/github');

async function run() {
  try {
    const message = core.getInput('message', { required: true });
    const token = core.getInput('github-token', { required: true });

    const octokit = github.getOctokit(token);
    const context = github.context;

    if (!context.payload.pull_request) {
      core.setFailed('This action only works on pull requests');
      return;
    }

    const { data: comment } = await octokit.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: context.payload.pull_request.number,
      body: message,
    });

    core.setOutput('comment-id', comment.id);
    core.info(`Comment created: ${comment.html_url}`);
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
```

```bash
# Compile with ncc (bundles node_modules)
npm install -g @vercel/ncc
ncc build index.js -o dist
```

## Docker Actions

```yaml
# action.yml
name: 'Security Scan'
description: 'Run security scan on codebase'
inputs:
  scan-type:
    description: 'Type of scan'
    required: false
    default: 'full'
runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.scan-type }}
  env:
    SCAN_CONFIG: '/config/scan.yml'
```

```dockerfile
# Dockerfile
FROM python:3.12-slim

RUN pip install safety bandit

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

```bash
#!/bin/bash
# entrypoint.sh
SCAN_TYPE=$1

echo "Running $SCAN_TYPE security scan..."

if [ "$SCAN_TYPE" = "full" ] || [ "$SCAN_TYPE" = "dependencies" ]; then
    safety check -r requirements.txt
fi

if [ "$SCAN_TYPE" = "full" ] || [ "$SCAN_TYPE" = "code" ]; then
    bandit -r src/ -f json -o bandit-report.json
fi

echo "Scan complete"
```

## Popular Marketplace Actions

### CI/CD

| Action | Purpose |
|--------|---------|
| `actions/checkout@v4` | Check out repository |
| `actions/setup-node@v4` | Setup Node.js |
| `actions/setup-python@v5` | Setup Python |
| `actions/setup-go@v5` | Setup Go |
| `actions/setup-java@v4` | Setup Java |
| `actions/cache@v4` | Cache dependencies |
| `actions/upload-artifact@v4` | Upload build artifacts |
| `actions/download-artifact@v4` | Download artifacts |

### Docker

| Action | Purpose |
|--------|---------|
| `docker/login-action@v3` | Login to container registry |
| `docker/build-push-action@v5` | Build and push Docker images |
| `docker/setup-buildx-action@v3` | Setup Docker Buildx |
| `docker/setup-qemu-action@v3` | Setup QEMU for multi-arch |
| `docker/metadata-action@v5` | Extract Docker metadata |

### Deployment

| Action | Purpose |
|--------|---------|
| `aws-actions/configure-aws-credentials@v4` | Configure AWS credentials |
| `azure/login@v2` | Azure login |
| `google-github-actions/auth@v2` | GCP authentication |
| `hashicorp/setup-terraform@v3` | Setup Terraform |
| `helm/chart-releaser-action@v1` | Helm chart releases |

### Code Quality

| Action | Purpose |
|--------|---------|
| `github/codeql-action/analyze@v3` | CodeQL analysis |
| `sonarsource/sonarcloud-github-action@v2` | SonarCloud scan |
| `reviewdog/action-eslint@v1` | ESLint with PR comments |

## Publishing Actions to Marketplace

1. Create a public repository for your action
2. Add `action.yml` with proper metadata
3. Tag a release: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. Create a GitHub Release
5. Check "Publish this Action to the GitHub Marketplace"
6. Select primary and secondary categories

### Versioning Strategy

```bash
# Tag specific version
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0

# Update major version tag (users reference v1)
git tag -fa v1 -m "Update v1 tag"
git push origin v1 --force
```

Users reference:
- `uses: owner/action@v1` — latest v1.x.x (recommended)
- `uses: owner/action@v1.0.0` — exact version
- `uses: owner/action@main` — latest (not recommended)
- `uses: owner/action@abc123` — specific commit (most secure)

## Advanced Workflow Techniques

### Dynamic Matrix

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: set-matrix
        run: |
          # Generate matrix from directory listing
          SERVICES=$(ls -d services/*/  | xargs -I {} basename {} | jq -R -s -c 'split("\n")[:-1]')
          echo "matrix={\"service\":$SERVICES}" >> $GITHUB_OUTPUT

  build:
    needs: prepare
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.prepare.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - run: echo "Building ${{ matrix.service }}"
        working-directory: services/${{ matrix.service }}
```

### Workflow Dispatch with Dynamic Inputs

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        type: environment
        description: 'Target environment'
      version:
        type: string
        description: 'Version to deploy'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - run: echo "Deploying ${{ inputs.version }} to ${{ inputs.environment }}"
```

### Passing Data Between Jobs

```yaml
jobs:
  job1:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.value }}
      should-deploy: ${{ steps.check.outputs.deploy }}
    steps:
      - id: version
        run: echo "value=1.2.3" >> $GITHUB_OUTPUT
      - id: check
        run: echo "deploy=true" >> $GITHUB_OUTPUT

  job2:
    needs: job1
    if: needs.job1.outputs.should-deploy == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying version ${{ needs.job1.outputs.version }}"
```

### Conditional Job Execution

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    outputs:
      should-run: ${{ steps.check.outputs.result }}
    steps:
      - id: check
        run: |
          if [[ "${{ github.event.head_commit.message }}" == *"[skip ci]"* ]]; then
            echo "result=false" >> $GITHUB_OUTPUT
          else
            echo "result=true" >> $GITHUB_OUTPUT
          fi

  build:
    needs: check
    if: needs.check.outputs.should-run == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building..."
```
