# Jenkins Course — Basic to Advanced

A modular course covering Jenkins CI/CD from fundamentals to production-grade setups.

## Modules

| # | Module | Topics |
|---|--------|--------|
| 01 | [Introduction](module-01-introduction/) | What is Jenkins, CI/CD concepts, history, use cases |
| 02 | [Installation & Setup](module-02-installation-and-setup/) | Install on Linux/Docker/K8s, initial configuration |
| 03 | [Architecture](module-03-architecture/) | Internal architecture, request flow, file system layout |
| 04 | [Jobs & Builds](module-04-jobs-and-builds/) | Freestyle jobs, parameterized builds, build triggers |
| 05 | [Pipelines](module-05-pipelines/) | Declarative & Scripted pipelines, Jenkinsfile, shared libraries |
| 06 | [Master-Slave Architecture](module-06-master-slave-architecture/) | Agent setup, SSH/JNLP agents, labels, distributed builds |
| 07 | [Plugins](module-07-plugins/) | Essential plugins, plugin management, writing custom plugins |
| 08 | [Security](module-08-security/) | Authentication, authorization, credentials, RBAC |
| 09 | [Integrations](module-09-integrations/) | Git, Docker, Kubernetes, SonarQube, Slack, Artifactory |
| 10 | [Advanced Topics](module-10-advanced-topics/) | HA, backup/restore, monitoring, performance tuning, CasC |
| 11 | [DevSecOps Pipeline](module-11-devsecops-pipeline/) | Jacoco, OWASP Dependency Check, SonarQube, OWASP ZAP, ECR, Artifactory, IaC scanning, pipeline failure conditions |
| 12 | [Jenkins on EC2 with GitHub](module-12-jenkins-ec2-github/) | EC2 setup, webhooks, GitHub API, commit status, bidirectional communication |
| 13 | [AWS Secrets in Jenkins](module-13-aws-secrets-in-jenkins/) | Secrets Manager, Parameter Store, IAM roles, credentials plugin, secret rotation |

## Prerequisites

- Linux basics (command line, package management)
- Git fundamentals
- Basic understanding of software build processes

## What You'll Be Able to Do After This Course

After completing all modules, you will be able to:

- Install and configure Jenkins on Linux, Docker, and Kubernetes
- Set up master-slave architecture with SSH and JNLP agents
- Write declarative pipelines with parameters, conditions, and error handling
- Build Java/Spring Boot applications with Maven
- Implement DevSecOps pipelines with security scanning at every stage
- Integrate Jenkins with Git, Docker, Artifactory, SonarQube, and AWS ECR
- Deploy applications to Kubernetes from Jenkins
- Manage credentials, RBAC, and security hardening
- Set up backup, monitoring, and high availability
- Connect Jenkins on EC2 to GitHub with webhooks and API integration
- Retrieve secrets from AWS Secrets Manager and Parameter Store in pipelines
- Configure pipeline failure conditions for security tools (SonarQube, OWASP, Trivy)

## Quick Reference

| Task | Where to Look |
|------|--------------|
| Install Jenkins | Module 02 |
| Set up agents/slaves | Module 06 |
| Write your first pipeline | Module 05 (Examples 1-6) |
| Add parameters to a pipeline | Module 05 (Example 7) |
| Conditional stage execution | Module 05 (Examples 16-20) |
| Handle errors in pipelines | Module 05 (Example 15) |
| Set up SonarQube scanning | Module 07 + Module 11 |
| Build a Spring Boot app | Module 11 |
| Full DevSecOps pipeline | Module 11 |
| Push images to ECR | Module 11 |
| Security tool failure thresholds | Module 11 (Pipeline Failure Conditions) |
| Jenkins + GitHub webhooks | Module 12 |
| GitHub API from Jenkins | Module 12 (Section 4) |
| AWS Secrets in pipelines | Module 13 |
| IAM instance profiles for Jenkins | Module 13 (Section 3) |
| Multi-stage pipeline | Module 05 (Multi-Stage Pipeline) |
| Shared libraries | Module 05 (Shared Libraries) |
| Jenkins HA setup | Module 10 (High Availability) |
