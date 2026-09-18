# Module 12: Capstone Project — End-to-End DevOps Pipeline

**Objective:** Build a complete CI/CD pipeline for a multi-module Maven project, simulating a real company environment.

---

## 12.1 Project: Online Banking Application

**Architecture:**

```
banking-app/                          (parent POM)
├── banking-common/                   (shared models, utilities)
├── banking-account-service/          (account management REST API)
├── banking-transaction-service/      (transaction processing)
└── banking-api-gateway/              (API gateway, aggregates services)
```

---

## 12.2 Step-by-Step Implementation

### Step 1: Create the Multi-Module Project

```bash
mkdir banking-app && cd banking-app

# Create parent pom.xml (packaging: pom)
# Create each module with archetype:generate
# Set up parent-child relationships
# Add inter-module dependencies
```

### Step 2: Add Build Plugins

```xml
<!-- In parent pom.xml -->
<build>
    <pluginManagement>
        <plugins>
            <!-- Compiler -->
            <plugin>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.12.1</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>
            <!-- Test reports -->
            <plugin>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.3</version>
            </plugin>
            <!-- Code coverage -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.11</version>
            </plugin>
            <!-- Security scan -->
            <plugin>
                <groupId>org.owasp</groupId>
                <artifactId>dependency-check-maven</artifactId>
                <version>9.0.7</version>
            </plugin>
        </plugins>
    </pluginManagement>
</build>
```

### Step 3: Configure Profiles

```xml
<profiles>
    <profile>
        <id>dev</id>
        <activation><activeByDefault>true</activeByDefault></activation>
        <properties>
            <spring.profiles.active>dev</spring.profiles.active>
        </properties>
    </profile>
    <profile>
        <id>prod</id>
        <properties>
            <spring.profiles.active>prod</spring.profiles.active>
        </properties>
    </profile>
    <profile>
        <id>security-scan</id>
        <build>
            <plugins>
                <plugin>
                    <groupId>org.owasp</groupId>
                    <artifactId>dependency-check-maven</artifactId>
                    <executions>
                        <execution>
                            <goals><goal>check</goal></goals>
                        </execution>
                    </executions>
                </plugin>
            </plugins>
        </build>
    </profile>
</profiles>
```

### Step 4: Create Dockerfile (for each service)

```dockerfile
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY banking-common/pom.xml banking-common/
COPY banking-account-service/pom.xml banking-account-service/
RUN mvn dependency:go-offline -B -pl banking-account-service -am
COPY banking-common/src banking-common/src
COPY banking-account-service/src banking-account-service/src
RUN mvn package -DskipTests -B -pl banking-account-service -am

FROM eclipse-temurin:17-jre-alpine
COPY --from=build /app/banking-account-service/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Step 5: Create CI/CD Pipeline

```yaml
# .github/workflows/banking-ci.yml
name: Banking App CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven

      - name: Compile
        run: ./mvnw clean compile -B

      - name: Unit Tests
        run: ./mvnw test -B

      - name: Upload Test Reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-reports
          path: '**/target/surefire-reports/'

      - name: Code Coverage
        run: ./mvnw jacoco:report -B

      - name: Upload Coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-reports
          path: '**/target/site/jacoco/'

  security-scan:
    runs-on: ubuntu-latest
    needs: build-and-test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven

      - name: OWASP Dependency Check
        run: ./mvnw dependency-check:aggregate -B

      - name: Upload Security Report
        uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: target/dependency-check-report.html

  package-and-deploy:
    runs-on: ubuntu-latest
    needs: [build-and-test, security-scan]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven

      - name: Package
        run: ./mvnw package -DskipTests -Pprod -B

      - name: Build Docker Images
        run: |
          docker build -f banking-account-service/Dockerfile -t banking-account:${{ github.sha }} .
          docker build -f banking-transaction-service/Dockerfile -t banking-txn:${{ github.sha }} .

      - name: Deploy to Nexus
        run: ./mvnw deploy -DskipTests -s ci-settings.xml -B
        env:
          NEXUS_USERNAME: ${{ secrets.NEXUS_USERNAME }}
          NEXUS_PASSWORD: ${{ secrets.NEXUS_PASSWORD }}
```

### Step 6: Add Maven Wrapper

```bash
mvn wrapper:wrapper -Dmaven=3.9.6
chmod +x mvnw
git add .mvn mvnw mvnw.cmd
```

---

## 12.3 Verification Checklist

Run through this checklist to verify your capstone:

```bash
# 1. Build entire project
./mvnw clean package -B

# 2. Run tests with coverage
./mvnw clean test jacoco:report -B

# 3. Build specific module
./mvnw clean package -pl banking-account-service -am -B

# 4. Build with production profile
./mvnw clean package -Pprod -DskipTests -B

# 5. Check dependency tree
./mvnw dependency:tree

# 6. Check for dependency updates
./mvnw versions:display-dependency-updates

# 7. Run security scan
./mvnw dependency-check:aggregate -B

# 8. Build Docker image
docker build -f banking-account-service/Dockerfile -t banking-account:latest .

# 9. Run the container
docker run -p 8080:8080 banking-account:latest

# 10. Push to GitHub and watch CI pipeline run
```

---

## 12.4 What You've Learned

By completing this capstone, you have hands-on experience with:

1. Multi-module Maven project structure
2. Parent POM with `dependencyManagement` and `pluginManagement`
3. Build profiles for dev/prod environments
4. JaCoCo code coverage enforcement
5. OWASP dependency security scanning
6. Multi-stage Docker builds with Maven
7. CI/CD pipelines (GitHub Actions) with Maven
8. Artifact deployment to Nexus
9. Maven Wrapper for version consistency

These are the exact skills used daily in enterprise DevOps teams.

---

---

## 12.5 Real-World Company Workflow — End-to-End Simulation

This section simulates exactly how a real company uses Maven in their daily workflow. Follow along to understand the complete picture.

### The Company: ShopEasy (E-Commerce Platform)

ShopEasy has a microservices architecture with these services:

```
product-service      → Product catalog (Spring Boot JAR)
order-service        → Order management (Spring Boot JAR)
payment-service      → Payment processing (Spring Boot JAR)
notification-service → Email/SMS notifications (Spring Boot JAR)
```

### Developer Workflow (Daily)

```bash
# 1. Developer clones the project
git clone git@github.com:shopeasy/product-service.git
cd product-service

# 2. Developer creates a feature branch
git checkout -b feature/add-product-search

# 3. Developer writes code
#    - Adds ProductSearchController.java
#    - Adds ProductSearchService.java
#    - Adds ProductSearchServiceTest.java

# 4. Developer builds and tests locally
mvn clean test
# Output: Tests run: 45, Failures: 0, Errors: 0

# 5. Developer commits and pushes
git add .
git commit -m "Add product search by category"
git push origin feature/add-product-search

# 6. Developer creates a Pull Request on GitHub
```

### CI Server Workflow (Automatic)

```bash
# Jenkins detects the push and runs automatically:

# Stage 1: Compile
mvn clean compile -B
# ✓ 85 source files compiled

# Stage 2: Unit Tests
mvn test -B
# ✓ 45 tests passed, 0 failures

# Stage 3: Code Coverage
mvn jacoco:report -B
# ✓ 82% line coverage (minimum: 80%)

# Stage 4: Security Scan
mvn dependency-check:check -B
# ✓ No vulnerabilities with CVSS >= 7

# Stage 5: Package
mvn package -DskipTests -B
# ✓ product-service-2.1.0-SNAPSHOT.jar created

# Stage 6: Deploy to Nexus (only on main branch)
mvn deploy -DskipTests -B
# ✓ Artifact uploaded to Nexus snapshots repository
```

### Artifact Server (Nexus)

```
Nexus Repository Manager
├── maven-snapshots/
│   └── com/shopeasy/product-service/
│       ├── 2.0.0-SNAPSHOT/
│       │   └── product-service-2.0.0-SNAPSHOT.jar    (previous version)
│       └── 2.1.0-SNAPSHOT/
│           └── product-service-2.1.0-SNAPSHOT.jar    (current development)
│
├── maven-releases/
│   └── com/shopeasy/product-service/
│       ├── 1.0.0/
│       │   └── product-service-1.0.0.jar             (production v1)
│       └── 2.0.0/
│           └── product-service-2.0.0.jar             (production v2)
│
└── maven-central-proxy/
    └── (cached copies of Spring Boot, Hibernate, etc.)
```

### Release Workflow (When Ready for Production)

```bash
# 1. Release manager runs Maven release plugin
mvn release:prepare
# Changes version: 2.1.0-SNAPSHOT → 2.1.0
# Creates Git tag: v2.1.0
# Bumps to next: 2.1.0 → 2.2.0-SNAPSHOT

mvn release:perform
# Builds tag v2.1.0
# Deploys product-service-2.1.0.jar to Nexus releases repo

# 2. Docker image built
docker build -t shopeasy/product-service:2.1.0 .
docker push registry.shopeasy.com/product-service:2.1.0

# 3. Kubernetes deployment updated
kubectl set image deployment/product-service \
  product-service=registry.shopeasy.com/product-service:2.1.0

# 4. Customers can now search products by category
```

### The Complete Flow — One Diagram

```
Developer                Git                 Jenkins              Nexus              Production
─────────               ─────               ───────              ─────              ──────────
                                                                                    
Write code ──────► Push to ──────► mvn clean ──────► Upload ──────► Docker
  .java            GitHub          package           .jar           container
  files                            │                                runs .jar
                                   ├── compile                      
                                   ├── test                         Customers
                                   ├── coverage                     use the
                                   ├── security                     application
                                   └── package                      
```

**This is the real build lifecycle in production.** Every Java project at every company follows this pattern — the tools may differ, but the flow is the same.

### Recommended Learning Order

Follow this order to build your understanding progressively:

| Step | Topic | Module |
|------|-------|--------|
| 1 | Build basics (source code → artifact) | [Module 0](../part-1-fundamentals/00-build-systems-foundations.md) |
| 2 | Java compilation (.java → .class → .jar) | [Module 0.5](../part-1-fundamentals/00.5-java-build-process.md) |
| 3 | Frameworks and Maven introduction | [Module 1](../part-1-fundamentals/01-what-is-maven.md) |
| 4 | Installing Java and Maven | [Module 2](../part-1-fundamentals/02-installation-and-configuration.md) |
| 5 | Project structure and packaging | [Module 3](../part-1-fundamentals/03-project-structure.md) |
| 6 | Maven lifecycle and goals | [Module 5](../part-2-core-build/05-build-lifecycle.md) |
| 7 | pom.xml and dependencies | [Module 4](../part-1-fundamentals/04-dependency-management.md) |
| 8 | Plugins and profiles | [Modules 6-7](../part-2-core-build/06-plugins.md) |
| 9 | Local repository and Nexus | [Module 9](../part-3-intermediate/09-repository-management.md) |
| 10 | CI/CD integration | [Module 10](../part-3-intermediate/10-cicd-integration.md) |
| 11 | Multi-module projects | [Module 8](../part-3-intermediate/08-multi-module-projects.md) |
| 12 | Advanced topics and Docker | [Module 11](../part-4-advanced/11-advanced-topics.md) |

---

**Congratulations!** You've completed the Maven for DevOps Engineers course.

See the [Quick Reference Card](../quick-reference.md) for a handy cheat sheet.
