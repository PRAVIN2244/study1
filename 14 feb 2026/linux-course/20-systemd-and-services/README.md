# Module 20: Systemd and Service Management

## 12.14 Systemd and Service Management

`systemd` is the init system and service manager for modern Linux. It replaces SysVinit with parallel, dependency-aware service startup.

### Common systemctl Commands

```bash
# Start, stop, restart services
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx       # Reload config without restart

# Enable/disable on boot
sudo systemctl enable nginx
sudo systemctl disable nginx

# Check status
systemctl status nginx

# List all active services
systemctl list-units --type=service

# List all services (including inactive)
systemctl list-unit-files --type=service

# Check failed services
systemctl --failed
```

### Creating a Custom systemd Service

Create a unit file at `/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=My Custom Application
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/myapp/server.py
Restart=on-failure
User=appuser
WorkingDirectory=/opt/myapp
Environment=PORT=8080

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd after creating/editing unit files
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable --now myapp.service

# Check logs
journalctl -u myapp.service -f
```

### systemd Targets

Targets are groups of units that define system states (like runlevels):

| Target | Purpose |
|--------|---------|
| `default.target` | Default boot target |
| `multi-user.target` | CLI multi-user mode |
| `graphical.target` | GUI mode |
| `rescue.target` | Single-user rescue mode |
| `emergency.target` | Minimal emergency shell |

```bash
# Check default target
systemctl get-default

# Change default
sudo systemctl set-default multi-user.target
```

### Logging with journalctl

```bash
# View all logs
journalctl

# Logs for a specific service
journalctl -u nginx

# Follow logs in real time
journalctl -f

# Logs since last boot
journalctl -b

# Logs from a time range
journalctl --since "2 hours ago"
journalctl --since "2024-01-01" --until "2024-01-02"

# Show only errors
journalctl -p err

# Disk usage by journal
journalctl --disk-usage

# Trim journal to 500MB
sudo journalctl --vacuum-size=500M
```

### systemd Timers (Replacement for cron)

Create a timer to run a backup daily:

**`/etc/systemd/system/backup.service`**:
```ini
[Unit]
Description=Run backup script

[Service]
Type=oneshot
ExecStart=/opt/backup.sh
```

**`/etc/systemd/system/backup.timer`**:
```ini
[Unit]
Description=Daily backup timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer
systemctl list-timers
```

---


## 12.7 Systemd Timers (Modern Cron Alternative)

```bash
# Create a service unit
$ sudo cat > /etc/systemd/system/backup.service << 'EOF'
[Unit]
Description=Daily Backup

[Service]
Type=oneshot
ExecStart=/opt/scripts/backup.sh
User=backup
EOF

# Create a timer unit
$ sudo cat > /etc/systemd/system/backup.timer << 'EOF'
[Unit]
Description=Run backup daily

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

$ sudo systemctl daemon-reload
$ sudo systemctl enable --now backup.timer

# List active timers
$ systemctl list-timers
NEXT                         LEFT          LAST                         PASSED       UNIT
Thu 2025-02-06 02:30:00 UTC  11h left      Wed 2025-02-05 02:30:00 UTC  12h ago      backup.timer
```

**Explanation**: Systemd timers offer advantages over cron: logging via journalctl, dependency management, and `Persistent=true` runs missed executions after downtime.

---


## 12.20 systemd Service Hardening

Restrict what services can access to reduce attack surface:

```ini
# Add to [Service] section of unit files
[Service]
ExecStart=/usr/bin/myapp
ExecStartPre=/usr/bin/myapp --check-config
ExecStartPost=/usr/bin/notify-admin "myapp started"
ExecStopPost=/usr/bin/notify-admin "myapp stopped"

# Security hardening directives
ProtectSystem=full          # Mount /usr and /boot as read-only
ProtectHome=yes             # Hide /home, /root, /run/user
PrivateTmp=yes              # Isolated /tmp for this service
NoNewPrivileges=yes         # Prevent privilege escalation
ReadOnlyPaths=/etc          # Make /etc read-only for this service
PrivateDevices=yes          # No access to physical devices
ProtectKernelTunables=yes   # Block writes to /proc and /sys
ProtectKernelModules=yes    # Block module loading
RestrictSUIDSGID=yes        # Block SUID/SGID file creation
```

```bash
# Check security score of a service
systemd-analyze security nginx.service

# Output shows a security exposure score (lower is better)
# and lists which hardening options are enabled/disabled
```

**Real-world**: In production, always harden services that face the internet (nginx, sshd, application servers) to limit damage if compromised.

---

