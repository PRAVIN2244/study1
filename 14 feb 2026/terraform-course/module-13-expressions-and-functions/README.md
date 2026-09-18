# Module 13: Expressions and Functions

## Level: ADVANCED | Estimated Time: 3 hours

---

## 13.1 The Terraform Console

The `terraform console` command opens an interactive REPL where you can test expressions and functions without creating resources.

```bash
terraform console
```

**Interactive Session:**
```
> max(1, 31, 12)
31

> upper("hello")
"HELLO"

> split("a", "tomato")
tolist(["tom", "to"])

> substr("hello world", 1, 4)
"ello"

> index(["a", "b", "c"], "b")
1

> length("adam")
4

> length(["ab", "bc"])
2

> lookup({a="1", b="2"}, "a", "novalue")
"1"

> lookup({a="1", b="2"}, "c", "novalue")
"novalue"

> cidrsubnet("10.0.0.0/16", 8, 1)
"10.0.1.0/24"

> formatdate("YYYY-MM-DD", timestamp())
"2024-01-15"

> exit
```

If you have a Terraform project initialized, the console can also access variables and resource attributes:

```bash
# In a project directory with main.tf
terraform console
```

```
> var.environment
"dev"

> local.common_tags
{
  "Environment" = "dev"
  "ManagedBy"   = "terraform"
}
```

> Use `terraform console` to experiment with functions before putting them in your config. Press `Ctrl+D` or type `exit` to quit.

---

## 13.2 For Expressions

Transform collections into new collections.

### List Comprehension

```hcl
# Transform a list
locals {
  names = ["alice", "bob", "charlie"]

  # Uppercase all names
  upper_names = [for name in local.names : upper(name)]
  # → ["ALICE", "BOB", "CHARLIE"]

  # With index
  indexed_names = [for i, name in local.names : "${i}: ${name}"]
  # → ["0: alice", "1: bob", "2: charlie"]

  # With filter
  long_names = [for name in local.names : upper(name) if length(name) > 3]
  # → ["ALICE", "CHARLIE"]
}
```

### Map Comprehension

```hcl
locals {
  instances = {
    web    = "t2.micro"
    api    = "t2.small"
    worker = "t2.medium"
  }

  # Transform map values
  instance_descriptions = {
    for name, type in local.instances : name => "Server ${name} uses ${type}"
  }
  # → { web = "Server web uses t2.micro", api = "Server api uses t2.small", ... }

  # Filter a map
  small_instances = {
    for name, type in local.instances : name => type if type == "t2.micro"
  }
  # → { web = "t2.micro" }

  # Swap keys and values
  type_to_name = {
    for name, type in local.instances : type => name
  }
  # → { "t2.micro" = "web", "t2.small" = "api", "t2.medium" = "worker" }
}
```

### Grouping with `...`

```hcl
locals {
  users = [
    { name = "alice",   role = "admin" },
    { name = "bob",     role = "dev" },
    { name = "charlie", role = "dev" },
    { name = "diana",   role = "admin" },
  ]

  # Group users by role
  users_by_role = {
    for user in local.users : user.role => user.name...
  }
  # → { admin = ["alice", "diana"], dev = ["bob", "charlie"] }
}
```

---

## 13.3 Splat Expressions

Shorthand for extracting attributes from lists:

```hcl
resource "aws_instance" "web" {
  count         = 3
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

# Splat expression (shorthand)
output "instance_ids" {
  value = aws_instance.web[*].id
  # → ["i-abc", "i-def", "i-ghi"]
}

# Equivalent for expression
output "instance_ids_for" {
  value = [for instance in aws_instance.web : instance.id]
}

# Nested splat
output "private_ips" {
  value = aws_instance.web[*].private_ip
}
```

---

## 13.4 Built-in Functions

### String Functions

```hcl
locals {
  # format - printf-style formatting
  formatted = format("Hello, %s! You have %d items.", "Alice", 5)
  # → "Hello, Alice! You have 5 items."

  # join - concatenate list elements
  joined = join(", ", ["a", "b", "c"])
  # → "a, b, c"

  # split - split string into list
  parts = split(",", "a,b,c")
  # → ["a", "b", "c"]

  # replace - string replacement
  cleaned = replace("hello-world_v2", "/[-_]/", ".")
  # → "hello.world.v2"

  # substr - substring
  short = substr("Hello, World!", 0, 5)
  # → "Hello"

  # trimspace - remove leading/trailing whitespace
  trimmed = trimspace("  hello  ")
  # → "hello"

  # lower / upper / title
  low   = lower("HELLO")    # → "hello"
  up    = upper("hello")    # → "HELLO"
  title_case = title("hello world")  # → "Hello World"

  # regex - extract with regex
  matched = regex("^([a-z]+)-([0-9]+)$", "server-42")
  # → ["server", "42"]

  # regexall - find all matches
  all_numbers = regexall("[0-9]+", "server-1-zone-2-rack-3")
  # → ["1", "2", "3"]

  # startswith / endswith
  is_prod = startswith("prod-server", "prod")  # → true
  is_json = endswith("config.json", ".json")   # → true

  # trimsuffix / trimprefix — remove known prefix/suffix
  domain    = trimsuffix("example.com.", ".")     # → "example.com"
  no_prefix = trimprefix("sg-abc123", "sg-")      # → "abc123"

  # Real-world: Clean trailing dot from Route53 zone name
  # data.aws_route53_zone.main.name returns "example.com."
  # clean_domain = trimsuffix(data.aws_route53_zone.main.name, ".")
  # → "example.com"

  # trim — remove specific characters from both ends
  cleaned_id = trim("##instance-42##", "#")  # → "instance-42"
}
```

### Numeric Functions

```hcl
locals {
  # min / max
  smallest = min(5, 3, 8, 1)   # → 1
  largest  = max(5, 3, 8, 1)   # → 8

  # ceil / floor
  rounded_up   = ceil(4.3)     # → 5
  rounded_down = floor(4.7)    # → 4

  # abs
  positive = abs(-42)          # → 42

  # parseint
  decimal = parseint("FF", 16) # → 255

  # pow
  squared = pow(2, 10)         # → 1024
}
```

### Collection Functions

```hcl
locals {
  list1 = [1, 2, 3]
  list2 = [3, 4, 5]
  map1  = { a = 1, b = 2 }
  map2  = { b = 3, c = 4 }

  # length
  len = length(local.list1)    # → 3

  # concat - merge lists
  merged_list = concat(local.list1, local.list2)
  # → [1, 2, 3, 3, 4, 5]

  # merge - merge maps (later values win)
  merged_map = merge(local.map1, local.map2)
  # → { a = 1, b = 3, c = 4 }

  # flatten - flatten nested lists
  flat = flatten([["a", "b"], ["c"], ["d", "e"]])
  # → ["a", "b", "c", "d", "e"]

  # distinct - remove duplicates
  unique = distinct([1, 2, 2, 3, 3, 3])
  # → [1, 2, 3]

  # sort
  sorted = sort(["banana", "apple", "cherry"])
  # → ["apple", "banana", "cherry"]

  # reverse
  reversed = reverse([1, 2, 3])
  # → [3, 2, 1]

  # contains
  has_two = contains(local.list1, 2)  # → true

  # index - find position
  pos = index(["a", "b", "c"], "b")  # → 1

  # element - get by index (wraps around)
  elem = element(["a", "b", "c"], 4)  # → "b" (4 % 3 = 1)

  # slice
  sliced = slice(["a", "b", "c", "d"], 1, 3)
  # → ["b", "c"]

  # chunklist - split into chunks
  chunks = chunklist(["a", "b", "c", "d", "e"], 2)
  # → [["a", "b"], ["c", "d"], ["e"]]

  # keys / values
  k = keys(local.map1)    # → ["a", "b"]
  v = values(local.map1)  # → [1, 2]

  # lookup - get map value with default
  val = lookup(local.map1, "c", "default")  # → "default"

  # zipmap - create map from two lists
  zipped = zipmap(["name", "age"], ["Alice", "30"])
  # → { name = "Alice", age = "30" }

  # setintersection / setunion / setsubtract
  common     = setintersection(toset(local.list1), toset(local.list2))  # → [3]
  all_values = setunion(toset(local.list1), toset(local.list2))         # → [1,2,3,4,5]
  only_in_1  = setsubtract(toset(local.list1), toset(local.list2))      # → [1,2]
}
```

### Type Conversion Functions

```hcl
locals {
  # tostring / tonumber / tobool
  str  = tostring(42)       # → "42"
  num  = tonumber("42")     # → 42
  bool = tobool("true")     # → true

  # tolist / toset / tomap
  as_list = tolist(toset([3, 1, 2]))  # → [1, 2, 3]
  as_set  = toset([1, 2, 2, 3])      # → toset([1, 2, 3])

  # try - return first non-error expression
  safe_value = try(var.optional_map.key, "default")

  # can - test if expression is valid
  is_valid = can(regex("^[a-z]+$", var.name))
}
```

### Encoding Functions

```hcl
locals {
  # jsonencode / jsondecode
  json_string = jsonencode({ name = "Alice", age = 30 })
  # → '{"age":30,"name":"Alice"}'

  parsed = jsondecode("{\"name\":\"Alice\"}")
  # → { name = "Alice" }

  # yamlencode / yamldecode
  yaml_string = yamlencode({ name = "Alice", items = ["a", "b"] })

  # base64encode / base64decode
  encoded = base64encode("Hello, World!")
  # → "SGVsbG8sIFdvcmxkIQ=="

  decoded = base64decode("SGVsbG8sIFdvcmxkIQ==")
  # → "Hello, World!"

  # templatefile - render a template
  user_data = templatefile("${path.module}/templates/init.sh.tpl", {
    environment = var.environment
    db_host     = aws_rds_instance.main.endpoint
  })
}
```

### Filesystem Functions

```hcl
locals {
  # file - read file content
  ssh_key = file("${path.module}/keys/deployer.pub")

  # fileexists - check if file exists
  has_config = fileexists("${path.module}/config.json")

  # templatefile - render template with variables
  config = templatefile("${path.module}/templates/config.json.tpl", {
    region      = var.region
    environment = var.environment
  })

  # fileset - find files matching pattern
  scripts = fileset("${path.module}/scripts", "*.sh")
  # → toset(["setup.sh", "deploy.sh", "cleanup.sh"])

  # filebase64 - read file as base64
  lambda_zip = filebase64("${path.module}/lambda.zip")

  # abspath - absolute path
  abs = abspath(path.module)

  # dirname / basename
  dir  = dirname("/path/to/file.txt")   # → "/path/to"
  base = basename("/path/to/file.txt")  # → "file.txt"

  # pathexpand - expand ~ to home directory
  home = pathexpand("~/.ssh/id_rsa")
}
```

### IP Network Functions

```hcl
locals {
  # cidrhost - calculate host IP in CIDR
  first_host = cidrhost("10.0.1.0/24", 1)    # → "10.0.1.1"
  last_host  = cidrhost("10.0.1.0/24", 254)  # → "10.0.1.254"

  # cidrsubnet - calculate subnet CIDR
  subnet_0 = cidrsubnet("10.0.0.0/16", 8, 0)   # → "10.0.0.0/24"
  subnet_1 = cidrsubnet("10.0.0.0/16", 8, 1)   # → "10.0.1.0/24"
  subnet_10 = cidrsubnet("10.0.0.0/16", 8, 10) # → "10.0.10.0/24"

  # cidrnetmask
  netmask = cidrnetmask("10.0.0.0/16")  # → "255.255.0.0"

  # Real-world: Generate subnet CIDRs dynamically
  subnet_cidrs = [for i in range(4) : cidrsubnet("10.0.0.0/16", 8, i)]
  # → ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}
```

### Date and Time Functions

```hcl
locals {
  # timestamp - current UTC time
  now = timestamp()
  # → "2024-01-15T10:30:00Z"

  # timeadd - add duration
  one_hour_later = timeadd(timestamp(), "1h")
  one_week_later = timeadd(timestamp(), "168h")

  # formatdate
  readable = formatdate("YYYY-MM-DD hh:mm:ss", timestamp())
  # → "2024-01-15 10:30:00"

  date_only = formatdate("YYYY-MM-DD", timestamp())
  # → "2024-01-15"
}
```

---

## 13.5 Template Files

### Template Syntax

```bash
# templates/user_data.sh.tpl

#!/bin/bash
set -e

echo "Setting up ${server_name} in ${environment}"

# Install packages
%{ for pkg in packages ~}
yum install -y ${pkg}
%{ endfor ~}

# Configure application
cat > /etc/myapp/config.json <<'CONFIG'
${jsonencode({
  environment = environment
  database    = db_endpoint
  port        = app_port
  features    = features
})}
CONFIG

%{ if environment == "prod" ~}
# Production-specific setup
systemctl enable monitoring-agent
systemctl start monitoring-agent
%{ endif ~}

systemctl start myapp
```

```hcl
# Using the template
resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  user_data = templatefile("${path.module}/templates/user_data.sh.tpl", {
    server_name = "app-server"
    environment = var.environment
    packages    = ["httpd", "php", "mysql"]
    db_endpoint = aws_rds_instance.main.endpoint
    app_port    = 8080
    features    = { logging = true, caching = false }
  })
}
```

---

## 13.6 Real-Life Example: Dynamic Subnet Calculator

```hcl
variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "availability_zones" {
  default = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

locals {
  az_count = length(var.availability_zones)

  # Generate public subnets: 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24
  public_subnets = {
    for i, az in var.availability_zones :
    az => {
      cidr = cidrsubnet(var.vpc_cidr, 8, i)
      az   = az
      name = "public-${az}"
    }
  }

  # Generate private subnets: 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24
  private_subnets = {
    for i, az in var.availability_zones :
    az => {
      cidr = cidrsubnet(var.vpc_cidr, 8, i + 10)
      az   = az
      name = "private-${az}"
    }
  }

  # All subnets combined
  all_subnets = merge(
    { for k, v in local.public_subnets : "public-${k}" => merge(v, { public = true }) },
    { for k, v in local.private_subnets : "private-${k}" => merge(v, { public = false }) }
  )
}

resource "aws_subnet" "all" {
  for_each = local.all_subnets

  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = each.value.public

  tags = {
    Name = each.value.name
    Tier = each.value.public ? "public" : "private"
  }
}
```

---

## 13.7 The `try` and `can` Functions

### try — Safe Access with Fallback

```hcl
locals {
  # Safely access nested values
  db_port = try(var.database_config.port, 5432)

  # Chain of fallbacks
  instance_type = try(
    var.override_instance_type,
    var.env_config[var.environment].instance_type,
    "t3.micro"
  )

  # Safe JSON parsing
  config = try(jsondecode(file("config.json")), {})
}
```

### can — Test Without Failing

```hcl
variable "email" {
  type = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email))
    error_message = "Must be a valid email address."
  }
}

locals {
  # Check if a value is a valid CIDR
  is_valid_cidr = can(cidrhost(var.cidr_block, 0))

  # Check if a key exists in a map
  has_prod = can(var.config["prod"])
}
```

---

## Exercises

### Exercise 13.1: Collection Transformation
Given a list of server configs, use `for` expressions to:
1. Extract all server names
2. Create a map of name → IP
3. Filter only servers with `role = "web"`
4. Group servers by role

### Exercise 13.2: Subnet Calculator
Write a configuration that takes a VPC CIDR and number of AZs, then automatically calculates public and private subnet CIDRs using `cidrsubnet`.

### Exercise 13.3: Template File
Create a template that generates an nginx configuration file with:
- Dynamic upstream servers from a variable
- Conditional SSL configuration
- Environment-specific settings

### Exercise 13.4: Function Chaining
Use a combination of `flatten`, `distinct`, `sort`, and `join` to process a complex nested data structure into a single formatted string.

---

## Key Takeaways

- `for` expressions transform lists and maps into new collections
- Splat expressions (`[*]`) are shorthand for simple list transformations
- Terraform has 100+ built-in functions across string, numeric, collection, encoding, filesystem, network, and date categories
- `templatefile` renders templates with variables and control flow
- `try` provides safe access with fallbacks; `can` tests expressions without failing
- `cidrsubnet` is essential for dynamic network planning
- Functions cannot be user-defined — only built-in functions are available

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Expressions Overview | [developer.hashicorp.com/terraform/language/expressions](https://developer.hashicorp.com/terraform/language/expressions) |
| `terraform console` | [developer.hashicorp.com/terraform/cli/commands/console](https://developer.hashicorp.com/terraform/cli/commands/console) |
| For Expressions | [developer.hashicorp.com/terraform/language/expressions/for](https://developer.hashicorp.com/terraform/language/expressions/for) |
| Splat Expressions | [developer.hashicorp.com/terraform/language/expressions/splat](https://developer.hashicorp.com/terraform/language/expressions/splat) |
| Conditional Expressions | [developer.hashicorp.com/terraform/language/expressions/conditionals](https://developer.hashicorp.com/terraform/language/expressions/conditionals) |
| Built-in Functions — Full Index | [developer.hashicorp.com/terraform/language/functions](https://developer.hashicorp.com/terraform/language/functions) |
| String Functions | [developer.hashicorp.com/terraform/language/functions#string-functions](https://developer.hashicorp.com/terraform/language/functions#string-functions) |
| Collection Functions | [developer.hashicorp.com/terraform/language/functions#collection-functions](https://developer.hashicorp.com/terraform/language/functions#collection-functions) |
| Numeric Functions | [developer.hashicorp.com/terraform/language/functions#numeric-functions](https://developer.hashicorp.com/terraform/language/functions#numeric-functions) |
| Date/Time Functions | [developer.hashicorp.com/terraform/language/functions#date-and-time-functions](https://developer.hashicorp.com/terraform/language/functions#date-and-time-functions) |
| Filesystem Functions | [developer.hashicorp.com/terraform/language/functions#filesystem-functions](https://developer.hashicorp.com/terraform/language/functions#filesystem-functions) |
| IP Network Functions | [developer.hashicorp.com/terraform/language/functions#ip-network-functions](https://developer.hashicorp.com/terraform/language/functions#ip-network-functions) |
| Encoding Functions | [developer.hashicorp.com/terraform/language/functions#encoding-functions](https://developer.hashicorp.com/terraform/language/functions#encoding-functions) |
| Hash/Crypto Functions | [developer.hashicorp.com/terraform/language/functions#hash-and-crypto-functions](https://developer.hashicorp.com/terraform/language/functions#hash-and-crypto-functions) |
| Type Conversion Functions | [developer.hashicorp.com/terraform/language/functions#type-conversion-functions](https://developer.hashicorp.com/terraform/language/functions#type-conversion-functions) |
| `templatefile` Function | [developer.hashicorp.com/terraform/language/functions/templatefile](https://developer.hashicorp.com/terraform/language/functions/templatefile) |
| `try` Function | [developer.hashicorp.com/terraform/language/functions/try](https://developer.hashicorp.com/terraform/language/functions/try) |
| `can` Function | [developer.hashicorp.com/terraform/language/functions/can](https://developer.hashicorp.com/terraform/language/functions/can) |
| `lookup` Function | [developer.hashicorp.com/terraform/language/functions/lookup](https://developer.hashicorp.com/terraform/language/functions/lookup) |
| `merge` Function | [developer.hashicorp.com/terraform/language/functions/merge](https://developer.hashicorp.com/terraform/language/functions/merge) |
| `flatten` Function | [developer.hashicorp.com/terraform/language/functions/flatten](https://developer.hashicorp.com/terraform/language/functions/flatten) |
| `cidrsubnet` Function | [developer.hashicorp.com/terraform/language/functions/cidrsubnet](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet) |

---

[← Previous Module](../module-12-provisioners-and-dynamic-blocks/README.md) | [Next Module: Custom Providers →](../module-14-custom-providers-and-plugins/README.md)
