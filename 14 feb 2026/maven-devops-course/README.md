# Maven for DevOps Engineers — Basic to Advanced

A structured course covering Apache Maven from fundamentals to production-grade CI/CD integration, designed for freshers entering DevOps.

**Duration:** ~40-50 hours (self-paced) or 6-8 weeks (instructor-led)
**Prerequisites:** Basic Linux command line, any programming exposure

---

## Course Structure

### Part 0: Build Systems Foundations (Pre-requisite)

| Module | Topic | File |
|--------|-------|------|
| 0 | Build Systems Foundations — Source Code vs Executable, Compilation Stages, Artifacts, Build Automation | [00-build-systems-foundations.md](part-1-fundamentals/00-build-systems-foundations.md) |
| 0.5 | The Java Build Process — .java → .class → .jar | [00.5-java-build-process.md](part-1-fundamentals/00.5-java-build-process.md) |

### Part 1: Fundamentals (Week 1-2)

| Module | Topic | File |
|--------|-------|------|
| 1 | Frameworks, Dependencies, Maven Architecture | [01-what-is-maven.md](part-1-fundamentals/01-what-is-maven.md) |
| 2 | Installing Maven, Configuration Files, settings.xml vs pom.xml, Local Repository | [02-installation-and-configuration.md](part-1-fundamentals/02-installation-and-configuration.md) |
| 3 | Project Structure, Packaging (JAR/WAR), GAV Coordinates, Archetypes | [03-project-structure.md](part-1-fundamentals/03-project-structure.md) |
| 4 | Dependency Management, SNAPSHOT vs RELEASE Versions, Scopes | [04-dependency-management.md](part-1-fundamentals/04-dependency-management.md) |

### Part 2: Core Build Concepts (Week 3-4)

| Module | Topic | File |
|--------|-------|------|
| 5 | Build Lifecycle, Phases, Goals, Maven Site | [05-build-lifecycle.md](part-2-core-build/05-build-lifecycle.md) |
| 6 | Maven Plugins — Tag Hierarchy, Phase Attachment, Goal Flow, Antrun Example | [06-plugins.md](part-2-core-build/06-plugins.md) |
| 7 | Properties and Profiles | [07-properties-and-profiles.md](part-2-core-build/07-properties-and-profiles.md) |

### Part 3: Intermediate (Week 5-6)

| Module | Topic | File |
|--------|-------|------|
| 8 | Multi-Module Projects — Parent/Child POM, Inheritance, dependencyManagement vs dependencies | [08-multi-module-projects.md](part-3-intermediate/08-multi-module-projects.md) |
| 9 | Repository Management (Nexus/Artifactory) | [09-repository-management.md](part-3-intermediate/09-repository-management.md) |
| 10 | Maven in CI/CD Pipelines | [10-cicd-integration.md](part-3-intermediate/10-cicd-integration.md) |

### Part 4: Advanced & Capstone (Week 7-8)

| Module | Topic | File |
|--------|-------|------|
| 11 | Advanced Maven — Wrapper, Docker, SonarQube, Deployment Plugins, Version Management | [11-advanced-topics.md](part-4-advanced/11-advanced-topics.md) |
| 12 | Capstone Project — End-to-End Pipeline + Real-World Company Workflow | [12-capstone-project.md](part-4-advanced/12-capstone-project.md) |

### Reference

| Resource | File |
|----------|------|
| Quick Reference Card & Troubleshooting | [quick-reference.md](quick-reference.md) |

---

## Learning Path Timeline

| Week | Modules | Focus |
|------|---------|-------|
| 0 | 0, 0.5 | Build basics — source code vs executable, Java compilation pipeline |
| 1 | 1-3 | Frameworks, Maven architecture, project structure, JAR/WAR, archetypes |
| 2 | 4 | Dependencies — practice `mvn dependency:tree` |
| 3 | 5-6 | Build lifecycle, goals, plugins — add JaCoCo |
| 4 | 7 | Profiles — create dev/staging/prod profiles |
| 5 | 8 | Multi-module projects — build a 3-module project |
| 6 | 9 | Set up Nexus with Docker, deploy artifacts |
| 7 | 10-11 | CI pipelines, Docker multi-stage builds, SonarQube, security scanning |
| 8 | 12 | Capstone project + real-world company workflow simulation |

## Recommended Learning Order (Phase-Based)

This maps to the 10 learning phases for building understanding progressively:

| Phase | Topic | Module(s) |
|-------|-------|-----------|
| 1 | Build basics (source code → artifact) | Module 0 |
| 2 | Java compilation (.java → .class → .jar) | Module 0.5 |
| 3 | Maven basics (what Maven is, architecture) | Module 1 |
| 4 | Maven architecture (workspace, POM, repos, plugins) | Module 1 (1.4) |
| 5 | Maven lifecycle (clean, default, site + goals) | Module 5 |
| 6 | Standard project structure | Module 3 |
| 7 | GAV coordinates (groupId, artifactId, version) | Module 3 (3.2) |
| 8 | Dependency management | Module 4 |
| 9 | Maven in CI/CD pipelines | Module 10 |
| 10 | Advanced topics (multi-module, Docker, release) | Modules 8, 11 |

## Lecture-to-Module Mapping (Parts 1-23)

Every topic from the lecture transcripts is covered:

| Part | Lecture Topic | Module | Section |
|------|-------------|--------|---------|
| 1 | Build Management (source→artifact) | Module 0 | 0.1-0.4 |
| 2 | Build Automation (problems, benefits) | Module 0 | 0.5 |
| 3 | Build Tools (Ant, Maven, Gradle) | Module 1 | 1.6 |
| 4 | Maven Introduction (4 roles) | Module 1 | 1.3 |
| 5 | Maven Architecture (workspace, POM, repos, plugins) | Module 1 | 1.4 |
| 6 | Goals and Plugins | Module 5 | 5.3 |
| 7 | Maven Lifecycle (default, clean, site) | Module 5 | 5.1-5.2 |
| 8 | Directory Structure | Module 3 | 3.3 |
| 9 | GAV Coordinates | Module 3 | 3.2 |
| 10 | Installing Maven | Module 2 | 2.1-2.2 |
| 11 | Creating Maven Project (archetype) | Module 3 | 3.4 |
| 12 | Running Lifecycle | Module 5 | 5.4 |
| 13 | Local Repository | Module 2 | 2.4 |
| 14 | pom.xml Deep Understanding | Module 3 | 3.5 |
| 15 | Plugin Configuration (structure) | Module 6 | 6.3 |
| 16 | Plugin Execution (phase binding) | Module 6 | 6.4 |
| 17 | Direct Plugin Invocation (two methods) | Module 6 | 6.4 |
| 18 | Profiles | Module 7 | 7.2 |
| 19 | SNAPSHOT Versions | Module 4 | 4.3 |
| 20 | Multi-Module Projects | Module 8 | 8.1-8.5 |
| 21 | Deployment Plugins (JBoss, Tomcat) | Module 11 | 11.8 |
| 22 | Maven Site (documentation) | Module 5 | 5.6 |
| 23 | settings.xml (global config) | Module 2 | 2.3 |

---

## Each Module Includes

- Conceptual explanation with real-life analogies
- Practical code/config examples from enterprise scenarios (e-commerce, banking)
- Hands-on exercises
- DevOps-specific tips (CI optimization, troubleshooting, security)
