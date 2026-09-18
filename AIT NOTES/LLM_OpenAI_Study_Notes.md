# LLM & OpenAI GPT --- Study Notes

## 1. What is an LLM?

**LLM = Large Language Model**

An LLM is an AI model trained on a huge amount of data to understand and
generate human-like language.

### Examples

1.  OpenAI GPT
2.  Google Gemini
3.  Meta Llama
4.  DeepSeek R1
5.  Anthropic Claude

An LLM is a machine-learning model that can read text, understand
context, and generate meaningful responses.

### What can an LLM do?

-   Answer questions
-   Write emails
-   Summarize documents
-   Translate languages
-   Generate code
-   Explain code
-   Generate images
-   Generate audio and video
-   Generate presentations/PPTs

------------------------------------------------------------------------

## 2. Normal Python Program vs LLM-Based Program

### Normal Python Program

``` python
name = "Ashok"
print(name)
```

**Output:**

``` text
Ashok
```

A normal program produces output according to the fixed instructions
written by the programmer.

### LLM-Based Program

**User prompt:**

``` text
Explain Python list with examples
```

**Possible LLM response:**

``` text
A list in Python is used to store multiple values in a single variable.
```

Example:

``` python
my_list = [10, 20, 30, 40]
```

Here, the LLM interprets the user's question and generates a response
according to the prompt and its available context.

------------------------------------------------------------------------

## 3. How an LLM Works Internally

A simplified flow is:

``` text
User Prompt
    ↓
Tokenization
    ↓
LLM Processing
    ↓
Predict Next Token
    ↓
Repeat Token Prediction
    ↓
Generated Response
```

### Step 1 --- User Input / Prompt

The user provides an instruction or question.

Example:

``` text
Explain Python lists.
```

### Step 2 --- Tokenization

The input is converted into **tokens**.

### Step 3 --- LLM Execution

The model processes the tokens using the patterns and relationships
learned during training, together with the current context.

### Step 4 --- Predict the Next Token

The model estimates which token should come next.

### Step 5 --- Generate the Response

Next-token prediction continues repeatedly until the response is
complete.

------------------------------------------------------------------------

## 4. What is Tokenization?

LLMs do not process text exactly the way humans read words. Text is
converted into smaller units called **tokens**.

A simplified example:

``` text
Input: I love Python

Possible conceptual tokens:
["I", "love", "Python"]
```

A word can also be represented by more than one token.

``` text
Input: Generative

Conceptual illustration:
["Gener", "ative"]
```

> **Important:** These examples are only illustrations. The exact tokens
> depend on the tokenizer used by the specific model.

------------------------------------------------------------------------

## 5. What Does an LLM Actually Do?

At generation time, an LLM repeatedly predicts the next token based on
the tokens already present in the context.

Example:

``` text
Input:
Python is a programming

Likely continuation:
language
```

The process continues token by token:

``` text
Python → is → a → programming → language → ...
```

This repeated prediction produces sentences, paragraphs, code, and other
text outputs.

------------------------------------------------------------------------

## 6. Why Are LLMs Called "Large"?

They are called large because modern LLM development typically involves:

1.  Very large datasets
2.  Huge quantities of text and other training data
3.  Large numbers of learned parameters
4.  Powerful computing infrastructure such as GPUs/accelerators
5.  Advanced deep-learning architectures, especially Transformers

### What is a parameter?

A **parameter** is a learned numerical value inside a neural network.
During training, the model adjusts large numbers of these values so it
can better model relationships and patterns in data.

------------------------------------------------------------------------

## 7. LLM vs Traditional Software

  -----------------------------------------------------------------------
  Traditional Software                LLM-Based Software
  ----------------------------------- -----------------------------------
  Primarily follows explicitly        Uses a trained model to generate
  programmed rules and logic          outputs

  Usually deterministic for the same  Can generate different outputs
  state/input                         depending on model/settings/context

  Programmer defines processing logic Much behavior is learned from
                                      training data

  Natural-language understanding      Designed to work directly with
  requires explicit components/logic  natural-language prompts

  Example: calculator                 Example: ChatGPT-style assistant
  -----------------------------------------------------------------------

LLMs do not think exactly like humans. They generate outputs using
learned statistical patterns, model computation, and the context
supplied to them.

------------------------------------------------------------------------

## 8. Paid, Free, and Open-Weight LLMs

The terms **paid**, **free**, and **open-source/open-weight** describe
different things, so they should not be treated as exact opposites.

### Paid/API-Based Services

Examples may include services from:

-   OpenAI
-   Anthropic
-   Google
-   Cohere

Charges may depend on:

-   Input tokens
-   Output tokens
-   API usage
-   Subscription plans
-   Enterprise plans
-   Additional platform features

### Advantages of Hosted/API Models

-   Easy to start
-   No need to manage model-serving infrastructure
-   Access to managed models and platform features
-   Scaling and maintenance are largely handled by the provider

### Possible Disadvantages

-   Usage costs
-   Internet/network dependency
-   Vendor dependency
-   Privacy/compliance considerations
-   Rate limits such as requests per minute (RPM)

### Free Access / Open Models

Examples can include:

-   Free tiers of ChatGPT or other AI services
-   Llama-family models
-   Mistral-family models
-   DeepSeek-family models

Some models can be downloaded and run locally when their licenses and
hardware requirements permit it.

### Advantages of Locally Run/Open Models

-   Greater control
-   Potential privacy benefits
-   Customization possibilities
-   Potentially lower marginal usage cost

### Disadvantages

-   Hardware requirements
-   Setup complexity
-   Model serving and maintenance
-   Performance depends heavily on available hardware and model size

------------------------------------------------------------------------

# GenAI Project Development Using an OpenAI Model

## 9. Project Overview

We will create a simple Python application that:

``` text
User Prompt
    ↓
Python Application
    ↓
OpenAI API
    ↓
Model
    ↓
Generated Response
    ↓
Application displays response
```

------------------------------------------------------------------------

## 10. Step 0 --- Create an OpenAI Platform Account and API Key

Create/configure an account in the OpenAI developer platform, set up
billing if required for your API usage, and create an API key.

**Security rule:** Never publish or hard-code a real API key in source
code, screenshots, Git repositories, or shared notes.

------------------------------------------------------------------------

## 11. Step 1 --- Create the Project Folder

Example folder name:

``` text
01-openai-gpt-chat-bot
```

A possible project structure is:

``` text
01-openai-gpt-chat-bot/
│
├── main.py
├── app.py
├── requirements.txt
├── .env
└── venv/
```

------------------------------------------------------------------------

## 12. Step 2 --- Create a Python Virtual Environment

Move into the project folder:

``` bash
cd 01-openai-gpt-chat-bot
```

Create a virtual environment:

``` bash
python -m venv venv
```

On Windows, activate it with:

``` bash
venv\Scripts\activate
```

A virtual environment keeps the Python packages for this project
separate from packages used by other projects.

------------------------------------------------------------------------

## 13. Step 3 --- Create `requirements.txt`

The screenshot contains:

``` text
openai
python-dotenv
streamlit
```

Install the dependencies:

``` bash
pip install -r requirements.txt
```

### What each package does

**`openai`**\
Provides the Python SDK used to communicate with the OpenAI API.

**`python-dotenv`**\
Loads environment variables from a `.env` file.

**`streamlit`**\
Allows us to build a simple web UI using Python.

------------------------------------------------------------------------

## 14. Step 4 --- Create the `.env` File

Create:

``` text
.env
```

Add:

``` env
OPENAI_API_KEY=your_api_key_here
```

Do **not** put your real key into notes or GitHub.

It is also good practice to add `.env` to `.gitignore`:

``` gitignore
.env
venv/
__pycache__/
```

------------------------------------------------------------------------

## 15. Step 5 --- Create `main.py`

The screenshots show this basic structure:

``` python
from openai import OpenAI
from dotenv import load_dotenv
import os

print("hello")

# Load environment variables
load_dotenv()

# Read OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Function to call GPT model
def ask_gpt(user_input):
    response = client.responses.create(
        model="gpt-5-mini",
        input=user_input
    )

    return response.output_text
```

> Model availability and exact model IDs can change. Use a model
> currently available to your API project.

------------------------------------------------------------------------

# 16. Explanation of `main.py` Line by Line

## Import `OpenAI`

``` python
from openai import OpenAI
```

This imports the `OpenAI` client class from the OpenAI Python package.

It lets us create a client that communicates with the OpenAI API.

------------------------------------------------------------------------

## Import `load_dotenv`

``` python
from dotenv import load_dotenv
```

This imports a function from `python-dotenv`.

Its job is to read variables stored in the `.env` file and make them
available as environment variables.

------------------------------------------------------------------------

## Import `os`

``` python
import os
```

`os` is part of Python's standard library.

Here it is used to retrieve an environment variable.

------------------------------------------------------------------------

## Load the `.env` File

``` python
load_dotenv()
```

Suppose `.env` contains:

``` env
OPENAI_API_KEY=your_api_key_here
```

After `load_dotenv()` runs, Python can access `OPENAI_API_KEY`.

------------------------------------------------------------------------

## Read the API Key

``` python
api_key = os.getenv("OPENAI_API_KEY")
```

Breakdown:

``` text
os
└── getenv()
      └── searches for OPENAI_API_KEY
             ↓
       returns its value
             ↓
       stored in api_key
```

If the variable does not exist, `os.getenv()` normally returns `None`.

------------------------------------------------------------------------

## Create the OpenAI Client

``` python
client = OpenAI(api_key=api_key)
```

Conceptually:

``` text
Python Program
     ↓
OpenAI Client
     ↓
Authentication using API key
     ↓
OpenAI API
```

`client` becomes the object through which the program makes API
requests.

------------------------------------------------------------------------

# 17. Creating the `ask_gpt()` Function

``` python
def ask_gpt(user_input):
```

This creates a function named `ask_gpt`.

`user_input` contains the prompt supplied by the user.

Example:

``` python
ask_gpt("Explain Python lists")
```

Inside the function:

``` python
response = client.responses.create(
    model="gpt-5-mini",
    input=user_input
)
```

### `client.responses.create(...)`

This sends a request through the OpenAI Responses API.

### `model=...`

Selects the model that should process the request.

### `input=user_input`

Passes the user's prompt to the model.

The result is stored in:

``` python
response
```

Finally:

``` python
return response.output_text
```

This extracts the generated text and returns it to the caller.

------------------------------------------------------------------------

## 18. Calling the Function

For example:

``` python
answer = ask_gpt("Explain Python list with an example")
print(answer)
```

The exact output is generated dynamically, so it can vary. A possible
output is:

``` text
A Python list is an ordered collection that can store multiple values.

Example:
numbers = [10, 20, 30, 40]
```

------------------------------------------------------------------------

# 19. Complete Request Flow

``` text
User
  │
  │ "Explain Python lists"
  ▼
ask_gpt(user_input)
  │
  ▼
client.responses.create(...)
  │
  │ API request
  ▼
OpenAI API
  │
  ▼
Selected Model
  │
  │ generated output
  ▼
response
  │
  ▼
response.output_text
  │
  ▼
return answer
  │
  ▼
User/Application
```

------------------------------------------------------------------------

# 20. Step 6 --- Create `app.py` with Streamlit

A simple UI can look like this:

``` python
import streamlit as st
from main import ask_gpt

st.title("My GPT Chatbot")

prompt = st.text_input("Enter your question:")

if st.button("Ask"):
    if prompt:
        answer = ask_gpt(prompt)
        st.write(answer)
```

### How the files are linked

``` text
app.py
   │
   │ from main import ask_gpt
   ▼
main.py
   │
   │ OpenAI SDK
   ▼
OpenAI API
   │
   ▼
Model
   │
   ▼
Response
   │
   ▼
app.py
   │
   ▼
Browser UI
```

`app.py` handles the user interface, while `main.py` contains the OpenAI
API logic.

------------------------------------------------------------------------

# 21. Step 7 --- Run the Application

Run:

``` bash
streamlit run app.py
```

Streamlit starts a local web application and displays the chatbot
interface in the browser.

------------------------------------------------------------------------

# 22. How All Project Files Work Together

``` text
requirements.txt
      │
      └── defines required Python packages

.env
      │
      └── stores OPENAI_API_KEY securely
                 │
                 ▼
main.py ─── load_dotenv()
      │
      ├── reads OPENAI_API_KEY
      ├── creates OpenAI client
      └── defines ask_gpt()
                 ▲
                 │ import
                 │
app.py ──────────┘
      │
      ├── gets prompt from user
      ├── calls ask_gpt()
      └── displays generated response
```

------------------------------------------------------------------------

# 23. Model Names Shown in the Provided Notes/Screenshot

The screenshot includes a comparison similar to:

  Model shown    Description in the provided material
  -------------- -------------------------------------------
  GPT-5.6 Luna   Advanced reasoning and complex tasks
  GPT-5          General-purpose AI, coding, reasoning
  GPT-5 mini     Faster and more cost-efficient tasks
  GPT-4.1        General-purpose and coding workloads
  GPT-4.1 mini   Lower-cost, faster applications
  GPT-4o         Text, vision, and multimodal applications
  GPT-4o mini    Lightweight and economical applications

Model catalogs change over time, so model names and availability should
be checked against current OpenAI documentation before building a
production application.

------------------------------------------------------------------------

# 24. Important API-Key Security

The screenshot contained what appears to be an API key. It has
intentionally **not** been copied into these notes.

If that screenshot contained a real active key, revoke/rotate that key
in your OpenAI account and create a new one.

Never write:

``` python
api_key = "sk-actual-secret-key"
```

Prefer:

``` python
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

and keep the real secret only in `.env`.

------------------------------------------------------------------------

# 25. Quick Revision

**LLM**\
Large Language Model.

**Prompt**\
The input/instruction supplied to an LLM.

**Token**\
A unit of text processed by a model.

**Tokenization**\
Converting text into tokens.

**API**\
An interface that allows one software application to communicate with
another.

**API key**\
A secret credential used to authenticate API requests.

**OpenAI client**\
The Python object used to make OpenAI API requests.

**`.env`**\
A file commonly used during local development to hold environment
variables and secrets.

**`load_dotenv()`**\
Loads values from `.env` into the environment.

**`os.getenv()`**\
Retrieves an environment variable.

**`requirements.txt`**\
Lists Python dependencies for a project.

**Streamlit**\
A Python framework for quickly creating interactive web applications.

------------------------------------------------------------------------

## Final Project Flow

``` text
User
 ↓
Streamlit UI (app.py)
 ↓
ask_gpt() in main.py
 ↓
OpenAI Python SDK
 ↓
OpenAI API
 ↓
LLM
 ↓
Generated response
 ↓
Streamlit displays the answer
```
