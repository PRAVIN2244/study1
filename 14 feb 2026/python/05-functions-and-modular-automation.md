# Module 5 — Functions and Modular Automation

A function is a reusable block of code that performs a specific task. Instead of writing the same code over and over, you write it once inside a function and call it whenever you need it.

---

## Defining and Calling a Function

```python
def greet():
    print("Hello!")
    print("Welcome to Python.")
```

**What this does:** The `def` keyword defines a function named `greet`. The two `print` lines are the function's **body** — they are indented under `def`, just like code under `if`. At this point, nothing is printed. The function is defined but not yet called.

```python
def greet():
    print("Hello!")
    print("Welcome to Python.")

greet()
greet()
```

**Output:**

```
Hello!
Welcome to Python.
Hello!
Welcome to Python.
```

**Why:** `greet()` calls the function — Python jumps to the function body, runs both `print` lines, then returns to where it was called. Calling it twice runs the body twice.

### Rule: Define Before You Call

```python
greet()

def greet():
    print("Hello!")
```

**Error:**

```
NameError: name 'greet' is not defined
```

**Why:** Python reads top to bottom. When it hits `greet()`, it has not seen the `def greet():` line yet. Always define functions before calling them.

### Rule: The Parentheses Are Required

```python
def greet():
    print("Hello!")

greet     # No parentheses
```

**Output:** Nothing happens. No error, no output.

**Why:** `greet` without `()` refers to the function object itself — it does not call it. You must write `greet()` to actually run the function.

---

## Functions with Parameters

Parameters let you pass data into a function so it can work with different values each time:

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")
greet("Bob")
```

**Output:**

```
Hello, Alice!
Hello, Bob!
```

**How this works:**

1. `greet("Alice")` — Python assigns `name = "Alice"` inside the function, then runs the body
2. `greet("Bob")` — Python assigns `name = "Bob"` inside the function, then runs the body

The value you pass in (`"Alice"`) is called an **argument**. The variable that receives it (`name`) is called a **parameter**.

### Multiple Parameters

```python
def add(a, b):
    result = a + b
    print(f"{a} + {b} = {result}")

add(3, 5)
add(10, 20)
```

**Output:**

```
3 + 5 = 8
10 + 20 = 30
```

**What happens if you pass the wrong number of arguments:**

```python
def add(a, b):
    print(a + b)

add(3)
```

**Error:**

```
TypeError: add() missing 1 required positional argument: 'b'
```

**Why:** The function expects 2 arguments but got 1. Python tells you exactly which argument is missing.

### Default Parameters

You can give parameters default values. If the caller does not provide a value, the default is used:

```python
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}!")

greet("Alice")
greet("Bob", "Good morning")
greet("Charlie", "Hey")
```

**Output:**

```
Hello, Alice!
Good morning, Bob!
Hey, Charlie!
```

**How this works:**

1. `greet("Alice")` — `greeting` not provided, uses default `"Hello"`
2. `greet("Bob", "Good morning")` — `greeting` is `"Good morning"`, overrides the default
3. `greet("Charlie", "Hey")` — `greeting` is `"Hey"`

**Rule: Default parameters must come after non-default parameters:**

```python
def greet(greeting="Hello", name):
    print(f"{greeting}, {name}!")
```

**Error:**

```
SyntaxError: non-default argument follows default argument
```

**Why:** Python would not know how to assign `greet("Alice")` — is `"Alice"` the `greeting` or the `name`? Put required parameters first, defaults last.

### Keyword Arguments

You can pass arguments by name for clarity:

```python
def create_user(name, age, city):
    print(f"Name: {name}, Age: {age}, City: {city}")

# Positional — order matters
create_user("Alice", 30, "New York")

# Keyword — order does not matter
create_user(city="London", name="Bob", age=25)
```

**Output:**

```
Name: Alice, Age: 30, City: New York
Name: Bob, Age: 25, City: London
```

**Why use keyword arguments:** When a function has many parameters, keyword arguments make the call self-documenting. You can see what each value means without checking the function definition.

---

## Return Values

Functions can send a result back to the caller using `return`:

```python
def add(a, b):
    return a + b

result = add(3, 5)
print(result)
```

**Output:**

```
8
```

**How this works:**

1. `add(3, 5)` runs the function with `a=3`, `b=5`
2. `return a + b` → `return 8` — the function sends `8` back to the caller
3. `result = add(3, 5)` stores the returned value `8` in `result`
4. `print(result)` displays `8`

**You can use the return value directly:**

```python
def add(a, b):
    return a + b

print(add(10, 20))

total = add(1, 2) + add(3, 4)
print(total)
```

**Output:**

```
30
10
```

**Why `total` is 10:** `add(1, 2)` returns `3`, `add(3, 4)` returns `7`, and `3 + 7 = 10`.

### Return vs Print — A Common Confusion

```python
def add_print(a, b):
    print(a + b)

def add_return(a, b):
    return a + b
```

These look similar but behave very differently:

```python
result1 = add_print(3, 5)
print(f"result1 is: {result1}")

result2 = add_return(3, 5)
print(f"result2 is: {result2}")
```

**Output:**

```
8
result1 is: None
result2 is: 8
```

**Step by step:**

1. `add_print(3, 5)` — prints `8` to the screen, but returns nothing
2. `result1` is `None` because the function has no `return` statement
3. `add_return(3, 5)` — does not print anything, but returns `8`
4. `result2` is `8` because the function returned it

**Rule:** Use `return` when you need to use the result later. Use `print` only when you want to display something to the user. Most functions should `return`, not `print`.

**Flow diagram — print vs return:**

```
add_print(3, 5)              add_return(3, 5)
      |                            |
      v                            v
  print(8)                    return 8
      |                            |
      v                            v
  Shows "8"                   Sends 8 back
  on screen                   to the caller
      |                            |
      v                            v
  returns None               caller gets 8
  (nothing useful)            (can use it)
```

### Returning Multiple Values

```python
def get_min_max(numbers):
    return min(numbers), max(numbers)

lowest, highest = get_min_max([5, 2, 8, 1, 9])
print(f"Min: {lowest}, Max: {highest}")
```

**Output:**

```
Min: 1, Max: 9
```

**How this works:** `return min(numbers), max(numbers)` returns a **tuple** — a pair of values. The `lowest, highest = ...` syntax **unpacks** the tuple into two separate variables.

### Return Stops the Function

```python
def check_age(age):
    if age < 0:
        return "Invalid age"
    if age >= 18:
        return "Adult"
    return "Minor"

print(check_age(-5))
print(check_age(25))
print(check_age(12))
```

**Output:**

```
Invalid age
Adult
Minor
```

**Why:** When Python hits a `return` statement, it immediately exits the function. No code after the `return` runs. This is why you can write multiple `return` statements — only the first one reached actually executes.

---

## Scope — Where Variables Live

Variables created inside a function only exist inside that function. This is called **local scope**:

```python
def my_function():
    secret = "hidden"
    print(secret)

my_function()
print(secret)
```

**Output:**

```
hidden
```

Then:

```
NameError: name 'secret' is not defined
```

**Why:** `secret` was created inside `my_function()`. Once the function finishes, `secret` is gone. The outside code cannot see it.

### Global Variables

Variables created outside functions are accessible everywhere:

```python
greeting = "Hello"

def say_hello(name):
    print(f"{greeting}, {name}!")

say_hello("Alice")
```

**Output:**

```
Hello, Alice!
```

**Why:** `greeting` is defined at the top level (global scope). Functions can **read** global variables.

**But you cannot modify a global variable from inside a function without `global`:**

```python
count = 0

def increment():
    count = count + 1    # This fails!

increment()
```

**Error:**

```
UnboundLocalError: cannot access local variable 'count' where it is not associated with a value
```

**Why:** When Python sees `count = count + 1`, it thinks `count` is a local variable (because of the assignment). But it has not been defined locally yet, so it fails.

> **Best practice:** Avoid relying on global variables. Pass data into functions as parameters and get results back via `return`. This makes functions predictable and testable.

---

## *args and **kwargs — Variable Number of Arguments

### *args — Accept Any Number of Positional Arguments

```python
def add_all(*numbers):
    total = 0
    for n in numbers:
        total += n
    return total

print(add_all(1, 2))
print(add_all(1, 2, 3, 4, 5))
print(add_all(10))
```

**Output:**

```
3
15
10
```

**How this works:** The `*` before `numbers` tells Python to collect all positional arguments into a **tuple**. So `add_all(1, 2, 3)` makes `numbers = (1, 2, 3)`.

### **kwargs — Accept Any Number of Keyword Arguments

```python
def print_info(**details):
    for key, value in details.items():
        print(f"  {key}: {value}")

print_info(name="Alice", age=30, city="New York")
```

**Output:**

```
  name: Alice
  age: 30
  city: New York
```

**How this works:** The `**` before `details` collects all keyword arguments into a **dictionary**. So `print_info(name="Alice", age=30)` makes `details = {"name": "Alice", "age": 30}`.

---

## Lambda Functions — Small Anonymous Functions

A lambda is a tiny function defined in one line:

```python
# Regular function
def double(x):
    return x * 2

# Same thing as a lambda
double = lambda x: x * 2

print(double(5))
```

**Output:**

```
10
```

**When to use lambdas:** They are most useful as arguments to functions like `sorted()`:

```python
students = [("Alice", 85), ("Bob", 92), ("Charlie", 78)]

# Sort by score (second element of each tuple)
sorted_students = sorted(students, key=lambda s: s[1], reverse=True)
print(sorted_students)
```

**Output:**

```
[('Bob', 92), ('Alice', 85), ('Charlie', 78)]
```

**How to read `lambda s: s[1]`:** "A function that takes `s` and returns `s[1]`." The `key` parameter tells `sorted()` what value to sort by.

**Sorting dictionaries:**

```python
people = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
]

by_age = sorted(people, key=lambda p: p["age"])
for p in by_age:
    print(f"  {p['name']}: {p['age']}")
```

**Output:**

```
  Bob: 25
  Alice: 30
  Charlie: 35
```

> **Rule:** If a lambda is more than one line of logic, use a regular `def` function instead. Lambdas are for simple, one-expression operations.

---

## Docstrings — Documenting Your Functions

A docstring is a string at the beginning of a function that explains what it does:

```python
def calculate_area(length, width):
    """
    Calculate the area of a rectangle.
    
    Args:
        length: The length of the rectangle.
        width: The width of the rectangle.
    
    Returns:
        The area as a number.
    """
    return length * width

# You can read the docstring with help()
help(calculate_area)
```

**Output:**

```
Help on function calculate_area in module __main__:

calculate_area(length, width)
    Calculate the area of a rectangle.
    
    Args:
        length: The length of the rectangle.
        width: The width of the rectangle.
    
    Returns:
        The area as a number.
```

**When to write docstrings:** For any function that is not immediately obvious from its name and parameters. Your future self (and your teammates) will thank you.

---

## Practical Examples

### Example 1: Temperature Converter

```python
def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    return celsius * 9/5 + 32

def fahrenheit_to_celsius(fahrenheit):
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5/9

print(celsius_to_fahrenheit(0))
print(celsius_to_fahrenheit(100))
print(fahrenheit_to_celsius(72))
```

**Output:**

```
32.0
212.0
22.22222222222222
```

**Why these values:**

- 0°C = 32°F (water freezes)
- 100°C = 212°F (water boils)
- 72°F ≈ 22.2°C (room temperature)

### Example 2: Grade Calculator with Multiple Functions

```python
def calculate_grade(score):
    """Convert a numeric score to a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def process_students(students):
    """Print grades for all students."""
    for name, score in students.items():
        grade = calculate_grade(score)
        status = "PASS" if grade != "F" else "FAIL"
        print(f"  {name}: {score} -> {grade} ({status})")

students = {
    "Alice": 95,
    "Bob": 82,
    "Charlie": 67,
    "Diana": 73,
    "Eve": 45,
}

process_students(students)
```

**Output:**

```
  Alice: 95 -> A (PASS)
  Bob: 82 -> B (PASS)
  Charlie: 67 -> D (PASS)
  Diana: 73 -> C (PASS)
  Eve: 45 -> F (FAIL)
```

**What is happening:** `process_students` loops through each student, calls `calculate_grade` to get the letter grade, and determines pass/fail. This shows how small functions compose together.

### Example 3: Password Validator

```python
def validate_password(password):
    """Check if a password meets security requirements."""
    errors = []
    
    if len(password) < 8:
        errors.append("Must be at least 8 characters")
    
    if not any(c.isupper() for c in password):
        errors.append("Must contain an uppercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Must contain a number")
    
    if errors:
        return False, errors
    else:
        return True, []

passwords = ["hello", "Hello123", "Ab1", "SecurePass1"]

for pwd in passwords:
    is_valid, errors = validate_password(pwd)
    if is_valid:
        print(f"  '{pwd}' — Valid")
    else:
        print(f"  '{pwd}' — Invalid: {', '.join(errors)}")
```

**Output:**

```
  'hello' — Invalid: Must be at least 8 characters, Must contain an uppercase letter, Must contain a number
  'Hello123' — Valid
  'Ab1' — Invalid: Must be at least 8 characters
  'SecurePass1' — Valid
```

**How `any()` works:** `any(c.isupper() for c in password)` checks if **any** character in the password is uppercase. If none are, `any()` returns `False`, and `not False` is `True`, so the error is added.

---

## Applying This to DevOps — A Preview

Functions are the building blocks of automation. Here is how the concepts from this module apply in DevOps:

```python
import time
import socket

def check_service(host, port, timeout=5):
    """Check if a service is listening on host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False

def retry(func, max_attempts=3, delay=2):
    """Retry a function up to max_attempts times."""
    for attempt in range(1, max_attempts + 1):
        result = func()
        if result:
            return True
        if attempt < max_attempts:
            print(f"  Attempt {attempt} failed, retrying in {delay}s...")
            time.sleep(delay)
    return False

def deploy(service, version, servers, dry_run=False):
    """Deploy a service to multiple servers."""
    print(f"Deploying {service} v{version}")
    
    if dry_run:
        print("  [DRY RUN] No changes made")
        return True
    
    for server in servers:
        print(f"  Deploying to {server}...")
    
    return True

# Usage:
# deploy("api", "2.3.1", ["web-01", "web-02"], dry_run=True)
```

**Patterns to notice:**

- **Default parameters** (`timeout=5`, `dry_run=False`) provide sensible defaults
- **Return values** (`True`/`False`) let the caller decide what to do next
- **Docstrings** explain what each function does
- **Small, focused functions** — each does one thing

---

## Exercises

**Exercise 1:** Write a function `is_even(n)` that returns `True` if a number is even, `False` otherwise. Test it with several numbers.

**Exercise 2:** Write a function `count_vowels(text)` that returns the number of vowels (a, e, i, o, u) in a string. Test with `"Hello World"` (should return 3).

**Exercise 3:** Write a function `find_longest(words)` that takes a list of strings and returns the longest one. If there is a tie, return the first one found.

**Exercise 4:** Write a function `fizzbuzz(n)` that returns `"FizzBuzz"` if `n` is divisible by both 3 and 5, `"Fizz"` if divisible by 3, `"Buzz"` if divisible by 5, or the number as a string otherwise. Use it in a loop to print results for 1-20.

---

## Common Mistakes

### 1. Forgetting return

```python
def add(a, b):
    a + b    # Computes the sum but does not return it

result = add(3, 5)
print(result)
```

**Output:**

```
None
```

**Why:** Without `return`, the function returns `None`. The computation `a + b` happens but the result is thrown away.

**Fix:** `return a + b`

### 2. Mutable Default Arguments

```python
def add_item(item, items=[]):
    items.append(item)
    return items

print(add_item("apple"))
print(add_item("banana"))
```

**Output:**

```
['apple']
['apple', 'banana']
```

**Why this is a bug:** The default list `[]` is created once when the function is defined, not each time it is called. All calls share the same list.

**Fix:**

```python
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(add_item("apple"))
print(add_item("banana"))
```

**Output:**

```
['apple']
['banana']
```

### 3. Functions That Do Too Much

If your function is named `deploy_and_notify_and_log`, it should be three separate functions: `deploy()`, `notify()`, and `log()`. Each function should do one thing well.

### 4. Calling Without Parentheses

```python
def get_status():
    return "OK"

status = get_status    # Missing ()
print(status)
```

**Output:**

```
<function get_status at 0x...>
```

**Why:** Without `()`, you get the function object, not its return value. Use `get_status()`.

---

## Summary

| Concept | What It Does | Example |
|---------|-------------|---------|
| `def` | Define a function | `def greet():` |
| Parameters | Accept input values | `def greet(name):` |
| Default params | Provide fallback values | `def greet(name="World"):` |
| `return` | Send a value back | `return result` |
| Multiple return | Return several values | `return min_val, max_val` |
| Scope | Variables live inside their function | Local vs global |
| `*args` | Accept any number of arguments | `def f(*args):` |
| `**kwargs` | Accept any keyword arguments | `def f(**kwargs):` |
| Lambda | One-line anonymous function | `lambda x: x * 2` |
| Docstring | Document a function | `"""Description."""` |

---

[Previous: Module 04 — Control Flow](04-control-flow.md) | [Next: Module 06 — File Handling and Log Processing](06-file-handling-and-log-processing.md)
