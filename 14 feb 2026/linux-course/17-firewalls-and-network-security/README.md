# Module 17: Firewalls and Network Security

## 8.9 Firewall — `iptables` and `ufw`

### `ufw` — Uncomplicated Firewall (Ubuntu)

```bash
# Enable firewall
$ sudo ufw enable
Firewall is active and enabled on system startup

# Check status
$ sudo ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere

# Allow a port
$ sudo ufw allow 8080/tcp
Rule added

# Allow from specific IP
$ sudo ufw allow from 10.0.0.0/24 to any port 22

# Deny a port
$ sudo ufw deny 3306/tcp

# Delete a rule
$ sudo ufw delete allow 8080/tcp

# Reset all rules
$ sudo ufw reset
```

### `iptables` — Advanced firewall

```bash
# List current rules
$ sudo iptables -L -n -v
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
 1234  100K ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22
  567   45K ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:80

# Allow incoming SSH
$ sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow incoming HTTP/HTTPS
$ sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
$ sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Drop all other incoming traffic
$ sudo iptables -A INPUT -j DROP

# Allow established connections
$ sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Save rules (persist across reboot)
$ sudo iptables-save > /etc/iptables/rules.v4
```

### `firewalld` (RHEL/CentOS)

```bash
# Check status
$ sudo firewall-cmd --state
running

# List allowed services
$ sudo firewall-cmd --list-all
public (active)
  services: cockpit dhcpv6-client ssh http https
  ports:

# Add a service
$ sudo firewall-cmd --permanent --add-service=http
$ sudo firewall-cmd --reload

# Add a port
$ sudo firewall-cmd --permanent --add-port=8080/tcp
$ sudo firewall-cmd --reload

# Remove a service
$ sudo firewall-cmd --permanent --remove-service=http
$ sudo firewall-cmd --reload
```

---


## 8.25 nftables — Modern Firewall Framework

`nftables` is the successor to `iptables`, used in Debian 10+, RHEL 8+, and newer distributions.

```bash
# List all rules
nft list ruleset

# Add a table and chain
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; }

# Allow SSH
nft add rule inet filter input tcp dport 22 accept

# Allow HTTP and HTTPS
nft add rule inet filter input tcp dport { 80, 443 } accept

# Drop all other incoming traffic
nft add rule inet filter input drop

# Save rules
nft list ruleset > /etc/nftables.conf

# Load rules on boot
sudo systemctl enable nftables
```

### iptables vs nftables

| Feature | iptables | nftables |
|---------|----------|----------|
| Syntax | Separate commands per rule | Unified syntax |
| Performance | Slower with many rules | Faster rule processing |
| IPv4/IPv6 | Separate tools (iptables/ip6tables) | Single tool handles both |
| Default in | Older distros | Debian 10+, RHEL 8+ |

---


## 8.28 Enterprise Network Services — Quick Reference

### NFS — Network File System

Share directories between Linux servers:

```bash
# Server: export a directory
sudo apt install nfs-kernel-server
echo "/shared 192.168.1.0/24(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server

# Client: mount the share
sudo apt install nfs-common
sudo mount -t nfs server:/shared /mnt/nfs
# Persist in /etc/fstab:
# server:/shared /mnt/nfs nfs defaults 0 0
```

### Samba — Windows File Sharing (SMB/CIFS)

Share files between Linux and Windows:

```bash
sudo apt install samba
# Edit /etc/samba/smb.conf:
# [shared]
#   path = /srv/samba/shared
#   browsable = yes
#   writable = yes
#   valid users = @smbgroup

sudo systemctl restart smbd
# Windows: \\linux-server\shared
```

### Apache HTTPD — Web Server

```bash
sudo apt install apache2              # Debian/Ubuntu
sudo yum install httpd                # RHEL/CentOS
sudo systemctl enable --now apache2
# Config: /etc/apache2/sites-available/
# Logs: /var/log/apache2/
```

### Chrony — NTP Time Synchronization

```bash
sudo apt install chrony
sudo systemctl enable --now chronyd
chronyc tracking                      # Check sync status
chronyc sources -v                    # View time sources
```

### DHCP Server

```bash
sudo apt install isc-dhcp-server
# Config: /etc/dhcp/dhcpd.conf
# subnet 192.168.1.0 netmask 255.255.255.0 {
#   range 192.168.1.100 192.168.1.200;
#   option routers 192.168.1.1;
#   option domain-name-servers 8.8.8.8;
# }
sudo systemctl restart isc-dhcp-server
```

---

## 8.29 Interview Questions — Module 8

**Q1: How do you troubleshoot network connectivity issues?**

Follow this systematic approach:
1. `ping localhost` — verify local network stack
2. `ping gateway` — verify LAN connectivity
3. `ping 8.8.8.8` — verify internet (bypasses DNS)
4. `ping google.com` — verify DNS resolution
5. `traceroute google.com` — find where packets stop
6. `ss -tulnp` — check listening services
7. `iptables -L -n` / `ufw status` — check firewall rules

**Q2: What is the difference between TCP and UDP?**

TCP is connection-oriented (3-way handshake), guarantees delivery and ordering — used for SSH, HTTP, databases. UDP is connectionless, best-effort — used for DNS, streaming, gaming. TCP is reliable but slower; UDP is fast but unreliable.

**Q3: How do you find which process is using a specific port?**

```bash
sudo ss -tlnp | grep :80             # Socket statistics
sudo lsof -i :80                     # List open files on port
sudo fuser 80/tcp                    # Find PID using port
sudo netstat -tlnp | grep :80        # Legacy (net-tools)
```

**Q4: What is the difference between `iptables` and `nftables`?**

`nftables` is the successor to `iptables` with unified syntax (handles IPv4/IPv6 in one tool), better performance with many rules, and atomic rule replacement. `iptables` is still widely used but deprecated in newer distributions (Debian 10+, RHEL 8+).

**Q5: How do you configure a static IP address?**

```bash
# Ubuntu (netplan)
sudo vi /etc/netplan/01-config.yaml
# network:
#   ethernets:
#     eth0:
#       addresses: [192.168.1.10/24]
#       gateway4: 192.168.1.1
#       nameservers:
#         addresses: [8.8.8.8, 8.8.4.4]
sudo netplan apply

# RHEL (nmcli)
sudo nmcli con mod eth0 ipv4.addresses 192.168.1.10/24
sudo nmcli con mod eth0 ipv4.gateway 192.168.1.1
sudo nmcli con mod eth0 ipv4.dns "8.8.8.8"
sudo nmcli con mod eth0 ipv4.method manual
sudo nmcli con up eth0
```
