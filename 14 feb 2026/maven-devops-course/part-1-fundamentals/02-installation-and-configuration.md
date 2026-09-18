# Module 2: Installing and Configuring Maven

**Objective:** Get Maven running on your machine and understand its configuration layers.

---

## 2.1 Prerequisites

Maven needs a Java compiler (JDK, not JRE):

```bash
# Check if Java is installed
java -version
javac -version   # This one matters — it's the compiler

# Install JDK on Ubuntu/Debian
sudo apt update && sudo apt install openjdk-17-jdk -y

# Install JDK on CentOS/RHEL
sudo yum install java-17-openjdk-devel -y
```

---

## 2.2 Installing Maven

### Option A: Package Manager (quick, but may be outdated)

```bash
# Ubuntu/Debian
sudo apt install maven -y

# CentOS/RHEL
sudo yum install maven -y
```

### Option B: Manual Install (recommended for control over version)

```bash
# Download
cd /opt
sudo wget https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz
sudo tar -xzf apache-maven-3.9.6-bin.tar.gz
sudo ln -s /opt/apache-maven-3.9.6 /opt/maven

# Set environment variables
echo 'export M2_HOME=/opt/maven' | sudo tee /etc/profile.d/maven.sh
echo 'export PATH=${M2_HOME}/bin:${PATH}' | sudo tee -a /etc/profile.d/maven.sh
source /etc/profile.d/maven.sh

# Verify
mvn -version
```

**Expected output:**
```
Apache Maven 3.9.6
Maven home: /opt/maven
Java version: 17.0.x, vendor: Eclipse Adoptium
```

---

## 2.3 Maven's Configuration Files

Maven has three configuration layers:

| Level | File | Location | Purpose |
|-------|------|----------|---------|
| Global | `settings.xml` | `$M2_HOME/conf/settings.xml` | Applies to all users on machine |
| User | `settings.xml` | `~/.m2/settings.xml` | Applies to current user |
| Project | `pom.xml` | Project root directory | Applies to this project only |

**Real-Life Example:** In a company, the global `settings.xml` on the Jenkins server points to the company's internal Nexus repository. Individual developers have their own `~/.m2/settings.xml` with their credentials. Each project has its own `pom.xml`.

### `pom.xml` vs `settings.xml` — What Goes Where?

| Aspect | `pom.xml` | `settings.xml` |
|--------|-----------|----------------|
| **Scope** | One project only | All projects on the machine |
| **Location** | Project root directory | `~/.m2/settings.xml` (user) or `$M2_HOME/conf/settings.xml` (global) |
| **Committed to Git?** | Yes — part of the project | **Never** — contains credentials |
| **Contains** | Dependencies, plugins, build config, profiles | Repository URLs, server credentials, mirrors, proxy settings |
| **Who edits it?** | Developers | DevOps engineers / system admins |

**What goes in `settings.xml`:**

```xml
<settings>
    <!-- Repository credentials (NEVER put these in pom.xml) -->
    <servers>
        <server>
            <id>company-nexus</id>
            <username>deployer</username>
            <password>{encrypted-password}</password>
        </server>
    </servers>

    <!-- Route all downloads through company's Nexus -->
    <mirrors>
        <mirror>
            <id>company-nexus</id>
            <mirrorOf>*</mirrorOf>
            <url>https://nexus.company.com/repository/maven-public/</url>
        </mirror>
    </mirrors>

    <!-- Proxy settings (if behind corporate firewall) -->
    <proxies>
        <proxy>
            <id>company-proxy</id>
            <active>true</active>
            <protocol>https</protocol>
            <host>proxy.company.com</host>
            <port>8080</port>
        </proxy>
    </proxies>
</settings>
```

**Rule: Never commit credentials in `pom.xml`.** Credentials go in `settings.xml`, which stays on the machine and is never pushed to Git.

### How Maven Reads Configuration (From Lecture)

Maven reads configuration in a specific order:

```
Step 1: Read settings.xml (global configuration)
        ↓
Step 2: Read pom.xml (project-specific configuration)
        ↓
Step 3: Merge both — settings.xml values are available to pom.xml
```

> **From Lecture**: "Before reading the local pom.xml, Maven will always try to take the settings.xml file and read the content. Along with this, it will read the content of the local pom.xml. So settings.xml acts as a global configuration file, whereas pom.xml acts as a local configuration file."

**The key difference:**

```
settings.xml                          pom.xml
┌─────────────────────────┐           ┌─────────────────────────┐
│ GLOBAL scope            │           │ LOCAL scope             │
│                         │           │                         │
│ Affects ALL projects    │           │ Affects ONLY this       │
│ using this Maven        │           │ project                 │
│ installation            │           │                         │
│                         │           │ Gets committed to Git   │
│ NEVER committed to Git  │           │ Visible to everyone     │
│ Contains secrets        │           │                         │
└─────────────────────────┘           └─────────────────────────┘
```

### Changing the Local Repository Path (From Lecture)

By default, Maven stores downloaded artifacts in `~/.m2/repository` (each user's home directory). In an organization with multiple developers sharing a machine, this is wasteful — each user downloads the same JARs.

**Solution: Set a shared local repository in settings.xml:**

```xml
<!-- $M2_HOME/conf/settings.xml -->
<settings>
    <!-- Change from default ~/.m2/repository to a shared location -->
    <localRepository>/opt/maven/shared-repo</localRepository>
    ...
</settings>
```

> **From Lecture**: "If I run, I shouldn't be going to my home directory to access files, and if you run, you shouldn't be going to your home directory. Both of us when we run Maven should be pointing to the same local repository."

Now any project using this Maven installation will read/write artifacts from `/opt/maven/shared-repo` instead of each user's `~/.m2/repository`.

### Server Credentials — The ID Reference Mechanism (From Lecture)

The lecture explains how to keep credentials out of pom.xml using the server ID mechanism:

**Step 1: Define credentials in settings.xml:**
```xml
<!-- settings.xml (NEVER committed to Git) -->
<settings>
    <servers>
        <server>
            <id>jboss-server</id>           <!-- Give it a name -->
            <username>deploy-user</username>
            <password>s3cret-p@ss</password>
        </server>
    </servers>
</settings>
```

**Step 2: Reference the ID in pom.xml:**
```xml
<!-- pom.xml (committed to Git — NO credentials visible) -->
<plugin>
    <groupId>org.jboss.as.plugins</groupId>
    <artifactId>jboss-as-maven-plugin</artifactId>
    <configuration>
        <id>jboss-server</id>    <!-- References settings.xml server ID -->
        <jbossHome>/opt/jboss</jbossHome>
    </configuration>
</plugin>
```

**What happens at runtime:**
```
Maven reads settings.xml → finds server with id="jboss-server"
Maven reads pom.xml → finds <id>jboss-server</id> in plugin config
Maven replaces the ID reference with the actual username/password
Plugin connects to JBoss with the credentials
```

> **From Lecture**: "If you just refer to this name, what it will do is replace this with whatever values that you have given here. Anyone who is trying to use this pom.xml will not know the username and password — that will be taken from the settings.xml."

### Other settings.xml Capabilities (From Lecture)

The settings.xml file supports several global configurations:

```xml
<settings>
    <!-- 1. Change local repository path -->
    <localRepository>/opt/maven/shared-repo</localRepository>

    <!-- 2. Server credentials (username/password) -->
    <servers>
        <server>
            <id>company-nexus</id>
            <username>deployer</username>
            <password>{encrypted}</password>
        </server>
    </servers>

    <!-- 3. Plugin groups — make plugins available to ALL projects -->
    <pluginGroups>
        <pluginGroup>org.jboss.as.plugins</pluginGroup>
        <pluginGroup>org.sonarsource.scanner.maven</pluginGroup>
    </pluginGroups>

    <!-- 4. Global profiles -->
    <profiles>
        <profile>
            <id>company-defaults</id>
            <repositories>
                <repository>
                    <id>company-nexus</id>
                    <url>https://nexus.company.com/repository/maven-public/</url>
                </repository>
            </repositories>
        </profile>
    </profiles>

    <!-- 5. Activate profiles by default -->
    <activeProfiles>
        <activeProfile>company-defaults</activeProfile>
    </activeProfiles>
</settings>
```

> **From Lecture**: "You can give values of plugins, you can change the repository path, if there is any server that you want to connect, or if there is any site you need to connect — everything can be specified here. If you specify anything here, it will be considered as a global value."

### ⚠️ Warning About settings.xml (From Lecture)

The default settings.xml has **everything commented out**. XML comments use `<!-- ... -->`.

```xml
<!-- This is commented — Maven ignores it -->
<!-- <localRepository>/opt/maven/repo</localRepository> -->

<!-- Uncomment to activate: -->
<localRepository>/opt/maven/repo</localRepository>
```

> **From Lecture**: "Make sure that you go through the file and understand, but don't change anything. Because if you uncomment something, then Maven will be behaving in a different way. Unless you have a requirement, you will not be changing the settings.xml."

**Real-Life Example — Enterprise Setup at a Bank:**
```
Jenkins CI Server:
├── $M2_HOME/conf/settings.xml (global)
│   ├── localRepository → /data/maven-cache (fast SSD, shared)
│   ├── servers → Nexus credentials, JBoss credentials
│   ├── mirrors → All downloads routed through internal Nexus
│   └── profiles → Company-wide repository URLs
│
├── Project A/pom.xml → references server id="nexus-releases"
├── Project B/pom.xml → references server id="nexus-releases"
└── Project C/pom.xml → references server id="jboss-prod"

Result: No credentials in ANY pom.xml. All projects share the same
        local repo cache. IT team manages settings.xml centrally.
```

---

## 2.4 The Local Repository (`~/.m2/repository`)

When Maven downloads a dependency, it caches it locally:

```bash
ls ~/.m2/repository/org/springframework/spring-core/
# 6.1.0/
#   spring-core-6.1.0.jar
#   spring-core-6.1.0.pom
#   spring-core-6.1.0.jar.sha1
```

### Local Repository Structure

The local repository mirrors the GAV coordinates:

```
~/.m2/repository/
├── org/springframework/spring-core/6.1.0/       ← groupId/artifactId/version/
│   ├── spring-core-6.1.0.jar                    ← the actual library
│   ├── spring-core-6.1.0.pom                    ← its pom.xml
│   └── spring-core-6.1.0.jar.sha1               ← checksum for verification
├── junit/junit/4.13.2/
│   ├── junit-4.13.2.jar
│   └── junit-4.13.2.pom
└── org/apache/maven/plugins/maven-compiler-plugin/3.12.1/
    └── maven-compiler-plugin-3.12.1.jar          ← plugins are stored here too
```

**Key insight:** Both dependencies AND plugins are stored in the local repository. They are all JAR files.

**DevOps Tip:** On CI servers, this cache can grow to several GB. You'll often need to:

```bash
# Clear the cache when debugging dependency issues
rm -rf ~/.m2/repository

# Or in CI, cache this directory between builds for speed
# (Jenkins, GitLab CI, GitHub Actions all support this)
```

---

## 2.5 Hands-On Exercise

```bash
# 1. Install Maven using the manual method
# 2. Run: mvn -version
# 3. Explore: ls $M2_HOME/conf/
# 4. Create user settings: mkdir -p ~/.m2 && cp $M2_HOME/conf/settings.xml ~/.m2/
# 5. Open ~/.m2/settings.xml and read through the comments
```

---

**Next:** [Module 3 — Maven Project Structure](03-project-structure.md)
