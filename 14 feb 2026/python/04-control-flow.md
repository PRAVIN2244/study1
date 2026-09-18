# Module 4 — Control Flow

Control flow lets your code make decisions and repeat actions. Without it, Python runs every line from top to bottom, doing the same thing every time. With control flow, your code can react to different situations.

---

## if Statements — Making Decisions

### Basic if

```python
age = 20

if age >= 18:
    print("You are an adult.")
```

**Output:**

```
You are an adult.
```

**How Python evaluates this:**

1. `age >= 18` → `20 >= 18` → `True`
2. Because the condition is `True`, Python runs the indented line
3. `print("You are an adult.")` displays the message

**What if the condition is False?**

```python
age = 15

if age >= 18:
    print("You are an adult.")

print("Program continues here.")
```

**Output:**

```
Program continues here.
```

**Why:** `15 >= 18` is `False`, so Python skips the indented block entirely. The last `print()` is not indented under the `if`, so it always runs.

### Rule: Indentation Defines the Block

Python uses indentation (4 spaces) to know which lines belong to the `if`. This is not optional — it is part of the syntax.

**What happens if you forget indentation:**

```python
age = 20

if age >= 18:
print("You are an adult.")
```

**Error:**

```
IndentationError: expected an indented block after 'if' statement on line 3
```

**Why:** Python saw the `if` line ending with `:` and expected the next line to be indented. It was not, so Python does not know what code belongs to the `if`.

### Rule: The Colon is Required

```python
age = 20

if age >= 18
    print("You are an adult.")
```

**Error:**

```
SyntaxError: expected ':'
```

**Why:** Every `if`, `elif`, `else`, `for`, and `while` line must end with a colon (`:`). The colon tells Python "the block of code starts on the next line."

---

### if / else — Two Paths

```python
temperature = 35

if temperature > 30:
    print("It's hot outside!")
else:
    print("The weather is nice.")
```

**Output:**

```
It's hot outside!
```

**How Python evaluates this:**

1. `temperature > 30` → `35 > 30` → `True`
2. Because `True`, Python runs the `if` block: prints "It's hot outside!"
3. The `else` block is skipped entirely

**Now change the value:**

```python
temperature = 22

if temperature > 30:
    print("It's hot outside!")
else:
    print("The weather is nice.")
```

**Output:**

```
The weather is nice.
```

**Why:** `22 > 30` is `False`, so Python skips the `if` block and runs the `else` block instead. One of the two blocks always runs — never both, never neither.

**Flow diagram:**

```
        condition
           |
     +-----+-----+
     |             |
   True          False
     |             |
     v             v
  if block     else block
     |             |
     +-----+------+
           |
           v
     continues...
```

---

### if / elif / else — Multiple Conditions

```python
score = 75

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
elif score >= 60:
    grade = "D"
else:
    grade = "F"

print(f"Score: {score}, Grade: {grade}")
```

**Output:**

```
Score: 75, Grade: C
```

**How Python evaluates this step by step:**

1. `score >= 90` → `75 >= 90` → `False` — skip
2. `score >= 80` → `75 >= 80` → `False` — skip
3. `score >= 70` → `75 >= 70` → `True` — **run this block**, set `grade = "C"`
4. All remaining `elif` and `else` are skipped — Python stops at the first `True`

**Key rule:** Python checks conditions from top to bottom. The **first** one that is `True` wins. Everything after it is ignored, even if other conditions would also be `True`.

**Demonstrating the "first match wins" rule:**

```python
score = 95

if score >= 70:
    grade = "C"
elif score >= 80:
    grade = "B"
elif score >= 90:
    grade = "A"

print(f"Score: {score}, Grade: {grade}")
```

**Output:**

```
Score: 95, Grade: C
```

**Why this is wrong:** 95 is >= 70, so Python matches the first condition and assigns "C". It never checks the others. **Order matters** — always put the most specific (highest) condition first.

---

## Combining Conditions — and, or, not

### and — Both Must Be True

```python
age = 25
has_license = True

if age >= 18 and has_license:
    print("You can drive.")
else:
    print("You cannot drive.")
```

**Output:**

```
You can drive.
```

**How Python evaluates:**

1. `age >= 18` → `25 >= 18` → `True`
2. `has_license` → `True`
3. `True and True` → `True`
4. The `if` block runs

**When one is False:**

```python
age = 25
has_license = False

if age >= 18 and has_license:
    print("You can drive.")
else:
    print("You cannot drive.")
```

**Output:**

```
You cannot drive.
```

**Why:** `True and False` → `False`. With `and`, **both** sides must be `True`.

### or — At Least One Must Be True

```python
is_weekend = False
is_holiday = True

if is_weekend or is_holiday:
    print("No work today!")
else:
    print("Time to work.")
```

**Output:**

```
No work today!
```

**How Python evaluates:**

1. `is_weekend` → `False`
2. `is_holiday` → `True`
3. `False or True` → `True`
4. The `if` block runs

With `or`, only **one** side needs to be `True`.

### not — Reverses the Condition

```python
is_raining = False

if not is_raining:
    print("Let's go for a walk.")
```

**Output:**

```
Let's go for a walk.
```

**How Python evaluates:**

1. `is_raining` → `False`
2. `not False` → `True`
3. The `if` block runs

### Combining Multiple Operators

```python
age = 25
is_student = True
has_id = False

if age >= 18 and (is_student or has_id):
    print("Eligible for discount.")
```

**Output:**

```
Eligible for discount.
```

**Step by step:**

1. `age >= 18` → `True`
2. `is_student or has_id` → `True or False` → `True`
3. `True and True` → `True`

**Why parentheses matter:** Without them, `age >= 18 and is_student or has_id` would evaluate as `(age >= 18 and is_student) or has_id` because `and` has higher precedence than `or`. Use parentheses to make your intent clear.

---

## Comparison Operators — Quick Reference

```python
x = 10
y = 20

print(x == y)     # Equal to          → False
print(x != y)     # Not equal to      → True
print(x > y)      # Greater than      → False
print(x < y)      # Less than         → True
print(x >= y)     # Greater or equal  → False
print(x <= y)     # Less or equal     → True
```

**Common mistake — using `=` instead of `==`:**

```python
x = 10

if x = 10:
    print("x is 10")
```

**Error:**

```
SyntaxError: invalid syntax. Maybe you meant '==' or ':='?
```

**Why:** `=` is assignment (store a value). `==` is comparison (check if equal). Python even suggests the fix in the error message.

---

## Truthiness — What Python Considers True or False

In `if` statements, Python does not require an explicit `True` or `False`. Every value has a "truthiness":

**Falsy values** (treated as `False`):

```python
# All of these are falsy:
if not False:       print("False is falsy")
if not None:        print("None is falsy")
if not 0:           print("0 is falsy")
if not 0.0:         print("0.0 is falsy")
if not "":          print("empty string is falsy")
if not []:          print("empty list is falsy")
if not {}:          print("empty dict is falsy")
```

**Output:**

```
False is falsy
None is falsy
0 is falsy
0.0 is falsy
empty string is falsy
empty list is falsy
empty dict is falsy
```

**Truthy values** (treated as `True`): everything else — any non-zero number, any non-empty string, any non-empty collection.

**Practical use — checking if a variable has a value:**

```python
name = ""

if name:
    print(f"Hello, {name}")
else:
    print("Name is empty!")
```

**Output:**

```
Name is empty!
```

**Why:** An empty string `""` is falsy. So `if name:` is `False`, and the `else` block runs.

```python
name = "Alice"

if name:
    print(f"Hello, {name}")
else:
    print("Name is empty!")
```

**Output:**

```
Hello, Alice
```

**Why:** `"Alice"` is a non-empty string, so it is truthy.

**Practical use — checking if a list has items:**

```python
items = ["apple", "banana"]

if items:
    print(f"You have {len(items)} items")
else:
    print("Your list is empty")
```

**Output:**

```
You have 2 items
```

**Why:** A list with elements is truthy. An empty list `[]` would be falsy.

---

## for Loops — Repeating Actions

A `for` loop runs a block of code once for each item in a sequence (list, string, range, etc.).

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

**How this works:**

1. **First iteration:** `fruit` = `"apple"` → prints "I like apple"
2. **Second iteration:** `fruit` = `"banana"` → prints "I like banana"
3. **Third iteration:** `fruit` = `"cherry"` → prints "I like cherry"
4. No more items → loop ends

The variable `fruit` is created by the `for` loop. On each iteration, it takes the next value from the list. You can name it anything — `fruit`, `item`, `x` — but use a descriptive name.

**Flow diagram:**

```
     Start
       |
       v
  +----------+
  | Next item |<-----------+
  | in list?  |            |
  +----------+            |
       |                   |
  +----+----+              |
  |         |              |
 Yes        No             |
  |         |              |
  v         v              |
Run body   Done            |
  |                        |
  +------------------------+
```

### Looping Through a String

```python
word = "Hello"

for letter in word:
    print(letter)
```

**Output:**

```
H
e
l
l
o
```

**Why:** A string is a sequence of characters. The `for` loop goes through each character one at a time.

### Looping with range()

`range()` generates a sequence of numbers. It does not create a list — it produces numbers one at a time as the loop needs them.

```python
for i in range(5):
    print(i)
```

**Output:**

```
0
1
2
3
4
```

**Why it starts at 0:** Python counts from 0 by default. `range(5)` produces 5 numbers: 0, 1, 2, 3, 4. It stops **before** 5.

**Specifying start and stop:**

```python
for i in range(1, 6):
    print(i)
```

**Output:**

```
1
2
3
4
5
```

**Why:** `range(1, 6)` starts at 1 and stops before 6. The stop value is always excluded.

**Specifying a step:**

```python
for i in range(0, 10, 2):
    print(i)
```

**Output:**

```
0
2
4
6
8
```

**Why:** The third argument is the step. `range(0, 10, 2)` means: start at 0, go up to (but not including) 10, counting by 2.

**Counting backwards:**

```python
for i in range(5, 0, -1):
    print(i)
```

**Output:**

```
5
4
3
2
1
```

**Why:** Step is `-1`, so it counts down. Starts at 5, stops before 0.

### enumerate() — When You Need the Index

Sometimes you need both the item and its position. `enumerate()` gives you both:

```python
colors = ["red", "green", "blue"]

for index, color in enumerate(colors):
    print(f"{index}: {color}")
```

**Output:**

```
0: red
1: green
2: blue
```

**How this works:** `enumerate()` wraps each item with its index. On each iteration, you get two values: the index and the item. The `index, color` syntax is called **unpacking** — it assigns each value to a separate variable.

**Starting the count from 1:**

```python
colors = ["red", "green", "blue"]

for index, color in enumerate(colors, start=1):
    print(f"{index}. {color}")
```

**Output:**

```
1. red
2. green
3. blue
```

**Why:** `start=1` tells `enumerate()` to begin counting at 1 instead of 0.

### zip() — Looping Through Multiple Lists Together

```python
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92, 78]

for name, score in zip(names, scores):
    print(f"{name}: {score}")
```

**Output:**

```
Alice: 85
Bob: 92
Charlie: 78
```

**How this works:** `zip()` pairs up items from both lists by position. First iteration gets `("Alice", 85)`, second gets `("Bob", 92)`, and so on.

**What if lists have different lengths?**

```python
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92]

for name, score in zip(names, scores):
    print(f"{name}: {score}")
```

**Output:**

```
Alice: 85
Bob: 92
```

**Why:** `zip()` stops at the shortest list. "Charlie" has no matching score, so it is skipped.

### Looping Through a Dictionary

```python
person = {"name": "Alice", "age": 30, "city": "New York"}

# Loop through keys and values
for key, value in person.items():
    print(f"{key}: {value}")
```

**Output:**

```
name: Alice
age: 30
city: New York
```

**Other ways to loop through a dictionary:**

```python
person = {"name": "Alice", "age": 30, "city": "New York"}

# Keys only
for key in person:
    print(key)
# name
# age
# city

# Values only
for value in person.values():
    print(value)
# Alice
# 30
# New York
```

### Nested for Loops — A Loop Inside a Loop

```python
for i in range(1, 4):
    for j in range(1, 4):
        print(f"{i} x {j} = {i * j}")
    print("---")
```

**Output:**

```
1 x 1 = 1
1 x 2 = 2
1 x 3 = 3
---
2 x 1 = 2
2 x 2 = 4
2 x 3 = 6
---
3 x 1 = 3
3 x 2 = 6
3 x 3 = 9
---
```

**How this works:** For each value of `i`, the inner loop runs completely through all values of `j`. The outer loop runs 3 times, and for each of those, the inner loop runs 3 times — so the `print` inside runs 9 times total.

---

## while Loops — Repeat Until a Condition Changes

A `while` loop keeps running as long as its condition is `True`:

```python
count = 1

while count <= 5:
    print(f"Count: {count}")
    count = count + 1

print("Done!")
```

**Output:**

```
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
Done!
```

**How Python evaluates this:**

1. `count = 1` → `1 <= 5` → `True` → print "Count: 1", set count to 2
2. `count = 2` → `2 <= 5` → `True` → print "Count: 2", set count to 3
3. `count = 3` → `3 <= 5` → `True` → print "Count: 3", set count to 4
4. `count = 4` → `4 <= 5` → `True` → print "Count: 4", set count to 5
5. `count = 5` → `5 <= 5` → `True` → print "Count: 5", set count to 6
6. `count = 6` → `6 <= 5` → `False` → loop ends
7. "Done!" prints

**What happens if you forget to update the counter:**

```python
count = 1

while count <= 5:
    print(f"Count: {count}")
    # Forgot: count = count + 1
```

**What happens:** This prints "Count: 1" forever. `count` never changes, so `1 <= 5` is always `True`. This is called an **infinite loop**. Press `Ctrl+C` to stop it.

**Rule:** Every `while` loop must change something that eventually makes the condition `False`.

**Flow diagram:**

```
     Start
       |
       v
  +-----------+
  | Condition |<-----------+
  |  True?    |            |
  +-----------+            |
       |                   |
  +----+----+              |
  |         |              |
 True      False           |
  |         |              |
  v         v              |
Run body   Done            |
  |                        |
  +-- update variable -----+
```

### while with User Input

```python
password = ""

while password != "secret123":
    password = input("Enter password: ")

print("Access granted!")
```

**How this works:**

1. `password` starts as `""`, which is not `"secret123"`, so the loop runs
2. The user types something — if it is wrong, the loop runs again
3. When the user types `"secret123"`, the condition becomes `False` and the loop ends

### Practical Example: Countdown

```python
countdown = 5

while countdown > 0:
    print(countdown)
    countdown -= 1    # Same as: countdown = countdown - 1

print("Go!")
```

**Output:**

```
5
4
3
2
1
Go!
```

---

## Loop Control: break, continue, else

### break — Exit the Loop Early

`break` immediately stops the loop, even if there are more items or the condition is still `True`:

```python
numbers = [1, 3, 5, 8, 9, 11]

for num in numbers:
    if num % 2 == 0:
        print(f"First even number: {num}")
        break
    print(f"  {num} is odd, keep looking...")
```

**Output:**

```
  1 is odd, keep looking...
  3 is odd, keep looking...
  5 is odd, keep looking...
First even number: 8
```

**How this works:**

1. `1 % 2 == 0` → `1 == 0` → `False` → print "1 is odd"
2. `3 % 2 == 0` → `1 == 0` → `False` → print "3 is odd"
3. `5 % 2 == 0` → `1 == 0` → `False` → print "5 is odd"
4. `8 % 2 == 0` → `0 == 0` → `True` → print "First even number: 8", then `break`
5. Loop ends immediately — 9 and 11 are never checked

### continue — Skip to the Next Iteration

`continue` skips the rest of the current iteration and jumps to the next one:

```python
for num in range(1, 8):
    if num % 2 == 0:
        continue    # Skip even numbers
    print(f"{num} is odd")
```

**Output:**

```
1 is odd
3 is odd
5 is odd
7 is odd
```

**How this works:**

1. `num = 1` → `1 % 2 == 0` → `False` → `continue` not hit → print "1 is odd"
2. `num = 2` → `2 % 2 == 0` → `True` → `continue` → skip to next iteration
3. `num = 3` → `3 % 2 == 0` → `False` → print "3 is odd"
4. `num = 4` → `4 % 2 == 0` → `True` → `continue` → skip
5. And so on...

### for/else — Did the Loop Complete Without Breaking?

The `else` block on a `for` loop runs only if the loop finished normally (without `break`):

```python
numbers = [1, 3, 5, 7, 9]
target = 4

for num in numbers:
    if num == target:
        print(f"Found {target}!")
        break
else:
    print(f"{target} not found in the list")
```

**Output:**

```
4 not found in the list
```

**Why:** The loop checked every number and never hit `break`. So the `else` block runs.

**Now with a value that exists:**

```python
numbers = [1, 3, 5, 7, 9]
target = 5

for num in numbers:
    if num == target:
        print(f"Found {target}!")
        break
else:
    print(f"{target} not found in the list")
```

**Output:**

```
Found 5!
```

**Why:** The loop found 5 and hit `break`. Because `break` was used, the `else` block is skipped.

### break in a while Loop

```python
attempt = 0
max_attempts = 5

while attempt < max_attempts:
    attempt += 1
    print(f"Attempt {attempt}...")
    
    if attempt == 3:
        print("Success on attempt 3!")
        break
else:
    print("All attempts failed.")
```

**Output:**

```
Attempt 1...
Attempt 2...
Attempt 3...
Success on attempt 3!
```

**Why:** `break` was hit on attempt 3, so the `else` block ("All attempts failed.") does not run.

---

## List Comprehensions — Concise List Creation

A list comprehension creates a new list by transforming each item from an existing sequence.

### Traditional Way vs. Comprehension

```python
# Traditional way — 4 lines
squares = []
for x in range(1, 6):
    squares.append(x ** 2)
print(squares)
```

**Output:**

```
[1, 4, 9, 16, 25]
```

```python
# List comprehension — 1 line, same result
squares = [x ** 2 for x in range(1, 6)]
print(squares)
```

**Output:**

```
[1, 4, 9, 16, 25]
```

**How to read it:** "Create a list of `x ** 2` for each `x` in `range(1, 6)`."

**The pattern:** `[expression for variable in iterable]`

### With a Condition (Filtering)

```python
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

evens = [n for n in numbers if n % 2 == 0]
print(evens)
```

**Output:**

```
[2, 4, 6, 8, 10]
```

**How to read it:** "Create a list of `n` for each `n` in `numbers`, but only if `n % 2 == 0`."

**The pattern:** `[expression for variable in iterable if condition]`

**Another example:**

```python
words = ["hi", "hello", "hey", "welcome", "bye"]

long_words = [w for w in words if len(w) > 4]
print(long_words)
```

**Output:**

```
['hello', 'welcome']
```

**Why:** Only "hello" (5 letters) and "welcome" (7 letters) have more than 4 characters.

### Transforming and Filtering Together

```python
names = ["alice", "BOB", "Charlie", "dave"]

# Capitalize names that are all lowercase
capitalized = [name.title() for name in names if name.islower()]
print(capitalized)
```

**Output:**

```
['Alice', 'Dave']
```

**Step by step:**

1. `"alice".islower()` → `True` → `"alice".title()` → `"Alice"` — included
2. `"BOB".islower()` → `False` — skipped
3. `"Charlie".islower()` → `False` — skipped
4. `"dave".islower()` → `True` → `"dave".title()` → `"Dave"` — included

### Dictionary Comprehension

```python
numbers = [1, 2, 3, 4, 5]

squares = {n: n ** 2 for n in numbers}
print(squares)
```

**Output:**

```
{1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
```

**How to read it:** "Create a dictionary where each key is `n` and each value is `n ** 2`."

### Set Comprehension

```python
words = ["hello", "world", "hello", "python", "world"]

unique_lengths = {len(w) for w in words}
print(unique_lengths)
```

**Output:**

```
{5, 6}
```

**Why:** "hello" and "world" are both 5 letters, "python" is 6. A set removes duplicates, so we get `{5, 6}`.

> **Readability rule:** If a comprehension gets complicated (multiple conditions, nested loops), use a regular `for` loop instead. Comprehensions should be readable at a glance.

---

## Practical Example: Simple Calculator

This example combines `if/elif/else` with nested conditions:

```python
num1 = 10
num2 = 3
operation = "divide"

if operation == "add":
    result = num1 + num2
elif operation == "subtract":
    result = num1 - num2
elif operation == "multiply":
    result = num1 * num2
elif operation == "divide":
    if num2 == 0:
        print("Error: Cannot divide by zero!")
        result = None
    else:
        result = num1 / num2
else:
    print(f"Unknown operation: {operation}")
    result = None

if result is not None:
    print(f"{num1} {operation} {num2} = {result}")
```

**Output:**

```
10 divide 3 = 3.3333333333333335
```

**How this works:**

1. `operation == "add"` → `"divide" == "add"` → `False` — skip
2. `operation == "subtract"` → `False` — skip
3. `operation == "multiply"` → `False` — skip
4. `operation == "divide"` → `True` — enter this block
5. Inside: `num2 == 0` → `3 == 0` → `False` → go to `else`, compute `10 / 3`
6. `result is not None` → `True` → print the result

**Why `is not None` instead of `!= None`:** `is` checks identity (is it the exact same object?), while `==` checks equality. For `None`, always use `is` or `is not`. This is a Python convention.

---

## Applying This to DevOps — A Preview

Now that you understand control flow, here is how these patterns appear in DevOps automation. You do not need to understand every detail yet — just see how `if`, `for`, and `while` are used in real scenarios.

### Checking Server Status

```python
servers = [
    {"name": "web-01", "status": "running", "cpu": 45},
    {"name": "web-02", "status": "stopped", "cpu": 0},
    {"name": "api-01", "status": "running", "cpu": 92},
]

for server in servers:
    name = server["name"]
    
    if server["status"] == "stopped":
        print(f"  {name}: STOPPED — needs restart")
    elif server["cpu"] > 80:
        print(f"  {name}: HIGH CPU ({server['cpu']}%) — alert!")
    else:
        print(f"  {name}: OK (CPU: {server['cpu']}%)")
```

**Output:**

```
  web-01: OK (CPU: 45%)
  web-02: STOPPED — needs restart
  api-01: HIGH CPU (92%) — alert!
```

**What is happening:** A `for` loop goes through each server. An `if/elif/else` chain decides what message to print based on the server's status and CPU usage.

### Retry Logic with while

```python
import time

max_retries = 3
attempt = 0

while attempt < max_retries:
    attempt += 1
    print(f"  Attempt {attempt}/{max_retries}: Connecting...")
    
    connected = (attempt == 3)  # Simulated: succeeds on 3rd try
    
    if connected:
        print("  Connected!")
        break
    else:
        print(f"  Failed. Retrying...")
        time.sleep(0.5)
else:
    print("  Could not connect after all retries.")
```

**Output:**

```
  Attempt 1/3: Connecting...
  Failed. Retrying...
  Attempt 2/3: Connecting...
  Failed. Retrying...
  Attempt 3/3: Connecting...
  Connected!
```

**What is happening:** A `while` loop retries a connection up to 3 times. If it succeeds, `break` exits the loop. If all attempts fail, the `else` block runs.

### Filtering with List Comprehension

```python
all_servers = ["web-01", "web-02", "api-01", "db-01", "api-02"]

web_servers = [s for s in all_servers if s.startswith("web-")]
api_servers = [s for s in all_servers if s.startswith("api-")]

print(f"Web: {web_servers}")
print(f"API: {api_servers}")
```

**Output:**

```
Web: ['web-01', 'web-02']
API: ['api-01', 'api-02']
```

---

## Exercises

**Exercise 1: FizzBuzz**

Write a program that prints numbers 1 to 20. For multiples of 3, print "Fizz" instead of the number. For multiples of 5, print "Buzz". For multiples of both 3 and 5, print "FizzBuzz".

Hint: Check the "both" case first (why?).

**Exercise 2: Count Passing and Failing**

Given a list of test scores `[85, 92, 78, 95, 60, 45, 88]`, use a loop to count how many are passing (>= 70) and how many are failing. Print both counts at the end.

**Exercise 3: Temperature Converter**

Use a list comprehension to convert a list of temperatures from Celsius to Fahrenheit: `celsius = [0, 10, 20, 30, 40]`. Formula: `F = C * 9/5 + 32`.

**Exercise 4: Find the Maximum**

Write a `while` loop that asks the user for numbers (use `input()`). When they type "done", stop and print the largest number entered.

**Exercise 5: Nested Loop Pattern**

Print this pattern using nested `for` loops:

```
*
**
***
****
*****
```

Hint: The outer loop controls the row (1 to 5). The inner loop prints stars.

---

## Common Mistakes

### 1. Forgetting the Colon

```python
if x > 5
    print("big")
```

**Error:** `SyntaxError: expected ':'`

**Fix:** `if x > 5:`

### 2. Wrong Indentation

```python
if True:
    print("line 1")
  print("line 2")
```

**Error:** `IndentationError: unexpected indent`

**Fix:** Use exactly 4 spaces for each level. Do not mix tabs and spaces.

### 3. Using = Instead of ==

```python
if x = 10:
    print("ten")
```

**Error:** `SyntaxError: invalid syntax`

**Fix:** `if x == 10:`

### 4. Infinite while Loop

```python
count = 1
while count <= 5:
    print(count)
    # Missing: count += 1
```

**What happens:** Prints `1` forever. Always update the loop variable.

### 5. Modifying a List While Looping

```python
numbers = [1, 2, 3, 4, 5]

for num in numbers:
    if num % 2 == 0:
        numbers.remove(num)

print(numbers)
```

**Output:**

```
[1, 3, 5]
```

This looks correct, but it can skip elements in larger lists. The safe way:

```python
numbers = [1, 2, 3, 4, 5]

# Loop over a copy, modify the original
for num in list(numbers):
    if num % 2 == 0:
        numbers.remove(num)

# Or use a list comprehension (better):
numbers = [n for n in numbers if n % 2 != 0]
```

### 6. Off-by-One with range()

```python
# Want to print 1 to 5
for i in range(5):
    print(i)
# Prints: 0, 1, 2, 3, 4  (not 1 to 5!)
```

**Fix:** `range(1, 6)` — remember, the stop value is excluded.

---

## Summary

| Concept | What It Does | Example |
|---------|-------------|---------|
| `if` | Runs code if condition is True | `if x > 0:` |
| `elif` | Checks another condition if previous was False | `elif x == 0:` |
| `else` | Runs if all conditions were False | `else:` |
| `and` | Both conditions must be True | `if a and b:` |
| `or` | At least one must be True | `if a or b:` |
| `not` | Reverses the condition | `if not done:` |
| `for` | Loops through a sequence | `for item in list:` |
| `range()` | Generates numbers | `range(1, 11)` |
| `enumerate()` | Loop with index | `for i, v in enumerate(list):` |
| `zip()` | Loop through multiple lists | `for a, b in zip(x, y):` |
| `while` | Loops while condition is True | `while count < 10:` |
| `break` | Exit loop immediately | `break` |
| `continue` | Skip to next iteration | `continue` |
| `for/else` | Else runs if no break | `for...else:` |
| List comp | Create list in one line | `[x**2 for x in range(5)]` |
| Dict comp | Create dict in one line | `{k: v for k, v in items}` |

---

[Previous: Module 03 — Python Fundamentals](03-python-fundamentals.md) | [Next: Module 05 — Functions and Modular Automation](05-functions-and-modular-automation.md)
