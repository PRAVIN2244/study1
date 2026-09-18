# Maven Quick Reference Card for DevOps Engineers

---

## Build Commands

```bash
mvn clean package                    # Clean + build + test + package
mvn clean package -DskipTests       # Skip test execution
mvn clean install                    # Build + install to local repo
mvn clean deploy                     # Build + upload to remote repo
mvn -B clean package                 # Batch mode (CI-friendly)
mvn -T 1C clean package              # Parallel build (1 thread/core)
```

## Test Commands

```bash
mvn test                             # Run unit tests
mvn verify                           # Run unit + integration tests
mvn test -Dtest=MyTest               # Run specific test class
mvn test -Dtest=MyTest#myMethod      # Run specific test method
```

## Dependency Commands

```bash
mvn dependency:tree                  # Show dependency tree
mvn dependency:analyze               # Find unused/undeclared deps
mvn versions:display-dependency-updates  # Check for updates
mvn dependency-check:check           # OWASP security scan
```

## Debug Commands

```bash
mvn -X clean package                 # Debug output
mvn help:effective-pom               # Show resolved POM
mvn help:effective-settings          # Show resolved settings
mvn help:active-profiles             # Show active profiles
```

## Multi-Module Commands

```bash
mvn -pl module-name -am package      # Build module + dependencies
mvn -pl !module-name package         # Build all except module
mvn -rf :module-name package         # Resume from module
```

## Release Commands

```bash
mvn release:prepare                  # Prepare release (tag, version)
mvn release:perform                  # Build and deploy release
mvn release:rollback                 # Undo failed release
```

## Miscellaneous

```bash
mvn -U clean package                 # Force update snapshots
mvn -o clean package                 # Offline mode
mvn wrapper:wrapper                  # Add Maven Wrapper
```

---

## Troubleshooting Cheat Sheet

| Problem | Command | What to Look For |
|---------|---------|-----------------|
| Dependency conflict | `mvn dependency:tree -Dverbose` | Multiple versions of same lib |
| Missing class at runtime | `mvn dependency:tree -Dincludes=groupId:*` | Wrong scope (provided vs compile) |
| Build works locally, fails in CI | `mvn help:effective-settings` | Different settings.xml |
| Slow builds | `mvn -T 1C clean package` | Enable parallel builds |
| Stale dependencies | `rm -rf ~/.m2/repository && mvn clean package` | Corrupted local cache |
| Can't download from Nexus | Check `settings.xml` server ID matches mirror ID | ID mismatch |
| SNAPSHOT not updating | `mvn -U clean package` | Force snapshot update |

---

## Key File Locations

| File | Location | Purpose |
|------|----------|---------|
| Project config | `pom.xml` | Project dependencies, plugins, build config |
| Global settings | `$M2_HOME/conf/settings.xml` | Machine-wide Maven config |
| User settings | `~/.m2/settings.xml` | User-specific Maven config |
| Local repo | `~/.m2/repository/` | Cached dependency JARs |
| Build output | `target/` | Compiled classes, JARs, reports |
| Test reports | `target/surefire-reports/` | JUnit XML test results |
| Coverage report | `target/site/jacoco/` | JaCoCo HTML coverage report |

---

## `-DskipTests` vs `-Dmaven.test.skip=true`

| Flag | Compiles Tests? | Runs Tests? | When to Use |
|------|:-:|:-:|-------------|
| (none) | Yes | Yes | CI/CD pipelines (always) |
| `-DskipTests` | Yes | No | Quick local builds |
| `-Dmaven.test.skip=true` | No | No | When tests don't compile |

---

## SNAPSHOT vs RELEASE

| Aspect | SNAPSHOT | RELEASE |
|--------|----------|---------|
| Version | `1.0.0-SNAPSHOT` | `1.0.0` |
| Mutable? | Yes | No |
| Use case | Development | Production |
| Maven behavior | Checks for updates | Downloads once |
