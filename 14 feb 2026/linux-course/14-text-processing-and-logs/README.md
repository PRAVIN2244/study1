# Module 10: Text Processing

Text processing is where Linux truly shines. These tools let you search, transform, and analyze data from logs, configs, CSVs, and command output.

## Sample Data

We'll use these files throughout this module:

```bash
# /var/log/access.log (web server log)
192.168.1.100 - - [05/Feb/2025:10:00:01] "GET /api/users HTTP/1.1" 200 1234
192.168.1.101 - - [05/Feb/2025:10:00:02] "POST /api/login HTTP/1.1" 401 89
192.168.1.100 - - [05/Feb/2025:10:00:03] "GET /api/health HTTP/1.1" 200 15
10.0.0.5 - - [05/Feb/2025:10:00:04] "GET /api/users HTTP/1.1" 200 1234
192.168.1.102 - - [05/Feb/2025:10:00:05] "DELETE /api/users/5 HTTP/1.1" 403 45
192.168.1.100 - - [05/Feb/2025:10:00:06] "GET /static/style.css HTTP/1.1" 200 8900

# employees.csv
Name,Department,Salary,City
Alice,Engineering,95000,New York
Bob,Marketing,72000,Chicago
Charlie,Engineering,105000,San Francisco
Diana,HR,68000,New York
Eve,Engineering,88000,Chicago
Frank,Marketing,75000,San Francisco
```

---

## 10.1 `grep` — Search Text Patterns

### Basic search

```bash
$ grep "ERROR" /var/log/syslog
Feb  5 10:15:23 server myapp[3456]: ERROR: Database connection failed
Feb  5 10:15:25 server myapp[3456]: ERROR: Retry attempt 1 failed
Feb  5 10:20:00 server myapp[3456]: ERROR: Service unavailable
```

**Explanation**: `grep` prints lines containing the pattern "ERROR". It searches line by line.

### Case-insensitive (`-i`)

```bash
$ grep -i "error" /var/log/syslog
Feb  5 10:15:23 server myapp[3456]: ERROR: Database connection failed
Feb  5 10:18:00 server myapp[3456]: error: config file not found
Feb  5 10:20:00 server myapp[3456]: Error: timeout exceeded
```

### Show line numbers (`-n`)

```bash
$ grep -n "401" access.log
2:192.168.1.101 - - [05/Feb/2025:10:00:02] "POST /api/login HTTP/1.1" 401 89
```

**Explanation**: `-n` prefixes each match with its line number. Line 2 has a 401 (unauthorized) response.

### Count matches (`-c`)

```bash
$ grep -c "200" access.log
4

$ grep -c "GET" access.log
4
```

**Explanation**: `-c` returns the count of matching lines, not the lines themselves.

### Invert match (`-v`)

```bash
$ grep -v "200" access.log
192.168.1.101 - - [05/Feb/2025:10:00:02] "POST /api/login HTTP/1.1" 401 89
192.168.1.102 - - [05/Feb/2025:10:00:05] "DELETE /api/users/5 HTTP/1.1" 403 45
```

**Explanation**: `-v` shows lines that do NOT match. Here it shows all non-200 (error) responses.

### Show context (`-A`, `-B`, `-C`)

```bash
$ grep -B 2 -A 2 "ERROR" /var/log/syslog
Feb  5 10:15:21 server myapp[3456]: INFO: Processing request
Feb  5 10:15:22 server myapp[3456]: WARN: Slow query detected
Feb  5 10:15:23 server myapp[3456]: ERROR: Database connection failed
Feb  5 10:15:24 server myapp[3456]: INFO: Attempting reconnection
Feb  5 10:15:25 server myapp[3456]: ERROR: Retry attempt 1 failed
```

**Explanation**: `-B 2` shows 2 lines Before, `-A 2` shows 2 lines After. `-C 2` shows 2 lines of Context (both before and after).

```bash
# Context lines (before + after combined)
$ grep -C 2 "Exception" app.log
Feb  5 10:15:21 Processing request id=abc123
Feb  5 10:15:22 Connecting to database
Feb  5 10:15:23 Exception: Connection refused
Feb  5 10:15:24 Retrying in 5 seconds
Feb  5 10:15:25 Connection established
```

### Recursive search (`-r`)

```bash
$ grep -rn "TODO" /opt/myapp/src/
/opt/myapp/src/app.js:45:  // TODO: Add input validation
/opt/myapp/src/db.js:12:   // TODO: Implement connection pooling
/opt/myapp/src/auth.js:78: // TODO: Add rate limiting

# Recursive, case-insensitive, with line numbers
$ grep -nRi "timeout" /var/log/
/var/log/app.log:234:ERROR: Connection timeout after 30s
/var/log/syslog:1024:systemd[1]: Timeout reached for service myapp
```

**Explanation**: `-r` (or `-R`) searches all files in a directory recursively. `-n` shows line numbers. `-i` makes the search case-insensitive. Combine flags for searching logs across directories.

### Search for whole words (`-w`)

```bash
$ grep -w "log" /etc/rsyslog.conf
*.info;mail.none;authpriv.none;cron.none    /var/log/messages
```

**Explanation**: `-w` matches whole words only. Without it, "log" would also match "login", "catalog", "dialog".

### Extended regex (`-E` or `egrep`)

```bash
$ grep -E "(401|403|500)" access.log
192.168.1.101 - - [05/Feb/2025:10:00:02] "POST /api/login HTTP/1.1" 401 89
192.168.1.102 - - [05/Feb/2025:10:00:05] "DELETE /api/users/5 HTTP/1.1" 403 45
```

**Explanation**: `-E` enables extended regex. `(401|403|500)` matches any of these HTTP error codes.

### Show only the matched part (`-o`)

```bash
$ grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' access.log
192.168.1.100
192.168.1.101
192.168.1.100
10.0.0.5
192.168.1.102
192.168.1.100
```

**Explanation**: `-o` prints only the matching portion, not the entire line. Combined with a regex for IP addresses, it extracts all IPs from the log.

### List files containing a match (`-l`)

```bash
$ grep -rl "database" /etc/
/etc/mysql/my.cnf
/etc/postgresql/15/main/postgresql.conf
```

**Explanation**: `-l` lists only filenames, not the matching lines. Useful for finding which config files mention a term.

### `fgrep` (fixed-string grep)

`fgrep` is equivalent to `grep -F`. It searches for literal text (no regex interpretation), which is faster and safer when patterns contain special regex characters.

```bash
$ fgrep "using" paragraph.txt
Linux is powerful for using command-line tools.
We are using grep, sed, and awk daily.

$ fgrep -c "using" paragraph.txt
2

$ fgrep -i "this" paragraph.txt
This course is practical and detailed.

$ fgrep -n "learning" paragraph.txt
4:We are learning Linux step by step.

$ fgrep -v "@re" paragraph.txt
This course is practical and detailed.
Linux is powerful for using command-line tools.

$ fgrep -x "this is" paragraph.txt
this is
```

**Explanation**:
- `-F` / `fgrep` = fixed-string search (no regex)
- `-c` = count matches
- `-i` = ignore case
- `-n` = show line numbers
- `-v` = exclude matching lines
- `-x` = match entire line exactly

---

## 10.2 `sed` — Stream Editor

`sed` transforms text line by line. Most commonly used for find-and-replace.

### Basic substitution

```bash
# Replace first occurrence on each line
$ sed 's/unix/linux/' test.txt

# Replace all occurrences on each line (global)
$ sed 's/unix/linux/g' test.txt

# Case-insensitive replace (GNU sed)
$ sed 's/unix/linux/gI' test.txt
```

**Explanation**: `s/old/new/` substitutes the first occurrence per line. `g` replaces all occurrences. `I` makes the match case-insensitive (so `Unix`, `UNIX`, `unix` all get replaced).

```bash
$ echo "Hello World" | sed 's/World/Linux/'
Hello Linux

$ echo "foo bar foo baz foo" | sed 's/foo/FOO/g'
FOO bar FOO baz FOO
```

### Edit a file in-place (`-i`)

```bash
$ cat config.yaml
server:
  port: 8080
  host: localhost

$ sed -i 's/localhost/0.0.0.0/' config.yaml
$ cat config.yaml
server:
  port: 8080
  host: 0.0.0.0
```

**Explanation**: `-i` modifies the file directly. Use `-i.bak` to create a backup before modifying:

```bash
# In-place edit with backup
$ sed -i.bak 's/org/repl/g' config.yaml
$ ls
config.yaml  config.yaml.bak
```

**Explanation**: `-i.bak` creates a backup file with `.bak` extension before making changes. Essential for safe mass config edits across servers and automated replacements in CI.

### Print specific lines

```bash
# Print lines 5 to 10
$ sed -n '5,10p' file.txt

# Print everything EXCEPT lines 5 to 10
$ sed -n '5,10!p' file.txt

# Print line 5 only
$ sed -n '5p' file.txt

# Print lines matching a pattern
$ sed -n '/ERROR/p' /var/log/syslog
```

**Explanation**: `-n` suppresses default output. `p` prints matching lines. `!p` inverts — prints everything except the matched range.

### Delete lines

```bash
# Delete line 5
$ sed '5d' file.txt

# Delete lines 2-4
$ sed '2,4d' file.txt

# Delete lines containing "abc"
$ sed '/abc/d' file.txt

# Delete comment lines
$ sed '/^#/d' config.yaml

# Delete empty lines
$ sed '/^$/d' config.yaml
```

**Explanation**: `d` deletes lines. `/abc/d` deletes any line containing "abc". `^#` matches lines starting with `#`. `^$` matches empty lines.

### Insert and append lines

```bash
# Insert before line 3
$ sed '3i\# This is a new comment' config.yaml

# Append after line 3
$ sed '3a\new_setting: true' config.yaml

# Insert before a pattern
$ sed '/\[database\]/i\# Database Configuration' config.ini
```

### Multiple operations

```bash
$ sed -e 's/foo/bar/g' -e 's/baz/qux/g' -e '/^#/d' file.txt
```

**Explanation**: `-e` chains multiple sed operations. Processes them in order on each line.

### Practical sed examples

```bash
# Change a port in a config file
$ sed -i 's/listen 80;/listen 8080;/' /etc/nginx/nginx.conf

# Comment out a line
$ sed -i 's/^PermitRootLogin yes/# PermitRootLogin yes/' /etc/ssh/sshd_config

# Uncomment a line
$ sed -i 's/^# *PermitRootLogin/PermitRootLogin/' /etc/ssh/sshd_config

# Replace between delimiters (useful for paths)
$ sed -i 's|/var/www/html|/opt/myapp/public|g' /etc/nginx/nginx.conf
```

**Explanation**: The last example uses `|` as the delimiter instead of `/` to avoid escaping slashes in file paths.

---

## 10.3 `awk` — Pattern Scanning & Processing

`awk` processes text column by column. It's a mini programming language.

### Print specific columns

```bash
# Print entire line
$ awk '{print $0}' emp.txt
Alice Engineering 95000 New_York
Bob Marketing 72000 Chicago

# Print first column
$ awk '{print $1}' emp.txt
Alice
Bob

# Print first and fourth columns
$ awk '{print $1, $4}' emp.txt
Alice New_York
Bob Chicago

$ echo "Alice Engineering 95000" | awk '{print $1, $3}'
Alice 95000
```

**Explanation**: `$1` = first column, `$2` = second, `$3` = third. `$0` = entire line. Columns are separated by whitespace by default.

### Process files with custom delimiter

```bash
# Use colon as delimiter (e.g., /etc/passwd)
$ awk -F':' '{print $1}' /etc/passwd | head -5
root
daemon
bin
sys
sync

# Same with getent
$ getent passwd | awk -F':' '{print $1}' | head -5
root
daemon
bin
sys
sync

# CSV with comma delimiter
$ awk -F',' '{print $1, $3}' employees.csv
Name Salary
Alice 95000
Bob 72000
Charlie 105000
Diana 68000
Eve 88000
Frank 75000
```

**Explanation**: `-F':'` sets the field separator to colon. `-F','` sets it to comma. Default is whitespace.

### Filter rows (pattern matching)

```bash
$ awk -F',' '$2 == "Engineering"' employees.csv
Alice,Engineering,95000,New York
Charlie,Engineering,105000,San Francisco
Eve,Engineering,88000,Chicago
```

**Explanation**: Only prints lines where column 2 equals "Engineering".

```bash
# Salary greater than 80000
$ awk -F',' '$3 > 80000 {print $1, $3}' employees.csv
Alice 95000
Charlie 105000
Eve 88000
```

### Built-in variables

| Variable | Meaning                          |
|----------|----------------------------------|
| `$0`     | Entire line                      |
| `$1-$N`  | Column N                         |
| `NR`     | Current line number              |
| `NF`     | Number of fields in current line |
| `FS`     | Field separator                  |
| `OFS`    | Output field separator           |

```bash
# Print line numbers
$ awk '{print NR, $0}' employees.csv
1 Name,Department,Salary,City
2 Alice,Engineering,95000,New York
3 Bob,Marketing,72000,Chicago
...

# Print last column
$ awk -F',' '{print $NF}' employees.csv
City
New York
Chicago
...

# Skip header line
$ awk -F',' 'NR > 1 {print $1, $3}' employees.csv
Alice 95000
Bob 72000
...

# Get first 5 usernames from /etc/passwd
$ awk -F':' 'NR <= 5 {print $1}' /etc/passwd
root
daemon
bin
sys
sync

# Print first and last field from any file
$ awk '{print $1, $NF}' emp.txt
Alice New_York
Bob Chicago

# Same with colon-delimited file
$ awk -F':' '{print $1, $NF}' /etc/passwd | head -5
root /bin/bash
daemon /usr/sbin/nologin
bin /usr/sbin/nologin
sys /usr/sbin/nologin
sync /bin/sync
```

**Explanation**: `NR <= 5` limits output to the first 5 lines. `$NF` always refers to the last field regardless of how many fields exist. Useful for quick analytics on logs, CSV outputs, and generating reports without Python.

### Calculations

```bash
# Sum of all salaries
$ awk -F',' 'NR > 1 {sum += $3} END {print "Total:", sum}' employees.csv
Total: 503000

# Average salary
$ awk -F',' 'NR > 1 {sum += $3; count++} END {print "Average:", sum/count}' employees.csv
Average: 83833.3

# Max salary
$ awk -F',' 'NR > 1 {if ($3 > max) {max=$3; name=$1}} END {print name, max}' employees.csv
Charlie 105000
```

### BEGIN and END blocks

```bash
$ awk -F',' 'BEGIN {print "=== Employee Report ==="} NR > 1 {print $1, "-", $2} END {print "=== Total:", NR-1, "employees ==="}' employees.csv
=== Employee Report ===
Alice - Engineering
Bob - Marketing
Charlie - Engineering
Diana - HR
Eve - Engineering
Frank - Marketing
=== Total: 6 employees ===
```

**Explanation**: `BEGIN` runs before processing any lines. `END` runs after all lines are processed. The main block runs for each line.

### Log analysis with awk

```bash
# Count requests per IP
$ awk '{print $1}' access.log | sort | uniq -c | sort -rn
      3 192.168.1.100
      1 192.168.1.102
      1 192.168.1.101
      1 10.0.0.5

# Count requests per HTTP status code
$ awk '{print $9}' access.log | sort | uniq -c | sort -rn
      4 200
      1 403
      1 401

# Total bytes transferred
$ awk '{sum += $10} END {print sum, "bytes"}' access.log
11517 bytes
```

---

## 10.4 `sort` — Sort Lines

```bash
# Alphabetical sort
$ sort file.txt

# Reverse sort
$ sort -r file.txt

# Numeric sort
$ sort -n numbers.txt

# Sort and remove duplicates
$ sort -u file.txt

# Sort by column 2 (whitespace-delimited)
$ sort -k2 file.txt

# Equivalent explicit form (with space)
$ sort -k 2 file.txt

# Numeric sort on column 3 (CSV)
$ sort -t',' -k3 -n employees.csv
Name,Department,Salary,City
Diana,HR,68000,New York
Bob,Marketing,72000,Chicago
Frank,Marketing,75000,San Francisco
Eve,Engineering,88000,Chicago
Alice,Engineering,95000,New York
Charlie,Engineering,105000,San Francisco

# Reverse numeric sort
$ sort -t',' -k3 -nr employees.csv
```

**Explanation**:
- `-t','` — field separator
- `-k2` / `-k3` — sort by column 2 or 3
- `-n` — numeric sort (otherwise "9" > "10" alphabetically)
- `-r` — reverse order
- `-u` — remove duplicate lines

Useful for sorting IP lists, unique user lists, reports, and log-derived data.

---

## 10.5 `uniq` — Remove/Count Duplicates

`uniq` only removes **adjacent** duplicates, so always use with `sort`.

```bash
# Remove duplicates
$ sort names.txt | uniq
Alice
Bob
Charlie

# Count occurrences
$ awk '{print $1}' access.log | sort | uniq -c
      3 192.168.1.100
      1 192.168.1.101
      1 192.168.1.102
      1 10.0.0.5

# Show only duplicates
$ sort names.txt | uniq -d
Alice

# Show only unique lines (appearing once)
$ sort names.txt | uniq -u
Charlie
```

---

## 10.6 `cut` — Extract Columns

```bash
# Cut by delimiter and field
$ cut -d',' -f1,3 employees.csv
Name,Salary
Alice,95000
Bob,72000
Charlie,105000
...

# Cut by character position
$ echo "hello" | cut -c 1
h

$ echo "hello" | cut -c 4
l

$ echo "hello everyone" | cut -c 1-5
hello

$ cut -c1-10 access.log
192.168.1.
192.168.1.
192.168.1.
10.0.0.5 -
...

# Extract usernames from /etc/passwd
$ cut -d':' -f1 /etc/passwd | head -5
root
daemon
bin
sys
sync

# Extract user description (field 5) from /etc/passwd
$ cut -d':' -f5 /etc/passwd | head -5
root
daemon
bin
sys
sync
```

**Explanation**: `-d` sets the delimiter, `-f` selects fields. `-c` selects character positions. Useful for parsing system files, extracting CSV fields, or slicing fixed-width data.

---

## 10.7 `wc` — Word Count

```bash
$ wc /etc/passwd
  35   45  1890 /etc/passwd
```

**Explanation**: Shows lines, words, and bytes (in that order).

```bash
# Count lines only
$ wc -l /etc/passwd
35 /etc/passwd

# Count words
$ wc -w README.md
1234 README.md

# Count characters (multibyte-aware)
$ wc -m file.txt
5678 file.txt

# Count bytes
$ wc -c file.txt
5702 file.txt
```

**Explanation**: `-m` counts characters (respects multibyte encodings like UTF-8). `-c` counts raw bytes. For ASCII-only files, both return the same number. For files with Unicode characters (e.g., emojis, accented letters), `-c` will be higher than `-m`.

```bash
# Count lines in command output
$ ps aux | wc -l
128

# Count files in a directory
$ ls /var/log/ | wc -l
24

# Count total users on the system
$ getent passwd | wc -l
42
```

**Explanation**: `getent passwd` lists all user accounts (local + LDAP/NIS if configured). Piping to `wc -l` counts them. Useful for auditing user accounts on a server.

---

## 10.8 `tr` — Translate Characters

`tr` translates, deletes, or squeezes characters from standard input.

```bash
# Replace specific characters
$ echo "hello everyone" | tr 'e' 'E'
hEllo EvEryonE

# Convert to uppercase
$ echo "hello world" | tr 'a-z' 'A-Z'
HELLO WORLD

# Convert to lowercase
$ echo "HELLO WORLD" | tr 'A-Z' 'a-z'
hello world

# Replace characters
$ echo "hello:world:foo" | tr ':' '\n'
hello
world
foo

# Delete characters
$ echo "hello everyone" | tr -d 'e'
hllo vryon

$ echo "Hello 123 World 456" | tr -d '0-9'
Hello  World

# Squeeze repeated characters
$ echo "hello     everyone" | tr -s ' '
hello everyone

# Remove carriage returns (Windows → Linux line endings)
$ tr -d '\r' < windows_file.txt > linux_file.txt
```

**Explanation**: `tr` reads from stdin only (cannot take a filename argument). Use redirection (`< file`) or pipes to feed it data. Useful for cleaning logs or data in pipelines before processing.

---

## 10.9 `xargs` — Build Commands from Input

`xargs` takes input and passes it as arguments to another command.

```bash
# Find and delete files
$ find /tmp -name "*.tmp" -mtime +7 | xargs rm -f

# Find and grep
$ find /opt/myapp -name "*.js" | xargs grep "TODO"
/opt/myapp/src/app.js:  // TODO: Add validation
/opt/myapp/src/db.js:   // TODO: Connection pooling

# Parallel execution
$ find . -name "*.png" | xargs -P 4 -I {} convert {} -resize 50% {}
```

**Explanation**:
- `xargs` reads lines from stdin and passes them as arguments
- `-P 4` — run 4 processes in parallel
- `-I {}` — replace `{}` with each input line

```bash
# Handle filenames with spaces
$ find . -name "*.log" -print0 | xargs -0 rm -f
```

**Explanation**: `-print0` and `-0` use null character as delimiter instead of newline, safely handling filenames with spaces.

```bash
# Create a directory from input
$ echo "folder1" | xargs mkdir

# Create multiple directories from a list
$ echo -e "dir1\ndir2\ndir3" | xargs mkdir -p

# Find .txt files and compress into a tar archive (null-delimited for safety)
$ find . -name "*.txt" -print0 | xargs -0 tar czf files.tar.gz
```

**Explanation**: `xargs` converts input lines into arguments for any command. `-print0` and `-0` handle filenames with spaces safely. Useful for batch operations — compress, delete, change permissions, or process thousands of files.

---

## 10.10 `tee` — Split Output

`tee` reads from standard input and writes to both standard output (screen) and one or more files simultaneously.

```bash
# Write to file AND display on screen
$ df -h | tee disk_report.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   35G  26% /

# Append to file (instead of overwriting)
$ echo "Check completed at $(date)" | tee -a disk_report.txt
Check completed at Wed Feb  5 15:00:00 UTC 2025

# Count lines and save the result to a file at the same time
$ wc -l /var/log/syslog | tee -a line_counts.txt
14523 /var/log/syslog

$ cat line_counts.txt
14523 /var/log/syslog
```

**Explanation**: Without `-a`, `tee` overwrites the file. With `-a`, it appends. This is useful when you want to watch output in real time while also saving it for later review — common during long builds, deployments, or log searches.

---

## 10.11 Combining Tools — Real-World Pipelines

### Top 10 IPs hitting your server

```bash
$ awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
      3 192.168.1.100
      1 192.168.1.102
      1 192.168.1.101
      1 10.0.0.5
```

**Explanation**: Extract IPs → sort → count unique → sort by count descending → top 10.

### Find 404 errors and their URLs

```bash
$ awk '$9 == 404 {print $7}' access.log | sort | uniq -c | sort -rn
      5 /old-page.html
      3 /missing-image.png
      1 /api/v1/deprecated
```

### Analyze response times from logs

```bash
$ awk '{print $NF}' access.log | sort -n | awk '
  {a[NR]=$1; sum+=$1}
  END {
    print "Count:", NR
    print "Min:", a[1]
    print "Max:", a[NR]
    print "Avg:", sum/NR
    print "P50:", a[int(NR*0.5)]
    print "P95:", a[int(NR*0.95)]
    print "P99:", a[int(NR*0.99)]
  }'
```

### Extract and count error types

```bash
$ grep "ERROR" /var/log/app.log | sed 's/.*ERROR: //' | sort | uniq -c | sort -rn
     45 Database connection timeout
     23 Authentication failed
     12 File not found
      5 Out of memory
```

### Generate a CSV report from logs

```bash
$ awk '{print $1","$9","$10}' access.log | \
  awk -F',' 'BEGIN {print "IP,Status,Bytes"} {print}'
IP,Status,Bytes
192.168.1.100,200,1234
192.168.1.101,401,89
192.168.1.100,200,15
10.0.0.5,200,1234
192.168.1.102,403,45
192.168.1.100,200,8900
```

### Find processes using the most memory

```bash
$ ps aux --no-header | awk '{mem[$11] += $6} END {for (p in mem) printf "%10d KB  %s\n", mem[p], p}' | sort -rn | head -10
    680000 KB  java
     98000 KB  postgres
     42000 KB  nginx
```

---

## 10.12 More `grep` Real-World Examples

```bash
# Search recursively with context (3 lines before and after)
$ grep -rn -B3 -A3 "OutOfMemoryError" /var/log/

# Search for multiple patterns
$ grep -E "ERROR|FATAL|CRITICAL" /var/log/app.log

# Exclude directories from recursive search
$ grep -rn "password" /opt/myapp --exclude-dir={.git,node_modules,vendor}

# Search only specific file types
$ grep -rn "TODO" /opt/myapp --include="*.py" --include="*.js"

# Count matches per file
$ grep -rc "ERROR" /var/log/*.log | sort -t: -k2 -rn
/var/log/app.log:245
/var/log/syslog:12
/var/log/auth.log:3

# Show only filenames with matches
$ grep -rl "database_url" /opt/myapp/config/
/opt/myapp/config/production.yaml
/opt/myapp/config/staging.yaml

# Invert match — show lines WITHOUT pattern
$ grep -v "^#" /etc/nginx/nginx.conf | grep -v "^$"
# Shows config without comments or blank lines
```

---

## 10.13 More `sed` Real-World Examples

```bash
# Replace in-place with backup
$ sed -i.bak 's/localhost/db-server/g' config.yaml
# Creates config.yaml.bak before modifying

# Delete blank lines
$ sed '/^$/d' file.txt

# Delete comment lines
$ sed '/^#/d' /etc/nginx/nginx.conf

# Insert a line before a match
$ sed '/\[database\]/i # Database configuration section' config.ini

# Insert a line after a match
$ sed '/server_name/a \    proxy_pass http://backend:8080;' nginx.conf

# Replace only on specific line numbers
$ sed '5s/old/new/' file.txt          # Only line 5
$ sed '10,20s/old/new/g' file.txt     # Lines 10-20

# Extract text between two patterns
$ sed -n '/BEGIN/,/END/p' file.txt

# Remove trailing whitespace
$ sed 's/[[:space:]]*$//' file.txt

# Add line numbers
$ sed = file.txt | sed 'N;s/\n/\t/'
```

---

## 10.14 More `awk` Real-World Examples

```bash
# Sum a column of numbers
$ awk '{sum += $5} END {print "Total:", sum}' data.txt

# Average of a column
$ awk '{sum += $3; count++} END {print "Average:", sum/count}' data.txt

# Print lines where a field matches a condition
$ awk '$3 > 100 {print $1, $3}' data.txt

# Format output as a table
$ ps aux | awk 'NR<=10 {printf "%-10s %5s %5s %s\n", $1, $2, $3, $11}'

# Process CSV files
$ awk -F',' '{print $1, $3}' employees.csv

# Group by and count
$ awk '{count[$1]++} END {for (k in count) print count[k], k}' access.log | sort -rn | head -10

# Conditional formatting
$ df -h | awk 'NR>1 {
    usage = $5 + 0
    if (usage > 90) status = "CRITICAL"
    else if (usage > 75) status = "WARNING"
    else status = "OK"
    printf "%-20s %5s  %s\n", $6, $5, status
}'
/                     75%  OK
/data                 92%  CRITICAL
/boot                 45%  OK

# Multi-line processing (join every 3 lines)
$ awk 'NR%3{printf "%s,",$0;next} {print $0}' file.txt
```

---

## 10.15 Addon Commands

### `head` and `tail` with pipes

```bash
# Show lines 50-60 of a file
$ sed -n '50,60p' /var/log/syslog

# Show everything except the first line (skip header)
$ tail -n +2 employees.csv

# Show everything except the last 5 lines
$ head -n -5 /var/log/syslog

# Follow multiple log files simultaneously
$ tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

### `column` — Format output into columns

```bash
$ cat employees.csv | column -t -s','
Name     Department   Salary  City
Alice    Engineering  95000   New York
Bob      Marketing    72000   Chicago
Charlie  Engineering  105000  San Francisco

# Format mount output
$ mount | column -t | head -5
```

### `diff` and `comm` — Compare files

```bash
# Side-by-side diff with color
$ diff --color -y file1.txt file2.txt

# Find lines only in file1
$ comm -23 <(sort file1.txt) <(sort file2.txt)

# Find lines common to both files
$ comm -12 <(sort file1.txt) <(sort file2.txt)
```

### `paste` — Merge files side by side

```bash
$ cat names.txt
Alice
Bob
Charlie

$ cat scores.txt
95
72
105

$ paste names.txt scores.txt
Alice   95
Bob     72
Charlie 105

$ paste -d',' names.txt scores.txt
Alice,95
Bob,72
Charlie,105
```

---

## 10.16 Troubleshooting with Text Processing

### Find the top error messages in logs

```bash
$ grep "ERROR" /var/log/app.log | sed 's/.*ERROR: //' | sort | uniq -c | sort -rn | head -10
     45 Database connection timeout
     23 Authentication failed
     12 File not found
      5 Out of memory
```

### Find IPs causing 5xx errors

```bash
$ awk '$9 ~ /^5/ {print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -5
    200 192.168.1.100
     50 10.0.0.5
```

### Extract timestamps of errors for pattern analysis

```bash
$ grep "ERROR" /var/log/app.log | awk '{print $1, $2}' | cut -d: -f1,2 | sort | uniq -c
     45 Feb 5 14:30
     12 Feb 5 14:35
      2 Feb 5 15:00
# Errors spiked at 14:30 — correlate with deployments or changes
```

### Monitor a log file for specific patterns

```bash
$ tail -f /var/log/app.log | grep --line-buffered "ERROR\|FATAL"
# --line-buffered ensures output appears immediately
```

---

## 10.17 Regex Cheat Sheet

Regular expressions (regex) are patterns used by `grep`, `sed`, `awk`, and many other tools to match text.

### Basic Regex (used by `grep`, `sed`)

| Pattern   | Meaning                    | Example                          |
|-----------|----------------------------|----------------------------------|
| `^`       | Start of line              | `grep '^root' /etc/passwd`       |
| `$`       | End of line                | `grep 'bash$' /etc/passwd`       |
| `.`       | Any single character       | `grep 'h.t' file.txt` → hat, hit, hot |
| `*`       | Zero or more of previous   | `grep 'go*d' file.txt` → gd, god, good |
| `[]`      | Character class            | `grep '[aeiou]' file.txt`        |
| `[^]`     | Negated character class    | `grep '[^0-9]' file.txt`        |
| `\`       | Escape special character   | `grep '3\.14' file.txt`         |

### Extended Regex (used by `grep -E`, `egrep`, `awk`)

| Pattern   | Meaning                    | Example                          |
|-----------|----------------------------|----------------------------------|
| `+`       | One or more of previous    | `grep -E 'go+d' file.txt` → god, good |
| `?`       | Zero or one of previous    | `grep -E 'colou?r' file.txt` → color, colour |
| `{n}`     | Exactly n times            | `grep -E '[0-9]{3}' file.txt` → 3-digit numbers |
| `{n,m}`   | Between n and m times      | `grep -E '[0-9]{2,4}' file.txt` |
| `\|`      | OR (alternation)           | `grep -E 'error\|fail' log.txt` |
| `()`      | Grouping                   | `grep -E '(ab)+' file.txt`      |

### Practical examples

```bash
# Lines starting with "Error"
$ grep '^Error' /var/log/app.log

# Lines ending with a number
$ grep '[0-9]$' data.txt

# Match IP addresses (approximate)
$ grep -E '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' access.log

# Match email-like patterns
$ grep -E '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' contacts.txt

# Match lines with ERROR, WARN, or FATAL
$ grep -E 'ERROR|WARN|FATAL' /var/log/app.log
```

**Explanation**: Use basic regex with `grep` and `sed` by default. Use `-E` (extended) when you need `+`, `?`, `{}`, `|`, or `()`. Regex is essential for searching logs, validating formats, and filtering data in pipelines.

---

## 10.18 Additional Text Command Variants (Requested Set)

### Extra `cut` examples

```bash
$ echo "hello students-hi" | cut -f1
hello students-hi

$ echo "hello students-hi" | cut -f1
hello students-hi
```

**Explanation**: Without `-d`, `cut -f` uses TAB as delimiter. If no TAB exists, full line is returned.

### Extra `tr` examples

```bash
$ tr a-z A-Z < file.txt
$ tr A-Z a-z < file.txt
$ tr -d '\n' < file.txt
```

**Use case**: Case normalization and newline stripping in pipelines.

### Extra `sort` variants

```bash
$ sort -k1 file.txt
$ sort -k2 file.txt
$ sort -t: -k1 /etc/passwd
```

### Extra `awk` variants

```bash
$ awk '{print $2}' file.txt
$ awk '{print $NF}' file.txt
$ awk '/pattern/' file.txt
$ awk '{sum+=$1} END {print sum}' file.txt
```

### Extra `grep` character-class examples

```bash
$ grep "." file.txt
$ grep "[0-9]" file.txt
$ grep "[a-z]" file.txt
$ grep "[A-Z]" file.txt
```

**Use case**: Fast pattern validation for mixed content logs/data.

## Summary

| Command | Purpose                    | Key Usage                                |
|---------|----------------------------|------------------------------------------|
| `grep`  | Search for patterns        | `-i`, `-r`, `-n`, `-v`, `-c`, `-E`       |
| `sed`   | Stream editing             | `s/old/new/g`, `-i`, `d`, `-n 'p'`       |
| `awk`   | Column processing          | `-F`, `{print $1}`, `NR`, `END`          |
| `sort`  | Sort lines                 | `-n`, `-r`, `-k`, `-t`, `-u`             |
| `uniq`  | Remove/count duplicates    | `-c`, `-d`, `-u` (use with `sort`)       |
| `cut`   | Extract columns            | `-d`, `-f`, `-c`                         |
| `wc`    | Count lines/words/bytes    | `-l`, `-w`, `-c`                         |
| `tr`    | Translate characters       | `'a-z' 'A-Z'`, `-d`, `-s`               |
| `xargs` | Build commands from input  | `-I {}`, `-P` (parallel), `-0`           |
| `tee`   | Split output to file+screen| `tee file`, `tee -a file`                |

**Next Module**: [11 - Shell Scripting](../11-shell-scripting/README.md)

---

---

## 10.12 Interview Questions — Module 10

**Q1: What is the difference between grep, sed, and awk?**

- `grep` — searches for patterns and prints matching lines (filter)
- `sed` — stream editor for find/replace, deletion, insertion (transform)
- `awk` — pattern scanning and processing language with field-based operations (analyze)

Use `grep` to find, `sed` to modify, `awk` to extract and compute.

**Q2: How do you find and replace text across multiple files?**

```bash
# Using sed
sed -i 's/old_text/new_text/g' *.conf

# Using find + sed (recursive)
find /etc -name "*.conf" -exec sed -i 's/old/new/g' {} +

# Preview before replacing (without -i)
grep -rn "old_text" /etc/
```

**Q3: Explain piping and redirection with examples.**

Piping (`|`) sends stdout of one command to stdin of another. Redirection (`>`, `>>`, `2>`) sends output to files.

```bash
ps aux | grep nginx | awk '{print $2}'    # Pipe: chain commands
ls > files.txt                             # Redirect stdout to file
ls 2> errors.txt                           # Redirect stderr to file
ls &> all.txt                              # Redirect both to file
ls >> files.txt                            # Append (don't overwrite)
```

**Q4: How do you extract specific columns from a CSV file?**

```bash
# Using cut
cut -d',' -f1,3 data.csv                  # Fields 1 and 3

# Using awk
awk -F',' '{print $1, $3}' data.csv       # More flexible

# Using awk with formatting
awk -F',' '{printf "%-20s %s\n", $1, $3}' data.csv
```

**Q5: How do you count unique occurrences in a log file?**

```bash
# Count unique IP addresses in access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
```
