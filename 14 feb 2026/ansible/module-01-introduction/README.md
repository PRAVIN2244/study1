# Module 1: Introduction to Ansible

## Topics
- What is Ansible
- Why Ansible over other tools
- Ansible architecture
- How Ansible works (step by step)
- Idempotency

## Architecture

```
CONTROL NODE
  Playbook (YAML) + Inventory (hosts) + ansible.cfg
         |
    Ansible Engine (Modules + Plugins)
         |
    SSH / WinRM connections
         |
  +------+------+------+
  |      |      |      |
Node1  Node2  Node3  NodeN
(Web)  (DB)   (App)  (...)
     MANAGED NODES
```

## How Ansible Works

1. You write a playbook (YAML file)
2. Ansible reads the inventory to know which hosts to target
3. Ansible connects to managed nodes via SSH
4. Ansible generates Python scripts from modules
5. Ansible copies scripts to managed nodes via SFTP/SCP
6. Ansible executes scripts on managed nodes
7. Ansible collects results and displays output
8. Ansible removes temporary scripts from managed nodes

## Comparison

| Feature | Ansible | Puppet | Chef | SaltStack |
|---------|---------|--------|------|-----------|
| Agent Required | No | Yes | Yes | Yes (optional) |
| Language | YAML | Puppet DSL | Ruby | YAML |
| Architecture | Push | Pull | Pull | Push/Pull |
| Learning Curve | Low | High | High | Medium |
| Communication | SSH | HTTPS (8140) | HTTPS (443) | ZeroMQ |
