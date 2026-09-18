# Module 9: Repository Management

**Objective:** Understand Maven repositories and how to set up Nexus/Artifactory for enterprise use.

---

## 9.1 Types of Repositories — Central vs Remote vs Local

Maven uses three types of repositories. Understanding the difference is essential.

### The Three Repository Types

| Aspect | Local Repository | Central Repository | Remote/Private Repository |
|--------|-----------------|-------------------|--------------------------|
| **What is it?** | Cache on your machine | Apache's public repo on the internet | Your company's private repo |
| **Location** | `~/.m2/repository` | `https://repo.maven.apache.org/maven2` | `https://nexus.company.com` or `https://company.jfrog.io` |
| **Who maintains it?** | Maven (automatic) | Apache Software Foundation | Your company's DevOps team |
| **What's stored?** | Cached copies of everything you've downloaded | All open-source Java libraries (Spring, Hibernate, JUnit, etc.) | Company's internal libraries + cached copies of public libraries |
| **Access** | Only you (your machine) | Everyone on the internet | Only your company's developers |

### How Maven Searches for Dependencies — The Search Order

When you add a dependency and run `mvn compile`, Maven searches in this order:

```
Step 1: Check LOCAL repository (~/.m2/repository)
        |
        |-- Found? --> Use it. Done. (fastest)
        |
        '-- Not found? --> Go to Step 2
                |
Step 2: Check REMOTE/PRIVATE repository (Nexus/Artifactory)
        |   (only if configured in pom.xml or settings.xml)
        |
        |-- Found? --> Download to local repo. Use it.
        |
        '-- Not found? --> Go to Step 3
                |
Step 3: Check CENTRAL repository (Maven Central)
        |
        |-- Found? --> Download to local repo. Use it.
        |
        '-- Not found? --> BUILD FAILS with "Could not resolve dependency"
```

### Visual Flow

```
Developer runs: mvn compile
        |
        v
+---------------------+     Cache     +---------------------+     Download    +------------------+
|  LOCAL Repository    | <------------ |  REMOTE Repository  | <------------- | CENTRAL Repository|
|  ~/.m2/repository    |               |  (Nexus/Artifactory)|               | (Maven Central)   |
|                      |               |                      |               |                   |
|  Checked FIRST       |               |  Checked SECOND      |               |  Checked LAST     |
|  Fastest (disk)      |               |  Fast (company LAN)  |               |  Slowest (internet)|
|                      |               |                      |               |                   |
|  Contains:           |               |  Contains:           |               |  Contains:        |
|  - Cached public JARs|               |  - Company's own JARs|               |  - ALL open-source|
|  - Cached company    |               |  - Cached public JARs|               |    Java libraries |
|    JARs              |               |  - Controlled by     |               |  - 10M+ artifacts |
|  - Installed local   |               |    DevOps team       |               |                   |
|    projects          |               |                      |               |                   |
+---------------------+               +---------------------+               +------------------+
```

### What Lives Where — Real Examples

**Local Repository (`~/.m2/repository`):**
```
~/.m2/repository/
|-- org/springframework/boot/spring-boot/3.2.0/
|   '-- spring-boot-3.2.0.jar              <-- Cached from Central/Nexus
|-- com/company/payment-lib/2.1.0/
|   '-- payment-lib-2.1.0.jar              <-- Cached from company Nexus
|-- junit/junit/4.13.2/
|   '-- junit-4.13.2.jar                   <-- Cached from Central/Nexus
'-- com/company/my-app/1.0-SNAPSHOT/
    '-- my-app-1.0-SNAPSHOT.jar             <-- Installed locally (mvn install)
```

**Central Repository (Maven Central):**
```
Only open-source libraries:
  - Spring Boot, Hibernate, JUnit, Log4j, Jackson, Guava
  - Any library published by open-source projects
  - Your company's internal libraries are NOT here
  - Proprietary/commercial libraries are NOT here
```

**Remote Repository (Company's Nexus/Artifactory):**
```
Company's own libraries + cached public libraries:
  - payment-lib-2.1.0.jar (your company built this)
  - user-service-api-3.0.jar (internal API library)
  - Spring Boot 3.2.0 (cached copy from Maven Central)
  - JUnit 5.10.1 (cached copy from Maven Central)
```

### When Each Repository is Used

| Scenario | Which Repo? | Why? |
|----------|------------|------|
| First time adding Spring Boot | Central --> Local | Downloaded from internet, cached locally |
| Second build with Spring Boot | Local only | Already cached, no download needed |
| Using company's `payment-lib` | Remote --> Local | Only exists in company's Nexus |
| Building your own project with `mvn install` | Local only | Installed directly to `~/.m2` |
| CI server building for first time | Remote --> Local | Nexus caches Central, CI downloads from Nexus |
| Internet is down | Local only | If cached, build works. If not cached, build fails. |

### Why Companies Don't Use Maven Central Directly

```
Without Nexus/Artifactory:              With Nexus/Artifactory:

Dev 1 --> Maven Central (internet)      Dev 1 --> Nexus --> Maven Central
Dev 2 --> Maven Central (internet)      Dev 2 --> Nexus (cached, no internet)
Dev 3 --> Maven Central (internet)      Dev 3 --> Nexus (cached, no internet)
CI    --> Maven Central (internet)      CI    --> Nexus (cached, no internet)

Problems:                               Benefits:
- 4 downloads of same JAR               - 1 download, cached for everyone
- Slow (internet for each)              - Fast (company LAN)
- Fails if Central is down              - Works even if Central is down
- No control over what enters           - Security team controls access
- No place for internal JARs            - Host company's own JARs
```

---

## 9.2 Why Companies Use Nexus/Artifactory

1. **Security:** Control which external dependencies enter the network
2. **Speed:** Cache downloads locally (download once, share across all developers/CI)
3. **Hosting:** Store your company's internal libraries
4. **Reliability:** Builds don't fail if Maven Central is down
5. **Compliance:** Audit trail of all dependencies used

---

## 9.3 Configuring Maven to Use a Private Repository

**In `~/.m2/settings.xml` (credentials):**

```xml
<settings>
    <servers>
        <server>
            <id>company-nexus</id>
            <username>deployer</username>
            <password>s3cret</password>  <!-- Use encrypted passwords in production -->
        </server>
    </servers>

    <mirrors>
        <!-- Route ALL requests through Nexus -->
        <mirror>
            <id>company-nexus</id>
            <mirrorOf>*</mirrorOf>
            <url>https://nexus.mycompany.com/repository/maven-public/</url>
        </mirror>
    </mirrors>
</settings>
```

**In `pom.xml` (where to deploy your artifacts):**

```xml
<distributionManagement>
    <repository>
        <id>company-nexus</id>
        <url>https://nexus.mycompany.com/repository/maven-releases/</url>
    </repository>
    <snapshotRepository>
        <id>company-nexus</id>
        <url>https://nexus.mycompany.com/repository/maven-snapshots/</url>
    </snapshotRepository>
</distributionManagement>
```

**Note:** The `<id>` in `<server>` must match the `<id>` in `<repository>` and `<mirror>`.

---

## 9.4 Configuring pom.xml to Connect with Remote Repositories — Step by Step

There are two things to configure:
1. **Where to download dependencies FROM** → `<repositories>` in `pom.xml` or `<mirrors>` in `settings.xml`
2. **Where to upload your artifacts TO** → `<distributionManagement>` in `pom.xml`

### Method 1: Add Repository Directly in pom.xml

Use `<repositories>` when you need dependencies from a specific remote repo:

```xml
<!-- pom.xml — Tell Maven to also look in your company's Nexus -->
<repositories>
    <!-- Maven Central is always checked by default -->
    <!-- Add your company's Nexus repository -->
    <repository>
        <id>company-nexus-releases</id>
        <name>Company Nexus Releases</name>
        <url>https://nexus.mycompany.com/repository/maven-releases/</url>
        <releases>
            <enabled>true</enabled>
        </releases>
        <snapshots>
            <enabled>false</enabled>
        </snapshots>
    </repository>

    <repository>
        <id>company-nexus-snapshots</id>
        <name>Company Nexus Snapshots</name>
        <url>https://nexus.mycompany.com/repository/maven-snapshots/</url>
        <releases>
            <enabled>false</enabled>
        </releases>
        <snapshots>
            <enabled>true</enabled>
            <updatePolicy>always</updatePolicy>  <!-- Check for new SNAPSHOTs every build -->
        </snapshots>
    </repository>
</repositories>
```

### Method 2: Use Mirror in settings.xml (Recommended for Companies)

Route ALL dependency downloads through Nexus. This is the preferred approach because:
- One config for all projects (not per-project)
- Nexus caches Maven Central — faster downloads
- Security team controls what enters the network

```xml
<!-- ~/.m2/settings.xml -->
<settings>
    <mirrors>
        <mirror>
            <id>company-nexus</id>
            <mirrorOf>*</mirrorOf>  <!-- Intercept ALL repository requests -->
            <url>https://nexus.mycompany.com/repository/maven-public/</url>
        </mirror>
    </mirrors>
</settings>
```

### Configuring Where to Upload Your Artifacts (distributionManagement)

`<distributionManagement>` tells Maven where to upload when you run `mvn deploy`:

```xml
<!-- pom.xml — Where to upload YOUR project's artifacts -->
<distributionManagement>
    <!-- Release artifacts (e.g., payment-service-2.1.0.jar) -->
    <repository>
        <id>company-nexus</id>
        <name>Company Releases</name>
        <url>https://nexus.mycompany.com/repository/maven-releases/</url>
    </repository>

    <!-- Snapshot artifacts (e.g., payment-service-2.2.0-SNAPSHOT.jar) -->
    <snapshotRepository>
        <id>company-nexus</id>
        <name>Company Snapshots</name>
        <url>https://nexus.mycompany.com/repository/maven-snapshots/</url>
    </snapshotRepository>
</distributionManagement>
```

**Then deploy:**
```bash
# If version is 2.2.0-SNAPSHOT → uploads to maven-snapshots
# If version is 2.1.0 → uploads to maven-releases
mvn clean deploy
```

### Complete Nexus Configuration Example

Here's everything together — what goes in `pom.xml` and what goes in `settings.xml`:

```xml
<!-- ============================================ -->
<!-- pom.xml (committed to Git — no secrets)      -->
<!-- ============================================ -->
<project>
    <groupId>com.company</groupId>
    <artifactId>payment-service</artifactId>
    <version>2.1.0-SNAPSHOT</version>

    <!-- Where to DOWNLOAD dependencies from -->
    <repositories>
        <repository>
            <id>company-nexus</id>
            <url>https://nexus.mycompany.com/repository/maven-public/</url>
        </repository>
    </repositories>

    <!-- Where to UPLOAD your artifact to -->
    <distributionManagement>
        <repository>
            <id>company-nexus</id>
            <url>https://nexus.mycompany.com/repository/maven-releases/</url>
        </repository>
        <snapshotRepository>
            <id>company-nexus</id>
            <url>https://nexus.mycompany.com/repository/maven-snapshots/</url>
        </snapshotRepository>
    </distributionManagement>
</project>
```

```xml
<!-- ============================================ -->
<!-- ~/.m2/settings.xml (NEVER committed to Git)  -->
<!-- ============================================ -->
<settings>
    <!-- Credentials for uploading (mvn deploy) -->
    <servers>
        <server>
            <id>company-nexus</id>           <!-- Must match <id> in pom.xml -->
            <username>deployer</username>
            <password>{encrypted-password}</password>
        </server>
    </servers>
</settings>
```

**The `<id>` connection rule:**
```
settings.xml <server><id>company-nexus</id>
                          │
pom.xml <repository><id>company-nexus</id>        ← Must match
pom.xml <snapshotRepository><id>company-nexus</id> ← Must match
```

### JFrog Artifactory Configuration

JFrog Artifactory works the same way — only the URLs differ:

```xml
<!-- pom.xml — JFrog Artifactory -->
<repositories>
    <repository>
        <id>jfrog-releases</id>
        <url>https://mycompany.jfrog.io/artifactory/libs-release/</url>
    </repository>
    <repository>
        <id>jfrog-snapshots</id>
        <url>https://mycompany.jfrog.io/artifactory/libs-snapshot/</url>
        <snapshots>
            <enabled>true</enabled>
        </snapshots>
    </repository>
</repositories>

<distributionManagement>
    <repository>
        <id>jfrog-releases</id>
        <url>https://mycompany.jfrog.io/artifactory/libs-release-local/</url>
    </repository>
    <snapshotRepository>
        <id>jfrog-snapshots</id>
        <url>https://mycompany.jfrog.io/artifactory/libs-snapshot-local/</url>
    </snapshotRepository>
</distributionManagement>
```

```xml
<!-- ~/.m2/settings.xml — JFrog credentials -->
<settings>
    <servers>
        <server>
            <id>jfrog-releases</id>
            <username>admin</username>
            <password>{encrypted-password}</password>
        </server>
        <server>
            <id>jfrog-snapshots</id>
            <username>admin</username>
            <password>{encrypted-password}</password>
        </server>
    </servers>
</settings>
```

### Real-Life Scenario — Setting Up a New Project at a Company

```
Day 1: You join a company. DevOps lead gives you:
  1. Nexus URL: https://nexus.company.com
  2. Your username/password
  3. A template settings.xml

You do:
  1. Copy settings.xml to ~/.m2/settings.xml
  2. Add your credentials
  3. Clone the project (pom.xml already has <repositories> and <distributionManagement>)
  4. Run: mvn clean package
  5. Maven downloads everything through Nexus — fast, cached, secure
```

---

## 9.5 SNAPSHOT vs RELEASE — Version Naming for Test and Production

| Aspect | SNAPSHOT | RELEASE |
|--------|----------|---------|
| Version | `1.0.0-SNAPSHOT` | `1.0.0` |
| Mutable? | Yes, can be overwritten | No, immutable |
| Use case | Active development, testing | Production-ready, shipped to customer |
| Maven behavior | Checks for updates daily | Downloads once, caches forever |
| Deployed to | `maven-snapshots` repository | `maven-releases` repository |

```bash
# Force Maven to check for updated SNAPSHOTs
mvn clean package -U
```

### Version Naming Conventions — What Companies Use

```
Development / Testing:
  payment-service-2.1.0-SNAPSHOT.jar     <-- SNAPSHOT = still being developed/tested
  payment-service-2.1.0-20240115.jar     <-- Timestamped SNAPSHOT (Maven adds this automatically)

Production Release:
  payment-service-2.1.0.jar              <-- No SNAPSHOT = final, production-ready
  payment-service-2.1.0-RC1.jar          <-- Release Candidate 1 (pre-production testing)
  payment-service-2.1.0-GA.jar           <-- General Availability (some projects use this)
```

### How pom.xml Changes Between Development and Release

**During development (testing):**
```xml
<!-- pom.xml — SNAPSHOT version for development/testing -->
<groupId>com.company</groupId>
<artifactId>payment-service</artifactId>
<version>2.1.0-SNAPSHOT</version>
```

- `mvn deploy` uploads to `maven-snapshots` repository
- Can be overwritten — every build replaces the previous SNAPSHOT
- QA tests this version
- Other teams depending on this get automatic updates

**For production release:**
```xml
<!-- pom.xml — Release version for production -->
<groupId>com.company</groupId>
<artifactId>payment-service</artifactId>
<version>2.1.0</version>
```

- `mvn deploy` uploads to `maven-releases` repository
- Immutable — once deployed, version 2.1.0 can never be changed
- This is what goes to production
- Customers use this version

### Complete Release Lifecycle — How pom.xml Version Changes

```
Phase 1: Development
  pom.xml version: 2.1.0-SNAPSHOT
  Artifact: payment-service-2.1.0-SNAPSHOT.jar
  Deployed to: maven-snapshots
  Used by: Developers, QA team for testing

Phase 2: Release Candidate (optional)
  pom.xml version: 2.1.0-RC1
  Artifact: payment-service-2.1.0-RC1.jar
  Deployed to: maven-releases
  Used by: QA team for final testing

Phase 3: Production Release
  pom.xml version: 2.1.0
  Artifact: payment-service-2.1.0.jar
  Deployed to: maven-releases
  Used by: Production servers, customers

Phase 4: Next Development Cycle
  pom.xml version: 2.2.0-SNAPSHOT
  Artifact: payment-service-2.2.0-SNAPSHOT.jar
  Deployed to: maven-snapshots
  Used by: Developers working on next version
```

### How to Change Version in pom.xml for Release

**Method 1: Manual (small projects)**
```bash
# Edit pom.xml manually: change 2.1.0-SNAPSHOT to 2.1.0
# Then build and deploy
mvn clean deploy
```

**Method 2: Using versions plugin (recommended)**
```bash
# Change version from SNAPSHOT to release
mvn versions:set -DnewVersion=2.1.0
mvn versions:commit

# Build and deploy the release
mvn clean deploy

# Tag in Git
git add pom.xml
git commit -m "Release 2.1.0"
git tag v2.1.0
git push origin v2.1.0

# Bump to next SNAPSHOT for development
mvn versions:set -DnewVersion=2.2.0-SNAPSHOT
mvn versions:commit
git add pom.xml
git commit -m "Start 2.2.0-SNAPSHOT development"
git push
```

**Method 3: Using Maven Release Plugin (fully automated)**
```bash
# Prepares the release: changes SNAPSHOT to release, tags Git
mvn release:prepare

# Performs the release: builds tag, deploys to releases repo
mvn release:perform

# After this:
# - 2.1.0 is deployed to maven-releases
# - Git tag v2.1.0 is created
# - pom.xml is bumped to 2.2.0-SNAPSHOT automatically
```

### Where Each Version Goes in Nexus

```
Nexus Repository Manager
|
|-- maven-snapshots/                    <-- SNAPSHOT versions go here
|   '-- com/company/payment-service/
|       '-- 2.1.0-SNAPSHOT/
|           '-- payment-service-2.1.0-SNAPSHOT.jar    (overwritten with each build)
|
|-- maven-releases/                     <-- Release versions go here
|   '-- com/company/payment-service/
|       |-- 2.0.0/
|       |   '-- payment-service-2.0.0.jar             (immutable, never changes)
|       '-- 2.1.0/
|           '-- payment-service-2.1.0.jar             (immutable, never changes)
|
'-- maven-central-proxy/                <-- Cached copies of public libraries
    '-- org/springframework/...
```

### pom.xml distributionManagement — Tells Maven Where to Upload

Maven automatically decides which repository to use based on the version:

```xml
<distributionManagement>
    <!-- If version does NOT contain SNAPSHOT, upload here -->
    <repository>
        <id>company-nexus</id>
        <url>https://nexus.company.com/repository/maven-releases/</url>
    </repository>

    <!-- If version CONTAINS SNAPSHOT, upload here -->
    <snapshotRepository>
        <id>company-nexus</id>
        <url>https://nexus.company.com/repository/maven-snapshots/</url>
    </snapshotRepository>
</distributionManagement>
```

```bash
# Version is 2.1.0-SNAPSHOT → Maven uploads to snapshotRepository URL
mvn deploy

# Version is 2.1.0 → Maven uploads to repository URL
mvn deploy
```

**Maven decides automatically based on the version string. You don't need to change `distributionManagement` — just change the version.**

### Real-Life Workflow at a Company

```
Sprint 1 (2 weeks):
  Developers work on payment-service:2.1.0-SNAPSHOT
  Every commit → Jenkins runs mvn deploy → SNAPSHOT uploaded to Nexus
  QA tests the SNAPSHOT version

Sprint End:
  Release manager runs: mvn release:prepare release:perform
  Version 2.1.0 deployed to maven-releases
  Git tag v2.1.0 created
  pom.xml bumped to 2.2.0-SNAPSHOT

Production:
  Operations deploys payment-service-2.1.0.jar to production
  Customers use the new features

Sprint 2 (next 2 weeks):
  Developers work on payment-service:2.2.0-SNAPSHOT
  Cycle repeats
```

---

## 9.6 Setting Up Nexus with Docker (DevOps Exercise)

```bash
# Run Nexus in Docker
docker run -d -p 8081:8081 --name nexus sonatype/nexus3

# Wait for startup (~2 minutes)
# Get admin password:
docker exec nexus cat /nexus-data/admin.password

# Access UI: http://localhost:8081
# Default repos:
#   maven-central (proxy to Maven Central)
#   maven-releases (hosted, for your releases)
#   maven-snapshots (hosted, for your snapshots)
#   maven-public (group combining all above)
```

---

## 9.7 Password Encryption

Never store plain-text passwords in `settings.xml`:

```bash
# Create a master password
mvn --encrypt-master-password MyMasterPassword
# Output: {jSMOWnoPFgsHVpMvz5VrIt5kRbzGpI8u+9EF1iFQyJQ=}

# Store it in ~/.m2/settings-security.xml
cat > ~/.m2/settings-security.xml << 'EOF'
<settingsSecurity>
    <master>{jSMOWnoPFgsHVpMvz5VrIt5kRbzGpI8u+9EF1iFQyJQ=}</master>
</settingsSecurity>
EOF

# Encrypt a server password
mvn --encrypt-password MyNexusPassword
# Output: {COQLCE6DU6GtcS5P=}

# Use the encrypted password in settings.xml
```

---

## 9.8 Hands-On Exercise

```bash
# 1. Run Nexus in Docker
# 2. Configure settings.xml to mirror through Nexus
# 3. Build your project — watch Nexus proxy and cache dependencies
# 4. Deploy your artifact: mvn clean deploy
# 5. Verify it appears in Nexus UI under maven-snapshots
# 6. Delete ~/.m2/repository and rebuild — dependencies come from Nexus cache
```

---

**Next:** [Module 10 — Maven in CI/CD Pipelines](10-cicd-integration.md)
