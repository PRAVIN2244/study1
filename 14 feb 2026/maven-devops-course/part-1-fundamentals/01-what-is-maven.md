# Module 1: Frameworks, Dependencies, and Maven

**Objective:** Understand what Java frameworks are, how they become project dependencies, what Maven does, and where it fits in the software delivery pipeline.

---

## 1.1 What is a Framework in Java?

A **framework** is a pre-written set of libraries and tools that provides a structure and ready-made functionality so you don't have to build everything from scratch.

**What a framework provides:**
- Ready-made code for common tasks (HTTP handling, database access, security)
- A design structure that organizes your application
- Best practices baked into the code
- Built-in features like logging, error handling, and configuration management

### Without a Framework vs With a Framework

**Without a framework** — you write everything from scratch:

```java
// 500+ lines to handle an HTTP request manually:
// 1. Open a socket on port 8080
// 2. Parse the raw HTTP request string
// 3. Route the URL to the right method
// 4. Convert Java objects to JSON manually
// 5. Handle errors, sessions, security...
// 6. Send the HTTP response back

ServerSocket server = new ServerSocket(8080);
Socket client = server.accept();
BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
String requestLine = in.readLine();  // "GET /users HTTP/1.1"
// ... hundreds more lines of boilerplate
```

**With a framework (Spring Boot)** — the same thing in 5 lines:

```java
@RestController
public class UserController {
    @GetMapping("/users")
    public List<User> getUsers() {
        return userService.findAll();  // Framework handles HTTP, JSON, routing
    }
}
```

### Common Java Frameworks

| Framework | Purpose | Real-Life Use |
|-----------|---------|---------------|
| **Spring / Spring Boot** | Web apps, REST APIs, microservices | Amazon, Netflix use Spring-based services |
| **Hibernate** | Database access (ORM — maps Java objects to DB tables) | Any app that stores data in MySQL/PostgreSQL |
| **Struts** | Older web framework | Legacy banking and government systems |
| **JUnit** | Testing framework | Every Java project uses this for unit tests |
| **Log4j / SLF4J** | Logging framework | Writing logs to files, consoles, monitoring tools |

### Why Do We Need Frameworks?

| Without Frameworks | With Frameworks |
|---|---|
| Write everything from scratch | Use pre-built, tested code |
| More boilerplate code | Less code, focus on business logic |
| Higher development time (months) | Faster development (weeks) |
| More chances of bugs and security holes | Built-in security and error handling |
| Hard to maintain | Standardized structure, easy maintenance |
| Difficult to scale | Built for scalability |

**Real-Life Analogy:** Building a house without a framework is like making every brick yourself. Using a framework is like buying pre-made walls, doors, and windows — you just assemble them into the house you want.

---

## 1.2 Are Frameworks Called Project Dependencies?

**Yes.** In Maven terminology, **frameworks are called dependencies**.

A **dependency** is any external library or framework that your project needs to compile, test, or run. When your project needs Spring Boot, you don't download it manually from a website. You **list it as a dependency in `pom.xml`**, and Maven downloads it automatically.

```xml
<dependencies>
    <!-- Spring Boot framework = a dependency -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>3.2.0</version>
    </dependency>

    <!-- Hibernate framework = a dependency -->
    <dependency>
        <groupId>org.hibernate.orm</groupId>
        <artifactId>hibernate-core</artifactId>
        <version>6.4.0.Final</version>
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

**How it works — step by step:**

```
Step 1: You list a dependency in pom.xml
            ↓
Step 2: Run: mvn compile (or mvn package)
            ↓
Step 3: Maven reads pom.xml
            ↓
Step 4: Maven checks local cache (~/.m2/repository)
            ↓
Step 5: If not found, downloads JAR from Maven Central repository
            ↓
Step 6: Stores the JAR in ~/.m2/repository
            ↓
Step 7: Adds the JAR to your project's classpath
            ↓
Step 8: Your code can now use the framework's classes
```

**Real-Life Analogy:** Think of `pom.xml` as a grocery list. Maven is the delivery service. You write "Spring Boot" on the list, Maven goes to the store (Maven Central), picks it up, and delivers it to your kitchen (local repository).

---

## 1.3 Why Do We Use Maven?

**Apache Maven** is a **build automation and dependency management tool** for Java projects. Maven itself is written in Java.

Maven is not just a compiler — it is four things in one:

1. **Build tool** — compiles and packages your code
2. **Dependency manager** — downloads libraries automatically
3. **Project management tool** — enforces standard structure
4. **Documentation generator** — creates project reports (`mvn site`)

### What Maven Does

| Task | Without Maven | With Maven |
|------|--------------|------------|
| **Download dependencies** | Manually download JARs from websites, copy to project | Add to `pom.xml`, Maven downloads automatically |
| **Compile code** | Run `javac` manually with classpath flags | `mvn compile` |
| **Run tests** | Manually run test classes | `mvn test` |
| **Package application** | Manually create JAR/WAR using `jar` command | `mvn package` |
| **Manage project lifecycle** | Write custom scripts for each step | Maven has a built-in lifecycle |
| **Share artifacts** | Email JARs or copy to shared drives | `mvn deploy` uploads to a repository |

### Maven's Core Responsibilities

```
┌─────────────────────────────────────────────────────┐
│                    MAVEN                             │
│                                                      │
│  1. Dependency Management                            │
│     → Downloads libraries from repositories          │
│     → Resolves version conflicts                     │
│     → Manages transitive dependencies                │
│                                                      │
│  2. Build Automation                                 │
│     → Compiles source code                           │
│     → Runs tests                                     │
│     → Packages into JAR/WAR                          │
│                                                      │
│  3. Project Lifecycle                                │
│     → Standardized phases (compile→test→package)     │
│     → Consistent across all projects                 │
│                                                      │
│  4. Project Structure                                │
│     → Convention over configuration                  │
│     → Every Maven project looks the same             │
└─────────────────────────────────────────────────────┘
```

**Real-Life Example:** Imagine you join a new company. They have 50 Java projects. Because all of them use Maven:
- Every project has the same folder structure
- Every project builds with `mvn clean package`
- Every project lists dependencies in `pom.xml`
- You don't need to learn a new build process for each project

---

## 1.4 Maven Architecture — Key Components

Maven has five key components that work together. Understanding how they connect is essential.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR MACHINE                                 │
│                                                                     │
│  ┌─────────────────┐         ┌──────────────────────┐              │
│  │   Workspace      │         │   Local Repository   │              │
│  │   (Your Project) │         │   (~/.m2/repository)  │              │
│  │                  │         │                      │              │
│  │  ├── pom.xml ◄───┼────┐   │  Cached JARs from    │              │
│  │  ├── src/        │    │   │  previous downloads   │              │
│  │  └── target/     │    │   │                      │              │
│  └────────┬─────────┘    │   └──────────┬───────────┘              │
│           │              │              │                           │
│           ▼              │              │                           │
│  ┌─────────────────┐    │              │                           │
│  │   Maven Engine   │    │              │                           │
│  │                  │◄───┘              │                           │
│  │  Reads pom.xml   │                   │                           │
│  │  Calls Plugins   │◄──────────────────┘                           │
│  │  Manages Deps    │         Checks local cache first              │
│  └────────┬─────────┘                                               │
│           │                                                         │
└───────────┼─────────────────────────────────────────────────────────┘
            │  If dependency not found locally,
            │  downloads from remote
            ▼
┌───────────────────────┐         ┌───────────────────────┐
│   Remote Repository   │         │   Central Repository  │
│   (Company's Nexus/   │ ◄─────► │   (Maven Central)     │
│    JFrog Artifactory)  │         │   repo.maven.apache.  │
│                       │         │   org/maven2           │
│   Your company's      │         │                       │
│   private JARs +      │         │   All open-source     │
│   cached public JARs  │         │   Java libraries      │
└───────────────────────┘         └───────────────────────┘
```

### Component Breakdown

| Component | What It Is | Location | Purpose |
|-----------|-----------|----------|---------|
| **Workspace** | Your project folder | Any directory on your machine | Contains source code + `pom.xml` |
| **POM file** | `pom.xml` — the configuration file | Project root directory | Tells Maven what to build, what dependencies to download, how to package |
| **Local Repository** | Cache of downloaded JARs | `~/.m2/repository` | Avoids re-downloading dependencies every build |
| **Remote Repository** | Company's private artifact server | Nexus/Artifactory URL | Stores company's internal JARs + caches public JARs |
| **Central Repository** | Apache's public repository | `repo.maven.apache.org` | Contains all open-source Java libraries |
| **Plugins** | Internal tools Maven uses to perform tasks (they are JAR files themselves) | Downloaded to `~/.m2/repository` automatically | Each build phase is executed by a plugin |

### How It All Works Together — Netflix Example

When a developer at Netflix runs `mvn package` on their microservice:

```
Step 1: Maven reads pom.xml
        → Finds: groupId=com.netflix, artifactId=user-service
        → Finds: 25 dependencies listed
        → Finds: packaging=jar

Step 2: Maven checks local repository (~/.m2/repository)
        → 20 dependencies already cached from previous builds
        → 5 dependencies missing

Step 3: Maven downloads missing 5 from remote repository
        → Company's Nexus server has 3 of them (cached from Maven Central)
        → Nexus fetches remaining 2 from Maven Central
        → All 5 stored in local repository for next time

Step 4: Maven calls plugins to execute build phases
        → maven-compiler-plugin: compiles .java → .class
        → maven-surefire-plugin: runs 200 unit tests
        → maven-jar-plugin: packages into user-service-3.1.jar

Step 5: Artifact created
        → target/user-service-3.1.jar (ready for deployment)
```

**All of this happens automatically with one command: `mvn package`**

---

## 1.5 Maven in the DevOps Context

As a DevOps engineer, you will:
- Set up CI/CD pipelines that run `mvn` commands
- Debug build failures in Jenkins/GitLab CI
- Manage artifact repositories (Nexus, Artifactory)
- Optimize build times for faster deployments
- Understand `pom.xml` to troubleshoot dependency conflicts

**Real-Life Example:** A developer pushes code to Git. Jenkins triggers a pipeline that runs `mvn clean package`. The pipeline fails with a dependency error. As the DevOps engineer, you need to read the `pom.xml`, understand the error, and fix the pipeline — not the Java code.

---

## 1.6 Maven vs Other Build Tools

| Tool | Language | Config File | Key Difference |
|------|----------|-------------|----------------|
| **Ant** | Java | `build.xml` (XML) | Oldest Java build tool. No conventions — you write every step manually. No dependency management. Still found in legacy projects. |
| **Maven** | Java/JVM | `pom.xml` (XML) | Convention over configuration. Standard structure. Built-in dependency management. Most widely used in enterprises. |
| **Gradle** | Java/JVM | `build.gradle` (Groovy/Kotlin) | More flexible, scriptable. Faster builds. Used by Android projects and newer Java projects. |
| npm | JavaScript | `package.json` | Node.js ecosystem |
| pip | Python | `requirements.txt` | Python ecosystem |

**Evolution:** Ant (2000) → Maven (2004) → Gradle (2012). Your course focuses on Maven because it's the most common in enterprise Java shops.

**Key takeaway:** Maven enforces a standard project structure and build process. This predictability is why it's still dominant in enterprise Java shops — and why DevOps engineers encounter it constantly.

---

## 1.7 Hands-On Exercise

1. Research: Find 3 open-source Java projects on GitHub that use Maven (look for `pom.xml` in the root).
2. Compare: Look at their `pom.xml` files — notice the similar structure.
3. Look at the `<dependencies>` section — identify which frameworks each project uses.
4. Think: How would you build these projects if you were setting up a CI pipeline?

---

**Next:** [Module 2 — Installing and Configuring Maven](02-installation-and-configuration.md)
