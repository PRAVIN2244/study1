# Quick Reference Card

## Most-Used Commands

| Command | Purpose |
|---------|---------|
| `git init` | Create a new repository |
| `git clone <url>` | Copy a remote repository |
| `git status` | Check working directory state |
| `git add <file>` | Stage changes |
| `git commit -m "msg"` | Create a commit |
| `git push origin <branch>` | Upload to remote |
| `git pull origin <branch>` | Download and merge from remote |
| `git switch -c <branch>` | Create and switch to a branch |
| `git merge <branch>` | Merge a branch into current |
| `git log --oneline` | View commit history |
| `git diff` | View unstaged changes |
| `git stash` | Temporarily save changes |
| `git restore <file>` | Discard working directory changes |
| `git revert <commit>` | Undo a commit safely |
| `git reset --hard HEAD~1` | Discard the last commit |
| `git rebase -i HEAD~N` | Interactively edit last N commits |
| `git cherry-pick <commit>` | Apply a specific commit |
| `git reflog` | View HEAD movement history |
| `git tag -a v1.0 -m "msg"` | Create an annotated tag |

## Git Aliases to Set Up Immediately

```bash
git config --global alias.s "status -s"
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.co "checkout"
git config --global alias.br "branch -vv"
git config --global alias.unstage "restore --staged"
git config --global alias.amend "commit --amend --no-edit"
git config --global alias.wip "commit -am 'WIP'"
```

---

