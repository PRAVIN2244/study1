## Module 6: File Operations and I/O

### 6.1 Input/Output Redirection

```bash
# Standard streams
# stdin  (0) — Input
# stdout (1) — Normal output
# stderr (2) — Error output

# Redirect stdout
echo "hello" > file.txt          # Overwrite
echo "world" >> file.txt         # Append

# Redirect stderr
command 2> errors.log            # Errors to file
command 2>> errors.log           # Append errors

# Redirect both
command > output.log 2>&1        # Both to same file
command &> output.log            # Shorthand (bash)
command > /dev/null 2>&1         # Discard everything

# Separate files
command > stdout.log 2> stderr.log

# Pipe stdout to another command
cat file.txt | grep "pattern" | sort | uniq -c

# Here document
cat <<EOF > /etc/nginx/conf.d/app.conf
server {
    listen 80;
    server_name app.example.com;
    location / {
        proxy_pass http://localhost:3000;
    }
}
EOF

# Here string
grep "admin" <<< "admin:x:0:0:root:/root:/bin/bash"

# Process substitution
diff <(ls dir1/) <(ls dir2/)     # Compare directory listings
while read line; do
    echo "$line"
done < <(kubectl get pods -o name)
```

### 6.2 Working with Temporary Files

```bash
#!/bin/bash

# Create temp file safely
TMPFILE=$(mktemp)
TMPDIR=$(mktemp -d)

# Always clean up
trap "rm -rf $TMPFILE $TMPDIR" EXIT

# Use temp files
curl -s "https://api.example.com/data" > "$TMPFILE"
process_data < "$TMPFILE"
```

### 6.3 File Descriptors

```bash
#!/bin/bash

# Open file descriptor for writing
exec 3> output.log

echo "This goes to stdout"
echo "This goes to file" >&3
echo "This also goes to stdout"

# Close file descriptor
exec 3>&-

# Open for reading
exec 4< input.txt
while read -r line <&4; do
    echo "Read: $line"
done
exec 4<&-

# Practical: Log to file AND stdout simultaneously
exec > >(tee -a /var/log/script.log) 2>&1
echo "This appears on screen AND in the log file"
```

### 6.4 File Watching and Monitoring

```bash
#!/bin/bash
# watch-deploy.sh — Watch a directory for new deployments

WATCH_DIR="/opt/deployments"
PROCESSED_DIR="/opt/deployments/processed"

mkdir -p "$PROCESSED_DIR"

echo "Watching $WATCH_DIR for new deployment packages..."

inotifywait -m -e create --format '%f' "$WATCH_DIR" | while read filename; do
    if [[ "$filename" == *.tar.gz ]]; then
        echo "[$(date)] New package detected: $filename"

        # Extract and deploy
        tar -xzf "${WATCH_DIR}/${filename}" -C /opt/app/
        
        # Restart service
        systemctl restart myapp

        # Move to processed
        mv "${WATCH_DIR}/${filename}" "$PROCESSED_DIR/"
        echo "[$(date)] Deployed: $filename"
    fi
done
```

### 6.5 Real-Life Example: Configuration File Manager

```bash
#!/bin/bash
# config-manager.sh — Manage application configs across environments

set -euo pipefail

CONFIG_DIR="./configs"
TEMPLATE_DIR="./templates"

generate_config() {
    local env="$1"
    local template="$2"
    local output="$3"

    echo "Generating $output for $env..."

    # Load environment-specific variables
    if [ ! -f "${CONFIG_DIR}/${env}.env" ]; then
        echo "ERROR: Environment file not found: ${CONFIG_DIR}/${env}.env"
        return 1
    fi

    # Start with template
    cp "$template" "$output"

    # Replace all {{VARIABLE}} placeholders with values from env file
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        # Replace placeholder
        sed -i "s|{{${key}}}|${value}|g" "$output"
    done < "${CONFIG_DIR}/${env}.env"

    # Check for unreplaced placeholders
    local remaining
    remaining=$(grep -c '{{.*}}' "$output" || true)
    if [ "$remaining" -gt 0 ]; then
        echo "WARNING: $remaining unreplaced placeholder(s) in $output:"
        grep -n '{{.*}}' "$output" | sed 's/^/  /'
        return 1
    fi

    echo "Config generated: $output"
}

# Usage
# configs/production.env:
#   DB_HOST=db.prod.internal
#   DB_PORT=5432
#   APP_PORT=8080
#   LOG_LEVEL=warn
#
# templates/app.conf.template:
#   database_host = {{DB_HOST}}
#   database_port = {{DB_PORT}}
#   listen_port = {{APP_PORT}}
#   log_level = {{LOG_LEVEL}}

generate_config "production" \
    "${TEMPLATE_DIR}/app.conf.template" \
    "/etc/myapp/app.conf"
```

### Exercises — Module 6
1. Write a script that tails multiple log files simultaneously, prefixing each line with the filename.
2. Create a config templating system that replaces `{{VAR}}` placeholders from a `.env` file.
3. Build a script that watches a directory and automatically compresses files older than 1 hour.

---
