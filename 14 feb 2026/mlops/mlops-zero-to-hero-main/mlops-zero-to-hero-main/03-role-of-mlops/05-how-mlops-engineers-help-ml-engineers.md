# How MLOps Engineers Help ML Engineers

In the previous lecture, we saw how ML engineers create an API for the model. But the API was running on **localhost** — to make it publicly available, deployment steps are needed.

This deployment is carried out by MLOps engineers. They focus on the **infrastructure and automation side** so ML engineers can concentrate on model logic and APIs.

---

## What MLOps Engineers Do for ML Engineers

```
┌──────────────────────────────────────────────────────────────────┐
│           MLOps ENGINEER'S DEPLOYMENT ACTIVITIES                  │
│                                                                   │
│   1. Containerize the model (Dockerfile + Docker build)          │
│      → Model runs anywhere and everywhere                        │
│                                                                   │
│   2. Create infrastructure (VMs, Kubernetes clusters)            │
│      → Using Infrastructure as Code (Terraform)                  │
│                                                                   │
│   3. Generate Kubernetes manifests                               │
│      → Deployments, Services, Ingress                            │
│                                                                   │
│   4. Deploy to Kubernetes                                        │
│      → With networking, load balancing, API gateway, security    │
│                                                                   │
│   5. Set up monitoring and observability                         │
│      → Track model performance, latency, errors                  │
└──────────────────────────────────────────────────────────────────┘
```

In this lecture, we focus on **Step 1: Containerization**. The remaining steps are covered in future lectures once we understand the required MLOps tools.

---

## Step 1: Write the Dockerfile

The Dockerfile defines how to package the model API into a container.

### The complete Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
```

### Line-by-line explanation

| Line | What it does | Why |
|------|-------------|-----|
| `FROM python:3.12-slim` | Use Python 3.12 as the base image | Avoids installing Python manually. If you used Ubuntu or Alpine, you'd need to install Python on top. |
| `WORKDIR /app` | Set the working directory inside the container | All subsequent commands run from `/app` |
| `COPY requirements.txt .` | Copy the dependency file first | **Before** copying source code — this is intentional (see below) |
| `RUN python -m pip install --upgrade pip` | Upgrade pip | Ensures latest pip version for dependency resolution |
| `RUN python -m pip install -r requirements.txt` | Install project dependencies | scikit-learn, flask, joblib, pandas |
| `COPY . .` | Copy all source files (app.py, train.py, artifacts/, etc.) | Done **after** installing dependencies |
| `EXPOSE 5001` | Document that the container listens on port 5001 | Informational — doesn't actually publish the port |
| `CMD ["python", "app.py"]` | Run the Flask API when the container starts | This is the entry point |

### Why copy requirements.txt before source code?

```
┌──────────────────────────────────────────────────────────────────┐
│           DOCKER LAYER CACHING                                    │
│                                                                   │
│   Layer 1: FROM python:3.12-slim          ← cached               │
│   Layer 2: COPY requirements.txt .        ← cached (if unchanged)│
│   Layer 3: RUN pip install -r req.txt     ← cached (if unchanged)│
│   Layer 4: COPY . .                       ← rebuilt (code changed)│
│                                                                   │
│   If you copy source code FIRST, then change app.py:             │
│   → Docker invalidates ALL layers after the change               │
│   → Dependencies are reinstalled every time (slow!)              │
│                                                                   │
│   By copying requirements.txt first:                             │
│   → Dependencies are only reinstalled when requirements change   │
│   → Source code changes don't trigger dependency reinstall        │
│   → Docker image builds are significantly faster                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Step 2: Build the Docker Image

```bash
docker build -t hello-mlops:latest .
```

**Output:**
```
[+] Building 2.3s (9/11)
 => [internal] load build definition from Dockerfile
 => transferring dockerfile: 228B
 => [internal] load metadata for docker.io/library/python:3.12-slim
 => [1/6] FROM docker.io/library/python:3.12-slim
 => [2/6] WORKDIR /app
 => [3/6] COPY requirements.txt .
 => [4/6] RUN python -m pip install --upgrade pip
 => [5/6] RUN python -m pip install -r requirements.txt
 => [6/6] COPY . .
 => exporting to image
```

> **Common mistake:** If you write `RUN python -m pip --upgrade pip` (missing `install`), the build will fail with `no such option: --upgrade`. Always use `python -m pip install --upgrade pip`.

---

## Step 3: Run the Container

```bash
# Run in detached mode, bind port 5001
docker run -d -p 5001:5001 hello-mlops:latest
```

**Output:**
```
026be724d502a73926f83c44f59073c003e788d5fce94d1920ebd2459267a26f
```

### Verify the container is running

```bash
docker ps
```

**Output:**
```
CONTAINER ID   IMAGE                COMMAND            CREATED        STATUS       PORTS
026be724d502   hello-mlops:latest   "python app.py"    5 seconds ago  Up 4 seconds 0.0.0.0:5001->5001/tcp
```

The model API is now running inside a Docker container, accessible on port 5001.

---

## Step 4: Test the Containerized Model

```bash
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[1,1,1,1]}'
```

**Output:**
```json
{"prediction":0}
```

The model works inside the container — same as when it was running directly on the host.

---

## What Containerization Achieves

| Before (without container) | After (with container) |
|---------------------------|----------------------|
| Model runs only on the developer's machine | Model runs anywhere Docker is installed |
| "Works on my machine" problems | Same behavior on laptop, VM, or Kubernetes |
| Manual Python/dependency setup | Everything bundled in the image |
| Different environments = different results | Identical environment every time |
| Hard to deploy to production | Ready to deploy to any infrastructure |

---

## What's Next (Future Lectures)

Containerization is the **first activity** MLOps engineers do to help ML engineers. Once the model is containerized, there's more to do:

```
┌──────────────────────────────────────────────────────────────────┐
│           REMAINING MLOps ACTIVITIES                              │
│                                                                   │
│   ✅ Containerize the model (this lecture)                       │
│                                                                   │
│   Next steps (covered in future lectures):                       │
│                                                                   │
│   → Infrastructure creation                                      │
│     • Virtual machines, Kubernetes clusters                      │
│     • Using Terraform (Infrastructure as Code)                   │
│                                                                   │
│   → Kubernetes manifests                                         │
│     • Deployments, Services, Ingress                             │
│     • Helm charts for templating                                 │
│                                                                   │
│   → Deploy to Kubernetes                                         │
│     • Model serving at scale                                     │
│     • KServe for ML-specific serving                             │
│                                                                   │
│   → Networking & Security                                        │
│     • Load balancing across model instances                      │
│     • API gateway for external access                            │
│     • SSL/TLS for secure communication                           │
│                                                                   │
│   → Monitoring & Observability                                   │
│     • Model accuracy tracking                                    │
│     • Latency and error monitoring                               │
│     • Drift detection and retraining triggers                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Section Summary: How All Three Roles Work Together

```
┌──────────────────────────────────────────────────────────────────┐
│           THE COMPLETE PICTURE                                    │
│                                                                   │
│   DATA SCIENTIST                                                  │
│   • Trains the model (train.py)                                  │
│   • Saves the model (artifacts/model.pkl)                        │
│   • Tests with sample inputs (run_model.py)                      │
│                                                                   │
│   MLOps ENGINEER helps Data Scientist                            │
│   • Sets up Git repository + .gitignore                          │
│   • Builds CI/CD pipeline (GitHub Actions)                       │
│   • Automates training on every push/PR                          │
│   • Uploads model artifacts automatically                        │
│                                                                   │
│   ML ENGINEER                                                     │
│   • Builds API for the model (app.py with Flask)                 │
│   • Ensures scalability and performance                          │
│   • Integrates with backend systems                              │
│                                                                   │
│   MLOps ENGINEER helps ML Engineer                               │
│   • Containerizes the model (Dockerfile + Docker)                │
│   • Creates infrastructure (Terraform)                           │
│   • Deploys to Kubernetes                                        │
│   • Sets up networking, load balancing, monitoring               │
└──────────────────────────────────────────────────────────────────┘
```

> **Remember it this way:**
> - MLOps engineers help data scientists with **training and saving** the model
> - MLOps engineers help ML engineers with **deploying** the model
