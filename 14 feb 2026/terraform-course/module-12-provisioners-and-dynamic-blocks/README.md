# Module 12: Provisioners and Dynamic Blocks

## Level: ADVANCED | Estimated Time: 3 hours

---

## 12.1 Provisioners

Provisioners execute scripts or commands on resources after creation. They are a **last resort** — prefer cloud-native solutions (user_data, AMIs, configuration management).

> ⚠️ HashiCorp recommends avoiding provisioners when possible. They add complexity and can fail in ways that leave resources in an inconsistent state.

### Types of Provisioners

```
┌──────────────────┬──────────────────────────────────────────┐
│   Provisioner    │   Purpose                                │
├──────────────────┼──────────────────────────────────────────┤
│ local-exec       │ Run command on YOUR machine              │
│ remote-exec      │ Run command on the REMOTE resource       │
│ file             │ Copy files to the remote resource        │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 12.2 local-exec Provisioner

Runs a command on the machine running Terraform:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  # Run after instance is created
  provisioner "local-exec" {
    command = "echo 'Instance ${self.id} created with IP ${self.public_ip}' >> instances.log"
  }
}
```

### With Environment Variables

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  provisioner "local-exec" {
    command = "ansible-playbook -i '${self.public_ip},' playbook.yml"

    environment = {
      ANSIBLE_HOST_KEY_CHECKING = "False"
      ENV                       = var.environment
    }
  }
}
```

### With Different Interpreters

```hcl
# Python script
provisioner "local-exec" {
  command     = "script.py ${self.id}"
  interpreter = ["python3", "-c"]
}

# PowerShell (Windows)
provisioner "local-exec" {
  command     = "Write-Output 'Created: ${self.id}'"
  interpreter = ["PowerShell", "-Command"]
}

# Bash with specific shell
provisioner "local-exec" {
  command     = "process_instance.sh ${self.id}"
  interpreter = ["/bin/bash", "-c"]
  working_dir = "${path.module}/scripts"
}
```

---

## 12.3 remote-exec Provisioner

Runs commands on the remote resource via SSH or WinRM:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  key_name      = aws_key_pair.deployer.key_name

  # Connection details for remote-exec
  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file("~/.ssh/deployer.pem")
    host        = self.public_ip
    timeout     = "5m"
  }

  # Inline commands
  provisioner "remote-exec" {
    inline = [
      "sudo yum update -y",
      "sudo yum install -y httpd",
      "sudo systemctl start httpd",
      "sudo systemctl enable httpd",
      "echo '<h1>Hello from ${self.id}</h1>' | sudo tee /var/www/html/index.html",
    ]
  }
}
```

### Remote-exec with Script

```hcl
provisioner "remote-exec" {
  script = "${path.module}/scripts/setup.sh"
}

# Or multiple scripts
provisioner "remote-exec" {
  scripts = [
    "${path.module}/scripts/install-deps.sh",
    "${path.module}/scripts/configure-app.sh",
    "${path.module}/scripts/start-services.sh",
  ]
}
```

---

## 12.4 file Provisioner

Copies files or directories to the remote resource:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  key_name      = aws_key_pair.deployer.key_name

  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file("~/.ssh/deployer.pem")
    host        = self.public_ip
  }

  # Copy a single file
  provisioner "file" {
    source      = "configs/app.conf"
    destination = "/tmp/app.conf"
  }

  # Copy a directory
  provisioner "file" {
    source      = "scripts/"
    destination = "/tmp/scripts"
  }

  # Copy inline content
  provisioner "file" {
    content     = "DATABASE_URL=${var.db_url}\nAPI_KEY=${var.api_key}"
    destination = "/tmp/.env"
  }

  # Then execute setup
  provisioner "remote-exec" {
    inline = [
      "sudo mv /tmp/app.conf /etc/myapp/app.conf",
      "chmod +x /tmp/scripts/*.sh",
      "/tmp/scripts/setup.sh",
    ]
  }
}
```

---

## 12.5 Provisioner Behavior

### Creation-Time (Default)

```hcl
provisioner "local-exec" {
  command = "echo 'Created!'"
  # Runs only when the resource is CREATED
}
```

### Destroy-Time

```hcl
provisioner "local-exec" {
  when    = destroy
  command = "echo 'Destroying ${self.id}' >> destroy.log"
  # Runs before the resource is DESTROYED
}
```

### Failure Behavior

```hcl
provisioner "local-exec" {
  command    = "might-fail.sh"
  on_failure = continue  # Don't fail the apply if this fails
  # Default is "fail" — which taints the resource
}
```

### What Happens When a Provisioner Fails

```
terraform apply
  → Resource created successfully
  → Provisioner runs... FAILS
  → Resource is TAINTED
  → Next terraform apply will DESTROY and RECREATE the resource
```

---

## 12.6 Alternatives to Provisioners

```
┌──────────────────────┬──────────────────────────────────────┐
│  Instead of...       │  Use...                              │
├──────────────────────┼──────────────────────────────────────┤
│ remote-exec to       │ user_data (cloud-init)               │
│ install software     │                                      │
│                      │                                      │
│ remote-exec to       │ Pre-baked AMIs (Packer)              │
│ configure servers    │                                      │
│                      │                                      │
│ local-exec to call   │ Terraform provider for that API      │
│ an API               │                                      │
│                      │                                      │
│ file provisioner     │ S3 + user_data to download           │
│                      │                                      │
│ remote-exec for      │ Ansible, Chef, Puppet                │
│ config management    │ (triggered after Terraform)          │
└──────────────────────┴──────────────────────────────────────┘
```

```hcl
# ✅ PREFERRED: user_data instead of remote-exec
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
  EOF
}
```

---

## 12.7 null_resource

The `null_resource` is a resource that doesn't create any infrastructure. It's used purely as a container for provisioners or triggers.

```hcl
resource "null_resource" "example" {
  provisioner "local-exec" {
    command = "echo 'This runs without creating any cloud resource'"
  }
}
```

### Use Cases

**Run a script after infrastructure is created:**

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

resource "null_resource" "configure" {
  # Re-run when instance ID changes (i.e., instance is recreated)
  triggers = {
    instance_id = aws_instance.web.id
  }

  provisioner "local-exec" {
    command = "echo '${aws_instance.web.private_ip}' >> inventory.txt"
  }

  provisioner "local-exec" {
    command = "ansible-playbook -i inventory.txt setup.yml"
  }
}
```

**Run a one-time setup command:**

```hcl
resource "null_resource" "init_database" {
  triggers = {
    db_endpoint = aws_rds_instance.main.endpoint
  }

  provisioner "local-exec" {
    command = "mysql -h ${aws_rds_instance.main.endpoint} -u admin -p${var.db_password} < schema.sql"
  }
}
```

> ⚠️ In Terraform 1.4+, consider using `terraform_data` as a replacement for `null_resource`. It's built-in and doesn't require the `hashicorp/null` provider.

```hcl
# Modern alternative to null_resource
resource "terraform_data" "example" {
  triggers_replace = [aws_instance.web.id]

  provisioner "local-exec" {
    command = "echo 'Instance recreated'"
  }
}
```

---

## 12.8 Complete Provisioner Example: All Three Types Together

This example combines `local-exec`, `file`, and `remote-exec` in a single resource:

```hcl
provider "aws" {
  region = "ap-south-1"
}

resource "aws_instance" "example" {
  ami           = "ami-0c1a7f89451184c8b"
  instance_type = "t2.micro"
  key_name      = "mykey"

  # Step 1: Create a script locally
  provisioner "local-exec" {
    command = "echo 'while true; do echo hi-students; sleep 5; done' > myscript.sh"
  }

  # Step 2: Copy the script to the remote server
  provisioner "file" {
    source      = "myscript.sh"
    destination = "/tmp/myscript.sh"
  }

  # Step 3: Execute the script on the remote server
  provisioner "remote-exec" {
    inline = [
      "chmod +x /tmp/myscript.sh",
      "nohup /tmp/myscript.sh 2>&1 &",
    ]
  }

  # Step 4: Log the private IP locally
  provisioner "local-exec" {
    command = "echo ${self.private_ip} >> private_ips.txt"
  }

  # Step 5: Handle failure gracefully
  provisioner "local-exec" {
    command    = "exit 1"
    on_failure = continue  # Don't taint the resource if this fails
  }

  # Step 6: Cleanup on destroy
  provisioner "local-exec" {
    when    = destroy
    command = "rm -f private_ips.txt myscript.sh"
  }

  # Connection block used by file and remote-exec provisioners
  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("mykey.pem")
    host        = self.public_ip
  }
}
```

### Key Points About `self`

- Inside a provisioner, `self` refers to the parent resource
- `self.public_ip` → the instance's public IP
- `self.private_ip` → the instance's private IP
- `self.id` → the instance ID
- `self` is only available inside provisioner and connection blocks

---

## 12.9 Dynamic Blocks

Dynamic blocks generate repeated nested blocks programmatically.

### Static vs Dynamic Blocks — When to Use Which

```
┌──────────────────────┬──────────────────────────────┬──────────────────────────────┐
│                      │  Static Blocks               │  Dynamic Blocks              │
├──────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Definition           │ Written out explicitly in HCL│ Generated from a collection  │
│ Readability          │ Immediately clear             │ Requires understanding loop  │
│ Flexibility          │ Fixed at write time           │ Driven by variables/data     │
│ Maintenance          │ Edit each block individually  │ Change the input collection  │
│ Best for             │ 1-3 blocks, rarely change     │ 3+ blocks, variable count    │
│ Debugging            │ Straightforward               │ Harder (check iterator vals) │
│ Nesting              │ N/A                           │ Supports nested dynamic      │
└──────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

**Rule of thumb:** If the number of blocks is fixed and small (1-3), use static blocks for clarity. If the blocks are driven by input variables, come from a data source, or repeat more than 3 times, use dynamic blocks.

**Static block example:**

```hcl
# Fixed, known at write time — static is fine
resource "aws_security_group" "db" {
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}
```

**Dynamic block equivalent (unnecessary here):**

```hcl
# ❌ Over-engineering for a single block
resource "aws_security_group" "db" {
  dynamic "ingress" {
    for_each = [{ port = 5432, cidr = "10.0.0.0/8" }]
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = [ingress.value.cidr]
    }
  }
}
```

**When dynamic blocks shine — variable number of rules:**

```hcl
# ✅ Number of rules varies per environment
variable "ingress_rules" {
  type = list(object({
    port        = number
    cidr        = string
    description = string
  }))
}

resource "aws_security_group" "app" {
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = [ingress.value.cidr]
    }
  }
}
```

---

### Without Dynamic Blocks (Repetitive)

```hcl
# ❌ Repetitive
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}
```

### With Dynamic Blocks

```hcl
# ✅ Clean and configurable
variable "ingress_rules" {
  default = [
    { port = 80,  cidr = "0.0.0.0/0",  description = "HTTP" },
    { port = 443, cidr = "0.0.0.0/0",  description = "HTTPS" },
    { port = 22,  cidr = "10.0.0.0/8", description = "SSH from internal" },
  ]
}

resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules

    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = [ingress.value.cidr]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### Dynamic Block Syntax

```hcl
dynamic "BLOCK_NAME" {
  for_each = COLLECTION
  iterator = OPTIONAL_ITERATOR_NAME  # defaults to BLOCK_NAME

  content {
    # Use BLOCK_NAME.key and BLOCK_NAME.value
    # Or ITERATOR_NAME.key and ITERATOR_NAME.value
    attribute = BLOCK_NAME.value.something
  }
}
```

### Custom Iterator Name

```hcl
dynamic "ingress" {
  for_each = var.ingress_rules
  iterator = rule  # Use "rule" instead of "ingress"

  content {
    from_port   = rule.value.port
    to_port     = rule.value.port
    protocol    = "tcp"
    cidr_blocks = [rule.value.cidr]
  }
}
```

---

## 12.10 Advanced Dynamic Block Examples

### IAM Policy with Dynamic Statements

```hcl
variable "s3_buckets" {
  default = {
    logs    = { actions = ["s3:GetObject", "s3:PutObject"], prefix = "logs/*" }
    backups = { actions = ["s3:GetObject"], prefix = "backups/*" }
    assets  = { actions = ["s3:GetObject", "s3:ListBucket"], prefix = "*" }
  }
}

data "aws_iam_policy_document" "s3_access" {
  dynamic "statement" {
    for_each = var.s3_buckets

    content {
      sid     = "Access${title(statement.key)}"
      effect  = "Allow"
      actions = statement.value.actions
      resources = [
        "arn:aws:s3:::${statement.key}-bucket",
        "arn:aws:s3:::${statement.key}-bucket/${statement.value.prefix}",
      ]
    }
  }
}
```

### Nested Dynamic Blocks

```hcl
variable "load_balancer_listeners" {
  default = {
    http = {
      port     = 80
      protocol = "HTTP"
      actions = [
        { type = "redirect", redirect_port = "443", redirect_protocol = "HTTPS" }
      ]
    }
    https = {
      port     = 443
      protocol = "HTTPS"
      actions = [
        { type = "forward", target_group_arn = "arn:aws:..." }
      ]
    }
  }
}

resource "aws_lb_listener" "this" {
  for_each = var.load_balancer_listeners

  load_balancer_arn = aws_lb.main.arn
  port              = each.value.port
  protocol          = each.value.protocol

  dynamic "default_action" {
    for_each = each.value.actions

    content {
      type             = default_action.value.type
      target_group_arn = lookup(default_action.value, "target_group_arn", null)

      dynamic "redirect" {
        for_each = default_action.value.type == "redirect" ? [1] : []

        content {
          port        = default_action.value.redirect_port
          protocol    = default_action.value.redirect_protocol
          status_code = "HTTP_301"
        }
      }
    }
  }
}
```

### Conditional Dynamic Blocks

```hcl
variable "enable_logging" {
  type    = bool
  default = true
}

resource "aws_s3_bucket" "this" {
  bucket = "my-bucket"

  dynamic "logging" {
    for_each = var.enable_logging ? [1] : []

    content {
      target_bucket = aws_s3_bucket.logs.id
      target_prefix = "access-logs/"
    }
  }
}
```

---

## 12.11 Dynamic Blocks Best Practices

| Do | Don't |
|----|-------|
| Use for repeated nested blocks | Use for top-level resources (use `for_each`) |
| Keep the logic simple | Nest more than 2 levels deep |
| Use meaningful iterator names | Overuse — sometimes repetition is clearer |
| Document complex dynamic blocks | Use when a simple static block suffices |

---

## Exercises

### Exercise 12.1: Provisioner Practice
Create an EC2 instance with:
1. A `local-exec` provisioner that logs the instance IP
2. A `remote-exec` provisioner that installs nginx
3. A destroy-time provisioner that logs the deletion

### Exercise 12.2: Dynamic Security Group
Create a security group module that accepts a list of rules as a variable and uses dynamic blocks to create them.

### Exercise 12.3: Refactor to Dynamic
Take a configuration with 5+ repeated `ingress` blocks and refactor it to use a dynamic block with a variable.

---

## Key Takeaways

- Provisioners are a last resort — prefer user_data, AMIs, or config management tools
- `local-exec` runs on your machine; `remote-exec` runs on the resource
- Failed provisioners taint the resource for recreation
- Dynamic blocks eliminate repetitive nested blocks
- Use `for_each` in dynamic blocks to iterate over collections
- Keep dynamic blocks simple — deeply nested ones are hard to debug
- Conditional dynamic blocks use `for_each = condition ? [1] : []`

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Provisioners Overview | [developer.hashicorp.com/terraform/language/resources/provisioners/syntax](https://developer.hashicorp.com/terraform/language/resources/provisioners/syntax) |
| `local-exec` Provisioner | [developer.hashicorp.com/terraform/language/resources/provisioners/local-exec](https://developer.hashicorp.com/terraform/language/resources/provisioners/local-exec) |
| `remote-exec` Provisioner | [developer.hashicorp.com/terraform/language/resources/provisioners/remote-exec](https://developer.hashicorp.com/terraform/language/resources/provisioners/remote-exec) |
| `file` Provisioner | [developer.hashicorp.com/terraform/language/resources/provisioners/file](https://developer.hashicorp.com/terraform/language/resources/provisioners/file) |
| Connection Block | [developer.hashicorp.com/terraform/language/resources/provisioners/connection](https://developer.hashicorp.com/terraform/language/resources/provisioners/connection) |
| `null_resource` | [registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) |
| `terraform_data` (Replaces null_resource) | [developer.hashicorp.com/terraform/language/resources/terraform-data](https://developer.hashicorp.com/terraform/language/resources/terraform-data) |
| Dynamic Blocks | [developer.hashicorp.com/terraform/language/expressions/dynamic-blocks](https://developer.hashicorp.com/terraform/language/expressions/dynamic-blocks) |
| `for_each` Meta-Argument | [developer.hashicorp.com/terraform/language/meta-arguments/for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each) |
| `self` Object | [developer.hashicorp.com/terraform/language/resources/provisioners/syntax#the-self-object](https://developer.hashicorp.com/terraform/language/resources/provisioners/syntax#the-self-object) |
| Provisioner `when` (Destroy-Time) | [developer.hashicorp.com/terraform/language/resources/provisioners/syntax#destroy-time-provisioners](https://developer.hashicorp.com/terraform/language/resources/provisioners/syntax#destroy-time-provisioners) |
| Provisioner `on_failure` | [developer.hashicorp.com/terraform/language/resources/provisioners/syntax#failure-behavior](https://developer.hashicorp.com/terraform/language/resources/provisioners/syntax#failure-behavior) |

---

[← Previous Module](../module-11-workspaces-and-environments/README.md) | [Next Module: Expressions and Functions →](../module-13-expressions-and-functions/README.md)
