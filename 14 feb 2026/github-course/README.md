# GitHub Course — Basic to Advanced

A modular course covering GitHub and GitHub Actions from fundamentals to production-grade CI/CD.

## Modules

| # | Module | Topics |
|---|--------|--------|
| 01 | [Introduction](module-01-introduction/) | GitHub overview, features, plans, terminology |
| 02 | [GitHub Setup](module-02-github-setup/) | Account setup, GitHub Enterprise Server install, organizations |
| 03 | [Actions Fundamentals](module-03-github-actions-fundamentals/) | Workflows, jobs, steps, triggers, YAML syntax |
| 04 | [Workflows](module-04-workflows/) | Workflow patterns, matrix builds, reusable workflows, environments |
| 05 | [Runners](module-05-runners/) | GitHub-hosted runners, self-hosted runners, custom runners, autoscaling |
| 06 | [Advanced Actions](module-06-advanced-actions/) | Custom actions, composite actions, marketplace, caching, artifacts |
| 07 | [Security](module-07-security/) | Dependabot, code scanning, secret scanning, OIDC, permissions |
| 08 | [Packages & Registry](module-08-packages-and-registry/) | GHCR, npm, Maven, NuGet, RubyGems package registries |
| 09 | [GitHub Administration](module-09-github-administration/) | Org management, policies, audit log, billing |
| 10 | [Enterprise Features](module-10-enterprise-features/) | GHES install, HA, backup, SAML SSO, IP allow lists |
| 11 | [Code to Deployment](module-11-code-to-deployment/) | How code moves from GitHub to K8s/EC2, deployment methods, full flow diagrams |

## Prerequisites

- Git fundamentals
- Basic YAML knowledge
- Command line basics
- A GitHub account (free tier works for most modules)

## Quick Reference

| Topic | Where to Look |
|-------|--------------|
| How code moves from GitHub to K8s | Module 11 (full step-by-step with diagrams) |
| How code moves from GitHub to EC2 | Module 11 (4 methods: SSH, Docker, CodeDeploy, ECS) |
| Git security practices (developer) | Module 07 (signed commits, SSH keys, .gitignore, credential management) |
| GitHub platform security | Module 07 (2FA, fine-grained PATs, workflow hardening) |
| Admin security checklist | Module 09 (full checklist with UI steps) |
| Give limited access to a user | Module 09 (5 scenarios with permission tables) |
| Protect a repository | Module 09 (branch protection, CODEOWNERS, rulesets) |
| Backup a repository | Module 09 (4 backup methods: clone, API, tools, mirror) |
| Set up GitHub Actions | Module 03 (fundamentals) → Module 04 (advanced workflows) |
| Self-hosted runners | Module 05 (setup, K8s ARC, autoscaling) |
