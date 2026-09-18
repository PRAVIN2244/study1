# Module 14: Additional Topics from Comprehensive Guide

## Topics Covered
- Managing Windows Managed Nodes (WinRM)
- Testing Playbooks with Molecule
- Bastion / Jump Host Configuration
- HashiCorp Vault Integration
- Jenkins CI/CD Integration
- Expect Module for Interactive Commands
- Managing Multiple SSH Keys
- Installing Specific Package Versions
- Preventing File Overwrites (backup parameter)
- Managing Temporary Files
- Validating Configurations Before Applying
- Refreshing Facts Mid-Playbook
- Executing Tasks on Failed Hosts
- Managing Multiple Ansible Versions
- High Availability (HA) Setup with Ansible

## Why This Module Exists

These topics were identified by cross-referencing the Ansible Comprehensive Guide
(unitite.txt) against the existing course modules (1-13). Each topic listed above
was present in the reference material but absent from the course.

## Key Commands

```bash
# Windows connectivity test
ansible windows -m win_ping

# Molecule testing
molecule test
molecule converge
molecule verify

# Jump host connection
ansible private_servers -m ping  # routes through bastion via SSH config

# HashiCorp Vault collection
ansible-galaxy collection install community.hashi_vault

# Retry failed hosts
ansible-playbook deploy.yml --limit @deploy.retry

# Multiple Ansible versions
python3 -m venv ~/ansible-2.16
source ~/ansible-2.16/bin/activate
pip install ansible==9.0.0
```
