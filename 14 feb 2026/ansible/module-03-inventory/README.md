# Module 3: Inventory Management

## Files
- `inventory/hosts.ini` - Static inventory (INI format)
- `inventory/hosts.yml` - Static inventory (YAML format)
- `inventory/group_vars/` - Group-level variables
- `inventory/host_vars/` - Host-level variables

## Useful Commands

```bash
ansible all --list-hosts -i inventory/hosts.ini
ansible webservers --list-hosts -i inventory/hosts.ini
ansible-inventory --graph -i inventory/hosts.ini
ansible-inventory --host web1 -i inventory/hosts.ini
ansible all -m ping -i inventory/hosts.ini
```

## Inventory Patterns

```bash
ansible all -m ping                        # All hosts
ansible webservers -m ping                 # Specific group
ansible 'webservers:dbservers' -m ping     # Union (OR)
ansible 'webservers:&production' -m ping   # Intersection (AND)
ansible 'all:!dbservers' -m ping           # Exclusion (NOT)
ansible 'web*' -m ping                     # Wildcard
ansible all -m ping --limit web1           # Runtime limit
```
