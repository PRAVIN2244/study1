# Module 24: SSH and Remote Server Management

## 12.1 SSH — Secure Shell

### Connect to a remote server

```bash
$ ssh devops@192.168.1.50
devops@192.168.1.50's password: ********
devops@web-server:~$
```

**Explanation**: `ssh username@server` is the most common syntax. Replace `devops` with your username and `192.168.1.50` with the server's IP or hostname.

**Industry use case**: DevOps engineers SSH into cloud servers (AWS EC2, Azure VMs, GCP instances) daily to deploy code, check logs, restart services, and troubleshoot issues.

### Connect using `-l` flag (login name)

```bash
$ ssh 192.168.1.50 -l devops
devops@192.168.1.50's password: ********
devops@web-server:~$
```

**Explanation**: `-l` specifies the login username. `ssh server -l username` is equivalent to `ssh username@server`. Some administrators prefer this syntax for scripting.

```bash
# Connect to an IP address as root
$ ssh 126.195.133.34 -l root
root@126.195.133.34's password: ********
root@prod-db:~#
```

**Explanation**: Connecting as `root` directly is common during initial server setup. In production, root login is typically disabled via `sshd_config` (`PermitRootLogin no`) and you use `sudo` instead.

**Real-life example**: A new cloud VM has only root access. You SSH in as root to create a regular user, set up SSH keys, then disable root login for security.

### Connect on a non-default port (`-p`)

```bash
$ ssh server -l username -p 2222

$ ssh 192.168.1.50 -l devops -p 2222
devops@192.168.1.50's password: ********
devops@web-server:~$
```

**Explanation**: SSH defaults to port `22`. The `-p` flag specifies a custom port. Many organizations change the SSH port to `2222` or another non-standard port to reduce automated brute-force attacks.

```bash
# Equivalent using @ syntax
$ ssh -p 2222 devops@192.168.1.50
```

**Industry use case**: In production environments, security teams often change the default SSH port as part of server hardening. Cloud providers like AWS also allow custom SSH ports via security groups. When connecting through a bastion/jump host, different services may listen on different ports.

**Real-life example**: Your company's security policy requires SSH on port 2222. After changing `Port 2222` in `/etc/ssh/sshd_config` on the server, all engineers must use `-p 2222` to connect.

### Connect with a specific key

```bash
$ ssh -i ~/.ssh/prod_key devops@192.168.1.50
```

### Connect with a `.pem` key file (AWS/Cloud)

```bash
$ ssh -i gvm.pem ubuntu@ec2-54-123-45-67.compute-1.amazonaws.com
ubuntu@ip-172-31-20-100:~$
```

**Explanation**: `-i` specifies the identity (private key) file. Cloud providers like AWS generate `.pem` key files when you create an instance. `PEM` stands for **Privacy Enhanced Mail** (a standard textual encoding format for cryptographic keys and certificates). The key file must have restricted permissions (`chmod 400 gvm.pem`), or SSH will refuse to use it.

```bash
# Set correct permissions first (required)
$ chmod 400 gvm.pem

# Then connect
$ ssh -i gvm.pem ubuntu@54.123.45.67
ubuntu@ip-172-31-20-100:~$
```

**Industry use case**: AWS EC2 instances use `.pem` key pairs for authentication. When you launch an instance, you download the `.pem` file once — if you lose it, you lose access. GCP and Azure have similar key-based workflows.

**Real-life example**: A DevOps engineer downloads `production-server.pem` from AWS, stores it in `~/.ssh/`, sets `chmod 400`, and uses `ssh -i ~/.ssh/production-server.pem ec2-user@10.0.1.50` to access the production server.

### SSH key generation

```bash
# Recommended: ed25519 (faster, more secure)
$ ssh-keygen -t ed25519 -C "devops@company.com"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/devops/.ssh/id_ed25519):
Enter passphrase (empty for no passphrase):
Your identification has been saved in /home/devops/.ssh/id_ed25519
Your public key has been saved in /home/devops/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:AbCdEf1234567890... devops@company.com

# Alternative: RSA with 4096 bits (wider compatibility)
$ ssh-keygen -t rsa -b 4096 -C "devops@company.com"
Generating public/private rsa key pair.
Enter file in which to save the key (/home/devops/.ssh/id_rsa):
```

**Explanation**: `ed25519` is the recommended algorithm (faster and more secure than RSA). Use RSA 4096 when connecting to older systems that don't support ed25519. The private key stays on your machine. The public key goes to the server.

### Copy public key to server

```bash
$ ssh-copy-id ubuntu@server2
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed
ubuntu@server2's password: ********
Number of key(s) added: 1

# Now you can login without a password
$ ssh ubuntu@server2
ubuntu@server2:~$
```

### Manual authorized_keys setup

When `ssh-copy-id` is not available (e.g., cloud VMs, containers):

```bash
# On the remote server:
$ mkdir -p ~/.ssh
$ chmod 700 ~/.ssh
$ vim ~/.ssh/authorized_keys
# Paste the contents of your local ~/.ssh/id_ed25519.pub
$ chmod 600 ~/.ssh/authorized_keys
```

**Explanation**: SSH requires strict permissions — `700` on `.ssh/` and `600` on `authorized_keys`. If permissions are too open, SSH refuses to use the key. This manual method is common when setting up Ansible, CI/CD pipelines, or cloud instances.

### SSH config file

```bash
$ cat ~/.ssh/config
Host web-prod
    HostName 192.168.1.50
    User devops
    IdentityFile ~/.ssh/prod_key
    Port 22

Host db-prod
    HostName 192.168.1.51
    User dbadmin
    IdentityFile ~/.ssh/prod_key

Host bastion
    HostName 203.0.113.10
    User jump
    IdentityFile ~/.ssh/bastion_key

Host internal-*
    ProxyJump bastion
    User devops
    IdentityFile ~/.ssh/prod_key
```

```bash
# Now connect with just:
$ ssh web-prod
$ ssh db-prod
$ ssh internal-app-server
```

**Explanation**: SSH config eliminates typing long commands. `ProxyJump` routes connections through a bastion/jump host — essential for accessing private networks.

### SSH tunneling (port forwarding)

```bash
# Local port forwarding: access remote service through local port
$ ssh -L 5432:localhost:5432 devops@db-server
# Now connect to localhost:5432 to reach the remote PostgreSQL

# Remote port forwarding: expose local service to remote
$ ssh -R 8080:localhost:3000 devops@public-server
# Remote server's port 8080 now forwards to your local port 3000

# Dynamic SOCKS proxy
$ ssh -D 1080 devops@proxy-server
# Configure browser to use SOCKS proxy at localhost:1080
```

### Harden SSH server

```bash
$ sudo vim /etc/ssh/sshd_config

# Key settings:
PermitRootLogin no              # Disable root login
PasswordAuthentication no       # Require key-based auth
PubkeyAuthentication yes        # Enable key auth
MaxAuthTries 3                  # Limit login attempts
AllowUsers devops deploy        # Whitelist users
Port 2222                       # Change default port (optional)
ClientAliveInterval 300         # Timeout idle sessions (5 min)
ClientAliveCountMax 2           # Disconnect after 2 missed keepalives

$ sudo systemctl restart sshd

# Legacy service-style restart (still seen on older systems)
$ sudo service sshd restart
```

### Run remote commands

```bash
# Single command
$ ssh web-prod "uptime && df -h && free -h"

# Run a local script on remote server
$ ssh web-prod 'bash -s' < local_script.sh

# Run command on multiple servers
$ for SERVER in web-01 web-02 web-03; do
    echo "=== $SERVER ==="
    ssh "$SERVER" "uptime"
done
```

---

## 12.1.1 PuTTY — SSH Client for Windows

### What is PuTTY?

**PuTTY** is a free, open-source terminal emulator and SSH client for Windows. It lets you connect to Linux servers from a Windows machine via SSH, Telnet, or serial connections.

| Component      | Purpose                                                |
|----------------|--------------------------------------------------------|
| **PuTTY**      | SSH/Telnet client — opens a terminal to a remote server|
| **PuTTYgen**   | Key generator — creates and converts SSH key pairs     |
| **Pageant**    | SSH agent — holds private keys in memory for auto-auth |
| **PSCP**       | Command-line SCP file transfer                         |
| **PSFTP**      | Command-line SFTP file transfer                        |

### Installation

1. Download from [https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html)
2. Download the **MSI installer** (includes all components) or individual `.exe` files
3. Run the installer — no special configuration needed

> **Alternative**: On Windows 10/11, you can use the built-in OpenSSH client instead of PuTTY:
> ```
> C:\> ssh devops@192.168.1.50
> ```
> Enable it via Settings → Apps → Optional Features → OpenSSH Client.

### Connecting to a Linux Server

#### Method 1: Password authentication

```
1. Open PuTTY
2. In the "Session" panel:
   - Host Name: 192.168.1.50  (your server's IP or hostname)
   - Port: 22
   - Connection type: SSH
3. Click "Open"
4. Accept the server's host key on first connection ("Accept")
5. Enter username: devops
6. Enter password: ********
7. You're now in a Linux terminal session
```

#### Method 2: SSH key authentication

```
1. Open PuTTY
2. In "Session": enter Host Name and Port
3. Navigate to Connection → SSH → Auth → Credentials
4. Under "Private key file for authentication", browse to your .ppk file
5. Go back to "Session", enter a name in "Saved Sessions", click "Save"
6. Click "Open"
7. Enter username when prompted — no password needed
```

### Generating SSH Keys with PuTTYgen

```
1. Open PuTTYgen
2. Select key type: EdDSA (Ed25519) — recommended
   (or RSA with 4096 bits if Ed25519 is not available)
3. Click "Generate"
4. Move the mouse randomly over the blank area to generate randomness
5. Once generated:
   - Add a passphrase (optional but recommended)
   - Click "Save private key" → save as .ppk file (keep this secret)
   - Copy the public key text from the top box
6. On the Linux server, paste the public key:
   $ mkdir -p ~/.ssh && chmod 700 ~/.ssh
   $ echo "paste-the-public-key-here" >> ~/.ssh/authorized_keys
   $ chmod 600 ~/.ssh/authorized_keys
```

### Converting Between Key Formats

Linux uses OpenSSH format, PuTTY uses `.ppk` format. You often need to convert between them.

#### OpenSSH → PuTTY (.ppk)

```
1. Open PuTTYgen
2. Click "Load" → change file filter to "All Files (*.*)"
3. Select your OpenSSH private key (id_rsa, id_ed25519, or .pem file)
4. Enter the passphrase if prompted
5. Click "Save private key" → save as .ppk
```

#### PuTTY (.ppk) → OpenSSH

```
1. Open PuTTYgen
2. Click "Load" → select your .ppk file
3. Go to Conversions → Export OpenSSH key
4. Save the file (e.g., id_rsa)
5. Copy to Linux: place in ~/.ssh/ with permissions 600
```

### Saving Sessions

To avoid re-entering connection details every time:

```
1. Fill in Host Name, Port, and key file path
2. In the "Session" panel, type a name in "Saved Sessions"
   (e.g., "Production Web Server")
3. Click "Save"
4. Next time, double-click the saved session to connect
```

### Useful PuTTY Settings

| Setting                          | Location                        | Recommended Value              |
|----------------------------------|---------------------------------|--------------------------------|
| Keepalive interval               | Connection                      | 60 seconds                     |
| Terminal bell                    | Terminal → Bell                 | Visual bell (less annoying)    |
| Scrollback lines                 | Window                          | 10000                          |
| Font size                        | Window → Appearance             | 12pt Consolas or Courier New   |
| Copy on select                   | Window → Selection              | Enabled (left-click to copy)   |
| Paste with right-click           | Window → Selection              | Enabled                        |
| Close window on exit             | Session                         | "Only on clean exit"           |

### PuTTY vs Native SSH

| Feature                | PuTTY (Windows)                | Native SSH (Linux/Mac/Win10+)  |
|------------------------|--------------------------------|--------------------------------|
| Interface              | GUI configuration              | Command-line only              |
| Key format             | `.ppk` (proprietary)           | OpenSSH format                 |
| Config file            | Windows Registry               | `~/.ssh/config`                |
| Session management     | GUI saved sessions             | SSH config Host entries        |
| Agent                  | Pageant                        | `ssh-agent`                    |
| Availability           | Requires installation          | Built into Linux/Mac/Win10+    |
| Scripting              | Limited                        | Full shell scripting           |

> **Recommendation**: If you're on Windows 10/11, prefer the built-in OpenSSH client over PuTTY — it uses the same commands as Linux (`ssh`, `scp`, `ssh-keygen`), making your skills transferable.

### Troubleshooting PuTTY Connections

#### "Connection refused"

```
- Verify the server IP and port (default: 22)
- Check that SSH is running on the server:
  $ sudo systemctl status sshd
- Check firewall rules:
  $ sudo ufw status
  $ sudo ss -tlnp | grep :22
```

#### "Server refused our key"

```
- Verify the key file is in .ppk format (not OpenSSH)
- Check that the public key is in ~/.ssh/authorized_keys on the server
- Check permissions on the server:
  $ chmod 700 ~/.ssh
  $ chmod 600 ~/.ssh/authorized_keys
- Check SSH server logs:
  $ sudo tail -20 /var/log/auth.log
```

#### "Network error: Connection timed out"

```
- Server may be unreachable (wrong IP, network issue, firewall)
- Try pinging the server from Windows:
  C:\> ping 192.168.1.50
- Check if a VPN is required to reach the server
- Verify security group / firewall rules allow your IP on port 22
```

---


## 12.11 WinSCP — Transfer Files Between Windows and Linux

### What is WinSCP?

**WinSCP** (Windows Secure Copy) is a free, open-source GUI application for Windows that transfers files between a local Windows machine and a remote Linux server. It supports **SFTP**, **SCP**, **FTP**, and **S3** protocols.

| Feature            | Description                                              |
|--------------------|----------------------------------------------------------|
| Protocol           | SFTP (default), SCP, FTP, S3                             |
| Authentication     | Password, SSH key (PuTTY `.ppk` or OpenSSH format)      |
| Interface          | Two-panel file manager (local left, remote right)        |
| Extras             | Built-in text editor, directory sync, scripting/automation|
| License            | Free and open source (GPL)                               |

### When to use WinSCP vs `scp`/`rsync`

| Use Case                                    | Tool          |
|---------------------------------------------|---------------|
| Quick file transfer from Windows desktop    | WinSCP        |
| Browsing remote directories visually        | WinSCP        |
| Automated transfers in scripts              | `scp`/`rsync` |
| Linux-to-Linux transfers                    | `scp`/`rsync` |
| Transferring files from CI/CD pipelines     | `scp`/`rsync` |

### Installation

1. Download from [https://winscp.net/eng/download.php](https://winscp.net/eng/download.php)
2. Run the installer and follow the prompts
3. Choose **Commander** interface (two-panel) or **Explorer** interface (single-panel)

> **Portable version**: Download the `.zip` instead of the installer if you need to run WinSCP from a USB drive without installing.

### Connecting to a Linux Server

#### Method 1: Password authentication

```
Host name:   192.168.1.50       (or your server's IP/hostname)
Port:        22
User name:   devops
Password:    ********
Protocol:    SFTP
```

1. Open WinSCP
2. In the **Login** dialog, enter the server details above
3. Click **Login**
4. Accept the server's host key fingerprint on first connection
5. You're connected — local files on the left, remote files on the right

#### Method 2: SSH key authentication (recommended)

If you have an OpenSSH private key (`id_ed25519` or `id_rsa`):

1. In the Login dialog, click **Advanced** → **SSH** → **Authentication**
2. Under **Private key file**, browse to your key file
3. WinSCP supports OpenSSH keys directly (`.pem`, `id_rsa`, `id_ed25519`)
4. If prompted, WinSCP will convert the key to PuTTY `.ppk` format automatically
5. Click **OK**, then **Login**

If you have a PuTTY `.ppk` key:

1. Same steps, but select the `.ppk` file directly — no conversion needed

#### Converting keys with PuTTYgen

If WinSCP doesn't auto-convert your key:

```
1. Open PuTTYgen (installed with WinSCP or PuTTY)
2. Click "Load" → select your OpenSSH private key (id_rsa, id_ed25519)
3. Click "Save private key" → save as .ppk
4. Use the .ppk file in WinSCP
```

### Transferring Files

#### Upload (Windows → Linux)

```
Method 1: Drag and drop
  - Navigate to the target directory on the right panel (remote)
  - Drag files from the left panel (local) to the right panel

Method 2: Right-click
  - Select files on the left panel
  - Right-click → Upload

Method 3: F5 shortcut
  - Select files on the left panel
  - Press F5 to upload
```

#### Download (Linux → Windows)

```
Method 1: Drag and drop
  - Drag files from the right panel (remote) to the left panel (local)

Method 2: Right-click
  - Select files on the right panel
  - Right-click → Download

Method 3: F5 shortcut
  - Select files on the right panel
  - Press F5 to download
```

### Transfer settings

| Setting              | Where                                    | Purpose                          |
|----------------------|------------------------------------------|----------------------------------|
| Transfer mode        | Transfer Settings dialog (Ctrl+T)        | Binary vs Text (line endings)    |
| Preserve timestamps  | Transfer Settings → Common               | Keep original modification times |
| Speed limit          | Transfer Settings → Background           | Limit bandwidth usage            |
| Resume support       | Transfer Settings → Background           | Resume interrupted transfers     |

> **Text vs Binary mode**: Use **Binary** (default) for most files. Use **Text** only for plain text files where you need Windows (`\r\n`) ↔ Linux (`\n`) line ending conversion.

### Editing Remote Files

WinSCP includes a built-in text editor for quick edits on the server:

```
1. Right-click a file on the remote panel
2. Select "Edit" (or press F4)
3. Make changes in the editor
4. Save (Ctrl+S) — WinSCP uploads the modified file automatically
```

You can also configure WinSCP to use an external editor (VS Code, Notepad++, etc.):

```
1. Go to Options → Preferences → Editors
2. Click "Add" → External editor
3. Browse to your editor executable
4. Move it above the internal editor in the list
```

### Directory Synchronization

WinSCP can sync directories between local and remote:

```
1. Navigate to the directories you want to sync (local and remote panels)
2. Go to Commands → Synchronize
3. Choose direction:
   - Local → Remote (upload new/changed files)
   - Remote → Local (download new/changed files)
   - Both (bidirectional sync)
4. Choose mode:
   - Synchronize files — copy new/modified files
   - Mirror files — make target identical to source (deletes extra files)
5. Click "OK" to preview, then "OK" to execute
```

### Saving Sessions

To avoid re-entering connection details:

```
1. In the Login dialog, fill in the connection details
2. Click "Save"
3. Name the session (e.g., "Production Web Server")
4. Check "Save password" if desired (stored encrypted)
5. Next time, double-click the saved session to connect
```

### WinSCP Command-Line / Scripting

WinSCP supports scripting for automated transfers:

```bat
:: upload_deploy.bat — Windows batch script
"C:\Program Files (x86)\WinSCP\WinSCP.com" /command ^
    "open sftp://devops@192.168.1.50/ -hostkey=""ssh-ed25519 255 AbCdEf...""" ^
    "put C:\builds\app.jar /opt/myapp/app.jar" ^
    "exit"
```

```bat
:: download_logs.bat
"C:\Program Files (x86)\WinSCP\WinSCP.com" /command ^
    "open sftp://devops@192.168.1.50/ -privatekey=""C:\keys\prod.ppk""" ^
    "get /var/log/myapp/*.log C:\logs\" ^
    "exit"
```

**Explanation**: `/command` runs WinSCP in batch mode. `open` connects, `put` uploads, `get` downloads, `exit` closes the session.

### Troubleshooting WinSCP Connections

#### "Connection refused" or "Connection timed out"

```
1. Verify the server IP and port (default: 22)
2. Check that SSH is running on the server:
   $ sudo systemctl status sshd
3. Check firewall allows port 22:
   $ sudo ufw status
   $ sudo ss -tlnp | grep :22
4. Try connecting with a terminal SSH client first to isolate the issue
```

#### "Access denied" or "Authentication failed"

```
1. Verify username and password
2. Check if password authentication is enabled on the server:
   $ grep PasswordAuthentication /etc/ssh/sshd_config
   PasswordAuthentication yes
3. If using key auth, verify the key file path and format
4. Check server-side permissions:
   $ ls -la ~/.ssh/
   $ cat ~/.ssh/authorized_keys
```

#### "Permission denied" when uploading

```
1. Check write permissions on the target directory:
   $ ls -ld /target/directory/
2. Check file ownership:
   $ stat /target/directory/
3. Upload to your home directory first, then move with SSH:
   $ sudo mv ~/uploaded_file /target/directory/
```

### Linux-Side Equivalents

The same transfers can be done from the Linux command line:

```bash
# Upload a file (from Linux to Linux)
$ scp local_file.txt devops@192.168.1.50:/home/devops/

# Download a file
$ scp devops@192.168.1.50:/var/log/app.log ./

# Upload a directory
$ scp -r local_dir/ devops@192.168.1.50:/opt/myapp/

# Sync directories (like WinSCP synchronize)
$ rsync -avz --progress local_dir/ devops@192.168.1.50:/opt/myapp/
```

---

