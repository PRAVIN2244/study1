# Module 4: Dependency Management

**Objective:** Understand how Maven resolves, downloads, and manages project dependencies.

---

## 4.1 How Dependencies Work

When you add a dependency to `pom.xml`, Maven:
1. Checks `~/.m2/repository` (local cache)
2. If not found, downloads from Maven Central (`https://repo.maven.apache.org/maven2`)
3. Also downloads that dependency's dependencies (transitive dependencies)

```xml
<dependencies>
    <!-- Direct dependency -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>
</dependencies>
```

This single dependency pulls in ~30+ transitive dependencies (Spring Core, Tomcat, Jackson, etc.).

### Real-Life Example — Banking Application Dependencies

A banking application may depend on dozens of frameworks. Maven resolves all of them automatically:

```xml
<dependencies>
    <!-- Web framework -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- Database access (Hibernate ORM) -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- Security (authentication, authorization) -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- Logging -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-logging</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- MySQL database driver -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
        <version>8.0.33</version>
        <scope>runtime</scope>
    </dependency>

    <!-- Testing -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <version>3.2.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

These 6 direct dependencies pull in **100+ transitive dependencies** automatically. Maven downloads, caches, and manages all of them. Without Maven, a developer would need to manually download and manage 100+ JAR files.

---

## 4.2 Dependency Scopes

| Scope | Compile Classpath | Test Classpath | Runtime Classpath | Packaged in JAR/WAR | Use Case |
|-------|:-:|:-:|:-:|:-:|----------|
| `compile` (default) | Yes | Yes | Yes | Yes | Most libraries |
| `provided` | Yes | Yes | No | No | Servlet API (Tomcat provides it) |
| `runtime` | No | Yes | Yes | Yes | JDBC drivers |
| `test` | No | Yes | No | No | JUnit, Mockito |
| `system` | Yes | Yes | No | No | Local JARs (avoid this) |

**Real-Life Example:** A web app deployed to Tomcat:

```xml
<!-- Tomcat provides the Servlet API, so don't package it -->
<dependency>
    <groupId>javax.servlet</groupId>
    <artifactId>javax.servlet-api</artifactId>
    <version>4.0.1</version>
    <scope>provided</scope>
</dependency>

<!-- MySQL driver is needed at runtime but not compile time -->
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
    <scope>runtime</scope>
</dependency>

<!-- JUnit is only for testing -->
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.10.1</version>
    <scope>test</scope>
</dependency>
```

---

## 4.3 SNAPSHOT vs RELEASE Versions

Every Maven artifact has a version. There are two types:

| Type | Example | Meaning | Mutable? |
|------|---------|---------|----------|
| **SNAPSHOT** | `1.0-SNAPSHOT` | Development version — still being worked on | Yes — can be overwritten |
| **RELEASE** | `1.0` | Final version — production-ready | No — immutable, never changes |

### Version Format

Maven versions follow the pattern: `major.minor.patch`

```
2.3.1
│ │ │
│ │ └── patch (bug fixes)
│ └──── minor (new features, backward compatible)
└────── major (breaking changes)
```

- `1.0-SNAPSHOT` → development version of 1.0
- `1.0` → released, final version of 1.0
- `1.1-SNAPSHOT` → development starts for next version

### The Problem SNAPSHOT Solves — From the Lecture

Imagine Component A and Component B in your project. B depends on A.

**Without SNAPSHOT (using release versions):**

```
Step 1: A has version 1.0
        A builds: a-1.0.jar
        B's pom.xml says: I need a-1.0.jar
        B builds successfully.

Step 2: Developer changes A's code.
        A changes version to 1.1
        A builds: a-1.1.jar
        A runs: mvn install (puts a-1.1.jar in local repo)
        B's pom.xml STILL says: I need a-1.0.jar  ← WRONG! Must update to 1.1
        Developer must edit B's pom.xml to change 1.0 → 1.1

Step 3: Developer changes A's code again.
        A changes version to 1.2
        A builds: a-1.2.jar
        A runs: mvn install
        B's pom.xml STILL says: I need a-1.1.jar  ← WRONG AGAIN! Must update to 1.2

... This repeats for EVERY change. Impractical.
```

**With SNAPSHOT:**

```
Step 1: A has version 1.0-SNAPSHOT
        A builds: a-1.0-SNAPSHOT.jar
        B's pom.xml says: I need a-1.0-SNAPSHOT.jar
        B builds successfully.

Step 2: Developer changes A's code.
        A KEEPS version 1.0-SNAPSHOT (no change!)
        A builds: a-1.0-SNAPSHOT.jar (same name, new content)
        A runs: mvn install (REPLACES old a-1.0-SNAPSHOT.jar in local repo)
        B's pom.xml STILL says: I need a-1.0-SNAPSHOT.jar  ← STILL CORRECT!
        B automatically picks up the latest build. No pom.xml change needed.

Step 3: Developer changes A's code again.
        Same thing — no version change, no pom.xml update needed.
```

**SNAPSHOT = the file name stays the same, but the content gets replaced with every build.** This is why it's called a "development copy" — you keep rebuilding it without changing the version number.

### Why SNAPSHOT Matters — Multi-Module Example

In a multi-module project, Module B depends on Module A:

```
calculator/
├── add/          (Module A — version 1.0-SNAPSHOT)
└── subtract/     (Module B — depends on Module A)
```

**Module A's `pom.xml`:**
```xml
<groupId>com.company</groupId>
<artifactId>add</artifactId>
<version>1.0-SNAPSHOT</version>
```

**Module B's `pom.xml`:**
```xml
<dependencies>
  <dependency>
    <groupId>com.company</groupId>
    <artifactId>add</artifactId>
    <version>1.0-SNAPSHOT</version>
  </dependency>
</dependencies>
```

**How it works:**

```bash
# Step 1: Build Module A and install to local repo
cd add
mvn install
# → add-1.0-SNAPSHOT.jar stored in ~/.m2/repository/com/company/add/1.0-SNAPSHOT/

# Step 2: Build Module B — it finds Module A in local repo
cd ../subtract
mvn compile
# → Maven finds add-1.0-SNAPSHOT.jar in ~/.m2/repository
# → Module B compiles successfully
```

**Without SNAPSHOT:** If Module A used version `1.0` (release), every time a developer changed Module A, they would need to manually bump the version to `1.1`, `1.2`, etc. With SNAPSHOT, Maven automatically picks up the latest build — no version bumping needed during development.

**When to switch from SNAPSHOT to RELEASE:**
```
Development:  payment-lib:2.1.0-SNAPSHOT  (changes daily)
Release:      payment-lib:2.1.0           (frozen, shipped to production)
Next cycle:   payment-lib:2.2.0-SNAPSHOT  (development continues)
```

---

## 4.4 Viewing the Dependency Tree

This is one of the most useful commands for DevOps troubleshooting:

```bash
# Full dependency tree
mvn dependency:tree

# Example output:
# com.mycompany:my-app:jar:1.0-SNAPSHOT
# +- org.springframework.boot:spring-boot-starter-web:jar:3.2.0:compile
# |  +- org.springframework.boot:spring-boot-starter:jar:3.2.0:compile
# |  |  +- org.springframework.boot:spring-boot:jar:3.2.0:compile
# |  |  +- org.springframework.boot:spring-boot-autoconfigure:jar:3.2.0:compile
# |  +- org.springframework.boot:spring-boot-starter-tomcat:jar:3.2.0:compile
# |  |  +- org.apache.tomcat.embed:tomcat-embed-core:jar:10.1.16:compile

# Filter for a specific dependency
mvn dependency:tree -Dincludes=org.apache.tomcat*
```

**Real-Life Scenario:** A build fails with `ClassNotFoundException` for `com.fasterxml.jackson.core.JsonParser`. You run `mvn dependency:tree -Dincludes=com.fasterxml.jackson*` and discover two different versions of Jackson are being pulled in by different dependencies. This is a **version conflict**.

---

## 4.5 Resolving Dependency Conflicts

```xml
<!-- Exclude a transitive dependency -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <version>3.2.0</version>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>

<!-- Use Jetty instead of Tomcat -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jetty</artifactId>
    <version>3.2.0</version>
</dependency>
```

---

## 4.6 The `<dependencyManagement>` Section

Used in parent POMs to lock dependency versions without actually adding them:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.16.0</version>  <!-- All child modules use this version -->
        </dependency>
    </dependencies>
</dependencyManagement>
```

Child modules then declare the dependency without a version:

```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <!-- version inherited from parent's dependencyManagement -->
</dependency>
```

---

## 4.7 How to Add a New Dependency — Step by Step

When your project needs a new library (e.g., you need to send emails using JavaMail), follow these steps:

### Step 1: Find the Dependency

Go to one of these websites:
- [https://mvnrepository.com](https://mvnrepository.com) — most popular, shows usage stats
- [https://search.maven.org](https://search.maven.org) — official Maven Central search

Search for the library name (e.g., "javax mail" or "spring boot starter mail").

### Step 2: Copy the Dependency XML

The website shows the exact XML to copy. Example for JavaMail:

```xml
<dependency>
    <groupId>com.sun.mail</groupId>
    <artifactId>javax.mail</artifactId>
    <version>1.6.2</version>
</dependency>
```

### Step 3: Add to Your `pom.xml`

Open your `pom.xml` and paste inside the `<dependencies>` section:

```xml
<dependencies>
    <!-- Existing dependencies... -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- NEW: Add JavaMail for sending emails -->
    <dependency>
        <groupId>com.sun.mail</groupId>
        <artifactId>javax.mail</artifactId>
        <version>1.6.2</version>
    </dependency>
</dependencies>
```

### Step 4: Maven Downloads It Automatically

```bash
# Option 1: Compile — Maven downloads missing dependencies
mvn compile

# Option 2: Download only (no compile)
mvn dependency:resolve

# You'll see in the output:
# Downloading from central: https://repo.maven.apache.org/.../javax.mail-1.6.2.jar
# Downloaded from central: javax.mail-1.6.2.jar (595 KB)
```

### Step 5: Verify It Was Added

```bash
# See the full dependency tree
mvn dependency:tree

# Output:
# com.company:my-app:jar:1.0-SNAPSHOT
# +- org.springframework.boot:spring-boot-starter-web:jar:3.2.0
# |  +- org.springframework.boot:spring-boot-starter:jar:3.2.0
# |  +- org.springframework:spring-web:jar:6.1.0
# |  \- org.apache.tomcat.embed:tomcat-embed-core:jar:10.1.16
# \- com.sun.mail:javax.mail:jar:1.6.2          ← Your new dependency
#    \- javax.activation:activation:jar:1.1      ← Its transitive dependency
```

### Step 6: Use It in Your Code

```java
import javax.mail.*;  // Now available because Maven added the JAR

public class EmailService {
    public void sendEmail(String to, String subject, String body) {
        // JavaMail code here
    }
}
```

### Complete Flow Diagram

```
Step 1: Search mvnrepository.com
            ↓
Step 2: Copy <dependency> XML
            ↓
Step 3: Paste into pom.xml <dependencies> section
            ↓
Step 4: Run mvn compile (or mvn dependency:resolve)
            ↓
Step 5: Maven checks ~/.m2/repository (local cache)
            ↓
        Found? → Use cached JAR
        Not found? → Download from Maven Central (or Nexus)
            ↓
Step 6: JAR stored in ~/.m2/repository
            ↓
Step 7: JAR added to project classpath
            ↓
Step 8: You can now import and use the library in your code
```

### Adding a Dependency with a Specific Scope

```xml
<!-- Available during compile AND runtime (default) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <version>3.2.0</version>
</dependency>

<!-- Available ONLY during testing -->
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.10.1</version>
    <scope>test</scope>
</dependency>

<!-- Available during compile but NOT packaged in JAR (server provides it) -->
<dependency>
    <groupId>jakarta.servlet</groupId>
    <artifactId>jakarta.servlet-api</artifactId>
    <version>6.0.0</version>
    <scope>provided</scope>
</dependency>

<!-- Available ONLY at runtime (not needed for compilation) -->
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
    <scope>runtime</scope>
</dependency>
```

### Useful Commands After Adding Dependencies

```bash
# See all dependencies (including transitive)
mvn dependency:tree

# Find unused dependencies in your code
mvn dependency:analyze

# Download all dependencies without building
mvn dependency:resolve

# Copy all dependency JARs to a folder
mvn dependency:copy-dependencies -DoutputDirectory=target/libs

# Check for newer versions of your dependencies
mvn versions:display-dependency-updates
```

---

## 4.8 Hands-On Exercise

```bash
# 1. Create a new Maven project: mvn archetype:generate -DarchetypeArtifactId=maven-archetype-quickstart -DgroupId=com.demo -DartifactId=dep-demo -DinteractiveMode=false
# 2. Go to mvnrepository.com and search for "gson" (Google's JSON library)
# 3. Copy the dependency XML and add it to pom.xml
# 4. Run: mvn dependency:tree — see gson appear
# 5. Add spring-boot-starter-web and run dependency:tree again — count transitive deps
# 6. Run: mvn dependency:analyze — see which deps are unused
# 7. Check for updates: mvn versions:display-dependency-updates
```

---

**Next:** [Module 5 — Build Lifecycle and Phases](../part-2-core-build/05-build-lifecycle.md)
