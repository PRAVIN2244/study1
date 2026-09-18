# Module 11 — Ansible Automation with Python

Ansible automates server configuration, application deployment, and orchestration. While Ansible playbooks are written in YAML, Python can drive Ansible programmatically — running playbooks, generating dynamic inventories, creating playbooks from templates, and integrating Ansible into larger automation workflows.

---

## Prerequisites

```bash
pip install ansible pyyaml
ansible --version
```

---

## Running Ansible Playbooks from Python

### Basic Playbook Runner

```python
import subprocess
import json

def run_playbook(playbook, inventory="inventory.ini", extra_vars=None,
                 check_mode=False, verbose=False):
    """Run an Ansible playbook and return the result."""
    cmd = [
        "ansible-playbook",
        playbook,
        "-i", inventory,
    ]
    
    if check_mode:
        cmd.append("--check")    # Dry run — no changes made
    
    if verbose:
        cmd.append("-v")
    
    if extra_vars:
        # Pass variables as JSON
        cmd.extend(["--extra-vars", json.dumps(extra_vars)])
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.returncode
    }

# Usage:
result = run_playbook(
    "deploy.yml",
    inventory="production",
    extra_vars={"app_version": "2.3.1", "environment": "prod"},
    check_mode=True    # Dry run first
)

if result["success"]:
    print("Playbook completed successfully!")
    print(result["stdout"])
else:
    print(f"Playbook failed (exit code {result['return_code']})")
    print(result["stderr"])
```

**How this works:**

1. Build the `ansible-playbook` command with all options
2. `--check` runs in dry-run mode (shows what would change without changing anything)
3. `--extra-vars` passes Python variables to the playbook as JSON
4. `subprocess.run()` executes the command and captures output
5. Return code 0 means success, anything else means failure

### Parsing Playbook Output

```python
def parse_playbook_recap(output):
    """Parse the PLAY RECAP section from Ansible output."""
    results = {}
    in_recap = False
    
    for line in output.split("\n"):
        if "PLAY RECAP" in line:
            in_recap = True
            continue
        
        if in_recap and "=" in line:
            # Example: web-01 : ok=5 changed=2 unreachable=0 failed=0
            parts = line.strip().split(":")
            if len(parts) >= 2:
                host = parts[0].strip()
                stats = {}
                for item in parts[1].strip().split():
                    if "=" in item:
                        key, value = item.split("=")
                        stats[key] = int(value)
                results[host] = stats
    
    return results

# Usage:
result = run_playbook("deploy.yml")
recap = parse_playbook_recap(result["stdout"])

for host, stats in recap.items():
    status = "FAILED" if stats.get("failed", 0) > 0 else "OK"
    print(f"  {host}: {status} (ok={stats.get('ok', 0)}, "
          f"changed={stats.get('changed', 0)}, "
          f"failed={stats.get('failed', 0)})")
```

**Output (example):**

```
  web-01: OK (ok=5, changed=2, failed=0)
  web-02: OK (ok=5, changed=0, failed=0)
  api-01: FAILED (ok=3, changed=1, failed=1)
```

---

## Dynamic Inventory

Ansible normally reads hosts from a static inventory file. A dynamic inventory script generates the host list at runtime — from a cloud API, a database, or any other source.

### How Dynamic Inventory Works

Ansible calls your script with `--list` and expects JSON output:

```python
#!/usr/bin/env python3
"""Dynamic inventory script for Ansible."""

import json
import sys

def get_inventory():
    """Generate inventory from your data source."""
    # In real use, this would query AWS, a database, etc.
    servers = [
        {"name": "web-01", "ip": "10.0.1.10", "group": "webservers", "env": "prod"},
        {"name": "web-02", "ip": "10.0.1.11", "group": "webservers", "env": "prod"},
        {"name": "api-01", "ip": "10.0.2.10", "group": "apiservers", "env": "prod"},
        {"name": "db-01", "ip": "10.0.3.10", "group": "databases", "env": "prod"},
    ]
    
    inventory = {
        "_meta": {
            "hostvars": {}
        }
    }
    
    for server in servers:
        group = server["group"]
        
        # Create group if it does not exist
        if group not in inventory:
            inventory[group] = {"hosts": [], "vars": {}}
        
        # Add host to group
        inventory[group]["hosts"].append(server["ip"])
        
        # Add host-specific variables
        inventory["_meta"]["hostvars"][server["ip"]] = {
            "hostname": server["name"],
            "environment": server["env"]
        }
    
    return inventory

if __name__ == "__main__":
    if "--list" in sys.argv:
        print(json.dumps(get_inventory(), indent=2))
    elif "--host" in sys.argv:
        # Return variables for a specific host
        print(json.dumps({}))
    else:
        print("Usage: --list or --host <hostname>")
        sys.exit(1)
```

**Output when called with `--list`:**

```json
{
  "_meta": {
    "hostvars": {
      "10.0.1.10": {"hostname": "web-01", "environment": "prod"},
      "10.0.1.11": {"hostname": "web-02", "environment": "prod"},
      "10.0.2.10": {"hostname": "api-01", "environment": "prod"},
      "10.0.3.10": {"hostname": "db-01", "environment": "prod"}
    }
  },
  "webservers": {
    "hosts": ["10.0.1.10", "10.0.1.11"],
    "vars": {}
  },
  "apiservers": {
    "hosts": ["10.0.2.10"],
    "vars": {}
  },
  "databases": {
    "hosts": ["10.0.3.10"],
    "vars": {}
  }
}
```

**To use it with Ansible:**

```bash
chmod +x inventory.py
ansible-playbook -i inventory.py deploy.yml
```

### AWS Dynamic Inventory

```python
#!/usr/bin/env python3
"""Dynamic inventory from AWS EC2 instances."""

import json
import sys

try:
    import boto3
except ImportError:
    print("Error: boto3 is required. Install with: pip install boto3")
    sys.exit(1)

def get_ec2_inventory(region="us-east-1"):
    """Query AWS for running EC2 instances."""
    ec2 = boto3.client("ec2", region_name=region)
    
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )
    
    inventory = {"_meta": {"hostvars": {}}}
    
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            ip = instance.get("PrivateIpAddress", "")
            if not ip:
                continue
            
            # Get the Name tag
            tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
            name = tags.get("Name", instance["InstanceId"])
            
            # Group by the "Role" tag (e.g., web, api, db)
            role = tags.get("Role", "ungrouped")
            
            if role not in inventory:
                inventory[role] = {"hosts": []}
            
            inventory[role]["hosts"].append(ip)
            inventory["_meta"]["hostvars"][ip] = {
                "hostname": name,
                "instance_id": instance["InstanceId"],
                "instance_type": instance["InstanceType"],
                "availability_zone": instance["Placement"]["AvailabilityZone"]
            }
    
    return inventory

if __name__ == "__main__":
    if "--list" in sys.argv:
        print(json.dumps(get_ec2_inventory(), indent=2))
    else:
        print(json.dumps({}))
```

---

## Generating Ansible Playbooks

Create playbooks programmatically from Python:

```python
import yaml

def generate_deploy_playbook(app_name, version, servers_group,
                              output_file="deploy_generated.yml"):
    """Generate a deployment playbook."""
    playbook = [
        {
            "name": f"Deploy {app_name} v{version}",
            "hosts": servers_group,
            "become": True,
            "vars": {
                "app_name": app_name,
                "app_version": version,
            },
            "tasks": [
                {
                    "name": "Update apt cache",
                    "apt": {"update_cache": True, "cache_valid_time": 3600}
                },
                {
                    "name": f"Stop {app_name} service",
                    "service": {"name": app_name, "state": "stopped"},
                    "ignore_errors": True
                },
                {
                    "name": f"Download {app_name} v{version}",
                    "get_url": {
                        "url": f"https://releases.example.com/{app_name}/{version}/{app_name}.tar.gz",
                        "dest": f"/opt/{app_name}/{app_name}.tar.gz"
                    }
                },
                {
                    "name": f"Extract {app_name}",
                    "unarchive": {
                        "src": f"/opt/{app_name}/{app_name}.tar.gz",
                        "dest": f"/opt/{app_name}/",
                        "remote_src": True
                    }
                },
                {
                    "name": f"Start {app_name} service",
                    "service": {"name": app_name, "state": "started", "enabled": True}
                },
                {
                    "name": "Wait for service to be ready",
                    "wait_for": {"port": 8080, "timeout": 30}
                }
            ]
        }
    ]
    
    with open(output_file, "w") as f:
        yaml.dump(playbook, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated playbook: {output_file}")
    return output_file

# Usage:
generate_deploy_playbook("myapp", "2.3.1", "webservers")
```

---

## Ansible Vault Integration

Manage encrypted secrets:

```python
import subprocess
import tempfile
import os

def encrypt_string(value, name, vault_password_file):
    """Encrypt a string using Ansible Vault."""
    result = subprocess.run(
        [
            "ansible-vault", "encrypt_string",
            value,
            "--name", name,
            "--vault-password-file", vault_password_file
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return result.stdout
    else:
        print(f"Encryption failed: {result.stderr}")
        return None

def decrypt_file(encrypted_file, vault_password_file):
    """Decrypt an Ansible Vault file and return contents."""
    result = subprocess.run(
        [
            "ansible-vault", "view",
            encrypted_file,
            "--vault-password-file", vault_password_file
        ],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return result.stdout
    else:
        print(f"Decryption failed: {result.stderr}")
        return None
```

---

## Practical Example: Multi-Environment Deployer

```python
import subprocess
import json
import sys
from datetime import datetime

class AnsibleDeployer:
    """Deploy applications across multiple environments."""
    
    ENVIRONMENTS = {
        "dev": {
            "inventory": "inventories/dev",
            "vars_file": "vars/dev.yml",
            "auto_approve": True
        },
        "staging": {
            "inventory": "inventories/staging",
            "vars_file": "vars/staging.yml",
            "auto_approve": True
        },
        "prod": {
            "inventory": "inventories/prod",
            "vars_file": "vars/prod.yml",
            "auto_approve": False    # Requires confirmation
        }
    }
    
    def deploy(self, app, version, environment, dry_run=False):
        """Deploy an application to an environment."""
        if environment not in self.ENVIRONMENTS:
            print(f"Unknown environment: {environment}")
            print(f"Valid: {list(self.ENVIRONMENTS.keys())}")
            return False
        
        env_config = self.ENVIRONMENTS[environment]
        
        print(f"\n{'='*50}")
        print(f"Deploying {app} v{version} to {environment}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        # Build command
        cmd = [
            "ansible-playbook",
            "deploy.yml",
            "-i", env_config["inventory"],
            "-e", json.dumps({
                "app_name": app,
                "app_version": version,
                "environment": environment
            }),
            "-e", f"@{env_config['vars_file']}"
        ]
        
        if dry_run:
            cmd.append("--check")
            print("[DRY RUN MODE]")
        
        # Production safety check
        if environment == "prod" and not dry_run:
            confirm = input("\nType 'yes' to deploy to PRODUCTION: ")
            if confirm != "yes":
                print("Deployment cancelled.")
                return False
        
        result = subprocess.run(cmd, text=True)
        
        success = result.returncode == 0
        status = "SUCCESS" if success else "FAILED"
        print(f"\nDeployment {status}")
        
        return success

# Usage:
# deployer = AnsibleDeployer()
# deployer.deploy("myapp", "2.3.1", "staging", dry_run=True)
# deployer.deploy("myapp", "2.3.1", "prod")
```

---

## Exercises

**Exercise 1:** Write a dynamic inventory script that reads server information from a CSV file and outputs Ansible-compatible JSON.

**Exercise 2:** Write a script that runs a playbook against multiple environments (dev, staging, prod) in sequence, stopping if any environment fails.

**Exercise 3:** Build a playbook generator that creates a playbook for setting up a web server (install nginx, copy config, start service) based on user input.

**Exercise 4:** Write a script that parses Ansible playbook output and sends a summary to Slack (host count, changed count, failed count).

---

## Common Mistakes

### 1. Not Using Check Mode First

Always run with `--check` (dry run) before applying changes, especially in production.

### 2. Hardcoding Inventory

```python
# Bad
run_playbook("deploy.yml", inventory="/home/alice/hosts")

# Good — use environment-specific inventory
run_playbook("deploy.yml", inventory=f"inventories/{environment}")
```

### 3. Not Handling Playbook Failures

Check the return code. Ansible returns non-zero on failure, and your automation should handle that.

### 4. Storing Secrets in Plain Text

Use Ansible Vault for passwords, API keys, and other secrets. Never commit unencrypted secrets to version control.

---

## Summary

| Task | Approach |
|------|----------|
| Run playbooks | `subprocess.run(["ansible-playbook", ...])` |
| Dynamic inventory | Python script with `--list` JSON output |
| Generate playbooks | Build Python dicts, write with `yaml.dump()` |
| Parse output | Read PLAY RECAP section from stdout |
| Manage secrets | `ansible-vault encrypt_string/view` |
| Multi-environment | Config dict mapping env → inventory + vars |

---

[Previous: Module 10 — Terraform Automation](10-terraform-automation-with-python.md) | [Next: Module 12 — Docker Automation](12-docker-automation.md)
