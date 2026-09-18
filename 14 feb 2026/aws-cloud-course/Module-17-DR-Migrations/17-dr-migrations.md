# Module 17: Disaster Recovery & Migrations

## 17.1 Disaster Recovery Overview

### RPO and RTO

```
Data loss ◀──── RPO ────▶ Disaster ◀──── RTO ────▶ Recovery
(Recovery Point Objective)            (Recovery Time Objective)

RPO = How much data can you afford to lose? (time between last backup and disaster)
RTO = How long can you afford to be down? (time to recover after disaster)
```

---

## 17.2 DR Strategies (Cheapest to Most Expensive)

### 1. Backup and Restore (High RPO, High RTO)

```
Normal: Data ──▶ S3 / EBS Snapshots / RDS Snapshots (periodic backups)
Disaster: Restore from backups ──▶ Launch infrastructure ──▶ Recover
```

- RPO: Hours (depends on backup frequency)
- RTO: Hours (time to restore and launch)
- Cost: Lowest (only storage costs)

### 2. Pilot Light

```
Normal: Core systems running at minimum (e.g., RDS replica, no app servers)
Disaster: Scale up app servers, switch DNS
```

- RPO: Minutes (continuous replication)
- RTO: 10s of minutes (start servers, switch traffic)
- Cost: Low (only core DB running)

### 3. Warm Standby

```
Normal: Full system running at minimum capacity in DR region
Disaster: Scale up to production capacity, switch DNS
```

- RPO: Seconds (continuous replication)
- RTO: Minutes (scale up existing infrastructure)
- Cost: Medium (reduced-capacity system always running)

### 4. Multi-Site / Hot Site (Active-Active)

```
Normal: Full production in both regions, traffic split between them
Disaster: Route all traffic to healthy region
```

- RPO: Near zero (active-active replication)
- RTO: Near zero (already running)
- Cost: Highest (2x infrastructure)

### Strategy Comparison

| Strategy | RPO | RTO | Cost |
|----------|-----|-----|------|
| Backup & Restore | Hours | Hours | $ |
| Pilot Light | Minutes | 10s of minutes | $$ |
| Warm Standby | Seconds | Minutes | $$$ |
| Multi-Site | Near zero | Near zero | $$$$ |

---

## 17.3 DR Tips

- Use Route 53 health checks and failover routing
- Automate recovery with CloudFormation / Terraform
- Test DR procedures regularly (game days)
- Use S3 Cross-Region Replication for data
- Use Aurora Global Database for database DR (< 1s RPO, < 1 min RTO)
- Use RDS Multi-AZ for AZ-level failures (not region-level)

---

## 17.4 AWS Elastic Disaster Recovery (DRS)

Formerly CloudEndure Disaster Recovery. Continuously replicates servers to AWS for fast recovery.

```
On-Premises / Other Cloud ──▶ AWS DRS Agent ──▶ Staging Area (low-cost instances)
                                                       │
                                                  Disaster occurs
                                                       │
                                                  Launch full instances in minutes
```

- Continuous block-level replication
- Sub-second RPO, minutes RTO
- Supports physical, virtual, and cloud servers

---

## 17.5 DMS — Database Migration Service

Migrate databases to AWS with minimal downtime. Source database remains operational during migration.

### Supported Migrations

| Type | Source → Target | Tool Needed |
|------|----------------|-------------|
| **Homogeneous** | MySQL → RDS MySQL | DMS only |
| **Heterogeneous** | Oracle → Aurora PostgreSQL | SCT + DMS |

### AWS Schema Conversion Tool (SCT)

Converts database schema from one engine to another (e.g., Oracle → PostgreSQL). Not needed for same-engine migrations.

### Continuous Replication

```bash
# DMS supports ongoing replication (CDC - Change Data Capture)
Source DB ──▶ DMS Replication Instance ──▶ Target DB
              (runs in VPC)                (keeps in sync)
```

### DMS Multi-AZ

Enable Multi-AZ for the DMS replication instance for HA. Provides redundant replication instance in another AZ.

### Common Migration Paths

| Source | Target | Notes |
|--------|--------|-------|
| On-prem MySQL | RDS MySQL | DMS with CDC |
| On-prem Oracle | Aurora PostgreSQL | SCT + DMS |
| RDS MySQL | Aurora MySQL | Use Aurora read replica, then promote |
| On-prem PostgreSQL | Aurora PostgreSQL | Use `pg_dump` or DMS |

---

## 17.6 AWS Application Migration Service (MGN)

Lift-and-shift migration of servers to AWS. Replaces the older Server Migration Service (SMS).

```
On-Premises Servers ──▶ MGN Agent ──▶ Continuous Replication ──▶ Test ──▶ Cutover
                                      (staging area in AWS)
```

- Supports physical, virtual, and cloud servers
- Minimal downtime during cutover
- Automated conversion to run natively on AWS

---

## 17.7 AWS Backup

Centralized backup service across AWS services.

### Supported Services

S3, EBS, EFS, RDS, Aurora, DynamoDB, DocumentDB, Neptune, FSx, Storage Gateway, EC2 (AMIs)

### Features

- **Backup Plans**: Define schedule, retention, lifecycle (move to cold storage)
- **Backup Vault**: Encrypted storage for backups
- **Vault Lock**: WORM (Write Once Read Many) — prevents deletion even by root
- **Cross-Region Backup**: Copy backups to another region for DR
- **Cross-Account Backup**: Copy backups to another AWS account

```bash
# Create backup vault
aws backup create-backup-vault --backup-vault-name my-vault

# Create backup plan
aws backup create-backup-plan --backup-plan '{
  "BackupPlanName": "daily-backup",
  "Rules": [{
    "RuleName": "daily-rule",
    "TargetBackupVaultName": "my-vault",
    "ScheduleExpression": "cron(0 3 * * ? *)",
    "StartWindowMinutes": 60,
    "CompletionWindowMinutes": 180,
    "Lifecycle": {
      "MoveToColdStorageAfterDays": 30,
      "DeleteAfterDays": 365
    }
  }]
}'
```

---

## 17.8 Transferring Large Data to AWS

| Amount | Method | Time |
|--------|--------|------|
| < 10 GB | Internet transfer | Minutes to hours |
| 10 GB – 10 TB | AWS DataSync (over internet or Direct Connect) | Hours |
| 10 TB – 80 TB | Snowball Edge | Days (shipping) |
| > 80 TB | Multiple Snowballs or Snowmobile | Days to weeks |
| Ongoing sync | DataSync or Storage Gateway | Continuous |

---

## 17.9 On-Premises Strategy with AWS

| Strategy | Service |
|----------|---------|
| Download AMIs as VM images | EC2 VM Import/Export |
| Run VMs on-premises | AWS Outposts (AWS infrastructure on-prem) |
| Migrate databases | DMS + SCT |
| Migrate servers | Application Migration Service (MGN) |
| Discover on-prem inventory | Application Discovery Service |
| Hybrid storage | Storage Gateway |
| Hybrid networking | Site-to-Site VPN, Direct Connect |

---

## 17.10 Key Takeaways

1. DR strategies: Backup & Restore (cheapest) → Pilot Light → Warm Standby → Multi-Site (fastest)
2. RPO = acceptable data loss; RTO = acceptable downtime
3. DMS for database migrations with minimal downtime; SCT for schema conversion
4. MGN for lift-and-shift server migrations
5. AWS Backup for centralized backup management across services
6. Vault Lock for compliance (WORM — prevents deletion)
7. Use Snowball for large offline data transfers (10 TB+)
8. Test DR procedures regularly — untested DR is not DR
