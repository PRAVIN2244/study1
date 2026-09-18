# Module 11: Advanced Maven for DevOps

**Objective:** Master advanced topics that separate a junior DevOps engineer from a senior one.

---

## 11.1 Maven Wrapper (`mvnw`)

The Maven Wrapper ensures everyone uses the same Maven version — no "works on my machine" issues:

```bash
# Generate wrapper files in your project
mvn wrapper:wrapper -Dmaven=3.9.6

# This creates:
# .mvn/wrapper/maven-wrapper.jar
# .mvn/wrapper/maven-wrapper.properties
# mvnw        (Linux/Mac script)
# mvnw.cmd    (Windows script)
```

**Usage in CI (always prefer `./mvnw` over `mvn`):**

```bash
# Instead of: mvn clean package
./mvnw clean package

# No Maven installation needed on the CI server
```

**Real-Life Example:** A team has 20 microservices. Some were created 3 years ago with Maven 3.6, others use 3.9. Without the wrapper, the CI server needs multiple Maven versions. With the wrapper, each project carries its own Maven version.

---

## 11.2 BOM (Bill of Materials)

A BOM is a special POM that manages dependency versions for a set of related libraries:

```xml
<dependencyManagement>
    <dependencies>
        <!-- Import Spring Boot BOM -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.2.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>

        <!-- Import AWS SDK BOM -->
        <dependency>
            <groupId>software.amazon.awssdk</groupId>
            <artifactId>bom</artifactId>
            <version>2.22.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<!-- Now use any Spring Boot or AWS dependency without specifying version -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <!-- version managed by BOM -->
    </dependency>
    <dependency>
        <groupId>software.amazon.awssdk</groupId>
        <artifactId>s3</artifactId>
        <!-- version managed by BOM -->
    </dependency>
</dependencies>
```

---

## 11.3 Maven Release Process

The release plugin automates the entire release workflow:

```bash
# Prerequisites:
# 1. No uncommitted changes
# 2. No SNAPSHOT dependencies
# 3. SCM (Git) configured in pom.xml

# Step 1: Prepare the release
mvn release:prepare
# What it does:
# - Changes 1.0.0-SNAPSHOT → 1.0.0 in pom.xml
# - Commits the change
# - Creates a Git tag: v1.0.0
# - Changes 1.0.0 → 1.1.0-SNAPSHOT in pom.xml
# - Commits the change

# Step 2: Perform the release
mvn release:perform
# What it does:
# - Checks out the tag
# - Builds and deploys the tagged version to Nexus

# If something goes wrong:
mvn release:rollback
```

**SCM configuration in `pom.xml`:**

```xml
<scm>
    <connection>scm:git:git://github.com/mycompany/my-app.git</connection>
    <developerConnection>scm:git:ssh://github.com/mycompany/my-app.git</developerConnection>
    <url>https://github.com/mycompany/my-app</url>
    <tag>HEAD</tag>
</scm>
```

---

## 11.4 Maven with Docker

**`Dockerfile` — Multi-stage build (production pattern):**

```dockerfile
# Stage 1: Build with Maven
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
# Download dependencies first (cached layer if pom.xml unchanged)
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests -B

# Stage 2: Run with minimal JRE
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**Why multi-stage?**
- Build image: ~800MB (includes Maven, JDK, source code)
- Final image: ~200MB (only JRE + JAR)

**Optimizing Docker layer caching:**

```dockerfile
# Copy pom.xml FIRST, then download dependencies
# This layer is cached unless pom.xml changes
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source code AFTER dependencies
# Only this layer rebuilds when code changes
COPY src ./src
RUN mvn package -DskipTests
```

---

## 11.5 Maven with SonarQube (Code Quality)

```bash
# Run SonarQube analysis
mvn sonar:sonar \
  -Dsonar.host.url=http://sonarqube.mycompany.com:9000 \
  -Dsonar.token=sqp_abc123 \
  -Dsonar.projectKey=my-app

# With quality gate check (fails build if quality gate fails)
mvn sonar:sonar \
  -Dsonar.qualitygate.wait=true
```

**SonarQube in `pom.xml`:**

```xml
<properties>
    <sonar.organization>mycompany</sonar.organization>
    <sonar.host.url>http://sonarqube:9000</sonar.host.url>
    <sonar.coverage.jacoco.xmlReportPaths>
        ${project.build.directory}/site/jacoco/jacoco.xml
    </sonar.coverage.jacoco.xmlReportPaths>
</properties>
```

---

## 11.6 Dependency Security Scanning

```xml
<!-- OWASP Dependency Check Plugin -->
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>9.0.7</version>
    <configuration>
        <failBuildOnCVSS>7</failBuildOnCVSS>  <!-- Fail on HIGH/CRITICAL -->
    </configuration>
    <executions>
        <execution>
            <goals><goal>check</goal></goals>
        </execution>
    </executions>
</plugin>
```

```bash
# Run security scan
mvn dependency-check:check

# Report at: target/dependency-check-report.html
```

**Real-Life Scenario:** Your company's security team mandates that no dependency with a CVSS score >= 7 can be deployed to production. You add this plugin to the CI pipeline. When Log4Shell (CVE-2021-44228, CVSS 10.0) was discovered, this plugin would have blocked any build using the vulnerable Log4j version.

---

## 11.7 Maven Settings for CI Servers

**`ci-settings.xml` (committed to repo, no secrets):**

```xml
<settings>
    <servers>
        <server>
            <id>nexus-releases</id>
            <username>${env.NEXUS_USERNAME}</username>
            <password>${env.NEXUS_PASSWORD}</password>
        </server>
        <server>
            <id>nexus-snapshots</id>
            <username>${env.NEXUS_USERNAME}</username>
            <password>${env.NEXUS_PASSWORD}</password>
        </server>
    </servers>
    <mirrors>
        <mirror>
            <id>nexus</id>
            <mirrorOf>*</mirrorOf>
            <url>${env.NEXUS_URL}/repository/maven-public/</url>
        </mirror>
    </mirrors>
</settings>
```

```bash
# Use in CI:
mvn -s ci-settings.xml clean deploy
```

---

## 11.8 Deployment Plugins — Deploying to Application Servers

Maven can deploy your WAR/JAR directly to application servers using deployment plugins. This automates the last step of the pipeline.

### Deploying to Apache Tomcat

```xml
<plugin>
    <groupId>org.apache.tomcat.maven</groupId>
    <artifactId>tomcat7-maven-plugin</artifactId>
    <version>2.2</version>
    <configuration>
        <url>http://localhost:8080/manager/text</url>
        <server>tomcat-server</server>       <!-- matches id in settings.xml -->
        <path>/my-webapp</path>              <!-- context path -->
    </configuration>
</plugin>
```

```bash
# Deploy WAR to Tomcat
mvn tomcat7:deploy

# Redeploy (undeploy + deploy)
mvn tomcat7:redeploy

# Undeploy
mvn tomcat7:undeploy
```

### Deploying to JBoss / WildFly

```xml
<plugin>
    <groupId>org.wildfly.plugins</groupId>
    <artifactId>wildfly-maven-plugin</artifactId>
    <version>4.2.0.Final</version>
    <configuration>
        <hostname>localhost</hostname>
        <port>9990</port>
    </configuration>
</plugin>
```

```bash
# Deploy to JBoss/WildFly
mvn wildfly:deploy

# Undeploy
mvn wildfly:undeploy

# Redeploy
mvn wildfly:redeploy
```

### Deployment Plugin Walkthrough (From Lecture)

The lecture demonstrates deploying to JBoss step by step. The key concepts apply to ANY deployment plugin (Tomcat, JBoss, Jetty, etc.).

**Step 1: Add the plugin to your module's pom.xml**

```xml
<build>
    <plugins>
        <plugin>
            <!-- GAV of the JBoss deployment plugin -->
            <groupId>org.jboss.as.plugins</groupId>
            <artifactId>jboss-as-maven-plugin</artifactId>
            <version>7.9.Final</version>
            <configuration>
                <!-- Where is the application server installed? -->
                <jbossHome>/path/to/jboss/installation</jbossHome>

                <!-- Server name (organizations give servers specific names) -->
                <serverName>default</serverName>

                <!-- What file to deploy — use this project's own GAV -->
                <filename>${project.build.finalName}.${project.packaging}</filename>
            </configuration>
        </plugin>
    </plugins>
</build>
```

**Configuration values explained:**

| Config Element | Purpose | Example |
|---------------|---------|---------|
| `jbossHome` | Directory where JBoss is installed on the machine | `/opt/jboss-7.1` |
| `serverName` | Name of the server instance (set by IT/admin team) | `default`, `production-1` |
| `filename` | The JAR/WAR file to deploy — typically this project's artifact | `component2-1.0-SNAPSHOT.jar` |

> **From Lecture**: "When you use the GAV of this particular project, whatever file we are creating — that is `component2-1.0-SNAPSHOT.jar` — is what gets connected to this application server and deployed."

**Step 2: Understand how the goal maps to Maven's lifecycle**

This is where it gets interesting. The plugin is NOT attached to any lifecycle phase in the configuration above. To invoke it, you call the goal directly:

```bash
# Go to the specific module
cd component2

# Call the plugin's deploy goal directly
mvn jboss-as:deploy
```

**What actually happens:**

```
You call:  mvn jboss-as:deploy
                    │
                    ▼
Maven sees "deploy" goal name
                    │
                    ▼
This maps to Maven's "deploy" lifecycle PHASE
                    │
                    ▼
Maven runs the FULL lifecycle from the beginning:
  validate → compile → test → package → ... → deploy
                    │
                    ▼
At the deploy phase, instead of the DEFAULT deploy plugin,
Maven uses YOUR JBoss plugin
                    │
                    ▼
JBoss plugin connects to the application server
and deploys the JAR/WAR file
```

> **From Lecture**: "When you say deploy, that was the last phase, right? So it is going from the beginning — first generating the resources, compiling the file, testing the file, and after testing it will create our default package, and after creating the package it is going to the deploy phase wherein it is calling the specific plugin that we have given."

**Step 3: Verify the deployment**

After running the deploy goal:
- Go to the JBoss admin console (manage deployments)
- The deployed file appears in the deployments list
- The application is now accessible on the server

**Step 4: Undeploy**

```bash
# Remove the deployed application
mvn jboss-as:undeploy
```

This also runs through the full lifecycle, but at the deploy phase it calls the undeploy goal instead — removing the application from the server.

**The pattern for ANY deployment plugin:**

```
1. Find out what application server your company uses
2. Find the corresponding Maven plugin
3. Get the plugin's GAV (from the plugin's documentation/usage page)
4. Add it to your pom.xml with the right configuration
5. Call the plugin's goal: mvn <plugin-prefix>:deploy
```

> **From Lecture**: "In the company, if they are using Apache then you have to use Apache's plugin. If they say JBoss, you have to use JBoss. If there is anything other than that, find out what tool they are using and based on that, what plugin to use."

### Using Cargo Plugin (Generic — Works with Many Servers)

Cargo supports Tomcat, JBoss, Jetty, GlassFish, and more:

```xml
<plugin>
    <groupId>org.codehaus.cargo</groupId>
    <artifactId>cargo-maven3-plugin</artifactId>
    <version>1.10.11</version>
    <configuration>
        <container>
            <containerId>tomcat9x</containerId>
            <type>remote</type>
        </container>
        <configuration>
            <type>runtime</type>
            <properties>
                <cargo.remote.uri>http://server:8080/manager/text</cargo.remote.uri>
                <cargo.remote.username>${tomcat.user}</cargo.remote.username>
                <cargo.remote.password>${tomcat.password}</cargo.remote.password>
            </properties>
        </configuration>
    </configuration>
</plugin>
```

```bash
mvn cargo:deploy
```

**Real-Life Example — CI/CD Pipeline with Deployment:**

```bash
# Complete pipeline command:
mvn clean install                    # Build + test
mvn tomcat7:redeploy                 # Deploy to Tomcat

# Or in a single pipeline:
mvn clean package tomcat7:redeploy -DskipTests
```

**Modern alternative:** Most companies now deploy using Docker containers instead of direct server deployment. But deployment plugins are still used in legacy enterprise environments.

---

## 11.9 Version Management

### The Problem: Why Manual Version Changes Are Tedious

During development, all projects use `1.0-SNAPSHOT` — this indicates a development copy, not yet released. When it's time to release, every version reference must change.

In a multi-module project, you'd have to manually edit:

```
parent/pom.xml          → change <version>1.0-SNAPSHOT</version>
component1/pom.xml      → change <version>, <parent><version>, <dependency><version>
component2/pom.xml      → change <version>, <parent><version>
... every pom.xml in every module
```

> **From Lecture**: "This way of doing it manually could be tedious because you need to know all the pom.xml that are available, and in the pom.xml you have to change all the references — here, here, here, and if you have a dependency you have to change this too."

### The Solution: `versions:set` Plugin

Maven has a built-in plugin that changes all versions across the entire project:

```bash
mvn versions:set -DnewVersion=2.3.1
```

**Breaking down the command:**

| Part | Meaning |
|------|---------|
| `versions:set` | Built-in plugin goal — sets the version across all project files |
| `-D` | Flag that means "pass a parameter to Maven" |
| `newVersion` | The parameter name the plugin expects |
| `2.3.1` | The value to set |

> **From Lecture**: "`-D` represents that you are passing a parameter. For that parameter, what is the name of the parameter, equals what is the value of the parameter."

**The `-D` flag works for any Maven parameter:**
```bash
mvn <goal> -D<parameterName>=<value>

# Examples:
mvn versions:set -DnewVersion=2.3.1
mvn test -DskipTests=true
mvn package -Dmaven.test.skip=true
```

### Running from the Parent (Multi-Module)

When you run `versions:set` from the parent directory, it applies to ALL modules automatically — this is the multi-module concept from the previous lecture:

```bash
cd my-project          # Go to parent directory
mvn versions:set -DnewVersion=2.3.1

# Output:
# [INFO] --- versions:set ---
# [INFO] Updating project my-project (parent)
# [INFO]   from version 1.0-SNAPSHOT to 2.3.1
# [INFO] Updating project component1
# [INFO]   from version 1.0-SNAPSHOT to 2.3.1
# [INFO] Updating project component2
# [INFO]   from version 1.0-SNAPSHOT to 2.3.1
```

### The Backup Mechanism

When `versions:set` runs, it creates a backup of every pom.xml it modifies:

```
component1/
├── pom.xml                    ← Modified (now has version 2.3.1)
└── pom.xml.versionsBackup     ← Copy of original (still has 1.0-SNAPSHOT)

component2/
├── pom.xml                    ← Modified
└── pom.xml.versionsBackup     ← Copy of original
```

> **From Lecture**: "It has taken a backup of the existing file. And if you go to each of the files, it would have got modified — everywhere it would have got modified as the specific version."

### Build the Release

After setting the version, build with `mvn install` (not `package`):

```bash
mvn install

# Output:
# [INFO] Reactor Build Order:
# [INFO]   my-project
# [INFO]   component2                    ← Built first (dependency)
# [INFO]   component1                    ← Built second
#
# [INFO] --- Building component2 2.3.1 ---
# [INFO] Installing component2-2.3.1.jar to ~/.m2/repository
#
# [INFO] --- Building component1 2.3.1 ---
# [INFO] Installing component1-2.3.1.jar to ~/.m2/repository
```

**Why `install` and not `package`?** Component1 depends on Component2. After version change, Component2's artifact is `component2-2.3.1.jar` — this must be in the local repository for Component1 to find it.

The output artifacts now have the release version:
```
component1/target/component1-2.3.1.jar    ← Ship this to customer
component2/target/component2-2.3.1.jar    ← Ship this to customer
```

### After Release: `versions:commit` or `versions:revert`

After building the release, you have two choices:

**Option 1: `versions:commit`** — Keep the version change permanently

```bash
mvn versions:commit
```

This deletes all `.versionsBackup` files, making the version change permanent. Use this when you want to commit the release version to Git.

**Option 2: `versions:revert`** — Go back to development version

```bash
mvn versions:revert

# What happens internally:
# 1. Deletes pom.xml (the modified file with 2.3.1)
# 2. Renames pom.xml.versionsBackup → pom.xml
# 3. All modules are back to 1.0-SNAPSHOT
```

> **From Lecture**: "Revert means it is going to delete the file and replace the backup as the original file. That is what ideally it is going to do."

After reverting, a build creates snapshot files again:
```bash
mvn install
# Creates: component1-1.0-SNAPSHOT.jar
# Creates: component2-1.0-SNAPSHOT.jar
# = We are back to working on a development copy
```

### Complete Release Workflow (From Lecture)

```
Development (1.0-SNAPSHOT)
        │
        ▼
┌─ versions:set -DnewVersion=2.3.1 ──┐
│   Backup files created               │
│   All pom.xml updated to 2.3.1       │
└──────────────────────────────────────┘
        │
        ▼
┌─ mvn install ───────────────────────┐
│   Build component2-2.3.1.jar        │
│   Build component1-2.3.1.jar        │
│   Ship these JARs to customer       │
└──────────────────────────────────────┘
        │
        ├──► versions:commit (keep 2.3.1 in pom.xml, delete backups)
        │         └── Use when committing release to Git
        │
        └──► versions:revert (restore 1.0-SNAPSHOT from backups)
                  └── Use when continuing development
                          │
                          ▼
                  Back to Development (1.0-SNAPSHOT)
```

### Quick Reference

```bash
# Set a new version across all modules
mvn versions:set -DnewVersion=2.3.1

# Revert if something went wrong (restores from backup)
mvn versions:revert

# Commit the version change (removes backup pom.xml files)
mvn versions:commit

# Check for newer dependency versions
mvn versions:display-dependency-updates

# Check for newer plugin versions
mvn versions:display-plugin-updates
```

**Real-Life Release Pipeline:**

```bash
# 1. Change version from SNAPSHOT to release
mvn versions:set -DnewVersion=2.3.1
mvn versions:commit

# 2. Build the release artifact
mvn clean install

# 3. Tag in Git
git add -A
git commit -m "Release 2.3.1"
git tag v2.3.1
git push origin v2.3.1

# 4. Bump to next SNAPSHOT for development
mvn versions:set -DnewVersion=2.4.0-SNAPSHOT
mvn versions:commit
git add -A
git commit -m "Start 2.4.0-SNAPSHOT development"
git push
```

---

## 11.10 Hands-On Exercise

```bash
# 1. Add Maven Wrapper to your project
./mvnw clean package

# 2. Create a multi-stage Dockerfile
docker build -t my-app:1.0 .
docker run -p 8080:8080 my-app:1.0

# 3. Run OWASP dependency check
mvn dependency-check:check
# Review the HTML report

# 4. Set up SonarQube with Docker and run analysis
docker run -d -p 9000:9000 sonarqube:community
mvn sonar:sonar -Dsonar.host.url=http://localhost:9000
```

---

**Next:** [Module 12 — Capstone Project](12-capstone-project.md)
