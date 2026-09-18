# Module 7 — AWS Network Analyzer

**Levels:** Beginner → Intermediate → Advanced  
**Duration:** ~15 hours  
**Prerequisites:** Module 6 (AWS CloudWatch), basic networking (TCP/IP, DNS, HTTP)

---

## Level 1: Beginner

### 7.1 VPC Fundamentals (Review)

#### VPC Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                          │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │  Public Subnet          │  │  Public Subnet          │  │
│  │  10.0.1.0/24 (AZ-a)    │  │  10.0.2.0/24 (AZ-b)    │  │
│  │  ┌─────┐  ┌─────┐      │  │  ┌─────┐  ┌─────┐      │  │
│  │  │ ALB │  │ NAT │      │  │  │ ALB │  │ NAT │      │  │
│  │  └─────┘  └─────┘      │  │  └─────┘  └─────┘      │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │  Private Subnet         │  │  Private Subnet         │  │
│  │  10.0.3.0/24 (AZ-a)    │  │  10.0.4.0/24 (AZ-b)    │  │
│  │  ┌─────┐  ┌─────┐      │  │  ┌─────┐  ┌─────┐      │  │
│  │  │ EC2 │  │ ECS │      │  │  │ EC2 │  │ ECS │      │  │
│  │  └─────┘  └─────┘      │  │  └─────┘  └─────┘      │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │  Data Subnet            │  │  Data Subnet            │  │
│  │  10.0.5.0/24 (AZ-a)    │  │  10.0.6.0/24 (AZ-b)    │  │
│  │  ┌─────┐               │  │  ┌─────┐               │  │
│  │  │ RDS │               │  │  │ RDS │               │  │
│  │  └─────┘               │  │  └─────┘               │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│  Internet Gateway                                           │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Route Tables

| Destination | Target | Purpose |
|-------------|--------|---------|
| `10.0.0.0/16` | `local` | VPC internal traffic |
| `0.0.0.0/0` | `igw-xxx` | Internet (public subnets) |
| `0.0.0.0/0` | `nat-xxx` | Internet via NAT (private subnets) |
| `172.16.0.0/16` | `pcx-xxx` | VPC peering |
| `10.1.0.0/16` | `tgw-xxx` | Transit Gateway |

#### Debugging Route Issues

```bash
# List route tables
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-123" \
  --query "RouteTables[*].{ID:RouteTableId,Routes:Routes[*].{Dest:DestinationCidrBlock,Target:GatewayId||NatGatewayId||TransitGatewayId}}"

# Check subnet associations
aws ec2 describe-route-tables \
  --query "RouteTables[*].{ID:RouteTableId,Subnets:Associations[*].SubnetId}"
```

### 7.3 Security Groups vs NACLs

| Feature | Security Group | NACL |
|---------|---------------|------|
| **Level** | Instance (ENI) | Subnet |
| **State** | Stateful (return traffic auto-allowed) | Stateless (must allow both directions) |
| **Rules** | Allow only | Allow and Deny |
| **Evaluation** | All rules evaluated | Rules evaluated in order (lowest number first) |
| **Default** | Deny all inbound, allow all outbound | Allow all |

#### Common Debugging Scenarios

| Symptom | Check |
|---------|-------|
| Can't SSH to instance | SG inbound rule for port 22 from your IP |
| Instance can't reach internet | Route table has 0.0.0.0/0 → IGW/NAT, SG allows outbound |
| Service A can't reach Service B | SG of B allows inbound from SG of A |
| Intermittent connectivity | NACL rules (stateless — check both inbound and outbound) |
| Can reach port 80 but not 443 | SG or NACL missing rule for port 443 |

### 7.4 VPC Flow Logs

Flow logs capture IP traffic metadata for network interfaces, subnets, or VPCs.

#### Enable Flow Logs

```bash
# VPC-level flow logs to CloudWatch
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-123 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789:role/flow-logs-role

# VPC-level flow logs to S3 (cheaper for high volume)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-123 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket/vpc-123/
```

#### Flow Log Format

```
version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status

# Example:
2 123456789012 eni-abc123 10.0.1.5 10.0.2.10 49152 443 6 20 4000 1609459200 1609459260 ACCEPT OK
2 123456789012 eni-abc123 203.0.113.5 10.0.1.5 12345 22 6 5 400 1609459200 1609459260 REJECT OK
```

| Field | Description |
|-------|-------------|
| `srcaddr` / `dstaddr` | Source / destination IP |
| `srcport` / `dstport` | Source / destination port |
| `protocol` | IANA protocol number (6=TCP, 17=UDP, 1=ICMP) |
| `packets` / `bytes` | Packet and byte count |
| `action` | ACCEPT or REJECT |

#### Analyzing Flow Logs with CloudWatch Logs Insights

```sql
-- Top rejected connections
fields @timestamp, srcAddr, dstAddr, dstPort, action
| filter action = "REJECT"
| stats count(*) as rejections by srcAddr, dstAddr, dstPort
| sort rejections desc
| limit 20

-- Traffic volume by source IP
fields srcAddr, bytes
| stats sum(bytes) as total_bytes by srcAddr
| sort total_bytes desc
| limit 10

-- Connections to specific port
fields @timestamp, srcAddr, dstAddr, action
| filter dstPort = 22
| stats count(*) by srcAddr, action
```

### Beginner Exercises

1. **VPC review:** Draw the network diagram for an existing VPC. Identify all subnets, route tables, and gateways.
2. **Security groups:** Audit security groups for an application. Identify overly permissive rules.
3. **Flow logs:** Enable VPC Flow Logs. Analyze rejected traffic to identify misconfigured security groups.
4. **Debugging:** Given a scenario where EC2 instance A cannot reach RDS instance B, walk through the debugging steps (route tables, security groups, NACLs).

---

## Level 2: Intermediate

### 7.5 Reachability Analyzer

Reachability Analyzer tests network connectivity between two resources without sending actual traffic.

#### How It Works

```
Source → [ENI] → [Security Group] → [NACL] → [Route Table] → [Peering/TGW] → [Route Table] → [NACL] → [Security Group] → [ENI] → Destination
```

It analyzes the entire path and reports which component blocks connectivity.

#### Creating an Analysis

```bash
aws ec2 create-network-insights-path \
  --source i-source123 \
  --destination i-dest456 \
  --protocol TCP \
  --destination-port 443

# Start analysis
aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-xxx

# Get results
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-xxx
```

#### Analysis Results

The analysis returns:
- **Reachable:** Full path with all components.
- **Not reachable:** The specific component blocking traffic and why.

| Blocking Component | Common Cause |
|-------------------|-------------|
| Security Group | Missing inbound/outbound rule |
| NACL | Deny rule or missing allow rule |
| Route Table | No route to destination |
| Peering Connection | Missing route or DNS resolution |
| Transit Gateway | Missing route table association |

#### Use Cases

- Validate network configuration before deployment.
- Debug connectivity issues without SSH access.
- Verify security group changes don't break connectivity.
- Audit network paths for compliance.

### 7.6 Traffic Mirroring

Traffic Mirroring copies network traffic from an ENI to a monitoring target for deep packet inspection.

```
┌──────────┐                    ┌──────────────────┐
│  Source   │ ──── Mirror ────▶ │  Mirror Target   │
│  ENI     │                    │  (NLB or ENI)    │
└──────────┘                    │                  │
                                │  ┌────────────┐  │
                                │  │ IDS/IPS    │  │
                                │  │ Zeek       │  │
                                │  │ Suricata   │  │
                                │  └────────────┘  │
                                └──────────────────┘
```

#### Setup

```bash
# Create mirror target (NLB)
aws ec2 create-traffic-mirror-target \
  --network-load-balancer-arn arn:aws:elasticloadbalancing:...:loadbalancer/net/mirror-nlb/xxx

# Create mirror filter
aws ec2 create-traffic-mirror-filter

# Add filter rules (mirror only specific traffic)
aws ec2 create-traffic-mirror-filter-rule \
  --traffic-mirror-filter-id tmf-xxx \
  --traffic-direction ingress \
  --rule-number 100 \
  --rule-action accept \
  --protocol 6 \
  --destination-port-range FromPort=443,ToPort=443

# Create mirror session
aws ec2 create-traffic-mirror-session \
  --network-interface-id eni-source \
  --traffic-mirror-target-id tmt-xxx \
  --traffic-mirror-filter-id tmf-xxx \
  --session-number 1
```

#### Use Cases

- Intrusion detection (IDS/IPS).
- Network forensics.
- Compliance monitoring.
- Application performance analysis.

### 7.7 Transit Gateway Analysis

#### Transit Gateway Architecture

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  VPC A   │  │  VPC B   │  │  VPC C   │
│ 10.0.0/16│  │ 10.1.0/16│  │ 10.2.0/16│
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └──────┬──────┴─────────────┘
            │
   ┌────────▼────────┐
   │ Transit Gateway  │
   │                  │
   │  Route Table A   │──── VPN ────── On-premises
   │  Route Table B   │──── DX  ────── Data center
   └──────────────────┘
```

#### Debugging Transit Gateway

```bash
# List TGW route tables
aws ec2 describe-transit-gateway-route-tables \
  --transit-gateway-route-table-ids tgw-rtb-xxx

# Search routes
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxx \
  --filters "Name=type,Values=static,propagated"

# Check attachments
aws ec2 describe-transit-gateway-attachments \
  --filters "Name=transit-gateway-id,Values=tgw-xxx"
```

#### Common TGW Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| VPC A can't reach VPC B | Missing route in TGW route table | Add route for VPC B CIDR |
| Asymmetric routing | Different route tables for different attachments | Align route tables |
| On-premises can't reach VPC | Missing propagation or static route | Enable route propagation |
| Overlapping CIDRs | Two VPCs use same CIDR range | Re-architect VPC addressing |

### 7.8 Load Balancer Debugging

#### ALB Metrics and Logs

| Metric | Indicates |
|--------|-----------|
| `HealthyHostCount` = 0 | All targets unhealthy |
| `HTTPCode_ELB_5XX` high | ALB itself is erroring (capacity, config) |
| `HTTPCode_Target_5XX` high | Backend services are failing |
| `TargetResponseTime` high | Backend is slow |
| `RejectedConnectionCount` > 0 | ALB at capacity |
| `ActiveConnectionCount` | Current connections |

#### ALB Access Logs

```
# Enable access logs
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn arn:aws:elasticloadbalancing:...:loadbalancer/app/my-alb/xxx \
  --attributes Key=access_logs.s3.enabled,Value=true \
               Key=access_logs.s3.bucket,Value=my-alb-logs \
               Key=access_logs.s3.prefix,Value=alb-logs
```

#### ALB Access Log Fields

| Field | Description |
|-------|-------------|
| `request_processing_time` | Time from ALB receiving request to sending to target |
| `target_processing_time` | Time target took to respond |
| `response_processing_time` | Time from receiving response to sending to client |
| `elb_status_code` | ALB's response code |
| `target_status_code` | Target's response code |
| `actions_executed` | Actions taken (forward, redirect, fixed-response) |

#### Debugging Flowchart

```
Client can't reach service
    │
    ├── DNS resolves? → Check Route 53 / DNS
    │
    ├── ALB reachable? → Check security groups, NACLs, internet gateway
    │
    ├── ALB returning errors?
    │   ├── 502 Bad Gateway → Target not responding (check target SG, health check)
    │   ├── 503 Service Unavailable → No healthy targets
    │   ├── 504 Gateway Timeout → Target too slow (check target_processing_time)
    │   └── 5xx from target → Application error (check application logs)
    │
    └── Intermittent? → Check target health, connection draining, sticky sessions
```

### Intermediate Exercises

1. **Reachability Analyzer:** Create 5 network insights paths. Test connectivity between different resource types (EC2→RDS, EC2→EC2 cross-VPC, Lambda→ElastiCache).
2. **Traffic Mirroring:** Set up traffic mirroring to capture HTTP traffic. Analyze with tcpdump or Wireshark.
3. **Transit Gateway:** Debug a scenario where VPC A can reach VPC B but not VPC C through a Transit Gateway.
4. **Load balancer:** Analyze ALB access logs to identify slow endpoints, error patterns, and client distribution.

---

## Level 3: Advanced

### 7.9 Complex Hybrid Network Debugging

#### Hybrid Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        AWS                              │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  VPC A   │  │  VPC B   │  │  VPC C   │              │
│  │ us-east-1│  │ us-west-2│  │ eu-west-1│              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                     │
│  ┌────▼─────────────▼─────────────▼──────┐              │
│  │         Transit Gateway               │              │
│  └────────────────┬──────────────────────┘              │
│                   │                                     │
│  ┌────────────────▼──────────────────────┐              │
│  │  VPN / Direct Connect                 │              │
│  └────────────────┬──────────────────────┘              │
└───────────────────┼─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│              On-Premises Data Center                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ App      │  │ Database │  │ Legacy   │              │
│  │ Servers  │  │ Cluster  │  │ Systems  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

#### Debugging Methodology

1. **Identify the path:** Source → all intermediate components → destination.
2. **Test each hop:**
   - DNS resolution
   - Route table at each hop
   - Security groups / NACLs at each boundary
   - VPN/DX tunnel status
   - Transit Gateway route tables
3. **Check for asymmetric routing:** Return path may differ from forward path.
4. **Verify MTU:** VPN tunnels have lower MTU (1400 vs 1500). Enable TCP MSS clamping.

#### VPN Debugging

```bash
# Check VPN tunnel status
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-xxx \
  --query "VpnConnections[*].VgwTelemetry[*].{Status:Status,OutsideIP:OutsideIpAddress,StatusMessage:StatusMessage}"

# Check Direct Connect virtual interface
aws directconnect describe-virtual-interfaces \
  --query "virtualInterfaces[*].{Name:virtualInterfaceName,State:virtualInterfaceState,BGPStatus:bgpPeers[*].bgpStatus}"
```

### 7.10 Multi-Region Network Visibility

#### Inter-Region Peering Monitoring

```bash
# Check peering connection status
aws ec2 describe-vpc-peering-connections \
  --filters "Name=status-code,Values=active" \
  --query "VpcPeeringConnections[*].{ID:VpcPeeringConnectionId,Requester:RequesterVpcInfo.{VPC:VpcId,Region:Region,CIDR:CidrBlock},Accepter:AccepterVpcInfo.{VPC:VpcId,Region:Region,CIDR:CidrBlock}}"
```

#### Network Manager

AWS Network Manager provides a global view of your network.

```bash
# Create global network
aws networkmanager create-global-network \
  --description "Production Network"

# Register Transit Gateway
aws networkmanager register-transit-gateway \
  --global-network-id global-network-xxx \
  --transit-gateway-arn arn:aws:ec2:us-east-1:123456789:transit-gateway/tgw-xxx
```

**Network Manager provides:**
- Global network topology visualization.
- Transit Gateway metrics across regions.
- VPN tunnel status across all connections.
- Route analysis across the global network.
- CloudWatch events for network changes.

### 7.11 Network Performance Optimization

#### Latency Analysis

| Tool | Measures |
|------|----------|
| **VPC Flow Logs** | Packet counts, byte counts (no latency) |
| **ALB access logs** | Request/target/response processing time |
| **CloudWatch metrics** | `NetworkIn/Out`, `PacketsIn/Out` |
| **Network Manager** | Cross-region latency |
| **Reachability Analyzer** | Path analysis (not latency) |

#### Optimization Strategies

| Issue | Solution |
|-------|----------|
| High cross-AZ latency | Place communicating services in same AZ |
| High cross-region latency | Use Global Accelerator or CloudFront |
| VPN throughput limits | Use Direct Connect or multiple VPN tunnels |
| NAT Gateway bottleneck | Use multiple NAT Gateways or VPC endpoints |
| DNS resolution latency | Use Route 53 Resolver endpoints |

#### VPC Endpoints (Reduce NAT Gateway Traffic)

```bash
# Gateway endpoint (S3, DynamoDB) — free
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-xxx

# Interface endpoint (other services) — $0.01/hour + data
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.sqs \
  --subnet-ids subnet-xxx \
  --security-group-ids sg-xxx
```

### 7.12 Security Auditing

#### Network Security Audit Checklist

| Check | Tool | Query |
|-------|------|-------|
| Open security groups (0.0.0.0/0) | AWS Config | `INCOMING_SSH_DISABLED`, `RESTRICTED_INCOMING_TRAFFIC` |
| Unused security groups | CLI | `describe-network-interfaces` cross-referenced with SGs |
| Flow log coverage | CLI | Check all VPCs have flow logs enabled |
| Public subnets with databases | Reachability Analyzer | Test internet → RDS path |
| Unencrypted traffic | Traffic Mirroring | Inspect for non-TLS traffic |

#### Automated Security Checks

```bash
# Find security groups allowing SSH from anywhere
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.from-port,Values=22" \
             "Name=ip-permission.to-port,Values=22" \
             "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query "SecurityGroups[*].{ID:GroupId,Name:GroupName,VPC:VpcId}"

# Find security groups allowing all traffic
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.protocol,Values=-1" \
             "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query "SecurityGroups[*].{ID:GroupId,Name:GroupName}"

# Check for VPCs without flow logs
aws ec2 describe-vpcs --query "Vpcs[*].VpcId" --output text | while read vpc; do
  logs=$(aws ec2 describe-flow-logs --filter "Name=resource-id,Values=$vpc" --query "FlowLogs[*].FlowLogId" --output text)
  if [ -z "$logs" ]; then
    echo "WARNING: VPC $vpc has no flow logs"
  fi
done
```

### Advanced Exercises

1. **Hybrid debugging:** Simulate a connectivity issue between an on-premises server (via VPN) and an EC2 instance. Debug using VPN telemetry, route tables, and Reachability Analyzer.
2. **Multi-region:** Set up Network Manager for a multi-region Transit Gateway deployment. Create a global topology view.
3. **Performance:** Analyze network performance between two AZs. Implement VPC endpoints to reduce NAT Gateway traffic and measure cost savings.
4. **Security audit:** Run a full network security audit. Identify and remediate: open security groups, missing flow logs, public database access paths.
5. **Incident response:** Given VPC Flow Logs showing a DDoS pattern, identify the attack source, affected resources, and implement mitigation (NACL deny rules, WAF).

---

## Previous Module

← [Module 6 — AWS CloudWatch](../06-aws-cloudwatch/README.md)

## Next Module

→ [Module 8 — Datadog + AWS Integration](../08-datadog-aws-integration/README.md)
