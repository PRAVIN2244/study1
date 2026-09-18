# Module 08 — Security

## Security Model

```
┌──────────────────────────────────────────┐
│              Authentication              │
│  "Who are you?"                          │
│  (Jenkins DB, LDAP, SAML, GitHub OAuth)  │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│              Authorization               │
│  "What can you do?"                      │
│  (Matrix, Role-Based, Project-Based)     │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│            Credentials Store             │
│  "What secrets can you access?"          │
│  (Passwords, SSH keys, tokens, files)    │
└──────────────────────────────────────────┘
```

## Authentication

### Jenkins Internal Database

Default method. Users are stored in Jenkins.

**Manage Jenkins → Security → Security Realm → Jenkins' own user database**

### LDAP / Active Directory

```yaml
# JCasC configuration
jenkins:
  securityRealm:
    ldap:
      configurations:
        - server: "ldap://ldap.example.com:389"
          rootDN: "dc=example,dc=com"
          userSearchBase: "ou=People"
          userSearch: "uid={0}"
          groupSearchBase: "ou=Groups"
          groupSearchFilter: "(& (cn={0}) (objectclass=posixGroup))"
          managerDN: "cn=admin,dc=example,dc=com"
          managerPasswordSecret: "${LDAP_PASSWORD}"
```

### GitHub OAuth

Install **GitHub Authentication Plugin**:

1. Create OAuth App in GitHub: Settings → Developer settings → OAuth Apps
2. Authorization callback URL: `https://jenkins.example.com/securityRealm/finishLogin`

```yaml
jenkins:
  securityRealm:
    github:
      githubWebUri: "https://github.com"
      githubApiUri: "https://api.github.com"
      clientID: "${GITHUB_CLIENT_ID}"
      clientSecret: "${GITHUB_CLIENT_SECRET}"
      oauthScopes: "read:org,user:email"
```

### SAML (SSO)

Install **SAML Plugin** for integration with Okta, Azure AD, OneLogin, etc.

## Authorization

### Matrix-Based Security

Fine-grained permissions per user/group:

```
                    admin   dev-team   qa-team   viewer
Overall/Read         ✓        ✓          ✓         ✓
Overall/Administer   ✓
Job/Build            ✓        ✓          ✓
Job/Configure        ✓        ✓
Job/Read             ✓        ✓          ✓         ✓
Job/Delete           ✓
View/Read            ✓        ✓          ✓         ✓
Agent/Build          ✓        ✓
Credentials/View     ✓        ✓
```

### Role-Based Access Control (RBAC)

Install **Role-based Authorization Strategy Plugin**:

```yaml
# JCasC
jenkins:
  authorizationStrategy:
    roleBased:
      roles:
        global:
          - name: "admin"
            description: "Full access"
            permissions:
              - "Overall/Administer"
            entries:
              - user: "admin"
              - group: "jenkins-admins"

          - name: "developer"
            description: "Build and view jobs"
            permissions:
              - "Overall/Read"
              - "Job/Build"
              - "Job/Cancel"
              - "Job/Read"
              - "Job/Workspace"
              - "Run/Replay"
              - "View/Read"
            entries:
              - group: "developers"

          - name: "viewer"
            description: "Read-only access"
            permissions:
              - "Overall/Read"
              - "Job/Read"
              - "View/Read"
            entries:
              - group: "everyone"

        items:
          - name: "project-alpha"
            description: "Access to Project Alpha jobs"
            pattern: "alpha-.*"
            permissions:
              - "Job/Build"
              - "Job/Configure"
              - "Job/Read"
            entries:
              - group: "team-alpha"
```

### Project-Based Matrix Authorization

Per-job permissions:

**Job → Configure → Enable project-based security**

```
User/Group    Build    Configure    Read    Delete
team-lead       ✓         ✓         ✓        ✓
developer       ✓                   ✓
qa              ✓                   ✓
```

## Credentials Management

### Credential Types

| Type | Use Case |
|------|----------|
| **Username with password** | Git repos, APIs, databases |
| **SSH Username with private key** | SSH agent connections, Git over SSH |
| **Secret text** | API tokens, webhook secrets |
| **Secret file** | Kubeconfig, certificates, keystores |
| **Certificate** | PKCS#12 certificates |

### Credential Scopes

| Scope | Visibility |
|-------|-----------|
| **Global** | Available to all jobs and pipelines |
| **System** | Only available to Jenkins system (agents, mail) |
| **Folder** | Available to jobs within a specific folder |

### Adding Credentials

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

### Using Credentials in Pipelines

```groovy
pipeline {
    agent any
    environment {
        // Automatically binds based on credential type
        GIT_CREDS = credentials('github-credentials')
        // For username/password: GIT_CREDS_USR, GIT_CREDS_PSW
        // For secret text: GIT_CREDS contains the secret
    }
    stages {
        stage('Deploy') {
            steps {
                // withCredentials block for explicit binding
                withCredentials([
                    usernamePassword(
                        credentialsId: 'docker-hub',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    ),
                    sshUserPrivateKey(
                        credentialsId: 'deploy-key',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    ),
                    file(
                        credentialsId: 'kubeconfig',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        kubectl --kubeconfig=$KUBECONFIG apply -f deploy.yaml
                    '''
                }
            }
        }
    }
}
```

## Security Best Practices

### Controller Hardening

```yaml
# JCasC security settings
jenkins:
  numExecutors: 0                    # No builds on controller
  slaveAgentPort: 50000              # Fixed JNLP port
  agentProtocols:
    - "JNLP4-connect"               # Only modern protocol
  crumbIssuer:
    standard:
      excludeClientIPFromCrumb: false  # CSRF protection

security:
  scriptApproval:
    approvedSignatures: []           # Minimize script approvals
  globalJobDslSecurityConfiguration:
    useScriptSecurity: true

unclassified:
  buildDiscarders:
    configuredBuildDiscarders:
      - "jobBuildDiscarder"          # Auto-discard old builds
```

### Checklist

1. **Disable Jenkins CLI over remoting** — use SSH or HTTP API instead
2. **Enable CSRF protection** (crumb issuer) — enabled by default
3. **Set controller executors to 0** — never run builds on controller
4. **Use HTTPS** — terminate TLS at reverse proxy
5. **Restrict agent protocols** — use only JNLP4
6. **Audit plugin security** — check advisories regularly
7. **Use credential scoping** — folder-level credentials when possible
8. **Enable access logging** — configure in reverse proxy
9. **Restrict script approvals** — review all Groovy script requests
10. **Backup credentials** — encrypted, stored securely off-server

### API Token Security

```
Manage Jenkins → Users → user → Configure → API Token

- Generate new token (named, revocable)
- Old-style API tokens are deprecated
- Tokens are shown only once at creation

Usage:
  curl -u user:TOKEN https://jenkins.example.com/api/json
```

### Audit Trail

Install **Audit Trail Plugin**:

```yaml
unclassified:
  audit-trail:
    logBuildCause: true
    pattern: ".*/(?:configSubmit|doDelete|postBuildResult|enable|disable|cancelQueue|stop|toggleLogKeep|doWipeOutWorkspace|createItem|createView|toggleOffline|cancelQuietDown|quietDown|restart|exit|safeExit).*"
    loggers:
      - file:
          log: "/var/log/jenkins/audit.log"
          limit: 100
          count: 10
```
