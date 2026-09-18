# AWS Certified AI Practitioner (AIF-C01) — Course Guide

## Course Overview

This guide covers all topics for the AWS Certified AI Practitioner exam (AIF-C01). Each module includes:

- Concept explanations with diagrams
- Real-life use cases
- Sample code with output explanations
- Step-by-step AWS Console (UI) walkthroughs
- Summary tables for quick review

---

## Modules

| # | Module | Topics |
|---|--------|--------|
| 1 | [Introduction to AI](module-01-introduction-to-ai.md) | What is AI, how it works, history, use cases, IDP, AI landscape |
| 2 | [AWS and Cloud Computing](module-02-aws-and-cloud-computing.md) | Client-server, cloud models, IaaS/PaaS/SaaS, Regions, AZs, Shared Responsibility |
| 3 | [Generative AI and Foundation Models](module-03-generative-ai-and-foundation-models.md) | Gen-AI, foundation models, LLMs, image generation, diffusion models |
| 3B | [Amazon Bedrock — Deep Dive](module-03b-amazon-bedrock.md) | Bedrock overview, fine-tuning (supervised/reinforcement), distillation, RAG, Knowledge Bases, embeddings, tokenization, agents, guardrails, model evaluation, CloudWatch monitoring |
| 4 | [Prompt Engineering](module-04-prompt-engineering.md) | Zero-shot, few-shot, chain-of-thought, system prompts, temperature, Top P |
| 5 | [Amazon Q](module-05-amazon-q.md) | Q Business, Q Developer, data sources, code generation, IDE integration |
| 6 | [AI and Machine Learning](module-06-ai-and-machine-learning.md) | Supervised/unsupervised/reinforcement learning, ML pipeline, NLP, computer vision |
| 7 | [AWS Managed AI Services](module-07-aws-managed-ai-services.md) | Rekognition, Textract, Comprehend, Translate, Polly, Transcribe, Lex, Kendra, Personalize |
| 8 | [Amazon SageMaker](module-08-amazon-sagemaker.md) | Studio, Ground Truth, Data Wrangler, training, deployment, Canvas |
| 9 | [Responsible AI](module-09-responsible-ai.md) | Core dimensions, interpretability vs explainability, bias types, Gen-AI challenges, prompt attacks, governance framework, data governance, compliance |
| 10 | [AWS Security Services & Infrastructure](module-10-aws-security-services.md) | Security & privacy for AI, monitoring, Shared Responsibility Model, secure data engineering, Gen-AI Security Scoping Matrix, MLOps, IAM, S3, EC2, Lambda, VPC/PrivateLink, Bedrock security, Audit Manager, Trusted Advisor, exam preparation |

---

## Quick Reference: AWS AI Services Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS AI/ML Services                           │
│                                                                      │
│  No ML Expertise Needed          ML Expertise Needed                 │
│  (Managed AI Services)           (Custom ML)                         │
│  ┌─────────────────────┐        ┌──────────────────────────┐        │
│  │ Rekognition (Vision)│        │ SageMaker                │        │
│  │ Textract (Documents)│        │  - Studio (IDE)          │        │
│  │ Comprehend (NLP)    │        │  - Training Jobs         │        │
│  │ Translate (Language)│        │  - Endpoints (Deploy)    │        │
│  │ Polly (Text→Speech) │        │  - Ground Truth (Label)  │        │
│  │ Transcribe (Speech) │        │  - Clarify (Bias/Explain)│        │
│  │ Lex (Chatbots)      │        │  - Canvas (No-Code)      │        │
│  │ Kendra (Search)     │        │  - JumpStart (Templates) │        │
│  │ Personalize (Recs)  │        │  - Pipelines (MLOps)     │        │
│  │ Forecast (TimeSeries│        │  - Model Monitor         │        │
│  │ Fraud Detector      │        │  - Feature Store         │        │
│  └─────────────────────┘        └──────────────────────────┘        │
│                                                                      │
│  Generative AI                   AI Assistants                       │
│  ┌─────────────────────┐        ┌──────────────────────────┐        │
│  │ Amazon Bedrock      │        │ Amazon Q Business        │        │
│  │  - Foundation Models│        │  - Enterprise Q&A        │        │
│  │  - Guardrails       │        │ Amazon Q Developer       │        │
│  │  - Knowledge Bases  │        │  - Code assistance       │        │
│  │  - Agents           │        │  - Code transformation   │        │
│  │  - Fine-tuning      │        │  - Security scanning     │        │
│  └─────────────────────┘        └──────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Exam Domains (AIF-C01)

| Domain | Weight | Key Topics |
|--------|--------|------------|
| **1. Fundamentals of AI and ML** | 20% | AI/ML concepts, types of learning, Gen-AI, foundation models |
| **2. Fundamentals of Generative AI** | 24% | LLMs, prompt engineering, foundation models, Bedrock |
| **3. Applications of Foundation Models** | 28% | Amazon Q, Bedrock, RAG, fine-tuning, agents |
| **4. Responsible AI** | 14% | Fairness, explainability, transparency, governance |
| **5. Security, Compliance, Governance** | 14% | IAM, encryption, compliance, data protection |

---

## How to Use This Guide

1. **Sequential study:** Read modules 1-10 in order for a complete learning path
2. **Targeted review:** Jump to specific modules for topics you need to review
3. **Hands-on practice:** Follow the step-by-step UI walkthroughs in each module
4. **Quick review:** Use the summary tables at the end of each module before the exam
5. **Code practice:** Run the sample code examples using AWS SDK (boto3) with your AWS account
