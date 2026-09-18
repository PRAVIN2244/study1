# Module 6: Variables, Facts, and Registers

## Files
- `vars/app_config.yml` - Application variables
- `vars/db_config.yml` - Database variables
- `playbooks/play_vars.yml` - Inline play variables
- `playbooks/vars_files_example.yml` - Loading vars from files
- `playbooks/facts_example.yml` - Gathering and using system facts
- `playbooks/register_example.yml` - Capturing task output
- `playbooks/lookups_example.yml` - Reading from external sources
- `playbooks/prompts_example.yml` - Interactive variable prompts
- `playbooks/dynamic_config.yml` - Environment-based dynamic configuration

## Variable Precedence (Low to High)

1. role defaults
2. inventory file group vars
3. inventory group_vars/all
4. playbook group_vars/all
5. inventory group_vars/*
6. playbook group_vars/*
7. inventory file host vars
8. inventory host_vars/*
9. playbook host_vars/*
10. host facts / cached set_facts
11. play vars
12. play vars_prompt
13. play vars_files
14. role vars
15. block vars
16. task vars
17. include_vars
18. set_facts / registered vars
19. role params
20. extra vars (-e) **ALWAYS WINS**
