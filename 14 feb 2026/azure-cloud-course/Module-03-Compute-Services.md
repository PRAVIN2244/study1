# Module 03: Azure Compute Services

## Certification Relevance: AZ-104 (20-25%), AZ-204

---

## 3.1 Azure Compute Overview

```
Azure Compute Services:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Virtual Machines (IaaS)     - Full control over OS         │
│  VM Scale Sets (IaaS)        - Auto-scaling VM groups       │
│  App Service (PaaS)          - Managed web hosting          │
│  Azure Functions (Serverless)- Event-driven code execution  │
│  Container Instances (CaaS)  - Run containers without VMs   │
│  Azure Kubernetes (CaaS)     - Container orchestration      │
│  Azure Batch                 - Large-scale parallel jobs     │
│  Azure Virtual Desktop       - Desktop virtualization        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.2 Azure Virtual Machines (VMs)

### What is an Azure VM?
An on-demand, scalable computing resource. You get a virtual computer with CPU, memory, storage, and networking — running Windows or Linux.

### Real-World Example
```
Industry Example: An e-commerce company migrates their on-premises
Windows Server running IIS and SQL Server to Azure VMs. They choose
a D-series VM for the web server and an E-series VM for the database,
reducing their hardware costs by 60%.
```

### VM Sizes (Series)

| Series | Optimized For | Use Case | Example Size | vCPUs | RAM | Cost/month* |
|--------|--------------|----------|-------------|-------|-----|-------------|
| B | Burstable | Dev/test, low traffic web | B2s | 2 | 4 GB | ~$30 |
| D | General purpose | Web servers, enterprise apps | D4s_v5 | 4 | 16 GB | ~$140 |
| E | Memory optimized | Databases, in-memory caching | E4s_v5 | 4 | 32 GB | ~$180 |
| F | Compute optimized | Batch processing, gaming | F4s_v2 | 4 | 8 GB | ~$120 |
| N | GPU | Machine learning, rendering | NC6s_v3 | 6 | 112 GB | ~$900 |
| L | Storage optimized | Big data, data warehousing | L8s_v3 | 8 | 64 GB | ~$500 |
| M | Large memory | SAP HANA, large databases | M32ts | 32 | 192 GB | ~$2,500 |

*Approximate Linux pricing, East US, pay-as-you-go

### VM Operating Systems: Client OS vs Server OS

Azure VMs can run both **client operating systems** (desktop) and **server operating systems**. Understanding the difference is important for choosing the right image.

```
SERVER OS (Most Common for Azure VMs):
┌─────────────────────────────────────────────────────────────┐
│ OS                          │ Use Case                      │
├─────────────────────────────┼───────────────────────────────┤
│ Windows Server 2022         │ Web servers (IIS), Active     │
│                             │ Directory, SQL Server, file   │
│                             │ servers, enterprise apps      │
├─────────────────────────────┼───────────────────────────────┤
│ Windows Server 2019         │ Legacy apps, older workloads  │
├─────────────────────────────┼───────────────────────────────┤
│ Ubuntu Server 22.04/24.04   │ Web servers (Nginx/Apache),   │
│                             │ Docker, Kubernetes, APIs      │
├─────────────────────────────┼───────────────────────────────┤
│ Red Hat Enterprise Linux    │ Enterprise Linux workloads,   │
│ (RHEL) 8/9                  │ SAP, Oracle databases         │
├─────────────────────────────┼───────────────────────────────┤
│ CentOS / AlmaLinux / Rocky  │ Free RHEL alternatives        │
├─────────────────────────────┼───────────────────────────────┤
│ Debian 11/12                │ Lightweight Linux servers     │
├─────────────────────────────┼───────────────────────────────┤
│ SUSE Linux Enterprise       │ SAP workloads, enterprise     │
└─────────────────────────────┴───────────────────────────────┘

CLIENT OS (Desktop — for specific use cases):
┌─────────────────────────────────────────────────────────────┐
│ OS                          │ Use Case                      │
├─────────────────────────────┼───────────────────────────────┤
│ Windows 10 Enterprise       │ Virtual desktops (VDI),       │
│                             │ development workstations,     │
│                             │ testing desktop apps          │
├─────────────────────────────┼───────────────────────────────┤
│ Windows 11 Enterprise       │ Azure Virtual Desktop (AVD),  │
│                             │ remote work desktops          │
│                             │ ⚠️ Multi-session available    │
│                             │ (multiple users on one VM)    │
└─────────────────────────────┴───────────────────────────────┘

When to use which:
┌─────────────────────────────────────────────────────────────┐
│ SCENARIO                        │ CHOOSE                    │
├─────────────────────────────────┼───────────────────────────┤
│ Host a website or API           │ Server OS (Ubuntu/Windows │
│                                 │ Server)                   │
├─────────────────────────────────┼───────────────────────────┤
│ Run a database                  │ Server OS                 │
├─────────────────────────────────┼───────────────────────────┤
│ Remote desktop for employees    │ Client OS (Win 10/11)     │
│                                 │ via Azure Virtual Desktop │
├─────────────────────────────────┼───────────────────────────┤
│ Test a desktop application      │ Client OS (Win 10/11)     │
├─────────────────────────────────┼───────────────────────────┤
│ Development workstation         │ Client OS or Server OS    │
│                                 │ (both work)               │
├─────────────────────────────────┼───────────────────────────┤
│ Run Docker containers           │ Server OS (Ubuntu or      │
│                                 │ Windows Server)           │
└─────────────────────────────────┴───────────────────────────┘

⚠️ LICENSING NOTE:
   - Server OS: License cost included in Azure VM price
   - Client OS (Windows 10/11): Requires Microsoft 365 or
     Windows per-user license. Available through Azure
     Virtual Desktop or with proper licensing.
   - Linux: Free (no license cost, only compute cost)
```

### How to Find OS Images in Azure Portal

```
When creating a VM, at the "Image" dropdown:

Step 1: Click "See all images"
Step 2: You'll see the Azure Marketplace with categories:
   → Windows Server: Windows Server 2022, 2019, 2016
   → Linux: Ubuntu, RHEL, Debian, CentOS, SUSE
   → Windows Client: Windows 10, Windows 11 (search for them)
   → Pre-configured: SQL Server on Windows, WordPress on Linux

Step 3: Use the search bar to find specific images:
   → Type "Ubuntu 22.04" → Select "Ubuntu Server 22.04 LTS"
   → Type "Windows 11" → Select "Windows 11 Enterprise"
   → Type "SQL Server" → Select "SQL Server 2022 on Windows Server 2022"

Step 4: Check pricing
   → Each image shows the base price
   → Some images include software costs (SQL Server, RHEL)
   → Linux images are generally cheaper (no OS license fee)
```

### Portal UI Walkthrough: Create a Linux Virtual Machine

```
PORTAL STEPS — Create a Linux VM:

Step 1: Navigate to Virtual Machines
   → Go to https://portal.azure.com
   → In the search bar, type "Virtual machines"
   → Click "Virtual machines" from the results
   → Click "+ Create" → "Azure virtual machine"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     Select "rg-demo-eastus"             │
   │                     (or click "Create new")             │
   └────────────────────────────────────────────────────────┘
   ┌─ Instance Details ─────────────────────────────────────┐
   │ Virtual machine name:  vm-web-01                        │
   │ Region:                (US) East US                     │
   │ Availability options:  No infrastructure redundancy     │
   │                        (select "Availability zone" for  │
   │                         production workloads)           │
   │ Security type:         Standard                         │
   │ Image:                 Ubuntu Server 22.04 LTS - x64    │
   │                        (click "See all images" for more)│
   │ VM architecture:       x64                              │
   │ Size:                  Standard_B2s (2 vCPUs, 4 GiB)   │
   │                        Click "See all sizes" to compare │
   └────────────────────────────────────────────────────────┘
   ┌─ Administrator Account ────────────────────────────────┐
   │ Authentication type:   ● SSH public key                 │
   │                        ○ Password                       │
   │ Username:              azureuser                        │
   │ SSH public key source: Generate new key pair            │
   │ Key pair name:         vm-web-01_key                    │
   └────────────────────────────────────────────────────────┘
   ┌─ Inbound Port Rules ──────────────────────────────────┐
   │ Public inbound ports:  ● Allow selected ports           │
   │ Select inbound ports:  ☑ SSH (22)                       │
   └────────────────────────────────────────────────────────┘

Step 3: Disks Tab
   → Click "Next: Disks >"
   ┌─ Disk Options ─────────────────────────────────────────┐
   │ OS disk type:          Premium SSD (recommended)        │
   │                        Options: Premium SSD, Standard   │
   │                        SSD, Standard HDD                │
   │ Delete with VM:        ☑ Check this box                 │
   │                        (auto-deletes disk when VM is    │
   │                         deleted — avoids orphaned disks)│
   └────────────────────────────────────────────────────────┘
   → To add a data disk: Click "+ Create and attach a new disk"
     → Size: 128 GiB
     → Type: Premium SSD
     → Click OK

Step 4: Networking Tab
   → Click "Next: Networking >"
   ┌─ Network Interface ────────────────────────────────────┐
   │ Virtual network:      (new) vm-web-01-vnet              │
   │                       (or select existing VNet)         │
   │ Subnet:               (new) default (10.0.0.0/24)      │
   │ Public IP:            (new) vm-web-01-ip                │
   │ NIC NSG:              Basic                             │
   │ Public inbound ports: Allow selected ports              │
   │ Select inbound ports: SSH (22)                          │
   │ Delete public IP and NIC when VM is deleted: ☑ Check    │
   └────────────────────────────────────────────────────────┘

Step 5: Management Tab
   → Click "Next: Management >"
   ┌─ Management Options ───────────────────────────────────┐
   │ Enable auto-shutdown:  ☑ Check this box                 │
   │ Shutdown time:         7:00:00 PM                       │
   │ Time zone:             Your timezone                    │
   │ Notification before:   ☑ (optional — sends email 30    │
   │                         min before shutdown)            │
   │                                                         │
   │ ⚠️ Auto-shutdown saves money on dev/test VMs!           │
   └────────────────────────────────────────────────────────┘

Step 6: Monitoring Tab — Attach a Custom Storage Account
   → Click "Next: Monitoring >"
   ┌─ Boot Diagnostics ─────────────────────────────────────┐
   │ Boot diagnostics:                                       │
   │   ● Enable with custom storage account                  │
   │   ○ Enable with managed storage account (default)       │
   │   ○ Disable                                             │
   │                                                         │
   │ If you select "Enable with custom storage account":     │
   │   Diagnostics storage account:                          │
   │     → Click the dropdown                                │
   │     → Select an existing storage account                │
   │       (e.g., stprodeastus2024)                          │
   │     → OR click "Create new" to make a new one:          │
   │       Name: stdiagvm2024                                │
   │       Performance: Standard                             │
   │       Redundancy: LRS                                   │
   │       Click "OK"                                        │
   │                                                         │
   │ ⚠️ WHY use a custom storage account?                    │
   │   → Boot diagnostics screenshots are stored here       │
   │   → Useful for troubleshooting VM boot failures        │
   │   → You can use one storage account for all VMs        │
   │   → Gives you control over storage location & access   │
   └────────────────────────────────────────────────────────┘

   ⚠️ NOTE: This storage account is for DIAGNOSTICS only.
   To attach a DATA storage account to your VM (for file shares,
   blob access, etc.), see the section below:
   "How to Attach a Storage Account to a VM After Creation"

Step 7: Advanced Tab
   → Click "Next: Advanced >"
   → (Leave defaults — used for custom scripts, extensions)

Step 8: Tags Tab
   → Click "Next: Tags >"
   → Add tags:
     Name: "Environment"    Value: "Demo"
     Name: "Project"        Value: "AzureCourse"

Step 9: Review + Create
   → Click "Review + create"
   → Azure validates your configuration (green checkmark ✓)
   → Review the summary:
     ┌─────────────────────────────────────────┐
     │ VM Name:        vm-web-01               │
     │ Region:         East US                 │
     │ Size:           Standard_B2s            │
     │ OS:             Ubuntu 22.04 LTS        │
     │ Estimated cost: ~$30.37/month           │
     └─────────────────────────────────────────┘
   → Click "Create"

Step 10: Download SSH Key
   → A popup appears: "Generate new key pair"
   → Click "Download private key and create resource"
   → Save the .pem file (e.g., vm-web-01_key.pem)
   → ⚠️ KEEP THIS FILE SAFE — you cannot download it again!

Step 11: Wait for Deployment
   → Deployment takes 1-3 minutes
   → You'll see "Your deployment is complete"
   → Click "Go to resource" to see your VM

Step 12: Connect to Your VM
   → On the VM overview page, note the Public IP address
   → Open your terminal:
     chmod 400 vm-web-01_key.pem
     ssh -i vm-web-01_key.pem azureuser@<PUBLIC_IP>
   → OR click "Connect" at the top → choose "SSH" or "Bastion"
```

### Portal UI Walkthrough: Create a Windows Virtual Machine

```
PORTAL STEPS — Create a Windows VM:

Step 1-4: Same as Linux VM above, except:
   → Image: Select "Windows Server 2022 Datacenter: Azure Edition - x64"
   → Administrator account:
     Authentication type: Password
     Username: azureuser
     Password: P@ssw0rd1234!  (must meet complexity requirements)
     Confirm password: P@ssw0rd1234!
   → Inbound ports: Select RDP (3389) instead of SSH (22)

Step 5: After creation, connect via RDP:
   → Go to VM → Click "Connect" → "RDP"
   → Click "Download RDP File"
   → Open the .rdp file
   → Enter username: azureuser
   → Enter password: P@ssw0rd1234!
   → Accept the certificate warning
   → You're now on the Windows desktop!
```

### Portal UI Walkthrough: Stop, Start, Resize, and Delete a VM

```
PORTAL STEPS — Manage a VM:

STOP a VM:
   → Go to Virtual machines → Click your VM name
   → Click "Stop" button at the top toolbar
   → Confirm by clicking "Yes"
   → Status changes to "Stopped (deallocated)"
   → ⚠️ You are NO LONGER charged for compute
   → ⚠️ Disk and public IP charges still apply

START a VM:
   → Go to Virtual machines → Click your VM name
   → Click "Start" button at the top toolbar
   → Status changes to "Running" (takes 30-60 seconds)

RESTART a VM:
   → Click "Restart" button at the top toolbar
   → Confirm by clicking "Yes"

RESIZE a VM:
   → Go to VM → Left sidebar → "Size"
   → You'll see a list of available sizes
   → Select a new size (e.g., Standard_D4s_v5)
   → Click "Resize"
   → ⚠️ VM will restart during resize

DELETE a VM:
   → Go to VM → Click "Delete" at the top toolbar
   → Check the boxes for resources to delete with it:
     ☑ Network interface
     ☑ Public IP address
     ☑ OS disk
   → Type "delete" to confirm
   → Click "Delete"
```

### Portal UI Walkthrough: Attach a Storage Account / Data Disk to a VM

```
PORTAL STEPS — Attach Additional Storage to an Existing VM:

METHOD 1: Add a Data Disk (Managed Disk)
─────────────────────────────────────────
This adds a new virtual hard drive to your VM.

Step 1: Go to your VM
   → Virtual machines → Click your VM name

Step 2: Open Disks settings
   → Left sidebar → "Disks"
   → You'll see the OS disk already attached

Step 3: Add a Data Disk
   → Click "+ Create and attach a new disk"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               disk-data-vm-web-01                  │
   │ Storage type:       Premium SSD (or Standard SSD/HDD)   │
   │ Size (GiB):         128                                  │
   │ Encryption type:    Default (platform-managed key)       │
   │ Click "Apply"                                            │
   └─────────────────────────────────────────────────────────┘
   → Click "Save" at the top of the Disks page

Step 4: Format and Mount the Disk Inside the VM
   → SSH into the VM (Linux):
     # Find the new disk
     lsblk
     # Output shows: sdc (or sdd) — the new unformatted disk

     # Create a partition
     sudo fdisk /dev/sdc
     # Press: n (new) → p (primary) → 1 → Enter → Enter → w (write)

     # Format the partition
     sudo mkfs.ext4 /dev/sdc1

     # Create a mount point
     sudo mkdir /mnt/data

     # Mount the disk
     sudo mount /dev/sdc1 /mnt/data

     # Make it permanent (survives reboot)
     echo '/dev/sdc1 /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab

     # Verify
     df -h /mnt/data
     # Output: /dev/sdc1  128G  60M  121G  1% /mnt/data

   → For Windows VM:
     → Open Disk Management (right-click Start → Disk Management)
     → You'll see the new disk as "Unallocated"
     → Right-click → "New Simple Volume"
     → Follow the wizard → Assign drive letter (e.g., E:)
     → Format as NTFS → Done


METHOD 2: Mount an Azure File Share (Storage Account)
─────────────────────────────────────────────────────
This connects your VM to an Azure Storage Account file share,
so the VM can read/write files stored in the cloud.

Step 1: Create a Storage Account and File Share
   → (See Module 05 for detailed steps)
   → Storage accounts → Create → Name: stfilesvm2024
   → Go to storage account → "File shares" → "+ File share"
   → Name: vm-shared-files, Quota: 100 GiB

Step 2: Get the Mount Command
   → Go to your File Share → Click "Connect"
   → Select your OS: Linux / Windows / macOS
   → Azure generates the exact mount command for you!

   For Windows:
   ┌─────────────────────────────────────────────────────────┐
   │ Azure generates a PowerShell script:                     │
   │                                                          │
   │ $connectTestResult = Test-NetConnection                  │
   │   -ComputerName stfilesvm2024.file.core.windows.net     │
   │   -Port 445                                              │
   │ if ($connectTestResult.TcpTestSucceeded) {               │
   │   net use Z: \\stfilesvm2024.file.core.windows.net\     │
   │   vm-shared-files /user:stfilesvm2024 <ACCESS_KEY>      │
   │ }                                                        │
   │                                                          │
   │ → Copy this script → Run in PowerShell on your VM       │
   │ → The file share appears as Z: drive                    │
   └─────────────────────────────────────────────────────────┘

   For Linux:
   ┌─────────────────────────────────────────────────────────┐
   │ Azure generates a bash script:                           │
   │                                                          │
   │ sudo mkdir /mnt/vm-shared-files                         │
   │ sudo mount -t cifs                                       │
   │   //stfilesvm2024.file.core.windows.net/vm-shared-files │
   │   /mnt/vm-shared-files                                   │
   │   -o vers=3.0,username=stfilesvm2024,                   │
   │   password=<ACCESS_KEY>,                                 │
   │   dir_mode=0777,file_mode=0777,serverino                │
   │                                                          │
   │ → Copy this script → Run on your Linux VM               │
   │ → Files are accessible at /mnt/vm-shared-files          │
   └─────────────────────────────────────────────────────────┘

Step 3: Verify
   → Create a file on the VM → It appears in Azure Portal
   → Upload a file in Azure Portal → It appears on the VM
   → Multiple VMs can mount the same file share for sharing
```

### Creating a VM with Azure CLI

```bash
# Create a Linux VM
az vm create \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard

# Meaning of each parameter:
# --resource-group    : Which resource group to place the VM in
# --name              : Name of the virtual machine
# --image             : OS image (Ubuntu 22.04 LTS)
# --size              : VM size (2 vCPUs, 4 GB RAM, burstable)
# --admin-username    : Login username for SSH
# --generate-ssh-keys : Auto-generate SSH key pair (~/.ssh/id_rsa)
# --public-ip-sku     : Standard public IP (zone-redundant)

# Output:
# {
#   "fqdns": "",
#   "id": "/subscriptions/.../virtualMachines/vm-web-01",
#   "location": "eastus",
#   "macAddress": "00-0D-3A-1B-2C-3D",
#   "powerState": "VM running",
#   "privateIpAddress": "10.0.0.4",
#   "publicIpAddress": "20.185.100.50",
#   "resourceGroup": "rg-demo-eastus",
#   "zones": ""
# }

# Create a Windows VM
az vm create \
  --resource-group rg-demo-eastus \
  --name vm-win-01 \
  --image Win2022Datacenter \
  --size Standard_D2s_v5 \
  --admin-username azureuser \
  --admin-password 'P@ssw0rd1234!' \
  --public-ip-sku Standard
```

### What Gets Created Automatically
```
When you create a VM, Azure also creates:
1. Virtual Network (VNet) - if none specified
2. Subnet - inside the VNet
3. Network Interface Card (NIC) - connects VM to network
4. Network Security Group (NSG) - firewall rules
5. Public IP Address - if requested
6. OS Disk - managed disk for the operating system

These are separate resources that can be managed independently.
```

### Managing VMs

```bash
# List all VMs
az vm list --output table
# Output:
# Name        ResourceGroup     Location    Zones
# ----------  ----------------  ----------  -------
# vm-web-01   rg-demo-eastus    eastus

# Show VM details
az vm show --resource-group rg-demo-eastus --name vm-web-01 --output table

# Get VM IP address
az vm show \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --show-details \
  --query publicIps \
  --output tsv
# Output: 20.185.100.50

# Start a VM
az vm start --resource-group rg-demo-eastus --name vm-web-01
# Meaning: Power on a stopped VM (you start paying for compute)

# Stop a VM (still incurs charges for disk and IP)
az vm stop --resource-group rg-demo-eastus --name vm-web-01
# Meaning: Shuts down the OS but keeps the VM allocated

# Deallocate a VM (stop paying for compute)
az vm deallocate --resource-group rg-demo-eastus --name vm-web-01
# Meaning: Releases the compute resources. No compute charges.
# ⚠️ IMPORTANT: "stop" vs "deallocate"
# stop = OS shutdown, still billed for compute
# deallocate = releases compute, NOT billed (but disk charges remain)

# Restart a VM
az vm restart --resource-group rg-demo-eastus --name vm-web-01

# Resize a VM
az vm resize \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --size Standard_D4s_v5
# Meaning: Change VM size (causes a reboot)

# List available sizes for a VM
az vm list-vm-resize-options \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --output table

# Delete a VM
az vm delete \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --yes
# ⚠️ This deletes only the VM. NIC, disk, public IP remain.
# To delete everything:
az vm delete --resource-group rg-demo-eastus --name vm-web-01 --yes
az network nic delete --resource-group rg-demo-eastus --name vm-web-01VMNic
az network public-ip delete --resource-group rg-demo-eastus --name vm-web-01PublicIP
az disk delete --resource-group rg-demo-eastus --name vm-web-01_OsDisk_1 --yes
```

### Portal UI Walkthrough: Connect to a Linux VM via SSH

```
PORTAL STEPS — Connect to a Linux VM:

METHOD 1: SSH from Your Local Terminal (Most Common)
────────────────────────────────────────────────────

Step 1: Get the VM's Public IP Address
   → Go to Virtual machines → Click your VM name
   → On the Overview page, find "Public IP address"
   → Copy it (e.g., 20.185.100.50)

Step 2: Open Your Terminal
   → Windows: Open PowerShell or Windows Terminal
   → macOS: Open Terminal (Applications → Utilities → Terminal)
   → Linux: Open Terminal (Ctrl+Alt+T)

Step 3: Set Permissions on Your SSH Key
   → If you downloaded a .pem file during VM creation:
     chmod 400 vm-web-01_key.pem
   → ⚠️ This is required — SSH refuses keys with open permissions

Step 4: Connect via SSH
   → Type the SSH command:
     ssh -i vm-web-01_key.pem azureuser@20.185.100.50
   → If you used "Generate SSH keys" (key stored in ~/.ssh/):
     ssh azureuser@20.185.100.50
   → First time: Type "yes" to accept the fingerprint

Step 5: You're Connected!
   → You'll see the Linux terminal prompt:
     azureuser@vm-web-01:~$
   → Run commands:
     sudo apt update && sudo apt install -y nginx
     curl localhost
   → Type "exit" to disconnect

METHOD 2: Connect via Azure Portal (Browser-Based SSH)
──────────────────────────────────────────────────────

Step 1: Go to your VM in Azure Portal
Step 2: Click "Connect" at the top toolbar
Step 3: Select "SSH using Azure CLI" or "Bastion"

   Using Bastion (if enabled):
   → Click "Bastion" tab
   → Username: azureuser
   → Authentication Type: SSH Private Key from Local File
   → Upload your .pem file
   → Click "Connect"
   → A browser-based terminal opens — no local SSH needed!

METHOD 3: Run Commands Without Logging In
─────────────────────────────────────────

Step 1: Go to your VM in Azure Portal
Step 2: Left sidebar → "Run command"
Step 3: Click "RunShellScript"
Step 4: Type your commands in the text box:
   apt update && apt install -y nginx
Step 5: Click "Run"
Step 6: Output appears below after execution
   → Useful for quick one-off commands without SSH setup
```

### Portal UI Walkthrough: Connect to a Windows VM via RDP

```
PORTAL STEPS — Connect to a Windows VM via Remote Desktop:

Step 1: Get the VM's Public IP Address
   → Go to Virtual machines → Click your Windows VM name
   → On the Overview page, find "Public IP address"
   → Copy it (e.g., 20.185.100.75)

Step 2: Download the RDP File
   → Click "Connect" at the top toolbar
   → Select "RDP" tab
   → Click "Download RDP File"
   → A file named "vm-win-01.rdp" downloads to your computer

Step 3: Open the RDP File
   → Windows: Double-click the .rdp file
     → Remote Desktop Connection opens automatically
   → macOS: Install "Microsoft Remote Desktop" from App Store
     → Open the .rdp file with Microsoft Remote Desktop
   → Linux: Install rdesktop or Remmina
     → rdesktop 20.185.100.75

Step 4: Enter Credentials
   ┌─ Windows Security ─────────────────────────────────────┐
   │ Enter your credentials:                                 │
   │                                                         │
   │ → Click "More choices" → "Use a different account"     │
   │                                                         │
   │ Username: azureuser                                     │
   │ Password: P@ssw0rd1234!                                 │
   │                                                         │
   │ Click "OK"                                              │
   └────────────────────────────────────────────────────────┘

Step 5: Accept Certificate Warning
   → You'll see: "The identity of the remote computer cannot
     be verified. Do you want to connect anyway?"
   → ☑ Check "Don't ask me again for connections to this computer"
   → Click "Yes"

Step 6: You're Connected!
   → The Windows Server desktop appears in a window
   → You can:
     • Open Server Manager
     • Install IIS (web server)
     • Open PowerShell
     • Browse files
     • Install applications
   → To disconnect: Click the X on the RDP window
     (VM keeps running — you're just disconnecting your view)

TROUBLESHOOTING RDP CONNECTION:
   ┌─────────────────────────────────────────────────────────┐
   │ Problem: "Unable to connect"                            │
   │ Fix 1: Check VM is running (not stopped/deallocated)    │
   │ Fix 2: Check NSG allows port 3389 (RDP) inbound        │
   │   → VM → Networking → Check inbound rules for 3389    │
   │ Fix 3: Check your IP is allowed in NSG                  │
   │   → Add your IP: VM → Networking → Add inbound rule   │
   │ Fix 4: VM might still be booting — wait 2-3 minutes    │
   └─────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────┐
   │ Problem: "Your credentials did not work"                │
   │ Fix 1: Click "More choices" → "Use a different account" │
   │ Fix 2: Username format: azureuser (not domain\user)     │
   │ Fix 3: Reset password in Portal:                        │
   │   → VM → Left sidebar → "Reset password"              │
   │   → Enter new password → Click "Update"                │
   └─────────────────────────────────────────────────────────┘

ALTERNATIVE: Connect via Azure Bastion (More Secure)
   → No public IP needed on the VM
   → No RDP port (3389) exposed to internet
   → Connect through browser:
     VM → Connect → Bastion → Enter credentials → Connect
   → RDP session opens in your browser tab
```

### SSH into a Linux VM (CLI)

```bash
# Connect via SSH
ssh azureuser@20.185.100.50

# If using a specific key file
ssh -i ~/.ssh/id_rsa azureuser@20.185.100.50

# Run a command on the VM without logging in
az vm run-command invoke \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --command-id RunShellScript \
  --scripts "apt update && apt install -y nginx"
# Meaning: Execute commands on the VM remotely through Azure
# Output:
# {
#   "value": [
#     {
#       "code": "ProvisioningState/succeeded",
#       "message": "Enable succeeded: \n[stdout]\n...nginx installed..."
#     }
#   ]
# }
```

### Open Ports

```bash
# Open port 80 for web traffic
az vm open-port \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --port 80 \
  --priority 1000
# Meaning: Add an NSG rule allowing inbound traffic on port 80

# Open port 443 for HTTPS
az vm open-port \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --port 443 \
  --priority 1010

# Open a range of ports
az vm open-port \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --port 8080-8090 \
  --priority 1020
```

### VM Availability Options

```
1. Availability Sets (99.95% SLA)
   - Protects against hardware failures within a data center
   - Fault Domains (FD): Separate power/network (max 3)
   - Update Domains (UD): Separate maintenance windows (max 20)

   ┌─── Availability Set ──────────────────────────┐
   │                                                │
   │  Fault Domain 0    Fault Domain 1              │
   │  ┌──────────┐      ┌──────────┐               │
   │  │ VM-1     │      │ VM-2     │  ← Different  │
   │  │ (UD 0)   │      │ (UD 1)   │    racks      │
   │  └──────────┘      └──────────┘               │
   │  ┌──────────┐      ┌──────────┐               │
   │  │ VM-3     │      │ VM-4     │               │
   │  │ (UD 2)   │      │ (UD 3)   │               │
   │  └──────────┘      └──────────┘               │
   └────────────────────────────────────────────────┘

2. Availability Zones (99.99% SLA)
   - Protects against entire data center failures
   - Physically separate locations within a region
   - Independent power, cooling, networking

   ┌─── Region: East US ────────────────────────────┐
   │                                                 │
   │  Zone 1          Zone 2          Zone 3         │
   │  ┌────────┐     ┌────────┐     ┌────────┐     │
   │  │ VM-1   │     │ VM-2   │     │ VM-3   │     │
   │  │        │     │        │     │        │     │
   │  └────────┘     └────────┘     └────────┘     │
   │  Data Center    Data Center    Data Center     │
   └─────────────────────────────────────────────────┘
```

```bash
# Create VM in a specific Availability Zone
az vm create \
  --resource-group rg-demo-eastus \
  --name vm-zone1 \
  --image Ubuntu2204 \
  --size Standard_D2s_v5 \
  --zone 1 \
  --admin-username azureuser \
  --generate-ssh-keys

# Create an Availability Set
az vm availability-set create \
  --resource-group rg-demo-eastus \
  --name avset-web \
  --platform-fault-domain-count 2 \
  --platform-update-domain-count 5

# Create VM in an Availability Set
az vm create \
  --resource-group rg-demo-eastus \
  --name vm-avset-01 \
  --image Ubuntu2204 \
  --size Standard_D2s_v5 \
  --availability-set avset-web \
  --admin-username azureuser \
  --generate-ssh-keys
```

---

## 3.3 VM Scale Sets (VMSS)

### What is a VM Scale Set?
A group of identical, load-balanced VMs that automatically increase or decrease in number based on demand or a schedule.

### Real-World Example
```
Industry Example: An online ticket booking platform uses VMSS.
Normal traffic: 3 VMs handle requests.
Concert tickets go on sale: Auto-scales to 50 VMs in minutes.
Sale ends: Scales back to 3 VMs.
Cost savings: Pay for 50 VMs only during the 2-hour sale window.
```

### Portal UI Walkthrough: Create a VM Scale Set

```
PORTAL STEPS — Create a VM Scale Set:

Step 1: Navigate to VM Scale Sets
   → Search "Virtual machine scale sets" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     Select "rg-demo-eastus"             │
   └────────────────────────────────────────────────────────┘
   ┌─ Scale Set Details ────────────────────────────────────┐
   │ Name:               vmss-web                            │
   │ Region:             East US                             │
   │ Availability zone:  Zones 1, 2, 3 (select all)         │
   │ Orchestration mode: Uniform                             │
   │ Image:              Ubuntu Server 22.04 LTS             │
   │ Size:               Standard_B2s                        │
   └────────────────────────────────────────────────────────┘
   ┌─ Administrator Account ────────────────────────────────┐
   │ Authentication type: SSH public key                     │
   │ Username:            azureuser                          │
   │ SSH key source:      Generate new key pair              │
   └────────────────────────────────────────────────────────┘

Step 3: Scaling Tab
   → Click "Next: Disks >" → "Next: Networking >" → "Next: Scaling >"
   ┌─ Scaling Configuration ────────────────────────────────┐
   │ Initial instance count:  2                              │
   │ Scaling policy:          ● Custom                       │
   │ Minimum instances:       2                              │
   │ Maximum instances:       10                             │
   │ Scale out:                                              │
   │   CPU threshold:         70%                            │
   │   Number of instances    2                              │
   │   to increase by:                                       │
   │ Scale in:                                               │
   │   CPU threshold:         30%                            │
   │   Number of instances    1                              │
   │   to decrease by:                                       │
   └────────────────────────────────────────────────────────┘

Step 4: Networking Tab (go back or configure)
   → Virtual network: Create new or select existing
   → Load balancing: ☑ Use a load balancer
   → Load balancer type: Azure load balancer
   → Select or create a load balancer

Step 5: Review + Create
   → Click "Review + create" → "Create"
   → Download SSH key when prompted
   → Deployment takes 2-5 minutes

Step 6: Verify
   → Go to resource → "Instances" in left sidebar
   → You'll see 2 running instances
   → Test auto-scaling by generating CPU load on the VMs
```

```bash
# Create a VM Scale Set
az vmss create \
  --resource-group rg-demo-eastus \
  --name vmss-web \
  --image Ubuntu2204 \
  --vm-sku Standard_B2s \
  --instance-count 2 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --upgrade-policy-mode automatic \
  --load-balancer vmss-web-lb

# Meaning:
# --instance-count 2  : Start with 2 VM instances
# --upgrade-policy-mode automatic : Auto-apply updates to instances
# --load-balancer      : Create a load balancer to distribute traffic

# Output:
# Creates: VMSS + Load Balancer + VNet + Public IP + 2 VM instances

# Configure auto-scaling
az monitor autoscale create \
  --resource-group rg-demo-eastus \
  --resource vmss-web \
  --resource-type Microsoft.Compute/virtualMachineScaleSets \
  --name autoscale-web \
  --min-count 2 \
  --max-count 10 \
  --count 2

# Add scale-out rule (add VMs when CPU > 70%)
az monitor autoscale rule create \
  --resource-group rg-demo-eastus \
  --autoscale-name autoscale-web \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 2
# Meaning: When average CPU exceeds 70% over 5 minutes, add 2 instances

# Add scale-in rule (remove VMs when CPU < 30%)
az monitor autoscale rule create \
  --resource-group rg-demo-eastus \
  --autoscale-name autoscale-web \
  --condition "Percentage CPU < 30 avg 5m" \
  --scale in 1
# Meaning: When average CPU drops below 30% over 5 minutes, remove 1 instance

# Manually scale
az vmss scale \
  --resource-group rg-demo-eastus \
  --name vmss-web \
  --new-capacity 5
# Meaning: Set exactly 5 instances

# List instances
az vmss list-instances \
  --resource-group rg-demo-eastus \
  --name vmss-web \
  --output table

# Update all instances (e.g., after changing the image)
az vmss update-instances \
  --resource-group rg-demo-eastus \
  --name vmss-web \
  --instance-ids "*"
```

---

## 3.4 Azure App Service (PaaS)

### What is App Service?
A fully managed platform for building, deploying, and scaling web apps. Supports .NET, Java, Node.js, Python, PHP, Ruby, and custom containers.

### Real-World Example
```
Industry Example: A SaaS company deploys their Node.js API on App Service.
They push code to GitHub, and App Service automatically builds and deploys.
No server management, automatic OS patches, built-in SSL, custom domains.
Monthly cost: ~$55 for a production-ready setup (B1 plan).
```

### App Service Plans

| Tier | Plan | Features | Cost/month* |
|------|------|----------|-------------|
| Free | F1 | 1 GB disk, 60 min/day compute, no SLA | $0 |
| Shared | D1 | Custom domains, 240 min/day compute | ~$10 |
| Basic | B1 | 1 core, 1.75 GB RAM, custom domains, SSL | ~$55 |
| Standard | S1 | Auto-scale, staging slots, daily backups | ~$70 |
| Premium | P1v3 | Enhanced performance, more slots, VNet integration | ~$115 |
| Isolated | I1v2 | Dedicated environment (ASE), network isolation | ~$300 |

### Portal UI Walkthrough: Create an App Service Web App

```
PORTAL STEPS — Create a Web App (App Service):

Step 1: Navigate to App Services
   → Search "App Services" in the top search bar
   → Click "App Services" from results
   → Click "+ Create" → "Web App"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     Select "rg-demo-eastus"             │
   └────────────────────────────────────────────────────────┘
   ┌─ Instance Details ─────────────────────────────────────┐
   │ Name:               myapp-demo-12345                    │
   │                     (globally unique — becomes          │
   │                      myapp-demo-12345.azurewebsites.net)│
   │ Publish:            ● Code  ○ Docker Container          │
   │ Runtime stack:      Node 18 LTS                         │
   │                     (dropdown: .NET, Java, Node,        │
   │                      Python, PHP, Ruby)                 │
   │ Operating System:   ● Linux  ○ Windows                  │
   │ Region:             East US                             │
   └────────────────────────────────────────────────────────┘
   ┌─ App Service Plan ─────────────────────────────────────┐
   │ Linux Plan:         Click "Create new"                  │
   │ Name:               plan-web-01                         │
   │ Pricing plan:       Click "Change size"                 │
   │   → Dev/Test tab:   Select "B1" (Basic)                 │
   │   → Production tab: Select "S1" (Standard) for         │
   │                     auto-scale and staging slots        │
   │   → Click "Apply"                                       │
   └────────────────────────────────────────────────────────┘

Step 3: Deployment Tab
   → Click "Next: Deployment >"
   ┌─ GitHub Actions ───────────────────────────────────────┐
   │ Continuous deployment: ● Enable  ○ Disable              │
   │ GitHub account:        Click "Authorize" → sign in      │
   │ Organization:          Your GitHub username              │
   │ Repository:            Select your repo                 │
   │ Branch:                main                             │
   │                                                         │
   │ (This auto-creates a GitHub Actions workflow for CI/CD) │
   └────────────────────────────────────────────────────────┘
   → OR leave disabled and deploy manually later

Step 4: Networking Tab
   → Click "Next: Networking >"
   → Enable public access: Yes
   → (Leave defaults for now)

Step 5: Monitoring Tab
   → Click "Next: Monitoring >"
   → Enable Application Insights: Yes
   → Application Insights name: ai-myapp-demo
   → (This enables performance monitoring automatically)

Step 6: Tags → Review + Create
   → Add tags: Environment=Demo
   → Click "Review + create" → "Create"
   → Deployment takes 1-2 minutes

Step 7: Verify Your Web App
   → Click "Go to resource"
   → Click "Browse" button at the top (or click the URL)
   → You'll see a default Azure placeholder page
   → Your app URL: https://myapp-demo-12345.azurewebsites.net
```

### Portal UI Walkthrough: Deploy Code to App Service

```
PORTAL STEPS — Deploy Code via Deployment Center:

Step 1: Go to your App Service
   → App Services → Click your app name

Step 2: Open Deployment Center
   → Left sidebar → "Deployment Center"

Step 3: Choose Source
   → Source dropdown:
     • GitHub (recommended — auto CI/CD)
     • Bitbucket
     • Local Git
     • Azure Repos
     • External Git
     • FTP
   → Select "GitHub"
   → Authorize GitHub if not already done
   → Organization: Your GitHub username
   → Repository: Select your repo
   → Branch: main

Step 4: Save
   → Click "Save" at the top
   → Azure creates a GitHub Actions workflow in your repo
   → Every push to main will auto-deploy to your app

Step 5: Monitor Deployment
   → Deployment Center → "Logs" tab
   → You'll see deployment history with status:
     ✅ Success (commit abc123) — 2 minutes ago
     ✅ Success (commit def456) — 1 hour ago
```

### Portal UI Walkthrough: Create a Deployment Slot (Staging)

```
PORTAL STEPS — Create a Staging Slot:

Step 1: Go to your App Service
   → App Services → Click your app name

Step 2: Open Deployment Slots
   → Left sidebar → "Deployment slots"
   → Click "+ Add Slot"

Step 3: Configure Slot
   → Name: staging
   → Clone settings from: myapp-demo-12345 (production)
   → Click "Add"

Step 4: Deploy to Staging
   → Click the staging slot name
   → Set up deployment (Deployment Center → GitHub → develop branch)
   → Test at: https://myapp-demo-12345-staging.azurewebsites.net

Step 5: Swap Staging to Production
   → Go back to "Deployment slots"
   → Click "Swap" at the top
   → Source: staging
   → Target: production
   → Click "Swap"
   → ⚠️ This is a zero-downtime swap!
   → If something breaks, click "Swap" again to rollback
```

### Creating an App Service with CLI

```bash
# Step 1: Create an App Service Plan
az appservice plan create \
  --resource-group rg-demo-eastus \
  --name plan-web-01 \
  --sku B1 \
  --is-linux

# Meaning:
# --sku B1     : Basic tier, 1 core, 1.75 GB RAM
# --is-linux   : Linux-based (omit for Windows)

# Output:
# {
#   "name": "plan-web-01",
#   "sku": { "name": "B1", "tier": "Basic", "capacity": 1 },
#   "kind": "linux",
#   "status": "Ready"
# }

# Step 2: Create a Web App
az webapp create \
  --resource-group rg-demo-eastus \
  --plan plan-web-01 \
  --name myapp-demo-12345 \
  --runtime "NODE:18-lts"

# Meaning:
# --plan       : Which App Service Plan to use
# --name       : Globally unique name (becomes myapp-demo-12345.azurewebsites.net)
# --runtime    : Language runtime

# List available runtimes
az webapp list-runtimes --os-type linux
# Output:
# DOTNETCORE:8.0, DOTNETCORE:7.0, NODE:18-lts, NODE:20-lts,
# PYTHON:3.12, PYTHON:3.11, JAVA:17-java17, PHP:8.3, ...

# Step 3: Deploy code from GitHub
az webapp deployment source config \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --repo-url https://github.com/Azure-Samples/nodejs-docs-hello-world \
  --branch main \
  --manual-integration

# Step 4: Browse the app
az webapp browse --resource-group rg-demo-eastus --name myapp-demo-12345
# Opens: https://myapp-demo-12345.azurewebsites.net
```

### Deployment Slots

```bash
# Create a staging slot
az webapp deployment slot create \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --slot staging

# Deploy to staging
az webapp deployment source config \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --slot staging \
  --repo-url https://github.com/your-repo/app \
  --branch develop

# Test staging: https://myapp-demo-12345-staging.azurewebsites.net

# Swap staging to production (zero-downtime deployment)
az webapp deployment slot swap \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --slot staging \
  --target-slot production

# Meaning: Staging becomes production, production becomes staging
# If something goes wrong, swap again to rollback instantly
```

### App Settings & Connection Strings

```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --settings \
    NODE_ENV=production \
    API_KEY=abc123 \
    DB_HOST=mydb.database.azure.com

# List app settings
az webapp config appsettings list \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --output table

# Set connection string
az webapp config connection-string set \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --connection-string-type SQLAzure \
  --settings DefaultConnection="Server=mydb.database.windows.net;Database=mydb;User=admin;Password=pass123"

# Enable logging
az webapp log config \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --application-logging filesystem \
  --level information

# Stream live logs
az webapp log tail \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345
```

### Custom Domains & SSL

```bash
# Add custom domain
az webapp config hostname add \
  --resource-group rg-demo-eastus \
  --webapp-name myapp-demo-12345 \
  --hostname www.mycompany.com

# Create managed SSL certificate (free)
az webapp config ssl create \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --hostname www.mycompany.com

# Bind SSL certificate
az webapp config ssl bind \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --certificate-thumbprint THUMBPRINT \
  --ssl-type SNI

# Enforce HTTPS
az webapp update \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --https-only true
```

---

## 3.5 Azure Virtual Desktop (AVD)

### What is AVD?
A desktop and app virtualization service that runs on Azure. Users access a full Windows desktop from any device.

```
Real-World Example: A company with 500 remote employees uses AVD.
Instead of shipping laptops, employees use their personal devices
to connect to a Windows 11 desktop running in Azure. IT manages
one golden image instead of 500 individual machines.

Benefits:
- Centralized management
- Data stays in the cloud (security)
- Scale up/down based on workforce size
- Multi-session Windows 11 (unique to Azure)
```

---

## 3.6 Azure Batch

### What is Azure Batch?
A service for running large-scale parallel and high-performance computing (HPC) jobs.

```
Real-World Example: A movie studio needs to render 100,000 frames
for a CGI movie. Using Azure Batch:
1. Upload rendering software and scene files
2. Azure Batch spins up 1,000 VMs
3. Each VM renders a portion of frames
4. All 100,000 frames complete in 2 hours instead of 200 hours
5. VMs are automatically deleted after the job
6. Cost: ~$500 for 2 hours of 1,000 VMs vs. buying hardware
```

---

## 3.7 Hands-On Lab: Deploy a Web Application

```bash
# Complete lab: Create a web app with staging slot

# Step 1: Create resource group
az group create --name rg-webapp-lab --location eastus

# Step 2: Create App Service Plan
az appservice plan create \
  --resource-group rg-webapp-lab \
  --name plan-lab \
  --sku S1 \
  --is-linux

# Step 3: Create Web App
az webapp create \
  --resource-group rg-webapp-lab \
  --plan plan-lab \
  --name webapp-lab-$(date +%s) \
  --runtime "NODE:18-lts"

# Step 4: Deploy sample app
az webapp deployment source config \
  --resource-group rg-webapp-lab \
  --name webapp-lab-TIMESTAMP \
  --repo-url https://github.com/Azure-Samples/nodejs-docs-hello-world \
  --branch main \
  --manual-integration

# Step 5: Create staging slot
az webapp deployment slot create \
  --resource-group rg-webapp-lab \
  --name webapp-lab-TIMESTAMP \
  --slot staging

# Step 6: Verify
curl https://webapp-lab-TIMESTAMP.azurewebsites.net
# Output: Hello World!

# Step 7: Clean up
az group delete --name rg-webapp-lab --yes --no-wait
```

---

## 3.8 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `SkuNotAvailable` | VM size not available in region | Use `az vm list-skus --location eastus --output table` to find available sizes |
| `OperationNotAllowed: VM is deallocated` | Trying to resize a running VM to unavailable size | Deallocate first: `az vm deallocate`, then resize |
| `OSProvisioningTimedOut` | VM agent couldn't complete setup | Check image compatibility, increase timeout, or use custom image |
| `OverconstrainedAllocationRequest` | No capacity for requested VM in availability set | Try different VM size or remove availability set constraint |
| `QuotaExceeded` | Subscription vCPU limit reached | Request quota increase in Portal → Subscriptions → Usage + quotas |
| `PublicIPCountLimitReached` | Too many public IPs | Delete unused IPs or request limit increase |
| `webapp: name already exists` | App name not globally unique | Choose a different name |
| `Cannot swap slots` | Slot has configuration errors | Check app settings and connection strings in both slots |

### Troubleshooting VM Connectivity

```bash
# Check VM status
az vm get-instance-view \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --query instanceView.statuses[1].displayStatus
# Expected: "VM running"

# Check NSG rules (firewall)
az network nsg rule list \
  --resource-group rg-demo-eastus \
  --nsg-name vm-web-01NSG \
  --output table

# Check if port is open
az vm run-command invoke \
  --resource-group rg-demo-eastus \
  --name vm-web-01 \
  --command-id RunShellScript \
  --scripts "ss -tlnp | grep :80"

# Boot diagnostics
az vm boot-diagnostics get-boot-log \
  --resource-group rg-demo-eastus \
  --name vm-web-01
```

---

## 3.9 Practice Questions

### Question 1
**What is the difference between `az vm stop` and `az vm deallocate`?**
- A) They are the same
- B) `stop` shuts down OS but keeps billing; `deallocate` releases compute and stops billing ✅
- C) `deallocate` deletes the VM
- D) `stop` releases the public IP

### Question 2
**Which App Service plan tier supports deployment slots?**
- A) Free
- B) Basic
- C) Standard ✅ (and above)
- D) All tiers

**Explanation**: Deployment slots are available starting from the Standard (S1) tier.

### Question 3
**A company needs VMs that automatically scale based on CPU usage. Which service should they use?**
- A) Azure Virtual Machines
- B) Azure VM Scale Sets ✅
- C) Azure App Service
- D) Azure Batch

### Question 4
**What SLA do VMs deployed across Availability Zones provide?**
- A) 99.9%
- B) 99.95%
- C) 99.99% ✅
- D) 100%

### Question 5
**Which compute service is best for running a web API without managing any infrastructure?**
- A) Azure Virtual Machines
- B) Azure App Service ✅
- C) Azure Batch
- D) Azure Virtual Desktop

---

[← Previous Module](./Module-02-Azure-Account-Portal-CLI-PowerShell.md) | [Next Module: Networking →](./Module-04-Networking.md)
