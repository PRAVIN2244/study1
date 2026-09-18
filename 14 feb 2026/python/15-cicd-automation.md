# Module 15 — CI/CD Automation with Python

CI/CD (Continuous Integration / Continuous Delivery) automates building, testing, and deploying code. Python can interact with CI/CD systems — triggering pipelines, monitoring builds, generating pipeline configurations, and orchestrating deployments across environments.

---

## CI/CD Pipeline Flow

```
Developer pushes code
        |
        v
CI Pipeline Triggers
        |
        v
+-------+-------+-------+-------+
|       |       |       |       |
v       v       v       v       v
Lint   Test   Build  Security  Docs
|       |       |       |       |
+-------+-------+-------+-------+
        |
        v
   All passed?
        |
   +----+----+
   |         |
  Yes        No
   |         |
   v         v
Deploy    Notify
to staging  team
   |
   v
Smoke tests
   |
   +----+----+
   |         |
  Pass      Fail
   |         |
   v         v
Deploy    Rollback
to prod   staging
```

---

## GitHub Actions — Generating Workflows

### Generating a Workflow File

```python
import yaml
from pathlib import Path

def generate_ci_workflow(app_name, language="python", python_version="3.11",
                          output_dir=".github/workflows"):
    """Generate a GitHub Actions CI workflow."""
    workflow = {
        "name": f"CI - {app_name}",
        "on": {
            "push": {"branches": ["main", "develop"]},
            "pull_request": {"branches": ["main"]}
        },
        "jobs": {
            "test": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": f"Set up Python {python_version}",
                        "uses": "actions/setup-python@v5",
                        "with": {"python-version": python_version}
                    },
                    {
                        "name": "Install dependencies",
                        "run": "pip install -r requirements.txt"
                    },
                    {
                        "name": "Run linter",
                        "run": "pip install flake8 && flake8 ."
                    },
                    {
                        "name": "Run tests",
                        "run": "pytest -v --tb=short"
                    }
                ]
            }
        }
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / "ci.yml"
    with open(filepath, "w") as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated: {filepath}")
    return str(filepath)

# Usage:
generate_ci_workflow("myapp", python_version="3.12")
```

### Generating a CD Workflow

```python
import yaml
from pathlib import Path

def generate_cd_workflow(app_name, environments=None, output_dir=".github/workflows"):
    """Generate a GitHub Actions deployment workflow."""
    if environments is None:
        environments = ["staging", "production"]
    
    jobs = {}
    previous = None
    
    for env in environments:
        job = {
            "runs-on": "ubuntu-latest",
            "environment": env,
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": f"Deploy to {env}",
                    "run": f"echo 'Deploying to {env}...'"
                },
                {
                    "name": "Run smoke tests",
                    "run": f"echo 'Testing {env}...'"
                }
            ]
        }
        
        # Production requires manual approval (via GitHub environment protection)
        if env == "production":
            job["needs"] = [previous] if previous else []
        elif previous:
            job["needs"] = [previous]
        
        jobs[f"deploy-{env}"] = job
        previous = f"deploy-{env}"
    
    workflow = {
        "name": f"CD - {app_name}",
        "on": {
            "push": {"branches": ["main"]},
            "workflow_dispatch": {}    # Allow manual triggers
        },
        "jobs": jobs
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / "cd.yml"
    with open(filepath, "w") as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated: {filepath}")

# Usage:
generate_cd_workflow("myapp", environments=["staging", "production"])
```

---

## GitHub Actions API — Monitoring Workflows

### Listing Workflow Runs

```python
import requests
import os

class GitHubActionsClient:
    """Client for GitHub Actions API."""
    
    def __init__(self, owner, repo):
        self.owner = owner
        self.repo = repo
        self.token = os.environ.get("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_workflow_runs(self, status=None, limit=10):
        """Get recent workflow runs."""
        params = {"per_page": limit}
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.base_url}/actions/runs",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()["workflow_runs"]
    
    def get_run_status(self, run_id):
        """Get status of a specific workflow run."""
        response = requests.get(
            f"{self.base_url}/actions/runs/{run_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def trigger_workflow(self, workflow_id, ref="main", inputs=None):
        """Trigger a workflow dispatch event."""
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        
        response = requests.post(
            f"{self.base_url}/actions/workflows/{workflow_id}/dispatches",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 204:
            print(f"Workflow triggered on branch: {ref}")
            return True
        else:
            print(f"Failed: {response.status_code} - {response.text}")
            return False

# Usage:
# gh = GitHubActionsClient("myorg", "myrepo")
# runs = gh.get_workflow_runs(status="completed", limit=5)
# for run in runs:
#     print(f"  {run['name']}: {run['conclusion']} ({run['created_at']})")
```

### Monitoring a Workflow Run

```python
import time

def wait_for_workflow(client, run_id, timeout=600, poll_interval=15):
    """Wait for a workflow run to complete."""
    start = time.time()
    
    while time.time() - start < timeout:
        run = client.get_run_status(run_id)
        status = run["status"]
        conclusion = run.get("conclusion")
        
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] Status: {status}, Conclusion: {conclusion or 'pending'}")
        
        if status == "completed":
            if conclusion == "success":
                print(f"\nWorkflow passed! ({elapsed}s)")
                return True
            else:
                print(f"\nWorkflow {conclusion}! ({elapsed}s)")
                return False
        
        time.sleep(poll_interval)
    
    print(f"\nTimeout after {timeout}s")
    return False

# Usage:
# gh = GitHubActionsClient("myorg", "myrepo")
# gh.trigger_workflow("ci.yml", ref="main")
# runs = gh.get_workflow_runs(limit=1)
# wait_for_workflow(gh, runs[0]["id"])
```

---

## Jenkins Automation

### Triggering Jenkins Jobs

```python
import requests
import os
import time

class JenkinsClient:
    """Client for Jenkins API."""
    
    def __init__(self, url=None, user=None, token=None):
        self.url = url or os.environ.get("JENKINS_URL", "http://localhost:8080")
        self.user = user or os.environ.get("JENKINS_USER")
        self.token = token or os.environ.get("JENKINS_TOKEN")
        self.auth = (self.user, self.token) if self.user else None
    
    def trigger_build(self, job_name, parameters=None):
        """Trigger a Jenkins build."""
        if parameters:
            endpoint = f"{self.url}/job/{job_name}/buildWithParameters"
            response = requests.post(endpoint, auth=self.auth, params=parameters)
        else:
            endpoint = f"{self.url}/job/{job_name}/build"
            response = requests.post(endpoint, auth=self.auth)
        
        if response.status_code in (200, 201):
            print(f"Build triggered: {job_name}")
            # Get the queue item URL from the Location header
            queue_url = response.headers.get("Location")
            return queue_url
        else:
            print(f"Failed: {response.status_code}")
            return None
    
    def get_build_status(self, job_name, build_number="lastBuild"):
        """Get the status of a Jenkins build."""
        endpoint = f"{self.url}/job/{job_name}/{build_number}/api/json"
        response = requests.get(endpoint, auth=self.auth)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "number": data["number"],
                "result": data.get("result"),
                "building": data["building"],
                "duration": data["duration"],
                "url": data["url"]
            }
        return None
    
    def get_build_log(self, job_name, build_number="lastBuild"):
        """Get the console output of a build."""
        endpoint = f"{self.url}/job/{job_name}/{build_number}/consoleText"
        response = requests.get(endpoint, auth=self.auth)
        return response.text if response.status_code == 200 else None
    
    def wait_for_build(self, job_name, build_number, timeout=600):
        """Wait for a build to complete."""
        start = time.time()
        
        while time.time() - start < timeout:
            status = self.get_build_status(job_name, build_number)
            
            if status and not status["building"]:
                return status
            
            elapsed = int(time.time() - start)
            print(f"  [{elapsed}s] Building...")
            time.sleep(10)
        
        print(f"Timeout after {timeout}s")
        return None

# Usage:
# jenkins = JenkinsClient()
# jenkins.trigger_build("deploy-app", parameters={"VERSION": "2.3.1", "ENV": "staging"})
# status = jenkins.get_build_status("deploy-app")
# print(f"Last build: #{status['number']} - {status['result']}")
```

---

## Pipeline Orchestrator

A tool that coordinates deployments across multiple stages:

```python
import time
from datetime import datetime

class PipelineOrchestrator:
    """Orchestrate multi-stage deployment pipelines."""
    
    def __init__(self):
        self.stages = []
        self.results = []
    
    def add_stage(self, name, func, **kwargs):
        """Add a stage to the pipeline."""
        self.stages.append({
            "name": name,
            "func": func,
            "kwargs": kwargs
        })
    
    def run(self, dry_run=False):
        """Execute all stages in order."""
        print(f"\n{'='*60}")
        print(f"Pipeline Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Stages: {len(self.stages)}")
        print(f"{'='*60}")
        
        for i, stage in enumerate(self.stages, 1):
            print(f"\n[{i}/{len(self.stages)}] {stage['name']}")
            print("-" * 40)
            
            start = time.time()
            
            try:
                if dry_run:
                    print(f"  [DRY RUN] Would execute: {stage['name']}")
                    success = True
                else:
                    success = stage["func"](**stage["kwargs"])
                
                duration = time.time() - start
                status = "PASSED" if success else "FAILED"
                
                self.results.append({
                    "stage": stage["name"],
                    "status": status,
                    "duration": duration
                })
                
                print(f"  Result: {status} ({duration:.1f}s)")
                
                if not success:
                    print(f"\nPipeline FAILED at stage: {stage['name']}")
                    return False
                
            except Exception as e:
                duration = time.time() - start
                self.results.append({
                    "stage": stage["name"],
                    "status": "ERROR",
                    "duration": duration,
                    "error": str(e)
                })
                print(f"  ERROR: {e}")
                print(f"\nPipeline FAILED at stage: {stage['name']}")
                return False
        
        print(f"\n{'='*60}")
        print("Pipeline PASSED")
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print pipeline execution summary."""
        print(f"\nSummary:")
        total_time = sum(r["duration"] for r in self.results)
        
        for r in self.results:
            icon = "OK" if r["status"] == "PASSED" else "!!"
            print(f"  [{icon}] {r['stage']}: {r['status']} ({r['duration']:.1f}s)")
        
        print(f"\nTotal time: {total_time:.1f}s")

# Example stage functions
def run_tests():
    print("  Running unit tests...")
    time.sleep(0.5)
    return True

def build_image(tag="latest"):
    print(f"  Building Docker image: myapp:{tag}")
    time.sleep(0.5)
    return True

def deploy(environment="staging"):
    print(f"  Deploying to {environment}...")
    time.sleep(0.5)
    return True

def smoke_test(url="http://localhost:8080"):
    print(f"  Running smoke tests against {url}...")
    time.sleep(0.5)
    return True

# Usage:
pipeline = PipelineOrchestrator()
pipeline.add_stage("Unit Tests", run_tests)
pipeline.add_stage("Build Image", build_image, tag="2.3.1")
pipeline.add_stage("Deploy to Staging", deploy, environment="staging")
pipeline.add_stage("Smoke Tests", smoke_test, url="https://staging.example.com")
pipeline.add_stage("Deploy to Production", deploy, environment="production")

pipeline.run(dry_run=True)
```

**Output:**

```
============================================================
Pipeline Started: 2024-01-15 14:30:00
Stages: 5
============================================================

[1/5] Unit Tests
----------------------------------------
  [DRY RUN] Would execute: Unit Tests
  Result: PASSED (0.0s)

[2/5] Build Image
----------------------------------------
  [DRY RUN] Would execute: Build Image
  Result: PASSED (0.0s)

...

============================================================
Pipeline PASSED

Summary:
  [OK] Unit Tests: PASSED (0.0s)
  [OK] Build Image: PASSED (0.0s)
  [OK] Deploy to Staging: PASSED (0.0s)
  [OK] Smoke Tests: PASSED (0.0s)
  [OK] Deploy to Production: PASSED (0.0s)

Total time: 0.0s
```

---

## Build Notification System

```python
import requests
import os
from datetime import datetime

def notify_build_result(pipeline_name, status, stages, duration,
                         channel="builds"):
    """Send build notification to Slack."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set, skipping notification")
        return
    
    color = "good" if status == "PASSED" else "danger"
    emoji = ":white_check_mark:" if status == "PASSED" else ":x:"
    
    stage_text = "\n".join(
        f"{'✓' if s['status'] == 'PASSED' else '✗'} {s['stage']} ({s['duration']:.1f}s)"
        for s in stages
    )
    
    payload = {
        "channel": channel,
        "attachments": [{
            "color": color,
            "title": f"{emoji} Pipeline: {pipeline_name} — {status}",
            "fields": [
                {"title": "Duration", "value": f"{duration:.0f}s", "short": True},
                {"title": "Time", "value": datetime.now().strftime("%H:%M:%S"), "short": True}
            ],
            "text": f"```\n{stage_text}\n```"
        }]
    }
    
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 200:
        print("Notification sent to Slack")
    else:
        print(f"Notification failed: {response.status_code}")
```

---

## Exercises

**Exercise 1:** Write a script that generates a GitHub Actions workflow for a Node.js project (install, lint, test, build).

**Exercise 2:** Build a pipeline monitor that polls GitHub Actions every 30 seconds and prints the status of the latest workflow run.

**Exercise 3:** Write a deployment orchestrator that deploys to staging, runs tests, and only deploys to production if staging tests pass.

**Exercise 4:** Build a CLI tool that triggers a Jenkins build, waits for it to complete, and prints the result with the last 20 lines of the build log.

---

## Common Mistakes

### 1. Not Waiting for Pipeline Completion

Triggering a build and assuming it succeeded without checking the result.

### 2. No Rollback Plan

Always have a way to roll back if a deployment fails. Include a rollback stage in your pipeline.

### 3. Hardcoding CI/CD URLs and Credentials

Use environment variables for Jenkins URLs, GitHub tokens, and Slack webhooks.

### 4. Not Testing Pipeline Changes

Test workflow file changes in a branch before merging to main. A broken CI config blocks the entire team.

---

## Summary

| System | Python Integration | Key Operations |
|--------|-------------------|----------------|
| GitHub Actions | REST API + YAML generation | Trigger, monitor, generate workflows |
| Jenkins | REST API | Trigger builds, get status, read logs |
| Custom Pipeline | Python orchestrator | Stage management, notifications |

---

[Previous: Module 14 — AWS Automation](14-aws-automation-using-boto3.md) | [Next: Module 16 — Monitoring Automation](16-monitoring-automation.md)
