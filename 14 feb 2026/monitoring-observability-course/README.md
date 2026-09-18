# Monitoring & Observability — Complete Course

A structured, module-based course covering monitoring and observability from fundamentals through production-grade implementations with real-world integrations.

## Course Map

### Part 1: Core Tools

| Module | Topic | Levels |
|--------|-------|--------|
| 1 | [Observability Foundations](modules/01-foundations/README.md) | Beginner |
| 2 | [Prometheus](modules/02-prometheus/README.md) | Beginner → Advanced |
| 3 | [Grafana](modules/03-grafana/README.md) | Beginner → Advanced |
| 4 | [Datadog](modules/04-datadog/README.md) | Beginner → Advanced |
| 5 | [ELK Stack](modules/05-elk-stack/README.md) | Beginner → Advanced |
| 6 | [AWS CloudWatch](modules/06-aws-cloudwatch/README.md) | Beginner → Advanced |
| 7 | [AWS Network Analyzer](modules/07-aws-network-analyzer/README.md) | Beginner → Advanced |
| 8 | [Datadog + AWS Integration](modules/08-datadog-aws-integration/README.md) | Beginner → Advanced |

### Part 2: Software Delivery Metrics

| Module | Topic | Levels |
|--------|-------|--------|
| 9 | [DORA Metrics & Pipeline Observability](modules/09-dora-metrics/README.md) | Intermediate |

### Part 3: Tool Integrations

| Module | Topic | Integrations |
|--------|-------|-------------|
| 10 | [Prometheus Integrations](modules/10-prometheus-integrations/README.md) | Kubernetes, AWS, Jenkins |
| 11 | [Grafana Integrations](modules/11-grafana-integrations/README.md) | Kubernetes, AWS, Jenkins |
| 12 | [Datadog Integrations](modules/12-datadog-integrations/README.md) | Kubernetes, AWS, Jenkins |
| 13 | [ELK Stack Integrations](modules/13-elk-integrations/README.md) | Kubernetes, AWS, Jenkins |
| 14 | [CloudWatch Integrations](modules/14-cloudwatch-integrations/README.md) | EKS, AWS Services, Jenkins |

### Part 4: Putting It All Together

| Module | Topic | Level |
|--------|-------|-------|
| 15 | [Real-World Architecture & Correlation](modules/15-real-world-architecture/README.md) | Advanced |

## How to Use This Course

### Recommended Learning Paths

**Path A: Full Course (all 15 modules)**
1. Start with Module 1 (Foundations).
2. Work through Part 1 (Modules 2–8) to learn each tool.
3. Study DORA metrics (Module 9).
4. Learn integrations (Modules 10–14) for tools you use.
5. Complete the capstone (Module 15).

**Path B: Prometheus + Grafana Focus**
1. Module 1 → Module 2 → Module 3 → Module 9 → Module 10 → Module 11 → Module 15

**Path C: Datadog Focus**
1. Module 1 → Module 4 → Module 8 → Module 9 → Module 12 → Module 15

**Path D: AWS-Native Focus**
1. Module 1 → Module 6 → Module 7 → Module 8 → Module 14 → Module 15

**Path E: Security & Compliance**
1. Module 1 → Module 5 → Module 7 → Module 13 (ELK+AWS) → Module 15

### Per-Module Structure

Each module contains:
- **Concepts** with architecture diagrams and comparison tables.
- **Configuration examples** with real YAML, JSON, CLI commands, and code.
- **Hands-on exercises** at each level.
- **Progressive difficulty** from beginner through advanced.

## Prerequisites

- Linux command line basics
- Docker fundamentals
- Basic networking (TCP/IP, DNS, HTTP)
- Kubernetes basics (for integration modules)
- An AWS account (for cloud modules)
- A Datadog trial account (for Datadog modules)
