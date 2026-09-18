# Module 15 — Real-World Architecture & Correlation

**Level:** Advanced  
**Duration:** ~20 hours  
**Prerequisites:** All previous modules

---

## 15.1 Production Monitoring Architecture

### Reference Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AWS (EKS + RDS + ALB)                           │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      EKS Cluster                                │   │
│  │                                                                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │   │
│  │  │ API Gateway│  │ Payment    │  │ Inventory  │  ← Application  │   │
│  │  │ Service    │  │ Service    │  │ Service    │    Services      │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                 │   │
│  │        │               │               │                        │   │
│  │  ┌─────▼───────────────▼───────────────▼──────┐                 │   │
│  │  │              Monitoring Stack              │                 │   │
│  │  │                                            │                 │   │
│  │  │  ┌────────────┐  ┌──────────────────────┐  │                 │   │
│  │  │  │ Prometheus │  │ Datadog Agent        │  │                 │   │
│  │  │  │ (metrics)  │  │ (APM + logs + NPM)   │  │                 │   │
│  │  │  └─────┬──────┘  └──────────┬───────────┘  │                 │   │
│  │  │        │                    │              │                 │   │
│  │  │  ┌─────▼──────┐            │              │                 │   │
│  │  │  │ Grafana    │            │              │                 │   │
│  │  │  │ (dashboards│            │              │                 │   │
│  │  │  └────────────┘            │              │                 │   │
│  │  │                            │              │                 │   │
│  │  │  ┌──────────────────────┐  │              │                 │   │
│  │  │  │ Filebeat (DaemonSet) │──┼──→ ELK      │                 │   │
│  │  │  │ (security logs)      │  │   (security) │                 │   │
│  │  │  └──────────────────────┘  │              │                 │   │
│  │  └────────────────────────────┼──────────────┘                 │   │
│  └───────────────────────────────┼──────────────────────────────────┘   │
│                                  │                                     │
│  ┌───────────────────────────────┼──────────────────────────────────┐   │
│  │  AWS Native Monitoring       │                                  │   │
│  │  CloudWatch ← RDS, ALB, Lambda, S3, SQS                        │   │
│  │  CloudTrail → ELK (security audit)                              │   │
│  │  VPC Flow Logs → ELK (network security)                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Jenkins (CI/CD)                                                │   │
│  │  Prometheus Plugin → Prometheus → Grafana (DORA dashboard)      │   │
│  │  Datadog Plugin → Datadog CI Visibility                         │   │
│  │  Build Logs → ELK (failure analysis)                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tool Responsibilities

| Tool | Primary Role | Data Types |
|------|-------------|------------|
| **Prometheus + Grafana** | Infrastructure and application metrics, dashboards, alerting | Metrics |
| **Datadog** | APM, distributed tracing, real-time application monitoring | Traces, metrics, logs |
| **ELK Stack** | Security log analysis, compliance, forensics | Logs |
| **CloudWatch** | AWS service monitoring, native alarms | Metrics, logs |
| **Jenkins** | CI/CD pipeline metrics, DORA data | Metrics, logs |

### Why Multiple Tools?

| Concern | Best Tool | Reason |
|---------|-----------|--------|
| Infrastructure metrics | Prometheus | Open source, PromQL, Kubernetes-native |
| Application tracing | Datadog APM | Auto-instrumentation, service map, trace search |
| Security audit | ELK + CloudTrail | Full-text search, custom detection rules, retention |
| AWS service health | CloudWatch | Native integration, no agent needed |
| Cost visibility | CloudWatch + Datadog | AWS billing metrics + Datadog cost analysis |
| CI/CD performance | Prometheus + Datadog | Pipeline metrics + CI Visibility |

---

## 15.2 Correlation Patterns

Senior engineers don't just monitor — they **correlate** signals across tools and data types to find root causes fast.

### Pattern 1: Deployment → Pod Crash

```
Signal Chain:
Jenkins deploy succeeds → Kubernetes rollout → New pods start → Pods crash (CrashLoopBackOff)

Detection:
1. Grafana annotation shows deployment at 14:00
2. Prometheus alert: kube_pod_container_status_restarts_total spike at 14:02
3. Datadog APM: error rate jumps from 0.1% to 15% at 14:02
4. ELK: application logs show "NullPointerException" in new code path

Correlation Query (PromQL):
increase(kube_pod_container_status_restarts_total{namespace="production"}[10m]) > 0
and on(namespace)
increase(deployments_total{environment="production"}[15m]) > 0

Action:
kubectl rollout undo deployment/payment-api -n production
```

### Pattern 2: AWS Cost Spike → HPA Misconfiguration

```
Signal Chain:
CloudWatch billing alarm fires → EC2 instance count doubled → HPA scaling aggressively → CPU target too low

Detection:
1. CloudWatch: aws.billing.estimated_charges jumps 40%
2. Datadog: aws.ec2.host_count increases from 10 to 20
3. Prometheus: kube_hpa_status_current_replicas == kube_hpa_spec_max_replicas
4. Grafana: CPU utilization per pod is only 15% (HPA target was set to 10%)

Root Cause:
HPA targetCPUUtilizationPercentage was set to 10 instead of 70

Fix:
kubectl patch hpa payment-api -n production -p '{"spec":{"targetCPUUtilizationPercentage":70}}'
```

### Pattern 3: Security Alert → IAM Change

```
Signal Chain:
ELK SIEM alert fires → CloudTrail shows IAM policy change → New policy allows S3 public access

Detection:
1. ELK: CloudTrail event "PutBucketPolicy" with public access
2. ELK: Source IP is from unusual location
3. CloudWatch: S3 GetObject requests spike from external IPs
4. Datadog: Security signal for "S3 bucket made public"

Investigation (Kibana KQL):
cloudtrail.eventName: "PutBucketPolicy"
AND cloudtrail.requestParameters.bucketName: "sensitive-data-bucket"

Timeline:
- 09:15 — IAM user "dev-user" attaches AdministratorAccess policy
- 09:18 — Same user changes S3 bucket policy to public
- 09:20 — External traffic to S3 bucket begins
- 09:45 — ELK alert fires (25 min MTTD)

Action:
1. Revoke IAM user credentials
2. Revert S3 bucket policy
3. Audit CloudTrail for all actions by this user
4. Enable MFA enforcement
```

### Pattern 4: Latency Spike → Database Bottleneck

```
Signal Chain:
Datadog APM shows P99 latency spike → Trace waterfall shows slow DB query → RDS CPU at 95%

Detection:
1. Datadog APM: P99 latency jumps from 200ms to 3s at 16:00
2. Datadog trace: 80% of latency is in "mysql.query" span
3. CloudWatch: aws.rds.cpuutilization hits 95%
4. ELK: RDS slow query log shows full table scan on orders table
5. Prometheus: connection pool exhaustion (pool_active == pool_max)

Correlation:
- Deployment at 15:55 introduced a new query without an index
- Query does full table scan on 10M row table
- RDS CPU saturates, all queries slow down
- Connection pool fills up, requests queue

Fix:
1. Add missing index: CREATE INDEX idx_orders_user_date ON orders(user_id, created_at)
2. Restart connection pool
3. Add query performance test to CI pipeline
```

### Pattern 5: Cascading Failure

```
Signal Chain:
Payment service timeout → Order service retries → Circuit breaker opens → User-facing errors

Detection Timeline:
16:00 — Payment gateway (external) starts responding slowly (5s → 30s)
16:02 — Datadog APM: payment-service P99 latency spikes
16:03 — Prometheus: payment-service connection pool exhausted
16:04 — Datadog APM: order-service error rate increases (timeout calling payment)
16:05 — Prometheus: order-service retry rate 10x normal
16:06 — CloudWatch: ALB TargetResponseTime P99 > 10s
16:07 — Prometheus: order-service circuit breaker opens
16:08 — Grafana alert: error rate > 5% (customer impact)

Root Cause:
External payment gateway degradation → no timeout configured → resource exhaustion → cascade

Fix:
1. Immediate: restart payment-service pods to clear stuck connections
2. Short-term: add 5s timeout to payment gateway calls
3. Long-term: implement circuit breaker pattern, add fallback payment flow
```

---

## 15.3 Building a Correlation Framework

### Unified Tagging

The foundation of cross-tool correlation is consistent tagging.

| Tag | Applied To | Value |
|-----|-----------|-------|
| `service` | All metrics, logs, traces | `payment-api` |
| `env` | All metrics, logs, traces | `production` |
| `version` | All metrics, logs, traces | `2.3.1` |
| `team` | All metrics, logs, traces | `payments` |
| `cluster` | Kubernetes metrics | `prod-us-east-1` |
| `region` | AWS metrics | `us-east-1` |

### Trace-Log-Metric Correlation

```
                    ┌─────────────┐
                    │   Trace     │
                    │  trace_id   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼───┐ ┌──────▼──────┐
        │   Logs    │ │Metrics│ │  Events     │
        │ trace_id  │ │service│ │ deployment  │
        │ span_id   │ │env    │ │ incident    │
        └───────────┘ └───────┘ └─────────────┘
```

**Implementation:**
1. Inject `trace_id` into application logs.
2. Use consistent `service` and `env` tags across all telemetry.
3. Emit deployment events with `service` and `version` tags.
4. Link incidents to services via tags.

### Cross-Tool Navigation

| From | To | Link Method |
|------|----|-------------|
| Grafana metric spike | Datadog traces | Data link with time range and service filter |
| Datadog trace | ELK logs | Log link with trace_id |
| CloudWatch alarm | Grafana dashboard | Alarm action → SNS → Lambda → Grafana annotation |
| Jenkins deployment | Grafana annotation | Post-deploy webhook |
| ELK security alert | CloudTrail events | Kibana saved search with user/IP filter |

---

## 15.4 What Senior Engineers Do

### They Don't Just Integrate — They Correlate

| Junior Approach | Senior Approach |
|----------------|-----------------|
| "CPU is high" | "CPU is high because the new deployment introduced an N+1 query" |
| "There are errors" | "Error rate increased 2 minutes after deploy, affecting the checkout flow, impacting $X revenue/minute" |
| "Alert fired" | "This alert is noise — the metric recovered in 30 seconds and no users were affected" |
| "Dashboard looks fine" | "Dashboard looks fine but SLO error budget is 60% consumed with 20 days remaining" |

### Incident Investigation Workflow

```
1. DETECT
   └── Alert fires (Prometheus/Datadog/CloudWatch)

2. TRIAGE
   ├── Check Golden Signals dashboard
   ├── Identify affected service(s)
   └── Determine customer impact (SLO breach?)

3. CORRELATE
   ├── Recent deployments? (Grafana annotations)
   ├── Infrastructure changes? (CloudTrail)
   ├── Dependency issues? (Datadog service map)
   └── Similar past incidents? (Incident management)

4. DIAGNOSE
   ├── Traces: Find slow/failing spans (Datadog APM)
   ├── Logs: Search for errors with trace_id (ELK/Datadog)
   ├── Metrics: Check resource saturation (Prometheus/CloudWatch)
   └── Network: Check connectivity (VPC Flow Logs, NPM)

5. REMEDIATE
   ├── Rollback deployment
   ├── Scale resources
   ├── Restart services
   ├── Apply hotfix
   └── Failover to backup

6. VERIFY
   ├── Error rate returns to baseline
   ├── Latency returns to baseline
   ├── SLO error budget consumption rate normalizes
   └── No secondary effects

7. POST-MORTEM
   ├── Timeline with MTTD and MTTR
   ├── Root cause analysis
   ├── Action items (monitoring gaps, code fixes, process changes)
   └── Update runbooks
```

---

## 15.5 Lab: Build a Complete Monitoring Stack

### Architecture

Build this end-to-end:

```
EKS Cluster
├── Sample Application (3 microservices)
│   ├── frontend (Node.js)
│   ├── api (Python/Flask)
│   └── worker (Python/Celery + Redis)
│
├── Monitoring Stack
│   ├── Prometheus (kube-prometheus-stack)
│   ├── Grafana (dashboards + alerts)
│   ├── Datadog Agent (APM + logs)
│   └── Filebeat → Elasticsearch → Kibana (security)
│
├── AWS Services
│   ├── ALB (ingress)
│   ├── RDS (PostgreSQL)
│   └── SQS (message queue)
│
└── Jenkins (CI/CD pipeline)
```

### Step-by-Step Lab

#### Phase 1: Infrastructure (2 hours)

1. Create EKS cluster with 3 nodes.
2. Deploy RDS PostgreSQL instance.
3. Create SQS queue.
4. Configure ALB ingress controller.

#### Phase 2: Application (2 hours)

1. Deploy the 3-service application.
2. Verify end-to-end request flow: ALB → frontend → api → RDS/SQS → worker.
3. Generate baseline traffic with a load generator.

#### Phase 3: Monitoring Setup (4 hours)

1. **Prometheus + Grafana:**
   - Install kube-prometheus-stack.
   - Create ServiceMonitors for application services.
   - Import Kubernetes dashboards.
   - Create application Golden Signals dashboard.

2. **Datadog:**
   - Deploy Datadog Agent with APM and logs.
   - Instrument application services.
   - Verify service map and traces.

3. **ELK:**
   - Deploy Filebeat for security logs.
   - Ingest CloudTrail and VPC Flow Logs.
   - Create security dashboards.

4. **CloudWatch:**
   - Enable Container Insights.
   - Create alarms for RDS and ALB.
   - Set up anomaly detection.

5. **Jenkins:**
   - Configure pipeline with Prometheus and Datadog plugins.
   - Set up deployment annotations.

#### Phase 4: Trigger Scenarios (4 hours)

##### Scenario 1: Failed Deployment

```bash
# Deploy a version with a bug (missing environment variable)
kubectl set image deployment/api api=api:buggy -n production

# Observe:
# - Prometheus: pod restart count increases
# - Datadog APM: error rate spikes
# - ELK: application error logs
# - Grafana: deployment annotation correlates with error spike

# Remediate:
kubectl rollout undo deployment/api -n production
```

##### Scenario 2: CPU Spike

```bash
# Run stress test inside a pod
kubectl exec -it deployment/api -n production -- stress --cpu 4 --timeout 300

# Observe:
# - Prometheus: container_cpu_usage_seconds_total spikes
# - CloudWatch: node_cpu_utilization increases
# - Prometheus: HPA scales up pods
# - Datadog: latency increases due to CPU contention
```

##### Scenario 3: Unauthorized Access Attempt

```bash
# Simulate unauthorized API calls
for i in $(seq 1 100); do
  aws s3 ls s3://restricted-bucket --region us-east-1 2>/dev/null
done

# Observe:
# - ELK: CloudTrail shows AccessDenied events
# - Kibana alert fires for repeated access denied
# - VPC Flow Logs show traffic pattern
```

##### Scenario 4: Database Saturation

```bash
# Generate heavy database load
kubectl exec -it deployment/api -n production -- python -c "
import psycopg2
conn = psycopg2.connect('...')
for i in range(1000):
    conn.cursor().execute('SELECT * FROM large_table WHERE unindexed_column = %s', (i,))
"

# Observe:
# - CloudWatch: RDS CPUUtilization spikes
# - Datadog APM: database spans show high latency
# - Prometheus: connection pool metrics show exhaustion
# - ELK: RDS slow query logs appear
```

#### Phase 5: Observe and Correlate (4 hours)

For each scenario:

1. **Identify the alert** that fired first.
2. **Trace the signal chain** across tools.
3. **Find the root cause** using correlated data.
4. **Document the investigation** with timestamps and tool references.
5. **Calculate MTTD and MTTR.**
6. **Write a runbook** for the failure mode.

#### Phase 6: DORA Metrics (2 hours)

1. Run 10 deployments (mix of successful and failed).
2. Calculate all four DORA metrics.
3. Build the DORA dashboard.
4. Identify which DORA performance level the team is at.
5. Propose improvements to move to the next level.

---

## 15.6 Monitoring Maturity Model

### Level 1: Reactive

- Basic infrastructure monitoring (CPU, memory, disk).
- Manual alert investigation.
- No correlation between tools.
- Alerts are noisy.

### Level 2: Proactive

- Application-level monitoring (Golden Signals).
- SLIs and SLOs defined.
- Dashboards for key services.
- Alerts are actionable.

### Level 3: Observability

- Distributed tracing across services.
- Log-metric-trace correlation.
- Deployment annotations on dashboards.
- Error budgets drive release decisions.
- DORA metrics tracked.

### Level 4: Predictive

- Anomaly detection identifies issues before alerts fire.
- Synthetic monitoring catches problems before users do.
- Automated remediation for known failure modes.
- Chaos engineering validates monitoring coverage.
- Cost optimization is continuous.

### Assessment Checklist

| Capability | L1 | L2 | L3 | L4 |
|-----------|----|----|----|----|
| Infrastructure metrics | ✓ | ✓ | ✓ | ✓ |
| Application metrics (Golden Signals) | | ✓ | ✓ | ✓ |
| SLIs / SLOs / Error budgets | | ✓ | ✓ | ✓ |
| Distributed tracing | | | ✓ | ✓ |
| Log-metric-trace correlation | | | ✓ | ✓ |
| Deployment tracking | | | ✓ | ✓ |
| DORA metrics | | | ✓ | ✓ |
| Anomaly detection | | | | ✓ |
| Synthetic monitoring | | | | ✓ |
| Automated remediation | | | | ✓ |
| Chaos engineering | | | | ✓ |

---

## 15.7 Final Assessment

### Capstone Project

Build a complete monitoring solution for a production-like environment:

1. **Deploy** a multi-service application on EKS with RDS and ALB.
2. **Instrument** with Prometheus, Grafana, Datadog, ELK, and CloudWatch.
3. **Define** SLIs, SLOs, and error budgets for 3 services.
4. **Build** dashboards: Golden Signals, DORA metrics, AWS infrastructure, security.
5. **Create** alerts: symptom-based, with runbooks, proper severity levels.
6. **Simulate** 3 failure scenarios. Investigate and resolve each.
7. **Document** MTTD and MTTR for each incident.
8. **Write** a post-mortem for the most complex incident.
9. **Assess** your monitoring maturity level and propose improvements.

### Evaluation Criteria

| Area | Weight | What's Evaluated |
|------|--------|-----------------|
| Tool setup and integration | 20% | All tools deployed and connected |
| Dashboard quality | 20% | Actionable, well-organized, uses variables |
| Alert quality | 20% | Symptom-based, actionable, proper severity |
| Incident investigation | 20% | Cross-tool correlation, root cause found |
| Documentation | 10% | SLOs, runbooks, post-mortem |
| DORA metrics | 10% | All four metrics tracked and visualized |

---

## Course Complete

← [Course Overview](../../README.md)
