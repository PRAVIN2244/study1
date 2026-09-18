# Complete Ansible Course: From Zero to Production

## Course Overview

| Module | Topic | Level |
|--------|-------|-------|
| 1 | Introduction to Ansible | Beginner |
| 2 | Installation and Environment Setup | Beginner |
| 3 | Inventory Management | Beginner |
| 4 | Ad-Hoc Commands | Beginner |
| 5 | Playbooks Fundamentals | Beginner-Intermediate |
| 6 | Variables, Facts and Registers | Intermediate |
| 7 | Conditionals, Loops and Handlers | Intermediate |
| 8 | Roles and Ansible Galaxy | Intermediate |
| 9 | Templates (Jinja2) and File Management | Intermediate |
| 10 | Vault, Security and Secrets | Intermediate-Advanced |
| 11 | Advanced Topics | Advanced |
| 12 | Real-World Industry Projects | Advanced |
| 13 | Common Errors and Troubleshooting | All Levels |

---

# MODULE 1: Introduction to Ansible

## 1.1 What is Ansible?

Ansible is an open-source IT automation tool written in Python. It automates:
- **Configuration Management** - Setting up servers consistently
- **Application Deployment** - Deploying code to servers
- **Orchestration** - Coordinating multi-tier deployments
- **Provisioning** - Creating cloud infrastructure

### Key Characteristics

| Feature | Description |
|---------|-------------|
| Agentless | No software needed on managed nodes (uses SSH) |
| Idempotent | Running the same task multiple times produces the same result |
| Declarative | You describe the desired state, not the steps |
| YAML-based | Human-readable configuration files |
| Push-based | Control node pushes configuration to managed nodes |

## 1.2 Why Ansible Over Other Tools?

| Feature | Ansible | Puppet | Chef | SaltStack |
|---------|---------|--------|------|-----------|
| Agent Required | No | Yes | Yes | Yes (optional) |
| Language | YAML | Puppet DSL | Ruby | YAML |
| Architecture | Push | Pull | Pull | Push/Pull |
| Learning Curve | Low | High | High | Medium |
| Communication | SSH | HTTPS (8140) | HTTPS (443) | ZeroMQ |

### Real-World Use Case

**Scenario**: A company has 500 servers across AWS, Azure, and on-premise.

- **Without Ansible**: SSH into each server, run commands manually. Takes days, error-prone.
- **With Ansible**: Write one playbook, execute once. Takes minutes, consistent results.

## 1.3 Ansible Architecture

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

### Components Explained

- **Control Node**: Machine where Ansible is installed. Must run Linux/macOS (Windows NOT supported as control node).
- **Managed Nodes**: Target machines. Can be Linux, Windows, network devices. No Ansible installation needed.
- **Inventory**: File listing all managed nodes, organized into groups.
- **Modules**: Units of code executed on managed nodes (e.g., apt, copy, service).
- **Plugins**: Extend Ansible core functionality (connection, callback, filter plugins).
- **Playbooks**: YAML files describing desired state of infrastructure.

## 1.4 How Ansible Works (Step by Step)

```
Step 1: You write a playbook (YAML file)
Step 2: Ansible reads the inventory to know which hosts to target
Step 3: Ansible connects to managed nodes via SSH
Step 4: Ansible generates Python scripts from modules
Step 5: Ansible copies scripts to managed nodes via SFTP/SCP
Step 6: Ansible executes scripts on managed nodes
Step 7: Ansible collects results and displays output
Step 8: Ansible removes temporary scripts from managed nodes
```

### Understanding Idempotency

```bash
# First run: Ansible installs nginx (CHANGED)
$ ansible webservers -m apt -a "name=nginx state=present"
web1 | CHANGED => { "changed": true }

# Second run: nginx already installed (OK - no change)
$ ansible webservers -m apt -a "name=nginx state=present"
web1 | SUCCESS => { "changed": false }
```

Ansible checks the current state before making changes. If the desired state already exists, it does nothing.

---

# MODULE 2: Installation and Environment Setup

## 2.1 Prerequisites

| Requirement | Control Node | Managed Node |
|-------------|-------------|--------------|
| OS | Linux/macOS | Linux/Windows/macOS |
| Python | 3.9+ | 2.7+ or 3.5+ |
| SSH | OpenSSH client | OpenSSH server |

## 2.2 Installation Methods

### Method 1: pip (Recommended)

```bash
$ sudo apt update && sudo apt install -y python3-pip
$ pip3 install ansible
$ ansible --version
```

**Output:**
```
ansible [core 2.16.3]
  config file = /etc/ansible/ansible.cfg
  configured module search path = ['/home/user/.ansible/plugins/modules']
  ansible python module location = /usr/lib/python3/dist-packages/ansible
  python version = 3.10.12
  jinja version = 3.1.2
```

**Meaning of each line:**
- `config file`: Location of the active configuration file
- `module search path`: Where Ansible looks for custom modules
- `python version`: Python interpreter Ansible uses

### Method 2: Ubuntu/Debian

```bash
$ sudo apt-add-repository --yes --update ppa:ansible/ansible
$ sudo apt install -y ansible
```

### Method 3: RHEL/CentOS/Fedora

```bash
$ sudo dnf install -y epel-release
$ sudo dnf install -y ansible-core
```

### Method 4: macOS

```bash
$ brew install ansible
```

### Method 5: Specific Version

```bash
$ pip3 install ansible==8.0.0
$ pip3 install ansible-core==2.16.3  # lighter, no collections
$ pip3 install --upgrade ansible     # upgrade to latest
```

## 2.3 Lab Environment Setup

### Option A: Vagrant (Local VMs)

```ruby
# Vagrantfile
Vagrant.configure("2") do |config|
  config.vm.define "control" do |control|
    control.vm.box = "ubuntu/jammy64"
    control.vm.hostname = "control"
    control.vm.network "private_network", ip: "192.168.56.10"
    control.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
    end
    control.vm.provision "shell", inline: <<-SHELL
      apt-get update && apt-get install -y ansible sshpass
    SHELL
  end

  config.vm.define "web1" do |web|
    web.vm.box = "ubuntu/jammy64"
    web.vm.hostname = "web1"
    web.vm.network "private_network", ip: "192.168.56.11"
  end

  config.vm.define "db1" do |db|
    db.vm.box = "ubuntu/jammy64"
    db.vm.hostname = "db1"
    db.vm.network "private_network", ip: "192.168.56.12"
  end
end
```

```bash
$ vagrant up
$ vagrant ssh control
```

### Option B: Docker (Lightweight)

```yaml
# docker-compose.yml
version: '3.8'
services:
  control:
    image: ubuntu:22.04
    container_name: ansible-control
    hostname: control
    command: sleep infinity
    volumes:
      - ./ansible:/ansible
    networks:
      ansible_net:
        ipv4_address: 172.20.0.10

  web1:
    image: ubuntu:22.04
    container_name: ansible-web1
    hostname: web1
    command: >
      bash -c "apt-get update && apt-get install -y openssh-server &&
      echo 'root:password' | chpasswd &&
      service ssh start && sleep infinity"
    networks:
      ansible_net:
        ipv4_address: 172.20.0.11

networks:
  ansible_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

## 2.4 SSH Key Setup

```bash
# Generate SSH key pair on control node
$ ssh-keygen -t ed25519 -C "ansible-control"

# Copy public key to managed nodes
$ ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.56.11
$ ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.56.12

# Test SSH connection (should not ask for password)
$ ssh user@192.168.56.11 "hostname"
# Output: web1
```

## 2.5 Ansible Configuration File (ansible.cfg)

Ansible looks for config in this order (first found wins):
1. `ANSIBLE_CONFIG` environment variable
2. `./ansible.cfg` (current directory)
3. `~/.ansible.cfg` (home directory)
4. `/etc/ansible/ansible.cfg` (global)

```ini
# ansible.cfg
[defaults]
inventory = ./inventory/hosts.ini
remote_user = ubuntu
host_key_checking = False
private_key_file = ~/.ssh/id_ed25519
forks = 10
retry_files_enabled = False
stdout_callback = yaml
timeout = 30
log_path = ./ansible.log

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

### Verify Configuration

```bash
$ ansible-config dump --only-changed

# Output:
# DEFAULT_HOST_KEY_CHECKING(ansible.cfg) = False
# DEFAULT_REMOTE_USER(ansible.cfg) = ubuntu
# DEFAULT_FORKS(ansible.cfg) = 10
```


---

# MODULE 3: Inventory Management

## 3.1 What is an Inventory?

An inventory defines the managed nodes Ansible will operate on. It can be:
- **Static**: A file (INI or YAML format)
- **Dynamic**: A script or plugin that queries external sources (AWS, Azure, etc.)

## 3.2 Static Inventory (INI Format)

### Basic Inventory

```ini
# inventory/hosts.ini

# Individual hosts (ungrouped)
192.168.56.11
192.168.56.12

# Named hosts with connection details
web1 ansible_host=192.168.56.11 ansible_user=ubuntu
db1  ansible_host=192.168.56.12 ansible_user=ubuntu ansible_port=2222
```

### Grouped Inventory

```ini
# inventory/hosts.ini

[webservers]
web1 ansible_host=192.168.56.11
web2 ansible_host=192.168.56.13
web3 ansible_host=192.168.56.14

[dbservers]
db1 ansible_host=192.168.56.12
db2 ansible_host=192.168.56.15

[loadbalancers]
lb1 ansible_host=192.168.56.16

# Group of groups (children)
[production:children]
webservers
dbservers
loadbalancers

# Variables for all webservers
[webservers:vars]
http_port=80
max_clients=200
ansible_user=ubuntu

# Variables for all dbservers
[dbservers:vars]
db_port=5432
ansible_user=postgres

# Variables for ALL hosts
[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

### Range Patterns

```ini
[webservers]
web[01:20] ansible_host=192.168.56.[11:30]

[dbservers]
db-[a:c] ansible_host=10.0.1.[1:3]
```

## 3.3 Static Inventory (YAML Format)

```yaml
# inventory/hosts.yml
all:
  vars:
    ansible_python_interpreter: /usr/bin/python3
  children:
    webservers:
      vars:
        http_port: 80
      hosts:
        web1:
          ansible_host: 192.168.56.11
        web2:
          ansible_host: 192.168.56.13
    dbservers:
      vars:
        db_port: 5432
      hosts:
        db1:
          ansible_host: 192.168.56.12
    production:
      children:
        webservers:
        dbservers:
```

## 3.4 Inventory Commands

```bash
# List all hosts
$ ansible all --list-hosts -i inventory/hosts.ini
# Output:
#   hosts (5):
#     web1
#     web2
#     db1
#     db2
#     lb1

# List hosts in a group
$ ansible webservers --list-hosts -i inventory/hosts.ini
# Output:
#   hosts (2):
#     web1
#     web2

# View inventory as graph
$ ansible-inventory --graph -i inventory/hosts.ini
# Output:
# @all:
#   |--@webservers:
#   |  |--web1
#   |  |--web2
#   |--@dbservers:
#   |  |--db1
#   |  |--db2

# View host variables
$ ansible-inventory --host web1 -i inventory/hosts.ini
# Output:
# {
#     "ansible_host": "192.168.56.11",
#     "http_port": 80,
#     "ansible_user": "ubuntu"
# }
```

## 3.5 Host and Group Variables (File-Based)

For larger projects, store variables in separate files:

```
project/
  ansible.cfg
  inventory/
    hosts.ini
  group_vars/
    all.yml          # Variables for all hosts
    webservers.yml   # Variables for webservers group
    dbservers.yml    # Variables for dbservers group
  host_vars/
    web1.yml         # Variables specific to web1
    db1.yml          # Variables specific to db1
  playbooks/
```

```yaml
# group_vars/all.yml
---
ntp_server: time.google.com
dns_servers:
  - 8.8.8.8
  - 8.8.4.4
```

```yaml
# group_vars/webservers.yml
---
http_port: 80
https_port: 443
document_root: /var/www/html
```

```yaml
# host_vars/web1.yml
---
server_id: 1
is_primary: true
```

### Variable Precedence (Low to High)

```
1.  role defaults (roles/x/defaults/main.yml)
2.  inventory file group vars
3.  inventory group_vars/all
4.  playbook group_vars/all
5.  inventory group_vars/*
6.  playbook group_vars/*
7.  inventory file host vars
8.  inventory host_vars/*
9.  playbook host_vars/*
10. host facts / cached set_facts
11. play vars
12. play vars_prompt
13. play vars_files
14. role vars (roles/x/vars/main.yml)
15. block vars
16. task vars
17. include_vars
18. set_facts / registered vars
19. role params
20. extra vars (-e "key=value")  <-- ALWAYS WINS
```

## 3.6 Inventory Patterns

```bash
# Target all hosts
$ ansible all -m ping

# Target a specific group
$ ansible webservers -m ping

# Target multiple groups (OR - union)
$ ansible 'webservers:dbservers' -m ping

# Target intersection (AND)
$ ansible 'webservers:&production' -m ping

# Target exclusion (NOT)
$ ansible 'all:!dbservers' -m ping

# Target specific host
$ ansible web1 -m ping

# Target with wildcard
$ ansible 'web*' -m ping

# Target with regex
$ ansible '~web[0-9]+' -m ping

# Limit at runtime
$ ansible all -m ping --limit web1
```

## 3.7 Testing Connectivity

```bash
$ ansible all -m ping -i inventory/hosts.ini

# Success output:
# web1 | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }

# Failure (SSH issue):
# web1 | UNREACHABLE! => {
#     "msg": "Failed to connect to the host via ssh: Connection refused",
#     "unreachable": true
# }

# Failure (Python missing):
# web1 | FAILED! => {
#     "module_stderr": "/bin/sh: 1: /usr/bin/python: not found",
#     "msg": "The module failed to execute correctly"
# }
```

**ping module**: Does NOT send ICMP ping. It tests SSH connectivity + Python availability. Returns "pong" if both work.


---

# MODULE 4: Ad-Hoc Commands

## 4.1 What are Ad-Hoc Commands?

Ad-hoc commands are one-liner Ansible commands for quick tasks without a playbook. Useful for quick checks, one-time operations, and testing modules.

### Syntax

```
ansible <host-pattern> -m <module> -a "<arguments>" [options]
```

| Option | Description |
|--------|-------------|
| `-m` | Module to use |
| `-a` | Arguments to pass to the module |
| `-i` | Inventory file path |
| `-b` | Become (sudo) |
| `-u` | Remote user |
| `-k` | Ask for SSH password |
| `-K` | Ask for sudo password |
| `-f` | Number of forks (parallel processes) |
| `-v/-vv/-vvv` | Verbosity level |

## 4.2 Essential Modules with Examples

### ping - Test Connectivity

```bash
$ ansible all -m ping

# Output:
# web1 | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }
```

**Meaning**: Tests SSH + Python on remote hosts. Returns "pong" on success.

### command - Run Commands (Default Module)

```bash
# command is the default module, -m is optional
$ ansible all -a "uptime"

# Output:
# web1 | CHANGED | rc=0 >>
#  14:23:01 up 5 days, 3:42, 1 user, load average: 0.08, 0.03, 0.01

$ ansible all -a "df -h"
$ ansible all -a "free -m"

# This FAILS - command module doesn't support pipes
$ ansible webservers -a "ps aux | grep nginx"
```

**Meaning**: `command` module runs commands directly without a shell. Does NOT support pipes, redirects, or environment variables.

### shell - Run Commands with Shell Features

```bash
# Use shell module for pipes, redirects, env vars
$ ansible webservers -m shell -a "ps aux | grep nginx | wc -l"

# Output:
# web1 | CHANGED | rc=0 >>
# 3

# Redirect output to a file
$ ansible all -m shell -a "df -h > /tmp/disk_report.txt"

# Use environment variables
$ ansible all -m shell -a "echo $HOME"
```

**Meaning**: `shell` module runs commands through `/bin/sh`, supporting all shell features.

### raw - Run Commands Without Python

```bash
# Useful when Python is not installed on managed node
$ ansible newservers -m raw -a "apt-get install -y python3"
```

**Meaning**: Sends raw commands over SSH without requiring Python. Used for bootstrapping.

### copy - Copy Files to Remote Hosts

```bash
$ ansible webservers -m copy -a "src=/home/user/index.html dest=/var/www/html/index.html owner=www-data group=www-data mode=0644" -b

# Output:
# web1 | CHANGED => {
#     "changed": true,
#     "checksum": "a4e7f8c...",
#     "dest": "/var/www/html/index.html",
#     "mode": "0644",
#     "owner": "www-data",
#     "size": 1234
# }

# Copy content directly (no source file needed)
$ ansible webservers -m copy -a "content='Hello World\n' dest=/tmp/hello.txt"
```

**Arguments**: `src` (local path), `dest` (remote path), `owner`, `group`, `mode`, `content` (inline text), `backup=yes` (backup existing).

### fetch - Copy Files FROM Remote Hosts

```bash
$ ansible dbservers -m fetch -a "src=/var/log/postgresql/postgresql.log dest=/tmp/db-logs/ flat=yes"
```

**Meaning**: Opposite of `copy`. Downloads files from managed nodes to control node.

### file - Manage Files and Directories

```bash
# Create a directory
$ ansible all -m file -a "path=/opt/myapp state=directory mode=0755 owner=root" -b

# Create a symbolic link
$ ansible webservers -m file -a "src=/etc/nginx/sites-available/myapp dest=/etc/nginx/sites-enabled/myapp state=link" -b

# Delete a file
$ ansible all -m file -a "path=/tmp/old_file.txt state=absent"

# Change permissions
$ ansible all -m file -a "path=/opt/myapp/script.sh mode=0755"
```

**State values**: `file` (ensure exists), `directory` (create dir), `link` (symlink), `hard` (hard link), `absent` (delete), `touch` (create empty/update timestamp).

### apt / yum - Package Management

```bash
# Install (Debian/Ubuntu)
$ ansible webservers -m apt -a "name=nginx state=present update_cache=yes" -b

# Output:
# web1 | CHANGED => {
#     "changed": true,
#     "stdout": "Setting up nginx (1.18.0) ...\n"
# }

# Install (RHEL/CentOS)
$ ansible webservers -m yum -a "name=httpd state=present" -b

# Install multiple packages
$ ansible webservers -m apt -a "name=nginx,curl,vim state=present" -b

# Remove a package
$ ansible webservers -m apt -a "name=nginx state=absent" -b

# Update all packages
$ ansible all -m apt -a "upgrade=dist update_cache=yes" -b
```

**State values**: `present`/`installed`, `absent`/`removed`, `latest`.

### service / systemd - Manage Services

```bash
# Start a service
$ ansible webservers -m service -a "name=nginx state=started" -b

# Stop
$ ansible webservers -m service -a "name=nginx state=stopped" -b

# Restart
$ ansible webservers -m service -a "name=nginx state=restarted" -b

# Enable at boot
$ ansible webservers -m service -a "name=nginx enabled=yes" -b

# Reload (without restart)
$ ansible webservers -m service -a "name=nginx state=reloaded" -b

# Using systemd module
$ ansible webservers -m systemd -a "name=nginx state=started enabled=yes daemon_reload=yes" -b
```

### user - Manage Users

```bash
# Create a user
$ ansible all -m user -a "name=deploy state=present shell=/bin/bash groups=sudo append=yes" -b

# Output:
# web1 | CHANGED => {
#     "changed": true,
#     "home": "/home/deploy",
#     "name": "deploy",
#     "shell": "/bin/bash",
#     "uid": 1001
# }

# Create user with SSH key
$ ansible all -m user -a "name=deploy generate_ssh_key=yes ssh_key_bits=4096" -b

# Remove a user
$ ansible all -m user -a "name=olduser state=absent remove=yes" -b
```

### cron - Manage Cron Jobs

```bash
# Create a cron job
$ ansible dbservers -m cron -a "name='DB Backup' minute=0 hour=2 job='/opt/scripts/backup.sh'" -b

# Remove a cron job
$ ansible dbservers -m cron -a "name='DB Backup' state=absent" -b

# Special time
$ ansible all -m cron -a "name='Cleanup' special_time=daily job='find /tmp -mtime +7 -delete'" -b
```

**Special time values**: `reboot`, `yearly`, `monthly`, `weekly`, `daily`, `hourly`.

### lineinfile - Manage Lines in Files

```bash
# Add a line
$ ansible all -m lineinfile -a "path=/etc/hosts line='192.168.56.20 app.local'" -b

# Replace a line matching regex
$ ansible all -m lineinfile -a "path=/etc/ssh/sshd_config regexp='^PermitRootLogin' line='PermitRootLogin no'" -b

# Remove a line
$ ansible all -m lineinfile -a "path=/etc/hosts regexp='.*old-server.*' state=absent" -b
```

### setup - Gather System Facts

```bash
# Gather all facts
$ ansible web1 -m setup

# Filter specific facts
$ ansible web1 -m setup -a "filter=ansible_distribution*"
# Output:
# web1 | SUCCESS => {
#     "ansible_facts": {
#         "ansible_distribution": "Ubuntu",
#         "ansible_distribution_version": "22.04",
#         "ansible_distribution_release": "jammy"
#     }
# }

# Filter memory facts
$ ansible web1 -m setup -a "filter=ansible_mem*"
```

## 4.3 Useful Ad-Hoc Patterns

### Fleet Status Checks

```bash
$ ansible all -a "uptime" -f 20
$ ansible all -m shell -a "df -h / | tail -1" -f 20
$ ansible all -m shell -a "free -m | grep Mem" -f 20
$ ansible webservers -m shell -a "systemctl is-active nginx"
```

### Emergency Operations

```bash
# Kill a runaway process
$ ansible all -m shell -a "pkill -f 'runaway_process'" -b

# Emergency patch
$ ansible all -m apt -a "name=openssl state=latest update_cache=yes" -b
```

### Dry Run (Check Mode)

```bash
$ ansible webservers -m apt -a "name=nginx state=present" -b --check
# Shows what WOULD change without actually changing
```


---

# MODULE 5: Playbooks Fundamentals

## 5.1 What is a Playbook?

A playbook is a YAML file containing one or more "plays." Each play maps a group of hosts to a set of tasks.

| Feature | Ad-Hoc | Playbook |
|---------|--------|----------|
| Reusable | No | Yes |
| Version controlled | No | Yes |
| Complex logic | No | Yes (conditionals, loops) |
| Multiple tasks | One at a time | Many in sequence |
| Error handling | Limited | Full (blocks, rescue) |

## 5.2 YAML Basics for Ansible

```yaml
# Key-value pairs
name: John
age: 30

# Lists
fruits:
  - apple
  - banana
  - cherry

# Dictionary
person:
  name: John
  age: 30

# Multi-line string (preserves newlines)
description: |
  Line 1
  Line 2

# Multi-line string (joins lines)
description: >
  This long sentence
  becomes one line.

# Boolean
enabled: true
disabled: false
```

### Common YAML Mistakes

```yaml
# WRONG: Tab indentation (causes errors!)
name:
	value: test

# CORRECT: Space indentation (2 spaces)
name:
  value: test

# WRONG: Missing space after colon
name:value

# CORRECT
name: value

# WRONG: Unquoted special characters
message: This has a : colon

# CORRECT
message: "This has a : colon"
```

## 5.3 First Playbook

```yaml
# playbooks/first_playbook.yml
---
- name: Configure web servers
  hosts: webservers
  become: yes

  tasks:
    - name: Ensure nginx is installed
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Start and enable nginx
      service:
        name: nginx
        state: started
        enabled: yes

    - name: Deploy index page
      copy:
        content: |
          <html>
          <body><h1>Hello from {{ inventory_hostname }}</h1></body>
          </html>
        dest: /var/www/html/index.html
        owner: www-data
        group: www-data
        mode: '0644'
```

### Running the Playbook

```bash
$ ansible-playbook playbooks/first_playbook.yml

# Output:
# PLAY [Configure web servers] ************************************************
#
# TASK [Gathering Facts] *******************************************************
# ok: [web1]
# ok: [web2]
#
# TASK [Ensure nginx is installed] *********************************************
# changed: [web1]
# changed: [web2]
#
# TASK [Start and enable nginx] ************************************************
# changed: [web1]
# changed: [web2]
#
# TASK [Deploy index page] *****************************************************
# changed: [web1]
# changed: [web2]
#
# PLAY RECAP *******************************************************************
# web1  : ok=4  changed=3  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
# web2  : ok=4  changed=3  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

**Output explained:**
- `ok`: Task ran, no changes needed
- `changed`: Task made changes
- `unreachable`: Could not connect
- `failed`: Task failed
- `skipped`: Task skipped (conditional)
- `rescued`: Failed but rescued by rescue block
- `ignored`: Failed but `ignore_errors: yes` was set

### Execution Options

```bash
# Dry run
$ ansible-playbook playbook.yml --check

# Dry run with diff
$ ansible-playbook playbook.yml --check --diff

# Limit to specific hosts
$ ansible-playbook playbook.yml --limit web1

# Start at a specific task
$ ansible-playbook playbook.yml --start-at-task "Deploy index page"

# Step through tasks interactively
$ ansible-playbook playbook.yml --step

# List all tasks
$ ansible-playbook playbook.yml --list-tasks

# Verbose output
$ ansible-playbook playbook.yml -v     # basic
$ ansible-playbook playbook.yml -vvv   # connection debugging

# Pass extra variables
$ ansible-playbook playbook.yml -e "http_port=8080"

# Syntax check
$ ansible-playbook playbook.yml --syntax-check
```

## 5.4 Multi-Play Playbook

```yaml
# playbooks/multi_tier_setup.yml
---
# Play 1: Common setup for all servers
- name: Common configuration
  hosts: all
  become: yes
  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install common packages
      apt:
        name: [vim, curl, wget, htop, net-tools]
        state: present

    - name: Set timezone
      timezone:
        name: UTC

# Play 2: Web servers
- name: Configure web servers
  hosts: webservers
  become: yes
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Start nginx
      service:
        name: nginx
        state: started
        enabled: yes

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted

# Play 3: Database servers
- name: Configure database servers
  hosts: dbservers
  become: yes
  tasks:
    - name: Install PostgreSQL
      apt:
        name: [postgresql, postgresql-contrib, python3-psycopg2]
        state: present

    - name: Start PostgreSQL
      service:
        name: postgresql
        state: started
        enabled: yes

    - name: Create application database
      become_user: postgres
      postgresql_db:
        name: myapp_db
        state: present
```

## 5.5 Tags

Tags let you run specific parts of a playbook.

```yaml
---
- name: Full server setup
  hosts: webservers
  become: yes
  tasks:
    - name: Install packages
      apt:
        name: [nginx, php-fpm]
        state: present
      tags: [install, packages]

    - name: Copy nginx config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      tags: [configure, nginx]

    - name: Deploy application
      copy:
        src: app/
        dest: /var/www/html/
      tags: [deploy]

    - name: Start services
      service:
        name: "{{ item }}"
        state: started
      loop: [nginx, php8.1-fpm]
      tags: [services, always]  # 'always' runs even when filtering
```

```bash
# Run only install tasks
$ ansible-playbook playbook.yml --tags install

# Run multiple tags
$ ansible-playbook playbook.yml --tags "install,configure"

# Skip deploy tasks
$ ansible-playbook playbook.yml --skip-tags deploy

# List all tags
$ ansible-playbook playbook.yml --list-tags
```

## 5.6 Error Handling

### ignore_errors

```yaml
tasks:
  - name: This might fail
    command: /opt/app/check_status.sh
    ignore_errors: yes

  - name: This runs regardless
    debug:
      msg: "Continuing..."
```

### block / rescue / always

```yaml
tasks:
  - name: Deploy with rollback
    block:
      - name: Deploy new version
        copy:
          src: app-v2/
          dest: /var/www/html/

      - name: Run migrations
        command: /opt/app/migrate.sh

    rescue:
      - name: Rollback to previous version
        copy:
          src: app-v1/
          dest: /var/www/html/

      - name: Send failure notification
        mail:
          to: ops@company.com
          subject: "Deployment FAILED on {{ inventory_hostname }}"

    always:
      - name: Ensure app is running
        service:
          name: myapp
          state: started
```

### failed_when / changed_when

```yaml
tasks:
  - name: Run health check
    command: /opt/app/healthcheck.sh
    register: health_result
    failed_when: "'CRITICAL' in health_result.stdout"

  - name: Check version (read-only, never "changed")
    command: cat /opt/app/VERSION
    register: version
    changed_when: false
```

### any_errors_fatal and max_fail_percentage

```yaml
# Stop ALL hosts if ANY host fails
- name: Critical deployment
  hosts: webservers
  any_errors_fatal: true
  tasks:
    - name: Deploy
      copy:
        src: app/
        dest: /var/www/html/

# Stop if more than 30% fail
- name: Rolling update
  hosts: webservers
  max_fail_percentage: 30
  serial: 5
  tasks:
    - name: Update
      apt:
        name: myapp
        state: latest
```

## 5.7 Playbook Keywords Reference

```yaml
---
- name: Play name
  hosts: target_group              # Required
  become: yes                      # Privilege escalation
  become_user: root                # User to become
  gather_facts: yes                # Gather system facts
  connection: ssh                  # Connection type
  serial: 5                        # Process N hosts at a time
  order: sorted                    # Host order
  any_errors_fatal: false          # Stop all on any failure
  environment:                     # Environment variables
    http_proxy: http://proxy:8080
  vars:                            # Play-level variables
    app_port: 8080
  vars_files:                      # Load variables from files
    - vars/common.yml
  pre_tasks: []                    # Tasks before roles
  roles: []                        # Roles to apply
  tasks: []                        # Main tasks
  post_tasks: []                   # Tasks after roles and tasks
  handlers: []                     # Triggered by notify
```


---

# MODULE 6: Variables, Facts, and Registers

## 6.1 Variable Types

| Type | Where Defined | Scope |
|------|--------------|-------|
| Play vars | In playbook `vars:` section | Play |
| vars_files | External YAML files | Play |
| group_vars | `group_vars/` directory | Group |
| host_vars | `host_vars/` directory | Host |
| Extra vars | Command line `-e` | Global (highest priority) |
| Registered vars | `register:` keyword | Task onwards |
| Facts | Gathered from hosts | Host |
| Role defaults | `roles/x/defaults/` | Role (lowest priority) |
| Role vars | `roles/x/vars/` | Role (high priority) |

## 6.2 Defining Variables

### In Playbook (play vars)

```yaml
---
- name: Variable examples
  hosts: webservers
  become: yes

  vars:
    http_port: 80
    app_name: mywebapp
    max_connections: 100
    admin_email: admin@example.com
    packages:
      - nginx
      - php-fpm
      - php-mysql
    database:
      host: db1.example.com
      port: 5432
      name: myapp_db

  tasks:
    - name: Install packages
      apt:
        name: "{{ packages }}"
        state: present

    - name: Show app name
      debug:
        msg: "Deploying {{ app_name }} on port {{ http_port }}"

    - name: Show database host
      debug:
        msg: "DB at {{ database.host }}:{{ database.port }}/{{ database.name }}"
        # Alternative syntax: {{ database['host'] }}
```

**Output:**
```
TASK [Show app name] **********************************************************
ok: [web1] => {
    "msg": "Deploying mywebapp on port 80"
}

TASK [Show database host] *****************************************************
ok: [web1] => {
    "msg": "DB at db1.example.com:5432/myapp_db"
}
```

### From External Files (vars_files)

```yaml
# vars/app_config.yml
---
app_name: mywebapp
app_version: "2.1.0"
app_port: 8080
app_user: www-data
app_dir: /opt/mywebapp

# vars/db_config.yml
---
db_host: db1.example.com
db_port: 5432
db_name: myapp_production
db_user: myapp_user
```

```yaml
# playbook.yml
---
- name: Deploy application
  hosts: webservers
  become: yes
  vars_files:
    - vars/app_config.yml
    - vars/db_config.yml

  tasks:
    - name: Create app directory
      file:
        path: "{{ app_dir }}"
        state: directory
        owner: "{{ app_user }}"

    - name: Show config
      debug:
        msg: "{{ app_name }} v{{ app_version }} -> {{ db_host }}:{{ db_port }}"
```

### From Command Line (Extra Vars)

```bash
# Single variable
$ ansible-playbook playbook.yml -e "app_version=3.0.0"

# Multiple variables
$ ansible-playbook playbook.yml -e "app_version=3.0.0 env=production"

# From JSON
$ ansible-playbook playbook.yml -e '{"app_version": "3.0.0", "env": "production"}'

# From a file
$ ansible-playbook playbook.yml -e "@vars/override.yml"
```

**Extra vars always win** - they override all other variable sources.

### Variable Data Types

```yaml
vars:
  # String
  name: "John Doe"

  # Integer
  port: 8080

  # Float
  version: 2.1

  # Boolean
  debug_mode: true

  # List
  servers:
    - web1
    - web2
    - web3

  # Dictionary
  database:
    host: localhost
    port: 5432

  # Multi-line string
  nginx_config: |
    server {
        listen 80;
        server_name example.com;
    }
```

## 6.3 Facts (System Information)

Facts are variables automatically gathered from managed nodes when a playbook runs.

### Gathering Facts

```yaml
---
- name: Display system facts
  hosts: webservers
  gather_facts: yes  # default is yes

  tasks:
    - name: Show OS information
      debug:
        msg: |
          Hostname: {{ ansible_hostname }}
          OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
          Kernel: {{ ansible_kernel }}
          Architecture: {{ ansible_architecture }}

    - name: Show hardware info
      debug:
        msg: |
          CPUs: {{ ansible_processor_vcpus }}
          RAM: {{ ansible_memtotal_mb }} MB
          Swap: {{ ansible_swaptotal_mb }} MB

    - name: Show network info
      debug:
        msg: |
          IP: {{ ansible_default_ipv4.address }}
          MAC: {{ ansible_default_ipv4.macaddress }}
          Gateway: {{ ansible_default_ipv4.gateway }}
          Interface: {{ ansible_default_ipv4.interface }}

    - name: Show disk info
      debug:
        msg: "Mount {{ item.mount }} - Size: {{ item.size_total }} - Free: {{ item.size_available }}"
      loop: "{{ ansible_mounts }}"
      when: item.mount == "/"
```

**Output:**
```
TASK [Show OS information] ****************************************************
ok: [web1] => {
    "msg": "Hostname: web1\nOS: Ubuntu 22.04\nKernel: 5.15.0-91-generic\nArchitecture: x86_64\n"
}

TASK [Show hardware info] *****************************************************
ok: [web1] => {
    "msg": "CPUs: 2\nRAM: 2048 MB\nSwap: 1024 MB\n"
}
```

### Commonly Used Facts

| Fact | Description | Example Value |
|------|-------------|---------------|
| `ansible_hostname` | Short hostname | `web1` |
| `ansible_fqdn` | Fully qualified domain name | `web1.example.com` |
| `ansible_distribution` | OS distribution | `Ubuntu` |
| `ansible_distribution_version` | OS version | `22.04` |
| `ansible_os_family` | OS family | `Debian` |
| `ansible_kernel` | Kernel version | `5.15.0-91-generic` |
| `ansible_architecture` | CPU architecture | `x86_64` |
| `ansible_processor_vcpus` | Number of CPUs | `2` |
| `ansible_memtotal_mb` | Total RAM in MB | `2048` |
| `ansible_default_ipv4.address` | Primary IP | `192.168.56.11` |
| `ansible_env.HOME` | Home directory | `/root` |
| `ansible_date_time.iso8601` | Current time | `2024-01-15T14:30:00Z` |

### Disabling Fact Gathering (Performance)

```yaml
---
- name: Fast playbook (no fact gathering)
  hosts: webservers
  gather_facts: no  # Saves 2-5 seconds per host

  tasks:
    - name: Quick task
      command: uptime
```

### Custom Facts (Local Facts)

Create custom facts on managed nodes that Ansible can read:

```bash
# On managed node, create /etc/ansible/facts.d/custom.fact
$ sudo mkdir -p /etc/ansible/facts.d
$ sudo cat > /etc/ansible/facts.d/custom.fact << 'EOF'
[application]
name=mywebapp
version=2.1.0
environment=production

[monitoring]
enabled=true
endpoint=http://monitor.example.com
EOF
```

```yaml
# Access custom facts in playbook
- name: Show custom facts
  debug:
    msg: |
      App: {{ ansible_local.custom.application.name }}
      Version: {{ ansible_local.custom.application.version }}
      Monitoring: {{ ansible_local.custom.monitoring.enabled }}
```

### set_fact - Create Facts Dynamically

```yaml
tasks:
  - name: Set a fact based on OS
    set_fact:
      package_manager: "{{ 'apt' if ansible_os_family == 'Debian' else 'yum' }}"

  - name: Use the dynamic fact
    debug:
      msg: "Using {{ package_manager }} on {{ ansible_distribution }}"

  - name: Calculate memory threshold
    set_fact:
      memory_threshold_mb: "{{ (ansible_memtotal_mb * 0.8) | int }}"

  - name: Show threshold
    debug:
      msg: "Alert if memory exceeds {{ memory_threshold_mb }} MB"
```

## 6.4 Registered Variables

Capture the output of a task for use in subsequent tasks.

```yaml
---
- name: Register variable examples
  hosts: webservers

  tasks:
    - name: Check disk space
      command: df -h /
      register: disk_result

    - name: Show full registered variable
      debug:
        var: disk_result

    # Output:
    # disk_result:
    #   changed: true
    #   cmd: ["df", "-h", "/"]
    #   rc: 0
    #   stdout: "Filesystem  Size  Used Avail Use% Mounted on\n/dev/sda1  20G  8.5G  11G  44% /"
    #   stdout_lines:
    #     - "Filesystem  Size  Used Avail Use% Mounted on"
    #     - "/dev/sda1  20G  8.5G  11G  44% /"
    #   stderr: ""
    #   stderr_lines: []

    - name: Show just stdout
      debug:
        msg: "{{ disk_result.stdout }}"

    - name: Show stdout as list of lines
      debug:
        msg: "{{ disk_result.stdout_lines }}"

    - name: Show return code
      debug:
        msg: "Return code: {{ disk_result.rc }}"

    - name: Check if nginx is installed
      command: which nginx
      register: nginx_check
      ignore_errors: yes

    - name: Install nginx if not found
      apt:
        name: nginx
        state: present
      when: nginx_check.rc != 0
      become: yes

    - name: Get list of running services
      shell: systemctl list-units --type=service --state=running --no-pager | grep running
      register: running_services

    - name: Check if nginx is running
      debug:
        msg: "Nginx is {{ 'running' if 'nginx' in running_services.stdout else 'not running' }}"
```

### Registered Variable Properties

| Property | Description |
|----------|-------------|
| `.stdout` | Standard output as string |
| `.stdout_lines` | Standard output as list of lines |
| `.stderr` | Standard error as string |
| `.stderr_lines` | Standard error as list of lines |
| `.rc` | Return code (0 = success) |
| `.changed` | Whether the task made changes |
| `.failed` | Whether the task failed |
| `.skipped` | Whether the task was skipped |
| `.results` | List of results (when using loops) |

## 6.5 Variable Filters

Ansible uses Jinja2 filters to transform variables.

```yaml
tasks:
  # String filters
  - debug:
      msg: "{{ 'hello world' | upper }}"          # HELLO WORLD
  - debug:
      msg: "{{ 'HELLO WORLD' | lower }}"           # hello world
  - debug:
      msg: "{{ 'hello world' | title }}"           # Hello World
  - debug:
      msg: "{{ '  hello  ' | trim }}"              # hello
  - debug:
      msg: "{{ 'hello' | replace('l', 'L') }}"     # heLLo
  - debug:
      msg: "{{ 'hello world' | length }}"           # 11

  # Default values
  - debug:
      msg: "{{ undefined_var | default('fallback') }}"  # fallback

  # List filters
  - debug:
      msg: "{{ [3, 1, 4, 1, 5] | sort }}"          # [1, 1, 3, 4, 5]
  - debug:
      msg: "{{ [3, 1, 4, 1, 5] | unique }}"         # [3, 1, 4, 5]
  - debug:
      msg: "{{ [1, 2, 3] | join(', ') }}"           # 1, 2, 3
  - debug:
      msg: "{{ [1, 2, 3] | first }}"                # 1
  - debug:
      msg: "{{ [1, 2, 3] | last }}"                 # 3
  - debug:
      msg: "{{ [1, 2, 3] | min }}"                  # 1
  - debug:
      msg: "{{ [1, 2, 3] | max }}"                  # 3
  - debug:
      msg: "{{ [1, 2, 3, 4, 5] | random }}"         # random element

  # Math filters
  - debug:
      msg: "{{ 3.7 | int }}"                        # 3
  - debug:
      msg: "{{ '42' | int }}"                       # 42
  - debug:
      msg: "{{ 3.14159 | round(2) }}"               # 3.14

  # Path filters
  - debug:
      msg: "{{ '/etc/nginx/nginx.conf' | basename }}"    # nginx.conf
  - debug:
      msg: "{{ '/etc/nginx/nginx.conf' | dirname }}"     # /etc/nginx
  - debug:
      msg: "{{ '~/projects' | expanduser }}"              # /home/user/projects

  # Hash/Crypto filters
  - debug:
      msg: "{{ 'password123' | hash('sha256') }}"
  - debug:
      msg: "{{ 'password123' | password_hash('sha512') }}"

  # Type conversion
  - debug:
      msg: "{{ some_list | to_json }}"
  - debug:
      msg: "{{ some_dict | to_yaml }}"
  - debug:
      msg: "{{ json_string | from_json }}"

  # Regex
  - debug:
      msg: "{{ 'Hello 123 World' | regex_search('[0-9]+') }}"  # 123
  - debug:
      msg: "{{ 'Hello World' | regex_replace('World', 'Ansible') }}"  # Hello Ansible
```

## 6.6 Lookups

Lookups read data from external sources.

```yaml
tasks:
  # Read a file
  - name: Read SSH public key
    debug:
      msg: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"

  # Read environment variable
  - name: Get HOME
    debug:
      msg: "{{ lookup('env', 'HOME') }}"

  # Read from CSV
  - name: Read CSV data
    debug:
      msg: "{{ lookup('csvfile', 'web1 file=servers.csv delimiter=, col=1') }}"

  # Generate password
  - name: Generate random password
    debug:
      msg: "{{ lookup('password', '/dev/null length=16 chars=ascii_letters,digits') }}"

  # Read from pipe (command output)
  - name: Get current date
    debug:
      msg: "{{ lookup('pipe', 'date +%Y-%m-%d') }}"

  # Read lines from a file
  - name: Read hosts file
    debug:
      msg: "{{ lookup('lines', 'cat /etc/hostname') }}"

  # URL lookup
  - name: Fetch URL content
    debug:
      msg: "{{ lookup('url', 'https://api.example.com/config') }}"
```

## 6.7 Prompting for Variables

```yaml
---
- name: Interactive playbook
  hosts: webservers
  vars_prompt:
    - name: username
      prompt: "Enter the username"
      private: no  # Show input (default: no for passwords)

    - name: password
      prompt: "Enter the password"
      private: yes  # Hide input
      encrypt: sha512_crypt  # Hash the password
      confirm: yes  # Ask twice for confirmation

    - name: environment
      prompt: "Which environment? (dev/staging/prod)"
      default: "dev"
      private: no

  tasks:
    - name: Create user
      user:
        name: "{{ username }}"
        password: "{{ password }}"
        state: present
      become: yes

    - name: Show environment
      debug:
        msg: "Deploying to {{ environment }}"
```

## 6.8 Real-World Example: Dynamic Configuration

```yaml
---
- name: Configure application based on environment
  hosts: webservers
  become: yes

  vars:
    environments:
      dev:
        debug: true
        replicas: 1
        db_host: dev-db.internal
        log_level: DEBUG
      staging:
        debug: true
        replicas: 2
        db_host: staging-db.internal
        log_level: INFO
      production:
        debug: false
        replicas: 5
        db_host: prod-db.internal
        log_level: WARNING

  tasks:
    - name: Set environment config
      set_fact:
        env_config: "{{ environments[target_env | default('dev')] }}"

    - name: Deploy configuration
      template:
        src: app.conf.j2
        dest: /opt/app/config.yml
      vars:
        debug_mode: "{{ env_config.debug }}"
        db_host: "{{ env_config.db_host }}"
        log_level: "{{ env_config.log_level }}"

    - name: Show active config
      debug:
        msg: "Environment: {{ target_env | default('dev') }}, DB: {{ env_config.db_host }}, Log: {{ env_config.log_level }}"
```

```bash
# Run for production
$ ansible-playbook playbook.yml -e "target_env=production"

# Output:
# TASK [Show active config] ****************************************************
# ok: [web1] => {
#     "msg": "Environment: production, DB: prod-db.internal, Log: WARNING"
# }
```


---

# MODULE 7: Conditionals, Loops, and Handlers

## 7.1 Conditionals (when)

The `when` keyword controls whether a task runs based on a condition.

### Basic Conditionals

```yaml
---
- name: Conditional examples
  hosts: all
  become: yes

  tasks:
    # String comparison
    - name: Install on Ubuntu only
      apt:
        name: nginx
        state: present
      when: ansible_distribution == "Ubuntu"

    # Numeric comparison
    - name: Alert if low memory
      debug:
        msg: "WARNING: Only {{ ansible_memtotal_mb }} MB RAM!"
      when: ansible_memtotal_mb < 1024

    # Boolean check
    - name: Run only if enabled
      debug:
        msg: "Feature is enabled"
      when: enable_feature | default(false)

    # Check if variable is defined
    - name: Run only if variable exists
      debug:
        msg: "Custom port: {{ custom_port }}"
      when: custom_port is defined

    # Check if variable is NOT defined
    - name: Set default port
      set_fact:
        custom_port: 8080
      when: custom_port is not defined

    # Check if string contains substring
    - name: Check if web server
      debug:
        msg: "This is a web server"
      when: "'web' in inventory_hostname"

    # Check if item is in list
    - name: Install only on specific hosts
      apt:
        name: special-package
        state: present
      when: inventory_hostname in ['web1', 'web2']
```

### Multiple Conditions

```yaml
tasks:
  # AND (all conditions must be true)
  - name: Install on Ubuntu 22.04 only
    apt:
      name: nginx
      state: present
    when:
      - ansible_distribution == "Ubuntu"
      - ansible_distribution_version == "22.04"
    # Both conditions must be true (implicit AND)

  # OR
  - name: Install on Debian or Ubuntu
    apt:
      name: nginx
      state: present
    when: ansible_distribution == "Ubuntu" or ansible_distribution == "Debian"

  # Complex condition
  - name: Complex check
    debug:
      msg: "Production web server with enough RAM"
    when:
      - "'web' in group_names"
      - "env == 'production'"
      - ansible_memtotal_mb >= 2048
```

### Conditionals with Registered Variables

```yaml
tasks:
  - name: Check if nginx is installed
    command: which nginx
    register: nginx_check
    ignore_errors: yes
    changed_when: false

  - name: Install nginx if not found
    apt:
      name: nginx
      state: present
    when: nginx_check.rc != 0

  - name: Show nginx version if installed
    command: nginx -v
    when: nginx_check.rc == 0
    register: nginx_version

  - name: Check service status
    command: systemctl is-active nginx
    register: nginx_status
    ignore_errors: yes
    changed_when: false

  - name: Start nginx if not running
    service:
      name: nginx
      state: started
    when: nginx_status.stdout != "active"
```

### Conditionals with OS Family

```yaml
tasks:
  - name: Install on Debian-based systems
    apt:
      name: "{{ item }}"
      state: present
    loop:
      - nginx
      - curl
    when: ansible_os_family == "Debian"

  - name: Install on RedHat-based systems
    yum:
      name: "{{ item }}"
      state: present
    loop:
      - httpd
      - curl
    when: ansible_os_family == "RedHat"
```

## 7.2 Loops

### loop (Recommended - replaces with_items)

```yaml
tasks:
  # Simple list loop
  - name: Install multiple packages
    apt:
      name: "{{ item }}"
      state: present
    loop:
      - nginx
      - php-fpm
      - php-mysql
      - redis-server

  # Output:
  # TASK [Install multiple packages] *********************************************
  # changed: [web1] => (item=nginx)
  # changed: [web1] => (item=php-fpm)
  # changed: [web1] => (item=php-mysql)
  # changed: [web1] => (item=redis-server)

  # Better: pass list directly to apt (faster, single transaction)
  - name: Install multiple packages (optimized)
    apt:
      name:
        - nginx
        - php-fpm
        - php-mysql
        - redis-server
      state: present
```

### Loop with Dictionaries

```yaml
tasks:
  - name: Create multiple users
    user:
      name: "{{ item.name }}"
      groups: "{{ item.groups }}"
      shell: "{{ item.shell | default('/bin/bash') }}"
      state: present
    loop:
      - { name: 'alice', groups: 'developers' }
      - { name: 'bob', groups: 'developers,sudo' }
      - { name: 'charlie', groups: 'ops,sudo', shell: '/bin/zsh' }
    become: yes

  # Output:
  # changed: [web1] => (item={'name': 'alice', 'groups': 'developers'})
  # changed: [web1] => (item={'name': 'bob', 'groups': 'developers,sudo'})
  # changed: [web1] => (item={'name': 'charlie', 'groups': 'ops,sudo', 'shell': '/bin/zsh'})
```

### Loop with Index (loop_control)

```yaml
tasks:
  - name: Create numbered config files
    copy:
      content: "Server {{ ansible_loop.index }} of {{ ansible_loop.length }}"
      dest: "/tmp/server_{{ ansible_loop.index }}.conf"
    loop:
      - web1
      - web2
      - web3
    loop_control:
      extended: yes  # Enable ansible_loop variable

  # ansible_loop.index    = 1-based index (1, 2, 3)
  # ansible_loop.index0   = 0-based index (0, 1, 2)
  # ansible_loop.first    = true if first iteration
  # ansible_loop.last     = true if last iteration
  # ansible_loop.length   = total number of items
```

### Loop with Custom Label

```yaml
tasks:
  - name: Create users (clean output)
    user:
      name: "{{ item.name }}"
      groups: "{{ item.groups }}"
    loop:
      - { name: 'alice', groups: 'dev', uid: 1001, comment: 'Alice Smith' }
      - { name: 'bob', groups: 'ops', uid: 1002, comment: 'Bob Jones' }
    loop_control:
      label: "{{ item.name }}"  # Show only name instead of full dict

  # Output (cleaner):
  # changed: [web1] => (item=alice)
  # changed: [web1] => (item=bob)
  # Instead of showing the entire dictionary
```

### Loop with Conditionals

```yaml
tasks:
  - name: Install packages only if needed
    apt:
      name: "{{ item.name }}"
      state: present
    loop:
      - { name: 'nginx', install: true }
      - { name: 'apache2', install: false }
      - { name: 'php-fpm', install: true }
    when: item.install
    become: yes

  # Output:
  # changed: [web1] => (item={'name': 'nginx', 'install': True})
  # skipping: [web1] => (item={'name': 'apache2', 'install': False})
  # changed: [web1] => (item={'name': 'php-fpm', 'install': True})
```

### Loop with dict2items

```yaml
vars:
  users:
    alice:
      groups: developers
      shell: /bin/bash
    bob:
      groups: ops
      shell: /bin/zsh

tasks:
  - name: Create users from dictionary
    user:
      name: "{{ item.key }}"
      groups: "{{ item.value.groups }}"
      shell: "{{ item.value.shell }}"
    loop: "{{ users | dict2items }}"
    become: yes
```

### Loop with Registered Variables

```yaml
tasks:
  - name: Check multiple services
    command: "systemctl is-active {{ item }}"
    loop:
      - nginx
      - postgresql
      - redis
    register: service_status
    ignore_errors: yes
    changed_when: false

  - name: Show service status
    debug:
      msg: "{{ item.item }}: {{ item.stdout }}"
    loop: "{{ service_status.results }}"

  # Output:
  # ok: [web1] => (item={'item': 'nginx', 'stdout': 'active', ...})
  # ok: [web1] => (item={'item': 'postgresql', 'stdout': 'inactive', ...})
  # ok: [web1] => (item={'item': 'redis', 'stdout': 'active', ...})

  - name: Start inactive services
    service:
      name: "{{ item.item }}"
      state: started
    loop: "{{ service_status.results }}"
    when: item.stdout != "active"
    become: yes
```

### Nested Loops (with_nested equivalent)

```yaml
tasks:
  - name: Create directories for each user
    file:
      path: "/home/{{ item.0 }}/{{ item.1 }}"
      state: directory
      owner: "{{ item.0 }}"
    loop: "{{ ['alice', 'bob'] | product(['documents', 'downloads', 'projects']) | list }}"
    become: yes

  # Creates:
  # /home/alice/documents, /home/alice/downloads, /home/alice/projects
  # /home/bob/documents, /home/bob/downloads, /home/bob/projects
```

### until (Retry Loop)

```yaml
tasks:
  - name: Wait for application to start
    uri:
      url: "http://localhost:8080/health"
      status_code: 200
    register: health_check
    until: health_check.status == 200
    retries: 30        # Try 30 times
    delay: 10          # Wait 10 seconds between retries

  # Ansible will try every 10 seconds, up to 30 times (5 minutes total)
  # Output:
  # TASK [Wait for application to start] ****************************************
  # FAILED - RETRYING: Wait for application to start (30 retries left)
  # FAILED - RETRYING: Wait for application to start (29 retries left)
  # ok: [web1]
```

## 7.3 Handlers

Handlers are tasks that run only when notified by another task. They run once at the end of the play, regardless of how many times they're notified.

### Basic Handler

```yaml
---
- name: Configure nginx
  hosts: webservers
  become: yes

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Copy nginx config
      copy:
        src: files/nginx.conf
        dest: /etc/nginx/nginx.conf
      notify: Restart nginx
      # Only notifies if the task actually changes something

    - name: Copy site config
      copy:
        src: files/mysite.conf
        dest: /etc/nginx/sites-available/mysite
      notify:
        - Restart nginx
        - Reload firewall

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted

    - name: Reload firewall
      command: ufw reload
```

**Key behaviors:**
- Handlers run only if the notifying task reports `changed`
- Handlers run once at the end of the play, even if notified multiple times
- Handlers run in the order they are defined, not the order they are notified

### Force Handler Execution

```yaml
tasks:
  - name: Copy config
    copy:
      src: nginx.conf
      dest: /etc/nginx/nginx.conf
    notify: Restart nginx

  - name: Force handlers to run now (before continuing)
    meta: flush_handlers

  - name: Verify nginx is running with new config
    uri:
      url: http://localhost
      status_code: 200
```

### Handler Listening

```yaml
tasks:
  - name: Update nginx config
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: "web server changed"

  - name: Update app config
    template:
      src: app.conf.j2
      dest: /opt/app/config.yml
    notify: "app config changed"

handlers:
  - name: Restart nginx
    service:
      name: nginx
      state: restarted
    listen: "web server changed"

  - name: Clear nginx cache
    file:
      path: /var/cache/nginx
      state: absent
    listen: "web server changed"

  - name: Restart application
    service:
      name: myapp
      state: restarted
    listen: "app config changed"
```

**Meaning**: Multiple handlers can listen to the same notification topic. When "web server changed" is notified, both "Restart nginx" and "Clear nginx cache" run.

## 7.4 Real-World Example: Complete Web Server Setup

```yaml
---
- name: Production web server setup
  hosts: webservers
  become: yes

  vars:
    nginx_worker_processes: "{{ ansible_processor_vcpus }}"
    app_servers:
      - { name: 'app1', port: 8001 }
      - { name: 'app2', port: 8002 }
      - { name: 'app3', port: 8003 }

  tasks:
    - name: Install packages based on OS
      apt:
        name:
          - nginx
          - certbot
          - python3-certbot-nginx
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"

    - name: Create app directories
      file:
        path: "/opt/{{ item.name }}"
        state: directory
        owner: www-data
        mode: '0755'
      loop: "{{ app_servers }}"
      loop_control:
        label: "{{ item.name }}"

    - name: Deploy app configs
      template:
        src: app.conf.j2
        dest: "/opt/{{ item.name }}/config.yml"
      loop: "{{ app_servers }}"
      loop_control:
        label: "{{ item.name }}"
      notify: Restart apps
      when: item.port is defined

    - name: Configure nginx
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: Reload nginx

    - name: Ensure nginx is running
      service:
        name: nginx
        state: started
        enabled: yes

    - name: Wait for nginx to respond
      uri:
        url: "http://localhost"
        status_code: 200
      register: nginx_health
      until: nginx_health.status == 200
      retries: 5
      delay: 3

  handlers:
    - name: Reload nginx
      service:
        name: nginx
        state: reloaded

    - name: Restart apps
      service:
        name: "{{ item.name }}"
        state: restarted
      loop: "{{ app_servers }}"
      loop_control:
        label: "{{ item.name }}"
```


---

# MODULE 8: Roles and Ansible Galaxy

## 8.1 What are Roles?

Roles are a way to organize playbooks into reusable, shareable components. Instead of one massive playbook, you break it into roles like `webserver`, `database`, `monitoring`.

### Why Use Roles?

| Without Roles | With Roles |
|--------------|------------|
| Single large playbook | Modular, organized structure |
| Copy-paste between projects | Reuse across projects |
| Hard to test individually | Test each role independently |
| Difficult to share | Share via Ansible Galaxy |

## 8.2 Role Directory Structure

```
roles/
  webserver/
    tasks/
      main.yml          # Main task list (auto-loaded)
    handlers/
      main.yml          # Handlers (auto-loaded)
    templates/
      nginx.conf.j2     # Jinja2 templates
    files/
      index.html        # Static files
    vars/
      main.yml          # Role variables (high priority)
    defaults/
      main.yml          # Default variables (lowest priority, easily overridden)
    meta/
      main.yml          # Role metadata and dependencies
    tests/
      test.yml          # Test playbook
      inventory         # Test inventory
    README.md           # Documentation
```

**Auto-loading**: Ansible automatically loads `main.yml` from `tasks/`, `handlers/`, `vars/`, `defaults/`, and `meta/` directories.

## 8.3 Creating a Role

### Method 1: ansible-galaxy init

```bash
$ ansible-galaxy init roles/webserver

# Output:
# - Role roles/webserver was created successfully

$ tree roles/webserver/
# roles/webserver/
# ├── README.md
# ├── defaults
# │   └── main.yml
# ├── files
# ├── handlers
# │   └── main.yml
# ├── meta
# │   └── main.yml
# ├── tasks
# │   └── main.yml
# ├── templates
# ├── tests
# │   ├── inventory
# │   └── test.yml
# └── vars
#     └── main.yml
```

### Method 2: Create Manually

```bash
$ mkdir -p roles/webserver/{tasks,handlers,templates,files,vars,defaults,meta}
```

## 8.4 Building a Complete Role: webserver

### defaults/main.yml (Default Variables)

```yaml
# roles/webserver/defaults/main.yml
---
# These can be easily overridden by the user
nginx_port: 80
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_server_name: "_"
nginx_root: /var/www/html
nginx_index: index.html
nginx_access_log: /var/log/nginx/access.log
nginx_error_log: /var/log/nginx/error.log
nginx_packages:
  - nginx
  - curl
```

### vars/main.yml (Role Variables - Higher Priority)

```yaml
# roles/webserver/vars/main.yml
---
# These are harder to override (use for internal role logic)
nginx_config_path: /etc/nginx
nginx_sites_available: /etc/nginx/sites-available
nginx_sites_enabled: /etc/nginx/sites-enabled
nginx_service_name: nginx
nginx_user: www-data
```

### tasks/main.yml (Main Tasks)

```yaml
# roles/webserver/tasks/main.yml
---
- name: Include OS-specific variables
  include_vars: "{{ ansible_os_family }}.yml"
  ignore_errors: yes

- name: Install nginx packages
  apt:
    name: "{{ nginx_packages }}"
    state: present
    update_cache: yes
  when: ansible_os_family == "Debian"

- name: Install nginx packages (RedHat)
  yum:
    name: "{{ nginx_packages }}"
    state: present
  when: ansible_os_family == "RedHat"

- name: Create document root
  file:
    path: "{{ nginx_root }}"
    state: directory
    owner: "{{ nginx_user }}"
    group: "{{ nginx_user }}"
    mode: '0755'

- name: Deploy nginx configuration
  template:
    src: nginx.conf.j2
    dest: "{{ nginx_config_path }}/nginx.conf"
    owner: root
    group: root
    mode: '0644'
    validate: "nginx -t -c %s"
  notify: Restart nginx

- name: Deploy default site
  template:
    src: default_site.conf.j2
    dest: "{{ nginx_sites_available }}/default"
  notify: Reload nginx

- name: Enable default site
  file:
    src: "{{ nginx_sites_available }}/default"
    dest: "{{ nginx_sites_enabled }}/default"
    state: link
  notify: Reload nginx

- name: Deploy index page
  copy:
    src: index.html
    dest: "{{ nginx_root }}/index.html"
    owner: "{{ nginx_user }}"
    mode: '0644'

- name: Start and enable nginx
  service:
    name: "{{ nginx_service_name }}"
    state: started
    enabled: yes
```

### handlers/main.yml

```yaml
# roles/webserver/handlers/main.yml
---
- name: Restart nginx
  service:
    name: "{{ nginx_service_name }}"
    state: restarted

- name: Reload nginx
  service:
    name: "{{ nginx_service_name }}"
    state: reloaded
```

### templates/nginx.conf.j2

```jinja2
# roles/webserver/templates/nginx.conf.j2
# Managed by Ansible - DO NOT EDIT MANUALLY
user {{ nginx_user }};
worker_processes {{ nginx_worker_processes }};
pid /run/nginx.pid;

events {
    worker_connections {{ nginx_worker_connections }};
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    access_log {{ nginx_access_log }};
    error_log {{ nginx_error_log }};

    gzip on;

    include {{ nginx_sites_enabled }}/*;
}
```

### templates/default_site.conf.j2

```jinja2
# roles/webserver/templates/default_site.conf.j2
server {
    listen {{ nginx_port }};
    server_name {{ nginx_server_name }};
    root {{ nginx_root }};
    index {{ nginx_index }};

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### files/index.html

```html
<!-- roles/webserver/files/index.html -->
<!DOCTYPE html>
<html>
<head><title>Welcome</title></head>
<body>
<h1>Server is running</h1>
<p>Configured by Ansible</p>
</body>
</html>
```

### meta/main.yml (Metadata and Dependencies)

```yaml
# roles/webserver/meta/main.yml
---
galaxy_info:
  author: Your Name
  description: Installs and configures Nginx web server
  license: MIT
  min_ansible_version: "2.14"
  platforms:
    - name: Ubuntu
      versions:
        - jammy
        - focal
    - name: EL
      versions:
        - "8"
        - "9"
  galaxy_tags:
    - nginx
    - web
    - webserver

dependencies:
  - role: common
  # - role: firewall
  #   vars:
  #     firewall_allowed_ports:
  #       - 80
  #       - 443
```

## 8.5 Using Roles in Playbooks

### Basic Usage

```yaml
# site.yml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  roles:
    - webserver
```

### With Variable Overrides

```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  roles:
    - role: webserver
      vars:
        nginx_port: 8080
        nginx_worker_processes: 4
        nginx_server_name: "app.example.com"
```

### Multiple Roles

```yaml
---
- name: Full server setup
  hosts: webservers
  become: yes
  roles:
    - common          # Runs first
    - security        # Runs second
    - webserver       # Runs third
    - monitoring      # Runs fourth
```

### Roles with pre_tasks and post_tasks

```yaml
---
- name: Deploy application
  hosts: webservers
  become: yes

  pre_tasks:
    - name: Disable monitoring alerts
      uri:
        url: "http://monitor.example.com/api/silence"
        method: POST

  roles:
    - webserver
    - application

  post_tasks:
    - name: Re-enable monitoring
      uri:
        url: "http://monitor.example.com/api/unsilence"
        method: POST

    - name: Verify deployment
      uri:
        url: "http://{{ inventory_hostname }}"
        status_code: 200
```

### include_role and import_role

```yaml
tasks:
  # import_role: Static, processed at playbook parse time
  - name: Apply webserver role
    import_role:
      name: webserver
    vars:
      nginx_port: 8080

  # include_role: Dynamic, processed at runtime
  - name: Conditionally apply monitoring
    include_role:
      name: monitoring
    when: enable_monitoring | default(true)

  # include_role with loop
  - name: Apply role for each app
    include_role:
      name: app_deploy
    vars:
      app_name: "{{ item.name }}"
      app_port: "{{ item.port }}"
    loop:
      - { name: 'api', port: 8001 }
      - { name: 'web', port: 8002 }
```

**import_role vs include_role:**

| Feature | import_role | include_role |
|---------|------------|--------------|
| Processing | Parse time (static) | Runtime (dynamic) |
| Conditionals | Applied to each task | Applied to include itself |
| Loops | Not supported | Supported |
| Tags | Inherited by tasks | Not inherited |
| Performance | Faster | Slightly slower |

## 8.6 Ansible Galaxy

Ansible Galaxy is a hub for sharing roles and collections.

### Searching for Roles

```bash
# Search on command line
$ ansible-galaxy search nginx

# Output:
# Found 500 roles matching your search:
#  Name                          Description
#  ----                          -----------
#  geerlingguy.nginx             Nginx installation for Linux
#  jdauphant.nginx               Ansible role to install and manage nginx
#  ...

# Get role info
$ ansible-galaxy info geerlingguy.nginx

# Output:
# Role: geerlingguy.nginx
#     description: Nginx installation for Linux
#     active: True
#     commit: ...
#     company: Midwestern Mac, LLC
#     download_count: 15000000
#     ...
```

### Installing Roles

```bash
# Install a role from Galaxy
$ ansible-galaxy install geerlingguy.nginx

# Output:
# - downloading role 'nginx', owned by geerlingguy
# - downloading role from https://github.com/geerlingguy/ansible-role-nginx/...
# - extracting geerlingguy.nginx to /home/user/.ansible/roles/geerlingguy.nginx
# - geerlingguy.nginx was installed successfully

# Install to custom path
$ ansible-galaxy install geerlingguy.nginx -p ./roles/

# Install specific version
$ ansible-galaxy install geerlingguy.nginx,3.1.0

# Install from GitHub
$ ansible-galaxy install git+https://github.com/user/role.git

# Install from requirements file
$ ansible-galaxy install -r requirements.yml
```

### Requirements File

```yaml
# requirements.yml
---
roles:
  - name: geerlingguy.nginx
    version: "3.1.0"

  - name: geerlingguy.postgresql
    version: "3.4.0"

  - name: geerlingguy.docker
    version: "6.1.0"

  - name: custom_role
    src: git+https://github.com/company/ansible-role-custom.git
    version: main

collections:
  - name: community.general
    version: "8.0.0"

  - name: amazon.aws
    version: "7.0.0"
```

```bash
# Install all roles and collections from requirements
$ ansible-galaxy install -r requirements.yml

# Force reinstall
$ ansible-galaxy install -r requirements.yml --force
```

### Listing and Removing Roles

```bash
# List installed roles
$ ansible-galaxy list

# Output:
# - geerlingguy.nginx, 3.1.0
# - geerlingguy.postgresql, 3.4.0
# - webserver, (unknown version)

# Remove a role
$ ansible-galaxy remove geerlingguy.nginx
```

### Using Galaxy Roles

```yaml
# site.yml
---
- name: Setup web server with Galaxy roles
  hosts: webservers
  become: yes

  roles:
    - role: geerlingguy.nginx
      vars:
        nginx_vhosts:
          - listen: "80"
            server_name: "example.com"
            root: "/var/www/html"
            index: "index.html"
        nginx_remove_default_vhost: true

    - role: geerlingguy.certbot
      vars:
        certbot_auto_renew: true
        certbot_create_if_missing: true
        certbot_certs:
          - domains:
              - example.com
```

## 8.7 Collections

Collections are a distribution format for Ansible content (roles, modules, plugins).

```bash
# Install a collection
$ ansible-galaxy collection install community.general

# Install from requirements
$ ansible-galaxy collection install -r requirements.yml

# List installed collections
$ ansible-galaxy collection list

# Use modules from collections
# In playbook:
- name: Use community module
  community.general.ufw:
    rule: allow
    port: '80'
    proto: tcp
```

## 8.8 Project Structure Best Practice

```
ansible-project/
  ansible.cfg
  inventory/
    production/
      hosts.ini
      group_vars/
        all.yml
        webservers.yml
        dbservers.yml
      host_vars/
        web1.yml
    staging/
      hosts.ini
      group_vars/
        all.yml
  playbooks/
    site.yml              # Master playbook
    webservers.yml        # Web server playbook
    dbservers.yml         # Database playbook
  roles/
    common/               # Base configuration
    webserver/             # Nginx setup
    database/              # PostgreSQL setup
    monitoring/            # Prometheus/Grafana
    security/              # Hardening
  collections/
    requirements.yml
  group_vars/             # Can also be at project root
  host_vars/
  files/                  # Shared static files
  templates/              # Shared templates
  README.md
```

```yaml
# playbooks/site.yml (Master Playbook)
---
- import_playbook: webservers.yml
- import_playbook: dbservers.yml
```

```bash
# Deploy everything
$ ansible-playbook playbooks/site.yml -i inventory/production/

# Deploy only web servers
$ ansible-playbook playbooks/webservers.yml -i inventory/production/

# Deploy to staging
$ ansible-playbook playbooks/site.yml -i inventory/staging/
```


---

# MODULE 9: Templates (Jinja2) and File Management

## 9.1 What are Templates?

Templates are files with placeholders that Ansible fills in with variable values. They use the Jinja2 templating engine. Template files have the `.j2` extension.

### Template vs Copy

| Feature | copy module | template module |
|---------|------------|-----------------|
| Variable substitution | No | Yes |
| Conditional logic | No | Yes |
| Loops | No | Yes |
| File extension | Any | `.j2` (convention) |
| Use case | Static files | Dynamic configuration |

## 9.2 Jinja2 Basics

```jinja2
{# This is a comment - not included in output #}

{{ variable }}              {# Print a variable #}
{{ variable | filter }}     {# Print with filter applied #}

{% if condition %}          {# Control structure #}
{% endif %}

{% for item in list %}      {# Loop #}
{% endfor %}
```

## 9.3 Template Examples

### Example 1: Nginx Virtual Host

```jinja2
{# templates/vhost.conf.j2 #}
{# Managed by Ansible - DO NOT EDIT MANUALLY #}

{% for vhost in nginx_vhosts %}
server {
    listen {{ vhost.port | default(80) }};
    server_name {{ vhost.server_name }};
    root {{ vhost.root | default('/var/www/html') }};

{% if vhost.ssl | default(false) %}
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/{{ vhost.server_name }}.crt;
    ssl_certificate_key /etc/ssl/private/{{ vhost.server_name }}.key;
{% endif %}

{% if vhost.locations is defined %}
{% for location in vhost.locations %}
    location {{ location.path }} {
{% if location.proxy_pass is defined %}
        proxy_pass {{ location.proxy_pass }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
{% else %}
        try_files $uri $uri/ =404;
{% endif %}
    }
{% endfor %}
{% endif %}

    access_log /var/log/nginx/{{ vhost.server_name }}_access.log;
    error_log /var/log/nginx/{{ vhost.server_name }}_error.log;
}

{% endfor %}
```

```yaml
# playbook.yml
vars:
  nginx_vhosts:
    - server_name: app.example.com
      port: 80
      ssl: true
      root: /var/www/app
      locations:
        - path: /
          proxy_pass: http://127.0.0.1:8080
        - path: /static
    - server_name: api.example.com
      port: 80
      locations:
        - path: /
          proxy_pass: http://127.0.0.1:3000

tasks:
  - name: Deploy vhost config
    template:
      src: vhost.conf.j2
      dest: /etc/nginx/sites-available/apps.conf
      owner: root
      mode: '0644'
      validate: "nginx -t -c %s"
    notify: Reload nginx
```

**Generated output for app.example.com:**
```nginx
server {
    listen 80;
    server_name app.example.com;
    root /var/www/app;

    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/app.example.com.crt;
    ssl_certificate_key /etc/ssl/private/app.example.com.key;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/app.example.com_access.log;
    error_log /var/log/nginx/app.example.com_error.log;
}
```

### Example 2: Application Configuration

```jinja2
{# templates/app.conf.j2 #}
# Application Configuration
# Generated by Ansible on {{ ansible_date_time.iso8601 }}
# Host: {{ ansible_hostname }}

[server]
host = {{ app_host | default('0.0.0.0') }}
port = {{ app_port }}
workers = {{ app_workers | default(ansible_processor_vcpus * 2) }}
debug = {{ app_debug | default(false) | lower }}

[database]
host = {{ db_host }}
port = {{ db_port | default(5432) }}
name = {{ db_name }}
user = {{ db_user }}
password = {{ db_password }}
pool_size = {{ db_pool_size | default(10) }}

[redis]
host = {{ redis_host | default('localhost') }}
port = {{ redis_port | default(6379) }}
db = {{ redis_db | default(0) }}

[logging]
level = {{ log_level | default('INFO') }}
file = /var/log/{{ app_name }}/app.log
max_size = {{ log_max_size | default('100MB') }}
backup_count = {{ log_backup_count | default(5) }}

{% if app_features is defined %}
[features]
{% for feature, enabled in app_features.items() %}
{{ feature }} = {{ enabled | lower }}
{% endfor %}
{% endif %}

{% if app_allowed_hosts is defined %}
[security]
allowed_hosts = {{ app_allowed_hosts | join(', ') }}
{% endif %}
```

### Example 3: Systemd Service File

```jinja2
{# templates/app.service.j2 #}
[Unit]
Description={{ app_name }} Application Service
After=network.target
{% if db_host is defined %}
After=postgresql.service
Requires=postgresql.service
{% endif %}

[Service]
Type=simple
User={{ app_user | default('www-data') }}
Group={{ app_group | default('www-data') }}
WorkingDirectory={{ app_dir }}
ExecStart={{ app_dir }}/venv/bin/python {{ app_dir }}/app.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

{% if app_env_vars is defined %}
{% for key, value in app_env_vars.items() %}
Environment="{{ key }}={{ value }}"
{% endfor %}
{% endif %}

StandardOutput=journal
StandardError=journal
SyslogIdentifier={{ app_name }}

[Install]
WantedBy=multi-user.target
```

## 9.4 Jinja2 Control Structures

### Conditionals

```jinja2
{# Simple if #}
{% if enable_ssl %}
listen 443 ssl;
{% endif %}

{# if/else #}
{% if environment == 'production' %}
debug = false
log_level = WARNING
{% elif environment == 'staging' %}
debug = true
log_level = INFO
{% else %}
debug = true
log_level = DEBUG
{% endif %}

{# Ternary (inline if) #}
debug = {{ 'true' if debug_mode else 'false' }}

{# Check if variable is defined #}
{% if custom_config is defined %}
include {{ custom_config }}
{% endif %}

{# Check if variable is not empty #}
{% if servers | length > 0 %}
upstream backend {
{% for server in servers %}
    server {{ server }};
{% endfor %}
}
{% endif %}
```

### Loops

```jinja2
{# Simple loop #}
{% for server in backend_servers %}
server {{ server.host }}:{{ server.port }};
{% endfor %}

{# Loop with index #}
{% for user in users %}
# User {{ loop.index }}: {{ user.name }}
{{ user.name }}:x:{{ 1000 + loop.index }}:{{ 1000 + loop.index }}::/home/{{ user.name }}:/bin/bash
{% endfor %}

{# Loop variables #}
{# loop.index     - 1-based iteration (1, 2, 3...) #}
{# loop.index0    - 0-based iteration (0, 1, 2...) #}
{# loop.first     - True if first iteration #}
{# loop.last      - True if last iteration #}
{# loop.length    - Total number of items #}

{# Loop with condition #}
{% for host in groups['webservers'] %}
{% if hostvars[host].ansible_host is defined %}
{{ hostvars[host].ansible_host }} {{ host }}
{% endif %}
{% endfor %}

{# Dictionary loop #}
{% for key, value in config_options.items() %}
{{ key }} = {{ value }}
{% endfor %}
```

### Whitespace Control

```jinja2
{# Without whitespace control - produces blank lines #}
{% for item in list %}
{{ item }}
{% endfor %}

{# With whitespace control (- strips whitespace) #}
{% for item in list -%}
{{ item }}
{%- endfor %}

{# Strip leading whitespace #}
{%- if condition %}
value
{%- endif %}
```

## 9.5 Jinja2 Filters in Templates

```jinja2
{# String filters #}
{{ hostname | upper }}                    {# WEB1 #}
{{ hostname | lower }}                    {# web1 #}
{{ hostname | capitalize }}               {# Web1 #}
{{ description | truncate(50) }}          {# First 50 chars... #}
{{ path | basename }}                     {# file.txt from /path/to/file.txt #}
{{ path | dirname }}                      {# /path/to from /path/to/file.txt #}

{# Default values #}
{{ port | default(8080) }}                {# Use 8080 if port is undefined #}
{{ feature | default(true) }}             {# Use true if undefined #}

{# List operations #}
{{ servers | join(', ') }}                {# "web1, web2, web3" #}
{{ servers | length }}                    {# 3 #}
{{ servers | first }}                     {# web1 #}
{{ servers | last }}                      {# web3 #}
{{ servers | sort }}                      {# sorted list #}
{{ servers | unique }}                    {# deduplicated list #}
{{ servers | map('upper') | list }}       {# ["WEB1", "WEB2"] #}

{# Math #}
{{ memory_mb | int }}                     {# Convert to integer #}
{{ (memory_mb * 0.8) | round(0) | int }} {# 80% of memory, rounded #}

{# JSON/YAML output #}
{{ config | to_json }}                    {# JSON string #}
{{ config | to_nice_json }}               {# Pretty JSON #}
{{ config | to_yaml }}                    {# YAML string #}

{# IP address filters #}
{{ '192.168.1.0/24' | ipaddr('network') }}   {# 192.168.1.0 #}
{{ '192.168.1.0/24' | ipaddr('netmask') }}   {# 255.255.255.0 #}

{# Regex #}
{{ version | regex_search('([0-9]+)\.([0-9]+)') }}
{{ text | regex_replace('old', 'new') }}

{# Hash #}
{{ 'password' | hash('sha256') }}
{{ 'password' | password_hash('sha512') }}

{# Ternary #}
{{ 'enabled' if feature_flag else 'disabled' }}
```

## 9.6 Template Module Options

```yaml
tasks:
  - name: Deploy config with template
    template:
      src: app.conf.j2           # Source template (relative to templates/ dir)
      dest: /etc/app/config.conf # Destination on remote host
      owner: root                # File owner
      group: root                # File group
      mode: '0644'               # File permissions
      backup: yes                # Create backup before overwriting
      validate: "nginx -t -c %s" # Validate before deploying (%s = temp file)
      force: yes                 # Overwrite even if dest exists (default: yes)
      lstrip_blocks: yes         # Strip leading whitespace from blocks
      trim_blocks: yes           # Strip newlines after block tags
    notify: Restart service
```

## 9.7 File Management Modules

### copy - Copy Static Files

```yaml
tasks:
  # Copy a single file
  - name: Copy config file
    copy:
      src: files/app.conf       # Relative to role's files/ directory
      dest: /etc/app/app.conf
      owner: root
      mode: '0644'
      backup: yes

  # Copy inline content
  - name: Create file with content
    copy:
      content: |
        # Custom configuration
        setting1 = value1
        setting2 = value2
      dest: /etc/app/custom.conf

  # Copy a directory
  - name: Copy entire directory
    copy:
      src: files/webapp/        # Trailing slash = copy contents
      dest: /var/www/html/
      owner: www-data
      mode: '0755'
```

### synchronize - rsync Wrapper

```yaml
tasks:
  - name: Sync application files
    synchronize:
      src: app/
      dest: /opt/myapp/
      delete: yes               # Delete files in dest not in src
      recursive: yes
      rsync_opts:
        - "--exclude=.git"
        - "--exclude=node_modules"
        - "--exclude=*.pyc"
```

### lineinfile - Manage Single Lines

```yaml
tasks:
  # Add a line
  - name: Add DNS server
    lineinfile:
      path: /etc/resolv.conf
      line: "nameserver 8.8.8.8"
      state: present

  # Replace a line
  - name: Set SSH port
    lineinfile:
      path: /etc/ssh/sshd_config
      regexp: '^#?Port\s+'
      line: "Port 2222"
    notify: Restart sshd

  # Add line after a match
  - name: Add config after section header
    lineinfile:
      path: /etc/app/config.conf
      insertafter: '^\[database\]'
      line: "pool_size = 20"

  # Add line before a match
  - name: Add comment before setting
    lineinfile:
      path: /etc/app/config.conf
      insertbefore: '^max_connections'
      line: "# Maximum database connections"

  # Remove a line
  - name: Remove old DNS
    lineinfile:
      path: /etc/resolv.conf
      regexp: '^nameserver 10\.0\.0\.1'
      state: absent

  # Ensure line in file with backup
  - name: Set kernel parameter
    lineinfile:
      path: /etc/sysctl.conf
      regexp: '^net.ipv4.ip_forward'
      line: "net.ipv4.ip_forward = 1"
      backup: yes
```

### blockinfile - Manage Blocks of Text

```yaml
tasks:
  - name: Add SSH config block
    blockinfile:
      path: /etc/ssh/sshd_config
      marker: "# {mark} ANSIBLE MANAGED BLOCK - Security Settings"
      block: |
        PermitRootLogin no
        PasswordAuthentication no
        MaxAuthTries 3
        ClientAliveInterval 300
        ClientAliveCountMax 2
    notify: Restart sshd

  # Output in file:
  # # BEGIN ANSIBLE MANAGED BLOCK - Security Settings
  # PermitRootLogin no
  # PasswordAuthentication no
  # MaxAuthTries 3
  # ClientAliveInterval 300
  # ClientAliveCountMax 2
  # # END ANSIBLE MANAGED BLOCK - Security Settings

  - name: Add hosts entries
    blockinfile:
      path: /etc/hosts
      marker: "# {mark} ANSIBLE MANAGED - App Servers"
      block: |
        {% for host in groups['webservers'] %}
        {{ hostvars[host].ansible_host }} {{ host }}
        {% endfor %}
```

### stat - Get File Information

```yaml
tasks:
  - name: Check if config exists
    stat:
      path: /etc/app/config.conf
    register: config_file

  - name: Show file info
    debug:
      msg: |
        Exists: {{ config_file.stat.exists }}
        Size: {{ config_file.stat.size | default('N/A') }}
        Owner: {{ config_file.stat.pw_name | default('N/A') }}
        Mode: {{ config_file.stat.mode | default('N/A') }}
        Is Dir: {{ config_file.stat.isdir | default('N/A') }}

  - name: Create config if missing
    template:
      src: config.conf.j2
      dest: /etc/app/config.conf
    when: not config_file.stat.exists

  - name: Check file checksum
    stat:
      path: /opt/app/binary
      checksum_algorithm: sha256
    register: binary_stat

  - name: Download new binary if checksum differs
    get_url:
      url: "https://releases.example.com/app-v2.0"
      dest: /opt/app/binary
      checksum: "sha256:abc123..."
    when: binary_stat.stat.checksum != "abc123..."
```

### archive / unarchive - Compress and Extract

```yaml
tasks:
  # Create an archive on remote host
  - name: Archive log files
    archive:
      path:
        - /var/log/app/*.log
        - /var/log/nginx/*.log
      dest: /tmp/logs_backup.tar.gz
      format: gz

  # Extract an archive
  - name: Extract application
    unarchive:
      src: files/app-v2.0.tar.gz   # Local file
      dest: /opt/app/
      owner: www-data
      mode: '0755'

  # Extract from URL
  - name: Download and extract
    unarchive:
      src: "https://releases.example.com/app-v2.0.tar.gz"
      dest: /opt/app/
      remote_src: yes  # Source is a URL or remote file
```

### find - Search for Files

```yaml
tasks:
  - name: Find old log files
    find:
      paths: /var/log
      patterns: "*.log"
      age: "7d"           # Older than 7 days
      recurse: yes
    register: old_logs

  - name: Delete old log files
    file:
      path: "{{ item.path }}"
      state: absent
    loop: "{{ old_logs.files }}"
    loop_control:
      label: "{{ item.path }}"

  - name: Find large files
    find:
      paths: /var
      size: "100m"         # Larger than 100MB
      recurse: yes
    register: large_files

  - name: Report large files
    debug:
      msg: "{{ item.path }} - {{ (item.size / 1048576) | round(1) }} MB"
    loop: "{{ large_files.files }}"
```


---

# MODULE 10: Vault, Security, and Secrets Management

## 10.1 What is Ansible Vault?

Ansible Vault encrypts sensitive data (passwords, API keys, certificates) so they can be safely stored in version control. It uses AES-256 encryption.

## 10.2 Encrypting Files

### Encrypt an Entire File

```bash
# Create and encrypt a new file
$ ansible-vault create secrets.yml
# Opens editor, enter vault password when prompted

# Encrypt an existing file
$ ansible-vault encrypt vars/db_credentials.yml

# Output:
# New Vault password:
# Confirm New Vault password:
# Encryption successful

# View encrypted file content
$ cat vars/db_credentials.yml
# $ANSIBLE_VAULT;1.1;AES256
# 61626364656667686970...
# (encrypted content)
```

### View Encrypted File

```bash
$ ansible-vault view vars/db_credentials.yml
# Vault password:
# (shows decrypted content)
```

### Edit Encrypted File

```bash
$ ansible-vault edit vars/db_credentials.yml
# Vault password:
# (opens in editor with decrypted content)
```

### Decrypt a File

```bash
$ ansible-vault decrypt vars/db_credentials.yml
# Vault password:
# Decryption successful

# Decrypt to a different file
$ ansible-vault decrypt vars/db_credentials.yml --output=vars/db_credentials_plain.yml
```

### Re-key (Change Password)

```bash
$ ansible-vault rekey vars/db_credentials.yml
# Vault password: (old password)
# New Vault password: (new password)
# Confirm New Vault password:
# Rekey successful
```

## 10.3 Encrypting Strings (Inline Encryption)

Instead of encrypting entire files, encrypt individual values:

```bash
$ ansible-vault encrypt_string 'SuperSecretPassword123' --name 'db_password'

# Output:
# db_password: !vault |
#           $ANSIBLE_VAULT;1.1;AES256
#           61626364656667686970...
# Encryption successful
```

Use the output directly in your YAML files:

```yaml
# vars/credentials.yml
---
db_user: myapp_user
db_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          61626364656667686970716a6b6c6d6e6f707172
          73747576777879303132333435363738393a3b3c
          3d3e3f404142434445464748494a4b4c4d4e4f50

api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          51525354555657585960616263646566676869
          70717273747576777879303132333435363738

# Non-sensitive values remain in plaintext
db_host: db.example.com
db_port: 5432
db_name: myapp_production
```

## 10.4 Using Vault in Playbooks

### Method 1: Password Prompt

```bash
$ ansible-playbook playbook.yml --ask-vault-pass
# Vault password: (enter password)
```

### Method 2: Password File

```bash
# Create a password file
$ echo 'MyVaultPassword123' > ~/.vault_pass
$ chmod 600 ~/.vault_pass

# Use password file
$ ansible-playbook playbook.yml --vault-password-file ~/.vault_pass

# Or set in ansible.cfg
# [defaults]
# vault_password_file = ~/.vault_pass
```

### Method 3: Environment Variable

```bash
$ export ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass
$ ansible-playbook playbook.yml
```

### Method 4: Script (Dynamic Password)

```bash
#!/bin/bash
# ~/.vault_pass_script.sh
# Fetch password from a secrets manager
aws secretsmanager get-secret-value --secret-id ansible-vault --query SecretString --output text
```

```bash
$ chmod +x ~/.vault_pass_script.sh
$ ansible-playbook playbook.yml --vault-password-file ~/.vault_pass_script.sh
```

### Multiple Vault Passwords (Vault IDs)

```bash
# Encrypt with vault ID
$ ansible-vault encrypt --vault-id dev@prompt vars/dev_secrets.yml
$ ansible-vault encrypt --vault-id prod@~/.vault_pass_prod vars/prod_secrets.yml

# Run with multiple vault IDs
$ ansible-playbook playbook.yml \
    --vault-id dev@prompt \
    --vault-id prod@~/.vault_pass_prod
```

## 10.5 Vault Best Practices

### Separate Encrypted and Unencrypted Variables

```
group_vars/
  production/
    vars.yml          # Non-sensitive (plaintext)
    vault.yml          # Sensitive (encrypted)
```

```yaml
# group_vars/production/vars.yml (plaintext)
---
db_host: prod-db.example.com
db_port: 5432
db_name: myapp_production
db_user: "{{ vault_db_user }}"        # Reference vault variable
db_password: "{{ vault_db_password }}" # Reference vault variable
api_url: https://api.example.com
api_key: "{{ vault_api_key }}"         # Reference vault variable
```

```yaml
# group_vars/production/vault.yml (encrypted)
---
vault_db_user: myapp_prod_user
vault_db_password: SuperSecretPassword123
vault_api_key: sk-abc123def456
vault_ssl_private_key: |
  -----BEGIN PRIVATE KEY-----
  MIIEvgIBADANBgkqhkiG9w0BAQE...
  -----END PRIVATE KEY-----
```

**Convention**: Prefix vault variables with `vault_` to make it clear where they come from.

### Never Commit Vault Password Files

```gitignore
# .gitignore
.vault_pass
*.vault_pass
vault_password_file
```

## 10.6 Security Hardening Playbook

```yaml
---
- name: Server security hardening
  hosts: all
  become: yes

  vars_files:
    - vars/security_settings.yml

  tasks:
    - name: Disable root SSH login
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?PermitRootLogin'
        line: 'PermitRootLogin no'
      notify: Restart sshd

    - name: Disable password authentication
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?PasswordAuthentication'
        line: 'PasswordAuthentication no'
      notify: Restart sshd

    - name: Set SSH idle timeout
      blockinfile:
        path: /etc/ssh/sshd_config
        marker: "# {mark} ANSIBLE MANAGED - Timeout Settings"
        block: |
          ClientAliveInterval 300
          ClientAliveCountMax 2
      notify: Restart sshd

    - name: Configure firewall (UFW)
      ufw:
        rule: allow
        port: "{{ item.port }}"
        proto: "{{ item.proto | default('tcp') }}"
      loop:
        - { port: '22' }
        - { port: '80' }
        - { port: '443' }

    - name: Enable firewall
      ufw:
        state: enabled
        policy: deny

    - name: Install fail2ban
      apt:
        name: fail2ban
        state: present

    - name: Configure fail2ban
      copy:
        content: |
          [sshd]
          enabled = true
          port = ssh
          filter = sshd
          logpath = /var/log/auth.log
          maxretry = 3
          bantime = 3600
          findtime = 600
        dest: /etc/fail2ban/jail.local
      notify: Restart fail2ban

    - name: Set file permissions on sensitive files
      file:
        path: "{{ item }}"
        mode: '0600'
      loop:
        - /etc/shadow
        - /etc/gshadow

    - name: Disable unused services
      service:
        name: "{{ item }}"
        state: stopped
        enabled: no
      loop:
        - cups
        - avahi-daemon
      ignore_errors: yes

    - name: Configure automatic security updates
      apt:
        name: unattended-upgrades
        state: present

    - name: Enable automatic updates
      copy:
        content: |
          APT::Periodic::Update-Package-Lists "1";
          APT::Periodic::Unattended-Upgrade "1";
          APT::Periodic::AutocleanInterval "7";
        dest: /etc/apt/apt.conf.d/20auto-upgrades

  handlers:
    - name: Restart sshd
      service:
        name: sshd
        state: restarted

    - name: Restart fail2ban
      service:
        name: fail2ban
        state: restarted
```

## 10.7 Managing SSL/TLS Certificates

```yaml
tasks:
  - name: Create SSL directory
    file:
      path: /etc/ssl/private
      state: directory
      mode: '0700'

  - name: Deploy SSL certificate
    copy:
      content: "{{ vault_ssl_certificate }}"
      dest: /etc/ssl/certs/app.crt
      mode: '0644'

  - name: Deploy SSL private key
    copy:
      content: "{{ vault_ssl_private_key }}"
      dest: /etc/ssl/private/app.key
      mode: '0600'
    no_log: true  # Don't log sensitive content

  - name: Install certbot for Let's Encrypt
    apt:
      name:
        - certbot
        - python3-certbot-nginx
      state: present

  - name: Obtain Let's Encrypt certificate
    command: >
      certbot certonly --nginx
      -d {{ domain_name }}
      --non-interactive
      --agree-tos
      --email {{ admin_email }}
    args:
      creates: "/etc/letsencrypt/live/{{ domain_name }}/fullchain.pem"
```

### no_log - Prevent Sensitive Data in Logs

```yaml
tasks:
  - name: Set database password
    mysql_user:
      name: "{{ db_user }}"
      password: "{{ db_password }}"
      priv: "*.*:ALL"
    no_log: true  # Prevents password from appearing in logs/output

  # Output with no_log:
  # TASK [Set database password] *************************************************
  # changed: [db1] => {"censored": "the output has been hidden due to the fact that 'no_log: true' was specified for this result"}
```


---

# MODULE 11: Advanced Topics

## 11.1 Dynamic Inventory

Dynamic inventory fetches host information from external sources at runtime instead of static files.

### AWS EC2 Dynamic Inventory

```yaml
# inventory/aws_ec2.yml
---
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
  - us-west-2

filters:
  tag:Environment:
    - production
  instance-state-name:
    - running

keyed_groups:
  # Group by tag "Role" (e.g., tag:Role=webserver -> group "role_webserver")
  - key: tags.Role
    prefix: role
    separator: "_"

  # Group by instance type
  - key: instance_type
    prefix: type

  # Group by region
  - key: placement.region
    prefix: region

hostnames:
  - tag:Name
  - private-ip-address

compose:
  ansible_host: private_ip_address
  ansible_user: "'ubuntu'"
```

```bash
# Install AWS collection
$ ansible-galaxy collection install amazon.aws

# Configure AWS credentials
$ export AWS_ACCESS_KEY_ID='AKIAIOSFODNN7EXAMPLE'
$ export AWS_SECRET_ACCESS_KEY='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

# Test dynamic inventory
$ ansible-inventory -i inventory/aws_ec2.yml --graph

# Output:
# @all:
#   |--@role_webserver:
#   |  |--web-prod-01
#   |  |--web-prod-02
#   |--@role_database:
#   |  |--db-prod-01
#   |--@region_us_east_1:
#   |  |--web-prod-01
#   |  |--db-prod-01
#   |--@region_us_west_2:
#   |  |--web-prod-02

# Use in playbook
$ ansible-playbook -i inventory/aws_ec2.yml playbook.yml
```

### Custom Dynamic Inventory Script

```python
#!/usr/bin/env python3
# inventory/custom_inventory.py
import json
import argparse

def get_inventory():
    """Return inventory from your custom source (API, database, etc.)"""
    inventory = {
        "webservers": {
            "hosts": ["web1.example.com", "web2.example.com"],
            "vars": {
                "http_port": 80,
                "ansible_user": "ubuntu"
            }
        },
        "dbservers": {
            "hosts": ["db1.example.com"],
            "vars": {
                "db_port": 5432,
                "ansible_user": "postgres"
            }
        },
        "_meta": {
            "hostvars": {
                "web1.example.com": {
                    "ansible_host": "10.0.1.11",
                    "server_id": 1
                },
                "web2.example.com": {
                    "ansible_host": "10.0.1.12",
                    "server_id": 2
                },
                "db1.example.com": {
                    "ansible_host": "10.0.1.21"
                }
            }
        }
    }
    return inventory

def get_host(hostname):
    """Return variables for a specific host"""
    inventory = get_inventory()
    return inventory["_meta"]["hostvars"].get(hostname, {})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--host", type=str)
    args = parser.parse_args()

    if args.list:
        print(json.dumps(get_inventory(), indent=2))
    elif args.host:
        print(json.dumps(get_host(args.host), indent=2))
```

```bash
# Make executable
$ chmod +x inventory/custom_inventory.py

# Test
$ ./inventory/custom_inventory.py --list
$ ansible-playbook -i inventory/custom_inventory.py playbook.yml
```

## 11.2 Callback Plugins

Callback plugins change how Ansible displays output.

### Built-in Callbacks

```ini
# ansible.cfg
[defaults]
# Change output format
stdout_callback = yaml          # YAML formatted output (recommended)
# stdout_callback = json        # JSON output
# stdout_callback = debug       # Detailed debug output
# stdout_callback = minimal     # Minimal output
# stdout_callback = dense       # One-line per task output

# Enable additional callbacks
callbacks_enabled = timer, profile_tasks, profile_roles
```

### timer - Show Total Execution Time

```
# Output with timer callback:
# PLAY RECAP *******************************************************************
# web1 : ok=5  changed=3  unreachable=0  failed=0
#
# Playbook run took 0 days, 0 hours, 2 minutes, 34 seconds
```

### profile_tasks - Show Per-Task Timing

```
# Output with profile_tasks:
# Thursday 15 January 2024  14:30:00 +0000 (0:00:45.123) 0:02:34.567 ****
# ===============================================================================
# Install packages -------------------------------------------- 45.12s
# Deploy configuration ---------------------------------------- 23.45s
# Restart services -------------------------------------------- 12.34s
# Gathering Facts --------------------------------------------- 5.67s
```

## 11.3 Delegation and Local Actions

### delegate_to - Run Task on Different Host

```yaml
tasks:
  # Run task on localhost instead of remote host
  - name: Add host to load balancer
    uri:
      url: "http://lb.example.com/api/backends"
      method: POST
      body: '{"host": "{{ inventory_hostname }}", "port": 80}'
      body_format: json
    delegate_to: localhost

  # Run task on a specific host
  - name: Update DNS record
    command: "nsupdate -k /etc/rndc.key"
    delegate_to: dns-server

  # Run task on the first host in a group
  - name: Run migration only once
    command: /opt/app/migrate.sh
    delegate_to: "{{ groups['dbservers'][0] }}"
    run_once: true
```

### local_action - Shorthand for delegate_to localhost

```yaml
tasks:
  - name: Create local backup directory
    local_action:
      module: file
      path: /tmp/backups/{{ inventory_hostname }}
      state: directory

  - name: Wait for port to be available
    local_action:
      module: wait_for
      host: "{{ ansible_host }}"
      port: 80
      delay: 5
      timeout: 300
```

### run_once - Execute Task Only Once

```yaml
tasks:
  - name: Run database migration (only once, not per host)
    command: /opt/app/migrate.sh
    run_once: true
    # Runs on the first host in the play, skips the rest

  - name: Send deployment notification
    slack:
      token: "{{ slack_token }}"
      msg: "Deployment complete on {{ ansible_play_hosts | length }} hosts"
    run_once: true
    delegate_to: localhost
```

## 11.4 Asynchronous Actions

For long-running tasks that might exceed SSH timeout:

```yaml
tasks:
  # Start a long task asynchronously
  - name: Run long database backup
    command: /opt/scripts/full_backup.sh
    async: 3600        # Maximum runtime in seconds (1 hour)
    poll: 0            # Don't wait (fire and forget)
    register: backup_job

  # Do other tasks while backup runs
  - name: Update application
    apt:
      name: myapp
      state: latest

  # Check on the async task
  - name: Wait for backup to complete
    async_status:
      jid: "{{ backup_job.ansible_job_id }}"
    register: backup_result
    until: backup_result.finished
    retries: 60
    delay: 60          # Check every 60 seconds

  - name: Show backup result
    debug:
      msg: "Backup completed: {{ backup_result }}"
```

## 11.5 Strategy Plugins

Control how Ansible executes tasks across hosts.

```yaml
# Linear strategy (default) - All hosts complete task 1 before task 2 starts
- name: Linear execution
  hosts: webservers
  strategy: linear
  tasks: [...]

# Free strategy - Each host runs independently, as fast as possible
- name: Free execution
  hosts: webservers
  strategy: free
  tasks: [...]

# Serial - Process hosts in batches
- name: Rolling update
  hosts: webservers
  serial: 2            # Process 2 hosts at a time
  tasks: [...]

# Serial with percentage
- name: Canary deployment
  hosts: webservers
  serial:
    - 1                # First: 1 host (canary)
    - 30%              # Then: 30% of remaining
    - 100%             # Finally: all remaining
  tasks: [...]
```

## 11.6 Performance Tuning

### ansible.cfg Optimizations

```ini
[defaults]
# Increase parallelism
forks = 20

# Disable fact gathering if not needed
gathering = smart          # Only gather if not cached
# gathering = explicit     # Never gather unless asked
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 86400  # Cache for 24 hours

# Use mitogen strategy (3-7x faster)
# strategy_plugins = /path/to/mitogen/ansible_mitogen/plugins/strategy
# strategy = mitogen_linear

[ssh_connection]
# Enable pipelining (major speedup)
pipelining = True

# SSH multiplexing
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o PreferredAuthentications=publickey

# Transfer method
transfer_method = piped    # Faster than sftp for small files
```

### Playbook Optimizations

```yaml
---
- name: Optimized playbook
  hosts: webservers
  become: yes
  gather_facts: no         # Skip if not needed

  tasks:
    # Gather only needed facts
    - name: Gather minimal facts
      setup:
        gather_subset:
          - '!all'
          - '!min'
          - network
          - hardware

    # Install all packages in one task (not loop)
    - name: Install packages (single transaction)
      apt:
        name:
          - nginx
          - php-fpm
          - redis
        state: present
        update_cache: yes
        cache_valid_time: 3600  # Don't update if cache is fresh

    # Use free strategy for independent tasks
    - name: Copy configs (order doesn't matter)
      copy:
        src: "{{ item }}"
        dest: "/etc/app/{{ item | basename }}"
      loop: "{{ lookup('fileglob', 'files/configs/*', wantlist=True) }}"
```

## 11.7 Custom Modules

### Simple Custom Module (Python)

```python
#!/usr/bin/env python3
# library/check_disk_space.py

from ansible.module_utils.basic import AnsibleModule
import shutil

def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='str', required=True),
            min_free_gb=dict(type='float', default=1.0),
        ),
        supports_check_mode=True
    )

    path = module.params['path']
    min_free_gb = module.params['min_free_gb']

    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024 ** 3)

        result = dict(
            changed=False,
            path=path,
            total_gb=round(total / (1024 ** 3), 2),
            used_gb=round(used / (1024 ** 3), 2),
            free_gb=round(free_gb, 2),
            min_free_gb=min_free_gb,
        )

        if free_gb < min_free_gb:
            module.fail_json(
                msg=f"Disk space low on {path}: {free_gb:.2f}GB free (minimum: {min_free_gb}GB)",
                **result
            )

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
```

```yaml
# Use custom module in playbook
tasks:
  - name: Check disk space
    check_disk_space:
      path: /
      min_free_gb: 5.0
    register: disk_check

  - name: Show disk info
    debug:
      msg: "{{ disk_check.path }}: {{ disk_check.free_gb }}GB free of {{ disk_check.total_gb }}GB"
```

## 11.8 Ansible with Docker

```yaml
---
- name: Manage Docker containers
  hosts: docker_hosts
  become: yes

  tasks:
    - name: Install Docker
      apt:
        name:
          - docker.io
          - docker-compose
          - python3-docker
        state: present

    - name: Start Docker service
      service:
        name: docker
        state: started
        enabled: yes

    - name: Pull Docker image
      docker_image:
        name: nginx
        tag: latest
        source: pull

    - name: Run container
      docker_container:
        name: web_app
        image: nginx:latest
        state: started
        restart_policy: always
        ports:
          - "80:80"
          - "443:443"
        volumes:
          - /opt/app/html:/usr/share/nginx/html:ro
          - /opt/app/nginx.conf:/etc/nginx/nginx.conf:ro
        env:
          APP_ENV: production
          LOG_LEVEL: info

    - name: Run docker-compose
      docker_compose:
        project_src: /opt/app/
        state: present
        pull: yes
```

## 11.9 Ansible with Kubernetes

```yaml
---
- name: Deploy to Kubernetes
  hosts: localhost
  connection: local

  tasks:
    - name: Create namespace
      k8s:
        state: present
        definition:
          apiVersion: v1
          kind: Namespace
          metadata:
            name: myapp

    - name: Deploy application
      k8s:
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: myapp
            namespace: myapp
          spec:
            replicas: 3
            selector:
              matchLabels:
                app: myapp
            template:
              metadata:
                labels:
                  app: myapp
              spec:
                containers:
                  - name: myapp
                    image: "myapp:{{ app_version }}"
                    ports:
                      - containerPort: 8080
                    resources:
                      requests:
                        memory: "128Mi"
                        cpu: "250m"
                      limits:
                        memory: "256Mi"
                        cpu: "500m"

    - name: Create service
      k8s:
        state: present
        definition:
          apiVersion: v1
          kind: Service
          metadata:
            name: myapp
            namespace: myapp
          spec:
            selector:
              app: myapp
            ports:
              - port: 80
                targetPort: 8080
            type: LoadBalancer

    - name: Wait for deployment
      k8s_info:
        kind: Deployment
        name: myapp
        namespace: myapp
      register: deployment
      until: deployment.resources[0].status.readyReplicas == 3
      retries: 30
      delay: 10
```

## 11.10 Ansible Tower / AWX

AWX is the open-source version of Ansible Tower (now Ansible Automation Platform). It provides:
- Web UI for running playbooks
- Role-based access control (RBAC)
- Job scheduling
- Inventory management
- Credential management
- API for integration

```bash
# Install AWX using Docker
$ git clone https://github.com/ansible/awx.git
$ cd awx
$ make docker-compose-build
$ make docker-compose

# Access at http://localhost:8043
# Default credentials: admin / password
```


---

# MODULE 12: Real-World Industry Projects

## Project 1: Multi-Tier Web Application Deployment

Deploy a production-grade application with Nginx (reverse proxy), Node.js (application), and PostgreSQL (database).

### Project Structure

```
project-webapp/
  ansible.cfg
  inventory/
    production/
      hosts.ini
      group_vars/
        all.yml
        webservers.yml
        appservers.yml
        dbservers.yml
      host_vars/
  playbooks/
    site.yml
    deploy.yml
    rollback.yml
  roles/
    common/
    nginx/
    nodejs_app/
    postgresql/
  templates/
  vars/
    vault.yml
```

### Inventory

```ini
# inventory/production/hosts.ini
[loadbalancers]
lb1 ansible_host=10.0.1.10

[webservers]
web1 ansible_host=10.0.1.11
web2 ansible_host=10.0.1.12

[appservers]
app1 ansible_host=10.0.2.11
app2 ansible_host=10.0.2.12

[dbservers]
db1 ansible_host=10.0.3.11
db2 ansible_host=10.0.3.12

[dbservers:vars]
ansible_user=postgres

[production:children]
loadbalancers
webservers
appservers
dbservers
```

### Master Playbook

```yaml
# playbooks/site.yml
---
- name: Common setup for all servers
  hosts: all
  become: yes
  roles:
    - common

- name: Configure load balancers
  hosts: loadbalancers
  become: yes
  roles:
    - role: nginx
      vars:
        nginx_role: loadbalancer
        nginx_upstream_servers: "{{ groups['webservers'] }}"

- name: Configure web servers
  hosts: webservers
  become: yes
  roles:
    - role: nginx
      vars:
        nginx_role: reverse_proxy
        nginx_backend_servers: "{{ groups['appservers'] }}"

- name: Configure application servers
  hosts: appservers
  become: yes
  serial: 1  # Rolling deployment - one at a time
  roles:
    - nodejs_app

- name: Configure database servers
  hosts: dbservers
  become: yes
  roles:
    - postgresql
```

### Common Role

```yaml
# roles/common/tasks/main.yml
---
- name: Update package cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name:
      - vim
      - curl
      - wget
      - htop
      - net-tools
      - ntp
      - fail2ban
      - ufw
    state: present

- name: Set timezone
  timezone:
    name: "{{ timezone | default('UTC') }}"

- name: Configure NTP
  service:
    name: ntp
    state: started
    enabled: yes

- name: Create deploy user
  user:
    name: deploy
    groups: sudo
    shell: /bin/bash
    create_home: yes

- name: Set up SSH key for deploy user
  authorized_key:
    user: deploy
    key: "{{ deploy_ssh_public_key }}"

- name: Harden SSH
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
  loop:
    - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
    - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
  notify: Restart sshd

- name: Configure firewall
  ufw:
    rule: allow
    port: "{{ item }}"
  loop: "{{ firewall_allowed_ports | default(['22']) }}"

- name: Enable firewall
  ufw:
    state: enabled
    policy: deny

handlers:
  - name: Restart sshd
    service:
      name: sshd
      state: restarted
```

### Node.js Application Role

```yaml
# roles/nodejs_app/tasks/main.yml
---
- name: Install Node.js repository
  shell: curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  args:
    creates: /etc/apt/sources.list.d/nodesource.list

- name: Install Node.js
  apt:
    name: nodejs
    state: present

- name: Create application directory
  file:
    path: "{{ app_dir }}"
    state: directory
    owner: "{{ app_user }}"
    mode: '0755'

- name: Deploy application code
  synchronize:
    src: "{{ app_source_dir }}/"
    dest: "{{ app_dir }}/"
    delete: yes
    rsync_opts:
      - "--exclude=node_modules"
      - "--exclude=.git"
      - "--exclude=.env"
  notify: Restart application

- name: Install npm dependencies
  npm:
    path: "{{ app_dir }}"
    production: yes

- name: Deploy environment file
  template:
    src: env.j2
    dest: "{{ app_dir }}/.env"
    owner: "{{ app_user }}"
    mode: '0600'
  notify: Restart application
  no_log: true

- name: Deploy systemd service
  template:
    src: app.service.j2
    dest: /etc/systemd/system/{{ app_name }}.service
  notify:
    - Reload systemd
    - Restart application

- name: Start application
  service:
    name: "{{ app_name }}"
    state: started
    enabled: yes

- name: Wait for application to be healthy
  uri:
    url: "http://localhost:{{ app_port }}/health"
    status_code: 200
  register: health
  until: health.status == 200
  retries: 30
  delay: 5

# roles/nodejs_app/handlers/main.yml
---
- name: Reload systemd
  systemd:
    daemon_reload: yes

- name: Restart application
  service:
    name: "{{ app_name }}"
    state: restarted
```

### Zero-Downtime Deployment Playbook

```yaml
# playbooks/deploy.yml
---
- name: Zero-downtime deployment
  hosts: appservers
  become: yes
  serial: 1  # One server at a time
  max_fail_percentage: 0

  pre_tasks:
    - name: Remove from load balancer
      uri:
        url: "http://{{ groups['loadbalancers'][0] }}/api/backend/{{ inventory_hostname }}"
        method: DELETE
      delegate_to: localhost

    - name: Wait for connections to drain
      wait_for:
        timeout: 30

  roles:
    - nodejs_app

  post_tasks:
    - name: Verify application health
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      register: health_check
      retries: 10
      delay: 5
      until: health_check.status == 200

    - name: Add back to load balancer
      uri:
        url: "http://{{ groups['loadbalancers'][0] }}/api/backend"
        method: POST
        body: '{"host": "{{ inventory_hostname }}", "port": {{ app_port }}}'
        body_format: json
      delegate_to: localhost

    - name: Wait for load balancer to register
      pause:
        seconds: 10
```

### Rollback Playbook

```yaml
# playbooks/rollback.yml
---
- name: Rollback to previous version
  hosts: appservers
  become: yes
  serial: 1

  vars_prompt:
    - name: rollback_version
      prompt: "Enter version to rollback to"
      private: no

  tasks:
    - name: Stop application
      service:
        name: "{{ app_name }}"
        state: stopped

    - name: Deploy previous version
      git:
        repo: "{{ app_git_repo }}"
        dest: "{{ app_dir }}"
        version: "{{ rollback_version }}"
        force: yes

    - name: Install dependencies
      npm:
        path: "{{ app_dir }}"
        production: yes

    - name: Start application
      service:
        name: "{{ app_name }}"
        state: started

    - name: Verify health
      uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      retries: 10
      delay: 5
```

---

## Project 2: CI/CD Pipeline with Ansible

Integrate Ansible with Jenkins/GitLab CI for automated deployments.

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - deploy_staging
  - deploy_production

variables:
  ANSIBLE_HOST_KEY_CHECKING: "False"

lint:
  stage: lint
  image: cytopia/ansible-lint
  script:
    - ansible-lint playbooks/site.yml
    - ansible-playbook playbooks/site.yml --syntax-check

test:
  stage: test
  image: ansible/ansible-runner
  script:
    - ansible-playbook playbooks/site.yml --check -i inventory/staging/

deploy_staging:
  stage: deploy_staging
  image: ansible/ansible-runner
  script:
    - echo "$VAULT_PASSWORD" > /tmp/.vault_pass
    - ansible-playbook playbooks/deploy.yml
        -i inventory/staging/
        --vault-password-file /tmp/.vault_pass
        -e "app_version=$CI_COMMIT_SHA"
    - rm /tmp/.vault_pass
  environment:
    name: staging
  only:
    - develop

deploy_production:
  stage: deploy_production
  image: ansible/ansible-runner
  script:
    - echo "$VAULT_PASSWORD" > /tmp/.vault_pass
    - ansible-playbook playbooks/deploy.yml
        -i inventory/production/
        --vault-password-file /tmp/.vault_pass
        -e "app_version=$CI_COMMIT_TAG"
    - rm /tmp/.vault_pass
  environment:
    name: production
  only:
    - tags
  when: manual  # Require manual approval
```

---

## Project 3: Complete Monitoring Stack (Prometheus + Grafana)

```yaml
# playbooks/monitoring.yml
---
- name: Deploy Prometheus
  hosts: monitoring
  become: yes

  vars:
    prometheus_version: "2.48.0"
    prometheus_targets: "{{ groups['all'] }}"

  tasks:
    - name: Create prometheus user
      user:
        name: prometheus
        system: yes
        shell: /usr/sbin/nologin
        create_home: no

    - name: Create directories
      file:
        path: "{{ item }}"
        state: directory
        owner: prometheus
      loop:
        - /etc/prometheus
        - /var/lib/prometheus

    - name: Download Prometheus
      unarchive:
        src: "https://github.com/prometheus/prometheus/releases/download/v{{ prometheus_version }}/prometheus-{{ prometheus_version }}.linux-amd64.tar.gz"
        dest: /tmp/
        remote_src: yes

    - name: Install Prometheus binaries
      copy:
        src: "/tmp/prometheus-{{ prometheus_version }}.linux-amd64/{{ item }}"
        dest: "/usr/local/bin/{{ item }}"
        remote_src: yes
        mode: '0755'
      loop:
        - prometheus
        - promtool

    - name: Deploy Prometheus config
      template:
        src: prometheus.yml.j2
        dest: /etc/prometheus/prometheus.yml
        owner: prometheus
      notify: Restart prometheus

    - name: Deploy systemd service
      template:
        src: prometheus.service.j2
        dest: /etc/systemd/system/prometheus.service
      notify:
        - Reload systemd
        - Restart prometheus

    - name: Start Prometheus
      service:
        name: prometheus
        state: started
        enabled: yes

  handlers:
    - name: Reload systemd
      systemd:
        daemon_reload: yes
    - name: Restart prometheus
      service:
        name: prometheus
        state: restarted

- name: Deploy Grafana
  hosts: monitoring
  become: yes

  tasks:
    - name: Add Grafana repository
      apt_repository:
        repo: "deb https://apt.grafana.com stable main"
        state: present

    - name: Add Grafana GPG key
      apt_key:
        url: https://apt.grafana.com/gpg.key
        state: present

    - name: Install Grafana
      apt:
        name: grafana
        state: present
        update_cache: yes

    - name: Deploy Grafana config
      template:
        src: grafana.ini.j2
        dest: /etc/grafana/grafana.ini
      notify: Restart grafana

    - name: Start Grafana
      service:
        name: grafana-server
        state: started
        enabled: yes

    - name: Add Prometheus datasource
      grafana_datasource:
        name: Prometheus
        ds_type: prometheus
        url: "http://localhost:9090"
        is_default: yes
        grafana_url: "http://localhost:3000"
        grafana_user: admin
        grafana_password: "{{ grafana_admin_password }}"

  handlers:
    - name: Restart grafana
      service:
        name: grafana-server
        state: restarted

- name: Deploy Node Exporter on all hosts
  hosts: all
  become: yes

  vars:
    node_exporter_version: "1.7.0"

  tasks:
    - name: Create node_exporter user
      user:
        name: node_exporter
        system: yes
        shell: /usr/sbin/nologin

    - name: Download Node Exporter
      unarchive:
        src: "https://github.com/prometheus/node_exporter/releases/download/v{{ node_exporter_version }}/node_exporter-{{ node_exporter_version }}.linux-amd64.tar.gz"
        dest: /tmp/
        remote_src: yes

    - name: Install Node Exporter
      copy:
        src: "/tmp/node_exporter-{{ node_exporter_version }}.linux-amd64/node_exporter"
        dest: /usr/local/bin/node_exporter
        remote_src: yes
        mode: '0755'

    - name: Deploy systemd service
      copy:
        content: |
          [Unit]
          Description=Node Exporter
          After=network.target

          [Service]
          User=node_exporter
          ExecStart=/usr/local/bin/node_exporter
          Restart=always

          [Install]
          WantedBy=multi-user.target
        dest: /etc/systemd/system/node_exporter.service
      notify: Restart node_exporter

    - name: Start Node Exporter
      service:
        name: node_exporter
        state: started
        enabled: yes

  handlers:
    - name: Restart node_exporter
      service:
        name: node_exporter
        state: restarted
```

---

## Project 4: AWS Infrastructure Provisioning

```yaml
# playbooks/aws_provision.yml
---
- name: Provision AWS Infrastructure
  hosts: localhost
  connection: local
  gather_facts: no

  vars:
    aws_region: us-east-1
    vpc_cidr: 10.0.0.0/16
    project_name: myapp
    environment: production

  tasks:
    - name: Create VPC
      amazon.aws.ec2_vpc_net:
        name: "{{ project_name }}-vpc"
        cidr_block: "{{ vpc_cidr }}"
        region: "{{ aws_region }}"
        tags:
          Environment: "{{ environment }}"
          Project: "{{ project_name }}"
      register: vpc

    - name: Create public subnet
      amazon.aws.ec2_vpc_subnet:
        vpc_id: "{{ vpc.vpc.id }}"
        cidr: 10.0.1.0/24
        az: "{{ aws_region }}a"
        tags:
          Name: "{{ project_name }}-public-1"
      register: public_subnet

    - name: Create Internet Gateway
      amazon.aws.ec2_vpc_igw:
        vpc_id: "{{ vpc.vpc.id }}"
        tags:
          Name: "{{ project_name }}-igw"
      register: igw

    - name: Create security group
      amazon.aws.ec2_security_group:
        name: "{{ project_name }}-web-sg"
        description: "Web server security group"
        vpc_id: "{{ vpc.vpc.id }}"
        rules:
          - proto: tcp
            ports: [80, 443]
            cidr_ip: 0.0.0.0/0
          - proto: tcp
            ports: [22]
            cidr_ip: 10.0.0.0/8
      register: web_sg

    - name: Launch EC2 instances
      amazon.aws.ec2_instance:
        name: "{{ project_name }}-web-{{ item }}"
        instance_type: t3.medium
        image_id: ami-0c55b159cbfafe1f0  # Ubuntu 22.04
        key_name: "{{ project_name }}-key"
        vpc_subnet_id: "{{ public_subnet.subnet.id }}"
        security_group: "{{ web_sg.group_id }}"
        network:
          assign_public_ip: true
        tags:
          Role: webserver
          Environment: "{{ environment }}"
        wait: yes
      loop: "{{ range(1, 4) | list }}"
      register: ec2_instances

    - name: Create RDS instance
      amazon.aws.rds_instance:
        db_instance_identifier: "{{ project_name }}-db"
        engine: postgres
        engine_version: "15"
        db_instance_class: db.t3.medium
        allocated_storage: 100
        master_username: "{{ vault_db_user }}"
        master_user_password: "{{ vault_db_password }}"
        vpc_security_group_ids:
          - "{{ db_sg.group_id }}"
        tags:
          Environment: "{{ environment }}"
      no_log: true

    - name: Add instances to inventory
      add_host:
        name: "{{ item.instances[0].public_ip_address }}"
        groups: webservers
        ansible_user: ubuntu
      loop: "{{ ec2_instances.results }}"

    - name: Wait for SSH
      wait_for:
        host: "{{ item.instances[0].public_ip_address }}"
        port: 22
        delay: 10
        timeout: 300
      loop: "{{ ec2_instances.results }}"

- name: Configure provisioned servers
  hosts: webservers
  become: yes
  roles:
    - common
    - webserver
```

---

## Project 5: Disaster Recovery Automation

```yaml
# playbooks/disaster_recovery.yml
---
- name: Disaster Recovery - Database Failover
  hosts: dbservers
  become: yes
  vars:
    primary_db: db1
    standby_db: db2

  tasks:
    - name: Check primary database health
      postgresql_ping:
        db: "{{ db_name }}"
        login_host: "{{ hostvars[primary_db].ansible_host }}"
        login_user: "{{ db_user }}"
        login_password: "{{ vault_db_password }}"
      register: primary_health
      ignore_errors: yes
      delegate_to: localhost
      run_once: true

    - name: Primary is healthy - no action needed
      debug:
        msg: "Primary database {{ primary_db }} is healthy. No failover needed."
      when: primary_health is succeeded
      run_once: true

    - name: FAILOVER - Promote standby to primary
      block:
        - name: Send alert notification
          slack:
            token: "{{ vault_slack_token }}"
            msg: "DATABASE FAILOVER INITIATED - Promoting {{ standby_db }} to primary"
            channel: "#ops-alerts"
          delegate_to: localhost

        - name: Promote standby database
          command: pg_ctl promote -D /var/lib/postgresql/15/main
          become_user: postgres
          when: inventory_hostname == standby_db

        - name: Update application config to point to new primary
          template:
            src: db_config.j2
            dest: /opt/app/.env
          vars:
            db_host: "{{ hostvars[standby_db].ansible_host }}"
          delegate_to: "{{ item }}"
          loop: "{{ groups['appservers'] }}"
          notify: Restart application

        - name: Restart application servers
          service:
            name: "{{ app_name }}"
            state: restarted
          delegate_to: "{{ item }}"
          loop: "{{ groups['appservers'] }}"

        - name: Verify application connectivity
          uri:
            url: "http://{{ item }}:{{ app_port }}/health"
            status_code: 200
          delegate_to: localhost
          loop: "{{ groups['appservers'] }}"
          retries: 5
          delay: 10

        - name: Send success notification
          slack:
            token: "{{ vault_slack_token }}"
            msg: "FAILOVER COMPLETE - {{ standby_db }} is now primary"
            channel: "#ops-alerts"
          delegate_to: localhost

      when: primary_health is failed
      run_once: true
```


---

# MODULE 13: Common Errors and Troubleshooting

## 13.1 Connection Errors

### Error: SSH Connection Refused

```
web1 | UNREACHABLE! => {
    "changed": false,
    "msg": "Failed to connect to the host via ssh: ssh: connect to host 192.168.56.11 port 22: Connection refused",
    "unreachable": true
}
```

**Causes and Fixes:**

| Cause | Fix |
|-------|-----|
| SSH not running on target | `sudo systemctl start sshd` on target |
| Wrong IP address | Verify `ansible_host` in inventory |
| Firewall blocking port 22 | `sudo ufw allow 22` on target |
| Wrong SSH port | Set `ansible_port=2222` in inventory |

**Debugging steps:**
```bash
# Test SSH manually
$ ssh -v user@192.168.56.11

# Check if port is open
$ nc -zv 192.168.56.11 22

# Check firewall on target
$ sudo ufw status
$ sudo iptables -L -n | grep 22
```

### Error: Permission Denied (Public Key)

```
web1 | UNREACHABLE! => {
    "msg": "Failed to connect to the host via ssh: Permission denied (publickey)."
}
```

**Fixes:**
```bash
# Check SSH key is copied
$ ssh-copy-id -i ~/.ssh/id_ed25519.pub user@192.168.56.11

# Verify key permissions
$ chmod 700 ~/.ssh
$ chmod 600 ~/.ssh/id_ed25519
$ chmod 644 ~/.ssh/id_ed25519.pub

# Check authorized_keys on target
$ ssh user@target "cat ~/.ssh/authorized_keys"

# Try with password temporarily
$ ansible all -m ping -k  # -k asks for SSH password

# Check ansible.cfg settings
# private_key_file = ~/.ssh/id_ed25519
# remote_user = ubuntu
```

### Error: Host Key Verification Failed

```
web1 | UNREACHABLE! => {
    "msg": "Failed to connect to the host via ssh: Host key verification failed."
}
```

**Fixes:**
```bash
# Option 1: Accept the host key
$ ssh-keyscan 192.168.56.11 >> ~/.ssh/known_hosts

# Option 2: Disable host key checking (lab/dev only)
# In ansible.cfg:
# [defaults]
# host_key_checking = False

# Option 3: Environment variable
$ export ANSIBLE_HOST_KEY_CHECKING=False
```

## 13.2 Authentication and Privilege Errors

### Error: Missing sudo Password

```
web1 | FAILED! => {
    "msg": "Missing sudo password"
}
```

**Fixes:**
```bash
# Option 1: Ask for sudo password
$ ansible-playbook playbook.yml --ask-become-pass  # or -K

# Option 2: Configure passwordless sudo on target
$ echo "ubuntu ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ubuntu

# Option 3: Set in ansible.cfg
# [privilege_escalation]
# become_ask_pass = True
```

### Error: Sudo: A Password is Required

```
web1 | FAILED! => {
    "msg": "Incorrect sudo password"
}
```

**Fixes:**
```bash
# Verify the password
$ ansible-playbook playbook.yml -K

# Check sudoers configuration on target
$ sudo visudo
# Ensure user has proper sudo access
```

## 13.3 Module Errors

### Error: Python Not Found

```
web1 | FAILED! => {
    "module_stderr": "/bin/sh: 1: /usr/bin/python: not found",
    "msg": "The module failed to execute correctly"
}
```

**Fixes:**
```bash
# Option 1: Install Python on target
$ ansible web1 -m raw -a "apt-get install -y python3" -b

# Option 2: Set Python interpreter in inventory
# In inventory:
# [all:vars]
# ansible_python_interpreter=/usr/bin/python3

# Option 3: Set in ansible.cfg
# [defaults]
# interpreter_python = auto_silent
```

### Error: Module Not Found

```
ERROR! couldn't resolve module/action 'community.general.ufw'
```

**Fixes:**
```bash
# Install the required collection
$ ansible-galaxy collection install community.general

# Or install from requirements
$ ansible-galaxy install -r requirements.yml

# Check installed collections
$ ansible-galaxy collection list
```

### Error: No Package Matching

```
web1 | FAILED! => {
    "msg": "No package matching 'nginx' is available"
}
```

**Fixes:**
```yaml
# Update cache before installing
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install nginx
  apt:
    name: nginx
    state: present

# Or use update_cache in the same task
- name: Install nginx
  apt:
    name: nginx
    state: present
    update_cache: yes
```

## 13.4 YAML Syntax Errors

### Error: YAML Parsing Error

```
ERROR! Syntax Error while loading YAML.
  mapping values are not allowed in this context

The error appears to be in 'playbook.yml': line 10, column 15
```

**Common causes and fixes:**

```yaml
# ERROR 1: Tab instead of spaces
# WRONG:
tasks:
	- name: Install nginx  # TAB character!

# CORRECT:
tasks:
  - name: Install nginx    # 2 spaces

# ERROR 2: Missing space after colon
# WRONG:
name:Install nginx

# CORRECT:
name: Install nginx

# ERROR 3: Unquoted special characters
# WRONG:
msg: Value is: {{ variable }}

# CORRECT:
msg: "Value is: {{ variable }}"

# ERROR 4: Incorrect indentation
# WRONG:
tasks:
- name: Task 1
  apt:
  name: nginx    # 'name' is at same level as 'apt'

# CORRECT:
tasks:
  - name: Task 1
    apt:
      name: nginx  # 'name' is indented under 'apt'

# ERROR 5: Missing dash for list items
# WRONG:
tasks:
  name: Task 1
  apt:
    name: nginx

# CORRECT:
tasks:
  - name: Task 1
    apt:
      name: nginx
```

### Validate YAML Before Running

```bash
# Syntax check
$ ansible-playbook playbook.yml --syntax-check

# Use yamllint
$ pip install yamllint
$ yamllint playbook.yml

# Use ansible-lint
$ pip install ansible-lint
$ ansible-lint playbook.yml
```

## 13.5 Variable Errors

### Error: Undefined Variable

```
web1 | FAILED! => {
    "msg": "The task includes an option with an undefined variable. The error was: 'db_host' is undefined"
}
```

**Fixes:**
```yaml
# Option 1: Define the variable
vars:
  db_host: localhost

# Option 2: Use default filter
- debug:
    msg: "DB host: {{ db_host | default('localhost') }}"

# Option 3: Check if defined
- name: Use variable if defined
  debug:
    msg: "{{ db_host }}"
  when: db_host is defined

# Option 4: Pass as extra var
# $ ansible-playbook playbook.yml -e "db_host=db.example.com"
```

### Error: Variable Type Mismatch

```
web1 | FAILED! => {
    "msg": "Unexpected templating type error occurred on ({{ ports }}): unhashable type: 'list'"
}
```

**Fixes:**
```yaml
# When using variables in certain contexts, convert types
- name: Show port list
  debug:
    msg: "{{ ports | join(', ') }}"  # Convert list to string

# When comparing, ensure types match
- name: Check port
  debug:
    msg: "Port is 80"
  when: http_port | int == 80  # Ensure integer comparison
```

## 13.6 Template Errors

### Error: Jinja2 Template Error

```
AnsibleError: template error while templating string: unexpected '}'
```

**Common fixes:**
```jinja2
{# WRONG: Missing closing brace #}
{{ variable }

{# CORRECT #}
{{ variable }}

{# WRONG: Nested braces in shell commands #}
command: echo ${HOME}

{# CORRECT: Escape or use raw #}
command: echo ${HOME}
{# Or use raw block in templates: #}
{% raw %}
echo ${HOME}
{% endraw %}
```

### Error: Template File Not Found

```
AnsibleError: Could not find or access 'nginx.conf.j2'
```

**Fixes:**
```yaml
# Templates are looked up relative to:
# 1. Role's templates/ directory
# 2. Playbook's templates/ directory
# 3. Current directory

# Ensure file exists in the right location:
# roles/webserver/templates/nginx.conf.j2
# OR
# templates/nginx.conf.j2 (next to playbook)

# Use absolute path if needed
- template:
    src: /full/path/to/nginx.conf.j2
    dest: /etc/nginx/nginx.conf
```

## 13.7 Vault Errors

### Error: Vault Password Not Provided

```
ERROR! Attempting to decrypt but no vault secrets found
```

**Fixes:**
```bash
# Provide vault password
$ ansible-playbook playbook.yml --ask-vault-pass

# Or use password file
$ ansible-playbook playbook.yml --vault-password-file ~/.vault_pass

# Or set in ansible.cfg
# [defaults]
# vault_password_file = ~/.vault_pass

# Or environment variable
$ export ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass
```

### Error: Decryption Failed

```
ERROR! Decryption failed on vars/secrets.yml
```

**Fixes:**
```bash
# Wrong password - verify you're using the correct one
$ ansible-vault view vars/secrets.yml  # Test with correct password

# Re-encrypt with new password
$ ansible-vault rekey vars/secrets.yml

# Check if file is actually encrypted
$ head -1 vars/secrets.yml
# Should show: $ANSIBLE_VAULT;1.1;AES256
```

## 13.8 Performance Issues

### Playbook Running Slowly

**Diagnosis and fixes:**

```bash
# Enable task profiling
# In ansible.cfg:
# [defaults]
# callbacks_enabled = profile_tasks

# Run and check which tasks are slow
$ ansible-playbook playbook.yml
# Output shows time per task
```

```yaml
# Fix 1: Disable fact gathering if not needed
- hosts: webservers
  gather_facts: no

# Fix 2: Use fact caching
# In ansible.cfg:
# [defaults]
# gathering = smart
# fact_caching = jsonfile
# fact_caching_connection = /tmp/facts_cache
# fact_caching_timeout = 86400

# Fix 3: Increase forks
# In ansible.cfg:
# [defaults]
# forks = 20

# Fix 4: Enable pipelining
# In ansible.cfg:
# [ssh_connection]
# pipelining = True

# Fix 5: Install packages in bulk (not loop)
# SLOW:
- name: Install packages
  apt:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - curl
    - vim

# FAST:
- name: Install packages
  apt:
    name:
      - nginx
      - curl
      - vim
    state: present

# Fix 6: Use free strategy for independent tasks
- hosts: webservers
  strategy: free
```

## 13.9 Debugging Techniques

### Verbose Mode

```bash
# Increasing verbosity levels
$ ansible-playbook playbook.yml -v      # Basic output
$ ansible-playbook playbook.yml -vv     # More detail
$ ansible-playbook playbook.yml -vvv    # Connection debugging
$ ansible-playbook playbook.yml -vvvv   # Full debug (includes SSH)
```

### Debug Module

```yaml
tasks:
  - name: Print variable value
    debug:
      var: my_variable

  - name: Print message
    debug:
      msg: "The value is {{ my_variable }}"

  - name: Print all variables for a host
    debug:
      var: hostvars[inventory_hostname]

  - name: Print all groups
    debug:
      var: groups

  - name: Print registered variable
    command: whoami
    register: result

  - debug:
      var: result
```

### Debugger

```yaml
# Enable debugger on failure
- name: Task with debugger
  command: /bin/false
  debugger: on_failed

# Debugger commands:
# p task        - Print task info
# p task.args   - Print task arguments
# p host        - Print current host
# p result      - Print task result
# redo          - Re-run the task
# continue      - Continue to next task
# quit          - Quit the debugger
```

### assert Module

```yaml
tasks:
  - name: Verify prerequisites
    assert:
      that:
        - ansible_distribution == "Ubuntu"
        - ansible_distribution_version is version('20.04', '>=')
        - ansible_memtotal_mb >= 2048
      fail_msg: "Server does not meet minimum requirements"
      success_msg: "All prerequisites met"
```

## 13.10 Common Error Quick Reference

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| `UNREACHABLE` | SSH connection failed | Check SSH, firewall, IP address |
| `Permission denied` | Wrong SSH key or user | `ssh-copy-id`, check `remote_user` |
| `Missing sudo password` | No passwordless sudo | Use `-K` or configure sudoers |
| `Python not found` | Python missing on target | Set `ansible_python_interpreter` |
| `Module not found` | Collection not installed | `ansible-galaxy collection install` |
| `Syntax Error` | YAML formatting issue | `ansible-playbook --syntax-check` |
| `Undefined variable` | Variable not set | Use `default()` filter or define var |
| `Vault decrypt failed` | Wrong vault password | Verify password, use `--ask-vault-pass` |
| `Template not found` | Wrong path to template | Check `templates/` directory |
| `changed: false` | Already in desired state | This is normal (idempotency) |
| `Timeout` | Slow network or host | Increase `timeout` in ansible.cfg |
| `Too many open files` | Too many forks | Reduce `forks` or increase ulimit |

## 13.11 Ansible Lint Rules

```bash
# Install ansible-lint
$ pip install ansible-lint

# Run lint
$ ansible-lint playbook.yml

# Common lint warnings and fixes:

# [command-instead-of-module] - Use module instead of command
# WRONG:
- command: apt-get install nginx
# CORRECT:
- apt:
    name: nginx
    state: present

# [no-changed-when] - Command tasks should have changed_when
# WRONG:
- command: cat /etc/hostname
# CORRECT:
- command: cat /etc/hostname
  changed_when: false

# [yaml] - YAML formatting issues
# Fix: Use consistent 2-space indentation

# [name] - All tasks should be named
# WRONG:
- apt:
    name: nginx
# CORRECT:
- name: Install nginx
  apt:
    name: nginx

# [risky-shell-pipe] - Shell pipes can hide errors
# WRONG:
- shell: cat /etc/passwd | grep root
# CORRECT:
- shell: cat /etc/passwd | grep root
  failed_when: false
  changed_when: false
```

## 13.12 Checklist Before Running Playbooks

```
Pre-flight checklist:

[ ] ansible --version              # Verify Ansible is installed
[ ] ansible-playbook --syntax-check # Validate YAML syntax
[ ] ansible-lint playbook.yml      # Check best practices
[ ] ansible-inventory --graph      # Verify inventory structure
[ ] ansible all -m ping            # Test connectivity to all hosts
[ ] ansible-playbook --check       # Dry run (check mode)
[ ] ansible-playbook --check --diff # Dry run with changes shown
[ ] ansible-playbook --list-tasks  # Review task list
[ ] ansible-playbook --list-hosts  # Verify target hosts
```

---

# MODULE 14: Additional Topics from Comprehensive Guide

This module covers topics referenced in the Ansible Comprehensive Guide and interview scenarios that are not addressed in earlier modules.

---

## 14.1 Managing Windows Managed Nodes (WinRM)

Ansible communicates with Linux hosts over SSH, but Windows hosts use **WinRM (Windows Remote Management)** instead. No agent is needed on Windows, but WinRM must be enabled.

### Setting Up WinRM on Windows

On the Windows target, open PowerShell as Administrator:

```powershell
# Enable WinRM
winrm quickconfig

# Allow unencrypted traffic (lab/dev only)
winrm set winrm/config/service '@{AllowUnencrypted="true"}'

# Allow basic authentication (lab/dev only)
winrm set winrm/config/service/auth '@{Basic="true"}'

# Verify WinRM is listening
winrm enumerate winrm/config/listener
# Output:
# Listener
#     Address = *
#     Transport = HTTP
#     Port = 5985
#     Enabled = true
```

### Installing pywinrm on the Control Node

```bash
# Install the Python WinRM library
$ pip install pywinrm

# Verify installation
$ python3 -c "import winrm; print('pywinrm installed')"
# Output: pywinrm installed
```

### Inventory Configuration for Windows Hosts

```ini
# inventory/hosts.ini
[windows]
win1 ansible_host=192.168.1.50

[windows:vars]
ansible_user=Administrator
ansible_password=SecurePass123
ansible_connection=winrm
ansible_winrm_transport=basic
ansible_winrm_server_cert_validation=ignore
ansible_port=5985
```

### Testing Connectivity to Windows Hosts

```bash
$ ansible windows -m win_ping -i inventory/hosts.ini

# Output:
# win1 | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }
```

### Common Windows Modules

```yaml
---
- name: Manage Windows servers
  hosts: windows
  tasks:
    - name: Install IIS
      win_feature:
        name: Web-Server
        state: present

    - name: Copy file to Windows
      win_copy:
        src: files/app.zip
        dest: C:\Temp\app.zip

    - name: Run PowerShell command
      win_shell: Get-Service | Where-Object {$_.Status -eq 'Running'}
      register: services

    - name: Show running services
      debug:
        var: services.stdout_lines

    - name: Ensure a service is running
      win_service:
        name: W3SVC
        state: started
        start_mode: auto

    - name: Install MSI package
      win_package:
        path: C:\Temp\installer.msi
        state: present
```

### Real-Life Use Case

A company manages a mixed fleet of 200 Linux and 50 Windows servers. Ansible uses SSH for Linux and WinRM for Windows from a single control node, applying OS-specific roles via `ansible_os_family` conditionals. This eliminates the need for separate tools.

### WSL (Windows Subsystem for Linux)

If your control node is a Windows machine, install WSL to run Ansible:

```bash
# On Windows (PowerShell as Admin)
wsl --install

# Inside WSL (Ubuntu)
sudo apt update && sudo apt install ansible -y
ansible --version
```

---

## 14.2 Testing Playbooks with Molecule

Molecule is a testing framework for Ansible roles. It creates isolated environments (Docker, Vagrant, etc.), runs your role, and verifies the result.

### Installing Molecule

```bash
$ pip install molecule molecule-docker

# Verify installation
$ molecule --version
# Output:
# molecule 6.0.3 using python 3.10
#     ansible:2.16.2
#     default:6.0.3 from molecule
```

### Initializing a Role with Molecule

```bash
$ molecule init role my_webserver --driver-name docker

# Output:
# INFO     Initializing new role my_webserver...
# INFO     Initialized role in /home/user/my_webserver successfully.

$ tree my_webserver/molecule/default/
# my_webserver/molecule/default/
# ├── converge.yml
# ├── molecule.yml
# └── verify.yml
```

### Molecule Configuration

```yaml
# molecule/default/molecule.yml
---
dependency:
  name: galaxy
driver:
  name: docker
platforms:
  - name: instance
    image: ubuntu:22.04
    pre_build_image: true
    command: /bin/bash
    tmpfs:
      - /run
      - /tmp
provisioner:
  name: ansible
verifier:
  name: ansible
```

### Converge Playbook (What to Test)

```yaml
# molecule/default/converge.yml
---
- name: Converge
  hosts: all
  become: yes
  roles:
    - role: my_webserver
```

### Verification Playbook

```yaml
# molecule/default/verify.yml
---
- name: Verify
  hosts: all
  become: yes
  tasks:
    - name: Check nginx is installed
      command: nginx -v
      register: nginx_version
      changed_when: false

    - name: Assert nginx is installed
      assert:
        that:
          - nginx_version.rc == 0
        fail_msg: "nginx is not installed"
        success_msg: "nginx is installed"

    - name: Check nginx is running
      service:
        name: nginx
        state: started
      register: nginx_service

    - name: Assert nginx is running
      assert:
        that:
          - nginx_service.status.ActiveState == "active"
```

### Running Molecule Tests

```bash
# Full test lifecycle: create → converge → verify → destroy
$ molecule test

# Output:
# INFO     default scenario test matrix: dependency, cleanup, destroy, syntax,
#          create, prepare, converge, idempotence, side_effect, verify, cleanup, destroy
# ...
# INFO     Running default > create
# INFO     Running default > converge
# PLAY [Converge] ****************************************************************
# TASK [my_webserver : Install nginx] ********************************************
# changed: [instance]
# ...
# INFO     Running default > idempotence
# INFO     Idempotence completed successfully.
# INFO     Running default > verify
# PLAY [Verify] ******************************************************************
# TASK [Assert nginx is installed] ***********************************************
# ok: [instance] => changed=false
#   msg: nginx is installed
# ...
# INFO     Verifier completed successfully.
# INFO     Running default > destroy
# INFO     Pruning extra files from scenario ephemeral directory

# Individual steps
$ molecule create      # Create the test instance
$ molecule converge    # Run the role
$ molecule verify      # Run verification tests
$ molecule destroy     # Tear down the instance
$ molecule login       # SSH into the test instance for debugging
```

### Real-Life Use Case

Before merging a role change into the main branch, a CI pipeline runs `molecule test` to verify the role works on Ubuntu 22.04 and CentOS 9 containers. This catches regressions before they reach production.

---

## 14.3 Bastion / Jump Host Configuration

A bastion (jump) host is an intermediary server that Ansible uses to reach hosts in private networks. SSH connections are tunneled through the bastion.

### Method 1: Inventory-Level Configuration

```ini
# inventory/hosts.ini
[private_servers]
app1 ansible_host=10.0.2.11
app2 ansible_host=10.0.2.12

[private_servers:vars]
ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion_user@bastion.example.com"'
ansible_user=ubuntu
```

### Method 2: Global Configuration in ansible.cfg

```ini
# ansible.cfg
[ssh_connection]
ssh_args = -o ProxyCommand="ssh -W %h:%p -q bastion_user@bastion.example.com"
```

### Method 3: Using ProxyJump (OpenSSH 7.3+)

```ini
# inventory/hosts.ini
[private_servers:vars]
ansible_ssh_common_args='-o ProxyJump=bastion_user@bastion.example.com'
```

### Method 4: SSH Config File

```bash
# ~/.ssh/config
Host bastion
    HostName bastion.example.com
    User bastion_user
    IdentityFile ~/.ssh/bastion_key

Host 10.0.2.*
    ProxyJump bastion
    User ubuntu
    IdentityFile ~/.ssh/app_key
```

```ini
# inventory/hosts.ini - no special args needed when SSH config is set
[private_servers]
app1 ansible_host=10.0.2.11
app2 ansible_host=10.0.2.12
```

### Testing the Connection

```bash
$ ansible private_servers -m ping

# Output:
# app1 | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }
# app2 | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }
```

### Real-Life Use Case

In AWS, application servers sit in private subnets with no public IPs. A bastion host in the public subnet acts as the SSH gateway. Ansible on a CI server connects through the bastion to configure all private instances without exposing them to the internet.

---

## 14.4 HashiCorp Vault Integration

HashiCorp Vault is an external secrets management tool. Ansible can retrieve secrets from it at runtime using the `community.hashi_vault` collection, keeping secrets out of playbooks and inventory files entirely.

### Installing the Collection

```bash
$ ansible-galaxy collection install community.hashi_vault

# Output:
# Starting galaxy collection install process
# Process install dependency map
# Installing 'community.hashi_vault:6.0.0' to '/home/user/.ansible/collections/...'
# community.hashi_vault was installed successfully

# Also install the hvac Python library
$ pip install hvac
```

### Retrieving Secrets with Lookup Plugin

```yaml
---
- name: Use HashiCorp Vault secrets
  hosts: dbservers
  become: yes

  vars:
    vault_addr: "https://vault.example.com:8200"
    vault_token: "{{ lookup('env', 'VAULT_TOKEN') }}"

  tasks:
    - name: Retrieve database password from Vault
      set_fact:
        db_password: "{{ lookup('community.hashi_vault.hashi_vault',
                         'secret/data/myapp/db',
                         token=vault_token,
                         url=vault_addr) }}"

    - name: Show retrieved secret (masked)
      debug:
        msg: "DB password retrieved successfully"
      no_log: true

    - name: Deploy database config
      template:
        src: db.conf.j2
        dest: /etc/myapp/db.conf
        mode: '0600'
      no_log: true
```

### Using Environment Variables for Authentication

```bash
# Set Vault environment variables before running the playbook
$ export VAULT_ADDR="https://vault.example.com:8200"
$ export VAULT_TOKEN="s.xxxxxxxxxxxxxxxxxxxxxxxx"

$ ansible-playbook deploy_db.yml
```

### Retrieving Multiple Secrets

```yaml
tasks:
  - name: Get all secrets from a path
    set_fact:
      app_secrets: "{{ lookup('community.hashi_vault.hashi_vault',
                       'secret/data/myapp',
                       token=vault_token,
                       url=vault_addr) }}"

  - name: Use individual secrets
    debug:
      msg: "API key starts with {{ app_secrets.data.api_key[:4] }}..."
    no_log: true
```

### Using AppRole Authentication (Production)

```yaml
tasks:
  - name: Retrieve secret using AppRole
    set_fact:
      db_creds: "{{ lookup('community.hashi_vault.hashi_vault',
                    'secret/data/myapp/db',
                    auth_method='approle',
                    role_id=lookup('env', 'VAULT_ROLE_ID'),
                    secret_id=lookup('env', 'VAULT_SECRET_ID'),
                    url='https://vault.example.com:8200') }}"
```

### Real-Life Use Case

A financial services company stores database credentials, API keys, and TLS certificates in HashiCorp Vault. Ansible playbooks retrieve these secrets at deploy time, so no credentials are stored in Git repositories. Vault also provides audit logs showing which playbook accessed which secret and when.

---

## 14.5 Jenkins CI/CD Integration

Jenkins can execute Ansible playbooks as part of build and deployment pipelines. This enables automated infrastructure provisioning and application deployment triggered by code changes.

### Prerequisites

```bash
# Install Ansible on the Jenkins node
$ sudo apt install ansible -y

# Install the Jenkins Ansible plugin (via Jenkins UI)
# Manage Jenkins → Plugins → Available → Search "Ansible" → Install
```

### Declarative Pipeline Example

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        ANSIBLE_HOST_KEY_CHECKING = 'False'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/org/infra-repo.git'
            }
        }

        stage('Lint') {
            steps {
                sh 'ansible-lint playbooks/site.yml'
                sh 'ansible-playbook playbooks/site.yml --syntax-check'
            }
        }

        stage('Dry Run') {
            steps {
                ansiblePlaybook(
                    playbook: 'playbooks/site.yml',
                    inventory: 'inventory/staging/hosts.ini',
                    extras: '--check --diff'
                )
            }
        }

        stage('Deploy to Staging') {
            steps {
                ansiblePlaybook(
                    playbook: 'playbooks/deploy.yml',
                    inventory: 'inventory/staging/hosts.ini',
                    credentialsId: 'ansible-ssh-key',
                    extras: '-e "app_version=${BUILD_NUMBER}"'
                )
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            input {
                message "Deploy to production?"
                ok "Yes, deploy"
            }
            steps {
                ansiblePlaybook(
                    playbook: 'playbooks/deploy.yml',
                    inventory: 'inventory/production/hosts.ini',
                    credentialsId: 'ansible-ssh-key',
                    vaultCredentialsId: 'ansible-vault-pass',
                    extras: '-e "app_version=${BUILD_NUMBER}"'
                )
            }
        }
    }

    post {
        failure {
            slackSend channel: '#deployments',
                      message: "Deployment FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        success {
            slackSend channel: '#deployments',
                      message: "Deployment SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
```

### Using Ansible with Jenkins Credentials

```groovy
// Store SSH key and vault password as Jenkins credentials
// Then reference them in the pipeline:
stage('Deploy') {
    steps {
        withCredentials([
            sshUserPrivateKey(credentialsId: 'ansible-ssh-key',
                              keyFileVariable: 'SSH_KEY'),
            string(credentialsId: 'vault-password',
                   variable: 'VAULT_PASS')
        ]) {
            sh """
                echo "\${VAULT_PASS}" > /tmp/.vault_pass
                ansible-playbook playbooks/deploy.yml \
                    -i inventory/production/hosts.ini \
                    --private-key=\${SSH_KEY} \
                    --vault-password-file=/tmp/.vault_pass \
                    -e "app_version=${BUILD_NUMBER}"
                rm -f /tmp/.vault_pass
            """
        }
    }
}
```

### Sample Command Output

```
Started by user admin
Running in Durability level: MAX_SURVIVABILITY
[Pipeline] Start of Pipeline
[Pipeline] stage (Lint)
[Pipeline] sh
+ ansible-lint playbooks/site.yml
Passed: 0 failure(s), 0 warning(s) on 1 files.
[Pipeline] stage (Deploy to Staging)
[Pipeline] ansiblePlaybook
[deploy.yml] $ ansible-playbook playbooks/deploy.yml -i inventory/staging/hosts.ini -e app_version=42

PLAY [Deploy application] ******************************************************

TASK [Deploy code] *************************************************************
changed: [staging-web1]

PLAY RECAP *********************************************************************
staging-web1 : ok=5  changed=3  unreachable=0  failed=0

Finished: SUCCESS
```

### Real-Life Use Case

A development team pushes code to GitHub. A Jenkins webhook triggers the pipeline, which lints the Ansible playbooks, runs a dry-run against staging, deploys to staging, runs integration tests, and then waits for manual approval before deploying to production. This provides a fully auditable deployment process.

---

## 14.6 Expect Module for Interactive Commands

Some commands require interactive input (passwords, confirmations). The `expect` module automates these by providing predefined responses to prompts.

### Prerequisites

```bash
# Install pexpect on the control node
$ pip install pexpect

# Ensure pexpect is also on managed nodes if using raw commands
```

### Basic Usage

```yaml
---
- name: Handle interactive commands
  hosts: all
  become: yes

  tasks:
    - name: Change user password interactively
      expect:
        command: passwd appuser
        responses:
          "New password:": "S3cur3P@ss!"
          "Retype new password:": "S3cur3P@ss!"
      no_log: true
```

### Sample Command Output

```
TASK [Change user password interactively] **************************************
changed: [web1]
```

### Handling Multiple Prompts

```yaml
tasks:
  - name: Initialize application with interactive setup
    expect:
      command: /opt/app/setup.sh
      responses:
        "Enter database host:": "db.internal"
        "Enter database port:": "5432"
        "Enter admin email:": "admin@example.com"
        "Confirm settings\\? \\(y/n\\)": "y"
      timeout: 60
```

### Using Regex in Responses

```yaml
tasks:
  - name: Handle varying prompts
    expect:
      command: ssh-keygen -t ed25519
      responses:
        "Enter file in which to save the key.*": "/home/user/.ssh/deploy_key"
        "Enter passphrase.*": ""
        "Enter same passphrase again.*": ""
      creates: /home/user/.ssh/deploy_key
```

### Real-Life Use Case

A legacy application installer requires interactive input for database credentials, license keys, and configuration options. The `expect` module automates this installation across 50 servers, providing consistent responses without manual intervention.

---

## 14.7 Managing Multiple SSH Keys

When different hosts require different SSH keys for authentication, Ansible supports per-host key configuration.

### Per-Host Key in Inventory

```ini
# inventory/hosts.ini
[webservers]
web1 ansible_host=10.0.1.11 ansible_ssh_private_key_file=~/.ssh/web_key
web2 ansible_host=10.0.1.12 ansible_ssh_private_key_file=~/.ssh/web_key

[dbservers]
db1 ansible_host=10.0.2.11 ansible_ssh_private_key_file=~/.ssh/db_key

[cloud]
aws1 ansible_host=54.23.45.67 ansible_ssh_private_key_file=~/.ssh/aws_key.pem
```

### Per-Group Key in group_vars

```yaml
# group_vars/webservers.yml
ansible_ssh_private_key_file: ~/.ssh/web_key
ansible_user: ubuntu

# group_vars/dbservers.yml
ansible_ssh_private_key_file: ~/.ssh/db_key
ansible_user: postgres
```

### Runtime Key Override

```bash
# Override key for a single run
$ ansible-playbook playbook.yml --private-key=~/.ssh/special_key

# Combine with specific user
$ ansible-playbook playbook.yml --private-key=~/.ssh/special_key -u deploy
```

### Real-Life Use Case

An organization manages servers across AWS (using .pem keys), on-premise data centers (using ed25519 keys), and a partner's infrastructure (using RSA keys). Each group in the inventory specifies its own key file, allowing a single playbook to target all environments.

---

## 14.8 Installing Specific Package Versions

Pinning package versions ensures consistent environments across deployments and prevents unexpected upgrades.

### Debian/Ubuntu (apt)

```yaml
tasks:
  - name: Install specific nginx version
    apt:
      name: nginx=1.18.0-0ubuntu1
      state: present
      update_cache: yes

  - name: Install specific version and hold it
    apt:
      name: nginx=1.18.0-0ubuntu1
      state: present

  - name: Prevent package from being upgraded
    dpkg_selections:
      name: nginx
      selection: hold
```

### RHEL/CentOS (yum/dnf)

```yaml
tasks:
  - name: Install specific httpd version
    yum:
      name: httpd-2.4.6-97.el7
      state: present

  - name: Install specific version with dnf
    dnf:
      name: nginx-1.20.1
      state: present
```

### Checking Available Versions

```bash
# Debian/Ubuntu
$ apt-cache madison nginx
# Output:
#  nginx | 1.18.0-0ubuntu1.4 | http://archive.ubuntu.com/ubuntu focal-updates/main amd64 Packages
#  nginx | 1.18.0-0ubuntu1   | http://archive.ubuntu.com/ubuntu focal/main amd64 Packages

# RHEL/CentOS
$ yum --showduplicates list nginx
# Output:
# Available Packages
# nginx.x86_64    1:1.20.1-9.el8    appstream
# nginx.x86_64    1:1.20.1-10.el8   appstream
```

### Real-Life Use Case

A compliance requirement mandates that all production servers run the same tested version of OpenSSL. Ansible pins the version during deployment and holds it to prevent automatic upgrades from breaking the application.

---

## 14.9 Preventing File Overwrites (backup Parameter)

The `backup` parameter in modules like `copy`, `template`, and `lineinfile` creates a timestamped backup before modifying a file.

### Using backup with copy

```yaml
tasks:
  - name: Deploy config with backup
    copy:
      src: nginx.conf
      dest: /etc/nginx/nginx.conf
      backup: yes

  # If the file existed, Ansible creates:
  # /etc/nginx/nginx.conf.2024.01.15-14:30:22~
```

### Using backup with template

```yaml
tasks:
  - name: Deploy template with backup
    template:
      src: app.conf.j2
      dest: /etc/myapp/app.conf
      backup: yes
    register: config_deploy

  - name: Show backup file path
    debug:
      msg: "Backup created at {{ config_deploy.backup_file }}"
    when: config_deploy.backup_file is defined
```

### Using creates to Skip If File Exists

```yaml
tasks:
  - name: Create file only if it doesn't exist
    command: /opt/app/generate-config.sh
    args:
      creates: /etc/myapp/generated.conf

  # The command only runs if /etc/myapp/generated.conf is absent
```

### Using force: no with copy

```yaml
tasks:
  - name: Copy default config only if not present
    copy:
      src: default.conf
      dest: /etc/myapp/app.conf
      force: no   # Don't overwrite if file exists
```

### Sample Command Output

```
TASK [Deploy config with backup] ***********************************************
changed: [web1] => {
    "backup_file": "/etc/nginx/nginx.conf.32015.2024-01-15@14:30:22~",
    "changed": true,
    "dest": "/etc/nginx/nginx.conf",
    "md5sum": "a1b2c3d4e5f6..."
}
```

### Real-Life Use Case

During a configuration rollout, the backup parameter preserves the previous config. If the new config causes issues, an operator can quickly restore the backup file without needing to redeploy.

---

## 14.10 Managing Temporary Files

Ansible creates temporary files during execution. You can also manage your own temporary files using `tempfile` module and cleanup tasks.

### Using the tempfile Module

```yaml
tasks:
  - name: Create a temporary file
    tempfile:
      state: file
      suffix: .conf
    register: temp_file

  - name: Show temp file path
    debug:
      msg: "Temp file: {{ temp_file.path }}"
    # Output: Temp file: /tmp/ansible.abc123.conf

  - name: Write to temp file
    copy:
      content: "temporary configuration data"
      dest: "{{ temp_file.path }}"

  - name: Use the temp file
    command: /opt/app/validate --config {{ temp_file.path }}

  - name: Clean up temp file
    file:
      path: "{{ temp_file.path }}"
      state: absent
```

### Creating Temporary Directories

```yaml
tasks:
  - name: Create a temporary directory
    tempfile:
      state: directory
      prefix: ansible_build_
    register: temp_dir

  - name: Use temp directory for build
    command: make -C {{ temp_dir.path }}

  - name: Clean up temp directory
    file:
      path: "{{ temp_dir.path }}"
      state: absent
```

### Cleanup Pattern with block/always

```yaml
tasks:
  - name: Work with temporary files safely
    block:
      - name: Create temp file
        tempfile:
          state: file
        register: temp

      - name: Do work with temp file
        copy:
          content: "build artifact"
          dest: "{{ temp.path }}"

      - name: Process temp file
        command: process {{ temp.path }}

    always:
      - name: Always clean up
        file:
          path: "{{ temp.path }}"
          state: absent
        when: temp.path is defined
```

### Real-Life Use Case

A deployment playbook downloads a build artifact to a temp directory, extracts it, copies files to the application directory, then cleans up the temp directory. Using `block/always` ensures cleanup happens even if the deployment fails midway.

---

## 14.11 Validating Configurations Before Applying

The `validate` parameter in the `template` and `copy` modules runs a validation command before committing the file. If validation fails, the file is not deployed.

### Validating Nginx Configuration

```yaml
tasks:
  - name: Deploy nginx config with validation
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
      validate: nginx -t -c %s
    notify: Reload nginx
```

The `%s` placeholder is replaced with the path to the temporary file. If `nginx -t -c` returns a non-zero exit code, the task fails and the original file is preserved.

### Validating sudoers File

```yaml
tasks:
  - name: Deploy sudoers file safely
    template:
      src: sudoers.j2
      dest: /etc/sudoers
      validate: visudo -cf %s
```

### Validating Apache Configuration

```yaml
tasks:
  - name: Deploy Apache config
    template:
      src: httpd.conf.j2
      dest: /etc/httpd/conf/httpd.conf
      validate: apachectl configtest -f %s
    notify: Restart httpd
```

### Validating sshd_config

```yaml
tasks:
  - name: Deploy SSH config
    template:
      src: sshd_config.j2
      dest: /etc/ssh/sshd_config
      validate: sshd -t -f %s
    notify: Restart sshd
```

### Sample Output on Validation Failure

```
TASK [Deploy nginx config with validation] *************************************
fatal: [web1]: FAILED! => {
    "changed": false,
    "msg": "failed to validate: nginx: [emerg] unknown directive \"servr\" in /tmp/ansible-tmp-xxx:3\nnginx: configuration file /tmp/ansible-tmp-xxx test failed"
}
```

### Real-Life Use Case

A typo in a sudoers file can lock all users out of sudo access. Using `validate: visudo -cf %s` prevents a broken sudoers file from ever being written to disk, avoiding a potential system lockout.

---

## 14.12 Refreshing Facts Mid-Playbook

Ansible gathers facts at the start of a play. If a task changes the system state (e.g., adding a network interface), you may need to refresh facts to pick up the changes.

### Force Fact Refresh

```yaml
tasks:
  - name: Add a network interface
    command: ip link add dummy0 type dummy

  - name: Refresh facts after system change
    setup:

  - name: Show updated network interfaces
    debug:
      var: ansible_interfaces
    # Now includes 'dummy0'
```

### Refresh Specific Fact Subsets

```yaml
tasks:
  - name: Install new package
    apt:
      name: docker.io
      state: present

  - name: Refresh only package facts
    setup:
      gather_subset:
        - '!all'
        - '!min'
        - pkg_mgr

  - name: Refresh only network facts
    setup:
      gather_subset:
        - '!all'
        - network
```

### Sample Command Output

```
TASK [Refresh facts after system change] ***************************************
ok: [web1]

TASK [Show updated network interfaces] *****************************************
ok: [web1] => {
    "ansible_interfaces": [
        "lo",
        "eth0",
        "dummy0"
    ]
}
```

### Real-Life Use Case

A playbook provisions a new disk, creates a filesystem, and mounts it. After mounting, facts are refreshed so subsequent tasks can reference `ansible_mounts` to verify the mount point exists before deploying data to it.

---

## 14.13 Executing Tasks on Failed Hosts

When a playbook run fails on some hosts, you can retry only the failed hosts without re-running the entire playbook.

### Using the Retry File

When a playbook fails, Ansible creates a `.retry` file listing the failed hosts:

```bash
$ ansible-playbook deploy.yml

# Output:
# PLAY RECAP *********************************************************************
# web1 : ok=5  changed=3  unreachable=0  failed=0
# web2 : ok=3  changed=1  unreachable=0  failed=1    ← failed
# web3 : ok=5  changed=3  unreachable=0  failed=0
#
# Retry file: deploy.retry

$ cat deploy.retry
# web2

# Retry only failed hosts
$ ansible-playbook deploy.yml --limit @deploy.retry
```

### Enabling Retry Files

```ini
# ansible.cfg
[defaults]
retry_files_enabled = True
retry_files_save_path = ~/.ansible-retry
```

### Using --limit with Failed Hosts

```bash
# Retry specific hosts manually
$ ansible-playbook deploy.yml --limit "web2,web5"

# Retry hosts that were unreachable
$ ansible-playbook deploy.yml --limit "web2"
```

### Programmatic Retry in Playbook

```yaml
tasks:
  - name: Deploy application
    command: /opt/deploy.sh
    register: deploy_result
    ignore_errors: yes

  - name: Retry deployment on failure
    command: /opt/deploy.sh --retry
    when: deploy_result is failed
    retries: 3
    delay: 30
    until: deploy_result is succeeded
```

### Real-Life Use Case

During a rolling deployment across 100 servers, 3 servers fail due to a transient network issue. Instead of re-running the entire playbook, the operator runs `ansible-playbook deploy.yml --limit @deploy.retry` to target only the 3 failed servers.

---

## 14.14 Managing Multiple Ansible Versions

Different projects may require different Ansible versions. Python virtual environments isolate these versions.

### Creating Isolated Environments

```bash
# Create a virtual environment for Ansible 2.14
$ python3 -m venv ~/ansible-2.14
$ source ~/ansible-2.14/bin/activate
(ansible-2.14) $ pip install ansible==7.0.0  # ansible-core 2.14
(ansible-2.14) $ ansible --version
# Output:
# ansible [core 2.14.0]
#   python version = 3.10.12
(ansible-2.14) $ deactivate

# Create another for Ansible 2.16
$ python3 -m venv ~/ansible-2.16
$ source ~/ansible-2.16/bin/activate
(ansible-2.16) $ pip install ansible==9.0.0  # ansible-core 2.16
(ansible-2.16) $ ansible --version
# Output:
# ansible [core 2.16.0]
#   python version = 3.10.12
(ansible-2.16) $ deactivate
```

### Switching Between Versions

```bash
# Activate the version you need
$ source ~/ansible-2.14/bin/activate
$ ansible-playbook legacy-playbook.yml
$ deactivate

$ source ~/ansible-2.16/bin/activate
$ ansible-playbook modern-playbook.yml
$ deactivate
```

### Using pipx for Global Isolation

```bash
# Install pipx
$ pip install pipx

# Install multiple Ansible versions as separate tools
$ pipx install --suffix=@7 ansible==7.0.0
$ pipx install --suffix=@9 ansible==9.0.0

# Use specific versions
$ ansible-playbook@7 legacy-playbook.yml
$ ansible-playbook@9 modern-playbook.yml
```

### Real-Life Use Case

A consulting firm manages infrastructure for multiple clients. Client A's playbooks require Ansible 2.14 due to deprecated module usage, while Client B uses the latest Ansible 2.16 features. Virtual environments let the team switch between versions without conflicts.

---

## 14.15 High Availability (HA) Setup with Ansible

Ansible can configure load balancers and health checks to achieve high availability for web services.

### HAProxy Load Balancer Setup

```yaml
---
- name: Configure HA web cluster
  hosts: loadbalancer
  become: yes

  vars:
    backend_servers: "{{ groups['webservers'] }}"

  tasks:
    - name: Install HAProxy
      apt:
        name: haproxy
        state: present

    - name: Deploy HAProxy configuration
      template:
        src: haproxy.cfg.j2
        dest: /etc/haproxy/haproxy.cfg
        validate: haproxy -c -f %s
      notify: Restart HAProxy

    - name: Ensure HAProxy is running
      service:
        name: haproxy
        state: started
        enabled: yes

  handlers:
    - name: Restart HAProxy
      service:
        name: haproxy
        state: restarted
```

### HAProxy Configuration Template

```jinja2
# templates/haproxy.cfg.j2
global
    log /dev/log local0
    maxconn 4096
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms
    option  httpchk GET /health

frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
{% for host in backend_servers %}
    server {{ host }} {{ hostvars[host].ansible_host }}:80 check inter 5s fall 3 rise 2
{% endfor %}

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
```

### Verifying HA Setup

```yaml
tasks:
  - name: Verify load balancer is distributing traffic
    uri:
      url: "http://{{ groups['loadbalancer'][0] }}/health"
      status_code: 200
    register: lb_health
    retries: 5
    delay: 5
    until: lb_health.status == 200

  - name: Check HAProxy stats
    uri:
      url: "http://{{ groups['loadbalancer'][0] }}:8404/stats"
      status_code: 200
```

### Sample HAProxy Stats Output

```
# Accessible at http://loadbalancer:8404/stats
# Shows:
# Backend    Status   Weight   Check
# web1       UP       1        L7OK/200 in 5ms
# web2       UP       1        L7OK/200 in 3ms
# web3       DOWN     1        L7STS/503 in 2ms  ← auto-removed from rotation
```

### Real-Life Use Case

An e-commerce platform uses Ansible to deploy a 3-node web cluster behind HAProxy. Health checks run every 5 seconds. If a web server fails, HAProxy removes it from rotation within 15 seconds (3 failed checks). Ansible can then automatically remediate the failed server and add it back.

---

# Course Summary

## Key Takeaways

1. **Ansible is agentless** - Uses SSH, no software needed on managed nodes
2. **Idempotency** - Safe to run playbooks multiple times
3. **YAML** - Human-readable, but whitespace-sensitive
4. **Inventory** - Organize hosts into groups with variables
5. **Modules** - Use built-in modules instead of shell commands
6. **Roles** - Organize code for reuse and sharing
7. **Vault** - Encrypt sensitive data, never commit plaintext secrets
8. **Templates** - Use Jinja2 for dynamic configuration files
9. **Error handling** - Use block/rescue/always for recovery
10. **Testing** - Always use `--check` and `--diff` before production runs

## Recommended Learning Path

```
Week 1: Modules 1-3 (Basics, Installation, Inventory)
Week 2: Modules 4-5 (Ad-Hoc Commands, Playbooks)
Week 3: Modules 6-7 (Variables, Conditionals, Loops)
Week 4: Modules 8-9 (Roles, Templates)
Week 5: Modules 10-11 (Vault, Advanced Topics)
Week 6: Module 12 (Build Industry Projects)
Ongoing: Module 13 (Reference for Troubleshooting)
```

## Essential Commands Cheat Sheet

```bash
# Connectivity
ansible all -m ping

# Ad-hoc commands
ansible webservers -m apt -a "name=nginx state=present" -b
ansible all -a "uptime"
ansible all -m shell -a "df -h | head -2"

# Playbook execution
ansible-playbook playbook.yml
ansible-playbook playbook.yml --check --diff
ansible-playbook playbook.yml --limit web1
ansible-playbook playbook.yml --tags deploy
ansible-playbook playbook.yml -e "version=2.0"

# Inventory
ansible-inventory --graph
ansible-inventory --host web1

# Vault
ansible-vault create secrets.yml
ansible-vault edit secrets.yml
ansible-vault encrypt_string 'secret' --name 'var_name'

# Galaxy
ansible-galaxy init roles/myrole
ansible-galaxy install -r requirements.yml
ansible-galaxy collection install community.general

# Debugging
ansible-playbook playbook.yml -vvv
ansible-playbook playbook.yml --syntax-check
ansible-lint playbook.yml
```
