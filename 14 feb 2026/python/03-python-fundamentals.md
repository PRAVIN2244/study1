# Module 3 — Python Fundamentals

This module teaches you the building blocks of Python — variables, data types, and collections. Every concept is explained step by step with examples, outputs, and explanations of why things work the way they do.

### What We Will Cover

There is a lot of ground to cover in this module. Here is the roadmap:

```
Python Fundamentals
│
├── Language Fundamentals
│   ├── Variables and data types
│   ├── Comments
│   ├── Primitive types (strings, numbers, booleans)
│   └── String manipulation
│
├── Core Data Structures
│   ├── Lists
│   ├── Tuples
│   ├── Sets
│   └── Dictionaries
│
├── Control Flow (Module 04)
│   ├── Conditional logic — if / elif / else
│   ├── Loops — for and while
│   └── Loop control — break and continue
│
├── Efficient Iteration (Module 04)
│   ├── List, set, and dictionary comprehensions
│   ├── range() for generating sequences
│   └── enumerate() and zip() for combining iterables
│
└── Functions and Classes (Module 05)
    ├── Defining functions, parameters, return values
    ├── Lambda functions
    ├── Variable arguments — *args and **kwargs
    └── Introduction to classes, methods, and inheritance
```

> **Note:** Control flow, comprehensions, and functions are covered in Modules 04 and 05. This module focuses on the language fundamentals and data structures.

---

## Comments — Explaining Your Code

Python code may be readable, but comments and docstrings explain intent, rationale, and usage. Comments (`#`) are ignored by the interpreter. Docstrings (`"""..."""`) are accessible at runtime via `__doc__` — we will come back to docstrings later when we discuss functions.

### Single-Line Comments (`#`)

Use `#` to comment a single line or add an inline note after code:

```python
# This is a single-line comment
error_code = 0  # initializing error counter
```

Single-line comments are useful for:

- Explaining **why** something is done (not what — the code shows the what)
- Adding `TODO` / `FIXME` markers for work that still needs to be done
- Temporarily disabling a line of code during debugging

```python
# TODO: handle case when argument is None
def process(value):
    return value.strip()

# FIXME: this breaks when the list is empty
first_item = items[0]
```

> **Tip:** Many IDEs (VS Code, PyCharm) recognize `TODO` and `FIXME` patterns and can list them in a dedicated panel, making it easy to track outstanding work.

### Write Self-Documenting Code

Adding too many comments can do more harm than good. Focus on writing code that is understandable by itself, and reserve comments for explaining intent, summarizing complex logic, or clarifying non-obvious decisions:

```python
# Bad — the comment just restates the code
x = 5  # set x to 5

# Good — the comment explains the reasoning
x = 5  # default retry count per AWS SDK recommendation
```

If a comment is obvious from the code, remove it and keep the code cleaner.

### Multi-Line / Block Comments

Prefix each line with `#` to comment out a block of code. This is useful for disabling sections or annotating complex logic:

```python
# if True:
#     print("I will execute")
```

It is also possible to wrap text between triple single-quotes (`'''...'''`) or triple double-quotes (`"""..."""`):

```python
'''
This block is technically a string literal,
not a true comment.
'''
```

However, triple-quoted strings have a different meaning in Python — they are interpreted as **docstrings** when placed at the start of a module, class, or function. Docstrings are accessible at runtime via the `__doc__` attribute and through help commands like `help()` in the REPL. If you want to prevent that behavior, use `#` on each line instead.

Here is a quick preview of how docstrings work (covered fully in Module 05):

```python
def greet():
    """Print greeting message"""
    print("Hello")

print(greet.__doc__)
```

**Output:**

```
Print greeting message
```

Docstrings are also useful as script headers in DevOps automation:

```python
"""
Script: cleanup_logs.py
Purpose: Remove logs older than 30 days
Author: DevOps Team
"""
```

> **Bottom line:** Use `#` for comments. Reserve `"""..."""` for docstrings (covered in Module 05 with functions).

---

## Variables — Giving Names to Values

A variable is a name that points to a value stored in memory. Think of it as a labeled box — you put something inside, and later you use the label to get it back.

### Creating Your First Variable

```python
name = "Alice"
```

**What this does:** Python creates a space in memory, stores the text `"Alice"` there, and attaches the label `name` to it. The `=` sign is the **assignment operator** — it does not mean "equals" in the math sense. It means "store this value with this name."

Now you can use the variable:

```python
name = "Alice"
print(name)
```

**Run it:**

```bash
python3 variables.py
```

**Output:**

```
Alice
```

**Why this output:** `print(name)` looks up what `name` points to (which is `"Alice"`) and displays it on the screen.

### Storing Different Kinds of Values

```python
city = "Mumbai"          # A piece of text (called a "string")
age = 25                 # A whole number (called an "integer")
temperature = 36.6       # A decimal number (called a "float")
is_raining = False       # A true/false value (called a "boolean")
```

**Run it with print statements:**

```python
city = "Mumbai"
age = 25
temperature = 36.6
is_raining = False

print(city)
print(age)
print(temperature)
print(is_raining)
```

**Output:**

```
Mumbai
25
36.6
False
```

**Line-by-line explanation:**

- `print(city)` prints `Mumbai` because `city` holds the text `"Mumbai"`.
- `print(age)` prints `25` because `age` holds the number `25`.
- `print(temperature)` prints `36.6` because `temperature` holds the decimal `36.6`.
- `print(is_raining)` prints `False` because `is_raining` holds the boolean value `False`.

### Variables Can Change

A variable is not permanent. You can change what it holds at any time:

```python
score = 10
print(score)

score = 25
print(score)

score = score + 5
print(score)
```

**Output:**

```
10
25
30
```

**What happened step by step:**

1. `score = 10` — `score` now holds `10`. Print shows `10`.
2. `score = 25` — `score` is reassigned. The old value `10` is gone. Print shows `25`.
3. `score = score + 5` — Python first calculates the right side: `25 + 5 = 30`. Then it stores `30` back into `score`. Print shows `30`.

### Rules for Variable Names

Python has strict rules about what you can name a variable. Let us see each rule with an example of what happens when you break it.

**Rule 1: Names can contain letters, numbers, and underscores.**

```python
user_name = "Bob"       # Valid — uses letters and underscore
server1 = "web-01"      # Valid — uses letters and a number
_private = "hidden"     # Valid — starts with underscore
```

**Rule 2: Names cannot start with a number.**

```python
1server = "web-01"
```

**Output (error):**

```
  File "test.py", line 1
    1server = "web-01"
     ^
SyntaxError: invalid decimal literal
```

**Why:** Python sees `1` and thinks you are writing a number. Then it finds `server` and gets confused — numbers cannot have letters attached to them. Fix: use `server1` instead.

**Rule 3: Names cannot contain hyphens or spaces.**

```python
my-name = "Alice"
```

**Output (error):**

```
  File "test.py", line 1
    my-name = "Alice"
       ^
SyntaxError: cannot assign to expression
```

**Why:** Python sees `my - name` and thinks you are trying to subtract `name` from `my`. The hyphen `-` is the subtraction operator. Fix: use `my_name` (underscore) instead.

```python
my name = "Alice"
```

**Output (error):**

```
  File "test.py", line 1
    my name = "Alice"
       ^^^^
SyntaxError: invalid syntax
```

**Why:** Python sees `my` as one thing and `name` as another. Variable names cannot have spaces. Fix: use `my_name`.

**Rule 4: Names cannot be Python reserved words.**

Python has words that are already taken for special purposes: `if`, `else`, `for`, `while`, `class`, `def`, `return`, `True`, `False`, `None`, `import`, `and`, `or`, `not`, etc.

```python
class = "math"
```

**Output (error):**

```
  File "test.py", line 1
    class = "math"
          ^
SyntaxError: invalid syntax
```

**Why:** `class` is a reserved word in Python (used to create classes, which you will learn later). Fix: use `class_name` or `subject`.

**Rule 5: Names are case-sensitive.**

```python
Name = "Alice"
name = "Bob"
NAME = "Charlie"

print(Name)
print(name)
print(NAME)
```

**Output:**

```
Alice
Bob
Charlie
```

**Why:** `Name`, `name`, and `NAME` are three completely different variables. Python treats uppercase and lowercase letters as different characters.

### Naming Conventions

These are not rules (Python will not give you an error), but they are standards that all Python programmers follow:

```python
# Good — lowercase with underscores (called "snake_case")
user_name = "Alice"
max_retries = 3
is_active = True

# Bad — works but not standard Python style
userName = "Alice"      # This is "camelCase" — used in JavaScript, not Python
MaxRetries = 3          # This is "PascalCase" — used for class names in Python

# Constants — use ALL_CAPS to signal "do not change this"
MAX_CONNECTIONS = 100
PI = 3.14159
DATABASE_URL = "localhost:5432"
```

#### Use Descriptive Names

Variable names should make the code self-explanatory:

```python
# Bad — meaningless names
a = "/usr/bin"
x = 10
y = "hello"

# Good — descriptive names
binary_path = "/usr/bin"
disk_usage_percent = 80
server_name = "web-01"
log_file_path = "/var/log/nginx.log"
```

#### DevOps Example — Storing Configuration Values

```python
server_ip = "192.168.1.20"
max_connections = 500
environment = "production"

print(f"Connecting to {server_ip} in {environment}")
```

**Output:**

```
Connecting to 192.168.1.20 in production
```

#### Quick Debug Tip

When debugging, print both the value and the type:

```python
print(server_name)
print(type(server_name))
```

This helps catch cases where a variable holds an unexpected type (e.g., a port stored as a string instead of an integer).

### Dynamic Typing — Python Figures Out the Type

In many languages (Java, C, Go), you must declare the type of a variable when you create it. Python does not require this — it figures out the type automatically based on the value you assign:

```python
item = 101
print(type(item))

item = "Code 101"
print(type(item))
```

**Output:**

```
<class 'int'>
<class 'str'>
```

The `type()` function tells you what kind of value a variable currently holds. In the example above, `item` starts as an integer and then becomes a string. Python allows this because it uses **dynamic typing** — the type is attached to the value, not to the variable name.

**Why this is dangerous:**

```python
item = 101
# ... 2000 lines of code later ...
print(item.upper())  # Crashes if item is still an int
```

If someone changes `item` to a number somewhere in between, your code breaks in a place far from where the problem was introduced. This makes debugging very difficult.

> **Rule of thumb:** Never reassign a value of a different type to the same variable. If a variable starts as a string, keep it as a string. If you need a number, use a different variable name.

If you genuinely need a variable that could hold different types (e.g., a function that accepts either a string or a number), make it explicit with type checks:

```python
if isinstance(item, str):
    print(item.upper())
elif isinstance(item, int):
    print(item * 2)
```

### Jupyter Tip — Quick Variable Inspection

When working in Jupyter notebooks or IPython, you can inspect variables quickly:

- **Tab autocomplete:** Type the first few letters of a variable name and press `Tab` to autocomplete.
- **Last-expression display:** In a Jupyter cell, the last expression is automatically displayed without needing `print()`:

```python
# In a Jupyter cell:
name = "Alice"
name  # This line's value is displayed automatically
```

**Output:**

```
'Alice'
```

This is useful for quick inspection during development, but always use `print()` in `.py` scripts.

---

## Strings — Working with Text

Strings are **ordered, immutable sequences of characters**. "Ordered" means each character has a position (index). "Immutable" means you cannot change a string after it is created — operations return new strings instead.

You can use single quotes `'hello'` or double quotes `"hello"` — both work the same way:

```python
single_line_str = "Double quoted"
single_line_str2 = 'Single quoted'
```

Use whichever quote style you prefer, but be consistent. Automated code formatters (like `black`) will normalize your choice across the codebase.

#### Triple-Quoted Strings — Multi-Line Text

Use triple quotes (`"""..."""` or `'''...'''`) for strings that span multiple lines. Whitespace and indentation inside the triple quotes are preserved exactly as written:

```python
command_template = """
I will not be indented
    I will be indented
"""

print(command_template)
```

**Output:**

```

I will not be indented
    I will be indented

```

Notice the blank lines at the start and end — they come from the newlines right after `"""` and before the closing `"""`. The four-space indent on the second line is preserved in the output. This is useful for building multi-line shell commands, SQL queries, or configuration templates.

### What Can You Do with Strings?

#### Finding the Length

```python
message = "Hello"
length = len(message)
print(length)
```

**Output:**

```
5
```

**Why `5`:** The string `"Hello"` has 5 characters: `H`, `e`, `l`, `l`, `o`. The `len()` function counts them.

#### Accessing Individual Characters

Each character in a string has a position number called an **index**. Indexing starts at `0`, not `1`.

```
 H   e   l   l   o
 0   1   2   3   4     ← index from the left
-5  -4  -3  -2  -1     ← index from the right
```

```python
word = "Hello"

print(word[0])
print(word[1])
print(word[4])
print(word[-1])
print(word[-2])
```

**Output:**

```
H
e
o
o
l
```

**Line-by-line explanation:**

- `word[0]` → `H` — Index 0 is the first character.
- `word[1]` → `e` — Index 1 is the second character.
- `word[4]` → `o` — Index 4 is the fifth (last) character.
- `word[-1]` → `o` — Index -1 means "last character." This is a shortcut so you do not need to know the length.
- `word[-2]` → `l` — Index -2 means "second to last."

**What happens if you use an index that does not exist?**

```python
word = "Hello"
print(word[10])
```

**Output (error):**

```
IndexError: string index out of range
```

**Why:** The string only has indices 0 through 4. Index 10 does not exist, so Python raises an error.

#### Slicing — Getting a Portion of a String

Slicing lets you extract a substring. The syntax is `string[start:end]` where `start` is included and `end` is excluded.

```python
text = "Hello, World!"

print(text[0:5])
print(text[7:12])
print(text[:5])
print(text[7:])
```

**Output:**

```
Hello
World
Hello
World!
```

**Line-by-line explanation:**

- `text[0:5]` → `Hello` — Characters at index 0, 1, 2, 3, 4. Index 5 is excluded.
- `text[7:12]` → `World` — Characters at index 7, 8, 9, 10, 11.
- `text[:5]` → `Hello` — When you omit the start, Python assumes 0. Same as `text[0:5]`.
- `text[7:]` → `World!` — When you omit the end, Python goes to the end of the string.

### Combining Strings (Concatenation)

You can join strings together using the `+` operator:

```python
first_name = "Alice"
last_name = "Smith"

full_name = first_name + " " + last_name
print(full_name)
```

**Output:**

```
Alice Smith
```

**What happened:** `first_name + " " + last_name` joins three strings: `"Alice"`, `" "` (a space), and `"Smith"` into one string `"Alice Smith"`.

**What happens if you try to add a string and a number?**

```python
name = "Alice"
age = 30
message = name + " is " + age + " years old"
```

**Output (error):**

```
TypeError: can only concatenate str (not "int") to str
```

**Why:** Python does not automatically convert numbers to strings. You cannot glue a number onto a string with `+`. The fix is to use f-strings (explained next) or convert the number: `str(age)`.

### f-strings — The Best Way to Put Variables Inside Text

f-strings (formatted string literals) let you embed variables directly inside a string by putting `f` before the opening quote and wrapping variables in `{}`:

```python
name = "Alice"
age = 30
city = "New York"

message = f"My name is {name}, I am {age} years old, and I live in {city}."
print(message)
```

**Output:**

```
My name is Alice, I am 30 years old, and I live in New York.
```

**How it works:** The `f` before the quote tells Python "look for `{}` inside this string and replace them with the values of the variables." Python handles the type conversion automatically — `age` is a number, but Python converts it to text inside the f-string.

You can also put expressions (calculations) inside the braces:

```python
price = 49.99
quantity = 3

print(f"Total: ${price * quantity}")
print(f"Total: ${price * quantity:.2f}")
```

**Output:**

```
Total: $149.97
Total: $149.97
```

**Explanation:**

- `{price * quantity}` — Python calculates `49.99 * 3 = 149.97` and puts the result in the string.
- `{price * quantity:.2f}` — The `:.2f` part is a format specifier. It means "show exactly 2 decimal places." For this value it looks the same, but for something like `10 / 3 = 3.333...` it would show `3.33`.

### Useful String Methods

A method is a function that belongs to a string. You call it with a dot: `string.method()`.

```python
text = "Hello, World!"

print(text.upper())
print(text.lower())
print(text.replace("World", "Python"))
print(text.startswith("Hello"))
print(text.endswith("World!"))
print("World" in text)
```

**Output:**

```
HELLO, WORLD!
hello, world!
Hello, Python!
True
True
True
```

**Line-by-line explanation:**

- `.upper()` → `HELLO, WORLD!` — Converts every letter to uppercase. The original `text` is not changed (strings are immutable — more on this below).
- `.lower()` → `hello, world!` — Converts every letter to lowercase.
- `.replace("World", "Python")` → `Hello, Python!` — Finds `"World"` and replaces it with `"Python"`.
- `.startswith("Hello")` → `True` — Checks if the string begins with `"Hello"`. It does, so the result is `True`.
- `.endswith("World!")` → `True` — Checks if the string ends with `"World!"`.
- `"World" in text` → `True` — The `in` operator checks if `"World"` appears anywhere inside `text`.

#### strip() — Removing Extra Whitespace

```python
messy = "   Hello, World!   "
clean = messy.strip()

print(f"Before: '{messy}'")
print(f"After:  '{clean}'")
```

**Output:**

```
Before: '   Hello, World!   '
After:  'Hello, World!'
```

**Why this matters:** Data from files, user input, and APIs often has extra spaces or trailing newlines. `.strip()` removes whitespace from both ends.

You can also strip from only one side:

```python
course_title = "     Python for DevOps    "

print(f"Original:  '{course_title}'")
print(f".strip():  '{course_title.strip()}'")
print(f".lstrip(): '{course_title.lstrip()}'")
print(f".rstrip(): '{course_title.rstrip()}'")
```

**Output:**

```
Original:  '     Python for DevOps    '
.strip():  'Python for DevOps'
.lstrip(): 'Python for DevOps    '
.rstrip(): '     Python for DevOps'
```

- `.lstrip()` removes whitespace from the **left** (start) only.
- `.rstrip()` removes whitespace from the **right** (end) only.

This is useful when processing log lines or command output where trailing whitespace or newlines can interfere with string comparisons.

#### split() — Breaking a String into Parts

```python
sentence = "Python is a great language"
words = sentence.split()
print(words)
```

**Output:**

```
['Python', 'is', 'a', 'great', 'language']
```

**What happened:** `.split()` breaks the string at every space and returns a list of the pieces. You can split on any character:

```python
date = "2024-01-15"
parts = date.split("-")
print(parts)

year = parts[0]
month = parts[1]
day = parts[2]
print(f"Year: {year}, Month: {month}, Day: {day}")
```

**Output:**

```
['2024', '01', '15']
Year: 2024, Month: 01, Day: 15
```

#### join() — Combining a List into a String

`.join()` is the reverse of `.split()`. You call it on the **separator** string and pass the list of parts:

```python
path = "/usr/local/bin"
path_parts = path.split("/")
print(f"path parts: {path_parts}")

# Join with backslash (for Windows-style paths)
print(f"joined path parts: {'\\'.join(path_parts)}")
```

**Output:**

```
path parts: ['', 'usr', 'local', 'bin']
joined path parts: \usr\local\bin
```

Notice the empty first element — that comes from the leading `/` before `usr`. When splitting on `/`, everything before the first `/` becomes an element (which is empty).

> **Escaping backslashes:** In Python strings, `\` is the escape character (e.g., `\n` is a newline). To include a literal backslash, write `\\`. This is why the join separator is `'\\'` — it produces a single `\` in the output.

You can join with any separator:

```python
print("-".join(["dev", "ops", "python"]))
```

**Output:**

```
dev-ops-python
```

**DevOps example — parsing a file path:**

```python
path = "/usr/local/bin"
folder = path.split("/")[1]
print(folder)
```

**Output:**

```
usr
```

Splitting on `/` gives `['', 'usr', 'local', 'bin']`, and index `[1]` picks `'usr'`. This pattern is common in log parsing scripts where you need to extract specific parts of a path.

### Strings Are Immutable

This is an important concept: **you cannot change a string after it is created.** Methods like `.upper()` and `.replace()` do not modify the original string — they create a new one.

```python
name = "Alice"
name.upper()
print(name)
```

**Output:**

```
Alice
```

**Why not `ALICE`?** Because `.upper()` returns a new string but does not change `name`. The new string was not saved anywhere. To keep the result, assign it back:

```python
name = "Alice"
name = name.upper()
print(name)
```

**Output:**

```
ALICE
```

Now `name` points to the new string `"ALICE"`.

You also cannot change individual characters by index:

```python
name = "Alice"
name[0] = "Z"
```

**Output (error):**

```
TypeError: 'str' object does not support item assignment
```

Once a string is created, it cannot be modified in place. You can operate on it and produce new strings, but the original remains unchanged.

---

### Exercise: Calculate Disk Usage Percentage

This exercise combines arithmetic, variables, `.upper()`, and f-string formatting into a single DevOps-relevant task.

**Objectives:**

1. Calculate disk usage percentage from given variables.
2. Print the raw decimal value.
3. Build a human-readable summary string (server name in uppercase, CPU cores, RAM, disk usage).
4. Apply float formatting (`.2f`) and percentage formatting (`.2%`).

**The flow:**

```
Define server variables
        │
        ▼
Calculate disk usage (used / total)
        │
        ▼
Print raw value (0.7)
        │
        ▼
Build summary with f-string
        │
        ▼
Apply formatting → display final output
```

**Given variables:**

```python
server_name = "alpha-server"
cpu_cores = 8
memory_gb = 32
disk_total_gb = 500
disk_used_gb = 350
```

**Step 1 — Calculate and print the raw value:**

```python
disk_usage_percentage = disk_used_gb / disk_total_gb
print(disk_usage_percentage)
```

**Output:**

```
0.7
```

This is the raw decimal — `350 / 500 = 0.7`.

**Step 2 — Build a human-readable summary:**

```python
summary = f"Server '{server_name.upper()}' ({cpu_cores} cores, {memory_gb}GB RAM) - Disk usage: {disk_usage_percentage}"
print(summary)
```

**Output:**

```
Server 'ALPHA-SERVER' (8 cores, 32GB RAM) - Disk usage: 0.7
```

How each part of the f-string works:

| Component | Purpose |
|---|---|
| `f"..."` | Enables string interpolation |
| `{server_name.upper()}` | Converts server name to uppercase |
| `{cpu_cores}` | Displays number of CPU cores |
| `{memory_gb}` | Displays RAM |
| `{disk_usage_percentage}` | Displays raw disk usage value |

**Step 3 — Apply float formatting:**

Python f-strings support format specifiers with the syntax `{value:format}`:

```python
# .2f → two decimal places, float format
summary_2f = f"Server '{server_name.upper()}' ({cpu_cores} cores, {memory_gb}GB RAM) - Disk usage: {disk_usage_percentage:.2f}"
print(summary_2f)

# .2% → two decimal places, percentage format (multiplies by 100 and adds %)
summary_pct = f"Server '{server_name.upper()}' ({cpu_cores} cores, {memory_gb}GB RAM) - Disk usage: {disk_usage_percentage:.2%}"
print(summary_pct)
```

**Output:**

```
Server 'ALPHA-SERVER' (8 cores, 32GB RAM) - Disk usage: 0.70
Server 'ALPHA-SERVER' (8 cores, 32GB RAM) - Disk usage: 70.00%
```

**Formatting comparison:**

| Format | Code | Output |
|---|---|---|
| Raw value | `{disk_usage_percentage}` | `0.7` |
| 2-decimal float | `{disk_usage_percentage:.2f}` | `0.70` |
| Percentage | `{disk_usage_percentage:.2%}` | `70.00%` |

The `.2%` specifier multiplies by 100, adds a `%` sign, and shows two decimal places — all in one step.

**Complete code:**

```python
server_name = "alpha-server"
cpu_cores = 8
memory_gb = 32
disk_total_gb = 500
disk_used_gb = 350

disk_usage_percentage = disk_used_gb / disk_total_gb
print(disk_usage_percentage)

summary = f"Server '{server_name.upper()}' ({cpu_cores} cores, {memory_gb}GB RAM) - Disk usage: {disk_usage_percentage}"
print(summary)

summary_formatted = f"Server '{server_name.upper()}' ({cpu_cores} cores, {memory_gb}GB RAM) - Disk usage: {disk_usage_percentage:.2%}"
print(summary_formatted)
```

**Concepts practiced:**

| Concept | How it was used |
|---|---|
| Arithmetic | `disk_used_gb / disk_total_gb` |
| Variables | Store server name, cores, RAM, disk values |
| f-strings | Build dynamic summary strings |
| `.upper()` | Convert server name to uppercase |
| `.2f` format | Control decimal places |
| `.2%` format | Display as percentage |

**Where this pattern is used in DevOps:**

- Monitoring scripts that check disk/CPU/memory usage
- Server health dashboards
- Cloud resource reporting (AWS, GCP, Azure)
- Infrastructure automation alerts

Example output from a multi-server monitoring script:

```
Server WEB01 disk usage 82.00%
Server WEB02 disk usage 45.00%
Server DB01 disk usage 91.00%
```

---

## Numbers — Integers and Floats

Python has two types of numbers:

- **Integers (`int`)** — Whole numbers without a decimal point: `10`, `-3`, `0`, `1000000`. Python integers have **arbitrary precision** — they can grow as large as your memory allows, with no overflow.
- **Floats (`float`)** — Numbers with a decimal point: `3.14`, `-0.5`, `100.0`. Floats use **IEEE 754** representation internally, which means small precision differences are possible (see below).

Unlike C or Java, Python integers have no upper limit:

```python
big_number = 999999999999999999999999999999999
print(big_number)
```

**Output:**

```
999999999999999999999999999999999
```

This works because Python allocates as much memory as needed for the number.

Adding `.0` to a number changes its type:

```python
print(type(1))    # <class 'int'>
print(type(1.0))  # <class 'float'>
```

### Float Precision — A Common Gotcha

Because floats use IEEE 754 binary representation, some decimal values cannot be stored exactly:

```python
print(0.1 * 3 == 0.3)
```

**Output:**

```
False
```

This is surprising — mathematically `0.1 × 3` is `0.3`. But internally, `0.1` cannot be represented exactly in binary, so `0.1 * 3` produces a tiny rounding error:

```python
print(0.1 * 3)
```

**Output:**

```
0.30000000000000004
```

To compare floats safely, use `math.isclose()` from the standard library:

```python
import math

print(math.isclose(0.1 * 3, 0.3))
```

**Output:**

```
True
```

`math.isclose()` accounts for small precision differences and returns `True` when the values are close enough. This matters in financial calculations, scientific computing, or any code where exact decimal comparison is needed.

### Arithmetic Operations

```python
print(10 + 3)
print(10 - 3)
print(10 * 3)
print(10 / 3)
print(10 // 3)
print(10 % 3)
print(2 ** 10)
```

**Output:**

```
13
7
30
3.3333333333333335
3
1
1024
```

**Line-by-line explanation:**

- `10 + 3` → `13` — Addition.
- `10 - 3` → `7` — Subtraction.
- `10 * 3` → `30` — Multiplication.
- `10 / 3` → `3.3333...` — **Regular division.** This always returns a float, even if the result is a whole number. `10 / 2` gives `5.0`, not `5`.
- `10 // 3` → `3` — **Integer division (floor division).** It divides and rounds down to the nearest whole number. `10 ÷ 3 = 3.33`, rounded down = `3`.
- `10 % 3` → `1` — **Modulo (remainder).** `10 ÷ 3 = 3` with a remainder of `1`. This is useful for checking if a number is even or odd: `number % 2 == 0` means even.
- `2 ** 10` → `1024` — **Exponentiation.** `2` raised to the power of `10`. Same as `2 × 2 × 2 × 2 × 2 × 2 × 2 × 2 × 2 × 2`.

### Why Does Division Always Return a Float?

```python
result = 10 / 2
print(result)
print(type(result))
```

**Output:**

```
5.0
<class 'float'>
```

Even though `10 / 2` is exactly `5`, Python returns `5.0` (a float). This is by design — true division (`/`) can produce decimals, so Python always returns a float to be consistent regardless of the operands.

If you want an integer result, use floor division (`//`):

```python
result = 10 // 2
print(result)
print(type(result))
```

**Output:**

```
5
<class 'int'>
```

### Floor Division — Result Type Depends on Operands

Unlike true division (`/`) which always returns a float, floor division (`//`) returns a type that depends on the operands:

```python
print(5 // 3)      # int // int → int
print(type(5 // 3))

print(5 // 3.0)    # int // float → float
print(type(5 // 3.0))
```

**Output:**

```
1
<class 'int'>
1.0
<class 'float'>
```

Both produce the same mathematical result (the floor of `5 ÷ 3`), but `5 // 3` returns `1` (int) while `5 // 3.0` returns `1.0` (float). If any operand is a float, the result is a float.

### Modulo — Keeping Values in Range

The modulo operator (`%`) returns the remainder after division. A practical use case is keeping an index within bounds:

```python
# Cycling through indices 0, 1, 2 regardless of how large the number gets
for i in range(5, 11):
    print(f"{i} % 3 = {i % 3}")
```

**Output:**

```
5 % 3 = 2
6 % 3 = 0
7 % 3 = 1
8 % 3 = 2
9 % 3 = 0
10 % 3 = 1
```

The result always stays between `0` and `2` — useful when you need to cycle through a list of fixed size.

**DevOps example — round-robin load balancing:**

```python
servers = ["web1", "web2", "web3"]

for i in range(6):
    print(servers[i % 3])
```

**Output:**

```
web1
web2
web3
web1
web2
web3
```

The modulo operator ensures the index wraps around, cycling through the server list regardless of how many requests come in.

### Type Checking and Conversion

Every value in Python has a type. You can check it with `type()`:

```python
print(type(42))
print(type(3.14))
print(type("hello"))
print(type(True))
```

**Output:**

```
<class 'int'>
<class 'float'>
<class 'str'>
<class 'bool'>
```

You can convert between types:

```python
# String to integer
age_text = "25"
age_number = int(age_text)
print(age_number + 5)
```

**Output:**

```
30
```

**What happened:** `age_text` is the string `"25"` (text, not a number). `int("25")` converts it to the integer `25`. Now you can do math with it: `25 + 5 = 30`.

**What happens if the string is not a valid number?**

```python
result = int("hello")
```

**Output (error):**

```
ValueError: invalid literal for int() with base 10: 'hello'
```

**Why:** Python cannot convert `"hello"` to a number because it is not a number. You can only convert strings that look like numbers: `"42"`, `"-7"`, `"100"`.

More conversions:

```python
# Integer to string
count = 42
count_text = str(count)
print("Count: " + count_text)

# Integer to float
whole = 10
decimal = float(whole)
print(decimal)

# Float to integer (drops the decimal part — does NOT round)
price = 19.99
whole_price = int(price)
print(whole_price)
```

**Output:**

```
Count: 42
10.0
19
```

**Important:** `int(19.99)` gives `19`, not `20`. It chops off the decimal part. It does not round. If you want rounding, use `round(19.99)` which gives `20`.

---

## Booleans — True and False

A boolean is a value that is either `True` or `False`. Booleans are the foundation of all decision-making in programming.

```python
is_sunny = True
is_raining = False

print(is_sunny)
print(is_raining)
```

**Output:**

```
True
False
```

> **Note:** `True` and `False` must be capitalized. `true` and `false` (lowercase) will cause a `NameError`.

### Comparison Operators — Producing Booleans

Comparisons always produce a boolean result:

```python
print(10 > 5)
print(10 < 5)
print(10 == 10)
print(10 != 5)
print(10 >= 10)
print(10 <= 5)
```

**Output:**

```
True
False
True
True
True
False
```

**Line-by-line explanation:**

- `10 > 5` → `True` — "Is 10 greater than 5?" Yes.
- `10 < 5` → `False` — "Is 10 less than 5?" No.
- `10 == 10` → `True` — "Is 10 equal to 10?" Yes. Note: `==` is comparison (two equals signs). `=` is assignment (one equals sign). Mixing them up is a common mistake.
- `10 != 5` → `True` — "Is 10 not equal to 5?" Yes, they are different.
- `10 >= 10` → `True` — "Is 10 greater than or equal to 10?" Yes (it is equal).
- `10 <= 5` → `False` — "Is 10 less than or equal to 5?" No.

### Combining Booleans — and, or, not

```python
age = 25
has_license = True

print(age >= 18 and has_license)
print(age >= 18 and not has_license)
print(age < 18 or has_license)
```

**Output:**

```
True
False
True
```

**Line-by-line explanation:**

- `age >= 18 and has_license` → `True and True` → `True` — Both conditions must be true for `and` to produce `True`.
- `age >= 18 and not has_license` → `True and not True` → `True and False` → `False` — `not` flips `True` to `False`.
- `age < 18 or has_license` → `False or True` → `True` — At least one condition must be true for `or` to produce `True`.

**Truth table for reference:**

| A | B | A and B | A or B | not A |
|---|---|---------|--------|-------|
| True | True | True | True | False |
| True | False | False | True | False |
| False | True | False | True | True |
| False | False | False | False | True |

### None — The Absence of a Value

`None` is a special value that means "nothing" or "no value." It is not the same as `0`, `""` (empty string), or `False`.

```python
result = None
print(result)
print(type(result))
```

**Output:**

```
None
<class 'NoneType'>
```

**When is None useful?** When a variable exists but does not have a meaningful value yet:

```python
middle_name = None

if middle_name is None:
    print("No middle name provided")
else:
    print(f"Middle name: {middle_name}")
```

**Output:**

```
No middle name provided
```

**Important:** Use `is None` to check for None, not `== None`. The `is` keyword checks identity (is this the exact same object?), which is the correct way to check for None.

---

## Lists — Ordered Collections

A list is an **ordered, mutable sequence** defined with square brackets `[]`. You can add, remove, or change items after creation.

Two key characteristics point towards using a list:

1. **Order matters** — items maintain their position (unless you explicitly insert or remove).
2. **Contents change** — you need to add, remove, or update elements over time.

Examples: a list of servers, deployment steps, log entries, availability zones.

### Creating a List

```python
servers = ["web01", "web02", "web03"]
print(servers)
```

**Output:**

```
['web01', 'web02', 'web03']
```

A list is created with square brackets `[]` and items separated by commas.

#### Mixed Types — Possible but Not Recommended

Lists can hold any type of value, and even mix types:

```python
mixed_list = ["config.yaml", 8080, True]

for item in mixed_list:
    print(type(item))
```

**Output:**

```
<class 'str'>
<class 'int'>
<class 'bool'>
```

Python does not complain, but mixing types makes it hard to reason about the code — you do not know whether you are dealing with a string, a number, or a boolean when you pull an item from the list. Keep list elements the same type unless you have a very good reason not to.

```python
numbers = [10, 20, 30, 40, 50]
empty = []

print(numbers)
print(empty)
```

**Output:**

```
[10, 20, 30, 40, 50]
[]
```

### Accessing Elements

Like strings, list elements are accessed by index, starting at 0:

```
 "apple"  "banana"  "cherry"
    0         1         2       ← index from left
   -3        -2        -1      ← index from right
```

```python
fruits = ["apple", "banana", "cherry"]

print(fruits[0])
print(fruits[1])
print(fruits[2])
print(fruits[-1])
```

**Output:**

```
apple
banana
cherry
cherry
```

**Explanation:**

- `fruits[0]` → `apple` — First element.
- `fruits[1]` → `banana` — Second element.
- `fruits[2]` → `cherry` — Third element.
- `fruits[-1]` → `cherry` — Last element (shortcut).

Using negative indices:

```python
servers = ["web01", "web02", "web03"]
print(servers[-1])   # Last item
print(servers[-2])   # Second to last
```

**Output:**

```
web03
web02
```

**What happens with an invalid index?**

```python
servers = ["web01", "web02", "web03"]
# print(servers[3])  # Will raise an IndexError exception
```

```
IndexError: list index out of range
```

This happens often when you do not know the list length in advance. For example, AWS regions have different numbers of availability zones — some have three, others have six. If you hardcode an index like `zones[5]` and the region only has three zones, you get an `IndexError`. Always check the list length or use safer access patterns.

### Slicing a List

Works the same as string slicing — `list[start:stop]` where `start` is included and `stop` is excluded:

```python
servers = ["web01", "web02", "web03"]

print(servers[:2])    # Elements at indexes 0 and 1
print(servers[1:])    # Elements at indexes 1 and 2
print(servers[-2:])   # Second to last and last elements
```

**Output:**

```
['web01', 'web02']
['web02', 'web03']
['web02', 'web03']
```

**Explanation:**

- `servers[:2]` → From the beginning up to (not including) index 2.
- `servers[1:]` → From index 1 to the end. The start index **is** included.
- `servers[-2:]` → The last two elements. Useful when you always want the tail regardless of list length.

You can also use a third parameter — the **step** — to select every Nth element:

```python
numbers = [10, 20, 30, 40, 50, 60]

print(numbers[::2])   # Every other element
print(numbers[1::2])  # Every other element, starting from index 1
```

**Output:**

```
[10, 30, 50]
[20, 40, 60]
```

**Slicing does not alter the original list** — it returns a new list:

```python
servers = ["web01", "web02", "web03"]
first_two = servers[:2]
print(first_two)
print(servers)  # Still has all 3 elements
```

**Output:**

```
['web01', 'web02']
['web01', 'web02', 'web03']
```

### Modifying Lists

Unlike strings, lists **are mutable** — you can change them after creation.

#### Changing an Element

```python
colors = ["red", "green", "blue"]
print(colors)

colors[1] = "yellow"
print(colors)
```

**Output:**

```
['red', 'green', 'blue']
['red', 'yellow', 'blue']
```

**What happened:** `colors[1] = "yellow"` replaced the element at index 1 (`"green"`) with `"yellow"`.

#### Adding Elements

```python
fruits = ["apple", "banana"]

fruits.append("cherry")
print(fruits)

fruits.insert(1, "orange")
print(fruits)
```

**Output:**

```
['apple', 'banana', 'cherry']
['apple', 'orange', 'banana', 'cherry']
```

**Explanation:**

- `.append("cherry")` adds `"cherry"` to the **end** of the list.
- `.insert(1, "orange")` inserts `"orange"` at index 1, pushing everything after it one position to the right. So `"banana"` moves from index 1 to index 2.

#### Removing Elements

```python
ports = [80, 443, 8080, 5000]

ports.remove(80)
print(ports)

removed_value = ports.pop(2)
print(ports)
print(f"Removed: {removed_value}")

last = ports.pop()
print(f"Removed last: {last}")
print(ports)
```

**Output:**

```
[443, 8080, 5000]
[443, 8080]
Removed: 5000
Removed last: 8080
[443]
```

**Explanation:**

- `.remove(80)` finds and removes the first occurrence of `80`. If the value does not exist, it raises a `ValueError`.
- `.pop(2)` removes and **returns** the element at index 2 (`5000`). You can use the returned value.
- `.pop()` with no argument removes and returns the **last** element.
- `del ports[0]` (not shown above) deletes the element at a specific index without returning it.

#### Mutation Side-Effects — Lists Are Shared by Reference

When you pass a list to a function, the function receives a reference to the **same** list, not a copy. Changes inside the function affect the original:

```python
def mutate_list(l):
    l.pop()

new_list = ["a", "b", "c"]
mutate_list(new_list)
print(new_list)
```

**Output:**

```
['a', 'b']
```

The function removed `"c"` from the original list. This is a common source of bugs — if you do not want the original modified, pass a copy: `mutate_list(new_list.copy())`.

### Useful List Operations

```python
numbers = [3, 1, 4, 1, 5, 9, 2, 6]

print(len(numbers))
print(min(numbers))
print(max(numbers))
print(sum(numbers))
print(sorted(numbers))
print(numbers)
```

**Output:**

```
8
1
9
31
[1, 1, 2, 3, 4, 5, 6, 9]
[3, 1, 4, 1, 5, 9, 2, 6]
```

**Explanation:**

- `len(numbers)` → `8` — The list has 8 elements.
- `min(numbers)` → `1` — The smallest value.
- `max(numbers)` → `9` — The largest value.
- `sum(numbers)` → `31` — The total of all values added together.
- `sorted(numbers)` → `[1, 1, 2, 3, 4, 5, 6, 9]` — Returns a **new** sorted list. The original list is not changed.
- `numbers` → `[3, 1, 4, 1, 5, 9, 2, 6]` — Still the original order. `sorted()` did not modify it.

If you want to sort the list itself (modify it in place), use `.sort()`:

```python
numbers = [3, 1, 4, 1, 5]
numbers.sort()
print(numbers)
```

**Output:**

```
[1, 1, 3, 4, 5]
```

### Checking if an Item Exists

```python
fruits = ["apple", "banana", "cherry"]

print("banana" in fruits)
print("grape" in fruits)
```

**Output:**

```
True
False
```

**Explanation:** The `in` operator checks if a value exists in the list. `"banana"` is in the list, so it returns `True`. `"grape"` is not, so it returns `False`.

### Looping Through a List

```python
fruits = ["apple", "banana", "cherry"]

for fruit in fruits:
    print(f"I like {fruit}")
```

**Output:**

```
I like apple
I like banana
I like cherry
```

**How it works:** The `for` loop takes each element from the list one at a time, assigns it to the variable `fruit`, and runs the indented code. First `fruit` is `"apple"`, then `"banana"`, then `"cherry"`.

If you need the index along with the value, use `enumerate()`:

```python
fruits = ["apple", "banana", "cherry"]

for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")
```

**Output:**

```
0: apple
1: banana
2: cherry
```

**How it works:** `enumerate()` gives you both the index and the value on each iteration. `index` gets `0, 1, 2` and `fruit` gets `"apple", "banana", "cherry"`.

### Exercise: Deployment Targets

Practice creating, accessing, appending, and modifying a list:

```python
# 1. Create a list of deployment targets
deployment_targets = ["us-east-1", "eu-west-1", "ap-southeast-2"]

# 2. Print the first target
print(deployment_targets[0])

# 3. Append a new region
deployment_targets.append("us-west-2")
print(deployment_targets)

# 4. Change the second element
deployment_targets[1] = "eu-central-1"
print(deployment_targets)
```

**Output:**

```
us-east-1
['us-east-1', 'eu-west-1', 'ap-southeast-2', 'us-west-2']
['us-east-1', 'eu-central-1', 'ap-southeast-2', 'us-west-2']
```

---

## Dictionaries — Key-Value Pairs

A dictionary stores data as **key-value pairs**. Think of a real dictionary: you look up a word (the key) to find its definition (the value).

### Creating a Dictionary

```python
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

print(person)
```

**Output:**

```
{'name': 'Alice', 'age': 30, 'city': 'New York'}
```

A dictionary is created with curly braces `{}`. Each entry has a **key** (like `"name"`) followed by a colon `:` and a **value** (like `"Alice"`). Entries are separated by commas.

### Accessing Values

You access values by their key, not by index:

```python
person = {"name": "Alice", "age": 30, "city": "New York"}

print(person["name"])
print(person["age"])
```

**Output:**

```
Alice
30
```

**What happens if the key does not exist?**

```python
person = {"name": "Alice", "age": 30}
print(person["email"])
```

**Output (error):**

```
KeyError: 'email'
```

**Why:** The key `"email"` does not exist in the dictionary. Python raises a `KeyError`.

**Safe access with `.get()`:**

```python
person = {"name": "Alice", "age": 30}

print(person.get("email"))
print(person.get("email", "not provided"))
print(person.get("name"))
```

**Output:**

```
None
not provided
Alice
```

**Explanation:**

- `.get("email")` → `None` — The key does not exist, so `.get()` returns `None` instead of raising an error.
- `.get("email", "not provided")` → `"not provided"` — You can specify a default value to return when the key is missing.
- `.get("name")` → `"Alice"` — The key exists, so it returns the value normally.

### Adding and Changing Values

```python
person = {"name": "Alice", "age": 30}
print(person)

# Add a new key
person["email"] = "alice@example.com"
print(person)

# Change an existing key
person["age"] = 31
print(person)
```

**Output:**

```
{'name': 'Alice', 'age': 30}
{'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}
{'name': 'Alice', 'age': 31, 'email': 'alice@example.com'}
```

**Explanation:**

- `person["email"] = "alice@example.com"` — The key `"email"` does not exist, so Python creates it.
- `person["age"] = 31` — The key `"age"` already exists, so Python updates its value from `30` to `31`.

The syntax is the same for adding and updating. Python decides based on whether the key already exists.

### Removing Values

```python
person = {"name": "Alice", "age": 30, "city": "New York"}

del person["city"]
print(person)
```

**Output:**

```
{'name': 'Alice', 'age': 30}
```

**What happened:** `del person["city"]` removes the key `"city"` and its value from the dictionary.

### Checking if a Key Exists

```python
person = {"name": "Alice", "age": 30}

print("name" in person)
print("email" in person)
```

**Output:**

```
True
False
```

**Explanation:** The `in` operator checks if a **key** exists in the dictionary (not a value). `"name"` is a key, so `True`. `"email"` is not a key, so `False`.

### Looping Through a Dictionary

```python
person = {"name": "Alice", "age": 30, "city": "New York"}

# Loop through keys only
print("Keys:")
for key in person:
    print(f"  {key}")

# Loop through values only
print("\nValues:")
for value in person.values():
    print(f"  {value}")

# Loop through both keys and values
print("\nKey-Value Pairs:")
for key, value in person.items():
    print(f"  {key}: {value}")
```

**Output:**

```
Keys:
  name
  age
  city

Values:
  Alice
  30
  New York

Key-Value Pairs:
  name: Alice
  age: 30
  city: New York
```

**Explanation:**

- `for key in person` — By default, looping over a dictionary gives you the keys.
- `for value in person.values()` — `.values()` gives you only the values.
- `for key, value in person.items()` — `.items()` gives you both the key and value as a pair on each iteration.

### Nested Dictionaries

A dictionary can contain other dictionaries. This is how you represent structured data:

```python
students = {
    "alice": {
        "age": 20,
        "grade": "A",
        "subjects": ["math", "science"]
    },
    "bob": {
        "age": 22,
        "grade": "B",
        "subjects": ["english", "history"]
    }
}

# Access nested values
print(students["alice"]["grade"])
print(students["bob"]["subjects"][0])
print(students["alice"]["age"])
```

**Output:**

```
A
english
20
```

**Explanation:**

- `students["alice"]` gives you Alice's dictionary: `{"age": 20, "grade": "A", "subjects": [...]}`.
- `students["alice"]["grade"]` goes one level deeper and gets `"A"`.
- `students["bob"]["subjects"][0]` gets Bob's subjects list `["english", "history"]`, then gets the first element `"english"`.
- `students["alice"]["age"]` gets `20`.

### Practical Example: Contact Book

```python
contacts = {}

# Add contacts
contacts["Alice"] = {"phone": "555-0101", "email": "alice@example.com"}
contacts["Bob"] = {"phone": "555-0102", "email": "bob@example.com"}
contacts["Charlie"] = {"phone": "555-0103", "email": "charlie@example.com"}

# Look up a contact
name = "Bob"
if name in contacts:
    info = contacts[name]
    print(f"Name:  {name}")
    print(f"Phone: {info['phone']}")
    print(f"Email: {info['email']}")
else:
    print(f"{name} not found")

# List all contacts
print("\nAll Contacts:")
for name, info in contacts.items():
    print(f"  {name}: {info['phone']}")
```

**Output:**

```
Name:  Bob
Phone: 555-0102
Email: bob@example.com

All Contacts:
  Alice: 555-0101
  Bob: 555-0102
  Charlie: 555-0103
```

---

## Tuples — Immutable Sequences

A tuple is an **ordered, immutable sequence** defined with parentheses `()`. Once created, you cannot add, remove, or change items. This is useful for fixed records like coordinates, version numbers, or host-port pairs where the position of each item has meaning.

**List vs Tuple:**

| Feature | List | Tuple |
|---|---|---|
| Ordered | Yes | Yes |
| Mutable | Yes | No |
| Syntax | `[]` | `()` |
| Performance | Slightly slower | Slightly faster |
| Use case | Dynamic data | Fixed records |

Tuples are slightly faster than lists because Python can optimize immutable objects internally. Use tuples when the data should never change.

**Common tuple use cases:**

| Use Case | Example |
|---|---|
| Coordinates | `(x, y)` |
| RGB colors | `(255, 0, 0)` |
| Version numbers | `(1, 2, 5)` |
| Host + port | `("127.0.0.1", 3000)` |

```python
host_port = ("127.0.0.1", 3000)
red_rgb = (255, 0, 0)

print(host_port)
print(type(host_port))
```

**Output:**

```
(127.0.0.1, 3000)
<class 'tuple'>
```

In a tuple, each position has meaning:

```
red_rgb = (255, 0, 0)

        +-------+-------+-------+
Index → |   0   |   1   |   2   |
        +-------+-------+-------+
Value → |  255  |   0   |   0   |
        +-------+-------+-------+
Meaning →  Red    Green    Blue
```

#### Single-Item Tuples — The Trailing Comma

To create a tuple with a single value, you must add a trailing comma. Without it, Python treats the parentheses as a grouping expression:

```python
not_a_tuple = ("only-value")
print(type(not_a_tuple))

actual_tuple = ("only-value",)   # trailing comma makes it a tuple
print(type(actual_tuple))
```

**Output:**

```
<class 'str'>
<class 'tuple'>
```

### Accessing Elements and Slicing

Works exactly like lists — index with `[]`, slice with `[start:stop]`:

```python
host_port = ("127.0.0.1", 3000)

print(f"Host: {host_port[0]}")
print(f"Port: {host_port[1]}")
```

**Output:**

```
Host: 127.0.0.1
Port: 3000
```

Slicing a tuple returns a tuple:

```python
red_rgb = (255, 0, 0)

print(red_rgb[-2:])
print(type(red_rgb[-2:]))
```

**Output:**

```
(0, 0)
<class 'tuple'>
```

### Why Can't You Change a Tuple?

```python
host_port = ("127.0.0.1", 3000)
# host_port[0] = "192.168.1.1"  # Uncommenting will raise a TypeError because tuples are immutable
```

```
TypeError: 'tuple' object does not support item assignment
```

Tuples are immutable by design — this protects data that should not change, like configuration constants or fixed records.

### Tuple Unpacking

You can assign each element of a tuple to a separate variable in one line:

```python
coordinates = (10, 20)
x, y = coordinates

print(f"x = {x}")
print(f"y = {y}")
```

**Output:**

```
x = 10
y = 20
```

**How it works:** Python takes the tuple `(10, 20)` and assigns `10` to `x` and `20` to `y`. The number of variables on the left must match the number of elements in the tuple.

**What happens if the count does not match?**

```python
coordinates = (10, 20, 30)
x, y = coordinates
```

**Output (error):**

```
ValueError: too many values to unpack (expected 2)
```

### When to Use Tuples vs Lists

- Use a **list** when the data may change (adding items, removing items, sorting).
- Use a **tuple** when the data should stay fixed (coordinates, RGB colors, database rows, function return values).

```python
# List — items may change
shopping_list = ["milk", "eggs", "bread"]
shopping_list.append("butter")    # This works

# Tuple — data is fixed
screen_resolution = (1920, 1080)
# screen_resolution[0] = 2560    # This would cause an error
```

### Tuple Quick Reference

| Operation | Syntax | Notes |
|---|---|---|
| Create | `t = (1, 2, 3)` | Use parentheses |
| Single item | `t = (1,)` | Trailing comma required |
| Index | `t[0]` | 0-based, same as lists |
| Slice | `t[1:3]` | Returns a tuple |
| Modify | Not allowed | `TypeError` on assignment |

### Exercise: Service Endpoint

Practice creating and accessing a tuple:

```python
# 1. Create a tuple with hostname and port
service_endpoint = ("auth-server.dev.local", 80)

# 2. Print the hostname and port
print(f"Hostname: {service_endpoint[0]}")
print(f"Port: {service_endpoint[1]}")

# 3. Attempt to modify — this would raise a TypeError
# service_endpoint[1] = 443  # Uncommenting will raise a TypeError because tuples are immutable
```

**Output:**

```
Hostname: auth-server.dev.local
Port: 80
```

---

## Sets — Unique Collections

A set is an **unordered, mutable collection** that contains only **unique items**. Duplicates are automatically removed. Sets are useful for membership testing, removing duplicates, and performing set operations (union, intersection, difference).

**Creating sets** — two ways:

```python
# Using curly braces
server_names = {"web01", "web02"}

# Using the set() constructor on a list (removes duplicates)
unique_ports = set([80, 443, 22, 80, 8080, 443])
print(unique_ports)
```

**Output:**

```
{80, 443, 8080, 22}
```

The duplicate `80` and `443` were removed. Notice the order may differ from what you typed — sets are **unordered** and do not preserve insertion order.

#### Set Items Must Be Immutable

The items inside a set must be immutable (hashable). This means you can have sets of strings, numbers, and tuples — but **not** sets of lists or sets of sets:

```python
# set_of_lists = set([[1, 2], [3, 4]])  # TypeError: unhashable type: 'list'
# set_of_sets = {{1, 2}, {3, 4}}        # TypeError: unhashable type: 'set'

set_of_tuples = {(1, 2), (3, 4)}        # Works — tuples are immutable
print(set_of_tuples)
print((1, 2) in set_of_tuples)
print((1, 3) in set_of_tuples)
```

**Output:**

```
{(1, 2), (3, 4)}
True
False
```

### Adding and Removing

```python
unique_ports = set([80, 443, 22, 8080])

unique_ports.add(3000)
print(unique_ports)

unique_ports.remove(22)
print(unique_ports)

# unique_ports.remove(22)  # Will raise KeyError because 22 is not in the set anymore

unique_ports.discard(22)   # Safe — does nothing if item is not present
print(unique_ports)
```

**Output:**

```
{80, 3000, 443, 8080, 22}
{80, 3000, 443, 8080}
{80, 3000, 443, 8080}
```

- `.add()` adds an item to the set.
- `.remove()` removes an item but **raises `KeyError`** if the item does not exist.
- `.discard()` removes an item but **does nothing** if the item does not exist — the safer option.

### Checking Membership

Checking if an item is in a set is **very fast** — much faster than checking a list:

```python
unique_ports = set([80, 443, 22, 8080])
server_names = {"web01", "web02"}

print(22 in unique_ports)
print(22 in server_names)
```

**Output:**

```
True
False
```

### Set Operations — Comparing Groups

Sets support mathematical operations for comparing groups. You can use either method syntax or operator syntax:

```python
developers = set(["alice", "bob", "charlie"])
admins = set(["alice", "david"])

# Membership
print("alice" in developers)
print("alice" in admins)

# Union — all unique items from both sets
print("Union:", developers.union(admins))
print("Union:", developers | admins)

# Intersection — items in both sets
print("Intersection:", developers.intersection(admins))
print("Intersection:", developers & admins)

# Difference — items in first set but not in second
print("Difference:", developers.difference(admins))
print("Difference:", developers - admins)
```

**Output:**

```
True
True
Union: {'alice', 'bob', 'charlie', 'david'}
Union: {'alice', 'bob', 'charlie', 'david'}
Intersection: {'alice'}
Intersection: {'alice'}
Difference: {'bob', 'charlie'}
Difference: {'bob', 'charlie'}
```

**Summary of operators:**

| Operation | Method | Operator | Result |
|---|---|---|---|
| Union | `.union(other)` | `\|` | All unique items from both sets |
| Intersection | `.intersection(other)` | `&` | Items in both sets |
| Difference | `.difference(other)` | `-` | Items in first set but not in second |

### Practical Example: Removing Duplicates

A common use of `set()` is to deduplicate a list:

```python
names = ["Alice", "Bob", "Alice", "Charlie", "Bob", "Alice"]

unique_names = set(names)
print(f"All names: {names}")
print(f"Unique names: {unique_names}")
print(f"Total: {len(names)}, Unique: {len(unique_names)}")
```

**Output:**

```
All names: ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob', 'Alice']
Unique names: {'Bob', 'Alice', 'Charlie'}
Total: 6, Unique: 3
```

Instead of iterating through a list with a `for` loop to check for duplicates, just call `set()` on the list.

### Exercise: Required vs Installed Packages

Practice creating sets, testing membership, and computing differences:

```python
# 1. Create a set with duplicates — duplicates are removed automatically
required_packages = set(["python3", "pip", "requests", "boto3", "pip"])
print(required_packages)

# 2. Test membership
print(f"Is 'requests' required? {'requests' in required_packages}")
print(f"Is 'ansible' required? {'ansible' in required_packages}")

# 3. Add and safely remove
required_packages.add("paramiko")
required_packages.discard("pip")
print(required_packages)

# 4. Compare with installed packages
installed_packages = {"docker", "python3", "pip"}
missing_packages = required_packages - installed_packages
extra_packages = installed_packages - required_packages
common_packages = required_packages & installed_packages

print(f"Missing packages: {missing_packages}")
print(f"Extra packages: {extra_packages}")
print(f"Common packages: {common_packages}")
```

**Output:**

```
{'python3', 'pip', 'requests', 'boto3'}
Is 'requests' required? True
Is 'ansible' required? False
{'python3', 'requests', 'boto3', 'paramiko'}
Missing packages: {'boto3', 'requests', 'paramiko'}
Extra packages: {'pip', 'docker'}
Common packages: {'python3'}
```

---

## Quick Reference — When to Use What

| Type | Syntax | Ordered? | Mutable? | Duplicates? | Items Must Be |
|------|--------|----------|----------|-------------|---------------|
| List | `[1, 2, 3]` | Yes | Yes | Yes | Any type |
| Tuple | `(1, 2, 3)` | Yes | No | Yes | Any type |
| Set | `{1, 2, 3}` | No | Yes (set itself) | No | Immutable |
| Dictionary | `{"a": 1}` | Yes* | Yes | Keys: No | Keys: Immutable |

*Dictionaries preserve insertion order in Python 3.7+.

**When to use each:**

| Collection | Use when... | Examples |
|---|---|---|
| **List** | You need an editable, position-aware sequence | Ordered deployment steps, log lines, file reads, task queues |
| **Tuple** | Data is fixed and positional | Host-port pairs, RGB colors, multiple return values from a function |
| **Set** | You need to deduplicate or check membership | Unique IP addresses from access logs, allowed ports whitelist, unique user IDs |
| **Dictionary** | You need to look up values by name | Server config, environment variables, API responses |

---

## Applying This to DevOps — A Preview

Now that you understand the data types, here is how they map to DevOps concepts. You will use these patterns throughout the later modules. You do not need to memorize them now — just see how the same building blocks apply.

**A server represented as a dictionary:**

```python
server = {
    "hostname": "web-prod-01",
    "ip": "10.0.1.50",
    "port": 8080,
    "region": "us-east-1",
    "healthy": True
}

print(f"Server: {server['hostname']}")
print(f"IP: {server['ip']}")
print(f"Healthy: {server['healthy']}")
```

**Output:**

```
Server: web-prod-01
IP: 10.0.1.50
Healthy: True
```

**A list of servers, filtered by name prefix:**

```python
servers = ["web-01", "web-02", "web-03", "api-01", "api-02"]

web_servers = [s for s in servers if s.startswith("web-")]
print(f"Web servers: {web_servers}")
```

**Output:**

```
Web servers: ['web-01', 'web-02', 'web-03']
```

**Sets for finding monitoring gaps:**

```python
prod_servers = {"web-01", "web-02", "api-01", "db-01"}
monitored_servers = {"web-01", "api-01", "cache-01"}

not_monitored = prod_servers - monitored_servers
print(f"Not monitored: {not_monitored}")

stale_monitoring = monitored_servers - prod_servers
print(f"Stale monitoring: {stale_monitoring}")
```

**Output:**

```
Not monitored: {'db-01', 'web-02'}
Stale monitoring: {'cache-01'}
```

---

## Exercises

**Exercise 1: Variables and Strings**

Create a file `profile.py` that stores your name, age, and favorite programming language in variables, then prints a sentence using an f-string.

Expected output (with your own values):

```
My name is Alex, I am 28 years old, and I love Python.
```

**Exercise 2: Lists**

Create a list of 5 cities you want to visit. Then:
1. Print the list.
2. Add a 6th city using `.append()`.
3. Remove the 2nd city using `.remove()`.
4. Print the final list and its length.

**Exercise 3: Dictionaries**

Create a dictionary for a book with keys: `title`, `author`, `year`, `pages`. Then:
1. Print each value on its own line.
2. Add a new key `genre`.
3. Change the `pages` value.
4. Print the final dictionary.

**Exercise 4: Sets**

Given two lists of numbers, find which numbers appear in both lists:

```python
list_a = [1, 2, 3, 4, 5, 6]
list_b = [4, 5, 6, 7, 8, 9]

common = set(list_a) & set(list_b)
print(f"Common numbers: {common}")
```

Run it and verify the output is `{4, 5, 6}`.

**Exercise 5: Type Conversion**

What does this code print? Try to predict the output before running it:

```python
a = "10"
b = "20"
print(a + b)
print(int(a) + int(b))
```

---

## Common Mistakes

### Mistake 1: Confusing `=` and `==`

```python
x = 5       # This ASSIGNS the value 5 to x
x == 5      # This CHECKS if x equals 5 (returns True or False)
```

If you write `if x = 5:` instead of `if x == 5:`, Python will give you a `SyntaxError`.

### Mistake 2: Index Out of Range

```python
fruits = ["apple", "banana", "cherry"]
print(fruits[3])    # IndexError! Valid indices are 0, 1, 2
```

A list with 3 items has indices 0, 1, 2. Index 3 does not exist.

### Mistake 3: Forgetting That Strings Are Immutable

```python
name = "alice"
name.upper()        # This does NOT change name
print(name)         # Still prints: alice

name = name.upper() # This saves the result back
print(name)         # Now prints: ALICE
```

### Mistake 4: Using a List Method on a String (or Vice Versa)

```python
name = "Alice"
name.append("!")    # AttributeError! Strings do not have .append()
```

`.append()` is a list method. Strings use `+` for concatenation: `name = name + "!"`.

### Mistake 5: Modifying a Dictionary While Looping Over It

```python
data = {"a": 1, "b": 2, "c": 3}

# This causes RuntimeError:
for key in data:
    if data[key] < 3:
        del data[key]    # Cannot delete while looping!

# Fix: loop over a copy of the keys
for key in list(data.keys()):
    if data[key] < 3:
        del data[key]    # Safe — looping over a separate list
```

---

[Previous: Module 02 — Setting up Python Environment](02-setting-up-python-environment.md) | [Next: Module 04 — Control Flow](04-control-flow.md)
