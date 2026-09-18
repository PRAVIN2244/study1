# Module 3: Maven Project Structure, Packaging, and Archetypes

**Objective:** Understand JAR vs WAR packaging, Maven coordinates (groupId, artifactId, packaging), archetypes, and the standard directory layout.

---

## 3.1 JAR vs WAR — Application Packaging

When Maven builds your project, it packages the compiled code into an archive file. The two main types are:

| Type | Full Form | Used For | How to Run |
|------|-----------|----------|------------|
| **JAR** | Java ARchive | Standalone Java applications | `java -jar myapp.jar` |
| **WAR** | Web Application ARchive | Java web applications | Deploy to Tomcat/JBoss/WildFly server |

### When to Use JAR

A **JAR** is a standalone application that runs on its own. It contains your compiled code and all dependencies bundled together.

```xml
<!-- In pom.xml -->
<packaging>jar</packaging>
```

**Examples of JAR applications:**
- A command-line tool that processes CSV files
- A Spring Boot microservice (Spring Boot embeds Tomcat inside the JAR)
- A batch job that runs nightly to generate reports
- A library that other projects use as a dependency

**How to run:**
```bash
# Build the JAR
mvn clean package

# Run it
java -jar target/my-app-1.0.0.jar
```

### When to Use WAR

A **WAR** is a web application that needs an external server (like Apache Tomcat) to run. The server provides the HTTP handling, and your WAR provides the application logic.

```xml
<!-- In pom.xml -->
<packaging>war</packaging>
```

**Examples of WAR applications:**
- An e-commerce website with JSP pages
- A REST API deployed to a company's Tomcat server
- A legacy banking application running on JBoss

**How to deploy:**
```bash
# Build the WAR
mvn clean package

# Copy WAR to Tomcat's webapps directory
cp target/my-webapp-1.0.0.war /opt/tomcat/webapps/

# Tomcat automatically deploys it
# Access at: http://server-ip:8080/my-webapp-1.0.0/
```

### JAR vs WAR — Side by Side

```
JAR (Standalone)                    WAR (Web Application)
┌──────────────────┐               ┌──────────────────┐
│  my-app.jar      │               │  my-webapp.war   │
│                  │               │                  │
│  ├── META-INF/   │               │  ├── META-INF/   │
│  ├── com/        │               │  ├── WEB-INF/    │
│  │   └── app/    │               │  │   ├── web.xml │
│  │       └── *.class             │  │   ├── classes/│
│  └── lib/        │               │  │   └── lib/    │
│      └── *.jar   │               │  └── *.jsp      │
└──────────────────┘               └──────────────────┘
        │                                   │
        ↓                                   ↓
  java -jar my-app.jar              Deploy to Tomcat
  (runs by itself)                  (needs a server)
```

**Real-Life Example:**
- **Swiggy's order processing service** → JAR (Spring Boot microservice, runs independently)
- **A government portal built in 2010** → WAR (deployed on Tomcat, uses JSP pages)

**Modern trend:** Most new projects use **JAR with embedded Tomcat** (Spring Boot style). WAR is still common in legacy enterprise applications.

---

## 3.2 GroupId, ArtifactId, and Packaging — Maven Coordinates

Every Maven project has three key identifiers called **Maven coordinates**. Together, they uniquely identify your project in the entire Maven ecosystem.

### groupId — Who Made It?

The `groupId` represents the **company, organization, or project group**. It follows Java package naming conventions (reversed domain name).

```xml
<groupId>com.flipkart.payments</groupId>
```

**Examples:**
| Company | groupId |
|---------|---------|
| Google | `com.google.cloud` |
| Amazon | `com.amazonaws` |
| Your company | `com.yourcompany.projectname` |
| A learning project | `devopsgroup` |

### artifactId — What Is It?

The `artifactId` is the **project name or module name**. It becomes the name of the JAR/WAR file.

```xml
<artifactId>payment-gateway</artifactId>
```

**Examples:**
| Project | artifactId |
|---------|-----------|
| User management service | `user-service` |
| Shared utility library | `common-utils` |
| Web application | `01-maven-webapp` |

### packaging — How to Package It?

The `packaging` element tells Maven what type of archive to create.

```xml
<packaging>war</packaging>
```

| Packaging Type | Output | Use Case |
|---------------|--------|----------|
| `jar` (default) | `my-app-1.0.0.jar` | Standalone apps, libraries |
| `war` | `my-app-1.0.0.war` | Web applications for Tomcat |
| `pom` | No artifact | Parent POM for multi-module projects |
| `ear` | `my-app-1.0.0.ear` | Enterprise apps (rare, legacy) |

### Complete Example — How Coordinates Work Together

```xml
<groupId>com.flipkart.payments</groupId>
<artifactId>payment-gateway</artifactId>
<version>2.3.1</version>
<packaging>jar</packaging>
```

This produces: `payment-gateway-2.3.1.jar`

And it's stored in the local repository at:
```
~/.m2/repository/com/flipkart/payments/payment-gateway/2.3.1/payment-gateway-2.3.1.jar
```

**Real-Life Analogy:** Think of Maven coordinates like a postal address:
- **groupId** = City (`com.flipkart.payments`)
- **artifactId** = Street name (`payment-gateway`)
- **version** = House number (`2.3.1`)

Together, they uniquely locate any artifact in the Maven universe.

---

## 3.3 The Standard Directory Layout

```
my-app/
├── pom.xml                          # Project Object Model (the brain)
├── src/
│   ├── main/
│   │   ├── java/                    # Application source code
│   │   │   └── com/mycompany/app/
│   │   │       └── App.java
│   │   └── resources/               # Config files (application.properties, etc.)
│   │       └── application.properties
│   └── test/
│       ├── java/                    # Test source code
│       │   └── com/mycompany/app/
│       │       └── AppTest.java
│       └── resources/               # Test-specific config files
└── target/                          # BUILD OUTPUT (generated, never commit this)
    ├── classes/                     # Compiled .class files
    ├── test-classes/                # Compiled test classes
    ├── my-app-1.0.0.jar             # The final artifact
    └── surefire-reports/            # Test results (XML/TXT)
```

### What Each Directory Contains

| Directory | Purpose | Example Files |
|-----------|---------|---------------|
| `src/main/java/` | Application source code | `App.java`, `UserService.java` |
| `src/main/resources/` | Configuration files, templates | `application.properties`, `log4j.xml` |
| `src/test/java/` | Unit test source code | `AppTest.java`, `UserServiceTest.java` |
| `src/test/resources/` | Test-specific config files | `test-data.sql`, `test-application.properties` |
| `target/` | Build output (generated, never commit) | `.class` files, `.jar` files, test reports |

**Why this matters for DevOps:**
- You know where to find the built artifact: always `target/`
- You know where test reports are: always `target/surefire-reports/`
- You know what to clean: `mvn clean` deletes `target/`
- You know what NOT to commit: `target/` goes in `.gitignore`

**Real-Life Example — Healthcare SaaS Company:**

```
src/main/java/com/company/patient/PatientService.java
src/main/java/com/company/patient/PatientController.java
src/main/java/com/company/patient/PatientRepository.java
src/test/java/com/company/patient/PatientServiceTest.java
src/main/resources/application.properties
```

Maven automatically knows:
- Files in `src/main/java/` → compile these
- Files in `src/test/java/` → run these as tests
- Files in `src/main/resources/` → include in the JAR
- No manual configuration needed — Maven follows the convention

---

## 3.4 Maven Archetypes — Project Templates

An **archetype** is a project template that decides what kind of project you want to create. Instead of manually creating folders and files, Maven generates the entire project structure for you.

### Common Archetypes

| Archetype | What It Creates | Packaging |
|-----------|----------------|-----------|
| `maven-archetype-quickstart` | Simple standalone Java app | JAR |
| `maven-archetype-webapp` | Java web application | WAR |

### Creating a Standalone Java App (JAR)

```bash
mvn archetype:generate \
  -DarchetypeArtifactId=maven-archetype-quickstart \
  -DarchetypeVersion=1.4 \
  -DgroupId=com.mycompany.app \
  -DartifactId=my-app \
  -DinteractiveMode=false
```

**Generated structure:**
```
my-app/
├── pom.xml
└── src/
    ├── main/java/com/mycompany/app/
    │   └── App.java
    └── test/java/com/mycompany/app/
        └── AppTest.java
```

### Creating a Web Application (WAR)

```bash
mvn archetype:generate \
  -DarchetypeArtifactId=maven-archetype-webapp \
  -DgroupId=devopsgroup \
  -DartifactId=01-maven-webapp \
  -DinteractiveMode=false
```

**Generated structure:**
```
01-maven-webapp/
├── pom.xml
└── src/
    └── main/
        ├── webapp/
        │   ├── WEB-INF/
        │   │   └── web.xml
        │   └── index.jsp
        └── resources/
```

### What Each Parameter Means

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `archetypeArtifactId` | Template type | `maven-archetype-webapp` |
| `groupId` | Company/organization name | `devopsgroup` or `com.mycompany` |
| `artifactId` | Project/module name | `01-maven-webapp` |
| `interactiveMode` | Don't ask questions, use defaults | `false` |

**Real-Life Analogy:** An archetype is like choosing a house blueprint. You pick "2-bedroom apartment" or "3-bedroom villa" — the builder (Maven) creates the structure. You then customize the interior (your code).

---

## 3.5 The `pom.xml` Anatomy

### Minimum `pom.xml`

The simplest valid `pom.xml` needs only four elements:

```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>demo</artifactId>
  <version>1.0</version>
</project>
```

This is enough for Maven to compile and package a project. Everything else (dependencies, plugins, properties) is optional.

### Full `pom.xml` Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <!-- POM model version (always 4.0.0) -->
    <modelVersion>4.0.0</modelVersion>

    <!-- Project coordinates (unique identifier) -->
    <groupId>com.mycompany.app</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>  <!-- jar, war, pom, ear -->

    <!-- Human-readable info -->
    <name>My Application</name>
    <description>A sample application</description>

    <!-- Properties (variables) -->
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <!-- Dependencies (libraries this project needs) -->
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>  <!-- Only needed during testing -->
        </dependency>
    </dependencies>

</project>
```

---

## 3.6 Hands-On Exercise

```bash
# 1. Generate a project
mvn archetype:generate -DgroupId=com.devops.demo -DartifactId=devops-demo \
  -DarchetypeArtifactId=maven-archetype-quickstart -DarchetypeVersion=1.4 \
  -DinteractiveMode=false

# 2. Explore the structure
cd devops-demo && find . -type f

# 3. Read the generated pom.xml
cat pom.xml

# 4. Build it
mvn package

# 5. See what was created
ls -la target/

# 6. Run the app
java -cp target/devops-demo-1.0-SNAPSHOT.jar com.devops.demo.App
# Output: Hello World!
```

---

**Next:** [Module 4 — Dependency Management](04-dependency-management.md)
