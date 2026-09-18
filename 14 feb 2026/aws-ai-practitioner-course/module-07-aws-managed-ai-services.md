# Module 7: AWS Managed AI Services

## 7.1 Overview

AWS provides pre-trained ML services that require no ML expertise. You call an API and get results — no model training needed.

### Why Use AWS Managed AI Services?

| Benefit | Description |
|---------|-------------|
| **Pre-trained** | Ready to use, no ML expertise needed |
| **High Availability** | Deployed across multiple AZs and Regions |
| **Performance** | Specialized CPU/GPUs for specific use cases |
| **Token-based Pricing** | Pay for what you use |
| **Provisioned Throughput** | For predictable workloads with cost savings |

```
┌─────────────────────────────────────────────────────────────┐
│                  AWS Managed AI Services                     │
│                                                              │
│  Vision          Language         Speech         Other       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │Rekognition│   │Comprehend│   │Transcribe│   │Forecast  │ │
│  │Textract   │   │Translate │   │Polly     │   │Personalize│ │
│  │Lookout    │   │Kendra    │   │Lex       │   │Fraud Det.│ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.2 Amazon Rekognition

**Purpose:** Image and video analysis — detect objects, faces, text, scenes, and activities.

### Key Features

| Feature | Description |
|---------|-------------|
| **Object & Scene Detection** | Identify objects (car, tree, dog) and scenes (beach, office) |
| **Facial Analysis** | Detect faces, estimate age, identify emotions, detect glasses |
| **Face Comparison** | Compare faces across images (identity verification) |
| **Celebrity Recognition** | Identify celebrities in images |
| **Text in Image** | Extract text from images (signs, license plates) |
| **Content Moderation** | Detect inappropriate or offensive content |
| **Custom Labels** | Train custom models for your specific objects |
| **Video Analysis** | Analyze video streams in real-time |

### Step-by-Step: Use Amazon Rekognition (via Console UI)

1. **Navigate to Rekognition**
   - AWS Console → Search **"Rekognition"** → Click the service

2. **Try Object Detection**
   - Left sidebar → **"Object and scene detection"**
   - Click **"Use your own image"** → Upload a photo
   - Click **"Analyze"**
   - Results show detected objects with confidence percentages:
     ```
     Dog       - 99.2%
     Animal    - 99.2%
     Pet       - 98.7%
     Grass     - 95.1%
     Outdoor   - 93.4%
     ```

3. **Try Facial Analysis**
   - Left sidebar → **"Facial analysis"**
   - Upload a photo with a face
   - Results show:
     ```
     Age Range:    25-35
     Gender:       Male (99.1%)
     Emotions:     Happy (95.2%), Calm (4.1%)
     Eyeglasses:   Yes (98.7%)
     Smile:        Yes (96.3%)
     ```

4. **Try Content Moderation**
   - Left sidebar → **"Image moderation"**
   - Upload an image
   - Results flag any inappropriate content with confidence scores

### Sample Code: Detect Labels in an Image

```python
import boto3

rekognition = boto3.client('rekognition', region_name='us-east-1')

# Analyze an image stored in S3
response = rekognition.detect_labels(
    Image={
        'S3Object': {
            'Bucket': 'my-images-bucket',
            'Name': 'photo.jpg'
        }
    },
    MaxLabels=10,
    MinConfidence=80
)

print("Detected labels:")
for label in response['Labels']:
    print(f"  {label['Name']}: {label['Confidence']:.1f}%")
```

**Output:**
```
Detected labels:
  Dog: 99.2%
  Animal: 99.2%
  Pet: 98.7%
  Golden Retriever: 96.5%
  Grass: 95.1%
  Outdoor: 93.4%
  Nature: 91.8%
  Park: 85.3%
```

### Real-Life Use Case

> **Example: Social Media Content Moderation**
> A social media platform uses Rekognition's content moderation API to automatically scan uploaded images. If an image is flagged as containing inappropriate content (confidence > 90%), it's held for human review before being published — protecting users and reducing the burden on human moderators.

### Custom Labels

Train Rekognition to find **your specific objects** (logos, products, custom items).

- Label your training images and upload to S3
- Only needs a **few hundred images or less**
- Rekognition creates a custom model on your image set
- Example: NFL uses it to find their logo in social media pictures

### Content Moderation Details

```
┌──────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│ User │────>│ Chatbot  │────>│ Rekognition  │────>│ Pass or  │
│      │     │ (App)    │     │ DetectMod-   │     │ Fail     │
│      │     │          │     │ erationLabels│     │          │
│      │     │ Generate │     │ API          │     │ 1-5%     │
│      │     │ image    │     │              │     │ → Human  │
│      │     │          │     │              │     │   Review │
└──────┘     └──────────┘     └──────────────┘     └──────────┘
```

- Brings human review down to **1-5%** of total content volume
- Integrated with **Amazon Augmented AI (A2I)** for human review
- **Custom Moderation Adaptors** — provide your own labeled images to extend or customize moderation

---

## 7.3 Amazon Textract

**Purpose:** Extract text, forms, and tables from scanned documents (OCR + intelligent extraction).

### Key Features

| Feature | Description |
|---------|-------------|
| **Text Detection** | Extract raw text from images and PDFs |
| **Form Extraction** | Extract key-value pairs (e.g., "Name: John Smith") |
| **Table Extraction** | Extract structured table data |
| **Expense Analysis** | Extract data from receipts and invoices |
| **Identity Document** | Extract data from IDs (driver's license, passport) |

### Step-by-Step: Use Amazon Textract (via Console UI)

1. **Navigate to Textract**
   - AWS Console → Search **"Textract"** → Click the service

2. **Analyze a Document**
   - Click **"Try Amazon Textract"** or **"Analyze document"**
   - Upload a document (invoice, receipt, form)
   - Select analysis type: **Raw text**, **Forms**, or **Tables**
   - Click **"Analyze"**

3. **View Results**
   - **Raw Text tab:** Shows all extracted text
   - **Forms tab:** Shows key-value pairs:
     ```
     Key: "Invoice Number"    Value: "INV-2024-001"
     Key: "Date"              Value: "March 15, 2024"
     Key: "Total Amount"      Value: "$1,234.56"
     ```
   - **Tables tab:** Shows structured table data:
     ```
     | Item        | Quantity | Price  |
     |-------------|----------|--------|
     | Widget A    | 10       | $50.00 |
     | Widget B    | 5        | $75.00 |
     ```

### Sample Code: Extract Text from a Document

```python
import boto3

textract = boto3.client('textract', region_name='us-east-1')

# Analyze a document from S3
response = textract.analyze_document(
    Document={
        'S3Object': {
            'Bucket': 'my-documents-bucket',
            'Name': 'invoice.pdf'
        }
    },
    FeatureTypes=['FORMS', 'TABLES']
)

# Extract key-value pairs
for block in response['Blocks']:
    if block['BlockType'] == 'KEY_VALUE_SET':
        if 'KEY' in block.get('EntityTypes', []):
            key_text = block.get('Text', '')
            print(f"Key: {key_text}")
```

---

## 7.4 Amazon Comprehend

**Purpose:** Natural Language Processing (NLP) — fully managed, serverless service to find insights and relationships in text.

### Key Features

| Feature | Description |
|---------|-------------|
| **Sentiment Analysis** | Positive, negative, neutral, or mixed |
| **Entity Recognition (NER)** | Extract predefined entities: people, places, organizations, dates |
| **Key Phrase Extraction** | Identify important phrases |
| **Language Detection** | Identify the language of text |
| **Topic Modeling** | Discover topics across a collection of documents |
| **PII Detection** | Find personally identifiable information |
| **Tokenization** | Analyze text using tokenization and parts of speech |

### Custom Classification

Organize documents into categories (classes) that **you** define.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Training Data│────>│ Comprehend   │────>│ Custom       │
│ (Amazon S3)  │     │ Custom       │     │ Classifier   │
│              │     │ Classifier   │     │              │
└──────────────┘     │ Training     │     │ Document ──► │
                     └──────────────┘     │ "Complaint"  │
                                          └──────────────┘
```

- Supports text, PDF, Word, images
- **Real-time Analysis** — single document, synchronous
- **Async Analysis** — multiple documents (batch), asynchronous
- Example: categorize customer emails by request type

### Custom Entity Recognition

Extract **domain-specific** terms and phrases (beyond standard NER).

- Extract terms like policy numbers, escalation phrases, product codes
- Train with custom data: list of entities + documents containing them
- Real-time or async analysis

```
Standard NER:  "John Smith" → PERSON, "Seattle" → LOCATION
Custom NER:    "POL-2024-001" → POLICY_NUMBER, "urgent escalation" → ESCALATION
```

### Step-by-Step: Use Amazon Comprehend (via Console UI)

1. **Navigate to Comprehend**
   - AWS Console → Search **"Comprehend"** → Click the service

2. **Try Real-Time Analysis**
   - Click **"Real-time analysis"** in the left sidebar
   - Paste text in the input box:
     ```
     Amazon Web Services is a cloud computing platform headquartered
     in Seattle, Washington. It was launched in 2006 by Jeff Bezos.
     ```
   - Click **"Analyze"**

3. **View Results**
   - **Entities tab:**
     ```
     Amazon Web Services  - ORGANIZATION
     Seattle              - LOCATION
     Washington           - LOCATION
     2006                 - DATE
     Jeff Bezos           - PERSON
     ```
   - **Key phrases tab:**
     ```
     "cloud computing platform"
     "Amazon Web Services"
     "Seattle, Washington"
     ```
   - **Sentiment tab:**
     ```
     Sentiment: NEUTRAL (0.89)
     ```
   - **Language tab:**
     ```
     Language: English (en) - 0.99
     ```

### Sample Code: Detect Entities

```python
import boto3

comprehend = boto3.client('comprehend', region_name='us-east-1')

text = """Amazon announced record profits in Q4 2024.
CEO Andy Jassy presented the results in Seattle."""

response = comprehend.detect_entities(
    Text=text,
    LanguageCode='en'
)

for entity in response['Entities']:
    print(f"  {entity['Text']:20s} | {entity['Type']:15s} | {entity['Score']:.2f}")
```

**Output:**
```
  Amazon               | ORGANIZATION    | 0.99
  Q4 2024              | DATE            | 0.98
  Andy Jassy           | PERSON          | 0.99
  Seattle              | LOCATION        | 0.99
```

---

## 7.5 Amazon Translate

**Purpose:** Neural machine translation between languages.

### Step-by-Step: Use Amazon Translate (via Console UI)

1. **Navigate to Translate**
   - AWS Console → Search **"Translate"** → Click the service

2. **Real-Time Translation**
   - Click **"Real-time translation"**
   - Select source language: **English**
   - Select target language: **French**
   - Type: `Cloud computing enables businesses to scale globally.`
   - Translation appears instantly:
     ```
     Le cloud computing permet aux entreprises de se développer à l'échelle mondiale.
     ```

### Sample Code: Translate Text

```python
import boto3

translate = boto3.client('translate', region_name='us-east-1')

response = translate.translate_text(
    Text="Cloud computing enables businesses to scale globally.",
    SourceLanguageCode='en',
    TargetLanguageCode='fr'
)

print(f"Translation: {response['TranslatedText']}")
```

**Output:**
```
Translation: Le cloud computing permet aux entreprises de se développer à l'échelle mondiale.
```

---

## 7.6 Amazon Polly

**Purpose:** Turn text into lifelike speech using deep learning.

### Step-by-Step: Use Amazon Polly (via Console UI)

1. **Navigate to Polly**
   - AWS Console → Search **"Polly"** → Click the service

2. **Synthesize Speech**
   - Click **"Text-to-Speech"**
   - Select a voice (e.g., **Joanna** - US English, Female)
   - Select engine: **Neural** (more natural) or **Standard**
   - Type text: `Welcome to AWS. Let's learn about cloud computing.`
   - Click **"Listen"** to hear the speech
   - Click **"Download"** to save as MP3

### Sample Code: Generate Speech

```python
import boto3

polly = boto3.client('polly', region_name='us-east-1')

response = polly.synthesize_speech(
    Text='Welcome to AWS. Let us learn about cloud computing.',
    OutputFormat='mp3',
    VoiceId='Joanna',
    Engine='neural'
)

with open('speech.mp3', 'wb') as f:
    f.write(response['AudioStream'].read())

print("Speech saved as speech.mp3")
```

### Polly Advanced Features

| Feature | Description | Example |
|---------|-------------|---------|
| **Lexicons** | Define how to read specific text | "AWS" → "Amazon Web Services" |
| **SSML** | Speech Synthesis Markup Language — control pronunciation | `"Hello, <break> how are you?"` adds a pause |
| **Voice Engines** | Generative, long-form, neural, standard | Neural voices sound most natural |
| **Speech Marks** | Encode where sentences/words start and end in audio | Lip-syncing, highlighting words as spoken |

---

## 7.7 Amazon Transcribe

**Purpose:** Automatically convert speech to text using deep learning (ASR — Automatic Speech Recognition).

### Key Features

| Feature | Description |
|---------|-------------|
| **Real-time transcription** | Transcribe live audio streams |
| **Batch transcription** | Transcribe audio files (MP3, WAV, FLAC) |
| **Speaker identification** | Identify different speakers in a conversation |
| **PII Redaction** | Automatically remove Personally Identifiable Information |
| **Automatic Language ID** | Identify language in multi-lingual audio |
| **Subtitles** | Generate SRT/VTT subtitle files |
| **Toxicity Detection** | ML-powered voice-based toxicity detection using tone, pitch, and text cues |

### Improving Transcription Accuracy

| Method | What It Does | Best For |
|--------|-------------|----------|
| **Custom Vocabularies** | Add specific words, phrases, domain terms, brand names, acronyms | Recognizing new words; provide pronunciation hints |
| **Custom Language Models** | Train Transcribe on your own domain-specific text data | Large volumes of domain-specific speech; learning word context |

> Use **both** Custom Vocabularies and Custom Language Models together for highest accuracy.

```
Before Custom Vocabulary:  "... A USA My crow services ..."
After Custom Vocabulary:   "... AWS Microservices ..."
```

### Step-by-Step: Use Amazon Transcribe (via Console UI)

1. **Navigate to Transcribe**
   - AWS Console → Search **"Transcribe"** → Click the service

2. **Create a Transcription Job**
   - Click **"Transcription jobs"** → **"Create job"**
   - Enter a job name
   - Select input data location (S3 URI of your audio file)
   - Select output location (S3 bucket for results)
   - Click **"Create job"**

3. **View Results**
   - Wait for the job to complete
   - Click on the job name to view the transcript
   - Download the JSON output with timestamps and confidence scores

---

## 7.8 Amazon Lex

**Purpose:** Build conversational chatbots with voice and text interfaces.

> Amazon Lex is the same technology that powers **Amazon Alexa**.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Intent** | What the user wants to do (e.g., "BookHotel", "OrderPizza") |
| **Utterance** | What the user says to trigger an intent ("I want to book a hotel") |
| **Slot** | Information needed to fulfill the intent (city, date, room type) |
| **Fulfillment** | Action taken after all slots are filled (call Lambda function) |

### Step-by-Step: Create a Simple Chatbot (via Console UI)

1. **Navigate to Lex**
   - AWS Console → Search **"Lex"** → Click **Amazon Lex**

2. **Create a Bot**
   - Click **"Create bot"**
   - Choose **"Create a blank bot"**
   - Enter bot name: `HotelBookingBot`
   - Select language: **English (US)**
   - Click **"Create"**

3. **Create an Intent**
   - Click **"Add intent"** → **"Add empty intent"**
   - Name: `BookHotel`
   - Add sample utterances:
     - "I want to book a hotel"
     - "Book a room for me"
     - "I need a hotel in {City}"

4. **Add Slots**
   - Add slot: `City` (type: AMAZON.City) — "Which city?"
   - Add slot: `CheckInDate` (type: AMAZON.Date) — "What date?"
   - Add slot: `Nights` (type: AMAZON.Number) — "How many nights?"

5. **Build and Test**
   - Click **"Build"**
   - Click **"Test"** to open the test chat window
   - Type: "I want to book a hotel"
   - The bot asks for City, Date, and Nights in sequence

---

## 7.9 Amazon Kendra

**Purpose:** Intelligent enterprise search powered by ML.

Unlike traditional keyword search, Kendra understands natural language questions and returns precise answers.

```
Traditional Search:                    Amazon Kendra:
Query: "vacation policy"               Query: "How many vacation days
                                               do new employees get?"
Result: List of documents               
containing "vacation" and              Result: "New employees receive
"policy" keywords                      15 vacation days per year."
                                       Source: HR Policy Doc, Page 12
```

### Step-by-Step: Set Up Amazon Kendra (via Console UI)

1. **Navigate to Kendra**
   - AWS Console → Search **"Kendra"** → Click the service

2. **Create an Index**
   - Click **"Create index"**
   - Enter index name and description
   - Select an IAM role
   - Choose edition (Developer for testing, Enterprise for production)
   - Click **"Create"**

3. **Add a Data Source**
   - Click **"Add data source"**
   - Choose connector type (S3, SharePoint, Confluence, etc.)
   - Configure the connection
   - Click **"Add data source"** → **"Sync now"**

4. **Search**
   - Click **"Search indexed content"**
   - Type a natural language question
   - View the answer with source document citations

---

## 7.10 Amazon Personalize

**Purpose:** Build real-time personalized recommendations.

### Use Cases

| Use Case | Example |
|----------|---------|
| **Product Recommendations** | "Customers who bought X also bought Y" |
| **Content Recommendations** | "Movies you might like" |
| **Personalized Search** | Search results ranked by user preferences |
| **Personalized Emails** | Tailored product suggestions in marketing emails |

### Personalize Recipes

Recipes are pre-built algorithms for specific recommendation use cases:

| Recipe Type | Example Recipe | Use Case |
|------------|---------------|----------|
| **User Personalization** | User-Personalization-v2 | Recommend items for individual users |
| **Personalized Ranking** | Personalized-Ranking-v2 | Rank items for a specific user |
| **Popular Items** | Trending-Now, Popularity-Count | Recommend trending or popular items |
| **Related Items** | Similar-Items | Recommend items similar to what user is viewing |
| **Next Best Action** | Next-Best-Action | Recommend the next action for a user |
| **User Segmentation** | Item-Affinity | Get user segments based on item preferences |

### Integration

Integrates with existing websites, applications, SMS, and email marketing systems. Same technology used by Amazon.com. Implement in **days, not months**.

### Real-Life Use Case

> **Example: E-commerce Recommendations**
> An online bookstore uses Amazon Personalize to recommend books. When a user browses mystery novels, the system learns their preferences and suggests similar titles. Over time, as the user interacts with more books, recommendations become more accurate — increasing sales by 15-30%.

---

## 7.11 Amazon Forecast

**Purpose:** Time-series forecasting using ML.

### Use Cases

| Use Case | Example |
|----------|---------|
| **Demand Forecasting** | Predict product demand for inventory planning |
| **Revenue Forecasting** | Predict future revenue based on historical data |
| **Resource Planning** | Predict server capacity needs |
| **Financial Planning** | Forecast cash flow and expenses |

---

## 7.12 Amazon Fraud Detector

**Purpose:** Identify potentially fraudulent online activities.

### Use Cases

| Use Case | Example |
|----------|---------|
| **Online Payment Fraud** | Flag suspicious credit card transactions |
| **New Account Fraud** | Detect fake account registrations |
| **Account Takeover** | Identify unauthorized account access |
| **Loyalty Program Abuse** | Detect fraudulent reward claims |

---

---

## 7.13 Amazon Mechanical Turk

A crowdsourcing marketplace to perform simple human tasks using a distributed virtual workforce.

| Feature | Description |
|---------|-------------|
| **Purpose** | Distribute tasks to human workers at scale |
| **Example** | Label 10,000,000 images at $0.10 per image |
| **Use Cases** | Image classification, data collection, business processing |
| **Integration** | Works with Amazon A2I, SageMaker Ground Truth |

---

## 7.14 Amazon Augmented AI (A2I)

Human oversight of ML predictions in production.

```
┌──────────┐     ┌──────────────┐     ┌──────────────────────┐
│ Input    │────>│ ML Model     │────>│ High confidence?     │
│ Data     │     │ (SageMaker,  │     │                      │
│          │     │  Rekognition)│     │ YES → Return to app  │
│          │     │              │     │ NO  → Human review   │
└──────────┘     └──────────────┘     └──────────┬───────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────┐
                                        │ Human Reviewers  │
                                        │ - Your employees │
                                        │ - 500K+ AWS      │
                                        │   contractors    │
                                        │ - Mechanical Turk│
                                        └────────┬─────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────┐
                                        │ Consolidated     │
                                        │ reviews (S3)     │
                                        │ → Can improve    │
                                        │   training data  │
                                        └──────────────────┘
```

- Some vendors are pre-screened for confidentiality requirements
- Reviewed data can be added to training datasets to improve models

---

## 7.15 Healthcare AI Services

### Amazon Transcribe Medical

| Feature | Description |
|---------|-------------|
| **Purpose** | Convert medical speech to text (HIPAA compliant) |
| **Terminology** | Medicine names, procedures, conditions, diseases |
| **Modes** | Real-time (microphone) and batch (upload files) |
| **Use Cases** | Physician dictation, drug safety call transcription |

### Amazon Comprehend Medical

| Feature | Description |
|---------|-------------|
| **Purpose** | Detect useful information in unstructured clinical text |
| **Input Types** | Physician's notes, discharge summaries, test results, case notes |
| **PHI Detection** | Uses NLP to detect Protected Health Information (DetectPHI API) |
| **Integration** | S3 for stored documents, Kinesis for real-time, Transcribe for audio → text |

### AWS HealthScribe

| Feature | Description |
|---------|-------------|
| **Purpose** | Automatically generate clinical notes from patient-clinician conversations (HIPAA eligible) |
| **Capabilities** | Rich transcripts, speaker role identification, dialogue classification, medical term extraction |
| **Use Cases** | Reduce documentation time, AI-generated clinical notes, efficient patient visit recaps |

---

## 7.16 Amazon EC2 for AI/ML

### EC2 Overview

EC2 (Elastic Compute Cloud) provides virtual machines in the cloud. For AI/ML workloads, specialized hardware is available.

### AWS AI Hardware

| Hardware | Purpose | Instance Types | Key Benefit |
|----------|---------|---------------|-------------|
| **GPU-based EC2** | General ML training and inference | P3, P4, P5, G3-G6 | Standard GPU acceleration |
| **AWS Trainium** | Deep Learning training (100B+ parameter models) | Trn1 (16 Trainium Accelerators) | **50% cost reduction** for training |
| **AWS Inferentia** | High-performance, low-cost inference | Inf1, Inf2 | **Up to 4x throughput, 70% cost reduction** |

> **Key Exam Point:** Trainium is for **training**, Inferentia is for **inference**. Both have the **lowest environmental footprint** among AWS ML chips.

---

## Module 7 Summary

| Service | Purpose | Key Feature |
|---------|---------|-------------|
| **Rekognition** | Image/video analysis | Object detection, facial analysis, content moderation, custom labels |
| **Textract** | Document processing | Extract text, forms, tables from scanned documents |
| **Comprehend** | NLP text analysis | Sentiment, entities, key phrases, PII, custom classification, custom NER |
| **Translate** | Language translation | 75+ languages, real-time translation |
| **Polly** | Text-to-Speech | Neural voices, lexicons, SSML, speech marks |
| **Transcribe** | Speech-to-Text | Custom vocabularies, custom language models, toxicity detection |
| **Lex** | Chatbots | Same tech as Alexa, intents + slots |
| **Kendra** | Enterprise search | Natural language Q&A, incremental learning |
| **Personalize** | Recommendations | Recipes for user personalization, ranking, trending, similar items |
| **Forecast** | Time-series prediction | Demand, revenue, resource forecasting |
| **Fraud Detector** | Fraud detection | Payment fraud, account takeover detection |
| **Mechanical Turk** | Human task marketplace | Crowdsourced labeling, data collection |
| **A2I** | Human oversight of ML | Route low-confidence predictions to human reviewers |
| **Transcribe Medical** | Medical speech-to-text | HIPAA compliant, medical terminology |
| **Comprehend Medical** | Medical NLP | PHI detection, clinical text analysis |
| **HealthScribe** | Clinical note generation | Auto-generate notes from patient conversations |
| **Trainium** | ML training hardware | 50% cost reduction for deep learning training |
| **Inferentia** | ML inference hardware | 4x throughput, 70% cost reduction for inference |

---

*Previous: [Module 6 — AI and Machine Learning](module-06-ai-and-machine-learning.md)*
*Next: [Module 8 — Amazon SageMaker](module-08-amazon-sagemaker.md)*
