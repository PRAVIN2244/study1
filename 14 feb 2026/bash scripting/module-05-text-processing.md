## Module 5: Text Processing — sed, awk, and Friends

### 5.1 grep — Pattern Matching

```bash
# Basic grep
grep "error" /var/log/syslog              # Lines containing "error"
grep -i "error" /var/log/syslog           # Case-insensitive
grep -c "error" /var/log/syslog           # Count matches
grep -n "error" /var/log/syslog           # Show line numbers
grep -v "debug" /var/log/syslog           # Invert (exclude "debug")
grep -r "TODO" ./src/                      # Recursive search
grep -l "password" /etc/*                  # List filenames only
grep -A3 -B1 "error" log.txt             # 3 lines after, 1 before

# Extended regex (-E or egrep)
grep -E "error|warning|critical" /var/log/syslog
grep -E "^[0-9]{1,3}\.[0-9]{1,3}" access.log    # Lines starting with IP

# Practical: Find failed SSH logins
grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn
```

### 5.2 sed — Stream Editor

```bash
# Substitute (s/old/new/)
sed 's/http/https/' urls.txt              # First occurrence per line
sed 's/http/https/g' urls.txt             # All occurrences (global)
sed -i 's/http/https/g' urls.txt          # Edit file in-place
sed -i.bak 's/http/https/g' urls.txt     # In-place with backup

# Delete lines
sed '/^#/d' config.txt                    # Delete comment lines
sed '/^$/d' config.txt                    # Delete empty lines
sed '1,5d' file.txt                       # Delete lines 1-5

# Insert/Append
sed '3i\New line before line 3' file.txt  # Insert before line 3
sed '3a\New line after line 3' file.txt   # Append after line 3

# Multiple operations
sed -e 's/foo/bar/g' -e '/^#/d' file.txt

# Address ranges
sed '10,20s/old/new/g' file.txt           # Only lines 10-20
sed '/START/,/END/d' file.txt             # Delete between patterns

# Practical: Update config files
sed -i 's/^listen_port=.*/listen_port=8080/' app.conf
sed -i '/^#.*max_connections/s/^#//' app.conf    # Uncomment a line
```

### 5.3 awk — Pattern Scanning and Processing

```bash
# Basic structure: awk 'pattern { action }' file

# Print specific columns
awk '{print $1, $3}' file.txt             # Columns 1 and 3
awk -F: '{print $1, $7}' /etc/passwd      # Custom delimiter

# Filtering
awk '$3 > 100' data.txt                   # Where column 3 > 100
awk '/error/ {print $0}' log.txt          # Lines matching "error"
awk '$9 >= 400' access.log                # HTTP errors in nginx log

# Built-in variables
# NR = record number (line number)
# NF = number of fields in current record
# FS = field separator
# OFS = output field separator

awk 'NR >= 10 && NR <= 20' file.txt       # Lines 10-20
awk '{print NR": "$0}' file.txt           # Add line numbers
awk '{print $NF}' file.txt                # Last column

# BEGIN and END blocks
awk 'BEGIN {print "Name\tShell"} 
     {print $1"\t"$7} 
     END {print "Total:", NR, "users"}' FS=: /etc/passwd

# Calculations
awk '{sum += $1} END {print "Total:", sum, "Average:", sum/NR}' numbers.txt

# Practical: Analyze disk usage by directory
du -sh /var/* 2>/dev/null | sort -rh | awk '{
    size=$1; dir=$2
    printf "%-10s %s\n", size, dir
}'

# Practical: Parse CSV
awk -F, '{
    name=$1; email=$2; role=$3
    if (role == "admin") 
        printf "ADMIN: %s <%s>\n", name, email
}' users.csv
```

### 5.4 Other Text Tools

```bash
# cut — Extract columns
cut -d: -f1,7 /etc/passwd                # Fields 1 and 7
cut -c1-10 file.txt                       # Characters 1-10

# tr — Translate/delete characters
echo "Hello World" | tr 'a-z' 'A-Z'      # HELLO WORLD
echo "extra   spaces" | tr -s ' '        # Squeeze spaces
cat file.txt | tr -d '\r'                 # Remove Windows line endings

# sort and uniq
sort file.txt                              # Sort alphabetically
sort -n file.txt                           # Sort numerically
sort -t: -k3 -n /etc/passwd              # Sort by field 3
sort file.txt | uniq -c | sort -rn        # Count occurrences

# paste — Merge files side by side
paste names.txt emails.txt                 # Tab-separated merge

# column — Format into columns
mount | column -t                          # Aligned columns

# xargs — Build commands from input
find . -name "*.log" | xargs rm -f
find . -name "*.sh" | xargs grep "TODO"
echo "web01 web02 web03" | xargs -n1 ping -c1
cat servers.txt | xargs -I{} ssh {} "uptime"
```

### 5.5 Real-Life Example: Kubernetes Log Parser

```bash
#!/bin/bash
# k8s-log-parser.sh — Parse and analyze Kubernetes pod logs

NAMESPACE="${1:-default}"
POD_PATTERN="${2:-.*}"
SINCE="${3:-1h}"

echo "Analyzing logs from namespace: $NAMESPACE (last $SINCE)"
echo "========================================================="

# Get matching pods
PODS=$(kubectl get pods -n "$NAMESPACE" -o name | grep -E "$POD_PATTERN")

for pod in $PODS; do
    pod_name=${pod#pod/}
    echo -e "\n--- $pod_name ---"

    logs=$(kubectl logs "$pod" -n "$NAMESPACE" --since="$SINCE" 2>/dev/null)

    if [ -z "$logs" ]; then
        echo "  (no logs)"
        continue
    fi

    total=$(echo "$logs" | wc -l)
    errors=$(echo "$logs" | grep -ci "error" || true)
    warnings=$(echo "$logs" | grep -ci "warn" || true)
    fatals=$(echo "$logs" | grep -ci "fatal\|panic" || true)

    echo "  Total lines: $total"
    echo "  Errors: $errors | Warnings: $warnings | Fatal: $fatals"

    if [ "$errors" -gt 0 ]; then
        echo "  Last 3 errors:"
        echo "$logs" | grep -i "error" | tail -3 | sed 's/^/    /'
    fi
done

echo -e "\n========================================================="
echo "Summary: $(echo "$PODS" | wc -w) pods analyzed"
```

### Exercises — Module 5
1. Write a one-liner that finds the top 10 largest files in `/var/log` and shows their sizes.
2. Use `awk` to parse `/etc/passwd` and list all users with `/bin/bash` as their shell, formatted as a table.
3. Write a script that parses an nginx access log and generates an hourly traffic report.

---
