# Module 5: User & Group Management

## 5.1 Key Files

Linux stores user and group information in plain text files:

| File              | Purpose                                      |
|-------------------|----------------------------------------------|
| `/etc/passwd`     | User account information                     |
| `/etc/shadow`     | Encrypted passwords and aging info           |
| `/etc/group`      | Group definitions and memberships            |
| `/etc/gshadow`    | Group passwords (rarely used)                |
| `/etc/sudoers`    | Sudo access rules                            |
| `/etc/login.defs` | Default settings for user creation           |

### `/etc/passwd` format

```bash
$ cat /etc/passwd | head -3
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
devops:x:1000:1000:DevOps User:/home/devops:/bin/bash
```

Breaking down `devops:x:1000:1000:DevOps User:/home/devops:/bin/bash`:

```
devops  : x    : 1000 : 1000 : DevOps User   : /home/devops : /bin/bash
│         │      │      │      │                │               │
│         │      │      │      │                │               └── Login shell
│         │      │      │      │                └── Home directory
│         │      │      │      └── Comment/full name (GECOS)
│         │      │      └── Primary group ID (GID)
│         │      └── User ID (UID)
│         └── Password placeholder (actual password in /etc/shadow)
└── Username
```

### `/etc/shadow` format

```bash
$ sudo cat /etc/shadow | grep devops
devops:$6$xyz...hash...:19758:0:99999:7:::
```

**Explanation**: Contains the hashed password. Only readable by root. The `$6$` prefix indicates SHA-512 hashing.

### `/etc/group` format

```bash
$ cat /etc/group | grep -E "devops|docker|sudo"
sudo:x:27:devops
docker:x:999:devops
developers:x:1001:devops,john,sarah
```

Format: `group_name:password:GID:member_list`

**Explanation**: User `devops` is a member of `sudo`, `docker`, and `developers` groups.

---

## 5.2 Viewing User Information

### Current user

```bash
$ whoami
devops

$ id
uid=1000(devops) gid=1000(devops) groups=1000(devops),27(sudo),999(docker)
```

**Explanation**: `whoami` shows the username. `id` shows UID, primary GID, and all group memberships. This is essential for debugging permission issues.

### Check another user

```bash
$ id john
uid=1001(john) gid=1001(john) groups=1001(john),1002(developers)
```

### List logged-in users

```bash
$ who
devops   pts/0        2025-02-05 10:00 (10.0.0.5)
john     pts/1        2025-02-05 11:30 (10.0.0.10)

$ w
 15:00:00 up 45 days,  3:12,  2 users,  load average: 0.15, 0.10, 0.08
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
devops   pts/0    10.0.0.5         10:00    0.00s  0.05s  0.00s w
john     pts/1    10.0.0.10        11:30    1:30m  0.02s  0.01s vim
```

**Explanation**: `who` shows logged-in users. `w` adds more detail: idle time, CPU usage, and what command each user is running. `john` has been idle for 1.5 hours and is in `vim`.

### Last logins

```bash
$ last -5
devops   pts/0    10.0.0.5     Wed Feb  5 10:00   still logged in
john     pts/1    10.0.0.10    Wed Feb  5 11:30   still logged in
devops   pts/0    10.0.0.5     Tue Feb  4 09:00 - 18:30  (09:30)
root     tty1                  Mon Feb  3 08:00 - 08:05  (00:05)
reboot   system boot  6.1.0   Mon Dec 22 12:00   still running
```

**Explanation**: `last` shows login history. Useful for auditing who accessed the system and when.

### Failed login attempts

```bash
$ sudo lastb -5
admin    ssh:notty    203.0.113.50     Wed Feb  5 14:50 - 14:50  (00:00)
root     ssh:notty    198.51.100.20    Wed Feb  5 14:45 - 14:45  (00:00)
test     ssh:notty    203.0.113.50     Wed Feb  5 14:40 - 14:40  (00:00)
```

**Explanation**: `lastb` shows failed login attempts. Multiple failures from the same IP suggest a brute-force attack.

---

## 5.3 `useradd` — Create Users

### Create a basic user

```bash
$ sudo useradd john
$ grep john /etc/passwd
john:x:1001:1001::/home/john:/bin/sh
```

**Explanation**: Creates user `john` with default settings. Note: on some distros, `useradd` doesn't create a home directory or set a shell by default.

### Create a user with all options

```bash
$ sudo useradd -m -d /home/john -s /bin/bash -c "John Smith" -G sudo,docker john
$ grep john /etc/passwd
john:x:1001:1001:John Smith:/home/john:/bin/bash

$ id john
uid=1001(john) gid=1001(john) groups=1001(john),27(sudo),999(docker)
```

**Explanation**:
- `-m` — create home directory
- `-d /home/john` — specify home directory path
- `-s /bin/bash` — set login shell
- `-c "John Smith"` — set comment/full name
- `-G sudo,docker` — add to supplementary groups

```bash
# Requested variant format
$ sudo useradd -g group -s /bin/bash -u 9999 -md /home/user username
```

### Create a system user (for services)

```bash
$ sudo useradd -r -s /usr/sbin/nologin -d /opt/myapp myapp
$ grep myapp /etc/passwd
myapp:x:998:998::/opt/myapp:/usr/sbin/nologin
```

**Explanation**: `-r` creates a system user (UID below 1000). `-s /usr/sbin/nologin` prevents interactive login. This is how you create users for running services (nginx, postgres, etc.).

### Set password

```bash
$ sudo passwd john
New password: ********
Retype new password: ********
passwd: password updated successfully
```

### Create user with expiry date

```bash
$ sudo useradd -m -s /bin/bash -e 2025-12-31 contractor
$ sudo chage -l contractor
Last password change                    : Feb 05, 2025
Password expires                        : never
Account expires                         : Dec 31, 2025
```

**Explanation**: `-e` sets an account expiration date. Useful for temporary contractors or interns.

---

## 5.4 `usermod` — Modify Users

### Add user to a group

```bash
$ sudo usermod -aG docker john
$ id john
uid=1001(john) gid=1001(john) groups=1001(john),27(sudo),999(docker)
```

**Explanation**: `-aG` appends the user to the specified group. **Always use `-a` (append)** — without it, the user is removed from all other supplementary groups.

> ⚠️ **Common mistake**: `usermod -G docker john` (without `-a`) removes john from ALL other groups except docker.

### Change login shell

```bash
$ sudo usermod -s /bin/zsh john
$ grep john /etc/passwd
john:x:1001:1001:John Smith:/home/john:/bin/zsh
```

### Change home directory

```bash
$ sudo usermod -d /home/john_new -m john
```

**Explanation**: `-d` sets the new home directory. `-m` moves the contents of the old home to the new location.

### Lock/unlock a user account

```bash
$ sudo usermod -L john          # Lock account
$ sudo passwd -S john
john L 02/05/2025 0 99999 7 -1  # L = Locked

$ sudo usermod -U john          # Unlock account
$ sudo passwd -S john
john P 02/05/2025 0 99999 7 -1  # P = Password set (active)
```

**Explanation**: Locking adds a `!` prefix to the password hash in `/etc/shadow`, preventing login. The account still exists but can't authenticate.

### Change username

```bash
$ sudo usermod -l john_new john
```

---

## 5.5 `userdel` — Delete Users

### Delete user (keep home directory)

```bash
$ sudo userdel john
```

### Delete user and home directory

```bash
$ sudo userdel -r john
```

**Explanation**: `-r` removes the home directory and mail spool. Without it, orphaned files remain on disk.

### Safe deletion workflow

```bash
# 1. Check what the user owns
$ sudo find / -user john 2>/dev/null
/home/john
/home/john/.bashrc
/tmp/john_session

# 2. Backup if needed
$ sudo tar czf /backup/john_home.tar.gz /home/john

# 3. Delete
$ sudo userdel -r john

# 4. Clean up orphaned files
$ sudo find / -nouser -exec ls -l {} \; 2>/dev/null
```

---

## 5.6 Group Management

### Create a group

```bash
$ sudo groupadd developers
$ grep developers /etc/group
developers:x:1002:
```

### Create a group with `addgroup` (Debian/Ubuntu)

```bash
$ sudo addgroup devops-team
Adding group `devops-team' (GID 1003) ...
Done.

$ grep devops-team /etc/group
devops-team:x:1003:
```

**Explanation**: `addgroup` is a Debian/Ubuntu-specific wrapper around `groupadd`. It provides friendlier output and automatically assigns the next available GID. On RHEL/CentOS, use `groupadd` instead.

```bash
# Add a user to a group with addgroup (Debian/Ubuntu)
$ sudo addgroup john devops-team
Adding user `john' to group `devops-team' ...
Done.
```

**Explanation**: `addgroup username groupname` adds an existing user to a group. This is equivalent to `usermod -aG devops-team john`.

### `groupadd` vs `addgroup`

| Feature      | `groupadd`                    | `addgroup`                     |
|--------------|-------------------------------|--------------------------------|
| Availability | All Linux distros             | Debian/Ubuntu only             |
| Output       | Silent on success             | Friendly confirmation messages |
| Scripting    | Preferred for portability     | Preferred on Debian/Ubuntu     |
| Options      | `-g` (GID), `-r` (system)    | `--gid`, `--system`            |

**Industry use case**: In Dockerfiles and automation scripts targeting Debian/Ubuntu, `addgroup` is commonly used because it's simpler. For cross-distro scripts, `groupadd` is preferred.

### Create a group with specific GID

```bash
$ sudo groupadd -g 5000 devops-team
```

### Add users to a group

```bash
$ sudo usermod -aG developers john
$ sudo usermod -aG developers sarah
$ grep developers /etc/group
developers:x:1002:john,sarah
```

### Remove a user from a group

```bash
$ sudo gpasswd -d john developers
Removing user john from group developers
```

### Delete a group

```bash
$ sudo groupdel developers
```

**Explanation**: You can't delete a group that is any user's primary group. Change the user's primary group first.

### List all groups for a user

```bash
$ groups devops
devops : devops sudo docker developers
```

---

## 5.7 `su` — Switch User

### Switch to another user

```bash
$ su john
Password: ********
john@server:/home/devops$
```

**Explanation**: Switches to `john` but stays in the current directory and keeps the original environment.

### Switch with full login environment (`-` or `-l`)

```bash
$ su - john
Password: ********
john@server:~$
```

**Explanation**: `su -` simulates a full login. Changes to john's home directory, loads john's environment variables, `.bashrc`, etc. This is the preferred way.

### Switch to root

```bash
$ su -
Password: ********
root@server:~#
```

**Explanation**: `su -` without a username switches to root. Notice the prompt changes from `$` to `#`.

### `su root` vs `su - root`

```bash
$ pwd
/home/devops/projects

$ su root
Password: ********
root@server:/home/devops/projects# pwd
/home/devops/projects

$ su - root
Password: ********
root@server:~# pwd
/root
```

**Explanation**:
- `su root` switches user but keeps the current directory and much of the current shell environment.
- `su - root` performs a full root login, moves to `/root`, and loads root's login environment. This is the recommended form for admin work.

### Run a single command as another user

```bash
$ su - john -c "whoami"
john
```

---

## 5.8 `sudo` — Execute as Superuser

### Run a command as root

```bash
$ sudo apt update
[sudo] password for devops:
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
...
```

**Explanation**: `sudo` runs the command with root privileges. It asks for **your** password (not root's). After authenticating, there's a grace period (usually 15 minutes) before it asks again.

### Run as a specific user

```bash
$ sudo -u postgres psql
psql (15.4)
postgres=#
```

**Explanation**: `-u postgres` runs the command as the `postgres` user. Common for database administration.

### `sudo` vs `su` (sudo vs su)

- `sudo` = run one command with elevated privileges (auditable, least privilege)
- `su` = switch to another user (often root) and start a full shell session

```bash
# One privileged command (recommended for most admin tasks)
$ sudo ls /root

# Full root session
$ su - root
Password: ********
root@server:~#
```

**Best practice**: Prefer `sudo` for day-to-day administration because it is safer and provides a clear audit trail.

### Open a root shell

```bash
$ sudo -i
root@server:~#

$ sudo -s
root@server:/home/devops#
```

**Explanation**: `-i` opens a login shell as root (like `su -`). `-s` opens a shell but keeps the current directory.

### Check sudo privileges

```bash
$ sudo -l
User devops may run the following commands on server:
    (ALL : ALL) ALL
```

**Explanation**: Lists what commands the current user can run with sudo.

### Edit the sudoers file safely

```bash
$ sudo visudo
```

**Explanation**: `visudo` opens `/etc/sudoers` in an editor with syntax checking. Never edit `/etc/sudoers` directly — a syntax error can lock you out of sudo.

### Sudoers file examples

```bash
# Give full sudo access to a user
devops  ALL=(ALL:ALL) ALL

# Allow a user to run specific commands without password
deploy  ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx, /usr/bin/systemctl restart myapp

# Give a group sudo access
%developers ALL=(ALL:ALL) ALL

# Allow a user to run commands as a specific user
dbadmin ALL=(postgres) ALL
```

**Explanation**:
- `ALL=(ALL:ALL) ALL` — from any host, as any user:group, run any command
- `NOPASSWD:` — don't require password for specified commands
- `%developers` — the `%` prefix means it's a group, not a user

### Add sudo access via drop-in file (preferred)

```bash
$ sudo visudo -f /etc/sudoers.d/deploy
# Add:
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
```

**Explanation**: Drop-in files in `/etc/sudoers.d/` are cleaner than editing the main sudoers file. They're included automatically.

---

## 5.9 Password Management

### Change your own password

```bash
$ passwd
Changing password for devops.
Current password: ********
New password: ********
Retype new password: ********
passwd: password updated successfully
```

### Change another user's password (as root)

```bash
$ sudo passwd john
New password: ********
Retype new password: ********
passwd: password updated successfully
```

### Force password change on next login

```bash
$ sudo passwd -e john
passwd: password expiry information changed.
```

**Explanation**: `-e` expires the password immediately. John must set a new password at next login.

### Password aging with `chage`

```bash
$ sudo chage -l devops
Last password change                    : Feb 05, 2025
Password expires                        : May 06, 2025
Password inactive                       : never
Account expires                         : never
Minimum number of days between password change : 0
Maximum number of days between password change : 90
Number of days of warning before password expires : 7
```

```bash
# Set password to expire every 90 days
$ sudo chage -M 90 devops

# Set minimum days between changes
$ sudo chage -m 7 devops

# Set warning days before expiry
$ sudo chage -W 14 devops

# Set account expiration
$ sudo chage -E 2025-12-31 contractor
```

---

## 5.10 Practical DevOps Scenarios

### Scenario 1: Onboard a new developer

```bash
# Create user with proper groups
$ sudo useradd -m -s /bin/bash -c "Jane Doe" -G developers,docker jane

# Set temporary password
$ sudo passwd jane

# Force password change on first login
$ sudo passwd -e jane

# Set up SSH key access
$ sudo mkdir -p /home/jane/.ssh
$ sudo cp /tmp/jane_pubkey.pub /home/jane/.ssh/authorized_keys
$ sudo chown -R jane:jane /home/jane/.ssh
$ sudo chmod 700 /home/jane/.ssh
$ sudo chmod 600 /home/jane/.ssh/authorized_keys
```

### Scenario 2: Create a service account

```bash
# Create system user for running an application
$ sudo useradd -r -s /usr/sbin/nologin -d /opt/myapp -c "MyApp Service" myapp
$ sudo mkdir -p /opt/myapp/{bin,config,logs}
$ sudo chown -R myapp:myapp /opt/myapp
```

### Scenario 3: Offboard a user

```bash
# Lock the account immediately
$ sudo usermod -L jane

# Check for running processes
$ sudo ps -u jane
  PID TTY          TIME CMD
 5678 pts/1    00:00:00 bash
 5690 pts/1    00:00:05 python3

# Kill all processes
$ sudo pkill -u jane

# Backup home directory
$ sudo tar czf /backup/jane_$(date +%Y%m%d).tar.gz /home/jane

# Remove user and home
$ sudo userdel -r jane

# Remove from sudoers if applicable
$ sudo rm -f /etc/sudoers.d/jane
```

### Scenario 4: Grant limited sudo access for CI/CD

```bash
$ sudo visudo -f /etc/sudoers.d/cicd
# Content:
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart myapp
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker pull *
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker-compose up -d
```

---

## 5.11 Addon Commands

### `finger` — User information lookup

```bash
$ finger devops
Login: devops                           Name: DevOps User
Directory: /home/devops                 Shell: /bin/bash
On since Wed Feb  5 10:00 (UTC) on pts/0 from 10.0.0.5
   5 minutes idle
Mail last read Wed Feb  5 14:00 2025
No Plan.
```

**Explanation**: `finger` shows user details, login status, and idle time. Install with `sudo apt install finger`.

### `chfn` — Change user information

```bash
$ sudo chfn devops
Changing the user information for devops
Enter the new value, or press ENTER for the default
        Full Name [DevOps User]: DevOps Engineer
        Room Number []: 301
        Work Phone []: 555-1234
        Home Phone []:

$ grep devops /etc/passwd
devops:x:1000:1000:DevOps Engineer,301,555-1234,:/home/devops:/bin/bash
```

### `getent` — Query user/group databases

```bash
# Look up a user (works with LDAP/NIS too)
$ getent passwd devops
devops:x:1000:1000:DevOps User:/home/devops:/bin/bash

# Look up a group
$ getent group docker
docker:x:999:devops,john

# List all users with UID >= 1000 (real users, not system accounts)
$ getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1, $3, $7}'
devops 1000 /bin/bash
john 1001 /bin/bash
```

### `loginctl` — Manage user sessions (systemd)

```bash
$ loginctl list-sessions
SESSION  UID USER   SEAT  TTY
      1 1000 devops       pts/0
      2 1001 john         pts/1

$ loginctl show-session 1
Id=1
User=1000
Name=devops
State=active
Remote=yes
RemoteHost=10.0.0.5

# Terminate a user's session
$ sudo loginctl terminate-session 2
```

---

## 5.12 Troubleshooting User & Access Issues

### Scenario: User can't log in via SSH

```bash
# Step 1: Check if account is locked
$ sudo passwd -S john
john L 02/05/2025 0 99999 7 -1
# L = Locked

# Fix: unlock
$ sudo usermod -U john

# Step 2: Check if shell is valid
$ grep john /etc/passwd
john:x:1001:1001::/home/john:/usr/sbin/nologin
# nologin shell prevents login

# Fix: set a valid shell
$ sudo usermod -s /bin/bash john

# Step 3: Check SSH key permissions
$ ls -la /home/john/.ssh/
-rw-rw-r-- 1 john john 400 Feb  5 10:00 authorized_keys
# Too open — SSH requires strict permissions

# Fix
$ chmod 700 /home/john/.ssh
$ chmod 600 /home/john/.ssh/authorized_keys

# Step 4: Check SSH logs
$ sudo tail -20 /var/log/auth.log | grep john
Feb  5 15:00:00 server sshd[4567]: Authentication refused: bad ownership or modes for file /home/john/.ssh/authorized_keys
```

### Scenario: "user is not in the sudoers file"

```bash
$ sudo apt update
john is not in the sudoers file. This incident will be reported.

# Fix: add user to sudo group
$ su -          # Switch to root
$ usermod -aG sudo john    # Debian/Ubuntu
$ usermod -aG wheel john   # RHEL/CentOS

# User must log out and back in for group change to take effect
$ su - john
$ sudo whoami
root
```

### Scenario: Accidentally removed user from all groups

```bash
# WRONG: this removes john from ALL supplementary groups
$ sudo usermod -G docker john

# Check damage
$ id john
uid=1001(john) gid=1001(john) groups=1001(john),999(docker)
# Lost sudo, developers, etc.

# Fix: add back to all needed groups
$ sudo usermod -aG sudo,docker,developers john
```

### Scenario: Find who ran a specific command

```bash
# Check sudo log
$ sudo grep "COMMAND" /var/log/auth.log | tail -10
Feb  5 14:45:10 server sudo: john : TTY=pts/1 ; COMMAND=/bin/rm -rf /opt/myapp/data

# Check bash history for a specific user
$ sudo cat /home/john/.bash_history | grep "rm"

# Check last logins
$ last john
john  pts/1  10.0.0.10  Wed Feb  5 11:30   still logged in
john  pts/0  10.0.0.10  Tue Feb  4 09:00 - 18:30  (09:30)
```

---


## Summary

| Command     | Purpose                    | Key Flags                          |
|-------------|----------------------------|------------------------------------|
| `useradd`   | Create user                | `-m`, `-s`, `-G`, `-r`             |
| `usermod`   | Modify user                | `-aG`, `-s`, `-L`, `-U`            |
| `userdel`   | Delete user                | `-r` (remove home)                 |
| `passwd`    | Set/change password        | `-e` (expire), `-S` (status)       |
| `groupadd`  | Create group               | `-g` (specify GID)                 |
| `groupdel`  | Delete group               | —                                  |
| `gpasswd`   | Manage group members       | `-d` (remove member)               |
| `su`        | Switch user                | `-` (full login)                   |
| `sudo`      | Run as superuser           | `-u`, `-i`, `-l`                   |
| `chage`     | Password aging             | `-l`, `-M`, `-E`                   |
| `id`        | Show user/group IDs        | —                                  |
| `who` / `w` | Show logged-in users       | —                                  |

**Next Module**: [06 - Process Management](../06-process-management/README.md)

---
## 5.13 PAM — Pluggable Authentication Modules

PAM controls how authentication works in Linux: login, SSH, sudo, password policies, and account lockout.

### How PAM Works

PAM configuration files are in `/etc/pam.d/`. Each service (login, sshd, sudo) has its own config.

```bash
# View PAM config for SSH
cat /etc/pam.d/sshd

# View PAM config for sudo
cat /etc/pam.d/sudo
```

### PAM Module Types

| Type | Purpose |
|------|---------|
| `auth` | Verify user identity (password, token) |
| `account` | Check account validity (expiry, access) |
| `password` | Manage password changes |
| `session` | Setup/teardown user sessions |

### Enforce Password Complexity

Install and configure `pam_pwquality`:

```bash
# Install
sudo apt install libpam-pwquality    # Debian/Ubuntu

# Edit password requirements
sudo vi /etc/security/pwquality.conf
```

```
# Minimum password length
minlen = 12
# Require at least 1 digit
dcredit = -1
# Require at least 1 uppercase
ucredit = -1
# Require at least 1 special character
ocredit = -1
# Reject passwords containing username
usercheck = 1
```

### Lock Account After Failed Login Attempts

Edit `/etc/pam.d/common-auth` (Debian) or `/etc/pam.d/system-auth` (RHEL):

```
auth required pam_faillock.so deny=5 unlock_time=300 fail_interval=900
```

This locks the account for 5 minutes after 5 failed attempts within 15 minutes.

```bash
# Check failed attempts for a user
faillock --user john

# Unlock a locked account
sudo faillock --user john --reset
```

### Real-world use cases

| Scenario | PAM Module |
|----------|-----------|
| Enforce strong passwords | `pam_pwquality` |
| Lock after failed logins | `pam_faillock` |
| Restrict login by time | `pam_time` |
| Restrict login by group | `pam_access` |
| Two-factor authentication | `pam_google_authenticator` |

---

## 5.14 The /etc/skel Directory

When creating a user with `useradd -m`, files from `/etc/skel` are copied into the new user's home directory.

```bash
# View default skeleton files
ls -la /etc/skel/
# .bashrc  .profile  .bash_logout

# Customize defaults for all new users
sudo cp custom_bashrc /etc/skel/.bashrc
sudo cp custom_vimrc /etc/skel/.vimrc

# Add a welcome message
echo "Welcome to the server!" | sudo tee /etc/skel/.welcome

# New users will get these files automatically
sudo useradd -m newuser
ls -la /home/newuser/
```

Use this to set default aliases, PS1 prompts, environment variables, or SSH configs for all new users.

---

## 5.15 Interview Questions — Module 5

**Q1: What is the difference between `/etc/passwd` and `/etc/shadow`?**

`/etc/passwd` stores user account info (username, UID, GID, home, shell) — readable by all users. `/etc/shadow` stores encrypted passwords and aging info — readable only by root. This separation prevents non-root users from accessing password hashes.

**Q2: How do you create a system user vs a regular user?**

```bash
useradd -r -s /sbin/nologin nginx    # System user (no login, low UID)
useradd -m -s /bin/bash john          # Regular user (home dir, login shell)
```

System users (UID < 1000) run services. Regular users (UID >= 1000) are interactive humans.

**Q3: What is PAM and why is it important?**

PAM (Pluggable Authentication Modules) controls authentication for all Linux services — login, SSH, sudo, password changes. It enforces password complexity (`pam_pwquality`), account lockout (`pam_faillock`), and access restrictions (`pam_access`).

**Q4: How do you grant a user sudo access for specific commands only?**

```bash
sudo visudo
# Add: deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
```

This allows user `deploy` to restart nginx without a password, but nothing else.

**Q5: What happens when you delete a user with `userdel` vs `userdel -r`?**

`userdel` removes the user account but leaves the home directory and mail spool. `userdel -r` removes the account AND deletes the home directory and mail. Always check for running processes (`ps -u username`) before deleting.

**Q6: How do you lock and unlock a user account?**

```bash
usermod -L username          # Lock (prepends ! to password hash)
usermod -U username          # Unlock
passwd -l username           # Alternative lock
passwd -u username           # Alternative unlock
chage -E 0 username          # Expire account immediately
```
