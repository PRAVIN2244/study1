# Module 01 — Introduction to GitLab

## What is GitLab?

GitLab is a complete DevOps platform delivered as a single application. It covers the entire software development lifecycle: planning, source code management, CI/CD, monitoring, and security.

- **Founded**: 2011 by Dmitriy Zaporozhets and Valery Sizov
- **License**: MIT (Community Edition), Proprietary (Enterprise)
- **Language**: Ruby on Rails (backend), Vue.js (frontend), Go (Gitaly, GitLab Runner)
- **Website**: https://about.gitlab.com

## GitLab Editions

| Feature | Community (CE) | Premium | Ultimate |
|---------|---------------|---------|----------|
| **Price** | Free | Paid | Paid |
| **Source Code** | Open source | Proprietary | Proprietary |
| **CI/CD** | ✓ | ✓ | ✓ |
| **Container Registry** | ✓ | ✓ | ✓ |
| **SAST/DAST** | Limited | ✓ | ✓ |
| **Dependency Scanning** | ✗ | ✗ | ✓ |
| **Compliance** | ✗ | ✓ | ✓ |
| **Epics & Roadmaps** | ✗ | ✓ | ✓ |
| **Support** | Community | Priority | Priority |

## GitLab vs GitHub vs Jenkins

| Feature | GitLab | GitHub | Jenkins |
|---------|--------|--------|---------|
| **Type** | Complete DevOps platform | Code hosting + Actions | CI/CD server |
| **SCM** | Built-in | Built-in | Requires plugin |
| **CI/CD** | Built-in (.gitlab-ci.yml) | Built-in (Actions) | Core feature (Jenkinsfile) |
| **Issue Tracking** | Built-in | Built-in | Requires plugin |
| **Container Registry** | Built-in | Built-in (GHCR) | Requires plugin |
| **Security Scanning** | Built-in (Ultimate) | Third-party / Advanced Security | Requires plugins |
| **Self-Hosted** | ✓ (CE/EE) | ✓ (Enterprise) | ✓ |
| **SaaS** | gitlab.com | github.com | ✗ |

## GitLab DevOps Stages

```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│  Plan   │─▶│ Create  │─▶│ Verify  │─▶│ Package │─▶│ Release │
│         │  │         │  │         │  │         │  │         │
│ Issues  │  │ Git     │  │ CI/CD   │  │Registry │  │ Deploy  │
│ Boards  │  │ Merge   │  │ Testing │  │ Helm    │  │ Envs    │
│ Epics   │  │ Requests│  │ Quality │  │ npm     │  │ Pages   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
      │                                                    │
      │           ┌─────────┐  ┌─────────┐                │
      │           │Configure│  │ Monitor │                │
      └──────────▶│         │─▶│         │◀───────────────┘
                  │ IaC     │  │ Metrics │
                  │ ChatOps │  │ Logging │
                  └─────────┘  └─────────┘
```

## Core Terminology

- **Project**: A repository with associated features (issues, CI/CD, wiki)
- **Group**: A collection of projects (like an organization)
- **Subgroup**: Nested groups for hierarchical organization
- **Merge Request (MR)**: GitLab's equivalent of a Pull Request
- **Pipeline**: A CI/CD workflow defined in `.gitlab-ci.yml`
- **Job**: A single task in a pipeline (build, test, deploy)
- **Stage**: A group of jobs that run in parallel
- **Runner**: An agent that executes CI/CD jobs
- **Artifact**: Files produced by a job (binaries, reports)
- **Environment**: A deployment target (dev, staging, production)
- **Registry**: Container image or package storage

## GitLab Workflow

```
1. Create Issue
   └── Describe feature/bug

2. Create Merge Request (from issue)
   └── Auto-creates branch

3. Write Code
   └── Push commits to branch

4. Pipeline Runs Automatically
   ├── Build
   ├── Test
   ├── Security Scan
   └── Review App deploys

5. Code Review
   ├── Reviewers comment
   ├── Approve MR
   └── Pipeline must pass

6. Merge
   ├── Squash commits (optional)
   ├── Delete source branch
   └── Close linked issue

7. Deploy
   ├── Auto-deploy to staging
   └── Manual deploy to production
```

## GitLab SaaS vs Self-Hosted

### SaaS (gitlab.com)

- No infrastructure to manage
- Free tier: 5 GB storage, 400 CI/CD minutes/month
- Premium/Ultimate tiers for more features
- Shared runners provided

### Self-Hosted

- Full control over data and infrastructure
- No usage limits (you provide the compute)
- Required for air-gapped or regulated environments
- You manage upgrades, backups, and scaling
