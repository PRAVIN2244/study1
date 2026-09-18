# Module 6: Maven Plugins

**Objective:** Understand that Maven does nothing by itself — plugins do all the work. Learn the two types of plugins, how to configure them, and the two ways to invoke them.

---

## 6.1 Everything is a Plugin

Maven by itself is just an engine. **Every action Maven performs is executed by a plugin.** Plugins are JAR files that Maven downloads and runs automatically.

| Phase | Plugin | What It Does |
|-------|--------|-------------|
| `compile` | `maven-compiler-plugin` | Compiles `.java` to `.class` |
| `test` | `maven-surefire-plugin` | Runs unit tests |
| `package` | `maven-jar-plugin` | Creates JAR file |
| `package` | `maven-war-plugin` | Creates WAR file |
| `deploy` | `maven-deploy-plugin` | Uploads to remote repo |
| `clean` | `maven-clean-plugin` | Deletes `target/` directory |
| `site` | `maven-site-plugin` | Generates HTML docs |

---

## 6.2 Two Types of Plugins

### Build Plugins

Used during the build process. Configured inside `<build><plugins>`. These are used **95% of the time**.

They handle:
- Compilation
- Testing
- Packaging
- Deployment
- Cleaning

### Reporting Plugins

Used to generate project documentation and reports. Configured inside `<reporting><plugins>`.

They generate:
- Dependency reports
- Project info pages
- Code coverage reports
- Javadoc documentation

```bash
# Build plugins run during:
mvn compile
mvn test
mvn package

# Reporting plugins run during:
mvn site
```

**Real-Life Example:** Build plugins are used by developers and CI servers every day. Reporting plugins are used by project managers, auditors, and architecture teams who need project documentation.

---

## 6.3 Plugin Structure — The Three Questions

Every plugin configuration in `pom.xml` answers three questions:

```
1. WHAT plugin?     → <groupId> + <artifactId> + <version>
2. WHEN to run?     → <executions> → <phase>
3. WHAT to do?      → <goals> + <configuration>
```

**Complete plugin structure:**

```xml
<build>
  <plugins>
    <plugin>
      <!-- WHAT plugin? -->
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-compiler-plugin</artifactId>
      <version>3.12.1</version>

      <!-- WHEN to run? + WHAT to do? -->
      <executions>
        <execution>
          <id>compile-java-17</id>
          <phase>compile</phase>        <!-- WHEN: during compile phase -->
          <goals>
            <goal>compile</goal>        <!-- WHAT: run the compile goal -->
          </goals>
        </execution>
      </executions>

      <!-- HOW to configure? -->
      <configuration>
        <source>17</source>
        <target>17</target>
      </configuration>
    </plugin>
  </plugins>
</build>
```

**Real-Life Example — Attaching Plugins to Phases:**

A company might attach custom plugins to different phases:

```
compile phase  →  code generation plugin runs (generates Java from schema)
test phase     →  coverage plugin uploads report to SonarQube
package phase  →  Docker plugin builds container image
deploy phase   →  notification plugin sends Slack message
```

---

## 6.4 Two Ways to Call Plugins

There are exactly two ways to run a plugin:

### Method 1 — Attach to Lifecycle Phase (Automatic)

The plugin runs automatically when Maven reaches that phase:

```xml
<plugin>
  <artifactId>maven-surefire-plugin</artifactId>
  <executions>
    <execution>
      <phase>test</phase>           <!-- Runs during 'test' phase -->
      <goals>
        <goal>test</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

```bash
mvn package
# Maven reaches 'test' phase → surefire plugin runs automatically
```

**Used for:** Automation. CI pipelines run `mvn clean install` and all bound plugins execute in order.

### Method 2 — Direct Plugin Invocation (Manual)

Run a plugin goal directly without going through the lifecycle:

```bash
mvn exec:exec                    # Run the exec-maven-plugin directly
mvn dependency:tree              # Run dependency plugin directly
mvn help:effective-pom           # Run help plugin directly
mvn versions:set -DnewVersion=2.0.0  # Run versions plugin directly
```

**Used for:** One-off tasks. A developer might run `mvn dependency:tree` to debug a conflict without rebuilding the entire project.

### Side-by-Side Comparison

| Aspect | Method 1: Lifecycle-Bound | Method 2: Direct Invocation |
|--------|--------------------------|----------------------------|
| **How** | Configured in `<executions>` with `<phase>` | Run from command line: `mvn plugin:goal` |
| **When it runs** | Automatically during lifecycle | Only when you explicitly call it |
| **Use case** | CI/CD automation | Developer debugging, one-off tasks |
| **Example** | `mvn package` triggers surefire | `mvn exec:exec` runs directly |

**Real-Life Example:**

```bash
# CI pipeline uses lifecycle-bound plugins (Method 1):
mvn clean install
# → compiler plugin runs at compile phase
# → surefire plugin runs at test phase
# → jar plugin runs at package phase
# All automatic.

# Developer uses direct invocation (Method 2):
mvn exec:exec
# → Only runs the exec plugin, nothing else
```

---

## 6.5 The pom.xml Plugin Tag Hierarchy — Step by Step

The lecture emphasized this structure. Every tag nests inside the previous one:

```
<project>                          ← Root tag (always)
  |
  +-- <build>                      ← "I want to configure build behavior"
       |
       +-- <plugins>               ← Plural: "I have one or more plugins"
            |
            +-- <plugin>           ← Singular: "Here is ONE plugin"
                 |
                 +-- <groupId>     ← WHAT plugin? (identity)
                 +-- <artifactId>
                 +-- <version>
                 |
                 +-- <executions>  ← Plural: "This plugin can execute multiple tasks"
                 |    |
                 |    +-- <execution>  ← Singular: "Here is ONE execution"
                 |         |
                 |         +-- <phase>   ← WHEN to run? (lifecycle phase)
                 |         +-- <goals>   ← WHAT to do?
                 |         |    +-- <goal>  ← Specific task name
                 |         |
                 |         +-- <configuration>  ← HOW to do it? (plugin-specific settings)
                 |
                 +-- <plugin>      ← Another plugin (you can have many)
```

**Rule about plural vs singular tags:**
- Tags ending with **s** (`plugins`, `executions`, `goals`) = containers that hold multiple items
- Tags without **s** (`plugin`, `execution`, `goal`) = individual items inside the container

```xml
<plugins>          ← Container (can hold many plugins)
    <plugin>       ← One plugin
    </plugin>
    <plugin>       ← Another plugin
    </plugin>
</plugins>

<executions>       ← Container (can hold many executions)
    <execution>    ← One execution (e.g., connect to server)
    </execution>
    <execution>    ← Another execution (e.g., deploy WAR)
    </execution>
</executions>
```

---

## 6.6 How Phase → Goal → Plugin Flow Works

This is the internal flow when Maven executes a phase:

```
You type: mvn compile
              |
              v
Maven lifecycle reaches: compile phase
              |
              v
Compile phase calls: compiler:compile goal
              |
              v
Goal knows: "I belong to maven-compiler-plugin"
              |
              v
maven-compiler-plugin executes the task
              |
              v
Result: .java files compiled to .class files
```

**Now with a custom plugin attached to compile:**

```
You type: mvn compile
              |
              v
Maven lifecycle reaches: compile phase
              |
              v
Step 1: Default compiler:compile goal runs
        → maven-compiler-plugin compiles .java → .class
              |
              v
Step 2: YOUR custom plugin runs (attached to compile phase)
        → Your plugin's goal is called
        → Your plugin executes the task from <configuration>
              |
              v
Compile phase is now complete
```

---

## 6.7 Phase Attachment Behavior — What Runs When?

This is one of the most important concepts from the lecture. When you attach a plugin to a phase, it runs **every time that phase is reached** — even if you called a later phase.

### Example: Plugin Attached to `compile` Phase

```xml
<plugin>
    <artifactId>maven-antrun-plugin</artifactId>
    <executions>
        <execution>
            <phase>compile</phase>     <!-- Attached to compile -->
            <goals><goal>run</goal></goals>
            <configuration>
                <target>
                    <echo message="Calling ant task after compile!"/>
                </target>
            </configuration>
        </execution>
    </executions>
</plugin>
```

**What happens with different commands:**

```bash
# Command: mvn compile
# Maven does:
#   1. process-resources (default)
#   2. compile (default)
#   3. antrun plugin runs ← attached to compile
# STOPS HERE

# Command: mvn test
# Maven does:
#   1. process-resources (default)
#   2. compile (default)
#   3. antrun plugin runs ← attached to compile (STILL RUNS!)
#   4. process-test-resources (default)
#   5. test-compile (default)
#   6. test (default)
# STOPS HERE
# The plugin ran because Maven goes through compile on the way to test.

# Command: mvn clean
# Maven does:
#   1. clean (default)
# STOPS HERE
# The plugin does NOT run — clean lifecycle doesn't include compile.

# Command: mvn package
# Maven does:
#   1. process-resources
#   2. compile
#   3. antrun plugin runs ← attached to compile (RUNS!)
#   4. test-compile
#   5. test
#   6. package
# STOPS HERE
```

**Key insight:** Maven always executes the lifecycle from the beginning. If your plugin is attached to `compile`, it runs whenever ANY phase after compile is called (`test`, `package`, `install`, `deploy`). But it does NOT run for `clean` because that's a separate lifecycle.

### Changing the Phase Attachment

If you change the phase to `clean`:

```xml
<execution>
    <phase>clean</phase>     <!-- Now attached to clean -->
    <goals><goal>run</goal></goals>
</execution>
```

```bash
# mvn clean → plugin RUNS (attached to clean)
# mvn compile → plugin does NOT run (clean lifecycle not triggered)
# mvn clean compile → plugin RUNS during clean, then compile runs normally
```

---

## 6.8 Multiple Executions for the Same Plugin

One plugin can perform different tasks at different phases. Each task is a separate `<execution>`:

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-antrun-plugin</artifactId>
    <version>3.1.0</version>

    <executions>
        <!-- Execution 1: Run after compile -->
        <execution>
            <id>after-compile</id>
            <phase>compile</phase>
            <goals><goal>run</goal></goals>
            <configuration>
                <target>
                    <echo message="Compile completed! Running post-compile tasks..."/>
                </target>
            </configuration>
        </execution>

        <!-- Execution 2: Run after test -->
        <execution>
            <id>after-test</id>
            <phase>test</phase>
            <goals><goal>run</goal></goals>
            <configuration>
                <target>
                    <echo message="Tests completed! Generating report..."/>
                </target>
            </configuration>
        </execution>

        <!-- Execution 3: Run after package -->
        <execution>
            <id>after-package</id>
            <phase>package</phase>
            <goals><goal>run</goal></goals>
            <configuration>
                <target>
                    <echo message="Package created! Ready for deployment."/>
                </target>
            </configuration>
        </execution>
    </executions>
</plugin>
```

```bash
# mvn compile → prints "Compile completed!"
# mvn test → prints "Compile completed!" AND "Tests completed!"
# mvn package → prints all three messages
```

**Real-Life Example:** A company uses the same deployment plugin with multiple executions:
- Execution 1 (phase: `pre-integration-test`): Start the application server
- Execution 2 (phase: `integration-test`): Deploy the WAR and run tests
- Execution 3 (phase: `post-integration-test`): Stop the application server

---

## 6.9 Real Example from Lecture: maven-antrun-plugin

This is the exact example from the lecture. Scenario: Your company is migrating from Ant to Maven. Instead of rewriting all Ant scripts, you call Ant from Maven using the `maven-antrun-plugin`.

### Step 1: Find the Plugin

Go to the Maven plugins page: [https://maven.apache.org/plugins/](https://maven.apache.org/plugins/)

Find `maven-antrun-plugin` → click → go to "Usage" page → get the GAV and syntax.

### Step 2: Add to pom.xml

```xml
<project>
    <groupId>com.company</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <build>
        <plugins>
            <plugin>
                <!-- WHAT plugin? (GAV from the plugin's usage page) -->
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-antrun-plugin</artifactId>
                <version>3.1.0</version>

                <executions>
                    <execution>
                        <!-- WHEN to run? -->
                        <phase>compile</phase>

                        <!-- WHAT goal to call? -->
                        <goals>
                            <goal>run</goal>
                        </goals>

                        <!-- WHAT to do? (Ant-specific configuration) -->
                        <configuration>
                            <target>
                                <echo message="Calling ant tasks from Maven!"/>
                                <echo message="Build timestamp: ${maven.build.timestamp}"/>
                            </target>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

### Step 3: Run and Observe

```bash
$ mvn compile

[INFO] --- maven-resources-plugin:3.3.1:resources ---
[INFO] --- maven-compiler-plugin:3.12.1:compile ---
[INFO] Nothing to compile - all classes are up to date
[INFO] --- maven-antrun-plugin:3.1.0:run ---        ← Plugin runs after compile!
[INFO] Executing tasks
     [echo] Calling ant tasks from Maven!
     [echo] Build timestamp: 2024-01-15
[INFO] Executed tasks
[INFO] BUILD SUCCESS
```

```bash
$ mvn test

[INFO] --- maven-compiler-plugin:3.12.1:compile ---
[INFO] --- maven-antrun-plugin:3.1.0:run ---        ← Still runs! (compile is part of test)
     [echo] Calling ant tasks from Maven!
[INFO] --- maven-surefire-plugin:3.2.3:test ---     ← Then test runs
[INFO] Tests run: 1, Failures: 0
[INFO] BUILD SUCCESS
```

```bash
$ mvn clean

[INFO] --- maven-clean-plugin:3.3.2:clean ---
[INFO] BUILD SUCCESS
# antrun plugin did NOT run — not attached to clean phase
```

### Step 4: Understanding the Configuration

The `<configuration>` section contains **Ant XML**, not Maven XML. This is because the antrun plugin passes the configuration to Ant for execution:

```xml
<configuration>
    <target>
        <!-- This is Ant syntax, not Maven syntax -->
        <echo message="Hello from Ant!"/>           <!-- Print a message -->
        <mkdir dir="${project.build.directory}/reports"/>  <!-- Create a directory -->
        <copy file="config.xml" todir="target/"/>   <!-- Copy a file -->
    </target>
</configuration>
```

**Key point from the lecture:** The `<configuration>` values are different for every plugin. For antrun, you write Ant XML. For compiler plugin, you set `<source>` and `<target>`. For a database plugin, you'd set URL, username, password. Always check the plugin's usage page for the correct configuration format.

---

## 6.10 Real Example from Lecture: maven-exec-plugin (Second Plugin)

The lecture added a **second plugin** alongside the antrun plugin to demonstrate two things:
1. You can have multiple plugins in the same `<plugins>` tag
2. A plugin can be configured **without** `<executions>` — for direct invocation only

### What is the exec-maven-plugin?

It runs any command from Maven — just like typing it on the command prompt. You can call:
- Shell scripts (`bash`, `sh`)
- Python scripts (`python`)
- Perl scripts (`perl`)
- Any executable or command (`git`, `docker`, `kubectl`)

### Adding It as a Second Plugin (No Phase Attachment)

```xml
<build>
    <plugins>
        <!-- FIRST PLUGIN: antrun (attached to compile phase) -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-antrun-plugin</artifactId>
            <version>3.1.0</version>
            <executions>
                <execution>
                    <phase>compile</phase>
                    <goals><goal>run</goal></goals>
                    <configuration>
                        <target>
                            <echo message="Calling ant task after compile!"/>
                        </target>
                    </configuration>
                </execution>
            </executions>
        </plugin>

        <!-- SECOND PLUGIN: exec (NO phase attachment — direct invocation only) -->
        <plugin>
            <groupId>org.codehaus.mojo</groupId>
            <artifactId>exec-maven-plugin</artifactId>
            <version>3.1.0</version>
            <!-- NO <executions> tag — this plugin is NOT attached to any phase -->
            <!-- It will ONLY run when you call it directly: mvn exec:exec -->
            <configuration>
                <executable>git</executable>    <!-- What command to run -->
                <arguments>
                    <argument>--version</argument>  <!-- Arguments to pass -->
                </arguments>
            </configuration>
        </plugin>
    </plugins>
</build>
```

### Understanding the Configuration

```xml
<configuration>
    <executable>git</executable>       <!-- The program to run (like typing "git" on terminal) -->
    <arguments>
        <argument>--version</argument> <!-- First argument -->
    </arguments>
</configuration>
```

This is equivalent to typing on the command line:
```bash
git --version
```

**Multiple arguments example:**
```xml
<configuration>
    <executable>git</executable>
    <arguments>
        <argument>config</argument>     <!-- First argument -->
        <argument>--list</argument>     <!-- Second argument -->
    </arguments>
</configuration>
<!-- Equivalent to: git config --list -->
```

**Other executable examples:**
```xml
<!-- Run a shell script -->
<executable>bash</executable>
<arguments>
    <argument>deploy.sh</argument>
</arguments>

<!-- Run a Python script -->
<executable>python</executable>
<arguments>
    <argument>generate_report.py</argument>
</arguments>

<!-- Run a Docker command -->
<executable>docker</executable>
<arguments>
    <argument>build</argument>
    <argument>-t</argument>
    <argument>myapp:latest</argument>
    <argument>.</argument>
</arguments>
```

### Why No `<executions>` Tag?

Notice the exec plugin has **no `<executions>`** and **no `<phase>`**. This is intentional.

- The antrun plugin IS attached to a phase → it runs automatically during the lifecycle
- The exec plugin is NOT attached to any phase → it ONLY runs when you call it directly

```bash
# mvn compile:
#   1. compile runs (default)
#   2. antrun plugin runs (attached to compile) ← RUNS
#   3. exec plugin does NOT run (not attached to any phase) ← DOES NOT RUN

# mvn exec:exec:
#   1. ONLY the exec plugin runs ← RUNS
#   2. Nothing else happens — no compile, no test, no antrun
```

### Finding the Plugin's Goal Name

Every plugin has goals listed on its homepage. To call a plugin directly, you need to know its goal:

1. Go to the plugin's homepage (e.g., `mojohaus.org/exec-maven-plugin`)
2. Look at the "Goals" section
3. The exec plugin has two goals:

| Goal | Command | What It Does |
|------|---------|-------------|
| `exec:exec` | `mvn exec:exec` | Runs any OS command (shell, python, git, etc.) |
| `exec:java` | `mvn exec:java` | Runs a Java program's main method |

For the antrun plugin:

| Goal | Command | What It Does |
|------|---------|-------------|
| `antrun:run` | `mvn antrun:run` | Runs Ant tasks |

### Running the Exec Plugin

```bash
$ mvn exec:exec

[INFO] --- exec-maven-plugin:3.1.0:exec ---
git version 2.43.0
[INFO] BUILD SUCCESS
```

Only the exec plugin ran. No compile, no test, no antrun — nothing else.

---

## 6.11 Two Ways to Invoke a Plugin — Complete Picture

The lecture demonstrated both ways side by side using the same pom.xml:

```
Way 1: ATTACH to a phase                Way 2: CALL directly
(antrun plugin)                          (exec plugin)
─────────────────────                    ─────────────────────

Has <executions> with <phase>            Has NO <executions>
Has <goals> inside execution             Has NO <phase>
                                         Only has GAV + <configuration>

Runs automatically when phase            Runs ONLY when you type
is reached in lifecycle                  mvn pluginPrefix:goalName

Example:                                 Example:
  mvn compile → antrun runs                mvn exec:exec → exec runs
  mvn test → antrun runs (compile          mvn compile → exec does NOT run
             is part of test)              mvn test → exec does NOT run
  mvn clean → antrun does NOT run          mvn clean → exec does NOT run
```

**When to use each:**

| Scenario | Use Way 1 (Phase) | Use Way 2 (Direct) |
|----------|-------------------|---------------------|
| CI pipeline automation | ✅ Attach to phase — runs every build | |
| One-off developer task | | ✅ Call directly — run only when needed |
| Must run every build | ✅ | |
| Run only sometimes | | ✅ |
| Connect to DB for migration | | ✅ `mvn exec:exec` |
| Generate code before compile | ✅ Attach to `generate-sources` | |
| Check dependency updates | | ✅ `mvn versions:display-dependency-updates` |

---

## 6.12 Finding Plugins — Where to Get the GAV

The lecture explained how to find plugins:

1. Go to [https://maven.apache.org/plugins/](https://maven.apache.org/plugins/) — lists all official Maven plugins
2. Click on the plugin you need
3. Go to the "Usage" page
4. Copy the GAV (groupId, artifactId, version) and the configuration structure

**Common plugins you'll find there:**

| Plugin | What It Does | Where to Find |
|--------|-------------|---------------|
| `maven-compiler-plugin` | Compile Java code | maven.apache.org/plugins |
| `maven-surefire-plugin` | Run unit tests | maven.apache.org/plugins |
| `maven-antrun-plugin` | Run Ant tasks from Maven | maven.apache.org/plugins |
| `maven-war-plugin` | Create WAR files | maven.apache.org/plugins |
| `maven-deploy-plugin` | Upload artifacts to remote repo | maven.apache.org/plugins |
| `exec-maven-plugin` | Run shell commands or Java programs | mojohaus.org/exec-maven-plugin |

For third-party plugins (not from Apache), search on [https://mvnrepository.com](https://mvnrepository.com).

---

## 6.13 Configuring Plugins

Plugins are configured in the `<build>` section of `pom.xml`:

```xml
<build>
    <plugins>
        <!-- Configure Java version for compilation -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.12.1</version>
            <configuration>
                <source>17</source>
                <target>17</target>
            </configuration>
        </plugin>

        <!-- Configure Surefire to generate XML test reports -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.2.3</version>
            <configuration>
                <reportsDirectory>${project.build.directory}/test-reports</reportsDirectory>
            </configuration>
        </plugin>
    </plugins>
</build>
```

---

## 6.14 Plugins Every DevOps Engineer Should Know

### 1. `maven-surefire-plugin` — Unit Tests

```xml
<plugin>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.2.3</version>
    <configuration>
        <!-- Run tests in parallel -->
        <parallel>methods</parallel>
        <threadCount>4</threadCount>
        <!-- Fail build if no tests found -->
        <failIfNoTests>true</failIfNoTests>
    </configuration>
</plugin>
```

### 2. `maven-failsafe-plugin` — Integration Tests

```xml
<plugin>
    <artifactId>maven-failsafe-plugin</artifactId>
    <version>3.2.3</version>
    <executions>
        <execution>
            <goals>
                <goal>integration-test</goal>
                <goal>verify</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

### 3. `jacoco-maven-plugin` — Code Coverage

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.11</version>
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
```

After running `mvn test`, coverage report is at `target/site/jacoco/index.html`.

### 4. `dockerfile-maven-plugin` — Build Docker Images

```xml
<plugin>
    <groupId>com.spotify</groupId>
    <artifactId>dockerfile-maven-plugin</artifactId>
    <version>1.4.13</version>
    <configuration>
        <repository>myregistry.com/my-app</repository>
        <tag>${project.version}</tag>
    </configuration>
</plugin>
```

### 5. `maven-release-plugin` — Automate Releases

```bash
# Prepares release: removes -SNAPSHOT, creates tag, bumps version
mvn release:prepare

# Performs release: builds tag, deploys artifact
mvn release:perform
```

### Real-Life Example: Enforcing Code Coverage in CI

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.11</version>
    <executions>
        <execution>
            <id>check</id>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

Build fails if coverage drops below 80%.

---

## 6.15 Running Plugin Goals Directly

```bash
# Run a specific plugin goal without going through the lifecycle
mvn compiler:compile              # Just compile
mvn surefire:test                 # Just run tests
mvn dependency:tree               # Show dependency tree
mvn help:effective-pom            # Show the full resolved POM
mvn help:effective-settings       # Show the full resolved settings
mvn versions:display-dependency-updates  # Check for newer versions
```

---

## 6.16 Hands-On Exercise

```bash
# Exercise 1: Add the antrun plugin (from the lecture)
# 1. Create a Maven project: mvn archetype:generate -DarchetypeArtifactId=maven-archetype-quickstart -DgroupId=com.demo -DartifactId=plugin-demo -DinteractiveMode=false
# 2. Add the maven-antrun-plugin to pom.xml (attached to compile phase, echo message)
# 3. Run: mvn compile — see the echo message after compile
# 4. Run: mvn test — see the echo message still runs (compile is part of test)
# 5. Run: mvn clean — see the echo message does NOT run (different lifecycle)
# 6. Change the phase to "clean" and repeat steps 3-5 — observe the difference

# Exercise 2: Add multiple plugins
# 7. Add a SECOND plugin (e.g., maven-antrun-plugin with a different execution on test phase)
# 8. Run: mvn test — see both executions run in order
# 9. Run: mvn compile — see only the compile-phase execution runs

# Exercise 3: See all plugins Maven uses
# 10. Run: mvn help:effective-pom > effective-pom.xml
#     — Read this file to see ALL plugins Maven uses (even default ones you didn't configure)
# 11. Run: mvn help:describe -Dplugin=compiler — see the compiler plugin's goals
```

---

**Next:** [Module 7 — Properties and Profiles](07-properties-and-profiles.md)
