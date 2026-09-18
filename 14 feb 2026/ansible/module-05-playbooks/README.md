# Module 5: Playbooks Fundamentals

## Files
- `playbooks/first_playbook.yml` - Basic single-play playbook
- `playbooks/multi_tier_setup.yml` - Multi-play playbook (web + db)
- `playbooks/tags_example.yml` - Using tags to run specific tasks
- `playbooks/error_handling.yml` - ignore_errors, block/rescue/always, failed_when

## Execution Commands

```bash
ansible-playbook playbook.yml                          # Run
ansible-playbook playbook.yml --check --diff           # Dry run with diff
ansible-playbook playbook.yml --limit web1             # Limit hosts
ansible-playbook playbook.yml --start-at-task "Deploy" # Start at task
ansible-playbook playbook.yml --step                   # Step through
ansible-playbook playbook.yml --tags install            # Run tagged tasks
ansible-playbook playbook.yml --skip-tags deploy        # Skip tagged tasks
ansible-playbook playbook.yml -e "http_port=8080"      # Extra vars
ansible-playbook playbook.yml --syntax-check           # Syntax check
ansible-playbook playbook.yml --list-tasks             # List tasks
```
