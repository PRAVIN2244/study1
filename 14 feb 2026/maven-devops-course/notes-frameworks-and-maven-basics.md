# Frameworks, Dependencies & Maven Basics — Class Notes

---

## 1. What are Frameworks and Why Java Projects Need Them

A **framework** is pre-written code that provides a structure and ready-made functionality so you don't have to build everything from scratch.

**Without a framework:**
```java
// You write 500 lines to handle HTTP requests, parse JSON,
// connect to a database, manage sessions, handle errors...
```

**With a framework (e.g., Spring Boot):**
```java
@RestController
public class UserController {
    @GetMapping("/users")
    public List<User> getUsers() {
        return userService.findAll();  // Framework handles HTTP, JSON, routing
    }
}
```

**Common Java Frameworks:**

| Framework | Purpose |
|-----------|---------|
| Spring / Spring Boot | Web applications, REST APIs, microservices |
| Hibernate | Database access (ORM — maps Java objects to DB tables) |
| Struts | Older web framework (legacy projects) |
| JUnit | Testing framework |
| Log4j | Logging framework |

**Why needed:**
- Saves time — don't reinvent the wheel
- Follows best practices — security, performance built in
- Standardized — every developer on the team follows the same patterns
- Maintained — bugs and security patches handled by the framework community

---

## 2. Frameworks = Project Dependencies

In Maven terminology, **frameworks are called dependencies**.

When your project needs Spring Boot, you don't download it manually. You **list it as a dependency in `pom.xml`**, and Maven downloads it for you.

```xml
<dependencies>
    <!-- Spring Boot framework = a dependency -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- JUnit testing framework = a dependency -->
    <dependency>
        <groupId>junit</groupId>
        <artifactId>junit</artifactId>
        <version>4.13.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

**Flow:**
```
You list dependency in pom.xml
        ↓
Run: mvn compile (or mvn package)
        ↓
Maven reads pom.xml
        ↓
Downloads JARs from repository → stores in ~/.m2/repository
        ↓
Adds them to your project's classpath
```

---

## 3. Application Packaging: JAR vs WAR

| Type | Full Form | Used For | How to Run |
|------|-----------|----------|------------|
| **JAR** | Java ARchive | Standalone Java applications | `java -jar myapp.jar` |
| **WAR** | Web Application ARchive | Java web applications | Deploy to Tomcat/JBoss server |

**In `pom.xml`:**
```xml
<!-- For standalone app -->
<packaging>jar</packaging>

<!-- For web app -->
<packaging>war</packaging>
```

**Real-Life Example:**
- A command-line tool that processes CSV files → **JAR**
- An e-commerce website with REST APIs → **WAR** (or JAR with embedded Tomcat via Spring Boot)

---

## 4. Installing Java — JDK and JRE

When you install Java, you get two things:

| Component | Full Form | Contains | Purpose |
|-----------|-----------|----------|---------|
| **JDK** | Java Development Kit | Compiler (`javac`) + JRE + dev tools | For **developing** Java code |
| **JRE** | Java Runtime Environment | JVM + libraries | For **running** Java code |

```
JDK = JRE + Development Tools (javac, jdb, javadoc)
JRE = JVM + Standard Libraries
```

**As a DevOps engineer:**
- **Build servers (Jenkins/CI):** Need **JDK** (because Maven compiles code)
- **Production servers:** Need only **JRE** (just running the JAR/WAR)

**Setting `JAVA_HOME`:**
```bash
# Find where Java is installed
which java
# /usr/lib/jvm/java-17-openjdk-amd64

# Set JAVA_HOME (add to ~/.bashrc or /etc/profile)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Verify
echo $JAVA_HOME
java -version
javac -version
```

---

## 5. Installing Maven

### Step-by-step:

```bash
# 1. Download Maven zip from Apache website
cd /opt
sudo wget https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz

# 2. Unzip the file
sudo tar -xzf apache-maven-3.9.6-bin.tar.gz

# 3. Set MAVEN_HOME and PATH (add to ~/.bashrc or /etc/profile)
export MAVEN_HOME=/opt/apache-maven-3.9.6
export PATH=$MAVEN_HOME/bin:$PATH

# 4. Verify
mvn -version
```

**Summary of environment variables:**
```bash
JAVA_HOME  = /usr/lib/jvm/java-17-openjdk-amd64
MAVEN_HOME = /opt/apache-maven-3.9.6
PATH       = $JAVA_HOME/bin:$MAVEN_HOME/bin:$PATH
```

---

## 6. Maven Archetypes

An **archetype** is a template that defines what kind of project you want to create.

| Archetype | What It Creates |
|-----------|----------------|
| `maven-archetype-quickstart` | Simple standalone Java app (JAR) |
| `maven-archetype-webapp` | Java web application (WAR) |

### Creating a Web Application:

```bash
mvn archetype:generate \
  -DarchetypeArtifactId=maven-archetype-webapp \
  -DgroupId=devopsgroup \
  -DartifactId=01-maven-webapp \
  -DinteractiveMode=false
```

**What each parameter means:**

| Parameter | Meaning | Example |
|-----------|---------|---------|
| `archetypeArtifactId` | Template type | `maven-archetype-webapp` |
| `groupId` | Company name or project name | `devopsgroup` or `com.mycompany` |
| `artifactId` | Project name or module name | `01-maven-webapp` |
| `interactiveMode` | Don't ask questions, use defaults | `false` |

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

---

## 7. Maven Build Lifecycle

When you run a Maven command, it executes phases in order:

```
mvn compile    →  validate → compile
mvn test       →  validate → compile → test
mvn package    →  validate → compile → test → package
mvn install    →  validate → compile → test → package → verify → install
mvn deploy     →  validate → compile → test → package → verify → install → deploy
```

**Key phases:**

| Phase | What Happens |
|-------|-------------|
| `validate` | Checks project structure is correct |
| `compile` | Compiles `.java` files → `.class` files |
| `test` | Runs unit tests |
| `package` | Creates JAR or WAR file in `target/` |
| `install` | Copies artifact to local repo (`~/.m2/repository`) |
| `deploy` | Uploads artifact to remote repo (Nexus/JFrog) |

**Most used commands:**
```bash
mvn clean package          # Delete old build + build fresh JAR/WAR
mvn clean package -DskipTests  # Same but skip tests
mvn clean install          # Build + put in local repo
mvn clean deploy           # Build + upload to remote repo
```

---

## 8. Maven Repositories — Where Dependencies Come From

```
                    Search Order
                    ──────────→

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. Local     │    │ 2. Remote    │    │ 3. Central   │
│    Repo      │ →  │    Repo      │ →  │    Repo      │
│              │    │              │    │              │
│ Your laptop  │    │ Company's    │    │ Apache's     │
│ ~/.m2/       │    │ JFrog/Nexus  │    │ Maven Central│
│ repository   │    │ server       │    │ repo.maven.  │
│              │    │              │    │ apache.org   │
└──────────────┘    └──────────────┘    └──────────────┘
```

| Repository | Location | Who Maintains It | Config Needed? |
|------------|----------|-----------------|----------------|
| **Local** | `C:\Users\<username>\.m2\repository` (Windows) or `~/.m2/repository` (Linux) | You (automatic) | No |
| **Central** | `https://repo.maven.apache.org/maven2` | Apache Foundation | No (default) |
| **Remote** | Company's JFrog/Nexus URL | Your company | Yes — `settings.xml` + `pom.xml` |

### Configuring a Remote Repository (JFrog)

**In `pom.xml`:**
```xml
<repositories>
    <repository>
        <id>jfrog-repo</id>
        <url>https://mycompany.jfrog.io/artifactory/maven-repo</url>
    </repository>
</repositories>
```

**In `~/.m2/settings.xml` (for credentials):**
```xml
<settings>
    <servers>
        <server>
            <id>jfrog-repo</id>  <!-- Must match the id in pom.xml -->
            <username>deploy-user</username>
            <password>encrypted-password</password>
        </server>
    </servers>
</settings>
```

**Why companies use remote repos (JFrog/Nexus):**
1. **Security** — control what external libraries enter the network
2. **Speed** — download once from internet, all developers/CI get it from local network
3. **Internal libraries** — host your company's own JARs that aren't on Maven Central
4. **Reliability** — builds don't break if Maven Central is down

---

## 9. Complete `pom.xml` Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <!-- WHO is this project? -->
    <groupId>devopsgroup</groupId>           <!-- Company/project name -->
    <artifactId>01-maven-webapp</artifactId> <!-- Module name -->
    <version>1.0-SNAPSHOT</version>          <!-- Version -->
    <packaging>war</packaging>               <!-- JAR or WAR -->

    <!-- WHAT does this project need? (Dependencies/Frameworks) -->
    <dependencies>
        <dependency>
            <groupId>javax.servlet</groupId>
            <artifactId>javax.servlet-api</artifactId>
            <version>4.0.1</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>

    <!-- WHERE to find dependencies? (Remote repo) -->
    <repositories>
        <repository>
            <id>jfrog-repo</id>
            <url>https://mycompany.jfrog.io/artifactory/maven-repo</url>
        </repository>
    </repositories>

</project>
```

---

## Quick Summary Diagram

```
Install Java (JDK)  →  Set JAVA_HOME + PATH
         ↓
Install Maven       →  Set MAVEN_HOME + PATH
         ↓
Create Project       →  mvn archetype:generate (choose webapp or quickstart)
         ↓
Add Dependencies    →  Edit pom.xml <dependencies> section
         ↓
Build Project       →  mvn clean package
         ↓
Maven downloads     →  Local repo (~/.m2) ← Remote repo (JFrog) ← Central repo (Apache)
         ↓
Output              →  target/01-maven-webapp.war (or .jar)
         ↓
Deploy              →  Copy WAR to Tomcat, or run JAR with java -jar
```
