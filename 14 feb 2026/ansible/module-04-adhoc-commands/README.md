# Module 4: Ad-Hoc Commands

## Syntax

```
ansible <host-pattern> -m <module> -a "<arguments>" [options]
```

## Options

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

## Essential Modules

### Connectivity
```bash
ansible all -m ping
```

### Commands
```bash
ansible all -a "uptime"                                          # command (default)
ansible webservers -m shell -a "ps aux | grep nginx | wc -l"    # shell (pipes)
ansible newservers -m raw -a "apt-get install -y python3"        # raw (no python)
```

### File Operations
```bash
ansible webservers -m copy -a "src=index.html dest=/var/www/html/index.html owner=www-data mode=0644" -b
ansible dbservers -m fetch -a "src=/var/log/postgresql/postgresql.log dest=/tmp/db-logs/ flat=yes"
ansible all -m file -a "path=/opt/myapp state=directory mode=0755 owner=root" -b
```

### Package Management
```bash
ansible webservers -m apt -a "name=nginx state=present update_cache=yes" -b
ansible webservers -m yum -a "name=httpd state=present" -b
```

### Service Management
```bash
ansible webservers -m service -a "name=nginx state=started enabled=yes" -b
ansible webservers -m service -a "name=nginx state=restarted" -b
```

### User Management
```bash
ansible all -m user -a "name=deploy state=present shell=/bin/bash groups=sudo append=yes" -b
```

### Cron Jobs
```bash
ansible dbservers -m cron -a "name='DB Backup' minute=0 hour=2 job='/opt/scripts/backup.sh'" -b
```

### Line in File
```bash
ansible all -m lineinfile -a "path=/etc/ssh/sshd_config regexp='^PermitRootLogin' line='PermitRootLogin no'" -b
```

### System Facts
```bash
ansible web1 -m setup
ansible web1 -m setup -a "filter=ansible_distribution*"
```

### Fleet Status Checks
```bash
ansible all -a "uptime" -f 20
ansible all -m shell -a "df -h / | tail -1" -f 20
ansible all -m shell -a "free -m | grep Mem" -f 20
```

### Dry Run
```bash
ansible webservers -m apt -a "name=nginx state=present" -b --check
```
