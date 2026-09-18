# Module 2: Installation and Environment Setup

## Files
- `Vagrantfile` - Local VM lab with control node + 2 managed nodes
- `docker-compose.yml` - Lightweight Docker-based lab
- `ansible.cfg` - Sample Ansible configuration

## Installation Methods

```bash
# pip (recommended)
pip3 install ansible

# Ubuntu/Debian
sudo apt-add-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible

# RHEL/CentOS
sudo dnf install -y epel-release && sudo dnf install -y ansible-core

# macOS
brew install ansible
```

## SSH Key Setup

```bash
ssh-keygen -t ed25519 -C "ansible-control"
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.56.11
```
