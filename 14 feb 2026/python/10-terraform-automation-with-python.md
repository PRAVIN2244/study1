# Module 10 — Terraform Automation with Python

Terraform manages infrastructure as code — servers, databases, networks, DNS. While you write Terraform in HCL, Python can automate the workflow around it: running plans, parsing output, auditing state files, enforcing policies, and integrating Terraform into larger automation pipelines.

---

## Prerequisites

Terraform must be installed:

```bash
terraform --version
```

```
Terraform v1.7.0
```

No special Python packages are needed — we use `subprocess` to run Terraform commands and `json` to parse output.

---

## Running Terraform Commands from Python

### The subprocess Wrapper

```python
import subprocess
import json

def run_terraform(command, working_dir=".", capture_json=False):
    """Run a Terraform command and return the output."""
    cmd = ["terraform"] + command
    
    if capture_json and "-json" not in command:
        cmd.append("-json")
    
    result = subprocess.run(
        cmd,
        cwd=working_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running: {' '.join(cmd)}")
        print(result.stderr)
        return None
    
    if capture_json:
        # Terraform JSON output may have multiple JSON objects (one per line)
        lines = result.stdout.strip().split("\n")
        parsed = []
        for line in lines:
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return parsed
    
    return result.stdout
```

**How this works:**

1. `subprocess.run()` executes the Terraform command as a child process
2. `capture_output=True` captures stdout and stderr
3. `text=True` returns strings instead of bytes
4. `cwd=working_dir` runs the command in the specified directory
5. If `capture_json=True`, we parse each line as JSON (Terraform outputs one JSON object per line)

### Basic Operations

```python
# Initialize Terraform
output = run_terraform(["init"], working_dir="./infra")
print(output)

# Validate configuration
output = run_terraform(["validate"], working_dir="./infra")
print(output)

# Format check
output = run_terraform(["fmt", "-check", "-recursive"], working_dir="./infra")
if output is not None:
    print("All files properly formatted")
```

---

## Running Terraform Plan

### Basic Plan

```python
def terraform_plan(working_dir=".", var_file=None, out_file=None):
    """Run terraform plan and return the output."""
    cmd = ["plan", "-no-color"]
    
    if var_file:
        cmd.extend(["-var-file", var_file])
    
    if out_file:
        cmd.extend(["-out", out_file])
    
    return run_terraform(cmd, working_dir=working_dir)

# Usage:
plan_output = terraform_plan("./infra", var_file="prod.tfvars", out_file="plan.out")
if plan_output:
    print(plan_output)
```

### Parsing Plan Output for Changes

```python
def parse_plan_summary(plan_output):
    """Extract the summary line from terraform plan output."""
    if not plan_output:
        return {"add": 0, "change": 0, "destroy": 0}
    
    for line in plan_output.split("\n"):
        if "Plan:" in line:
            # Example: "Plan: 3 to add, 1 to change, 0 to destroy."
            parts = line.split()
            summary = {
                "add": 0,
                "change": 0,
                "destroy": 0
            }
            for i, word in enumerate(parts):
                if word == "add," or word == "add.":
                    summary["add"] = int(parts[i - 1])
                elif word == "change," or word == "change.":
                    summary["change"] = int(parts[i - 1])
                elif word == "destroy." or word == "destroy,":
                    summary["destroy"] = int(parts[i - 1])
            return summary
    
    return {"add": 0, "change": 0, "destroy": 0}

# Usage:
plan_output = terraform_plan("./infra")
summary = parse_plan_summary(plan_output)
print(f"Resources to add: {summary['add']}")
print(f"Resources to change: {summary['change']}")
print(f"Resources to destroy: {summary['destroy']}")

# Safety check
if summary["destroy"] > 0:
    print("\nWARNING: Resources will be destroyed!")
    print("Review the plan carefully before applying.")
```

**Output (example):**

```
Resources to add: 3
Resources to change: 1
Resources to destroy: 0
```

---

## Running Terraform Apply

```python
def terraform_apply(working_dir=".", plan_file=None, auto_approve=False):
    """Run terraform apply."""
    cmd = ["apply", "-no-color"]
    
    if auto_approve:
        cmd.append("-auto-approve")
    
    if plan_file:
        cmd.append(plan_file)
    
    return run_terraform(cmd, working_dir=working_dir)

# Safe workflow: plan first, review, then apply
plan_output = terraform_plan("./infra", out_file="plan.out")
summary = parse_plan_summary(plan_output)

if summary["destroy"] > 0:
    print("Destructive changes detected. Aborting.")
elif summary["add"] + summary["change"] == 0:
    print("No changes needed.")
else:
    print(f"Applying: {summary['add']} add, {summary['change']} change")
    terraform_apply("./infra", plan_file="plan.out")
```

---

## Reading Terraform State

Terraform state contains the current state of your infrastructure. You can read it with `terraform show -json`:

```python
def get_terraform_state(working_dir="."):
    """Read the current Terraform state."""
    result = subprocess.run(
        ["terraform", "show", "-json"],
        cwd=working_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    return json.loads(result.stdout)

def list_resources(working_dir="."):
    """List all resources in the Terraform state."""
    state = get_terraform_state(working_dir)
    if not state or "values" not in state:
        print("No resources found in state.")
        return []
    
    resources = []
    root = state["values"].get("root_module", {})
    
    for resource in root.get("resources", []):
        resources.append({
            "type": resource["type"],
            "name": resource["name"],
            "provider": resource["provider_name"],
            "values": resource.get("values", {})
        })
    
    return resources

# Usage:
resources = list_resources("./infra")
print(f"Total resources: {len(resources)}")
for r in resources:
    print(f"  {r['type']}.{r['name']} ({r['provider']})")
```

**Output (example):**

```
Total resources: 5
  aws_instance.web (aws)
  aws_instance.api (aws)
  aws_security_group.web_sg (aws)
  aws_s3_bucket.logs (aws)
  aws_db_instance.main (aws)
```

---

## Infrastructure Audit Tool

A practical tool that audits your Terraform state for security and cost issues:

```python
import subprocess
import json

def audit_infrastructure(working_dir="."):
    """Audit Terraform state for common issues."""
    state = get_terraform_state(working_dir)
    if not state or "values" not in state:
        print("No state to audit.")
        return
    
    resources = state["values"].get("root_module", {}).get("resources", [])
    findings = []
    
    for resource in resources:
        rtype = resource["type"]
        rname = resource["name"]
        values = resource.get("values", {})
        
        # Check: EC2 instances without tags
        if rtype == "aws_instance":
            tags = values.get("tags", {})
            if not tags or "Name" not in tags:
                findings.append({
                    "severity": "WARNING",
                    "resource": f"{rtype}.{rname}",
                    "issue": "Missing 'Name' tag"
                })
            
            # Check instance type (cost optimization)
            instance_type = values.get("instance_type", "")
            expensive_types = ["m5.xlarge", "m5.2xlarge", "c5.2xlarge", "r5.xlarge"]
            if instance_type in expensive_types:
                findings.append({
                    "severity": "INFO",
                    "resource": f"{rtype}.{rname}",
                    "issue": f"Using expensive instance type: {instance_type}"
                })
        
        # Check: S3 buckets without encryption
        if rtype == "aws_s3_bucket":
            encryption = values.get("server_side_encryption_configuration")
            if not encryption:
                findings.append({
                    "severity": "ERROR",
                    "resource": f"{rtype}.{rname}",
                    "issue": "S3 bucket without server-side encryption"
                })
        
        # Check: Security groups with 0.0.0.0/0
        if rtype == "aws_security_group":
            for rule in values.get("ingress", []):
                cidrs = rule.get("cidr_blocks", [])
                if "0.0.0.0/0" in cidrs:
                    port = rule.get("from_port", "?")
                    findings.append({
                        "severity": "ERROR",
                        "resource": f"{rtype}.{rname}",
                        "issue": f"Port {port} open to the internet (0.0.0.0/0)"
                    })
    
    # Print report
    print(f"\nInfrastructure Audit Report")
    print("=" * 50)
    print(f"Total resources: {len(resources)}")
    print(f"Findings: {len(findings)}")
    
    for finding in findings:
        severity = finding["severity"]
        icon = {"ERROR": "[!!]", "WARNING": "[!]", "INFO": "[i]"}[severity]
        print(f"\n  {icon} {severity}: {finding['resource']}")
        print(f"      {finding['issue']}")
    
    if not findings:
        print("\nNo issues found!")

# Usage:
# audit_infrastructure("./infra")
```

**Output (example):**

```
Infrastructure Audit Report
==================================================
Total resources: 5
Findings: 3

  [!!] ERROR: aws_s3_bucket.logs
      S3 bucket without server-side encryption

  [!!] ERROR: aws_security_group.web_sg
      Port 22 open to the internet (0.0.0.0/0)

  [!] WARNING: aws_instance.api
      Missing 'Name' tag
```

---

## Terraform Workspace Manager

Manage multiple environments (dev, staging, prod) with workspaces:

```python
def list_workspaces(working_dir="."):
    """List all Terraform workspaces."""
    result = subprocess.run(
        ["terraform", "workspace", "list"],
        cwd=working_dir,
        capture_output=True,
        text=True
    )
    
    workspaces = []
    current = None
    
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("*"):
            name = line.replace("*", "").strip()
            current = name
            workspaces.append(name)
        elif line:
            workspaces.append(line)
    
    return workspaces, current

def switch_workspace(name, working_dir="."):
    """Switch to a Terraform workspace, creating it if needed."""
    workspaces, current = list_workspaces(working_dir)
    
    if name == current:
        print(f"Already on workspace: {name}")
        return True
    
    if name in workspaces:
        cmd = ["workspace", "select", name]
    else:
        cmd = ["workspace", "new", name]
    
    result = run_terraform(cmd, working_dir=working_dir)
    return result is not None

# Usage:
workspaces, current = list_workspaces("./infra")
print(f"Workspaces: {workspaces}")
print(f"Current: {current}")

# switch_workspace("staging", "./infra")
```

---

## Generating Terraform Files with Python

Sometimes you need to generate Terraform configuration dynamically:

```python
import json

def generate_ec2_instances(instances, output_file="generated.tf.json"):
    """Generate Terraform config for multiple EC2 instances."""
    terraform_config = {
        "resource": {
            "aws_instance": {}
        }
    }
    
    for instance in instances:
        name = instance["name"]
        terraform_config["resource"]["aws_instance"][name] = {
            "ami": instance.get("ami", "ami-0c55b159cbfafe1f0"),
            "instance_type": instance.get("type", "t2.micro"),
            "tags": {
                "Name": name,
                "Environment": instance.get("env", "dev"),
                "ManagedBy": "python-automation"
            }
        }
    
    with open(output_file, "w") as f:
        json.dump(terraform_config, f, indent=2)
    
    print(f"Generated {output_file} with {len(instances)} instance(s)")

# Usage:
instances = [
    {"name": "web-01", "type": "t3.small", "env": "prod"},
    {"name": "web-02", "type": "t3.small", "env": "prod"},
    {"name": "api-01", "type": "t3.medium", "env": "prod"},
]

generate_ec2_instances(instances)
```

**Output:**

```
Generated generated.tf.json with 3 instance(s)
```

**Why `.tf.json`:** Terraform accepts configuration in both HCL (`.tf`) and JSON (`.tf.json`) format. JSON is easier to generate programmatically.

---

## Exercises

**Exercise 1:** Write a script that runs `terraform plan` and sends a Slack notification with the summary (X to add, Y to change, Z to destroy).

**Exercise 2:** Write a state auditor that checks for resources without tags and generates a report.

**Exercise 3:** Write a script that compares two Terraform state files and reports what changed between them.

**Exercise 4:** Build a CLI tool that wraps common Terraform workflows: `init + plan`, `plan + apply`, and `destroy` with confirmation prompts.

---

## Common Mistakes

### 1. Running Apply Without Plan Review

Always run `plan` first and review the output. Automate the plan step, but require human approval for `apply` in production.

### 2. Not Handling Terraform Errors

```python
# Bad — ignores errors
subprocess.run(["terraform", "apply", "-auto-approve"])

# Good — check return code
result = subprocess.run(["terraform", "apply", "-auto-approve"],
                        capture_output=True, text=True)
if result.returncode != 0:
    print(f"Apply failed: {result.stderr}")
```

### 3. Hardcoding Paths and Variables

Use environment variables or config files for paths, AWS regions, and other environment-specific values.

### 4. Not Using Workspaces or Separate State

Never use the same state file for dev and prod. Use workspaces or separate backend configurations.

---

## Summary

| Task | Approach |
|------|----------|
| Run Terraform commands | `subprocess.run(["terraform", ...])` |
| Parse plan output | Read stdout, look for "Plan:" line |
| Read state | `terraform show -json` → `json.loads()` |
| Audit resources | Parse state JSON, check for issues |
| Generate config | Write `.tf.json` files with `json.dump()` |
| Manage workspaces | `terraform workspace list/select/new` |

---

[Previous: Module 09 — Git Automation](09-git-automation-with-python.md) | [Next: Module 11 — Ansible Automation](11-ansible-automation.md)
