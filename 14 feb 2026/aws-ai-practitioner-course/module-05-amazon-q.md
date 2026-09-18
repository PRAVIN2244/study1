# Module 5: Amazon Q

## 5.1 Amazon Q Business

A fully managed Gen-AI assistant for your employees, built on Amazon Bedrock. It answers questions, provides summaries, generates content, and automates tasks based on your company's knowledge and data.

> You cannot choose the underlying FM — Amazon Q Business manages this for you.

### What Employees Can Ask

```
┌──────────┐     ┌──────────────────┐     ┌──────────────────────┐
│ Employee │────>│ Amazon Q Business│────>│ Company's Internal   │
│          │     │                  │     │ Data                 │
│          │◄────│                  │◄────│                      │
└──────────┘     └──────────────────┘     └──────────────────────┘
```

Example questions:
- "Write a job posting for a Senior Product Marketing Manager role"
- "Create a social media post under 50 words to advertise the new role"
- "What was discussed during the team meetings in the week of 4/12?"
- "Submit a time-off request for next Friday"
- "Send a meeting invite to the design team for Tuesday at 2pm"

### Data Connectors (Fully Managed RAG)

Amazon Q Business connects to **40+ enterprise data sources** using built-in data connectors:

```
┌──────────────────┐     ┌──────────────────────────────────────┐
│ Amazon Q Business│◄────│ Data Sources (crawl via connectors)  │
│                  │     │                                      │
│                  │     │ AWS:        S3, RDS, Aurora, WorkDocs │
│                  │     │ Microsoft:  365, SharePoint           │
│                  │     │ Google:     GDrive, Gmail             │
│                  │     │ Other:      Salesforce, Slack         │
│                  │     │             Confluence, and more...   │
└──────────────────┘     └──────────────────────────────────────┘
```

### Plugins (3rd Party Integrations)

Plugins allow Amazon Q Business to **interact with** (not just read from) third-party services:

| Plugin Type | Examples | What It Does |
|------------|---------|-------------|
| **Built-in Plugins** | Jira, ServiceNow, Zendesk, Salesforce | Send issues, create tickets, update records |
| **Custom Plugins** | Any 3rd party application | Connect via APIs to any service |

### Authentication with IAM Identity Center

```
┌───────┐     ┌──────────────────┐     ┌──────────────────┐
│ Users │────>│ IAM Identity     │────>│ Amazon Q Business│
│       │     │ Center           │     │ (Web Application)│
│       │     │                  │     │                  │
│       │     │ Authentication   │     │ Users receive    │
│       │     │                  │     │ responses only   │
│       │     │ External IdPs:   │     │ from documents   │
│       │     │ - Google Login   │     │ they have access │
│       │     │ - Microsoft AD   │     │ to               │
└───────┘     └──────────────────┘     └──────────────────┘
```

- Users authenticate through IAM Identity Center
- Responses are generated **only from documents the user has access to** (respects permissions)
- IAM Identity Center can integrate with external Identity Providers (Google, Microsoft AD)

### Admin Controls (Guardrails)

| Control | Description |
|---------|-------------|
| **Block words/topics** | Prevent responses about specific subjects (e.g., "Gaming Consoles") |
| **Internal-only responses** | Respond only with internal information (vs. using external knowledge) |
| **Global controls** | Apply to all topics |
| **Topic-level controls** | More granular rules for specific subjects |

**Example:**
```
Employee: "How can I configure a brand new Nintendo Switch?"
Amazon Q:  "Sorry, but this is a restricted topic."
           (Gaming Consoles is a blocked topic)
```

### Step-by-Step: Set Up Amazon Q Business (via Console UI)

1. **Navigate to Amazon Q Business**
   - AWS Console → Search **"Amazon Q Business"** → Click the service

2. **Create an Application**
   - Click **"Create application"**
   - Enter application name (e.g., "Company Knowledge Base")
   - Select a service role (or let AWS create one)
   - Click **"Create"**

3. **Connect a Data Source**
   - Click **"Add data source"**
   - Choose a connector (e.g., **Amazon S3**, **Confluence**, **SharePoint**)
   - Configure the connection (bucket name, URL, credentials)
   - Click **"Add data source"**

4. **Sync Data**
   - Click **"Sync now"** to index your documents
   - Wait for sync to complete

5. **Configure Admin Controls**
   - Go to **"Admin controls"**
   - Add blocked topics (e.g., "Gaming Consoles", "Competitor Products")
   - Set response scope (internal-only or allow external knowledge)

6. **Set Up Authentication**
   - Configure **IAM Identity Center** integration
   - Add users or connect external IdP

7. **Test the Assistant**
   - Click **"Preview web experience"**
   - Ask: "What is our company's vacation policy?"
   - Verify the response includes source citations

### Amazon Q Apps (No-Code Gen-AI Apps)

Create Gen-AI-powered applications **without coding** using natural language:

- Leverages your company's internal data
- Can use plugins (Jira, etc.)
- Build custom workflows and tools for your team

### Real-Life Use Case

> **Example: HR Self-Service**
> A company connects Amazon Q Business to their HR policy documents in S3, their Confluence wiki, and their Jira instance. Employees can ask "How many vacation days do I get after 2 years?" and get an instant answer with a source link. They can also say "Submit a time-off request for next Friday" and Q Business creates the request via the Jira plugin.

---

## 5.2 Amazon Q Developer

An AI assistant for developers that helps with AWS infrastructure, coding, debugging, and cost management.

### 5.2.1 AWS Console Features

| Feature | What It Does |
|---------|-------------|
| **AWS Documentation Q&A** | Answer questions about AWS services and service selection |
| **Account Resources** | Answer questions about resources in your AWS account |
| **CLI Suggestions** | Suggest CLI commands to make changes to your account |
| **Bill Analysis** | Help understand and analyze your AWS costs |
| **Error Resolution** | Help resolve errors and troubleshoot issues |

**Example:**
```
Developer: "List all of my Lambda functions"
Amazon Q:   "You have 5 AWS Lambda resources in us-east-1:
             - test-function-1
             - test-function-2
             - ..."
```

### 5.2.2 IDE Code Companion

Amazon Q Developer integrates with IDEs to help with software development (similar to GitHub Copilot):

| Feature | Description |
|---------|-------------|
| **Code Suggestions** | Real-time code completions and generation |
| **Security Scans** | Scan code for security vulnerabilities |
| **Debugging** | Identify and fix bugs |
| **Optimizations** | Suggest performance improvements |
| **Code Generation** | Generate code from natural language descriptions |
| **Software Agent** | Implement features, generate documentation, bootstrap projects |

**Supported Languages:** Java, JavaScript, Python, TypeScript, C#, and more.

**Supported IDEs:**

| IDE | Integration |
|-----|-------------|
| **Visual Studio Code** | Extension |
| **Visual Studio** | Extension |
| **JetBrains IDEs** | Plugin |

### Step-by-Step: Use Amazon Q Developer in VS Code

1. **Install the Extension**
   - Open VS Code → Extensions (Ctrl+Shift+X)
   - Search **"Amazon Q"** → Click **"Install"**

2. **Sign In**
   - Click the Amazon Q icon in the sidebar
   - Choose **"Use for Free"** (with Builder ID) or sign in with AWS account
   - Complete authentication

3. **Get Code Suggestions**
   - Open a Python file
   - Type a comment:
     ```python
     # Function to upload a file to S3 with error handling
     ```
   - Press Enter — Amazon Q suggests the complete function
   - Press **Tab** to accept

4. **Chat with Amazon Q**
   - Click the chat icon in the sidebar
   - Ask: "Explain this function" (with code selected)
   - Or: "Write unit tests for this function"

5. **Run Security Scan**
   - Right-click in the editor → **"Run Amazon Q Security Scan"**
   - View detected vulnerabilities with remediation suggestions

### Step-by-Step: Use Amazon Q Developer in AWS Console

1. **Open Amazon Q in the Console**
   - Go to [https://console.aws.amazon.com](https://console.aws.amazon.com)
   - Look for the **Amazon Q icon** (chat bubble) in the bottom-right corner
   - Click it to open the chat panel

2. **Ask AWS Questions**
   - Type: "How do I create an S3 bucket with versioning enabled?"
   - Amazon Q provides step-by-step instructions

3. **Understand Costs**
   - Type: "Why did my AWS bill increase last month?"
   - Amazon Q analyzes your billing data and explains cost changes

4. **Troubleshoot Errors**
   - Type: "I'm getting an AccessDenied error on my S3 bucket"
   - Amazon Q suggests IAM policy changes

---

## 5.3 Amazon Q for Other AWS Services

### Amazon Q for QuickSight

| Feature | Description |
|---------|-------------|
| **Natural Language Q&A** | Ask questions about your data in plain English |
| **Executive Summaries** | Generate summaries of your dashboards |
| **Visual Generation** | Generate and edit visuals for dashboards |

> Amazon QuickSight is used to visualize data and create dashboards. Amazon Q understands natural language to help you interact with your data.

### Amazon Q for EC2

| Feature | Description |
|---------|-------------|
| **Instance Selection** | Provides guidance on EC2 instance types best suited to your workload |
| **Natural Language** | Describe your requirements in plain language to get suggestions |
| **Workload Advice** | Ask for advice by providing workload requirements |

### Amazon Q for AWS Chatbot

| Feature | Description |
|---------|-------------|
| **Slack/Teams Integration** | Deploy an AWS Chatbot in Slack or Microsoft Teams |
| **Troubleshooting** | Troubleshoot issues directly in chat |
| **Notifications** | Receive alarms, security findings, billing alerts |
| **Support Requests** | Create AWS support requests from chat |
| **Amazon Q Access** | Access Amazon Q directly in AWS Chatbot |

### Amazon Q for AWS Glue

AWS Glue is an ETL (Extract, Transform, Load) service for moving data between systems.

| Feature | Description |
|---------|-------------|
| **Chat** | Answer general questions about Glue, provide documentation links |
| **Code Generation** | Generate AWS Glue ETL scripts, answer questions about existing scripts |
| **Troubleshooting** | Understand errors in Glue jobs, provide step-by-step resolution |

---

## 5.4 PartyRock

A Gen-AI app-building playground powered by Amazon Bedrock.

| Feature | Description |
|---------|-------------|
| **No Coding Required** | Build Gen-AI apps using a visual interface |
| **No AWS Account Required** | Free to experiment |
| **Multiple FMs** | Experiment with various foundation models |
| **Similar to Q Apps** | UI similar to Amazon Q Apps but with less setup |

**URL:** [https://partyrock.aws/](https://partyrock.aws/)

### Real-Life Use Case

> **Example: Rapid Prototyping**
> A product manager wants to test whether an AI-powered "meeting notes summarizer" would be useful for their team. They use PartyRock to build a prototype in 10 minutes — no coding, no AWS account. After validating the concept with their team, they build the production version using Amazon Bedrock and Q Business.

---

## 5.5 Amazon Q vs. Other AWS AI Services

| Feature | Amazon Q Business | Amazon Q Developer | Amazon Bedrock |
|---------|------------------|-------------------|----------------|
| **Purpose** | Enterprise Q&A and task automation | Code assistance and AWS help | Build custom Gen-AI apps |
| **Target User** | Business users, employees | Software developers | ML engineers, developers |
| **Data Sources** | 40+ enterprise connectors | Code repos, AWS account | Custom training data |
| **Customization** | Admin controls, plugins | IDE integration | Fine-tune models, RAG, agents |
| **FM Selection** | Managed (you can't choose) | Managed | You choose the FM |

---

## Module 5 Summary

| Concept | Key Takeaway |
|---------|-------------|
| Amazon Q Business | Fully managed Gen-AI assistant for employees; built on Bedrock |
| Data Connectors | 40+ connectors: S3, RDS, SharePoint, Confluence, Slack, Gmail, etc. |
| Plugins | Interact with Jira, ServiceNow, Zendesk, Salesforce, custom APIs |
| IAM Identity Center | Authentication; users only see documents they have access to |
| Admin Controls | Block topics, restrict to internal data, global and topic-level rules |
| Amazon Q Apps | No-code Gen-AI apps using natural language |
| Amazon Q Developer | AI code companion + AWS console assistant |
| IDE Integration | VS Code, Visual Studio, JetBrains — code suggestions, security scans |
| Q for QuickSight | Natural language data Q&A, dashboard summaries |
| Q for EC2 | Instance type recommendations based on workload |
| Q for AWS Chatbot | Slack/Teams integration for troubleshooting and notifications |
| Q for Glue | ETL script generation and troubleshooting |
| PartyRock | No-code Gen-AI playground — no AWS account needed |

---

*Previous: [Module 4 — Prompt Engineering](module-04-prompt-engineering.md)*
*Next: [Module 6 — AI and Machine Learning](module-06-ai-and-machine-learning.md)*
