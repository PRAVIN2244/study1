# Module 3: Generative AI and Foundation Models

## 3.1 What is Generative AI?

Generative AI (Gen-AI) is a subset of Deep Learning used to **generate new data** that is similar to the data it was trained on.

**Types of content Gen-AI can create:**

| Content Type | Example | Tools |
|-------------|---------|-------|
| **Text** | Articles, emails, code, summaries | ChatGPT, Claude, Amazon Titan |
| **Images** | Photos, illustrations, art | DALL-E, Stable Diffusion, Midjourney |
| **Audio** | Music, voice cloning, sound effects | Suno, ElevenLabs |
| **Code** | Functions, applications, scripts | GitHub Copilot, Amazon CodeWhisperer |
| **Video** | Short clips, animations | Sora, Runway |

### How Generative AI Works (High Level)

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Training Data │────>│ Generative Model │────>│ New Content      │
│ (text, images,│     │ (learns patterns)│     │ (text, images,   │
│  audio, code) │     │                  │     │  audio, code)    │
└──────────────┘     └──────────────────┘     └──────────────────┘
```

1. A model is trained on massive amounts of unlabeled data
2. The model learns patterns, structures, and relationships in the data
3. Given a prompt, the model generates new content that follows those learned patterns

### Real-Life Use Case

> **Example: Marketing Content Generation**
> A marketing team uses Gen-AI to draft 50 variations of ad copy for A/B testing. Instead of a copywriter spending days writing each version, the AI generates them in seconds. The team reviews, edits, and selects the best ones — reducing content creation time by 90%.

---

## 3.2 Foundation Models

A **Foundation Model** is a large AI model trained on a wide variety of input data that can be adapted for a broad range of tasks.

### Key Characteristics

| Property | Details |
|----------|---------|
| **Training Cost** | Tens of millions of dollars |
| **Training Data** | Books, articles, websites, code, images — vast and diverse |
| **Versatility** | One model, many tasks (text generation, summarization, Q&A, translation) |
| **Adaptation** | Can be fine-tuned for specific use cases |

### The Foundation Model Workflow

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│ Unlabeled    │     │ Foundation Model │     │ Broad Range of Tasks │
│ Data         │────>│                  │────>│                      │
│ (pretrain)   │     │                  │     │ - Text Generation    │
│              │     │                  │     │ - Summarization      │
│              │     │                  │     │ - Info Extraction    │
│              │     │                  │     │ - Image Generation   │
│              │     │                  │     │ - Chatbot            │
│              │     │                  │     │ - Q&A                │
└──────────────┘     └──────────────────┘     └──────────────────────┘
                           │
                           │ Adapt / Fine-tune
                           ▼
                     ┌──────────────────┐
                     │ Specialized Task │
                     │ (e.g., medical   │
                     │  diagnosis)      │
                     └──────────────────┘
```

### Major Foundation Model Providers

| Provider | Models | License |
|----------|--------|---------|
| **OpenAI** | GPT-4, GPT-4o | Commercial (paid API) |
| **Anthropic** | Claude 3, Claude 3.5 | Commercial (paid API) |
| **Meta (Facebook)** | LLaMA 2, LLaMA 3 | Open-source (free) |
| **Google** | Gemini, BERT, PaLM | Mixed (BERT is open-source) |
| **Amazon** | Amazon Titan | Commercial (via Bedrock) |
| **Stability AI** | Stable Diffusion | Open-source (free) |

> **Key Exam Point:** Some foundation models are open-source (free to use: Meta's LLaMA, Google's BERT) while others require a commercial license (OpenAI's GPT-4, Anthropic's Claude).

### Real-Life Use Case

> **Example: GPT-4o as a Foundation Model**
> GPT-4o is the foundation model behind ChatGPT. OpenAI trained it on a massive dataset of text from the internet. Users interact with it through ChatGPT's interface, but the underlying model can also be accessed via API for custom applications — customer support bots, content generators, code assistants, etc.

---

## 3.3 Large Language Models (LLMs)

A **Large Language Model** is a type of AI designed to generate coherent, human-like text.

### Key Properties

| Property | Details |
|----------|---------|
| **Size** | Billions of parameters (GPT-4 has ~1.7 trillion) |
| **Training Data** | Books, articles, websites, code, and other textual data |
| **Capabilities** | Translation, summarization, Q&A, content creation, code generation |
| **Notable Example** | GPT-4 (powers ChatGPT by OpenAI) |

### How LLMs Generate Text

LLMs are **non-deterministic** — the same prompt can produce different outputs each time.

**Step 1: User provides a prompt**
```
User: "What is AWS?"
```

**Step 2: Model generates probability distribution for the next word**
```
After "After the rain, the streets were"

Word        Probability
─────────── ───────────
wet         0.40
flooded     0.25
slippery    0.15
empty       0.10
muddy       0.05
clean       0.03
blocked     0.02
```

**Step 3: Algorithm selects a word based on probability (with randomness)**
```
Selected: "flooded" (chosen randomly, weighted by probability)
```

**Step 4: Process repeats for the next word**
```
After "After the rain, the streets were flooded"

Word        Probability
─────────── ───────────
and         0.30
with        0.20
but         0.15
from        0.12
until       0.10
because     0.08
.           0.05
```

**Step 5: Continue until the response is complete**

> **Key Exam Point:** LLMs are non-deterministic — the generated text may be different for every user using the same prompt. This is because word selection involves randomness weighted by probability.

### Sample Code: Calling an LLM via AWS Bedrock (Python)

```python
import boto3
import json

# Create a Bedrock Runtime client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Define the prompt
prompt = "What is AWS?"

# Call the model (using Amazon Titan Text)
response = bedrock.invoke_model(
    modelId='amazon.titan-text-express-v1',
    body=json.dumps({
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0.7,    # Higher = more random/creative
            "topP": 0.9
        }
    }),
    contentType='application/json',
    accept='application/json'
)

# Parse the response
result = json.loads(response['body'].read())
print(result['results'][0]['outputText'])
```

**Output:**
```
AWS (Amazon Web Services) is a cloud computing platform provided by
Amazon that offers a wide range of services including computing power,
storage, databases, machine learning, and more. It allows businesses
and individuals to access IT resources on-demand with pay-as-you-go
pricing, eliminating the need to invest in physical infrastructure.
```

**Code Explanation:**
- `boto3.client('bedrock-runtime')` — Creates a client to interact with Amazon Bedrock
- `modelId` — Specifies which foundation model to use
- `temperature` — Controls randomness (0 = deterministic, 1 = very creative)
- `topP` — Controls diversity of word selection (0.9 means consider top 90% probable words)
- `maxTokenCount` — Maximum length of the generated response

---

## 3.4 Generative AI for Images

Gen-AI can work with images in three ways:

### 3.4.1 Text-to-Image Generation

Generate images from text descriptions (prompts).

```
Prompt: "Generate a blue sky with white clouds
         and the word 'Hello' written in the sky"

Result: [AI-generated image matching the description]
```

### 3.4.2 Image-to-Image Transformation

Transform existing images into new styles.

```
Input:  [Original photograph]
Prompt: "Transform this image in Japanese anime style"
Result: [Same scene rendered in anime art style]
```

### 3.4.3 Image-to-Text (Visual Understanding)

Generate text descriptions from images.

```
Input:  [Photo of fruits]
Prompt: "Describe how many apples you see in the picture"
Result: "The picture shows one apple. The other fruit is an orange."
```

### Step-by-Step: Generate Images with Amazon Bedrock (via Console UI)

1. **Navigate to Amazon Bedrock**
   - Go to [https://console.aws.amazon.com](https://console.aws.amazon.com)
   - Search for **"Bedrock"** in the search bar
   - Click **Amazon Bedrock**

2. **Enable Model Access**
   - In the left sidebar, click **"Model access"**
   - Click **"Manage model access"**
   - Check the box next to **Stability AI** (for Stable Diffusion) or **Amazon** (for Titan Image Generator)
   - Click **"Save changes"**
   - Wait for access to be granted (usually instant)

3. **Open the Image Playground**
   - In the left sidebar, click **"Playgrounds"** → **"Image"**
   - Select a model (e.g., **Stable Diffusion XL** or **Amazon Titan Image Generator**)

4. **Generate an Image**
   - In the prompt box, type: `A futuristic city skyline at sunset with flying cars`
   - Click **"Run"** or **"Generate"**
   - Wait 10-30 seconds for the image to appear

5. **View and Download**
   - The generated image appears in the output panel
   - Click to download or copy

### Real-Life Use Case

> **Example: E-commerce Product Visualization**
> An online furniture store uses image generation AI to show customers how a sofa would look in different colors and fabrics. Instead of photographing every variation (expensive), they generate realistic images from a single base photo — saving thousands in photography costs.

---

## 3.5 Diffusion Models

Diffusion models (like Stable Diffusion) are the technology behind most image generation AI.

### How Diffusion Models Work

**Training Phase: Forward Diffusion**
```
Original Image ──► Add Noise ──► Add More Noise ──► Pure Noise
[Clear photo]      [Slightly      [Very noisy]       [Random
                    noisy]                             static]
```

The model learns to understand how noise is added to images at each step.

**Generation Phase: Reverse Diffusion**
```
Pure Noise ──► Remove Noise ──► Remove More Noise ──► Generated Image
[Random        [Shapes           [Recognizable         [Clear image
 static]        emerging]          features]             of a cat]

                    Guided by prompt:
                    "a cat with a computer"
```

The model reverses the process — starting from random noise and gradually removing it, guided by the text prompt, until a clear image emerges.

### Step-by-Step Breakdown

1. **Start with random noise** (like TV static)
2. **The model predicts what noise to remove** at each step
3. **The text prompt guides the process** — "a cat with a computer" tells the model what shapes and features to reveal
4. **After many steps** (typically 20-50), a clear image emerges
5. **Each generation is unique** — even the same prompt produces different images

### Sample Code: Generate Image with Stable Diffusion on Bedrock (Python)

```python
import boto3
import json
import base64

# Create Bedrock Runtime client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Define the prompt
prompt = "A futuristic city skyline at sunset with flying cars"

# Call Stable Diffusion model
response = bedrock.invoke_model(
    modelId='stability.stable-diffusion-xl-v1',
    body=json.dumps({
        "text_prompts": [
            {"text": prompt, "weight": 1.0}
        ],
        "cfg_scale": 7,        # How closely to follow the prompt (1-35)
        "steps": 50,           # Number of diffusion steps
        "seed": 42,            # For reproducibility (optional)
        "width": 1024,
        "height": 1024
    }),
    contentType='application/json',
    accept='application/json'
)

# Parse and save the image
result = json.loads(response['body'].read())
image_data = base64.b64decode(result['artifacts'][0]['base64'])

with open('generated_image.png', 'wb') as f:
    f.write(image_data)

print("Image saved as generated_image.png")
```

**Output:**
```
Image saved as generated_image.png
```

**Code Explanation:**
- `cfg_scale` — Controls how strictly the model follows the prompt (higher = more literal)
- `steps` — Number of denoising steps (more steps = higher quality but slower)
- `seed` — Random seed for reproducibility (same seed + same prompt = same image)
- `width/height` — Output image dimensions
- The response contains a base64-encoded image that we decode and save

---

## 3.6 Key Concepts for the Exam

| Concept | Definition | Example |
|---------|-----------|---------|
| **Generative AI** | Subset of Deep Learning that creates new content | ChatGPT generating text |
| **Foundation Model** | Large model trained on diverse data, adaptable to many tasks | GPT-4, Claude, Titan |
| **LLM** | Foundation model specialized in text generation | GPT-4, LLaMA |
| **Non-deterministic** | Same input can produce different outputs | Two users asking the same question get different answers |
| **Temperature** | Controls randomness in text generation (0=deterministic, 1=creative) | Low temp for factual answers, high for creative writing |
| **Diffusion Model** | Generates images by learning to reverse a noise-adding process | Stable Diffusion, DALL-E |
| **Open-source vs Commercial** | Some models are free (LLaMA), others require payment (GPT-4) | Meta's LLaMA vs OpenAI's GPT-4 |
| **Prompt** | The input/instruction given to a Gen-AI model | "Write a poem about clouds" |

---

## Module 3 Summary

| Topic | Key Takeaway |
|-------|-------------|
| Generative AI | Subset of Deep Learning that generates new text, images, audio, code, video |
| Foundation Models | Expensive to train, versatile, can be adapted for specific tasks |
| LLMs | Generate text word-by-word using probability distributions; non-deterministic |
| Image Generation | Text-to-image, image-to-image, image-to-text capabilities |
| Diffusion Models | Learn to add noise (training) then reverse the process (generation) |
| Amazon Bedrock | AWS service providing access to multiple foundation models via API and console |

---

*Previous: [Module 2 — AWS and Cloud Computing](module-02-aws-and-cloud-computing.md)*
*Next: [Module 3B — Amazon Bedrock Deep Dive](module-03b-amazon-bedrock.md)*
