# Module 0: Build Systems Foundations

**Objective:** Understand why build tools exist — what source code, compilation, packaging, and artifacts mean — before touching Maven.

---

## 0.1 Source Code vs Executable

Every software application starts as **source code** — human-readable text files that programmers write. But computers cannot run source code directly. It must be converted into something the machine understands.

| Concept | What It Is | Example |
|---------|-----------|---------|
| **Source code** | Human-readable text files written by developers | `PaymentService.java`, `index.html`, `app.py` |
| **Executable / Binary** | Machine-readable files that computers can run | `payment-service.jar`, `app.exe`, `a.out` |

**The key idea:** Source code is for humans. Executables are for machines. Something must convert one into the other.

```
Source Code (what developers write)          Executable (what computers run)
┌──────────────────────────┐                ┌──────────────────────────┐
│  PaymentService.java     │                │                          │
│  FraudCheck.java         │  ──────────►   │  payment-service-1.0.jar │
│  DatabaseClient.java     │   (build)      │                          │
│  application.properties  │                │  (single deployable file)│
└──────────────────────────┘                └──────────────────────────┘
     You can read this                          Computer runs this
     in a text editor                           QA tests this
```

**Real-Life Analogy:** Source code is like an architect's blueprint. The executable is the actual building. You can't live in a blueprint — it needs to be constructed first. The build process is the construction.

### Build Management Definition

**Build management** is the process of converting source code into deliverables (artifacts) through two stages:

```
Stage 1 — Compilation                    Stage 2 — Assembly (Packaging)
─────────────────────                    ──────────────────────────────
.java  →  .class                         .class files  →  .jar / .war / .ear
(source)  (bytecode)                     (many files)     (single deliverable)
```

The output of this process — JAR, WAR, or EAR — is called by many names. They all mean the same thing:

| Term | Meaning |
|------|---------|
| **Deliverable** | The file you deliver to QA / customer |
| **Artifact** | The packaged output of a build |
| **Binary** | Any compiled, non-human-readable file |
| **Package** | The bundled archive (JAR/WAR/EAR) |

**Real-Life Example — Hospital Management System:**

```
Developers write:                    Build system creates:
─────────────────                    ─────────────────────
Appointment.java                     hospital-system.war
DoctorService.java                   (single deliverable)
Billing.java
PatientRecord.java
```

QA tests the WAR file — not the raw `.java` files. That's build management.

---

## 0.2 Compilation — Translating Human Code to Machine Code

**Compilation** is the process of converting source code into a format the computer can execute.

### How Compilation Works in Java

```
Step 1: Developer writes          Step 2: Compiler converts         Step 3: JVM runs
─────────────────────────         ─────────────────────────         ─────────────────
PaymentService.java        ──►   PaymentService.class        ──►   Application runs
(human-readable)           javac  (bytecode, machine-readable)     on any OS
```

**In detail:**

```bash
# Developer writes this file: PaymentService.java
public class PaymentService {
    public void processPayment(double amount) {
        System.out.println("Processing payment: $" + amount);
    }
}

# Compiler converts it:
javac PaymentService.java
# Output: PaymentService.class (bytecode — not human-readable)

# JVM runs it:
java PaymentService
# Output: Processing payment: $99.99
```

### Compilation in Different Languages

| Language | Source File | Compiler | Output | How to Run |
|----------|-----------|----------|--------|------------|
| **Java** | `.java` | `javac` | `.class` (bytecode) | `java ClassName` |
| **C** | `.c` | `gcc` | `.o` → executable | `./program` |
| **Go** | `.go` | `go build` | binary executable | `./program` |
| **Python** | `.py` | Not compiled (interpreted) | Runs directly | `python app.py` |
| **JavaScript** | `.js` | Not compiled (interpreted) | Runs directly | `node app.js` |

**Why this matters for DevOps:** When you set up a CI/CD pipeline for a Java project, the pipeline must compile the code. If compilation fails, the build fails. You need to understand what compilation is to debug these failures.

---

## 0.3 Packaging — Bundling Everything Together

After compilation, you have many `.class` files scattered across directories. **Packaging** bundles them into a single deployable file.

```
Before Packaging (many files)              After Packaging (one file)
┌──────────────────────────┐              ┌──────────────────────────┐
│  target/classes/          │              │                          │
│  ├── PaymentService.class │              │  payment-service-1.0.jar │
│  ├── FraudCheck.class     │  ────────►   │                          │
│  ├── DatabaseClient.class │  (package)   │  Contains ALL .class     │
│  ├── OrderProcessor.class │              │  files + config files    │
│  └── application.properties              │  + dependencies          │
└──────────────────────────┘              └──────────────────────────┘
   Hard to deploy                            Easy to deploy
   (which files? where?)                     (one file, copy anywhere)
```

**Why packaging matters:**
- You can't send 500 individual `.class` files to the QA team
- You can't deploy 500 files to a production server one by one
- A single packaged file (JAR/WAR) is easy to version, store, and deploy

---

## 0.4 Artifacts and Binaries

An **artifact** is the final output of the build process — the deployable file.

| Term | Meaning | Example |
|------|---------|---------|
| **Artifact** | The packaged output of a build | `payment-service-1.0.jar` |
| **Binary** | Any compiled, non-human-readable file | `.class` files, `.jar` files |
| **Deliverable** | The artifact that gets deployed to production | `payment-service-1.0.jar` |

### Types of Java Artifacts

| Type | Full Form | Contains | Used For |
|------|-----------|----------|----------|
| **JAR** | Java ARchive | `.class` files + resources | Standalone apps, libraries, microservices |
| **WAR** | Web Application ARchive | `.class` files + JSP + web.xml | Web apps deployed to Tomcat/JBoss |
| **EAR** | Enterprise Application ARchive | Multiple JARs + WARs | Large enterprise apps (rare today) |

```
Artifact Types:

JAR ──► Standalone application     ──► java -jar app.jar
WAR ──► Web application            ──► Deploy to Tomcat server
EAR ──► Enterprise application     ──► Deploy to JBoss/WebLogic (legacy)
```

**Real-Life Example:** At a fintech company like PayPal:

```
Developers write:                    Build system produces:
─────────────────                    ─────────────────────
PaymentService.java                  payment-service-1.0.jar
FraudCheck.java                      (single artifact)
DatabaseClient.java
TransactionLogger.java
application.properties
```

QA tests `payment-service-1.0.jar` — not the raw `.java` files. Operations deploys `payment-service-1.0.jar` to production servers. That's the artifact.

---

## 0.5 Build Automation — Why We Need Build Tools

In a real project, building an application involves many steps:

```
1. Download external libraries (dependencies)
2. Compile source code (.java → .class)
3. Run unit tests
4. Run integration tests
5. Check code quality
6. Package into JAR/WAR
7. Upload to artifact repository
8. Deploy to server
```

**Without build automation (manual process):**

```bash
# Step 1: Download dependencies manually from websites
# Step 2: Set classpath manually
javac -cp lib/spring-core.jar:lib/hibernate.jar:lib/... src/**/*.java
# Step 3: Run tests manually
java -cp ... org.junit.runner.JUnitCore com.company.AllTests
# Step 4: Package manually
jar cf payment-service.jar -C target/classes .
# Step 5: Copy to server manually
scp payment-service.jar user@server:/opt/apps/
```

**Problems with manual builds:**
- Takes 30+ minutes of manual work
- Easy to forget a step
- Different developers do it differently
- "Works on my machine" — fails on another machine
- No consistency, no repeatability

**With build automation (Maven):**

```bash
mvn clean package
# Does ALL of the above in one command, in 2 minutes
# Same result every time, on every machine
```

### Benefits of Build Automation

| Benefit | Explanation |
|---------|-------------|
| **Faster builds** | Minutes instead of hours |
| **Fewer errors** | No forgotten steps, no typos |
| **Reproducibility** | Same result every time, on every machine |
| **Build history** | Track what was built, when, by whom |
| **Easier maintenance** | Change one config file, not 50 scripts |

**Real-Life Analogy:** Manual builds are like hand-washing clothes — slow, inconsistent, error-prone. Build automation is like a washing machine — put clothes in, press one button, get consistent results every time.

---

## 0.6 The Developer → QA → Customer Workflow

In every software company, code flows through a pipeline before reaching customers:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│Developer │────►│   Git    │────►│ CI Server│────►│ Artifact │────►│Production│
│          │     │Repository│     │(Jenkins) │     │  Server  │     │  Server  │
│ Writes   │     │          │     │          │     │(Nexus/   │     │          │
│ .java    │     │ Stores   │     │ Builds   │     │Artifactory)    │ Runs     │
│ files    │     │ source   │     │ artifact │     │ Stores   │     │ artifact │
│          │     │ code     │     │          │     │ artifact │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                       │
                                       ▼
                                 ┌──────────┐
                                 │   QA     │
                                 │          │
                                 │ Tests    │
                                 │ artifact │
                                 └──────────┘
```

### Step-by-Step Workflow at a Real Company

**Example: An e-commerce company building a payment service**

```
Step 1: Developer writes code
────────────────────────────
  Developer creates PaymentService.java
  Developer writes PaymentServiceTest.java
  Developer commits to Git: git push origin feature/payment-v2

Step 2: CI Server builds automatically
────────────────────────────────────
  Jenkins detects the push
  Jenkins runs: mvn clean package
  Maven compiles → tests → packages
  Output: payment-service-2.0.jar

Step 3: QA tests the artifact
─────────────────────────────
  QA deploys payment-service-2.0.jar to staging server
  QA runs functional tests, performance tests
  QA approves or rejects

Step 4: Artifact stored in repository
─────────────────────────────────────
  Approved artifact uploaded to Nexus/Artifactory
  Version 2.0 is now available for deployment

Step 5: Deployment to production
────────────────────────────────
  Operations team deploys payment-service-2.0.jar
  Customers can now use the new payment features
```

**Key insight:** QA never sees `.java` files. Operations never sees `.java` files. They only work with the **artifact** (the JAR/WAR). The build system is the bridge between source code and the deployable artifact.

---

## 0.7 What is Build Management?

**Build management** is the practice of automating and controlling the entire process from source code to deployable artifact.

It includes:

| Aspect | What It Means | Tool Example |
|--------|--------------|--------------|
| **Dependency management** | Automatically download libraries your code needs | Maven, Gradle |
| **Compilation** | Convert source code to machine code | `javac` (called by Maven) |
| **Testing** | Run automated tests | JUnit (called by Maven) |
| **Packaging** | Bundle everything into a deployable file | Maven (`mvn package`) |
| **Artifact storage** | Store built artifacts for deployment | Nexus, Artifactory |
| **Version control** | Track which version of code produced which artifact | Git + Maven versioning |

**Real-Life Example:** At a company like Netflix:

```
50 microservices, each with:
  - 100+ Java files
  - 30+ dependencies
  - 200+ unit tests

Without build management:
  - Each service takes 1 hour to build manually
  - 50 services × 1 hour = 50 hours of manual work per release
  - High chance of human error

With build management (Maven + Jenkins):
  - Each service builds in 3 minutes automatically
  - 50 services build in parallel in 10 minutes
  - Zero human error — same process every time
```

---

## 0.8 Summary — The Complete Picture

```
Source Code          Compilation          Packaging           Artifact
(.java files)   →   (.class files)   →   (bundling)     →   (.jar/.war file)
                                                                  │
Human-readable       Machine-readable     Single file            │
Developer writes     Computer understands  Easy to deploy         ▼
                                                            QA tests it
                                                            Ops deploys it
                                                            Customer uses it
```

**The build tool (Maven) automates this entire pipeline.**

---

## 0.9 Hands-On Exercise

```bash
# 1. Create a simple Java file
mkdir -p /tmp/build-demo/src && cd /tmp/build-demo
cat > src/HelloWorld.java << 'EOF'
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello from source code!");
    }
}
EOF

# 2. Compile it manually (source code → bytecode)
javac src/HelloWorld.java
ls src/HelloWorld.class    # This is the compiled bytecode

# 3. Run the compiled class
java -cp src HelloWorld
# Output: Hello from source code!

# 4. Package it into a JAR manually
jar cfe HelloWorld.jar HelloWorld -C src HelloWorld.class
ls -la HelloWorld.jar      # This is the artifact

# 5. Run the JAR
java -jar HelloWorld.jar
# Output: Hello from source code!

# 6. Clean up
rm -rf /tmp/build-demo

# Now imagine doing this for 500 files with 30 dependencies...
# That's why Maven exists.
```

---

**Next:** [Module 0.5 — Java Build Process](00.5-java-build-process.md)
