# Module 01 — Introduction to GitHub

## What is GitHub?

GitHub is a cloud-based platform for version control and collaboration using Git. It provides source code hosting, CI/CD (GitHub Actions), project management, security scanning, and package hosting.

- **Founded**: 2008 by Tom Preston-Werner, Chris Wanstrath, PJ Hyett, Scott Chacon
- **Acquired by**: Microsoft (2018)
- **Users**: 100M+ developers
- **Website**: https://github.com

## GitHub Plans

| Feature | Free | Team | Enterprise |
|---------|------|------|------------|
| **Public repos** | Unlimited | Unlimited | Unlimited |
| **Private repos** | Unlimited | Unlimited | Unlimited |
| **Collaborators** | Unlimited | Unlimited | Unlimited |
| **Actions minutes** | 2,000/month | 3,000/month | 50,000/month |
| **Packages storage** | 500 MB | 2 GB | 50 GB |
| **Code owners** | ✓ | ✓ | ✓ |
| **Protected branches** | Limited | ✓ | ✓ |
| **Required reviewers** | ✗ | ✓ | ✓ |
| **SAML SSO** | ✗ | ✗ | ✓ |
| **Audit log** | ✗ | ✗ | ✓ |
| **GHES (self-hosted)** | ✗ | ✗ | ✓ |
| **Advanced Security** | Public repos | ✗ | Add-on |

## GitHub Products

| Product | Description |
|---------|-------------|
| **GitHub.com** | SaaS platform (cloud-hosted) |
| **GitHub Enterprise Cloud** | Enhanced cloud with SSO, audit, compliance |
| **GitHub Enterprise Server (GHES)** | Self-hosted GitHub for on-premises |
| **GitHub Actions** | CI/CD automation platform |
| **GitHub Packages** | Package hosting (npm, Docker, Maven, etc.) |
| **GitHub Copilot** | AI-powered code assistant |
| **GitHub Advanced Security** | SAST, secret scanning, dependency review |
| **GitHub Pages** | Static site hosting |

## Core Terminology

- **Repository (repo)**: A project containing files, history, and configuration
- **Branch**: A parallel version of the repository
- **Commit**: A snapshot of changes
- **Pull Request (PR)**: A proposal to merge changes from one branch to another
- **Fork**: A personal copy of someone else's repository
- **Issue**: A task, bug report, or feature request
- **Actions**: GitHub's CI/CD platform
- **Workflow**: An automated process defined in YAML
- **Runner**: A machine that executes workflow jobs
- **Organization (org)**: A shared account for teams
- **Team**: A group of org members with specific permissions

## GitHub vs GitLab vs Jenkins

| Feature | GitHub | GitLab | Jenkins |
|---------|--------|--------|---------|
| **Type** | Code hosting + CI/CD | Complete DevOps platform | CI/CD server |
| **Hosting** | SaaS + GHES | SaaS + Self-hosted | Self-hosted only |
| **CI/CD Config** | `.github/workflows/*.yml` | `.gitlab-ci.yml` | `Jenkinsfile` |
| **Marketplace** | Actions marketplace | CI/CD components | Plugin ecosystem |
| **Container Registry** | GHCR (ghcr.io) | Built-in | Requires plugin |
| **Issue Tracking** | Issues + Projects | Issues + Boards | Requires plugin |
| **Security** | Advanced Security | Built-in (Ultimate) | Requires plugins |
| **Learning Curve** | Low | Moderate | Steep |

## GitHub Flow

The recommended workflow for GitHub:

```
1. Create a branch from main
   └── git checkout -b feature/my-feature

2. Make changes and commit
   └── git add . && git commit -m "Add feature"

3. Push branch to GitHub
   └── git push origin feature/my-feature

4. Open a Pull Request
   └── Describe changes, request reviewers

5. CI/CD runs automatically
   ├── Tests pass ✓
   ├── Linting passes ✓
   └── Security checks pass ✓

6. Code review
   ├── Reviewers comment
   └── Approve PR

7. Merge to main
   ├── Squash and merge (clean history)
   ├── Merge commit (preserve history)
   └── Rebase and merge (linear history)

8. Delete branch
   └── Automatic cleanup
```

## GitHub Architecture (SaaS)

```
┌─────────────────────────────────────────────────┐
│                  GitHub.com                       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Web UI   │  │ REST API │  │ GraphQL API  │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Actions  │  │ Packages │  │ Security     │   │
│  │ (CI/CD)  │  │ (Registry│  │ (Scanning)   │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Issues   │  │ Projects │  │ Discussions  │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────┘
         │
         │  ┌──────────────┐  ┌──────────────┐
         ├──│ GitHub-hosted │  │ Self-hosted  │
         │  │ Runners      │  │ Runners      │
         │  └──────────────┘  └──────────────┘
         │
         │  ┌──────────────┐
         └──│ GitHub Apps  │
            │ & Webhooks   │
            └──────────────┘
```

## Getting Started

1. Create a GitHub account at https://github.com
2. Set up SSH keys:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   cat ~/.ssh/id_ed25519.pub
   # Add to GitHub: Settings → SSH and GPG keys → New SSH key
   ```
3. Configure Git:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your_email@example.com"
   ```
4. Create your first repository
5. Set up GitHub Actions (Module 03)
