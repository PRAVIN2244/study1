# Module 11: Serverless Computing

## Certification Relevance: AZ-204 (25-30%)

---

## 11.1 Serverless Concepts

```
Serverless does NOT mean "no servers." It means:
- You don't manage servers
- You write code, Azure runs it
- Auto-scales from 0 to thousands of instances
- Pay only when code executes (per-execution billing)
- No idle costs (scale to zero)

Azure Serverless Services:
├── Azure Functions      → Event-driven code execution
├── Logic Apps           → Visual workflow automation
├── Event Grid           → Event routing service
├── Service Bus          → Enterprise message broker
└── Durable Functions    → Stateful function orchestration
```

---

## 11.2 Azure Functions

### What is Azure Functions?
A serverless compute service that runs small pieces of code (functions) in response to events.

### Triggers and Bindings

```
Trigger = What starts the function (exactly ONE per function)
Binding = Input/output connections to other services (zero or more)

Common Triggers:
├── HTTP          → REST API endpoint
├── Timer         → Scheduled execution (cron)
├── Blob Storage  → File uploaded/modified
├── Queue Storage → Message added to queue
├── Service Bus   → Message received
├── Event Grid    → Event published
├── Cosmos DB     → Document created/modified
└── Event Hub     → Stream event received

Common Bindings:
├── Blob Storage (input/output)
├── Queue Storage (output)
├── Cosmos DB (input/output)
├── Table Storage (input/output)
├── SendGrid (output - email)
└── SignalR (output - real-time)
```

### Hosting Plans

| Plan | Scale | Max Timeout | Cost |
|------|-------|-------------|------|
| **Consumption** | 0 to 200 instances | 5 min (configurable to 10) | Pay per execution |
| **Premium** | 1 to 100 instances | 30 min (unlimited) | Pre-warmed instances |
| **Dedicated** | Manual/auto-scale | Unlimited | App Service Plan pricing |

### Portal UI Walkthrough: Create an Azure Function App

```
PORTAL STEPS — Create a Function App:

Step 1: Navigate to Function App
   → Search "Function App" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     rg-demo-eastus                      │
   └────────────────────────────────────────────────────────┘
   ┌─ Instance Details ─────────────────────────────────────┐
   │ Function App name:  func-demo-2024                      │
   │                     (globally unique — becomes          │
   │                      func-demo-2024.azurewebsites.net)  │
   │ Runtime stack:      Node.js                             │
   │   (Options: .NET, Node.js, Python, Java, PowerShell)   │
   │ Version:            18 LTS                              │
   │ Region:             East US                             │
   │ Operating System:   ● Linux  ○ Windows                  │
   │ Hosting plan:       ● Consumption (Serverless)          │
   │                     ○ Functions Premium                 │
   │                     ○ App Service Plan                  │
   └────────────────────────────────────────────────────────┘

Step 3: Storage Tab
   → Click "Next: Storage >"
   → Storage account: Select existing or create new
   → (Function App needs a storage account for internal state)

Step 4: Networking → Monitoring
   → Click "Next: Networking >" (leave defaults)
   → Click "Next: Monitoring >"
   → Enable Application Insights: ● Yes
   → (This enables performance monitoring for your functions)

Step 5: Review + Create
   → Click "Review + create" → "Create"
   → Deployment takes 1-2 minutes

Step 6: Create Your First Function
   → Click "Go to resource"
   → Left sidebar → "Functions"
   → Click "+ Create"
   ┌─ Create Function ──────────────────────────────────────┐
   │ Development environment: ● Develop in portal            │
   │   (Options: VS Code, Any editor, Portal)               │
   │ Template:               HTTP trigger                    │
   │ New Function:           HttpTrigger1                    │
   │ Authorization level:    Anonymous                       │
   │   (Options: Anonymous, Function, Admin)                │
   │ Click "Create"                                          │
   └────────────────────────────────────────────────────────┘

Step 7: Edit and Test the Function
   → Click "HttpTrigger1" → "Code + Test"
   → You'll see the default code:
     module.exports = async function (context, req) {
       const name = req.query.name || "World";
       context.res = { body: "Hello, " + name + "!" };
     };
   → Click "Test/Run" at the top
   → Method: GET
   → Query parameter: name = Azure
   → Click "Run"
   → Output: "Hello, Azure!"

Step 8: Get the Function URL
   → Click "Get function URL" at the top
   → Copy the URL
   → Open in browser: https://func-demo-2024.azurewebsites.net/api/HttpTrigger1?name=Azure
   → You'll see: "Hello, Azure!"

Step 9: Create a Timer-Triggered Function
   → Go back to Functions → "+ Create"
   → Template: Timer trigger
   → Name: TimerTrigger1
   → Schedule: 0 */5 * * * * (every 5 minutes — CRON format)
   → Click "Create"
   → This function runs automatically every 5 minutes
```

### Portal UI Walkthrough: Create a Logic App

```
PORTAL STEPS — Create a Logic App (No-Code Workflow):

Step 1: Navigate to Logic Apps
   → Search "Logic Apps" in the search bar
   → Click "+ Add"

Step 2: Basics Tab
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-demo-eastus                       │
   │ Logic App name:     logic-email-alert                    │
   │ Region:             East US                              │
   │ Plan type:          ● Consumption (pay per execution)    │
   │                     ○ Standard                           │
   └─────────────────────────────────────────────────────────┘
   → Click "Review + create" → "Create"

Step 3: Design the Workflow
   → Click "Go to resource"
   → Click "Logic app designer" in left sidebar
   → Choose a template or "Blank Logic App"

Step 4: Add a Trigger
   → Search for "Recurrence" → Select "Recurrence" trigger
   → Interval: 1    Frequency: Hour
   → (This runs the workflow every hour)

Step 5: Add an Action
   → Click "+ New step"
   → Search "Send an email" → Select "Office 365 Outlook"
   → Sign in to your Microsoft account
   → Configure:
     To:      your-email@company.com
     Subject: Azure Alert - Hourly Check
     Body:    This is an automated check from Azure Logic Apps

Step 6: Save and Run
   → Click "Save" at the top
   → Click "Run Trigger" → "Run" to test immediately
   → Check your email for the message
```

### Creating Azure Functions with CLI

```bash
# Create a Function App
az functionapp create \
  --resource-group rg-demo-eastus \
  --name func-demo-2024 \
  --consumption-plan-location eastus \
  --runtime node \
  --runtime-version 18 \
  --functions-version 4 \
  --storage-account stprodeastus2024

# Meaning:
# --consumption-plan-location : Use Consumption plan (pay per execution)
# --runtime node              : Node.js runtime
# --functions-version 4       : Azure Functions v4
# --storage-account           : Required for function state/triggers

# Create locally with Azure Functions Core Tools
func init MyFunctionApp --javascript
cd MyFunctionApp
func new --name HttpTrigger --template "HTTP trigger"
```

### Function Code Examples

```javascript
// HTTP Trigger Function (Node.js)
// Responds to HTTP requests like a REST API endpoint

const { app } = require('@azure/functions');

app.http('HttpTrigger', {
    methods: ['GET', 'POST'],
    authLevel: 'anonymous',
    handler: async (request, context) => {
        context.log('HTTP trigger function processed a request.');

        const name = request.query.get('name') || 
                     (await request.json()).name || 
                     'World';

        return {
            body: `Hello, ${name}!`
        };
    }
});

// URL: https://func-demo-2024.azurewebsites.net/api/HttpTrigger?name=Azure
// Output: Hello, Azure!
```

```javascript
// Timer Trigger (runs on schedule)
// Cron expression: second minute hour day month day-of-week

const { app } = require('@azure/functions');

app.timer('TimerTrigger', {
    schedule: '0 */5 * * * *',  // Every 5 minutes
    handler: async (myTimer, context) => {
        context.log('Timer function ran at:', new Date().toISOString());
        
        // Example: Clean up expired sessions
        // Example: Send daily report emails
        // Example: Sync data between systems
    }
});

// Cron examples:
// '0 */5 * * * *'    → Every 5 minutes
// '0 0 * * * *'      → Every hour
// '0 0 9 * * *'      → Every day at 9:00 AM
// '0 0 9 * * 1-5'    → Weekdays at 9:00 AM
// '0 30 9 1 * *'     → 1st of every month at 9:30 AM
```

```javascript
// Blob Trigger (fires when file uploaded to storage)

const { app } = require('@azure/functions');

app.storageBlob('BlobTrigger', {
    path: 'images/{name}',
    connection: 'AzureWebJobsStorage',
    handler: async (blob, context) => {
        context.log(`Blob trigger for: ${context.triggerMetadata.name}`);
        context.log(`Blob size: ${blob.length} bytes`);
        
        // Example: Generate thumbnail
        // Example: Extract text with OCR
        // Example: Scan for viruses
    }
});
```

```python
# Queue Trigger (Python example)
# Processes messages from Azure Queue Storage

import azure.functions as func
import json
import logging

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="order-queue",
                   connection="AzureWebJobsStorage")
def process_order(msg: func.QueueMessage):
    order = json.loads(msg.get_body().decode('utf-8'))
    logging.info(f'Processing order: {order["orderId"]}')
    
    # Process the order
    # Send confirmation email
    # Update inventory
```

### Deploy Functions

```bash
# Deploy from local project
func azure functionapp publish func-demo-2024

# Output:
# Getting site publishing info...
# Uploading package...
# Deployment successful.
# Functions in func-demo-2024:
#     HttpTrigger - [httpTrigger]
#         Invoke url: https://func-demo-2024.azurewebsites.net/api/httptrigger

# Deploy from GitHub (continuous deployment)
az functionapp deployment source config \
  --resource-group rg-demo-eastus \
  --name func-demo-2024 \
  --repo-url https://github.com/myorg/my-functions \
  --branch main

# Set application settings
az functionapp config appsettings set \
  --resource-group rg-demo-eastus \
  --name func-demo-2024 \
  --settings "DATABASE_URL=mongodb://..." "API_KEY=secret123"

# View function logs
func azure functionapp logstream func-demo-2024
```

### Real-World Example
```
Industry Example: Image Processing Pipeline

1. User uploads photo to Blob Storage
2. Blob Trigger fires → Azure Function processes image
3. Function generates thumbnail → saves to "thumbnails" container
4. Function extracts metadata → writes to Cosmos DB
5. Function sends notification → Queue message to notification service
6. Queue Trigger fires → sends email to user

Cost for 100,000 images/month:
- Consumption plan: ~$2 (1 million free executions/month)
- Storage: ~$5
- Total: ~$7/month vs. running a VM 24/7 (~$30/month)
```

---

## 11.3 Azure Logic Apps

### What is Logic Apps?
A visual workflow automation service. Build integrations without writing code using a drag-and-drop designer.

```
Logic Apps vs Functions:

Logic Apps:                          Functions:
├── Visual designer (no code)        ├── Code-first
├── 400+ connectors (Office 365,     ├── Custom logic
│   Salesforce, SAP, Twitter)        ├── Low-latency requirements
├── Long-running workflows           ├── Short-lived executions
├── Business process automation      ├── Data processing
└── Integration scenarios            └── API backends
```

### Common Connectors

```
Microsoft:           Third-Party:          On-Premises:
├── Office 365       ├── Salesforce        ├── SQL Server
├── SharePoint       ├── Twitter/X         ├── File System
├── Teams            ├── Slack             ├── SAP
├── Dynamics 365     ├── Mailchimp         ├── Oracle DB
├── Azure Services   ├── Twilio            ├── IBM MQ
└── Power BI         └── GitHub            └── FTP/SFTP
```

### Real-World Example
```
Industry Example: Employee Onboarding Automation

Trigger: When new employee added to HR system (Workday)
Actions:
1. Create user in Entra ID
2. Assign Microsoft 365 license
3. Add to Teams channels
4. Create Jira account
5. Send welcome email via Outlook
6. Create equipment request in ServiceNow
7. Notify manager via Teams

Before Logic Apps: IT manually does 7 steps (2 hours per employee)
After Logic Apps: Fully automated (2 minutes, zero errors)
```

```bash
# Create a Logic App
az logic workflow create \
  --resource-group rg-demo-eastus \
  --name logic-onboarding \
  --location eastus \
  --definition '{
    "definition": {
      "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
      "triggers": {
        "manual": {
          "type": "Request",
          "kind": "Http"
        }
      },
      "actions": {}
    }
  }'

# Most Logic Apps are built in the Portal visual designer
```

---

## 11.4 Azure Event Grid

### What is Event Grid?
A fully managed event routing service that enables event-driven architectures.

```
Event Sources → Event Grid → Event Handlers

Sources:                    Handlers:
├── Blob Storage            ├── Azure Functions
├── Resource Groups         ├── Logic Apps
├── Azure Subscriptions     ├── Event Hubs
├── IoT Hub                 ├── Queue Storage
├── Custom Topics           ├── Webhooks
├── Entra ID                ├── Service Bus
└── Container Registry      └── Automation Runbooks

Example Flow:
Blob uploaded → Event Grid → Azure Function (process image)
                           → Logic App (send notification)
                           → Queue (audit log)
```

```bash
# Create an Event Grid subscription (trigger function when blob created)
az eventgrid event-subscription create \
  --name sub-blob-created \
  --source-resource-id "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Storage/storageAccounts/stprodeastus2024" \
  --endpoint "https://func-demo-2024.azurewebsites.net/api/BlobProcessor" \
  --included-event-types Microsoft.Storage.BlobCreated

# Meaning: When a blob is created in the storage account,
# send an event to the Azure Function endpoint
```

---

## 11.5 Azure Service Bus

```
Service Bus vs Queue Storage:

Queue Storage:                    Service Bus:
├── Simple FIFO queue             ├── Enterprise messaging
├── Max message: 64 KB            ├── Max message: 256 KB (Standard), 100 MB (Premium)
├── Max queue: 500 TB             ├── Topics & Subscriptions (pub/sub)
├── No ordering guarantee         ├── FIFO guarantee (sessions)
├── At-least-once delivery        ├── At-most-once delivery option
├── ~$0.04/million operations     ├── ~$10/month (Standard)
└── Best for: Simple decoupling   └── Best for: Enterprise integration
```

```bash
# Create Service Bus namespace
az servicebus namespace create \
  --resource-group rg-demo-eastus \
  --name sb-demo-2024 \
  --location eastus \
  --sku Standard

# Create a queue
az servicebus queue create \
  --resource-group rg-demo-eastus \
  --namespace-name sb-demo-2024 \
  --name order-queue \
  --max-size 1024

# Create a topic (pub/sub)
az servicebus topic create \
  --resource-group rg-demo-eastus \
  --namespace-name sb-demo-2024 \
  --name order-events

# Create subscriptions to the topic
az servicebus topic subscription create \
  --resource-group rg-demo-eastus \
  --namespace-name sb-demo-2024 \
  --topic-name order-events \
  --name email-notifications

az servicebus topic subscription create \
  --resource-group rg-demo-eastus \
  --namespace-name sb-demo-2024 \
  --topic-name order-events \
  --name inventory-updates
```

---

## 11.6 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Function `cold start` slow | Consumption plan scales from zero | Use Premium plan with pre-warmed instances |
| `Function timeout` | Exceeds plan limit (5/10 min) | Optimize code or use Premium/Dedicated plan |
| `Storage account not found` | Missing AzureWebJobsStorage setting | Set storage connection in app settings |
| Logic App `ActionFailed` | Connector authentication expired | Re-authorize the connector in designer |
| Event Grid `delivery failed` | Endpoint not responding | Check endpoint health; review dead-letter queue |
| `429 Too Many Requests` | Function throttled | Increase plan capacity or add retry logic |
| Service Bus `MessageLockLost` | Processing took too long | Increase lock duration or optimize processing |

---

## 11.7 Practice Questions

### Question 1
**Which Azure Functions plan scales to zero (no cost when idle)?**
- A) Premium
- B) Dedicated
- C) Consumption ✅
- D) All plans

### Question 2
**What is the maximum execution timeout for a Consumption plan function?**
- A) 1 minute
- B) 5 minutes (configurable to 10) ✅
- C) 30 minutes
- D) Unlimited

### Question 3
**Which service provides visual workflow automation with 400+ connectors?**
- A) Azure Functions
- B) Azure Logic Apps ✅
- C) Azure Event Grid
- D) Azure Service Bus

### Question 4
**Event Grid is best described as:**
- A) A message queue
- B) An event routing service ✅
- C) A database
- D) A compute service

### Question 5
**Which messaging service supports Topics and Subscriptions (pub/sub)?**
- A) Queue Storage
- B) Azure Service Bus ✅
- C) Event Grid
- D) Event Hub

---

[← Previous Module](./Module-10-Containers-and-Kubernetes.md) | [Next Module: Advanced Networking →](./Module-12-Advanced-Networking.md)
