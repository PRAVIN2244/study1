# Module 4: Linux Distributions

## 1.3 Linux Distributions

A **distribution (distro)** = Linux Kernel + Package Manager + Desktop/Server Tools + Configuration

### Major Distribution Families

```
                        ┌─────────┐
                        │  Linux  │
                        │ Kernel  │
                        └────┬────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌──────────┐
         │ Debian │    │ RedHat │    │  Others  │
         └───┬────┘    └───┬────┘    └────┬─────┘
             │             │              │
        ┌────┴────┐   ┌────┴────┐    ┌────┴────┐
        │ Ubuntu  │   │  RHEL   │    │  Arch   │
        │ Mint    │   │ CentOS  │    │  Alpine │
        │ Kali    │   │ Fedora  │    │  SUSE   │
        └─────────┘   │ Amazon  │    └─────────┘
                      │  Linux  │
                      └─────────┘
```

### Choosing a Distro (DevOps Perspective)

| Distro         | Package Manager | Use Case                        |
|----------------|-----------------|----------------------------------|
| Ubuntu/Debian  | `apt`           | Cloud servers, development       |
| RHEL/CentOS    | `yum`/`dnf`     | Enterprise production servers    |
| Amazon Linux   | `yum`/`dnf`     | AWS-native workloads             |
| Alpine         | `apk`           | Minimal Docker containers        |
| Fedora         | `dnf`           | Cutting-edge development         |
| Arch           | `pacman`        | Rolling release, customization   |

---

