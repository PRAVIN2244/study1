# Module 8: Multi-Module Projects — Parent POM, Child POM, and POM Inheritance

**Objective:** Understand how large projects use multiple `pom.xml` files, how parent and child POMs work, what gets inherited, and how to override settings.

---

## 8.1 Why Multi-Module?

Real applications aren't a single JAR. A banking platform might have:

```
banking-platform/                     ← Parent project (1 pom.xml)
├── pom.xml                           ← PARENT POM (Mother POM)
├── banking-common/                   ← Child module 1
│   └── pom.xml                       ← CHILD POM
├── banking-account-service/          ← Child module 2
│   └── pom.xml                       ← CHILD POM
├── banking-payment-service/          ← Child module 3
│   └── pom.xml                       ← CHILD POM
└── banking-notification-service/     ← Child module 4
    └── pom.xml                       ← CHILD POM
```

**That's 5 `pom.xml` files** — one parent and four children. Each child has its own source code, dependencies, and build output. The parent controls shared settings.

### Why Not One Big Project?

| Single Project | Multi-Module |
|---------------|-------------|
| One huge JAR with everything | Each service is a separate JAR |
| Change one file → rebuild everything | Change one module → rebuild only that module |
| One team works on everything | Different teams own different modules |
| Hard to deploy independently | Deploy each service independently |
| One failure breaks everything | Services are isolated |

**Real-Life Example:** At a company like Flipkart:
- `cart-service` team works on their module
- `payment-service` team works on their module
- Both share `common-utils` module
- Parent POM ensures everyone uses the same Spring Boot version

---

## 8.2 The Parent POM (Mother POM) — In Detail

The parent POM is the **controller**. It doesn't contain any Java code. Its job is to:

1. **List all child modules** (`<modules>`)
2. **Lock dependency versions** (`<dependencyManagement>`)
3. **Lock plugin versions** (`<pluginManagement>`)
4. **Define shared properties** (`<properties>`)
5. **Set the packaging to `pom`** (no JAR/WAR output)

### Complete Parent POM Example

```xml
<!-- banking-platform/pom.xml — THE PARENT (MOTHER) POM -->
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <!-- Parent's own identity -->
    <groupId>com.banking</groupId>
    <artifactId>banking-platform</artifactId>
    <version>1.0.0-SNAPSHOT</version>

    <!-- IMPORTANT: Parent packaging is always "pom" -->
    <!-- This means: "I don't produce a JAR/WAR. I only manage children." -->
    <packaging>pom</packaging>

    <!-- ============================================ -->
    <!-- 1. LIST OF CHILD MODULES                     -->
    <!-- ============================================ -->
    <!-- Maven will build these in dependency order -->
    <modules>
        <module>banking-common</module>
        <module>banking-account-service</module>
        <module>banking-payment-service</module>
        <module>banking-notification-service</module>
    </modules>

    <!-- ============================================ -->
    <!-- 2. SHARED PROPERTIES                         -->
    <!-- ============================================ -->
    <!-- All children inherit these -->
    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>${java.version}</maven.compiler.source>
        <maven.compiler.target>${java.version}</maven.compiler.target>
        <spring.boot.version>3.2.0</spring.boot.version>
        <junit.version>5.10.1</junit.version>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <!-- ============================================ -->
    <!-- 3. DEPENDENCY VERSION CONTROL                -->
    <!-- ============================================ -->
    <!-- dependencyManagement does NOT add dependencies -->
    <!-- It only LOCKS versions for children who choose to use them -->
    <dependencyManagement>
        <dependencies>
            <!-- Spring Boot BOM — manages 200+ dependency versions -->
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring.boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>

            <!-- Lock JUnit version for all children -->
            <dependency>
                <groupId>org.junit.jupiter</groupId>
                <artifactId>junit-jupiter</artifactId>
                <version>${junit.version}</version>
            </dependency>

            <!-- Lock internal module version -->
            <dependency>
                <groupId>com.banking</groupId>
                <artifactId>banking-common</artifactId>
                <version>${project.version}</version>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <!-- ============================================ -->
    <!-- 4. PLUGIN VERSION CONTROL                    -->
    <!-- ============================================ -->
    <!-- pluginManagement does NOT activate plugins -->
    <!-- It only LOCKS versions for children who choose to use them -->
    <build>
        <pluginManagement>
            <plugins>
                <plugin>
                    <artifactId>maven-compiler-plugin</artifactId>
                    <version>3.12.1</version>
                    <configuration>
                        <source>${java.version}</source>
                        <target>${java.version}</target>
                    </configuration>
                </plugin>
                <plugin>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>3.2.3</version>
                </plugin>
                <plugin>
                    <groupId>org.jacoco</groupId>
                    <artifactId>jacoco-maven-plugin</artifactId>
                    <version>0.8.11</version>
                </plugin>
            </plugins>
        </pluginManagement>
    </build>

</project>
```

### What `<packaging>pom</packaging>` Means

```
packaging=jar  → Maven produces a .jar file (default)
packaging=war  → Maven produces a .war file
packaging=pom  → Maven produces NOTHING — this project only manages children
```

The parent POM never has `src/main/java/`. It has no code. It's purely a management file.

---

## 8.3 The Child POM — In Detail

Each child module has its own `pom.xml` that:

1. **Points to the parent** using `<parent>` tag
2. **Inherits** groupId, version, properties, dependency versions, plugin versions
3. **Defines only what's unique** to this module (its own dependencies, its own packaging)

### Complete Child POM Example

```xml
<!-- banking-platform/banking-account-service/pom.xml — A CHILD POM -->
<project>
    <modelVersion>4.0.0</modelVersion>

    <!-- ============================================ -->
    <!-- POINT TO PARENT                              -->
    <!-- ============================================ -->
    <parent>
        <groupId>com.banking</groupId>           <!-- Parent's groupId -->
        <artifactId>banking-platform</artifactId> <!-- Parent's artifactId -->
        <version>1.0.0-SNAPSHOT</version>         <!-- Parent's version -->
        <!-- <relativePath>../pom.xml</relativePath>  Optional: path to parent pom -->
    </parent>

    <!-- ============================================ -->
    <!-- CHILD'S OWN IDENTITY                         -->
    <!-- ============================================ -->
    <!-- groupId: INHERITED from parent (com.banking) — no need to repeat -->
    <!-- version: INHERITED from parent (1.0.0-SNAPSHOT) — no need to repeat -->
    <artifactId>banking-account-service</artifactId>  <!-- MUST define — unique to this child -->
    <packaging>jar</packaging>

    <!-- ============================================ -->
    <!-- CHILD'S OWN DEPENDENCIES                     -->
    <!-- ============================================ -->
    <dependencies>
        <!-- Version NOT needed — inherited from parent's dependencyManagement -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <!-- Depend on sibling module -->
        <dependency>
            <groupId>com.banking</groupId>
            <artifactId>banking-common</artifactId>
            <!-- Version NOT needed — parent's dependencyManagement controls it -->
        </dependency>

        <!-- Version NOT needed — inherited from parent -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

</project>
```

### What the Child Must Define vs What It Inherits

| Element | Must Define? | Inherited from Parent? |
|---------|:-----------:|:---------------------:|
| `<parent>` | Yes | — |
| `<artifactId>` | Yes (unique per child) | No |
| `<groupId>` | No | Yes — inherits parent's groupId |
| `<version>` | No | Yes — inherits parent's version |
| `<packaging>` | Optional (defaults to `jar`) | No |
| `<properties>` | No | Yes — inherits all parent properties |
| Dependency versions | No | Yes — from `<dependencyManagement>` |
| Plugin versions | No | Yes — from `<pluginManagement>` |
| `<dependencies>` | Yes (only what this child needs) | No — each child picks its own |

**Key insight:** The child POM is much shorter than the parent because most settings are inherited.

### The `<parent>` Tag's Role in Build Order (From Lecture)

> **Key Insight from Lecture**: The `<parent>` tag does TWO things, not one!

Most tutorials only explain `<parent>` for **inheritance** (sharing versions, dependencies). But the lecture reveals its **second role**: enabling Maven to determine the correct **build order**.

**Without `<parent>` tag in children:**
```
Parent pom.xml:
<modules>
    <module>subtract</module>   <!-- listed first -->
    <module>add</module>         <!-- listed second -->
    <module>division</module>    <!-- listed third -->
</modules>

Child pom.xml (subtract): NO <parent> tag
Child pom.xml (add): NO <parent> tag
```

**Result**: Maven builds in **listing order** — subtract, add, division.
If subtract depends on add, the **build fails** because add hasn't been built yet. Maven has no way to know about dependencies between modules — it blindly follows the order you listed.

**With `<parent>` tag in children:**
```xml
<!-- subtract/pom.xml -->
<parent>
    <groupId>com.calculator</groupId>
    <artifactId>calculator-parent</artifactId>
    <version>1.0</version>
</parent>

<dependencies>
    <dependency>
        <groupId>com.calculator</groupId>
        <artifactId>add</artifactId>
        <version>1.0</version>
    </dependency>
</dependencies>
```

**Result**: Maven **scans all child POMs**, reads their `<dependencies>`, and builds in **dependency order** — add first, then subtract, then division — regardless of listing order.

**How it works:**
```
Without <parent>:                    With <parent>:
┌─────────────────────┐              ┌─────────────────────┐
│ Parent POM          │              │ Parent POM          │
│ modules:            │              │ modules:            │
│   - subtract        │              │   - subtract        │
│   - add             │              │   - add             │
│   - division        │              │   - division        │
│                     │              │                     │
│ Maven reads ONLY    │              │ Maven reads modules │
│ the listing order   │              │ THEN scans each     │
│                     │              │ child's <parent> +  │
│ Build: subtract →   │              │ <dependencies>      │
│ add → division      │              │                     │
│ (may fail!)         │              │ Build: add →        │
└─────────────────────┘              │ subtract → division │
                                     │ (correct order!)    │
                                     └─────────────────────┘
```

> **Rule**: Always add `<parent>` tag to child POMs. Without it, you lose both inheritance AND intelligent build ordering.

---

## 8.4 POM Inheritance — What Gets Inherited

When a child declares `<parent>`, it automatically inherits everything from the parent:

```
Parent POM defines:                    Child POM inherits:
────────────────────                   ────────────────────
groupId: com.banking            ──►   groupId: com.banking (automatic)
version: 1.0.0-SNAPSHOT         ──►   version: 1.0.0-SNAPSHOT (automatic)
properties:                     ──►   All properties available
  java.version=17                     ${java.version} = 17
  spring.boot.version=3.2.0          ${spring.boot.version} = 3.2.0
dependencyManagement:           ──►   Version locks available
  spring-boot = 3.2.0                (child uses without specifying version)
  junit = 5.10.1
pluginManagement:               ──►   Plugin configs available
  compiler-plugin = 3.12.1           (child uses without specifying version)
  surefire-plugin = 3.2.3
```

### The Inheritance Chain — Super POM

Maven has a hidden **Super POM** that every project inherits from, even if you don't declare a `<parent>`:

```
Super POM (built into Maven)
    │
    │  Provides: Maven Central repo URL, default plugin versions,
    │            default directory layout (src/main/java, etc.)
    │
    ▼
Your Parent POM (banking-platform/pom.xml)
    │
    │  Provides: groupId, version, properties,
    │            dependencyManagement, pluginManagement
    │
    ├──► Child 1: banking-common/pom.xml
    ├──► Child 2: banking-account-service/pom.xml
    ├──► Child 3: banking-payment-service/pom.xml
    └──► Child 4: banking-notification-service/pom.xml
```

### Seeing the Full Resolved POM (Effective POM)

To see everything a child inherits (including from Super POM), run:

```bash
cd banking-account-service
mvn help:effective-pom
```

This shows the **effective POM** — the complete, resolved POM with all inherited values filled in. It can be 500+ lines long because it includes everything from the Super POM, parent POM, and child POM merged together.

```bash
# Save it to a file for reading
mvn help:effective-pom -Doutput=effective-pom.xml
cat effective-pom.xml
```

---

## 8.5 `<dependencyManagement>` vs `<dependencies>` — The Difference

This is one of the most confusing concepts. Here's the clear distinction:

| Aspect | `<dependencyManagement>` | `<dependencies>` |
|--------|------------------------|-------------------|
| **Where** | Parent POM | Parent or Child POM |
| **Does it add the dependency?** | **No** — only locks the version | **Yes** — actually adds it to the project |
| **Purpose** | "If any child uses this, use version X" | "This project needs this library" |
| **Effect on child** | Child can use it without specifying version | Child gets the dependency automatically |

### Example — How They Work Together

**Parent POM:**
```xml
<!-- This does NOT add Spring Boot to any child -->
<!-- It only says: "IF a child uses Spring Boot, use version 3.2.0" -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.2.0</version>
        </dependency>
    </dependencies>
</dependencyManagement>
```

**Child POM:**
```xml
<!-- This ADDS Spring Boot to this child -->
<!-- No version needed — parent's dependencyManagement provides it -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <!-- version 3.2.0 inherited from parent -->
    </dependency>
</dependencies>
```

**Real-Life Analogy:**
- `<dependencyManagement>` = A company policy: "All teams must use Spring Boot 3.2.0"
- `<dependencies>` = A team actually using Spring Boot in their project

The policy doesn't force anyone to use Spring Boot. But if they do, they must use version 3.2.0.

---

## 8.6 `<pluginManagement>` vs `<plugins>` — The Difference

Same concept as dependencies:

| Aspect | `<pluginManagement>` | `<plugins>` |
|--------|---------------------|-------------|
| **Where** | Parent POM | Parent or Child POM |
| **Does it activate the plugin?** | **No** — only locks version and config | **Yes** — actually runs the plugin |
| **Purpose** | "If any child uses this plugin, use this version and config" | "This project uses this plugin" |

**Parent POM:**
```xml
<build>
    <!-- Does NOT activate JaCoCo — only locks its version -->
    <pluginManagement>
        <plugins>
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.11</version>
            </plugin>
        </plugins>
    </pluginManagement>
</build>
```

**Child POM (only if this child wants JaCoCo):**
```xml
<build>
    <!-- Actually activates JaCoCo for this child -->
    <plugins>
        <plugin>
            <groupId>org.jacoco</groupId>
            <artifactId>jacoco-maven-plugin</artifactId>
            <!-- version 0.8.11 inherited from parent -->
            <executions>
                <execution>
                    <goals><goal>prepare-agent</goal></goals>
                </execution>
                <execution>
                    <id>report</id>
                    <phase>test</phase>
                    <goals><goal>report</goal></goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

---

## 8.7 Child Overriding Parent Settings

A child can **override** anything inherited from the parent:

### Overriding a Dependency Version

```xml
<!-- Parent locks Jackson to 2.16.0 -->
<!-- But this child needs 2.17.0 for a specific feature -->
<dependencies>
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.17.0</version>  <!-- Overrides parent's 2.16.0 -->
    </dependency>
</dependencies>
```

### Overriding a Property

```xml
<!-- Parent sets java.version=17 -->
<!-- But this legacy child needs Java 11 -->
<properties>
    <java.version>11</java.version>  <!-- Overrides parent's 17 -->
</properties>
```

### Overriding a Plugin Configuration

```xml
<!-- Parent sets compiler source=17 -->
<!-- But this child needs source=11 -->
<build>
    <plugins>
        <plugin>
            <artifactId>maven-compiler-plugin</artifactId>
            <configuration>
                <source>11</source>   <!-- Overrides parent's 17 -->
                <target>11</target>
            </configuration>
        </plugin>
    </plugins>
</build>
```

**Rule:** Child always wins. If a child defines something that the parent also defines, the child's value takes priority.

---

## 8.8 Multiple pom.xml Files — How They Relate

Here's how all the `pom.xml` files connect in a real project:

```
Super POM (hidden, built into Maven)
│
│ Provides: Maven Central URL, default directories, default plugins
│
▼
banking-platform/pom.xml  ← PARENT POM
│
│ Provides: groupId, version, properties, dependencyManagement, pluginManagement
│ Packaging: pom (no artifact)
│ Lists: <modules> — all children
│
├──► banking-common/pom.xml  ← CHILD POM
│    │ Inherits: groupId, version, properties, dep versions, plugin versions
│    │ Defines: artifactId=banking-common, packaging=jar
│    │ Adds: its own dependencies
│    │ Output: banking-common-1.0.0-SNAPSHOT.jar
│    │
├──► banking-account-service/pom.xml  ← CHILD POM
│    │ Inherits: everything from parent
│    │ Defines: artifactId=banking-account-service
│    │ Adds: spring-boot-starter-web, banking-common dependency
│    │ Output: banking-account-service-1.0.0-SNAPSHOT.jar
│    │
├──► banking-payment-service/pom.xml  ← CHILD POM
│    │ Inherits: everything from parent
│    │ Defines: artifactId=banking-payment-service
│    │ Adds: spring-boot-starter-web, banking-common dependency
│    │ Output: banking-payment-service-1.0.0-SNAPSHOT.jar
│    │
└──► banking-notification-service/pom.xml  ← CHILD POM
     │ Inherits: everything from parent
     │ Defines: artifactId=banking-notification-service
     │ Adds: spring-boot-starter-mail
     │ Output: banking-notification-service-1.0.0-SNAPSHOT.jar
```

### What Happens When You Run `mvn clean package` from the Parent

```bash
cd banking-platform
mvn clean package

# Maven reads parent pom.xml
# Finds <modules> list
# Determines build order based on inter-module dependencies
# Builds each child in order:

# [INFO] Reactor Build Order:
# [INFO]   banking-platform                 (parent — no artifact)
# [INFO]   banking-common                   (built first — no sibling deps)
# [INFO]   banking-account-service          (depends on common)
# [INFO]   banking-payment-service          (depends on common)
# [INFO]   banking-notification-service     (depends on common)
#
# [INFO] BUILD SUCCESS
# [INFO] Total time: 25 seconds
```

---

## 8.9 Building Multi-Module Projects

```bash
# Build everything from the root
cd banking-platform
mvn clean package

# Build only a specific module (and its dependencies)
mvn clean package -pl banking-account-service -am
# -pl = project list (which module to build)
# -am = also make (build dependencies of that module too)

# Build a module WITHOUT its dependencies
mvn clean package -pl banking-account-service

# Skip a module
mvn clean package -pl !banking-notification-service

# Resume build from a failed module
mvn clean package -rf :banking-payment-service
```

**Real-Life Scenario:** In CI, a developer changes only `banking-account-service`. Instead of building all 4 modules (which takes 10 minutes), you build only the changed module:

```bash
mvn clean package -pl banking-account-service -am
# Takes 2 minutes instead of 10
```

---

## 8.10 Complete Walkthrough from the Lecture — Step by Step

This follows the exact flow from the lecture. We'll create a `demo` project with `add` and `subtract` modules, see dependency failures, fix them, and set up the parent POM.

### Step 1: Create the Project Folder and Module Folders

```bash
# Create the parent project folder
mkdir demo && cd demo

# Create module folders
mkdir add
mkdir subtract
```

```
demo/                    ← Parent project folder
├── add/                 ← Module 1 folder (empty for now)
└── subtract/            ← Module 2 folder (empty for now)
```

### Step 2: Create the `add` Module (First Child)

Each module needs its own `pom.xml` and `src/` directory structure — it becomes a "mini project":

```bash
# Create directory structure for add module
mkdir -p add/src/main/java/com/company/add
mkdir -p add/src/test/java/com/company/add
```

Create `add/pom.xml` — change the `artifactId` to `add`:

```xml
<!-- demo/add/pom.xml -->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.company</groupId>
    <artifactId>add</artifactId>           <!-- Changed from "demo" to "add" -->
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

Create the Java source file:

```java
// demo/add/src/main/java/com/company/add/AddService.java
package com.company.add;

public class AddService {
    public int add(int a, int b) {
        return a + b;
    }
}
```

**Build the add module individually:**

```bash
cd add
mvn package

# Output:
# [INFO] Building add 1.0-SNAPSHOT
# [INFO] --- maven-compiler-plugin:compile ---
# [INFO] Compiling 1 source file
# [INFO] --- maven-jar-plugin:jar ---
# [INFO] Building jar: demo/add/target/add-1.0-SNAPSHOT.jar
# [INFO] BUILD SUCCESS
```

Result: `add/target/add-1.0-SNAPSHOT.jar` is created.

### Step 3: Create the `subtract` Module (Second Child)

```bash
cd ../subtract
mkdir -p src/main/java/com/company/subtract
mkdir -p src/test/java/com/company/subtract
```

Create `subtract/pom.xml` — change `artifactId` to `subtract`:

```xml
<!-- demo/subtract/pom.xml -->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.company</groupId>
    <artifactId>subtract</artifactId>      <!-- Changed to "subtract" -->
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <dependencies>
        <!-- JUnit (default) -->
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>

        <!-- Depends on the "add" module -->
        <dependency>
            <groupId>com.company</groupId>
            <artifactId>add</artifactId>
            <version>1.0-SNAPSHOT</version>
        </dependency>
    </dependencies>
</project>
```

### Step 4: Build subtract — IT FAILS (Dependency Not Found)

```bash
cd subtract
mvn package

# OUTPUT — BUILD FAILURE:
# [ERROR] Failed to execute goal: Could not resolve dependencies
# [ERROR]   com.company:add:jar:1.0-SNAPSHOT
# [ERROR]
# [ERROR] Could not find artifact com.company:add:jar:1.0-SNAPSHOT
# [ERROR]   in central (https://repo.maven.apache.org/maven2)
```

**Why does it fail?** Maven looks for `add-1.0-SNAPSHOT.jar` in:
1. Local repository (`~/.m2/repository`) — NOT FOUND
2. Remote repository (Maven Central) — NOT FOUND (it's our project, not open-source)

The JAR exists in `add/target/add-1.0-SNAPSHOT.jar`, but Maven doesn't look in other module's `target/` folders. It only looks in the local repository.

### Step 5: Fix It — Install the `add` Module First

```bash
# Go to the add module
cd ../add

# Install copies the JAR from target/ to ~/.m2/repository/
mvn install

# Output:
# [INFO] --- maven-install-plugin:install ---
# [INFO] Installing demo/add/target/add-1.0-SNAPSHOT.jar
#        to ~/.m2/repository/com/company/add/1.0-SNAPSHOT/add-1.0-SNAPSHOT.jar
# [INFO] Installing demo/add/pom.xml
#        to ~/.m2/repository/com/company/add/1.0-SNAPSHOT/add-1.0-SNAPSHOT.pom
```

Maven copies TWO files to the local repository:
- `add-1.0-SNAPSHOT.jar` — the compiled module
- `add-1.0-SNAPSHOT.pom` — the pom.xml (needed as reference for dependencies)

### Step 6: Build subtract Again — IT SUCCEEDS

```bash
cd ../subtract
mvn package

# Output:
# [INFO] Building subtract 1.0-SNAPSHOT
# [INFO] --- maven-compiler-plugin:compile ---
# [INFO] Compiling 1 source file
# [INFO] --- maven-jar-plugin:jar ---
# [INFO] Building jar: demo/subtract/target/subtract-1.0-SNAPSHOT.jar
# [INFO] BUILD SUCCESS
```

Maven found `add-1.0-SNAPSHOT.jar` in the local repository and used it.

### Step 7: Create the Parent POM

Going into each module folder and building one by one is tedious. The parent POM solves this.

Create `demo/pom.xml` (the parent):

```xml
<!-- demo/pom.xml — PARENT POM -->
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.company</groupId>
    <artifactId>demo</artifactId>
    <version>1.0-SNAPSHOT</version>

    <!-- packaging=pom means: "I don't compile anything.
         I only pass goals to my child modules." -->
    <packaging>pom</packaging>

    <!-- List all modules the parent should handle -->
    <modules>
        <module>add</module>
        <module>subtract</module>
    </modules>
</project>
```

**The parent POM has NO `src/` folder.** It doesn't compile code. Its only job is:
1. Pass whatever goal you give it to ALL child modules
2. Determine the correct build order based on dependencies

### Step 8: Build Everything from the Parent

```bash
cd demo    # Go to parent directory
mvn install    # Use install, NOT package!

# Output:
# [INFO] Reactor Build Order:
# [INFO]   demo                    (pom — parent, no compilation)
# [INFO]   add                     (built FIRST — no dependencies)
# [INFO]   subtract                (built SECOND — depends on add)
#
# [INFO] --- Building add 1.0-SNAPSHOT ---
# [INFO] Compiling 1 source file
# [INFO] Building jar: add/target/add-1.0-SNAPSHOT.jar
# [INFO] Installing add-1.0-SNAPSHOT.jar to ~/.m2/repository
#
# [INFO] --- Building subtract 1.0-SNAPSHOT ---
# [INFO] Compiling 1 source file
# [INFO] Building jar: subtract/target/subtract-1.0-SNAPSHOT.jar
# [INFO] Installing subtract-1.0-SNAPSHOT.jar to ~/.m2/repository
#
# [INFO] BUILD SUCCESS
```

**Why `mvn install` and not `mvn package`?**

```bash
# mvn package from parent:
#   1. Builds add → creates add-1.0-SNAPSHOT.jar in add/target/
#   2. Builds subtract → FAILS! add-1.0-SNAPSHOT.jar is NOT in local repo
#      (package doesn't copy to local repo, only install does)

# mvn install from parent:
#   1. Builds add → creates JAR → copies to ~/.m2/repository ← KEY STEP
#   2. Builds subtract → finds add in local repo → SUCCEEDS
```

Maven passes the SAME goal to ALL modules. If you say `mvn install`, every module gets `install`. If you say `mvn package`, every module gets `package` — but then dependencies between modules won't be available in the local repo.

**Rule: Always use `mvn install` (or `mvn clean install`) when building multi-module projects from the parent.**

### Step 9: Adding a Third Module — Division (From Lecture)

Add a third module to demonstrate build ordering with multiple dependencies:

```
demo/
├── pom.xml (parent)
├── add/
│   └── pom.xml
├── subtract/
│   └── pom.xml
└── division/          ← NEW third module
    └── pom.xml
```

**division/pom.xml:**
```xml
<project>
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>com.company</groupId>
        <artifactId>demo</artifactId>
        <version>1.0-SNAPSHOT</version>
    </parent>

    <artifactId>division</artifactId>

    <dependencies>
        <dependency>
            <groupId>com.company</groupId>
            <artifactId>subtract</artifactId>
            <version>1.0-SNAPSHOT</version>
        </dependency>
    </dependencies>
</project>
```

**Update parent pom.xml to include division:**
```xml
<modules>
    <module>add</module>
    <module>subtract</module>
    <module>division</module>
</modules>
```

**Run `mvn install` from parent:**
```
$ cd demo
$ mvn install

[INFO] Reactor Build Order:
[INFO]   demo                    (pom — parent)
[INFO]   add                     ← Built FIRST (no dependencies)
[INFO]   subtract                ← Built SECOND (depends on add)
[INFO]   division                ← Built THIRD (depends on subtract)

[INFO] BUILD SUCCESS
```

Each module goes through the FULL lifecycle (compile → test → package → install) before the next module starts.

### Step 10: Proving Listing Order Doesn't Matter

Deliberately reorder modules in parent pom.xml:

```xml
<!-- INTENTIONALLY "wrong" order -->
<modules>
    <module>division</module>    <!-- depends on subtract — listed FIRST -->
    <module>subtract</module>    <!-- depends on add — listed SECOND -->
    <module>add</module>         <!-- no dependencies — listed LAST -->
</modules>
```

**Run `mvn install`:**
```
[INFO] Reactor Build Order:
[INFO]   demo
[INFO]   add                    ← Still built FIRST!
[INFO]   subtract               ← Still built SECOND!
[INFO]   division               ← Still built THIRD!

[INFO] BUILD SUCCESS
```

> Maven ignores your listing order when `<parent>` tags are present. It scans all child POMs, reads their `<dependencies>`, and creates a **dependency graph** to determine the correct build order.

**Without `<parent>` tags**, the same reordered listing would fail:
```
[INFO] Reactor Build Order:
[INFO]   division               ← Built first (as listed)
[INFO]   ERROR: Could not resolve dependency: subtract
[INFO] BUILD FAILURE
```

### Step 11: The Same-Goal Limitation

When you run a command from the parent directory, the **same goal is passed to ALL modules**:

```bash
$ cd demo
$ mvn install    # ALL modules get "install"
```

You **cannot** do this from the parent:
```
# NOT POSSIBLE from parent:
# "compile add, but package subtract, and install division"
```

Every module receives the SAME lifecycle phase.

**Workaround — The `-pl` flag** (covered in section 8.9):
```bash
# Build ONLY subtract (without cd-ing into its folder)
mvn install -pl subtract

# Build subtract AND all modules it depends on
mvn install -pl subtract -am

# Skip a specific module
mvn install -pl !division
```

### Final Project Structure

```
demo/                              ← Parent project
├── pom.xml                        ← PARENT POM (packaging=pom, lists modules)
├── add/                           ← Child module 1
│   ├── pom.xml                    ← CHILD POM (artifactId=add)
│   ├── src/main/java/...          ← Source code
│   └── target/
│       └── add-1.0-SNAPSHOT.jar   ← Build output
├── subtract/                      ← Child module 2
│   ├── pom.xml                    ← CHILD POM (artifactId=subtract, depends on add)
│   ├── src/main/java/...          ← Source code
│   └── target/
│       └── subtract-1.0-SNAPSHOT.jar  ← Build output
└── division/                      ← Child module 3
    ├── pom.xml                    ← CHILD POM (artifactId=division, depends on subtract)
    ├── src/main/java/...          ← Source code
    └── target/
        └── division-1.0-SNAPSHOT.jar  ← Build output
```

---

## 8.11 Hands-On Exercise

```bash
# 1. Create the calculator project above (parent + add + subtract)
# 2. Build from root: mvn clean install
# 3. Check local repo: ls ~/.m2/repository/com/company/add/1.0-SNAPSHOT/
# 4. Build only subtract: mvn clean package -pl subtract -am
# 5. See effective POM: cd add && mvn help:effective-pom
# 6. Add a third module "multiply" that depends on "add"
# 7. Rebuild from root and observe the reactor order
```

---

**Next:** [Module 9 — Repository Management](09-repository-management.md)
