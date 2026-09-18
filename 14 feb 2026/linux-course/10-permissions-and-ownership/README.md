# Module 4: File Permissions & Ownership

## 4.1 Understanding Linux Permissions

Every file and directory in Linux has three attributes:
- **Owner** (user) — the user who owns the file
- **Group** — the group associated with the file
- **Permissions** — what actions owner, group, and others can perform

### Reading Permission Strings

```bash
$ ls -l deploy.sh
-rwxr-xr-- 1 devops developers 245 Feb  5 11:00 deploy.sh
```

Breaking down `-rwxr-xr--`:

```
-  rwx  r-x  r--
│  │    │    │
│  │    │    └── Others (everyone else): read only
│  │    └── Group (developers): read + execute
│  └── Owner (devops): read + write + execute
└── File type: - = regular file, d = directory, l = symlink
```

### Permission Bits

| Symbol | Permission | On Files              | On Directories                    |
|--------|------------|-----------------------|-----------------------------------|
| `r`    | Read       | View file contents    | List directory contents (`ls`)    |
| `w`    | Write      | Modify file contents  | Create/delete files in directory  |
| `x`    | Execute    | Run as a program      | Enter directory (`cd`)            |
| `-`    | None       | Permission denied     | Permission denied                 |

### Numeric (Octal) Representation

Each permission has a numeric value:

```
r = 4    w = 2    x = 1    - = 0
```

Add them up for each category:

```
rwx = 4+2+1 = 7    (full access)
r-x = 4+0+1 = 5    (read + execute)
r-- = 4+0+0 = 4    (read only)
rw- = 4+2+0 = 6    (read + write)
--- = 0+0+0 = 0    (no access)
```

### Common Permission Patterns

| Numeric | Symbolic      | Meaning                                    | Use Case                    |
|---------|---------------|--------------------------------------------|-----------------------------|
| `755`   | `rwxr-xr-x`  | Owner: full, Others: read+execute          | Scripts, directories        |
| `644`   | `rw-r--r--`  | Owner: read+write, Others: read            | Regular files, configs      |
| `700`   | `rwx------`  | Owner only: full access                    | Private scripts, `.ssh/`    |
| `600`   | `rw-------`  | Owner only: read+write                     | SSH keys, secrets           |
| `777`   | `rwxrwxrwx`  | Everyone: full access                      | ⚠️ Security risk, avoid     |
| `400`   | `r--------`  | Owner: read only                           | SSH private keys            |

---

## 4.2 `chmod` — Change Permissions

### Numeric mode

```bash
$ ls -l script.sh
-rw-r--r-- 1 devops devops 245 Feb  5 11:00 script.sh

$ chmod 755 script.sh
$ ls -l script.sh
-rwxr-xr-x 1 devops devops 245 Feb  5 11:00 script.sh
```

**Explanation**: Changed from `644` (rw-r--r--) to `755` (rwxr-xr-x). The owner can now execute the script, and group/others can read and execute it.

### Symbolic mode

Syntax: `chmod [who][operator][permission] file`

- **Who**: `u` (user/owner), `g` (group), `o` (others), `a` (all)
- **Operator**: `+` (add), `-` (remove), `=` (set exactly)
- **Permission**: `r`, `w`, `x`

```bash
# Add execute permission for the owner
$ chmod u+x script.sh
$ ls -l script.sh
-rwxr--r-- 1 devops devops 245 Feb  5 11:00 script.sh
```

**Explanation**: `u+x` adds execute (`x`) for the user/owner (`u`). Other permissions unchanged.

```bash
# Remove write permission from group and others
$ chmod go-w config.yaml
$ ls -l config.yaml
-rw-r--r-- 1 devops devops 512 Feb  5 11:00 config.yaml
```

**Explanation**: `go-w` removes write (`w`) from group (`g`) and others (`o`).

```bash
# Set exact permissions for all
$ chmod a=r secret.key
$ ls -l secret.key
-r--r--r-- 1 devops devops 1024 Feb  5 11:00 secret.key
```

**Explanation**: `a=r` sets all categories to read-only. Any existing write or execute permissions are removed.

```bash
# Add execute for everyone
$ chmod +x deploy.sh
$ ls -l deploy.sh
-rwxr-xr-x 1 devops devops 245 Feb  5 11:00 deploy.sh
```

**Explanation**: Without specifying who, `+x` adds execute for all (user, group, others).

### `chmod 777` — Full permissions for everyone

```bash
$ chmod 777 file.txt
$ ls -l file.txt
-rwxrwxrwx 1 devops devops 1024 Feb  5 11:00 file.txt
```

**Explanation**: `777` gives read, write, and execute permissions to the owner, group, and everyone else. Breaking it down:
- `7` (owner) = `r(4) + w(2) + x(1)` = read + write + execute
- `7` (group) = `r(4) + w(2) + x(1)` = read + write + execute
- `7` (others) = `r(4) + w(2) + x(1)` = read + write + execute

> ⚠️ **Security risk**: `chmod 777` is almost never appropriate in production. It means any user on the system can read, modify, and execute the file. This is a common finding in security audits and penetration tests.

```bash
# Find all 777 files on the system (security audit)
$ find / -type f -perm 777 2>/dev/null
/tmp/insecure_script.sh
/var/www/html/uploads/user_file.php

# Fix: set appropriate permissions instead
$ chmod 644 file.txt      # Owner read/write, others read-only
$ chmod 755 script.sh     # Owner full, others read/execute
```

**When 777 might be used (rare)**:
- Quick temporary debugging in a non-production environment
- Shared `/tmp` directories (which already have the sticky bit for protection)

**Real-life example**: A junior engineer sets `chmod 777` on a web upload directory to fix a "permission denied" error. This allows any user to upload and execute files — a serious security vulnerability. The correct fix is `chmod 755` with proper ownership: `chown www-data:www-data /var/www/uploads`.

### Recursive permissions (`-R`)

```bash
$ chmod -R 755 /opt/myapp/
```

**Explanation**: `-R` applies permissions recursively to all files and subdirectories. Use with caution — you usually want different permissions for files (644) and directories (755).

### Set different permissions for files and directories

```bash
# Set directories to 755
$ find /opt/myapp -type d -exec chmod 755 {} \;

# Set files to 644
$ find /opt/myapp -type f -exec chmod 644 {} \;

# Set scripts to 755
$ find /opt/myapp -type f -name "*.sh" -exec chmod 755 {} \;
```

**Explanation**: This is the correct way to set permissions recursively. Directories need `x` (execute) to be entered with `cd`. Files generally don't need execute unless they're scripts.

### Copy permissions from another file

```bash
$ chmod --reference=working_script.sh new_script.sh
$ ls -l new_script.sh
-rwxr-xr-x 1 devops devops 500 Feb  5 15:00 new_script.sh
```

### View permissions in octal

```bash
$ stat -c '%a %n' /etc/nginx/nginx.conf
644 /etc/nginx/nginx.conf

# Check permissions of all files in a directory
$ stat -c '%a %U:%G %n' /opt/myapp/*
755 myapp:myapp /opt/myapp/bin
644 myapp:myapp /opt/myapp/config.yaml
755 myapp:myapp /opt/myapp/start.sh
```

---

## 4.3 `chown` — Change Ownership

### Change owner

```bash
$ ls -l app.conf
-rw-r--r-- 1 devops devops 512 Feb  5 11:00 app.conf

$ sudo chown nginx app.conf
$ ls -l app.conf
-rw-r--r-- 1 nginx devops 512 Feb  5 11:00 app.conf
```

**Explanation**: Changed the owner from `devops` to `nginx`. Only root (via `sudo`) can change file ownership.

### Change owner and group

```bash
$ sudo chown nginx:www-data app.conf
$ ls -l app.conf
-rw-r--r-- 1 nginx www-data 512 Feb  5 11:00 app.conf
```

**Explanation**: `nginx:www-data` sets owner to `nginx` and group to `www-data`. The colon separates owner and group.

### Change group only

```bash
$ sudo chown :developers project/
$ ls -ld project/
drwxr-xr-x 2 devops developers 4096 Feb  5 11:00 project/
```

**Explanation**: `:developers` changes only the group, leaving the owner unchanged.

### Report changes (`-c`)

```bash
$ sudo chown -c root file1.txt
changed ownership of 'file1.txt' from devops to root

$ sudo chown -c root file1.txt
                                    # No output — ownership already correct
```

**Explanation**: `-c` (like `--changes`) reports only when a change is actually made. If the file already has the specified owner, it produces no output. This is useful in scripts to see what was actually modified.

```bash
# Verbose mode shows every file, even unchanged ones
$ sudo chown -v root file1.txt file2.txt
ownership of 'file1.txt' retained as root
changed ownership of 'file2.txt' from devops to root
```

**Explanation**: `-v` (verbose) reports on every file. `-c` only reports actual changes — less noisy for large operations.

**Industry use case**: When running `chown` across hundreds of files in a deployment script, `-c` lets you see only the files that were actually changed, making it easy to audit what happened.

**Real-life example**: After deploying a new version of a web app, you run `sudo chown -cR www-data:www-data /var/www/html/` to fix ownership. The `-c` flag shows you exactly which new files had their ownership corrected.

### Change owner to root

```bash
$ ls -l /etc/myapp/config.yml
-rw-r--r-- 1 devops devops 2048 Feb  5 11:00 /etc/myapp/config.yml

$ sudo chown root /etc/myapp/config.yml
$ ls -l /etc/myapp/config.yml
-rw-r--r-- 1 root devops 2048 Feb  5 11:00 /etc/myapp/config.yml
```

**Explanation**: Changes the owner to `root` while keeping the group unchanged. Only root can modify the file now (assuming `644` permissions). This is standard for sensitive config files that should not be editable by regular users.

**Real-life example**: After editing `/etc/nginx/nginx.conf` as a regular user, you change ownership back to root so that only privileged users can modify it: `sudo chown root /etc/nginx/nginx.conf`.

### Change owner and group together

```bash
$ sudo chown root:devops /opt/app/config.yml
$ ls -l /opt/app/config.yml
-rw-r--r-- 1 root devops 2048 Feb  5 11:00 /opt/app/config.yml
```

**Explanation**: Sets owner to `root` and group to `devops` in one command. The `root:devops` syntax uses a colon to separate owner and group. This pattern is common when root should own the file but a specific group needs read access.

**Real-life example**: Application config files are often owned by `root:appgroup` with `640` permissions — root can read/write, the application group can read, and others have no access.

### Recursive ownership change (`-R`)

```bash
$ sudo chown -R www-data:www-data /var/www/html/
```

**Explanation**: Changes owner and group for `/var/www/html/` and all its contents. Common when setting up web server document roots.

```bash
# Change ownership of an entire application directory to root
$ sudo chown -R root:devops /opt/myapp/
$ ls -l /opt/myapp/
total 12
drwxr-xr-x 2 root devops 4096 Feb  5 11:00 bin
drwxr-xr-x 2 root devops 4096 Feb  5 11:00 config
drwxr-xr-x 2 root devops 4096 Feb  5 11:00 logs
```

**Explanation**: `-R` applies the ownership change recursively to the directory and everything inside it. Here, `root` owns all files and directories, and the `devops` group has group-level access.

**Real-life example**: After deploying an application to `/opt/myapp/`, you run `sudo chown -R root:appgroup /opt/myapp/` to ensure root owns the files (preventing unauthorized modification) while the application's service account (in `appgroup`) can still read them.

---

## 4.4 `chgrp` — Change Group

### Change group on a file

```bash
$ ls -l report.txt
-rw-r--r-- 1 devops devops 1024 Feb  5 11:00 report.txt

$ sudo chgrp developers report.txt
$ ls -l report.txt
-rw-r--r-- 1 devops developers 1024 Feb  5 11:00 report.txt
```

**Explanation**: `chgrp` changes only the group. Equivalent to `chown :developers report.txt`.

### Change group on a directory

```bash
$ ls -ld /opt/myapp/
drwxr-xr-x 4 root root 4096 Feb  5 11:00 /opt/myapp/

$ sudo chgrp developers /opt/myapp/
$ ls -ld /opt/myapp/
drwxr-xr-x 4 root developers 4096 Feb  5 11:00 /opt/myapp/
```

**Explanation**: `chgrp` works on directories the same way as files. Only the directory itself is changed — files inside are not affected.

**Industry use case**: When setting up a shared project directory, you change the group to the team's group so all members can access it. Combined with SGID (`chmod g+s`), new files inside will inherit the group automatically.

### Recursive group change (`-R`)

```bash
$ sudo chgrp -R developers /opt/myapp/
$ ls -l /opt/myapp/
-rw-r--r-- 1 root developers  512 Feb  5 11:00 config.yaml
-rwxr-xr-x 1 root developers  245 Feb  5 11:00 start.sh
drwxr-xr-x 2 root developers 4096 Feb  5 11:00 logs/
```

**Explanation**: `-R` (recursive) changes the group for the directory and **all files and subdirectories** inside it. Without `-R`, only the top-level directory is changed.

```bash
# Verify the recursive change
$ find /opt/myapp/ -exec stat -c '%n %G' {} \;
/opt/myapp/ developers
/opt/myapp/config.yaml developers
/opt/myapp/start.sh developers
/opt/myapp/logs/ developers
/opt/myapp/logs/app.log developers
```

**Real-life example**: A new team takes over a project. You run `sudo chgrp -R newteam /opt/project/` to transfer group ownership of all project files at once, then set `chmod 2775` on the directory so new files inherit the group.

---

## 4.5 `umask` — Default Permission Mask

When you create a file or directory, the permissions are determined by subtracting the `umask` from the maximum permissions.

- Maximum for files: `666` (no execute by default for safety)
- Maximum for directories: `777`

### Check current umask

```bash
$ umask
0022

$ umask -S
u=rwx,g=rx,o=rx
```

**Explanation**: The umask `0022` means:
- Files created with: `666 - 022 = 644` (rw-r--r--)
- Directories created with: `777 - 022 = 755` (rwxr-xr-x)

### Verify with file creation

```bash
$ touch newfile.txt
$ mkdir newdir
$ ls -l
-rw-r--r-- 1 devops devops    0 Feb  5 15:00 newfile.txt
drwxr-xr-x 2 devops devops 4096 Feb  5 15:00 newdir
```

**Explanation**: Confirms the umask calculation. `newfile.txt` got `644`, `newdir` got `755`.

### Set a more restrictive umask

```bash
$ umask 0077
$ touch private.txt
$ mkdir private_dir
$ ls -l
-rw------- 1 devops devops    0 Feb  5 15:05 private.txt
drwx------ 2 devops devops 4096 Feb  5 15:05 private_dir
```

**Explanation**: `umask 0077` means:
- Files: `666 - 077 = 600` (rw-------)
- Directories: `777 - 077 = 700` (rwx------)

Only the owner can access these files. Useful for sensitive environments.

### Common umask values

| umask  | File Permissions | Directory Permissions | Use Case                |
|--------|------------------|-----------------------|-------------------------|
| `0022` | `644` (rw-r--r--)| `755` (rwxr-xr-x)    | Default, shared systems |
| `0027` | `640` (rw-r-----)| `750` (rwxr-x---)    | Group collaboration     |
| `0077` | `600` (rw-------)| `700` (rwx------)    | Private/secure          |
| `0002` | `664` (rw-rw-r--)| `775` (rwxrwxr-x)    | Group-writable projects |

### Make umask persistent

```bash
# Add to ~/.bashrc or ~/.profile
$ echo "umask 0027" >> ~/.bashrc
$ source ~/.bashrc
```

---

## 4.6 Special Permissions

### SUID (Set User ID) — `4`

When set on an executable, it runs with the **owner's** permissions, not the caller's.

```bash
$ ls -l /usr/bin/passwd
-rwsr-xr-x 1 root root 68208 Feb  5 11:00 /usr/bin/passwd
```

**Explanation**: The `s` in the owner's execute position means SUID is set. `passwd` is owned by root, so any user running it temporarily gets root privileges — necessary because `passwd` needs to write to `/etc/shadow`.

```bash
# Set SUID
$ chmod u+s program
$ chmod 4755 program

# Remove SUID
$ chmod u-s program
```

### SGID (Set Group ID) — `2`

On files: runs with the group's permissions.
On directories: new files inherit the directory's group.

```bash
$ ls -ld /shared/project/
drwxrwsr-x 2 root developers 4096 Feb  5 11:00 /shared/project/
```

**Explanation**: The `s` in the group's execute position means SGID. Any file created inside `/shared/project/` will automatically belong to the `developers` group, regardless of who creates it.

```bash
# Set SGID on a directory
$ chmod g+s /shared/project/
$ chmod 2775 /shared/project/

# Verify: create a file inside
$ touch /shared/project/newfile.txt
$ ls -l /shared/project/newfile.txt
-rw-r--r-- 1 devops developers 0 Feb  5 15:00 newfile.txt
```

**Explanation**: Even though `devops` created the file, the group is `developers` (inherited from the directory).

### Sticky Bit — `1`

On directories: only the file owner (or root) can delete files, even if others have write permission.

```bash
$ ls -ld /tmp
drwxrwxrwt 15 root root 4096 Feb  5 15:00 /tmp
```

**Explanation**: The `t` in the others' execute position is the sticky bit. `/tmp` is world-writable (`777`), but the sticky bit prevents users from deleting each other's files.

```bash
# Set sticky bit
$ chmod +t /shared/
$ chmod 1777 /shared/

# Verify
$ ls -ld /shared/
drwxrwxrwt 2 root root 4096 Feb  5 15:00 /shared/
```

### Special Permissions Summary

| Permission  | Numeric | Symbol | On Files                    | On Directories                  |
|-------------|---------|--------|-----------------------------|---------------------------------|
| SUID        | `4xxx`  | `s`    | Run as file owner           | (no effect)                     |
| SGID        | `2xxx`  | `s`    | Run as file group           | New files inherit group         |
| Sticky Bit  | `1xxx`  | `t`    | (no effect)                 | Only owner can delete files     |

---

## 4.7 Finding Permission Issues

### Find world-writable files (security audit)

```bash
$ find / -type f -perm -o=w 2>/dev/null
/tmp/debug.log
/var/tmp/cache.dat
```

**Explanation**: `-perm -o=w` finds files where others have write permission. These are potential security risks.

### Find SUID files

```bash
$ find / -type f -perm -u=s 2>/dev/null
/usr/bin/passwd
/usr/bin/sudo
/usr/bin/su
/usr/bin/newgrp
```

**Explanation**: Lists all SUID binaries. Unexpected SUID files could indicate a security breach.

### Find files with no owner

```bash
$ find / -nouser -o -nogroup 2>/dev/null
/home/olduser/leftover.txt
```

**Explanation**: Files without a valid owner or group usually belong to deleted users. These should be reassigned or removed.

---

## 4.8 Access Control Lists (ACLs)

ACLs provide fine-grained permissions beyond the standard owner/group/others model.

### View ACLs

```bash
$ getfacl project/
# file: project/
# owner: devops
# group: devops
user::rwx
group::r-x
other::r-x
```

### Set ACL for a specific user

```bash
$ setfacl -m u:john:rwx project/
$ getfacl project/
# file: project/
# owner: devops
# group: devops
user::rwx
user:john:rwx
group::r-x
mask::rwx
other::r-x
```

**Explanation**: `-m` modifies the ACL. `u:john:rwx` gives user `john` full access to `project/`, without changing permissions for anyone else.

### Set ACL for a group

```bash
$ setfacl -m g:qa:rx project/
```

**Explanation**: Gives the `qa` group read and execute access.

### Set default ACL (inherited by new files)

```bash
$ setfacl -d -m u:john:rwx project/
```

**Explanation**: `-d` sets a default ACL. New files created inside `project/` will automatically grant `john` rwx access.

### Remove ACLs

```bash
$ setfacl -x u:john project/     # Remove specific ACL
$ setfacl -b project/             # Remove all ACLs
```

### Check if a file has ACLs

```bash
$ ls -l project/
drwxrwxr-x+ 2 devops devops 4096 Feb  5 15:00 project/
```

**Explanation**: The `+` at the end of the permission string indicates ACLs are set.

---

## 4.9 Practical DevOps Scenarios

### Scenario 1: Secure SSH keys

```bash
$ chmod 700 ~/.ssh
$ chmod 600 ~/.ssh/id_rsa
$ chmod 644 ~/.ssh/id_rsa.pub
$ chmod 644 ~/.ssh/authorized_keys
```

**Explanation**: SSH refuses to work if key permissions are too open. Private key must be `600`, `.ssh` directory must be `700`.

### Scenario 2: Web server document root

```bash
$ sudo chown -R www-data:www-data /var/www/html/
$ sudo find /var/www/html -type d -exec chmod 755 {} \;
$ sudo find /var/www/html -type f -exec chmod 644 {} \;
```

**Explanation**: Web server user (`www-data`) owns the files. Directories are `755` (traversable), files are `644` (readable).

### Scenario 3: Shared project directory

```bash
$ sudo mkdir /shared/project
$ sudo chown :developers /shared/project
$ sudo chmod 2775 /shared/project
```

**Explanation**: SGID (`2`) ensures new files inherit the `developers` group. `775` lets group members create and modify files.

### Scenario 4: Security audit one-liner

```bash
$ find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -l {} \; 2>/dev/null
```

**Explanation**: Finds all SUID (`-4000`) and SGID (`-2000`) files on the system. Run periodically to detect unauthorized privilege escalation binaries.

---

## 4.10 Troubleshooting Permission Issues

### Scenario: "Permission denied" running a script

```bash
$ ./deploy.sh
bash: ./deploy.sh: Permission denied

# Step 1: Check permissions
$ ls -l deploy.sh
-rw-r--r-- 1 devops devops 245 Feb  5 11:00 deploy.sh
# No execute (x) permission

# Step 2: Fix
$ chmod +x deploy.sh
$ ./deploy.sh
# Works now

# Alternative: run with bash directly (no execute permission needed)
$ bash deploy.sh
```

### Scenario: SSH key rejected — "Permissions too open"

```bash
$ ssh -i ~/.ssh/id_rsa server
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for '/home/devops/.ssh/id_rsa' are too open.

# Fix: set correct permissions
$ chmod 700 ~/.ssh
$ chmod 600 ~/.ssh/id_rsa
$ chmod 644 ~/.ssh/id_rsa.pub
$ chmod 644 ~/.ssh/authorized_keys
$ chmod 644 ~/.ssh/known_hosts
```

### Scenario: Web app can't write to upload directory

```bash
$ curl -X POST -F "file=@photo.jpg" http://localhost/upload
{"error": "Permission denied: /var/www/html/uploads"}

# Step 1: Check ownership
$ ls -ld /var/www/html/uploads
drwxr-xr-x 2 root root 4096 Feb  5 10:00 /var/www/html/uploads
# Owned by root, but web server runs as www-data

# Step 2: Fix ownership
$ sudo chown www-data:www-data /var/www/html/uploads

# Step 3: Verify
$ ls -ld /var/www/html/uploads
drwxr-xr-x 2 www-data www-data 4096 Feb  5 10:00 /var/www/html/uploads
```

### Scenario: User can't access a directory even with correct permissions

```bash
$ ls /opt/myapp/config/
ls: cannot access '/opt/myapp/config/': Permission denied

# Check the ENTIRE path — every parent directory needs execute (x)
$ namei -l /opt/myapp/config/
f: /opt/myapp/config/
dr-xr-xr-x root   root   /
drwxr-xr-x root   root   opt
drwx------ root   root   myapp      # <-- No access for others!
drwxr-xr-x myapp  myapp  config

# Fix: add execute permission on the parent
$ sudo chmod o+x /opt/myapp
```

**Explanation**: To access any file, you need execute (`x`) permission on EVERY directory in the path. `namei -l` shows permissions for each component.

### Scenario: Find all files owned by a deleted user

```bash
$ sudo find / -nouser -o -nogroup 2>/dev/null
/home/olduser/leftover.txt
/tmp/olduser_session

# Reassign to a valid user
$ sudo chown -R devops:devops /home/olduser/
# Or delete
$ sudo rm -rf /home/olduser/
```

---


## Summary

| Command   | Purpose                    | Key Usage                              |
|-----------|----------------------------|----------------------------------------|
| `chmod`   | Change permissions         | `chmod 755 file`, `chmod u+x file`     |
| `chown`   | Change owner/group         | `chown user:group file`                |
| `chgrp`   | Change group               | `chgrp group file`                     |
| `umask`   | Set default permissions    | `umask 0022`                           |
| `getfacl` | View ACLs                  | `getfacl file`                         |
| `setfacl` | Set ACLs                   | `setfacl -m u:user:rwx file`           |

**Next Module**: [05 - User & Group Management](../05-user-and-group-management/README.md)

---

---

## 4.10 Interview Questions — Module 4

**Q1: Explain Linux file permissions (rwx) and how to read them.**

Every file has three permission sets: owner (u), group (g), others (o). Each set has read (r=4), write (w=2), execute (x=1). Example: `-rwxr-xr--` means owner has rwx (7), group has r-x (5), others have r-- (4) = `754`.

**Q2: What is the difference between chmod symbolic and numeric modes?**

Symbolic: `chmod u+x file` (add execute for user). Numeric: `chmod 755 file` (rwxr-xr-x). Numeric is faster for setting all permissions at once. Symbolic is better for modifying specific bits.

**Q3: What are SUID, SGID, and Sticky Bit?**

- **SUID** (4000): File executes with owner's privileges. Example: `/usr/bin/passwd` runs as root to modify `/etc/shadow`.
- **SGID** (2000): On files, executes with group's privileges. On directories, new files inherit the directory's group.
- **Sticky Bit** (1000): On directories, only the file owner can delete their files. Example: `/tmp`.

```bash
find / -perm -4000 -type f 2>/dev/null    # Find all SUID binaries (security audit)
```

**Q4: What is umask and how does it affect file creation?**

umask defines which permissions are removed from new files/directories. Default file permissions are 666, directories 777. With `umask 022`: files get 644 (666-022), directories get 755 (777-022).

**Q5: When would you use ACLs instead of standard permissions?**

When you need to grant different permissions to multiple specific users or groups on the same file — standard permissions only support one owner and one group. Example: user `alice` needs read access and user `bob` needs read-write access to the same file.

```bash
setfacl -m u:alice:r-- file.txt
setfacl -m u:bob:rw- file.txt
getfacl file.txt
```
