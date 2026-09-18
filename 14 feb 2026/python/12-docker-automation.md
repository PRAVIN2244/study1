# Module 12 — Docker Automation with Python

Docker is the standard for packaging and running applications in containers. Python can automate Docker operations — building images, managing containers, cleaning up resources, monitoring health, and orchestrating multi-container deployments.

---

## Prerequisites

```bash
pip install docker
```

```python
import docker

client = docker.from_env()
print(f"Docker version: {client.version()['Version']}")
```

**Output:**

```
Docker version: 24.0.7
```

**What `docker.from_env()` does:** It creates a Docker client that connects to the Docker daemon using the same settings as the `docker` CLI (reads `DOCKER_HOST` environment variable or uses the default socket).

---

## Managing Containers

### Listing Running Containers

```python
import docker

client = docker.from_env()

containers = client.containers.list()

if not containers:
    print("No running containers.")
else:
    print(f"{'NAME':<25} {'IMAGE':<30} {'STATUS':<20}")
    print("-" * 75)
    for c in containers:
        print(f"{c.name:<25} {c.image.tags[0] if c.image.tags else 'untagged':<30} {c.status:<20}")
```

**Output (example):**

```
NAME                      IMAGE                          STATUS
web-app                   nginx:latest                   running
redis-cache               redis:7-alpine                 running
postgres-db               postgres:15                    running
```

### Running a Container

```python
import docker

client = docker.from_env()

container = client.containers.run(
    "nginx:latest",
    name="my-nginx",
    ports={"80/tcp": 8080},        # Map container port 80 to host port 8080
    detach=True,                    # Run in background
    environment={"NGINX_HOST": "localhost"},
    labels={"managed-by": "python-automation"}
)

print(f"Started: {container.name}")
print(f"ID: {container.short_id}")
print(f"Status: {container.status}")
```

**Output:**

```
Started: my-nginx
ID: a1b2c3d4e5
Status: created
```

**Key parameters:**

- `detach=True` — run in background (like `docker run -d`)
- `ports={"80/tcp": 8080}` — port mapping (like `-p 8080:80`)
- `environment={}` — environment variables (like `-e`)
- `labels={}` — metadata labels for organizing containers

### Stopping and Removing Containers

```python
import docker

client = docker.from_env()

try:
    container = client.containers.get("my-nginx")
    
    print(f"Stopping {container.name}...")
    container.stop(timeout=10)    # Wait up to 10 seconds for graceful shutdown
    
    print(f"Removing {container.name}...")
    container.remove()
    
    print("Done!")
except docker.errors.NotFound:
    print("Container not found.")
except docker.errors.APIError as e:
    print(f"Docker API error: {e}")
```

### Getting Container Logs

```python
import docker

client = docker.from_env()

container = client.containers.get("my-nginx")

# Get last 20 lines of logs
logs = container.logs(tail=20).decode("utf-8")
print(logs)

# Stream logs in real-time
for line in container.logs(stream=True, follow=True):
    print(line.decode("utf-8").strip())
```

### Executing Commands Inside a Container

```python
import docker

client = docker.from_env()

container = client.containers.get("my-nginx")

# Run a command inside the container
exit_code, output = container.exec_run("nginx -v")
print(f"Exit code: {exit_code}")
print(f"Output: {output.decode('utf-8').strip()}")

# Check disk usage inside container
exit_code, output = container.exec_run("df -h /")
print(output.decode("utf-8"))
```

**Output:**

```
Exit code: 0
Output: nginx version: nginx/1.25.3
```

---

## Building Docker Images

### Building from a Dockerfile

```python
import docker

client = docker.from_env()

# Build an image from a Dockerfile in the current directory
image, build_logs = client.images.build(
    path=".",                          # Directory containing Dockerfile
    tag="myapp:1.0.0",                 # Image name and tag
    rm=True,                           # Remove intermediate containers
    buildargs={"APP_VERSION": "1.0.0"} # Build arguments
)

# Print build output
for log in build_logs:
    if "stream" in log:
        print(log["stream"].strip())

print(f"\nBuilt image: {image.tags}")
print(f"Size: {image.attrs['Size'] / 1024 / 1024:.1f} MB")
```

**Output (example):**

```
Step 1/5 : FROM python:3.11-slim
Step 2/5 : WORKDIR /app
Step 3/5 : COPY requirements.txt .
Step 4/5 : RUN pip install -r requirements.txt
Step 5/5 : COPY . .

Built image: ['myapp:1.0.0']
Size: 145.3 MB
```

### Listing Images

```python
import docker

client = docker.from_env()

images = client.images.list()

print(f"{'REPOSITORY:TAG':<40} {'SIZE (MB)':<12} {'CREATED'}")
print("-" * 70)

for image in images:
    tag = image.tags[0] if image.tags else "<none>"
    size_mb = image.attrs["Size"] / 1024 / 1024
    created = image.attrs["Created"][:10]
    print(f"{tag:<40} {size_mb:<12.1f} {created}")
```

---

## Docker Cleanup

Unused images, containers, and volumes consume disk space. Automate cleanup:

```python
import docker

def docker_cleanup(client, dry_run=True):
    """Clean up unused Docker resources."""
    results = {
        "containers": [],
        "images": [],
        "volumes": [],
        "space_freed": 0
    }
    
    # 1. Remove stopped containers
    stopped = client.containers.list(filters={"status": "exited"})
    for container in stopped:
        if dry_run:
            print(f"  [DRY RUN] Would remove container: {container.name}")
        else:
            container.remove()
            print(f"  Removed container: {container.name}")
        results["containers"].append(container.name)
    
    # 2. Remove dangling images (untagged)
    dangling = client.images.list(filters={"dangling": True})
    for image in dangling:
        size_mb = image.attrs["Size"] / 1024 / 1024
        if dry_run:
            print(f"  [DRY RUN] Would remove image: {image.short_id} ({size_mb:.1f} MB)")
        else:
            client.images.remove(image.id, force=True)
            print(f"  Removed image: {image.short_id} ({size_mb:.1f} MB)")
        results["images"].append(image.short_id)
        results["space_freed"] += size_mb
    
    # 3. Remove unused volumes
    unused_volumes = client.volumes.list(filters={"dangling": True})
    for volume in unused_volumes:
        if dry_run:
            print(f"  [DRY RUN] Would remove volume: {volume.name}")
        else:
            volume.remove()
            print(f"  Removed volume: {volume.name}")
        results["volumes"].append(volume.name)
    
    # Summary
    print(f"\nCleanup Summary:")
    print(f"  Containers: {len(results['containers'])}")
    print(f"  Images: {len(results['images'])}")
    print(f"  Volumes: {len(results['volumes'])}")
    print(f"  Space freed: {results['space_freed']:.1f} MB")
    
    return results

# Usage:
client = docker.from_env()
docker_cleanup(client, dry_run=True)     # Preview first
# docker_cleanup(client, dry_run=False)  # Actually clean up
```

---

## Container Health Monitoring

```python
import docker
import time

def monitor_containers(client, interval=10):
    """Monitor running containers and report health status."""
    print(f"Monitoring containers (every {interval}s)... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            containers = client.containers.list()
            
            if not containers:
                print("No running containers.")
            else:
                print(f"{'NAME':<20} {'CPU %':<10} {'MEM':<15} {'STATUS'}")
                print("-" * 60)
                
                for c in containers:
                    try:
                        stats = c.stats(stream=False)
                        
                        # Calculate CPU percentage
                        cpu_delta = (stats["cpu_stats"]["cpu_usage"]["total_usage"] -
                                    stats["precpu_stats"]["cpu_usage"]["total_usage"])
                        system_delta = (stats["cpu_stats"]["system_cpu_usage"] -
                                       stats["precpu_stats"]["system_cpu_usage"])
                        cpu_percent = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0
                        
                        # Calculate memory usage
                        mem_usage = stats["memory_stats"].get("usage", 0) / 1024 / 1024
                        mem_limit = stats["memory_stats"].get("limit", 1) / 1024 / 1024
                        
                        print(f"{c.name:<20} {cpu_percent:<10.1f} "
                              f"{mem_usage:.0f}/{mem_limit:.0f} MB  {c.status}")
                    except Exception:
                        print(f"{c.name:<20} {'N/A':<10} {'N/A':<15} {c.status}")
            
            print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

# Usage:
# client = docker.from_env()
# monitor_containers(client, interval=5)
```

---

## Docker Compose Operations

For multi-container applications, use Docker Compose via subprocess:

```python
import subprocess
import yaml

def compose_up(compose_file="docker-compose.yml", detach=True, build=False):
    """Start services defined in a Docker Compose file."""
    cmd = ["docker", "compose", "-f", compose_file, "up"]
    
    if detach:
        cmd.append("-d")
    if build:
        cmd.append("--build")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Services started successfully!")
        print(result.stdout)
    else:
        print(f"Failed to start services:")
        print(result.stderr)
    
    return result.returncode == 0

def compose_down(compose_file="docker-compose.yml", volumes=False):
    """Stop and remove services."""
    cmd = ["docker", "compose", "-f", compose_file, "down"]
    
    if volumes:
        cmd.append("-v")    # Also remove volumes
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def compose_status(compose_file="docker-compose.yml"):
    """Show status of Compose services."""
    result = subprocess.run(
        ["docker", "compose", "-f", compose_file, "ps", "--format", "json"],
        capture_output=True, text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        import json
        for line in result.stdout.strip().split("\n"):
            service = json.loads(line)
            print(f"  {service['Name']}: {service['State']} (port: {service.get('Publishers', 'N/A')})")
```

### Generating Docker Compose Files

```python
import yaml

def generate_compose(services, output_file="docker-compose.generated.yml"):
    """Generate a Docker Compose file from a service definition."""
    compose = {
        "version": "3.8",
        "services": {}
    }
    
    for svc in services:
        service_def = {
            "image": svc["image"],
            "restart": svc.get("restart", "unless-stopped"),
        }
        
        if "ports" in svc:
            service_def["ports"] = svc["ports"]
        if "environment" in svc:
            service_def["environment"] = svc["environment"]
        if "volumes" in svc:
            service_def["volumes"] = svc["volumes"]
        if "depends_on" in svc:
            service_def["depends_on"] = svc["depends_on"]
        
        compose["services"][svc["name"]] = service_def
    
    with open(output_file, "w") as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated: {output_file}")

# Usage:
services = [
    {
        "name": "web",
        "image": "nginx:latest",
        "ports": ["8080:80"],
        "depends_on": ["api"]
    },
    {
        "name": "api",
        "image": "myapp:latest",
        "ports": ["3000:3000"],
        "environment": {"DATABASE_URL": "postgres://db:5432/myapp"},
        "depends_on": ["db"]
    },
    {
        "name": "db",
        "image": "postgres:15",
        "environment": {"POSTGRES_DB": "myapp", "POSTGRES_PASSWORD": "secret"},
        "volumes": ["pgdata:/var/lib/postgresql/data"]
    }
]

generate_compose(services)
```

---

## Practical Example: Build Pipeline

```python
import docker
import sys
from datetime import datetime

def build_and_deploy(image_name, version, dockerfile_path=".",
                     registry=None, dry_run=False):
    """Build a Docker image, tag it, and optionally push to a registry."""
    client = docker.from_env()
    full_tag = f"{image_name}:{version}"
    
    print(f"\n{'='*50}")
    print(f"Build Pipeline: {full_tag}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # Step 1: Build
    print(f"\n[1/4] Building {full_tag}...")
    try:
        image, logs = client.images.build(
            path=dockerfile_path,
            tag=full_tag,
            rm=True,
            buildargs={"VERSION": version}
        )
        size_mb = image.attrs["Size"] / 1024 / 1024
        print(f"  Built successfully ({size_mb:.1f} MB)")
    except docker.errors.BuildError as e:
        print(f"  Build failed: {e}")
        return False
    
    # Step 2: Tag for registry
    if registry:
        registry_tag = f"{registry}/{full_tag}"
        print(f"\n[2/4] Tagging as {registry_tag}...")
        image.tag(registry_tag)
        print("  Tagged.")
    else:
        print("\n[2/4] No registry specified, skipping tag.")
    
    # Step 3: Run tests
    print(f"\n[3/4] Running smoke test...")
    try:
        container = client.containers.run(
            full_tag,
            command="echo 'Container starts successfully'",
            remove=True
        )
        print(f"  Test passed: {container.decode('utf-8').strip()}")
    except docker.errors.ContainerError as e:
        print(f"  Test failed: {e}")
        return False
    
    # Step 4: Push
    if registry and not dry_run:
        print(f"\n[4/4] Pushing to {registry}...")
        try:
            for line in client.images.push(registry_tag, stream=True, decode=True):
                if "status" in line:
                    print(f"  {line['status']}")
            print("  Push complete.")
        except docker.errors.APIError as e:
            print(f"  Push failed: {e}")
            return False
    else:
        print(f"\n[4/4] {'[DRY RUN] ' if dry_run else ''}Skipping push.")
    
    print(f"\nPipeline complete!")
    return True

# Usage:
# build_and_deploy("myapp", "1.2.3", registry="ghcr.io/myorg", dry_run=True)
```

---

## Exercises

**Exercise 1:** Write a script that lists all running containers and their resource usage (CPU, memory) in a formatted table.

**Exercise 2:** Write a cleanup script that removes all stopped containers, dangling images, and unused volumes. Include a `--dry-run` flag.

**Exercise 3:** Write a script that monitors a specific container and restarts it if it stops unexpectedly.

**Exercise 4:** Build a CLI tool that wraps Docker Compose operations: `up`, `down`, `status`, `logs` for a specific project.

---

## Common Mistakes

### 1. Not Handling Docker Daemon Connection Errors

```python
# Bad — crashes if Docker is not running
client = docker.from_env()

# Good
try:
    client = docker.from_env()
    client.ping()
except docker.errors.DockerException as e:
    print(f"Cannot connect to Docker: {e}")
    print("Is Docker running?")
    sys.exit(1)
```

### 2. Not Cleaning Up Containers

Always remove containers after use, especially in CI/CD. Use `remove=True` for one-off containers.

### 3. Not Setting Resource Limits

```python
# Good — set memory and CPU limits
container = client.containers.run(
    "myapp:latest",
    mem_limit="512m",
    cpu_period=100000,
    cpu_quota=50000,    # 50% of one CPU
    detach=True
)
```

### 4. Ignoring Build Cache

Use `.dockerignore` to exclude unnecessary files from the build context. Large build contexts slow down builds.

---

## Summary

| Task | Docker SDK | CLI Alternative |
|------|-----------|----------------|
| List containers | `client.containers.list()` | `docker ps` |
| Run container | `client.containers.run()` | `docker run` |
| Stop container | `container.stop()` | `docker stop` |
| Build image | `client.images.build()` | `docker build` |
| Push image | `client.images.push()` | `docker push` |
| Get logs | `container.logs()` | `docker logs` |
| Exec command | `container.exec_run()` | `docker exec` |
| Cleanup | `client.images.prune()` | `docker system prune` |

---

[Previous: Module 11 — Ansible Automation](11-ansible-automation.md) | [Next: Module 13 — Kubernetes Automation](13-kubernetes-automation.md)
