# Shell Scripting for DevOps Engineers
## Complete Course: Basic to Advanced

**Duration:** 12 Modules (~12 weeks at 1 module/week)
**Prerequisites:** Basic computer literacy, access to a Linux/macOS terminal
**Goal:** Go from zero to writing production-grade shell scripts for DevOps workflows

---

## Course Structure

### Phase 1: Foundation
- [Module 1: The Shell — Your First Tool](module-01-the-shell.md)
- [Module 2: Variables, Data Types, Scope, and Comments](module-02-variables.md)
- [Module 3: Conditionals and Control Flow](module-03-conditionals.md)

### Phase 2: Intermediate
- [Module 4: Functions and Script Organization](module-04-functions.md)
- [Module 5: Text Processing — sed, awk, and Friends](module-05-text-processing.md)
- [Module 6: File Operations and I/O](module-06-file-operations.md)

### Phase 3: Advanced
- [Module 7: Process Management and Job Control](module-07-process-management.md)
- [Module 8: Networking and Remote Operations](module-08-networking.md)
- [Module 9: Error Handling, Debugging, and Security](module-09-error-handling.md)

### Phase 4: DevOps Applied
- [Module 10: Docker and Container Automation](module-10-docker.md)
- [Module 11: CI/CD, Cloud, and Infrastructure Automation](module-11-cicd-cloud.md)
- [Module 12: Capstone Projects and Production Patterns](module-12-capstone.md)

---

## Recommended Learning Path

| Week | Module | Focus |
|------|--------|-------|
| 1 | Module 1 | Get comfortable with the terminal |
| 2 | Module 2 | Variables and data handling |
| 3 | Module 3 | Logic and loops |
| 4 | Module 4 | Functions and script structure |
| 5 | Module 5 | Text processing (spend extra time here) |
| 6 | Module 6 | File I/O and redirection |
| 7 | Module 7 | Process management |
| 8 | Module 8 | Networking and SSH |
| 9 | Module 9 | Error handling and security |
| 10 | Module 10 | Docker automation |
| 11 | Module 11 | CI/CD and cloud |
| 12 | Module 12 | Capstone projects |

## Tools to Install

```bash
# Essential tools for this course
sudo apt-get install -y \
    shellcheck        # Shell script linter
    jq                # JSON processor
    curl              # HTTP client
    inotify-tools     # File watching
    moreutils         # sponge, parallel, etc.
    bc                # Calculator

# Optional but recommended
# docker, kubectl, aws-cli, terraform
```

## Resources

- **ShellCheck**: https://www.shellcheck.net — Paste your scripts for instant feedback
- **Bash Reference Manual**: https://www.gnu.org/software/bash/manual/
- **Advanced Bash-Scripting Guide**: https://tldp.org/LDP/abs/html/
- **explainshell.com**: Paste any command to see what each part does
- **Bash Pitfalls**: https://mywiki.wooledge.org/BashPitfalls

---

*Course designed for DevOps engineers starting from scratch. Each module builds on the previous one. Practice every exercise — reading alone won't make you proficient.*
