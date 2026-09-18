# Module 3B: Amazon Bedrock — Deep Dive

## 3B.1 What is Amazon Bedrock?

Amazon Bedrock is a fully managed service for building Generative AI applications on AWS. It provides access to a wide array of foundation models through a unified API.

### Key Features

| Feature | Description |
|---------|-------------|
| **Fully Managed** | No servers to manage — AWS handles infrastructure |
| **Data Control** | Your data stays private; it is never used to train the base foundation models |
| **Pay-per-Use** | Pricing based on tokens processed or images generated |
| **Unified API** | Same API structure regardless of which model you use |
| **Multiple FMs** | Access models from Amazon, Anthropic, Meta, Stability AI, and more |
| **Built-in Features** | RAG, LLM Agents, Guardrails, Fine-tuning out of the box |
| **Security & Governance** | Encryption, IAM integration, responsible AI features |

### How Bedrock Works

```
┌──────────────────────────────────────────────────────────────┐
│                      Amazon Bedrock                          │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │ Foundation Models │    │ Features                     │   │
│  │                  │    │                              │   │
│  │ - Amazon Titan   │    │ - Knowledge Bases (RAG)      │   │
│  │ - Anthropic Claude│   │ - Fine-tuning                │   │
│  │ - Meta Llama     │    │ - Agents                     │   │
│  │ - Stability AI   │    │ - Guardrails                 │   │
│  │ - Cohere         │    │ - Model Evaluation           │   │
│  │ - Mistral        │    │ - Embeddings                 │   │
│  └──────────────────┘    └──────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Unified API — Same interface for all models          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Interactive Playground — Test models in the console  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Bedrock Workflow

```
User ──► 1. Select Model (e.g., Anthropic Claude)
     ──► 2. Send Prompt: "What's the most popular dish in Italy?"
     ◄── 3. Receive Response: "Pizza & Pasta."
```

Behind the scenes, Bedrock can also:
- Fetch data from **Knowledge Bases** (RAG) for more accurate responses
- Apply **Fine-tuning** to customize the model with your data (stored in S3)
- Route through **Guardrails** to filter harmful content
- Use **Agents** to perform multi-step tasks

### Step-by-Step: Access Amazon Bedrock (via Console UI)

1. **Navigate to Bedrock**
   - Go to [https://console.aws.amazon.com](https://console.aws.amazon.com)
   - Search for **"Bedrock"** in the search bar
   - Click **Amazon Bedrock**

2. **Enable Model Access**
   - Left sidebar → **"Model access"**
   - Click **"Manage model access"**
   - Check the boxes next to the models you want (e.g., Anthropic Claude, Amazon Titan, Meta Llama)
   - Click **"Save changes"**
   - Wait for access status to show **"Access granted"**

3. **Try the Playground**
   - Left sidebar → **"Playgrounds"** → **"Chat"**
   - Select a model from the dropdown (e.g., **Anthropic Claude 3 Sonnet**)
   - Type a prompt: `Explain cloud computing in 3 sentences.`
   - Click **"Run"**
   - View the response

---

## 3B.2 Foundation Models on Bedrock

Bedrock makes a **copy** of the foundation model available only to you. Your data is never used to train the original FM.

### Choosing a Foundation Model

Consider these factors when selecting a model:

| Factor | What to Evaluate |
|--------|-----------------|
| **Model Type** | Text, image, multimodal (text + image) |
| **Performance** | Speed, accuracy, quality of output |
| **Context Window** | Maximum tokens the model can process at once |
| **Capabilities** | What tasks the model excels at |
| **Customization** | Can it be fine-tuned? |
| **Model Size** | Larger = more capable but more expensive |
| **Licensing** | Open-source vs. commercial |
| **Latency** | Response time requirements |
| **Compliance** | Regulatory requirements for your industry |

### Model Comparison

| Model | Max Tokens | Strengths | Use Cases | Pricing (per 1K tokens) |
|-------|-----------|-----------|-----------|------------------------|
| **Amazon Titan Text Express** | 8K | High-performance text, 100+ languages | Content creation, classification, education | Input: $0.0008, Output: $0.0016 |
| **Meta Llama 2 70B** | 4K | Large-scale tasks, dialogue, English | Text generation, customer service | Input: $0.0019, Output: $0.0025 |
| **Anthropic Claude 2.1** | 200K | High-capacity text, multi-language | Analysis, forecasting, document comparison | Input: $0.008, Output: $0.024 |
| **Stable Diffusion XL** | 77 tokens/prompt | Image generation | Advertising, media, creative content | $0.04–$0.08 per image |

### What is Amazon Titan?

Amazon Titan is AWS's own family of foundation models:

| Property | Details |
|----------|---------|
| **Provider** | AWS (first-party) |
| **Types** | Text, Image, Multimodal, Embeddings |
| **Access** | Fully managed API via Bedrock |
| **Customization** | Can be fine-tuned with your own data |
| **Cost** | Smaller models are more cost-effective |

> **Key Exam Point:** Multimodal models accept varied types of input (text, images) and can produce varied types of output. Smaller models are cheaper but less capable.

### Step-by-Step: Compare Models in Bedrock (via Console UI)

1. **Navigate to Bedrock** → Left sidebar → **"Foundation models"**
2. **Browse Models**
   - Filter by provider (Amazon, Anthropic, Meta, etc.)
   - Filter by modality (Text, Image, Embedding)
   - Click on a model to see details: description, pricing, context window, capabilities
3. **Compare in Playground**
   - Open two browser tabs with the Chat playground
   - Select a different model in each
   - Send the same prompt to both
   - Compare response quality, speed, and style

---

## 3B.3 Fine-Tuning a Model

Fine-tuning adapts a **copy** of a foundation model with your own data. It changes the model's weights to specialize it for your use case.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Base FM      │  +  │ Your Data    │  =  │ Fine-tuned       │
│ (general)    │     │ (Amazon S3)  │     │ Custom Model     │
└──────────────┘     └──────────────┘     └──────────────────┘
```

**Requirements:**
- Training data must adhere to a specific format
- Training data must be stored in Amazon S3
- Not all models support fine-tuning

### 3B.3.1 Supervised Fine-Tuning

Improves model performance on specific tasks using **labeled input-output pairs**.

**Training Data Format (JSONL):**
```json
{
  "prompt": "Who is Stephane Maarek?",
  "completion": "Stephane Maarek is an AWS instructor who dedicates his time to make the best AWS courses so that his students can pass all AWS certification exams."
}
```

```json
{
  "prompt": "What is Amazon S3?",
  "completion": "Amazon S3 is an object storage service that offers industry-leading scalability, data availability, security, and performance."
}
```

**How it works:**
1. You provide labeled examples (prompt + expected completion)
2. The model learns to produce outputs matching your examples
3. The model's weights are updated to reflect your domain knowledge

### 3B.3.2 Reinforcement Fine-Tuning

Improves the model using **feedback-based learning** with a reward function.

```
┌──────────┐     ┌──────────────┐     ┌─────────────────┐
│  Prompt  │────>│  Model       │────>│  Response A      │
│          │     │  generates   │     │  Response B      │
│          │     │  multiple    │     │  Response C      │
│          │     │  responses   │     │                  │
└──────────┘     └──────────────┘     └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │ Reward Function  │
                                      │                  │
                                      │ Response A → 9   │
                                      │ Response B → 5   │
                                      │ Response C → 2   │
                                      └────────┬────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │ Update model     │
                                      │ to produce more  │
                                      │ high-scoring     │
                                      │ responses        │
                                      └─────────────────┘
```

**Reward Function Types:**
| Type | How It Works | Use Case |
|------|-------------|----------|
| **Objective** | AWS Lambda (Python code) evaluates responses programmatically | Factual accuracy, format compliance |
| **Subjective** | Another model acts as a "judge" using evaluation instructions | Empathy, tone, helpfulness |

**Example: Technical Customer Support Chatbot**

Prompt: *"My app is running very slowly."*

| Response | Score | Why |
|----------|-------|-----|
| "Restart the app." | 5.0 | Helpful but superficial — no diagnosis, no empathy |
| "That sounds frustrating. I can help you figure this out. Before we troubleshoot, can you tell me when it started and what you were doing at the time?" | 9.0 | Empathetic, diagnostic, efficient — acknowledges frustration, gathers context |
| "Please open a support ticket and attach logs A, B, and C." | 2.0 | Not helpful — pushes work to user, breaks conversational flow |

The model learns iteratively from these scores and tries to achieve higher scores over time.

### Supervised vs. Reinforcement Fine-Tuning

```
Supervised Fine-Tuning:
┌──────────────┐     ┌──────────────┐
│ Input Prompt │────>│ Output Prompt│
│ (provided)   │     │ (provided)   │
└──────────────┘     └──────────────┘

Reinforcement Fine-Tuning:
┌──────────────┐     ┌──────────────────────────┐
│ Input Prompt │────>│ Output A (Score = 2.0)   │
│ (provided)   │     │ Output B (Score = 5.0)   │
│              │     │ Output C (Score = 9.0)   │
│              │     │ (all generated by model) │
└──────────────┘     └──────────────────────────┘
```

| Aspect | Supervised | Reinforcement |
|--------|-----------|---------------|
| **Input** | Prompt + expected output (both provided) | Prompt only (provided) |
| **Output** | Model learns to match provided output | Model generates outputs, scored by reward function |
| **Cost** | Usually cheaper (less compute, less data) | More expensive (multiple generations per prompt) |
| **Best For** | Domain knowledge, specific formats | Tone, style, behavior, subjective quality |

### 3B.3.3 Distillation

Making models **smaller and faster** by transferring knowledge from a large model to a small one.

```
┌──────────────────┐                ┌──────────────────┐
│ Larger Model     │   Knowledge    │ Smaller Model    │
│ (Teacher)        │───────────────>│ (Student)        │
│                  │   Transfer     │                  │
│ Slow, expensive  │                │ Fast, cheap      │
│ High accuracy    │                │ Slightly lower   │
│                  │                │ accuracy         │
└──────────────────┘                └──────────────────┘
```

| Property | Details |
|----------|---------|
| **Cost Reduction** | Up to 75% less expensive than the original model |
| **Trade-off** | Decrease in accuracy, but potentially acceptable for your use case |
| **Process** | You provide input data (prompts); the teacher model generates outputs; the student model learns from them |
| **Goal** | Efficiency, speed, and cost reduction |

### Real-Life Use Case

> **Example: E-commerce Chatbot Distillation**
> A company uses Claude 3 Opus (large, expensive) for their customer support chatbot. After collecting thousands of real conversations, they distill the knowledge into a smaller Titan model. The distilled model handles 90% of queries at 25% of the cost, with the large model reserved for complex cases.

### Fine-Tuning Cost Considerations

| Factor | Details |
|--------|---------|
| **Training Cost** | Re-training requires significant compute budget |
| **Supervised is Cheaper** | Less compute-intensive, less data usually required |
| **Expertise Required** | ML engineers needed to prepare data, run fine-tuning, evaluate results |
| **Running Cost** | Fine-tuned models cost more to run than base models |
| **Pricing Options** | On-demand (per token) or Provisioned Throughput (per month) |

### Fine-Tuning Use Cases

| Use Case | Example |
|----------|---------|
| **Custom Persona** | Chatbot with a specific tone or personality |
| **Updated Knowledge** | Training with more recent information than the base model has |
| **Proprietary Data** | Training on your emails, customer service records, internal docs |
| **Targeted Tasks** | Categorization, accuracy assessment, domain-specific Q&A |

### Step-by-Step: Fine-Tune a Model in Bedrock (via Console UI)

1. **Prepare Training Data**
   - Create a JSONL file with prompt-completion pairs:
     ```json
     {"prompt": "What is our return policy?", "completion": "Our return policy allows returns within 30 days of purchase with a valid receipt."}
     {"prompt": "How do I track my order?", "completion": "You can track your order by logging into your account and clicking 'Order History'."}
     ```
   - Upload the file to an **S3 bucket**

2. **Navigate to Bedrock** → Left sidebar → **"Custom models"**

3. **Create a Fine-Tuning Job**
   - Click **"Customize model"** → **"Create fine-tuning job"**
   - Select a base model (e.g., Amazon Titan Text Express)
   - Enter job name
   - Specify S3 path to your training data
   - Configure hyperparameters (epochs, learning rate, batch size)
   - Select output S3 location for the fine-tuned model

4. **Start Training**
   - Click **"Create fine-tuning job"**
   - Monitor progress in the custom models dashboard
   - Training can take minutes to hours depending on data size

5. **Test the Fine-Tuned Model**
   - Once complete, the model appears under **"Custom models"**
   - To use it, you need to purchase **Provisioned Throughput** or use on-demand pricing
   - Test in the playground by selecting your custom model

---

## 3B.4 Model Evaluation

Bedrock provides two ways to evaluate model quality: **Automatic** and **Human**.

### 3B.4.1 Automatic Evaluation

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Benchmark        │     │ Model to         │     │ Generated    │
│ Questions        │────>│ Evaluate         │────>│ Answers      │
└──────────────────┘     └──────────────────┘     └──────┬───────┘
                                                         │
┌──────────────────┐                                     │
│ Benchmark        │─────────────────────────────────────┤
│ Answers          │                                     │
└──────────────────┘                                     ▼
                                                  ┌──────────────┐
                                                  │ Judge Model  │
                                                  │              │
                                                  │ Grading Score│
                                                  └──────────────┘
```

**Built-in task types:**
- Text summarization
- Question and answer
- Text classification
- Open-ended text generation

**Data sources:**
- Bring your own prompt dataset
- Use built-in curated prompt datasets

### Automated Evaluation Metrics

| Metric | What It Measures | How It Works |
|--------|-----------------|-------------|
| **ROUGE** | Summarization quality | Measures matching n-grams between reference and generated text. ROUGE-N = n-gram overlap; ROUGE-L = longest common subsequence |
| **BLEU** | Translation quality | Evaluates precision of n-grams (1,2,3,4) and penalizes brevity |
| **BERTScore** | Semantic similarity | Uses pre-trained BERT model to compare contextualized embeddings via cosine similarity. Captures nuance better than word-matching |
| **Perplexity** | Prediction confidence | How well the model predicts the next token. **Lower is better** |

### Real-Life Use Case: Automated Evaluation

```
┌──────────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Clickstream Data │     │              │     │ BERTScore        │
│ Cart Data        │────>│ Generative   │────>│ ROUGE            │
│ Purchased Items  │     │ AI Model     │     │ BLEU             │
│ Customer Feedback│     │              │     │                  │
└──────────────────┘     └──────┬───────┘     └────────┬─────────┘
                               │                       │
                               ▼                       │
                    ┌──────────────────┐                │
                    │ Display products │                │
                    │ based on customer│◄───────────────┘
                    │ profile          │   feedback loop
                    │                  │
                    │ Generate dynamic │
                    │ product          │
                    │ descriptions     │
                    └──────────────────┘
```

### Benchmark Datasets

| Property | Details |
|----------|---------|
| **Purpose** | Curated collections designed to evaluate language model performance |
| **Coverage** | Wide range of topics, complexities, linguistic phenomena |
| **Measures** | Accuracy, speed, efficiency, scalability |
| **Bias Detection** | Some benchmarks detect bias and discrimination against groups |
| **Custom** | You can create your own benchmark dataset specific to your business |

### 3B.4.2 Human Evaluation

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Benchmark        │     │ Model to         │     │ Generated    │
│ Questions +      │────>│ Evaluate         │────>│ Answers      │
│ Benchmark Answers│     │                  │     │ (1, 2, 3...) │
└──────────────────┘     └──────────────────┘     └──────┬───────┘
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                                                  │ Work Team    │
                                                  │ (Employees / │
                                                  │  SMEs)       │
                                                  │              │
                                                  │ Grading Score│
                                                  └──────────────┘
```

**Work team options:**
- Employees of your company
- Subject-Matter Experts (SMEs)

**Evaluation methods:**
- Thumbs up / thumbs down
- Ranking responses
- Custom scoring criteria

**Task types:** Same as automatic evaluation, plus custom tasks.

### Business Metrics for Model Evaluation

| Metric | What It Measures | Example |
|--------|-----------------|---------|
| **User Satisfaction** | User feedback on model responses | Survey scores for an e-commerce chatbot |
| **ARPU** (Average Revenue Per User) | Revenue attributed to the Gen-AI app | Monitor revenue changes after deploying AI |
| **Cross-Domain Performance** | Model's ability across different domains | Multi-category e-commerce platform |
| **Conversion Rate** | Desired outcomes (purchases, sign-ups) | Higher conversion after AI recommendations |
| **Efficiency** | Computation and resource utilization | Reduce production line processing time |

### Step-by-Step: Evaluate a Model in Bedrock (via Console UI)

1. **Navigate to Bedrock** → Left sidebar → **"Model evaluation"**

2. **Create an Automatic Evaluation**
   - Click **"Create evaluation job"**
   - Select **"Automatic"**
   - Choose the model to evaluate
   - Select task type (e.g., text summarization)
   - Choose a prompt dataset (built-in or upload your own to S3)
   - Select evaluation metrics (ROUGE, BLEU, BERTScore)
   - Click **"Create"**

3. **View Results**
   - Wait for the evaluation to complete
   - View scores for each metric:
     ```
     ROUGE-L:    0.72
     BLEU:       0.65
     BERTScore:  0.89
     ```
   - Higher scores indicate better performance (except Perplexity — lower is better)

4. **Create a Human Evaluation**
   - Click **"Create evaluation job"** → Select **"Human"**
   - Choose the model and task type
   - Select or create a work team
   - Define evaluation criteria (thumbs up/down, ranking, custom)
   - Click **"Create"**
   - Work team members receive evaluation tasks and provide scores

---

## 3B.5 RAG and Knowledge Bases

### What is RAG?

**RAG = Retrieval-Augmented Generation** — allows a foundation model to reference a data source outside of its training data before generating a response.

```
┌──────┐  Prompt   ┌──────────────────────────────────────────────┐
│ User │──────────>│              Amazon Bedrock                   │
│      │           │                                               │
│      │           │  ┌─────────────┐    ┌──────────────────────┐ │
│      │           │  │ Knowledge   │    │ Foundation Model     │ │
│      │           │  │ Base        │    │                      │ │
│      │           │  │             │    │ Receives:            │ │
│      │           │  │ ┌─────────┐│    │ Original prompt      │ │
│      │           │  │ │ Vector  ││───>│ + Retrieved context  │ │
│      │           │  │ │ Database││    │                      │ │
│      │           │  │ └────┬────┘│    │ Generates:           │ │
│      │           │  │      │     │    │ Accurate response    │ │
│      │           │  │ ┌────┴────┐│    │ with source data     │ │
│      │           │  │ │ Data    ││    └──────────┬───────────┘ │
│      │           │  │ │ Sources ││               │             │
│      │           │  │ │(S3,etc.)││               │             │
│      │           │  │ └─────────┘│               │             │
│      │           │  └─────────────┘               │             │
│      │◄──────────────────────────────────────────┘             │
│      │  Response  │                                              │
└──────┘           └──────────────────────────────────────────────┘
```

### RAG Step-by-Step Flow

1. **User sends a query:** "Who's the product manager for John?"
2. **Bedrock searches the Knowledge Base** (vector database) for relevant information
3. **Relevant documents are retrieved:** "John Product Info — Product Manager: Jessie Smith, Engineer: Sara Ronald"
4. **Augmented prompt is created:** Original query + retrieved context
5. **Foundation model generates response:** "Jessie Smith is the Product Manager for John."

### How Vector Databases Work in RAG

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Amazon   │────>│ Document │────>│ Embeddings   │────>│ Vector       │
│ S3       │     │ Chunks   │     │ Model        │     │ Database     │
│ (source) │     │          │     │ (e.g., Titan)│     │              │
└──────────┘     └──────────┘     └──────────────┘     └──────────────┘
```

1. Documents in S3 are split into **chunks**
2. Each chunk is converted to a **vector embedding** using an embeddings model
3. Vectors are stored in a **vector database** for fast similarity search
4. When a user asks a question, the query is also converted to a vector
5. The database finds the most similar document chunks (nearest neighbors)
6. Those chunks are passed to the FM as context

### Supported Vector Databases

| Database | Type | Key Feature |
|----------|------|-------------|
| **Amazon OpenSearch Service** | Search & analytics | Real-time similarity queries, kNN search, scalable |
| **Amazon Aurora PostgreSQL** | Relational database | AWS proprietary, pgvector extension |
| **Amazon Neptune Analytics** | Graph database | Graph-based RAG (GraphRAG) |
| **Amazon S3 Vectors** | Object storage | Cost-effective, sub-second query performance |

### Supported Data Sources for Knowledge Bases

| Source | Description |
|--------|-------------|
| **Amazon S3** | Documents, PDFs, text files |
| **Confluence** | Wiki pages, documentation |
| **Microsoft SharePoint** | Enterprise documents |
| **Salesforce** | CRM data, knowledge articles |
| **Web pages** | Your website, social media feeds |

### RAG Use Cases

| Use Case | Knowledge Base Content | RAG Application |
|----------|----------------------|-----------------|
| **Customer Service** | Products, features, specs, FAQs, troubleshooting guides | Chatbot answering customer queries |
| **Legal Research** | Laws, regulations, case precedents, legal opinions | Chatbot for legal queries |
| **Healthcare Q&A** | Diseases, treatments, clinical guidelines, research papers | Medical query answering system |

### Step-by-Step: Create a Knowledge Base in Bedrock (via Console UI)

1. **Prepare Your Data**
   - Upload documents (PDFs, text files, HTML) to an **S3 bucket**
   - Example: Upload your company's FAQ document, product manuals, policy docs

2. **Navigate to Bedrock** → Left sidebar → **"Knowledge bases"**

3. **Create a Knowledge Base**
   - Click **"Create knowledge base"**
   - Enter name and description
   - Select an **IAM role** (or let Bedrock create one)

4. **Configure Data Source**
   - Click **"Add data source"**
   - Select **Amazon S3**
   - Enter the S3 bucket URI (e.g., `s3://my-company-docs/`)
   - Configure chunking strategy:
     - **Default** — Bedrock automatically chunks documents
     - **Fixed size** — Specify chunk size (e.g., 300 tokens)
     - **No chunking** — Each file is one chunk

5. **Select Embeddings Model**
   - Choose **Amazon Titan Embeddings** (recommended)
   - This model converts your documents into vector representations

6. **Select Vector Database**
   - Choose a vector store:
     - **Quick create** — Bedrock creates an OpenSearch Serverless collection for you
     - **Existing** — Use your own OpenSearch, Aurora, or Neptune database

7. **Create and Sync**
   - Click **"Create knowledge base"**
   - Click **"Sync"** to index your documents
   - Wait for sync to complete

8. **Test the Knowledge Base**
   - Click **"Test"** in the knowledge base detail page
   - Select a foundation model for generating responses
   - Ask a question: "What is our refund policy?"
   - View the response with source citations

### Sample Code: Query a Knowledge Base via API

```python
import boto3
import json

bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

response = bedrock_agent.retrieve_and_generate(
    input={
        'text': 'What is our company refund policy?'
    },
    retrieveAndGenerateConfiguration={
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            'knowledgeBaseId': 'ABCDEF1234',
            'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
        }
    }
)

print("Answer:", response['output']['text'])
print("\nSources:")
for citation in response.get('citations', []):
    for ref in citation.get('retrievedReferences', []):
        print(f"  - {ref['location']['s3Location']['uri']}")
```

**Output:**
```
Answer: Our refund policy allows customers to request a full refund
within 30 days of purchase. Items must be in original condition with
proof of purchase. Refunds are processed within 5-7 business days.

Sources:
  - s3://my-company-docs/policies/refund-policy.pdf
```

### Real-Life Use Case

> **Example: Internal IT Helpdesk**
> A company creates a Bedrock Knowledge Base connected to their IT documentation in Confluence and S3. When an employee asks "How do I reset my VPN password?", RAG retrieves the relevant IT guide and generates a step-by-step answer with a link to the source document — reducing IT support tickets by 40%.

---

## 3B.6 Tokenization and Context Windows

### Tokenization

**Tokenization** is the process of converting raw text into a sequence of tokens that the model can process.

| Method | How It Works | Example |
|--------|-------------|---------|
| **Word-based** | Text split into individual words | "I love AWS" → ["I", "love", "AWS"] |
| **Subword** | Long words split into smaller pieces | "unhappiness" → ["un", "happiness"] |

> You can experiment with tokenization at: [https://platform.openai.com/tokenizer](https://platform.openai.com/tokenizer)

### Context Window

The **context window** is the maximum number of tokens an LLM can consider when generating text.

| Property | Impact |
|----------|--------|
| **Larger window** | More information, better coherence, handles longer documents |
| **Smaller window** | Faster, less memory, cheaper |
| **Trade-off** | Large context windows require more memory and processing power |

> **Key Exam Point:** The context window is the **first factor** to consider when choosing a model. If you need to process long documents (legal contracts, research papers), you need a model with a large context window (e.g., Claude's 200K tokens).

### Context Window Comparison

| Model | Context Window |
|-------|---------------|
| Amazon Titan Text Express | 8K tokens |
| Meta Llama 2 70B | 4K tokens |
| Anthropic Claude 2.1 | 200K tokens |
| Stable Diffusion XL | 77 tokens per prompt |

---

## 3B.7 Embeddings

**Embeddings** convert text, images, or audio into **vectors** (arrays of numerical values) that capture semantic meaning.

### How Embeddings Work

```
"the cat sat on the mat"
         │
         ▼ tokenization
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ the │ cat │ sat │ on  │ the │ mat │
└──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┘
   │     │     │     │     │     │
   ▼     ▼     ▼     ▼     ▼     ▼
 Token Token Token Token Token Token
  ID    ID    ID    ID    ID    ID
  865   128   789   658   864   486
   │     │     │     │     │     │
   ▼     ▼     ▼     ▼     ▼     ▼
┌──────────────────────────────────┐
│        Embeddings Model          │
│        (e.g., Amazon Titan)      │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  cat → [0.025, -0.009, -0.011,  │
│         0.021, ...]              │
│  the → [1.042, -5.432, 0.239,   │
│         -2.241, ...]             │
└──────────────────────────────────┘
               │
               ▼
        Vector Database
```

### Key Properties of Embeddings

| Property | Details |
|----------|---------|
| **High Dimensionality** | Vectors have hundreds or thousands of dimensions |
| **Semantic Meaning** | Each dimension captures a feature (meaning, sentiment, role) |
| **Similarity** | Words with similar meanings have similar vectors |
| **Search** | Embeddings power semantic search applications |

### Semantic Similarity

Words with related meanings have similar embedding vectors:

```
Word      d1    d2    d3    d4    d5   ... d100
────────  ────  ────  ────  ────  ────     ────
dog       0.6   0.9   0.1   0.4  -0.7     -0.2
puppy     0.5   0.8  -0.1   0.2  -0.6     -0.1   ← similar to "dog"
cat       0.7  -0.1   0.4   0.3  -0.4     -0.3   ← somewhat similar
houses   -0.8  -0.4  -0.5   0.1  -0.9      0.8   ← very different
```

When visualized in 2D (dimensionality reduction):
```
        ▲
        │    • puppy
        │  • dog
        │
        │        • cat
        │
        │
        │                        • houses
        └──────────────────────────────►
```

"Dog" and "puppy" cluster together because they're semantically similar. "Houses" is far away because it's unrelated.

### Real-Life Use Case

> **Example: Semantic Search**
> A user searches for "affordable laptop for students." Traditional keyword search looks for exact word matches. With embeddings, the search engine understands the *meaning* and also returns results for "budget notebook for college" and "cheap computer for school" — even though the exact words don't match.

---

## 3B.8 Bedrock Guardrails

Guardrails control the interaction between users and foundation models to ensure safe, appropriate responses.

### What Guardrails Do

| Feature | Description |
|---------|-------------|
| **Content Filtering** | Filter undesirable and harmful content (hate, insults, sexual, violence) |
| **PII Removal** | Remove Personally Identifiable Information for enhanced privacy |
| **Hallucination Reduction** | Reduce false or fabricated information |
| **Topic Blocking** | Block specific topics the model should not discuss |
| **Word Filtering** | Block specific words or phrases |
| **Monitoring** | Analyze user inputs that violate guardrails |

### How Guardrails Work

```
┌──────┐     ┌──────────────────────────────────────────┐     ┌──────┐
│ User │────>│              Amazon Bedrock               │────>│ User │
│      │     │                                           │     │      │
│ "Suggest   │  ┌────────────┐    ┌──────────────────┐  │  "Sorry,  │
│  me        │  │ Guardrails │    │ Foundation Model │  │  this is  │
│  something │  │            │    │                  │  │  a        │
│  to cook   │  │ Blocked    │    │ (not reached     │  │  restricted│
│  tonight"  │  │ Topics:    │    │  for blocked     │  │  topic."  │
│            │  │ - Food     │    │  topics)         │  │           │
│            │  │   Recipes  │    │                  │  │           │
│            │  └────────────┘    └──────────────────┘  │           │
└──────┘     └──────────────────────────────────────────┘     └──────┘
```

You can create **multiple guardrails** for different use cases and monitor which user inputs trigger violations.

### Step-by-Step: Create a Guardrail in Bedrock (via Console UI)

1. **Navigate to Bedrock** → Left sidebar → **"Guardrails"**

2. **Create a Guardrail**
   - Click **"Create guardrail"**
   - Enter name: `customer-support-guardrail`
   - Enter description

3. **Configure Content Filters**
   - Set filter strength for both **input** (user messages) and **output** (model responses):

   | Category | Input Filter | Output Filter |
   |----------|-------------|---------------|
   | Hate | High | High |
   | Insults | Medium | High |
   | Sexual | High | High |
   | Violence | Medium | High |

4. **Add Denied Topics**
   - Click **"Add denied topic"**
   - Name: `medical-advice`
   - Definition: "Do not provide medical diagnoses or treatment recommendations"
   - Sample phrases: "What medicine should I take?", "Diagnose my symptoms"
   - Add more topics as needed:
     - `competitor-discussion` — "Do not discuss competitor products"
     - `financial-advice` — "Do not provide investment recommendations"

5. **Add Word Filters**
   - Add specific words or phrases to block
   - Enable **profanity filter** toggle

6. **Configure PII Handling**
   - Select action: **Block** (reject the request) or **Mask** (replace PII with `[PII]`)
   - Select PII types to detect:
     - Email addresses
     - Phone numbers
     - Social Security numbers
     - Credit card numbers
     - Names, addresses

7. **Test the Guardrail**
   - Click **"Test"** tab
   - Select a model to test with
   - Try prompts that should be blocked:
     - "What medicine should I take for a headache?" → Should be blocked (denied topic)
     - "My email is john@example.com" → PII should be masked
   - Try normal prompts to verify they pass through

8. **Apply to Your Application**
   - Note the Guardrail ID
   - Use it in API calls:

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body=json.dumps({
        "messages": [{"role": "user", "content": "What medicine should I take?"}],
        "max_tokens": 200
    }),
    guardrailIdentifier='abc123',      # Your guardrail ID
    guardrailVersion='1',
    contentType='application/json',
    accept='application/json'
)

result = json.loads(response['body'].read())
print(result)
```

**Output (when blocked):**
```json
{
  "output": {
    "text": "Sorry, I cannot provide medical advice. Please consult a healthcare professional."
  },
  "stopReason": "guardrail_intervened",
  "guardrailAction": "BLOCKED"
}
```

---

## 3B.9 Bedrock Agents

Agents manage and carry out **multi-step tasks** by coordinating actions, integrating with external systems, and leveraging RAG.

### What Agents Do

| Capability | Description |
|-----------|-------------|
| **Task Coordination** | Perform tasks in the correct order, pass information between steps |
| **Action Groups** | Execute pre-defined actions (API calls, Lambda functions) |
| **System Integration** | Connect to databases, APIs, and external services |
| **RAG Integration** | Retrieve information from Knowledge Bases when needed |
| **Chain of Thought** | Break complex requests into logical steps |

### Agent Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Bedrock Agent                            │
│                                                               │
│  ┌─────────────┐    ┌──────────────────────────────────────┐ │
│  │ Instructions│    │ Chain of Thought                     │ │
│  │ (system     │    │                                      │ │
│  │  prompt)    │    │ Step 1 → Step 2 → Step 3 → ... → N  │ │
│  └─────────────┘    └──────────┬───────────────────────────┘ │
│                                │                              │
│  ┌─────────────────────────────┼─────────────────────────┐   │
│  │                             │                         │   │
│  ▼                             ▼                         ▼   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Action       │    │ Action       │    │ Knowledge    │   │
│  │ Group 1      │    │ Group 2      │    │ Bases        │   │
│  │              │    │              │    │              │   │
│  │ API calls    │    │ Lambda       │    │ Search docs  │   │
│  │ (OpenAPI)    │    │ functions    │    │ for context  │   │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘   │
│         │                   │                                │
│         ▼                   ▼                                │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ External API │    │ Database     │                       │
│  └──────────────┘    └──────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
User ──► "What did I buy last week and what should I buy next?"
              │
              ▼
         Bedrock Agent
              │
              ├── Step 1: Call /getRecentPurchases (Action Group 1)
              │           → Returns: ["Widget A", "Widget B"]
              │
              ├── Step 2: Call /getRecommendedPurchases (Action Group 1)
              │           → Returns: ["Widget C", "Widget D"]
              │
              ├── Step 3: Search Knowledge Base for return policy
              │           → Returns: "30-day return policy"
              │
              └── Step 4: Generate final response using FM
                          → "Last week you purchased Widget A and Widget B.
                             Based on your history, I recommend Widget C
                             and Widget D. Remember, all purchases have
                             a 30-day return policy."
```

### Agent Setup Components

| Component | Description | Example |
|-----------|-------------|---------|
| **Instructions** | System prompt defining the agent's behavior | "You are a shopping assistant. Help users with orders and recommendations." |
| **Action Groups** | Sets of API actions the agent can perform | `/getRecentPurchases`, `/getRecommendedPurchases`, `/getPurchaseDetails/{id}` |
| **API Schema** | OpenAPI specification defining available endpoints | JSON/YAML file describing API routes, parameters, responses |
| **Lambda Functions** | Backend logic for action groups | `PlaceOrderLambda` — processes order placement |
| **Knowledge Bases** | Document collections for RAG | Company return policy, product catalog |

### Step-by-Step: Create a Bedrock Agent (via Console UI)

1. **Navigate to Bedrock** → Left sidebar → **"Agents"**

2. **Create an Agent**
   - Click **"Create agent"**
   - Enter agent name: `shopping-assistant`
   - Enter instructions (system prompt):
     ```
     You are a helpful shopping assistant. Help users find products,
     check order status, and make recommendations based on their
     purchase history. Always be polite and helpful.
     ```
   - Select a foundation model (e.g., Anthropic Claude 3 Sonnet)

3. **Add an Action Group**
   - Click **"Add action group"**
   - Enter name: `order-management`
   - Select action type: **Define with API schemas**
   - Upload an OpenAPI schema file or define inline:
     ```yaml
     openapi: 3.0.0
     paths:
       /getRecentPurchases:
         get:
           summary: Get user's recent purchases
           parameters:
             - name: userId
               in: query
               required: true
               schema:
                 type: string
     ```
   - Select or create a **Lambda function** to handle the API calls

4. **Attach a Knowledge Base** (optional)
   - Click **"Add knowledge base"**
   - Select an existing knowledge base (e.g., product catalog, return policy)

5. **Prepare and Test**
   - Click **"Prepare"** to build the agent
   - Click **"Test"** to open the test chat
   - Try: "What did I buy last week?"
   - The agent calls the action group, retrieves data, and generates a response

6. **Deploy**
   - Click **"Create alias"** to create a deployable version
   - Use the alias ARN in your application code

### Real-Life Use Case

> **Example: Travel Booking Agent**
> A travel company creates a Bedrock Agent with three action groups: (1) search flights, (2) search hotels, (3) book reservations. The agent also has a Knowledge Base with travel policies and destination guides. When a user says "Plan a 5-day trip to Tokyo in April for 2 people," the agent searches flights, finds hotels, checks visa requirements from the Knowledge Base, and presents a complete itinerary — all in one conversation.

---

## 3B.10 Bedrock and CloudWatch Monitoring

### Model Invocation Logging

```
┌──────────┐     ┌──────────────┐     ┌──────────────────┐
│ Bedrock  │────>│ CloudWatch   │     │ Amazon S3        │
│ invoke   │     │ Logs         │     │ (log storage)    │
│ model    │     │              │     │                  │
│          │────>│ Includes:    │────>│ Includes:        │
│          │     │ - Text       │     │ - Text           │
│          │     │ - Images     │     │ - Images         │
│          │     │ - Embeddings │     │ - Embeddings     │
└──────────┘     └──────────────┘     └──────────────────┘
```

**What's logged:**
- All model invocations (who called what model, when)
- Input prompts and output responses
- Images and embeddings (if applicable)
- Can be analyzed with **CloudWatch Logs Insights** for patterns and alerting

### CloudWatch Metrics

| Metric | What It Measures |
|--------|-----------------|
| **InvocationCount** | Number of model invocations |
| **InvocationLatency** | Time to generate a response |
| **ContentFilteredCount** | Number of times Guardrails blocked content |
| **InputTokenCount** | Tokens in the input prompt |
| **OutputTokenCount** | Tokens in the generated response |

> **Key Exam Point:** The `ContentFilteredCount` metric helps verify that Guardrails are functioning correctly. You can build CloudWatch Alarms on top of these metrics.

### Step-by-Step: Enable Bedrock Logging (via Console UI)

1. **Navigate to Bedrock** → Left sidebar → **"Settings"**

2. **Enable Model Invocation Logging**
   - Toggle **"Model invocation logging"** to ON
   - Select log destination:
     - **CloudWatch Logs** — for real-time analysis and alerting
     - **Amazon S3** — for long-term storage and compliance
   - Select what to log:
     - Text (prompts and responses)
     - Images
     - Embeddings
   - Click **"Save"**

3. **View Logs in CloudWatch**
   - Navigate to **CloudWatch** → **"Logs"** → **"Log groups"**
   - Find the Bedrock log group
   - Click **"Logs Insights"** to query:
     ```
     fields @timestamp, @message
     | filter modelId = "anthropic.claude-3-sonnet"
     | sort @timestamp desc
     | limit 20
     ```

4. **Create an Alarm**
   - Navigate to **CloudWatch** → **"Alarms"** → **"Create alarm"**
   - Select metric: **Bedrock** → **ContentFilteredCount**
   - Set threshold: **Greater than 10 in 5 minutes**
   - Configure SNS notification
   - This alerts you if Guardrails are blocking an unusual number of requests

---

## 3B.11 Bedrock Pricing

Amazon Bedrock offers three pricing models:

### Pricing Models

| Model | How It Works | Best For |
|-------|-------------|----------|
| **On-Demand** | Pay-as-you-go, no commitment | Unpredictable workloads, experimentation |
| **Batch** | Submit multiple predictions at once; output is a single file in S3 | Large-scale processing; up to **50% discount** |
| **Provisioned Throughput** | Purchase model units for a fixed period (1 month, 6 months) | Guaranteed capacity; works with base, fine-tuned, and custom models |

### On-Demand Pricing by Model Type

| Model Type | What You Pay For |
|-----------|-----------------|
| **Text Models** | Every input token + every output token processed |
| **Embedding Models** | Every input token processed (no output charge) |
| **Image Models** | Every image generated |

> **Key Exam Point:** On-Demand works with **base models only**. To use fine-tuned or custom models, you need **Provisioned Throughput**.

### Cost Drivers and Savings

| Factor | Impact on Cost |
|--------|---------------|
| **Number of input/output tokens** | Main driver of cost — more tokens = higher cost |
| **Model size** | Smaller models are usually cheaper |
| **On-Demand** | No commitment, standard pricing |
| **Batch** | Up to 50% discount for bulk processing |
| **Provisioned Throughput** | Not typically a cost-saving measure — used to reserve capacity |
| **Temperature, Top K, Top P** | **No impact on pricing** — these only affect output quality |

### Model Improvement Techniques — Cost Order (Cheapest to Most Expensive)

```
┌─────────────────────────────────────────────────────────────┐
│  Cost Order (cheapest → most expensive)                     │
│                                                              │
│  1. Prompt Engineering                              FREE     │
│     No model training needed                                 │
│                                                              │
│  2. RAG (Retrieval-Augmented Generation)            LOW      │
│     Uses external knowledge, no FM changes                   │
│                                                              │
│  3. Instruction-based Fine-Tuning                   MEDIUM   │
│     FM fine-tuned with specific instructions                 │
│     (requires additional computation)                        │
│                                                              │
│  4. Domain Adaptation Fine-Tuning                   HIGH     │
│     Model trained on domain-specific dataset                 │
│     (requires intensive computation)                         │
└─────────────────────────────────────────────────────────────┘
```

> **Key Exam Point:** Always try prompt engineering first (free), then RAG (low cost), before resorting to fine-tuning (expensive). This is a common exam question.

### Real-Life Use Case

> **Example: Cost Optimization for a Customer Support Bot**
> A company starts with prompt engineering to build their support bot (free). When answers aren't accurate enough, they add RAG with a Knowledge Base of their product docs (low cost). Only for highly specialized medical device queries do they fine-tune the model (expensive) — keeping 80% of queries on the cheapest tier.

---

## 3B.12 Amazon Nova

Amazon Nova is a family of AI foundation models built by AWS, designed to be fast, cost-effective, and enterprise-ready. Accessible through Amazon Bedrock.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Application  │────>│ Amazon       │────>│ Amazon Nova  │
│              │     │ Bedrock      │     │              │
│              │◄────│              │◄────│              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Nova Model Family

#### Understanding Models (Text & Multimodal)

| Model | Capability | Best For |
|-------|-----------|----------|
| **Nova Premier** | Most capable multimodal model | Complex reasoning tasks; best teacher for distilling custom models |
| **Nova Pro** | Best balance of accuracy, speed, and cost | Wide range of tasks (general purpose) |
| **Nova Lite** | Very low-cost multimodal, lightning fast | Processing image, video, and text inputs on a budget |
| **Nova Micro** | Text-only, lowest latency, very low cost | Fast text responses where multimodal isn't needed |

#### Creative Models

| Model | Capability | Best For |
|-------|-----------|----------|
| **Nova Canvas** | Image generation | Creating images for advertising, media, design |
| **Nova Reel** | Video generation | Creating video content |

#### Speech Models

| Model | Capability | Best For |
|-------|-----------|----------|
| **Nova Sonic** | Conversational speech understanding and generation | Real-time voice conversations in multiple languages |

### Amazon Nova 2

Enhanced next-generation models with advanced capabilities:

| Model | Capability | Input Types |
|-------|-----------|-------------|
| **Nova 2 Lite** | Fast, cost-effective reasoning for everyday workloads | Text, images, videos, documents |
| **Nova 2 Sonic** | Speech-to-speech FM for natural, real-time voice conversations | Speech, text |
| **Nova 2 Multimodal Embeddings** | State-of-the-art embedding model for agentic RAG and semantic search | Multimodal |
| **Nova 2 Omni** | All-in-one model for multimodal reasoning and image generation | Text, images, audio |

**Nova 2 Key Features:**
- Up to **1M tokens** of context window
- Advanced reasoning capabilities
- Build interactive chatbots, analyze documents and videos, create AI agents

### Step-by-Step: Use Amazon Nova in Bedrock (via Console UI)

1. **Navigate to Bedrock** → Left sidebar → **"Model access"**
2. **Enable Nova Models**
   - Click **"Manage model access"**
   - Check boxes next to **Amazon Nova** models you want
   - Click **"Save changes"**
3. **Test in Playground**
   - Left sidebar → **"Playgrounds"** → **"Chat"**
   - Select a Nova model (e.g., **Amazon Nova Pro**)
   - Try a prompt: `Analyze the pros and cons of microservices architecture`
   - Compare response quality and speed with other models

### Real-Life Use Case

> **Example: Choosing the Right Nova Model**
> A company builds three AI features: (1) A quick FAQ chatbot uses **Nova Micro** for fast, cheap text responses. (2) A product image analyzer uses **Nova Lite** for low-cost multimodal processing. (3) A complex financial analysis tool uses **Nova Pro** for the best accuracy-speed-cost balance. They use **Nova Premier** only to distill a custom model for their specialized use case.

---

## Module 3B Summary

| Topic | Key Takeaway |
|-------|-------------|
| Amazon Bedrock | Fully managed Gen-AI service with unified API, multiple FMs, pay-per-use |
| Foundation Models | Choose based on context window, capabilities, cost, licensing |
| Amazon Titan | AWS's own FM family — text, image, multimodal, embeddings |
| Amazon Nova | AWS's next-gen FM family — Premier, Pro, Lite, Micro, Canvas, Reel, Sonic |
| Supervised Fine-Tuning | Train with labeled input-output pairs to specialize the model |
| Reinforcement Fine-Tuning | Train with reward functions to improve subjective quality |
| Distillation | Transfer knowledge from large (teacher) to small (student) model — up to 75% cheaper |
| Model Evaluation | Automatic (ROUGE, BLEU, BERTScore) and Human (work teams) |
| RAG | Retrieve external data to augment model responses — reduces hallucinations |
| Knowledge Bases | Connect S3, Confluence, SharePoint, Salesforce, web pages to Bedrock |
| Vector Databases | OpenSearch, Aurora PostgreSQL, Neptune Analytics, S3 Vectors |
| Tokenization | Converting text to tokens; context window = max tokens a model can process |
| Embeddings | Convert text to vectors capturing semantic meaning; power similarity search |
| Guardrails | Content filtering, PII removal, topic blocking, word filtering |
| Agents | Multi-step task execution with action groups, Lambda, and Knowledge Bases |
| Pricing | On-Demand (base models), Batch (50% discount), Provisioned Throughput (reserved) |
| Cost Order | Prompt Engineering → RAG → Instruction Fine-Tuning → Domain Fine-Tuning |
| CloudWatch | Invocation logging, metrics (ContentFilteredCount), alarms |

---

## Key Exam Concepts

| Concept | Definition |
|---------|-----------|
| **RAG** | Retrieval-Augmented Generation — fetch external data before generating |
| **Fine-tuning** | Adapt a model copy with your data (changes weights) |
| **Distillation** | Make models smaller/cheaper by transferring knowledge |
| **Guardrails** | Control model behavior — filter content, block topics, mask PII |
| **Agents** | Multi-step task execution with external system integration |
| **Embeddings** | Numerical vectors capturing semantic meaning of text |
| **Context Window** | Maximum tokens a model can process (first factor in model selection) |
| **ROUGE/BLEU/BERTScore** | Automated metrics for evaluating model output quality |
| **ContentFilteredCount** | CloudWatch metric showing how often Guardrails block content |
| **On-Demand vs Batch** | Batch provides up to 50% discount for bulk processing |
| **Cost Order** | Prompt Engineering (free) → RAG (low) → Fine-Tuning (high) |
| **Amazon Nova** | AWS FM family: Premier (best), Pro (balanced), Lite (cheap multimodal), Micro (text-only, fastest) |

---

*Previous: [Module 3 — Generative AI and Foundation Models](module-03-generative-ai-and-foundation-models.md)*
*Next: [Module 4 — Prompt Engineering](module-04-prompt-engineering.md)*
