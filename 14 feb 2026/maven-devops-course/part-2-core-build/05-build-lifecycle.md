# Module 5: Maven Build Lifecycle, Phases, and Goals

**Objective:** Understand what happens when you run `mvn package`, the three lifecycles, what goals are, and how goals relate to plugins.

---

## 5.1 The Three Built-in Lifecycles

Maven has **three independent lifecycles**. Each lifecycle is a sequence of phases that run in order.

### 1. Clean Lifecycle — Remove Old Build Output

```bash
mvn clean
```

This deletes the `target/` directory (all compiled files, JARs, WARs from previous builds).

**When to use:** Almost always. Run `mvn clean package` instead of just `mvn package` to ensure a fresh build.

### 2. Default Lifecycle — Build, Test, Package, Deploy

```bash
mvn compile    # Compile source code
mvn test       # Compile + run tests
mvn package    # Compile + test + create JAR/WAR
mvn install    # Compile + test + package + install to local repo
mvn deploy     # Compile + test + package + install + upload to remote repo
```

This is the lifecycle you use 95% of the time.

### 3. Site Lifecycle — Generate Documentation

```bash
mvn site
```

Generates an HTML documentation site in `target/site/` with project info, dependency reports, and test results.

| Lifecycle | Purpose | Triggered By |
|-----------|---------|-------------|
| **clean** | Remove previous build output | `mvn clean` |
| **default** | Build and deploy the project | `mvn compile`, `mvn package`, `mvn install` |
| **site** | Generate project documentation | `mvn site` |

---

## 5.2 Default Lifecycle Phases (in order)

When you run a phase, **all preceding phases run first**:

```
validate    → Check project is correct, all info available
compile     → Compile source code (.java → .class)
test        → Run unit tests (using Surefire plugin)
package     → Package compiled code (JAR/WAR)
verify      → Run integration tests and quality checks
install     → Install artifact to local repo (~/.m2/repository)
deploy      → Upload artifact to remote repo (Nexus/Artifactory)
```

**This is the single most important concept:**

```bash
mvn package
# Actually runs: validate → compile → test → package

mvn install
# Actually runs: validate → compile → test → package → verify → install

mvn deploy
# Runs ALL phases including uploading to remote repository
```

---

## 5.3 What is a Goal?

A **goal** is a specific task that a plugin performs. When you run a Maven command, Maven calls a plugin, and the plugin executes a goal.

**Think of it this way:**
- A **phase** is WHAT needs to happen (e.g., "compile the code")
- A **goal** is HOW it happens (e.g., the `compiler:compile` goal in the `maven-compiler-plugin`)
- A **plugin** is WHO does the work (e.g., `maven-compiler-plugin`)

```
Phase (WHAT)          Plugin (WHO)                Goal (HOW)
─────────────         ──────────────────          ─────────────────
compile          →    maven-compiler-plugin   →   compiler:compile
test             →    maven-surefire-plugin   →   surefire:test
package (jar)    →    maven-jar-plugin        →   jar:jar
package (war)    →    maven-war-plugin        →   war:war
install          →    maven-install-plugin    →   install:install
deploy           →    maven-deploy-plugin     →   deploy:deploy
clean            →    maven-clean-plugin      →   clean:clean
site             →    maven-site-plugin       →   site:site
```

### Running Goals Directly

You can run a plugin goal directly without going through the lifecycle:

```bash
# Run the compile goal of the compiler plugin
mvn compiler:compile

# Run the test goal of the surefire plugin
mvn surefire:test

# Run the tree goal of the dependency plugin
mvn dependency:tree

# Run the effective-pom goal of the help plugin
mvn help:effective-pom
```

**Format:** `mvn plugin-prefix:goal-name`

### How Phases and Goals Connect

When you run `mvn compile`, Maven:
1. Looks up which plugin is bound to the `compile` phase
2. Finds `maven-compiler-plugin`
3. Executes the `compiler:compile` goal
4. The plugin compiles `.java` files into `.class` files

```
You type: mvn compile
              ↓
Maven finds: compile phase → maven-compiler-plugin → compiler:compile goal
              ↓
Plugin runs: javac src/main/java/**/*.java → target/classes/
```

**Real-Life Analogy:** 
- **Phase** = "Paint the wall" (the task)
- **Plugin** = The painter (the worker)
- **Goal** = "Apply primer coat" or "Apply final coat" (specific actions the painter performs)

A single plugin can have multiple goals, just like a painter can do multiple tasks.

---

## 5.4 Commands You'll Use Daily as a DevOps Engineer

```bash
# Clean previous build + compile + test + create JAR
mvn clean package

# Same but skip tests (use during debugging, never in CI)
mvn clean package -DskipTests

# Skip test compilation AND execution
mvn clean package -Dmaven.test.skip=true

# Install to local repo (useful for multi-module projects)
mvn clean install

# Deploy to remote repository (Nexus/Artifactory)
mvn clean deploy

# Only compile, don't test or package
mvn compile

# Only run tests
mvn test

# Generate site documentation
mvn site
```

**Real-Life Example — Jenkins Pipeline:**

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean compile'
            }
        }
        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
        stage('Package') {
            steps {
                sh 'mvn package -DskipTests'  // Tests already ran
            }
        }
        stage('Deploy to Nexus') {
            steps {
                sh 'mvn deploy -DskipTests'
            }
        }
    }
}
```

---

## 5.5 Understanding `-DskipTests` vs `-Dmaven.test.skip=true`

| Flag | Compiles Tests? | Runs Tests? | When to Use |
|------|:-:|:-:|-------------|
| (none) | Yes | Yes | CI/CD pipelines (always) |
| `-DskipTests` | Yes | No | Quick local builds |
| `-Dmaven.test.skip=true` | No | No | When tests don't even compile |

---

## 5.6 Maven Site — Documentation Generation

The **site lifecycle** generates a complete HTML documentation website for your project:

```bash
mvn site
```

**Output location:** `target/site/index.html`

### What `mvn site` Generates

| Report | What It Shows |
|--------|--------------|
| **Project Summary** | GroupId, ArtifactId, Version, description |
| **Dependency Report** | All dependencies with versions and licenses |
| **Plugin Report** | All plugins used in the build |
| **Source Code Cross-Reference** | Browsable source code with line numbers |
| **JaCoCo Coverage** | Code coverage report (if JaCoCo plugin is configured) |
| **Surefire Report** | Test results summary |

```bash
# Generate site
mvn site

# Open in browser
open target/site/index.html    # macOS
xdg-open target/site/index.html  # Linux
```

### Who Uses Maven Site?

| Role | What They Look At |
|------|------------------|
| **Project managers** | Project summary, dependency list |
| **Auditors** | Dependency licenses, security reports |
| **Architecture teams** | Dependency tree, module structure |
| **New team members** | Project overview, how to build |

**Real-Life Example:** A company's compliance team needs to verify that no GPL-licensed libraries are used in a commercial product. They run `mvn site` and check the dependency report for license information.

### Build Plugins vs Reporting Plugins (From Lecture)

Maven has two types of plugins:

| Type | Purpose | Where Configured | Example |
|------|---------|-----------------|---------|
| **Build plugins** | Compile, test, package, deploy | `<build><plugins>` | `maven-compiler-plugin`, `maven-surefire-plugin` |
| **Reporting plugins** | Generate documentation and reports | `<reporting><plugins>` | `maven-site-plugin`, `maven-project-info-reports-plugin` |

> **From Lecture**: "In the build type plugin I said you have one type is build, the other one is reporting plugin. These are those plugins using which we will be generating the report or documentation."

The `site` lifecycle uses **reporting plugins** to gather information from the project and produce HTML output.

### How `mvn site` Works in Multi-Module Projects (From Lecture)

When you run `mvn site` from a multi-module parent directory:

```bash
cd demo          # Parent project directory
mvn site
```

**What happens:**

1. Maven downloads reporting plugins (first run only — cached in local repo after that)
2. For each module AND the parent, Maven:
   - Reads the pom.xml
   - Gathers all dependency information
   - Checks dependency convergence (are transitive dependencies consistent?)
   - Collects plugin information
   - Generates HTML reports

**Output structure:**
```
demo/                              ← Parent project
├── target/
│   └── site/                      ← Parent site (created for FIRST TIME!)
│       └── index.html             ← Project overview, module list
├── component1/
│   └── target/
│       └── site/
│           └── index.html         ← Component1 details
└── component2/
    └── target/
        └── site/
            └── index.html         ← Component2 details
```

> **From Lecture**: "Until now in our parent project we never had the target because we never had a source. But now it has created one folder called target and inside that there is a folder called site."

**What each component's site shows:**

```
Component1 Site (index.html):
┌──────────────────────────────────────────────┐
│ Project Information                          │
│   GroupId: com.company                       │
│   ArtifactId: component1                     │
│   Version: 1.0-SNAPSHOT                      │
│                                              │
│ Dependencies                                 │
│   Compile Scope:                             │
│     com.company:component2:1.0-SNAPSHOT.jar  │
│                                              │
│   Test Scope:                                │
│     junit:junit:4.13.2                       │
│                                              │
│ Dependency Tree                              │
│   component1                                 │
│   ├── component2 (compile)                   │
│   └── junit (test)                           │
│                                              │
│ Repository: https://repo.maven.apache.org    │
└──────────────────────────────────────────────┘
```

> **From Lecture**: "For component one it is depending on component two at the compile phase. So at the compile phase it needs this component2 jar, and for that what is the GAV — it gives this here. And for running the test, what is the dependency that it needs."

### What to Do with the Site Output

| Option | How | When Used |
|--------|-----|-----------|
| Zip and store in Git | `cd target && zip -r site.zip site/` | Version-controlled documentation |
| Upload to wiki | Copy HTML to Confluence/wiki | Team-accessible docs |
| Host on documentation site | Deploy to internal web server | Permanent project reference |
| Share directly | Send `target/site/` folder | Quick audit/review |

> **From Lecture**: "Rather than sharing all the information about the source code for the project, if you just give this, they can go through that and they can get the details about the project."

**Real-Life Example — Audit at a Financial Company:**
```bash
# Before quarterly audit, generate documentation for all microservices
cd banking-platform
mvn site

# Zip the output
cd target && zip -r banking-platform-docs-Q4-2024.zip site/

# Upload to the compliance team's SharePoint
# They review: dependency licenses, versions, security reports
# No source code access needed — site output is sufficient
```

---

## 5.7 Hands-On Exercise

```bash
cd devops-demo

# 1. Run each phase individually and observe what happens:
mvn validate
mvn compile    && ls target/classes/
mvn test       && ls target/surefire-reports/
mvn package    && ls target/*.jar
mvn install    && ls ~/.m2/repository/com/devops/demo/

# 2. Run: mvn clean  — observe target/ is deleted
# 3. Run: mvn clean package — observe the full sequence
# 4. Add -X flag for debug output: mvn clean package -X | head -100
```

---

**Next:** [Module 6 — Maven Plugins](06-plugins.md)
