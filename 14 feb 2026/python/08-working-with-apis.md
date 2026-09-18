# Module 8 — Working with APIs

An API (Application Programming Interface) lets your Python code talk to other services over the internet. When you check the weather on your phone, the app calls a weather API. When you deploy code, your CI/CD system calls APIs for GitHub, Docker Hub, and your cloud provider.

In DevOps, you interact with APIs constantly — GitHub, Jenkins, AWS, Slack, monitoring tools. This module teaches you how.

---

## What is a REST API?

A REST API uses HTTP (the same protocol your browser uses) to send and receive data. The key concepts:

| Concept | Meaning | Example |
|---------|---------|---------|
| **Endpoint** | A URL that represents a resource | `https://api.github.com/users/octocat` |
| **Method** | The action to perform | GET (read), POST (create), PUT (update), DELETE (remove) |
| **Request** | What you send to the API | URL + method + optional data |
| **Response** | What the API sends back | Status code + data (usually JSON) |
| **Status Code** | Whether the request succeeded | 200 (OK), 404 (Not Found), 500 (Server Error) |

---

## Installing the requests Library

Python's built-in `urllib` works but is verbose. The `requests` library is the standard choice:

```bash
pip install requests
```

Verify it is installed:

```python
import requests
print(requests.__version__)
```

**Output:**

```
2.31.0
```

---

## Making Your First API Call

```python
import requests

response = requests.get("https://httpbin.org/get")

print(f"Status Code: {response.status_code}")
print(f"Content Type: {response.headers['Content-Type']}")
print(f"Response Body:\n{response.text[:200]}")
```

**Output:**

```
Status Code: 200
Content Type: application/json
Response Body:
{
  "args": {},
  "headers": {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Host": "httpbin.org",
    ...
  },
  "url": "https://httpbin.org/get"
}
```

**How this works:**

```
Your Python Script                    Remote Server
       |                                   |
       +--- HTTP GET request ------------->|
       |    (URL + headers)                |
       |                                   |
       |                          Processes request
       |                                   |
       |<--- HTTP Response ----------------+
       |    (status code + headers + body)
       |
       v
  response.status_code  (200, 404, 500...)
  response.headers      (Content-Type, etc.)
  response.text         (the actual data)
```

1. `requests.get(url)` sends an HTTP GET request to the URL
2. The server processes the request and sends back a response
3. `response.status_code` — the HTTP status code (200 = success)
4. `response.headers` — metadata about the response
5. `response.text` — the response body as a string

### Parsing JSON Responses

Most APIs return JSON. Use `.json()` to parse it into a Python dictionary:

```python
import requests

response = requests.get("https://httpbin.org/get")
data = response.json()

print(type(data))
print(f"URL: {data['url']}")
print(f"Host: {data['headers']['Host']}")
```

**Output:**

```
<class 'dict'>
URL: https://httpbin.org/get
Host: httpbin.org
```

**Why `.json()` instead of `json.loads(response.text)`:** They do the same thing, but `.json()` is shorter and handles encoding automatically.

---

## HTTP Methods — GET, POST, PUT, DELETE

### GET — Read Data

```python
import requests

# Get information about a GitHub user
response = requests.get("https://api.github.com/users/octocat")
user = response.json()

print(f"Name: {user['name']}")
print(f"Location: {user['location']}")
print(f"Public repos: {user['public_repos']}")
```

**Output:**

```
Name: The Octocat
Location: San Francisco
Public repos: 8
```

### POST — Create Data

```python
import requests

# httpbin.org echoes back what you send
response = requests.post(
    "https://httpbin.org/post",
    json={"name": "Alice", "role": "DevOps Engineer"}
)

data = response.json()
print(f"Status: {response.status_code}")
print(f"Sent data: {data['json']}")
```

**Output:**

```
Status: 200
Sent data: {'name': 'Alice', 'role': 'DevOps Engineer'}
```

**How this works:**

- `requests.post(url, json=data)` sends a POST request with JSON data in the body
- The `json=` parameter automatically converts the Python dict to JSON and sets the `Content-Type` header

### PUT — Update Data

```python
import requests

response = requests.put(
    "https://httpbin.org/put",
    json={"name": "Alice", "role": "Senior DevOps Engineer"}
)

print(f"Status: {response.status_code}")
```

**Output:**

```
Status: 200
```

### DELETE — Remove Data

```python
import requests

response = requests.delete("https://httpbin.org/delete")
print(f"Status: {response.status_code}")
```

**Output:**

```
Status: 200
```

---

## HTTP Status Codes

Every API response includes a status code that tells you what happened:

| Code | Meaning | What to Do |
|------|---------|-----------|
| 200 | OK — request succeeded | Process the data |
| 201 | Created — resource was created | Success for POST requests |
| 204 | No Content — success, no body | Success for DELETE requests |
| 400 | Bad Request — your request is wrong | Check your data |
| 401 | Unauthorized — bad or missing credentials | Check your API key/token |
| 403 | Forbidden — you do not have permission | Check your permissions |
| 404 | Not Found — resource does not exist | Check the URL |
| 429 | Too Many Requests — rate limited | Wait and retry |
| 500 | Internal Server Error — server broke | Not your fault, retry later |

### Checking Status Codes in Your Code

```python
import requests

response = requests.get("https://api.github.com/users/octocat")

if response.status_code == 200:
    user = response.json()
    print(f"Found user: {user['name']}")
elif response.status_code == 404:
    print("User not found")
else:
    print(f"Unexpected error: {response.status_code}")
```

**A shorter way — raise an exception on errors:**

```python
import requests

response = requests.get("https://api.github.com/users/nonexistent-user-12345")

try:
    response.raise_for_status()
    user = response.json()
    print(f"Found: {user['name']}")
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
```

**Output:**

```
HTTP Error: 404 Client Error: Not Found for url: https://api.github.com/users/nonexistent-user-12345
```

**What `raise_for_status()` does:** If the status code is 4xx or 5xx, it raises an `HTTPError` exception. If the status is 2xx (success), it does nothing.

---

## Query Parameters

Many APIs accept parameters in the URL to filter or customize results:

```python
import requests

# Search GitHub repositories
response = requests.get(
    "https://api.github.com/search/repositories",
    params={
        "q": "language:python",
        "sort": "stars",
        "per_page": 3
    }
)

data = response.json()
print(f"Total results: {data['total_count']}")
print(f"\nTop 3 Python repos:")

for repo in data["items"]:
    print(f"  {repo['full_name']}: {repo['stargazers_count']:,} stars")
```

**Output (approximate):**

```
Total results: 12345678

Top 3 Python repos:
  public-apis/public-apis: 280,000 stars
  donnemartin/system-design-primer: 245,000 stars
  TheAlgorithms/Python: 175,000 stars
```

**How `params` works:** `requests` converts the dictionary into URL query parameters. The actual URL becomes:

```
https://api.github.com/search/repositories?q=language:python&sort=stars&per_page=3
```

---

## Headers and Authentication

Most APIs require authentication. The most common methods:

### API Token in Headers

```python
import requests

# GitHub API with personal access token
headers = {
    "Authorization": "token ghp_your_token_here",
    "Accept": "application/vnd.github.v3+json"
}

response = requests.get(
    "https://api.github.com/user",
    headers=headers
)

if response.status_code == 200:
    user = response.json()
    print(f"Authenticated as: {user['login']}")
else:
    print(f"Auth failed: {response.status_code}")
```

### Bearer Token (Common for OAuth)

```python
import requests

headers = {
    "Authorization": "Bearer your_token_here"
}

response = requests.get("https://api.example.com/data", headers=headers)
```

### Basic Authentication

```python
import requests

response = requests.get(
    "https://api.example.com/data",
    auth=("username", "password")
)
```

> **Security rule:** Never hardcode tokens in your code. Use environment variables:

```python
import os
import requests

token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("Error: GITHUB_TOKEN environment variable not set")
    exit(1)

headers = {"Authorization": f"token {token}"}
response = requests.get("https://api.github.com/user", headers=headers)
```

**Set the environment variable before running:**

```bash
export GITHUB_TOKEN="ghp_your_token_here"
python3 github_api.py
```

---

## Handling Errors and Timeouts

### Timeouts

Always set a timeout so your script does not hang forever:

```python
import requests

try:
    response = requests.get("https://httpbin.org/delay/10", timeout=3)
    print(f"Status: {response.status_code}")
except requests.exceptions.Timeout:
    print("Request timed out after 3 seconds")
except requests.exceptions.ConnectionError:
    print("Could not connect to the server")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

**Output:**

```
Request timed out after 3 seconds
```

**Why:** `timeout=3` means "give up after 3 seconds." The endpoint `/delay/10` waits 10 seconds before responding, so the timeout fires first.

### Retry Logic

```python
import requests
import time

def api_call_with_retry(url, max_retries=3, delay=2):
    """Make an API call with automatic retries."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"  Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                print(f"  Retrying in {delay}s...")
                time.sleep(delay)
    
    print("  All retries exhausted.")
    return None

result = api_call_with_retry("https://httpbin.org/get")
if result:
    print(f"Success: {result.status_code}")
```

---

## Pagination — Getting All Results

Many APIs return results in pages. You need to loop through all pages:

```python
import requests

def get_all_repos(username):
    """Get all public repositories for a GitHub user."""
    repos = []
    page = 1
    
    while True:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"page": page, "per_page": 100}
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break
        
        page_repos = response.json()
        
        if not page_repos:
            break    # No more results
        
        repos.extend(page_repos)
        print(f"  Page {page}: got {len(page_repos)} repos")
        page += 1
    
    return repos

repos = get_all_repos("octocat")
print(f"\nTotal repos: {len(repos)}")
for repo in repos[:5]:
    print(f"  {repo['name']}: {repo['description']}")
```

**How pagination works:**

1. Request page 1 with `per_page=100` (maximum items per page)
2. If the response has items, add them to our list and request page 2
3. If the response is empty, we have all the data — stop

---

## Rate Limiting

APIs limit how many requests you can make. GitHub allows 60 requests/hour without authentication, 5000 with a token.

```python
import requests

response = requests.get("https://api.github.com/rate_limit")
data = response.json()

core = data["resources"]["core"]
print(f"Limit: {core['limit']}")
print(f"Remaining: {core['remaining']}")
print(f"Resets at: {core['reset']}")
```

**Output (unauthenticated):**

```
Limit: 60
Remaining: 58
Resets at: 1705334400
```

**Handling rate limits in your code:**

```python
import requests
import time

def rate_limited_request(url, headers=None):
    """Make a request, respecting rate limits."""
    response = requests.get(url, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"Rate limited. Waiting {retry_after}s...")
        time.sleep(retry_after)
        return requests.get(url, headers=headers)
    
    return response
```

---

## Practical Example: Slack Webhook

Send messages to a Slack channel from Python:

```python
import requests
import json

def send_slack_message(webhook_url, message, color="good"):
    """Send a message to Slack via webhook."""
    payload = {
        "attachments": [{
            "text": message,
            "color": color    # "good" (green), "warning" (yellow), "danger" (red)
        }]
    }
    
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code == 200:
        print("Message sent to Slack!")
    else:
        print(f"Failed: {response.status_code} - {response.text}")

# Usage (replace with your actual webhook URL):
# webhook = os.environ.get("SLACK_WEBHOOK_URL")
# send_slack_message(webhook, "Deployment complete!", "good")
# send_slack_message(webhook, "High CPU on web-01!", "danger")
```

---

## Practical Example: GitHub API Wrapper

A reusable class for interacting with the GitHub API:

```python
import requests
import os

class GitHubAPI:
    """Simple wrapper for the GitHub API."""
    
    def __init__(self, token=None):
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self.session.headers["Accept"] = "application/vnd.github.v3+json"
    
    def get_user(self, username):
        """Get user information."""
        response = self.session.get(f"{self.base_url}/users/{username}")
        response.raise_for_status()
        return response.json()
    
    def get_repos(self, username):
        """Get all repositories for a user."""
        repos = []
        page = 1
        while True:
            response = self.session.get(
                f"{self.base_url}/users/{username}/repos",
                params={"page": page, "per_page": 100}
            )
            response.raise_for_status()
            page_data = response.json()
            if not page_data:
                break
            repos.extend(page_data)
            page += 1
        return repos
    
    def create_issue(self, owner, repo, title, body=""):
        """Create an issue in a repository."""
        response = self.session.post(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            json={"title": title, "body": body}
        )
        response.raise_for_status()
        return response.json()

# Usage:
# gh = GitHubAPI(token=os.environ.get("GITHUB_TOKEN"))
# user = gh.get_user("octocat")
# print(f"Name: {user['name']}, Repos: {user['public_repos']}")
```

**Why use `requests.Session()`:** A session reuses the same connection and headers across multiple requests. This is faster and cleaner than passing headers to every call.

---

## Exercises

**Exercise 1:** Write a script that takes a GitHub username as a command-line argument and prints their name, location, and number of public repos.

**Exercise 2:** Write a script that searches GitHub for repositories matching a keyword (using the search API) and prints the top 10 results with their star counts.

**Exercise 3:** Write a function that checks if a website is up by making a GET request and checking the status code. Test it with several URLs. Include timeout handling.

**Exercise 4:** Build a simple weather checker using a free weather API (like wttr.in): `requests.get("https://wttr.in/London?format=j1")`. Parse the JSON and print the current temperature and conditions.

---

## Common Mistakes

### 1. Not Handling Errors

```python
# Bad — crashes if the server is down
response = requests.get("https://api.example.com/data")
data = response.json()

# Good — handle errors
try:
    response = requests.get("https://api.example.com/data", timeout=5)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"API call failed: {e}")
```

### 2. Hardcoding API Tokens

```python
# Bad — token visible in code and version control
headers = {"Authorization": "token ghp_abc123secret"}

# Good — use environment variables
import os
token = os.environ.get("GITHUB_TOKEN")
```

### 3. Not Setting Timeouts

```python
# Bad — hangs forever if server does not respond
response = requests.get("https://api.example.com/data")

# Good — fails after 10 seconds
response = requests.get("https://api.example.com/data", timeout=10)
```

### 4. Ignoring Rate Limits

Making thousands of requests without checking rate limits will get your IP or token blocked. Always check `X-RateLimit-Remaining` headers and add delays between requests.

### 5. Not Using Sessions for Multiple Requests

```python
# Bad — creates a new connection each time
for i in range(100):
    response = requests.get(url, headers=headers)

# Good — reuses connections
session = requests.Session()
session.headers.update(headers)
for i in range(100):
    response = session.get(url)
```

---

## Summary

| Concept | Code | Notes |
|---------|------|-------|
| GET request | `requests.get(url)` | Read data |
| POST request | `requests.post(url, json=data)` | Create data |
| PUT request | `requests.put(url, json=data)` | Update data |
| DELETE request | `requests.delete(url)` | Remove data |
| Parse JSON | `response.json()` | Returns dict |
| Status code | `response.status_code` | 200 = success |
| Check errors | `response.raise_for_status()` | Raises on 4xx/5xx |
| Query params | `params={"key": "value"}` | Added to URL |
| Headers | `headers={"Auth": "token"}` | Sent with request |
| Timeout | `timeout=5` | Seconds to wait |
| Session | `requests.Session()` | Reuse connections |

---

[Previous: Module 07 — CLI Tool Development](07-python-cli-tool-development.md) | [Next: Module 09 — Git Automation](09-git-automation-with-python.md)
