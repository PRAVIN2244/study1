# Module 7: Properties and Profiles

**Objective:** Parameterize builds and handle environment-specific configurations.

---

## 7.1 Maven Properties

Properties are variables you define and reference with `${...}`:

```xml
<properties>
    <!-- Custom properties -->
    <java.version>17</java.version>
    <spring.boot.version>3.2.0</spring.boot.version>
    <junit.version>5.10.1</junit.version>

    <!-- Compiler settings -->
    <maven.compiler.source>${java.version}</maven.compiler.source>
    <maven.compiler.target>${java.version}</maven.compiler.target>
</properties>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
        <version>${spring.boot.version}</version>
    </dependency>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>${junit.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

**Built-in properties:**

```xml
${project.basedir}          <!-- /path/to/project -->
${project.version}          <!-- 1.0-SNAPSHOT -->
${project.artifactId}       <!-- my-app -->
${project.build.directory}  <!-- /path/to/project/target -->
${env.JAVA_HOME}            <!-- Environment variable -->
${settings.localRepository} <!-- ~/.m2/repository -->
```

### Overriding Directory Structure with Properties (From Lecture)

Maven expects the standard directory structure (`src/main/java`, `src/test/java`, etc.). But what if you're migrating an existing project that uses a different layout?

> **From Lecture**: "They are already working on some project and they have a different structure, a different tool, and now they are saying 'I want to move to Maven.' To move to Maven, we need the directory structure and the pom.xml. But they will say 'I cannot change the directory structure.'"

**Every directory in Maven is a property that can be overridden:**

```xml
<build>
    <!-- Override where Maven looks for source files -->
    <sourceDirectory>${project.basedir}/source/java</sourceDirectory>

    <!-- Override where Maven looks for test files -->
    <testSourceDirectory>${project.basedir}/tests/java</testSourceDirectory>

    <!-- Override where Maven looks for resources -->
    <resources>
        <resource>
            <directory>${project.basedir}/source/resources</directory>
        </resource>
    </resources>

    <!-- Override where Maven puts compiled output -->
    <outputDirectory>${project.basedir}/build/classes</outputDirectory>

    <!-- Override where Maven puts test output -->
    <testOutputDirectory>${project.basedir}/build/test-classes</testOutputDirectory>

    <!-- Override where Maven puts the final JAR/WAR -->
    <directory>${project.basedir}/build</directory>
</build>
```

**Default values (what Maven uses if you don't override):**

| Property | Default Value | Purpose |
|----------|--------------|---------|
| `sourceDirectory` | `${basedir}/src/main/java` | Java source files |
| `testSourceDirectory` | `${basedir}/src/test/java` | Test source files |
| `scriptSourceDirectory` | `${basedir}/src/main/scripts` | Script files |
| `outputDirectory` | `${basedir}/target/classes` | Compiled class files |
| `testOutputDirectory` | `${basedir}/target/test-classes` | Compiled test classes |
| `directory` | `${basedir}/target` | All build output |

**Example — Migrating a legacy project:**

```
Legacy project structure:          Maven standard structure:
├── code/                          ├── src/
│   ├── main/                      │   ├── main/
│   │   └── Calculator.java        │   │   └── java/
│   └── tests/                     │   │       └── Calculator.java
│       └── CalcTest.java          │   └── test/
└── output/                        │       └── java/
                                   │           └── CalcTest.java
                                   └── target/
```

```xml
<!-- pom.xml for the legacy project -->
<build>
    <sourceDirectory>${project.basedir}/code/main</sourceDirectory>
    <testSourceDirectory>${project.basedir}/code/tests</testSourceDirectory>
    <directory>${project.basedir}/output</directory>
</build>
```

### ⚠️ Why You Should NOT Override Directories (From Lecture)

> **From Lecture**: "It is not advisable to do, because if you think again — instead of giving all these values, it was so simple for us if we just maintain the directory structure. Even if you miss one of the values, then Maven will not work."

**Problems with custom directories:**
1. **Miss one property → Maven breaks** — you must override ALL related properties
2. **Hard to replicate** — copying the project to another team requires explaining the custom layout
3. **Confuses other developers** — everyone expects the standard Maven structure
4. **Breaks IDE integration** — IntelliJ/Eclipse expect standard paths

**The standard structure gives you:**
- Zero configuration for directories
- Easy project replication (copy, change pom.xml values, done)
- All plugins work out of the box
- Any Maven developer can navigate the project immediately

> **From Lecture**: "That is one of the advantages why Maven acts as a project management tool — if you follow the standard directory structure, go through Maven's lifecycle phases, and use the pom.xml through defining all the values."

**Real-Life Example — Migration at a Company:**
```
Team A: "We have 50 Java files in /code/src/ and tests in /code/tests/. 
         We can't restructure — too risky."

DevOps: Adds directory overrides to pom.xml. Build works.
        But 6 months later, a new plugin (JaCoCo) doesn't find test classes
        because it looks at the default testOutputDirectory.
        
        They spend 2 days debugging before realizing they need to override
        ANOTHER directory property.

Team B: Spends 1 day restructuring to standard Maven layout.
        Everything works forever with zero directory configuration.
```

---

## 7.2 Maven Profiles

Profiles let you customize the build for different environments:

```xml
<profiles>
    <!-- Development profile (default) -->
    <profile>
        <id>dev</id>
        <activation>
            <activeByDefault>true</activeByDefault>
        </activation>
        <properties>
            <db.url>jdbc:mysql://localhost:3306/devdb</db.url>
            <log.level>DEBUG</log.level>
        </properties>
    </profile>

    <!-- Staging profile -->
    <profile>
        <id>staging</id>
        <properties>
            <db.url>jdbc:mysql://staging-db.internal:3306/stagingdb</db.url>
            <log.level>INFO</log.level>
        </properties>
    </profile>

    <!-- Production profile -->
    <profile>
        <id>prod</id>
        <properties>
            <db.url>jdbc:mysql://prod-db.internal:3306/proddb</db.url>
            <log.level>WARN</log.level>
        </properties>
    </profile>
</profiles>
```

**Activating profiles:**

```bash
# Activate by name
mvn clean package -Pprod

# Activate multiple profiles
mvn clean package -Pstaging,coverage

# Check which profiles are active
mvn help:active-profiles
```

---

## 7.3 Profiles with Plugins — Controlling When Plugins Run

The lecture demonstrated a key use case: **moving plugins inside a profile** so they only run when you explicitly activate that profile.

### The Problem

When you attach a plugin to a phase (e.g., `clean`), it runs **every time** you call that phase. You can't skip it:

```xml
<!-- This plugin runs EVERY TIME you call mvn clean -->
<build>
    <plugins>
        <plugin>
            <artifactId>maven-antrun-plugin</artifactId>
            <executions>
                <execution>
                    <phase>clean</phase>
                    <goals><goal>run</goal></goals>
                    <configuration>
                        <target><echo message="Deploying to server..."/></target>
                    </configuration>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

```bash
mvn clean    # Plugin ALWAYS runs — you can't skip it
```

What if you want the plugin to run only sometimes?

### The Solution: Move Plugins Inside a Profile

Instead of putting plugins directly in `<build>`, put the entire `<build>` block inside a `<profile>`:

```xml
<!-- Plugins are INSIDE a profile — Maven only reads them when profile is activated -->
<profiles>
    <profile>
        <id>atom</id>                    <!-- Profile name -->
        <build>
            <plugins>
                <!-- Antrun plugin (attached to clean phase) -->
                <plugin>
                    <groupId>org.apache.maven.plugins</groupId>
                    <artifactId>maven-antrun-plugin</artifactId>
                    <version>3.1.0</version>
                    <executions>
                        <execution>
                            <phase>clean</phase>
                            <goals><goal>run</goal></goals>
                            <configuration>
                                <target>
                                    <echo message="Calling ant task!"/>
                                </target>
                            </configuration>
                        </execution>
                    </executions>
                </plugin>

                <!-- Exec plugin (no phase — direct invocation only) -->
                <plugin>
                    <groupId>org.codehaus.mojo</groupId>
                    <artifactId>exec-maven-plugin</artifactId>
                    <version>3.1.0</version>
                    <configuration>
                        <executable>git</executable>
                        <arguments>
                            <argument>--version</argument>
                        </arguments>
                    </configuration>
                </plugin>
            </plugins>
        </build>
    </profile>
</profiles>
```

### Demo: Without Profile vs With Profile

```bash
# WITHOUT profile — Maven does NOT read the plugins
$ mvn clean
[INFO] --- maven-clean-plugin:3.3.2:clean ---
[INFO] BUILD SUCCESS
# Only clean ran. Antrun plugin did NOT run.
# Maven didn't read the profile configuration.

# WITH profile — Maven reads the plugins
$ mvn clean -Patom
[INFO] --- maven-clean-plugin:3.3.2:clean ---
[INFO] --- maven-antrun-plugin:3.1.0:run ---
     [echo] Calling ant task!
[INFO] BUILD SUCCESS
# Clean ran, THEN antrun plugin ran.
# Maven read the profile and found the plugin attached to clean.

# Direct invocation WITHOUT profile — FAILS
$ mvn exec:exec
[ERROR] No plugin found for prefix 'exec'
# Maven doesn't know about the exec plugin — it's inside a profile that wasn't activated.

# Direct invocation WITH profile — WORKS
$ mvn exec:exec -Patom
[INFO] --- exec-maven-plugin:3.1.0:exec ---
git version 2.43.0
[INFO] BUILD SUCCESS
# Maven read the profile, found the exec plugin, and ran it.
```

### Real-Life Scenario: Test vs Production Deployment

A company has two environments. They create two profiles with different deployment plugins:

```xml
<profiles>
    <!-- TEST profile — deploys to test server -->
    <profile>
        <id>test-deploy</id>
        <build>
            <plugins>
                <plugin>
                    <groupId>org.apache.tomcat.maven</groupId>
                    <artifactId>tomcat7-maven-plugin</artifactId>
                    <version>2.2</version>
                    <configuration>
                        <url>http://test-server:8080/manager/text</url>
                        <server>test-tomcat</server>
                        <path>/myapp</path>
                    </configuration>
                </plugin>
            </plugins>
        </build>
    </profile>

    <!-- PRODUCTION profile — deploys to production server -->
    <profile>
        <id>prod-deploy</id>
        <build>
            <plugins>
                <plugin>
                    <groupId>org.apache.tomcat.maven</groupId>
                    <artifactId>tomcat7-maven-plugin</artifactId>
                    <version>2.2</version>
                    <configuration>
                        <url>http://prod-server:8080/manager/text</url>
                        <server>prod-tomcat</server>
                        <path>/myapp</path>
                    </configuration>
                </plugin>
            </plugins>
        </build>
    </profile>
</profiles>
```

```bash
# Deploy to TEST server
mvn clean package tomcat7:deploy -Ptest-deploy

# Deploy to PRODUCTION server
mvn clean package tomcat7:deploy -Pprod-deploy

# Just build — no deployment (no profile activated)
mvn clean package
```

**Same project, same pom.xml, different behavior based on which profile you activate.**

### Summary: Three Ways to Control Plugin Execution

| Method | How | When Plugin Runs |
|--------|-----|-----------------|
| **Attach to phase** | `<executions><phase>compile</phase>` | Every time that phase runs |
| **Direct invocation** | `mvn exec:exec` (no `<executions>`) | Only when you call it directly |
| **Inside a profile** | `<profiles><profile><build><plugins>` + `-Pname` | Only when you activate the profile |

**Interview question:** "How can you call different plugins for different environments?"
**Answer:** Create separate profiles (test, staging, prod), put environment-specific plugins inside each profile, and activate the desired profile with `-P` flag.

---

## 7.4 Resource Filtering

Combine profiles with resource filtering to inject values into config files:

**`src/main/resources/application.properties`:**

```properties
database.url=${db.url}
logging.level.root=${log.level}
app.version=${project.version}
```

**`pom.xml`:**

```xml
<build>
    <resources>
        <resource>
            <directory>src/main/resources</directory>
            <filtering>true</filtering>  <!-- Enable variable substitution -->
        </resource>
    </resources>
</build>
```

```bash
mvn clean package -Pprod
# application.properties in the JAR will contain:
# database.url=jdbc:mysql://prod-db.internal:3306/proddb
# logging.level.root=WARN
# app.version=1.0-SNAPSHOT
```

**Real-Life Example — CI/CD Pipeline:**

```groovy
pipeline {
    agent any
    parameters {
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'])
    }
    stages {
        stage('Build') {
            steps {
                sh "mvn clean package -P${params.ENVIRONMENT}"
            }
        }
    }
}
```

---

## 7.5 Profile Activation Triggers

Profiles can activate automatically:

```xml
<profile>
    <id>windows-build</id>
    <activation>
        <!-- Activate on Windows -->
        <os><family>windows</family></os>
    </activation>
</profile>

<profile>
    <id>java17</id>
    <activation>
        <!-- Activate when JDK 17 is detected -->
        <jdk>17</jdk>
    </activation>
</profile>

<profile>
    <id>ci</id>
    <activation>
        <!-- Activate when CI env var is set -->
        <property>
            <name>env.CI</name>
        </property>
    </activation>
</profile>
```

---

## 7.6 Hands-On Exercise

```bash
# 1. Add dev/staging/prod profiles to your pom.xml
# 2. Create src/main/resources/application.properties with ${db.url}
# 3. Enable resource filtering in pom.xml
# 4. Build with each profile and check the output:
mvn clean package -Pdev
unzip -p target/devops-demo-1.0-SNAPSHOT.jar application.properties

mvn clean package -Pprod
unzip -p target/devops-demo-1.0-SNAPSHOT.jar application.properties

# 5. Run: mvn help:active-profiles
# 6. Run: mvn help:all-profiles
```

---

**Next:** [Module 8 — Multi-Module Projects](../part-3-intermediate/08-multi-module-projects.md)
