# Architecture

Internet (client)
     │
     ▼
Internet Gateway (IGW) attached to VPC
     │
     ▼
Application Load Balancer (ALB) — internet-facing (ENIs in Public Subnets A & B)
     │  (Listener: HTTP 80)
     ▼
Target Group (HTTP: 80, Health-check: /predict)
     │
     ▼
Auto Scaling Group (ASG)
     │
     ▼
EC2 Instance (in a Public Subnet)  ──>  Nginx (listen :80) ── proxy_pass──>  Gunicorn (127.0.0.1:6000) ──> WSGI app (/predict)
