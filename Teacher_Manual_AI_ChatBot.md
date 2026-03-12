# Teacher Manual — AI ChatBot Thesis Project
## Retrieval-Augmented Generation (RAG) System for PDF Document Querying

---

**Student:** [Ergi Toshkezi]  
**Thesis Title:** AI-Powered Document Querying System Using Retrieval-Augmented Generation (RAG)  
**Academic Year:** 2025/2026  
**Date:** March 2026  
**Technology Stack:** Python · Streamlit · FAISS · LLM API · SQLite · RSA Encryption

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview & Architecture](#2-system-overview--architecture)
3. [Project File Structure](#3-project-file-structure)
4. [Component Deep-Dive](#4-component-deep-dive)
   - 4.1 [ChatBox_complete.py — The Main Application](#41-chatbox_completepy--the-main-application)
   - 4.2 [Machine_A.py — Security & Key Management](#42-machine_apy--security--key-management)
   - 4.3 [htmlTemplates.py — UI Chat Templates](#43-htmltemplatespy--ui-chat-templates)
5. [Data & Process Flow — Step by Step](#5-data--process-flow--step-by-step)
6. [Key Technologies Explained](#6-key-technologies-explained)
7. [Database Design](#7-database-design)
8. [Security Architecture](#8-security-architecture)
9. [API Integration](#9-api-integration)
10. [User Interface Walkthrough](#10-user-interface-walkthrough)
11. [Important Design Choices & Trade-offs](#11-important-design-choices--trade-offs)
12. [Potential Extensions & Improvements](#12-potential-extensions--improvements)
13. [Glossary of Technical Terms](#13-glossary-of-technical-terms)

---

## 1. Executive Summary

This thesis project implements a **Retrieval-Augmented Generation (RAG)** chatbot that allows users to upload PDF documents and ask natural-language questions about them. The system retrieves the most semantically relevant sections of the documents and uses a **Large Language Model (LLM)** to generate a coherent, context-aware answer.

The system combines several advanced concepts:

| Concept | Implementation |
|---|---|
| Natural Language Processing | Sentence-level semantic embeddings via BGE-M3 model |
| Vector Search | Facebook AI Similarity Search (FAISS) — indexed in-memory and persisted in SQLite |
| Generative AI | Mistral-7B-Instruct LLM via REST API |
| Data Persistence | SQLite database with compressed and binary-serialized storage |
| Security | RSA-2048 asymmetric encryption for API key protection |
| Web UI | Streamlit — interactive Python-native web application |

The core innovation is that **the LLM never reads the full PDF**. Instead, only the top-k most relevant chunks are retrieved via FAISS and injected as context into the LLM prompt — a critical RAG design pattern that dramatically reduces token cost and latency while maintaining accuracy.

---

## 2. System Overview & Architecture

The system follows a **classic RAG pipeline** with persistent storage:

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Streamlit)                   │
│   [Upload PDF] → [Process] ──────────────────────────────────────►  │
│   [Select Manual] ─────────────────────────────────────────────────► │
│   [Ask Question] ──────────────────────────────────────────────────► │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │    PDF INGESTION PIPELINE   │
          │  1. partition_pdf()         │
          │     (unstructured lib)      │
          │  2. chunk_by_title()        │
          │  3. get_vectorstore()       │
          │     → EmbeddingApiRunnable  │
          │     → FAISS IndexFlatL2     │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │    PERSISTENCE (SQLite)     │
          │  save_analysis_to_db()      │
          │  - Compressed text (gzip)   │
          │  - Serialized FAISS index   │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │       QUERY PIPELINE        │
          │  handle_userinput()         │
          │  1. Token count check       │
          │  2. Embedd_user_question()  │
          │  3. FAISS.search() → top-k  │
          │  4. get_conversation_chain  │
          │     → LLMApiRunnable        │
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼──────────────┐
          │      RESPONSE DISPLAY       │
          │  display_chat_history()     │
          │  htmlTemplates.py (CSS/HTML)│
          └─────────────────────────────┘
```

---

## 3. Project File Structure

```
AI_Chatbot/
│
├── ChatBox_complete.py          ← MAIN APPLICATION (906 lines)
│                                   All logic: ingestion, embedding,
│                                   vector search, LLM API, Streamlit UI
│
├── Machine_A.py                 ← SECURITY MODULE (73 lines)
│                                   RSA-2048 key generation & decryption
│
├── htmlTemplates.py             ← UI TEMPLATES (45 lines)
│                                   CSS styling + HTML for chat bubbles
│
├── .env                         ← ENVIRONMENT VARIABLES (not committed)
│                                   API keys (encrypted), API URLs
│
├── key/
│   ├── private_key.pem          ← RSA private key (machine-local, secret)
│   └── public_key.pem           ← RSA public key (shareable)
│
├── Analysed_PDFs/               ← Temporary PDF upload directory
│
├── *.db                         ← SQLite databases (one per project)
│                                   e.g., TxIA.db
│
└── poppler-25.11.0/             ← Poppler binaries for PDF rendering
    └── Library/bin/
```

---

## 4. Component Deep-Dive

### 4.1 `ChatBox_complete.py` — The Main Application

This is the central file of the project. It is structured into:

---

#### 4.1.1 Imports & Initialization (Lines 1–20)

```python
import streamlit as st
from unstructured.chunking.title import chunk_by_title
from htmlTemplates import css, bot_template, user_template
import faiss
import sqlite3
import tiktoken
import Machine_A
```

Key imports and their roles:

| Library | Role |
|---|---|
| `streamlit` | Web application framework — displays the UI |
| `unstructured` | Parses PDF files into structured elements (text, tables, titles) |
| `faiss` | Facebook's vector similarity search engine |
| `sqlite3` | Python's built-in SQL database used for persistence |
| `tiktoken` | OpenAI's tokenizer — used to count token budget |
| `Machine_A` | Custom security module for RSA decryption |
| `gzip` / `json` | Compression and serialisation of text chunks |
| `numpy` | Numerical array operations needed by FAISS |

The line:
```python
tokenizer = tiktoken.get_encoding("cl100k_base")
```
Initialises the `cl100k_base` tokenizer (the same one used by GPT-4 and text-embedding-ada-002) to count tokens accurately.

---

#### 4.1.2 Poppler Path Configuration (Lines 22–24)

```python
poppler_bin_path = r"C:\...\poppler-25.11.0\Library\bin"
os.environ["PATH"] += os.pathsep + poppler_bin_path
```

**Poppler** is a C++ PDF rendering library required by the `unstructured` library to process PDFs at high resolution. Its binaries must be on the system PATH before any PDF is processed.

---

#### 4.1.3 Database Functions (Lines 43–248)

There are five database-related functions:

| Function | Purpose |
|---|---|
| `get_available_dbs()` | Scans directory for `*.db` files and returns names without extension |
| `does_DB_exists(DB)` | Uses glob pattern matching to check if a named DB file exists |
| `init_db(DB)` | Creates the SQLite database and the `pdf_analysis` table if not yet present |
| `save_analysis_to_db(...)` | Serialises and saves FAISS index + compressed text into the DB |
| `load_analysis_from_db(...)` | Retrieves and deserialises FAISS index for one specific file |
| `Load_selected_analysis_from_db(sel, DB)` | Retrieves FAISS indexes and text chunks for **one or more** files using LIKE queries |

**How `save_analysis_to_db` works in detail:**

```
Input: filename, analysis text, chunked texts (list), FAISS index object, DB name
  │
  ├── Step 1: faiss.serialize_index(faiss_index) → bytes (numpy uint8 array)
  │
  ├── Step 2: json.dumps(text) → JSON string
  │           gzip.compress(...) → compressed bytes
  │
  └── Step 3: INSERT OR REPLACE into SQLite table
              - filename (TEXT, PRIMARY KEY)
              - analysis (TEXT, placeholder description)
              - chunked_text (BLOB, gzip-compressed JSON)
              - vectorstore (BLOB, serialized FAISS binary)
```

**Why serialize and compress?**

- FAISS indexes are in-memory binary structures — they must be serialised (converted to a byte stream) to be stored in a database.
- Text chunks can be large; gzip compression reduces storage by ~60–80%.
- `sqlite3.Binary()` wraps raw bytes as a proper BLOB type for the SQLite driver.

---

#### 4.1.4 PDF Text Extraction (Lines 256–328)

**Two extraction strategies exist:**

```python
def get_pdf_text0(filepath):   # Categorize-based approach (research version)
    elements = partition_pdf(filepath, strategy="hi_res", infer_table_structure=True)
    container = [e.to_dict() for e in elements]
    return categorize(container)

def get_pdf_text(filepath):    # Active production version
    elements = partition_pdf(filepath, strategy="hi_res", infer_table_structure=True)
    return elements
```

The argument `strategy="hi_res"` instructs `unstructured` to use a high-resolution OCR approach — suitable for PDFs with complex layouts, tables, or scanned pages. `infer_table_structure=True` tells the parser to detect and reconstruct table structures.

**The `categorize()` function (lines 291–320):**

This is an **original custom algorithm** developed as part of the thesis. It iterates through parsed elements and:

1. Detects `Table` type elements and passes them through `convert_table_to_text()` which formats tab-separated columns using `|` delimiters for readability.
2. Groups text content together until a new **Title** element is detected (title = new section boundary).
3. Marks end-of-section with the sentinel string `"ERGI"` and saves the accumulated chunk.
4. Writes all resulting chunks to `Output_Chunk.txt` for debugging and inspection.

This manual chunking strategy ensures that each chunk is **semantically coherent** — it stays within one section/topic rather than cutting arbitrarily by character count.

**The `get_text_chunks()` function (lines 280–285):**

```python
def get_text_chunks(elements):
    chunks = chunk_by_title(
        elements,
        max_characters=3000,
        new_after_n_chars=2000,
        multipage_sections=False
    )
    return chunks
```

Used in the production pipeline — `chunk_by_title` from the `unstructured` library splits the document at title elements, respecting:
- `max_characters=3000`: hard maximum per chunk
- `new_after_n_chars=2000`: preferred soft maximum
- `multipage_sections=False`: a section does not span multiple pages

---

#### 4.1.5 `EmbeddingApiRunnable` Class (Lines 337–389)

This is a **custom wrapper class** that communicates with an external embedding API:

```python
class EmbeddingApiRunnable:
    def __init__(self, api_url, api_key):
        ...

    def invoke_e(self, texts):
        # Posts list of texts to the API, returns list of embedding vectors
        payload = {"model": "bge-m3", "input": texts}
        response = requests.post(self.api_url, headers=headers, json=payload)
        embeddings = [item['embedding'] for item in response.json()['data']]
        return embeddings
```

**BGE-M3** (BAAI General Embedding — Multilingual, Multi-functionality, Multi-granularity) is chosen for its high-quality multilingual sentence embeddings. Each text chunk is converted to a dense floating-point vector (high-dimensional representation capturing semantic meaning).

The class implements multiple interfaces:
- `invoke_e(texts)` — Primary method
- `invoke(texts)` — Alias for compatibility
- `embed_documents(texts)` — Batch interface convention
- `__call__(texts)` — Makes the object callable (syntactic sugar)

---

#### 4.1.6 `get_vectorstore()` — Building the FAISS Index (Lines 397–441)

This function orchestrates the **indexing** step of the RAG pipeline:

```
Inputs: text_chunks (list of unstructured Element objects)
        │
        ├── Step 1: Decrypt API key using Machine_A.decrypt_message()
        │
        ├── Step 2: Extract raw text from each chunk
        │           texts = [chunk.to_dict()['text'] for chunk in text_chunks]
        │
        ├── Step 3: Call EmbeddingApiRunnable → returns list of vectors
        │
        ├── Step 4: Convert to numpy array
        │           embeddings = np.array(embeddings)
        │
        ├── Step 5: Determine embedding dimension d = embeddings.shape[1]
        │
        ├── Step 6: Create FAISS IndexFlatL2(d)
        │           Flat L2 = exact nearest-neighbour search (no approximation)
        │
        └── Step 7: Add all embeddings to the index
                    index.add(embeddings)

Output: (index, texts) → stored in session state + persisted to SQLite
```

**Why FAISS IndexFlatL2?**

`IndexFlatL2` performs **exact nearest-neighbour search using L2 (Euclidean) distance**. The squared L2 distance between two vectors `a` and `b` is:

```
d(a, b) = Σ (aᵢ - bᵢ)²
```

Lower distance = more semantically similar. This exact index was chosen for correctness — the document collections are not large enough to require approximate search (e.g., `IndexIVFFlat`).

---

#### 4.1.7 Token Management (Lines 452–467 and 527–529)

**Two token counting functions:**

```python
def count_tokens(text):            # Simple word-split approximation (early dev)
    return len(text.split())

def count_tokens(text):            # Production version (overrides above)
    return len(tokenizer.encode(text))   # Uses cl100k_base tokenizer
```

The `truncate_chat_history_()` function (lines 461–467):

```python
def truncate_chat_history_(history):
    while sum(count_tokens(msg['content']) for msg in history) > 512:
        if len(history) > 0:
            history.pop(0)   # Drop OLDEST message
    return history
```

This implements a **sliding window** memory management strategy. When the cumulative token count of conversation history exceeds 512 tokens, the oldest messages are removed from the left (FIFO — First In, First Out). This prevents the LLM context window from overflowing while keeping the most recent conversational context intact.

---

#### 4.1.8 `LLMApiRunnable` Class (Lines 477–521)

This class calls the **Large Language Model (LLM)** API:

```python
class LLMApiRunnable:
    def invoke(self, messages, temperature=0.1, max_tokens=1024):
        payload = {
            "model": "mistral-7b-instruct",
            "temperature": 0.1,   # Near-deterministic responses
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": messages}]
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        content = response.json()['choices'][0]['message']['content']
        return content
```

**Mistral-7B-Instruct** is a 7-billion-parameter open-weight instruction-following language model. Key parameters:

| Parameter | Value | Effect |
|---|---|---|
| `temperature` | 0.1 | Very low randomness → focused, factual answers |
| `max_tokens` | 1024 | Maximum number of output tokens per response |
| `model` | mistral-7b-instruct | Instruction-fine-tuned variant for Q&A tasks |

---

#### 4.1.9 `get_conversation_chain_faiss()` — RAG Orchestration (Lines 536–568)

This function is the **heart of the RAG system**. It takes the user question and the top-k FAISS results and constructs an LLM prompt:

```python
results_text = "\n".join(
    [f"Result {i+1}: {result['text']} (distance: {result['distance']:.4f})"
     for i, result in enumerate(faiss_results)]
)

prompt = (
    f"User question: {query}\n\n"
    f"Here are some related results:\n{results_text}\n\n"
    "Please summarize or reorder the results based on their relevance to the question."
)

response = llm(prompt)
```

**Why this prompt structure?**

The prompt injects:
1. The original user question for grounding
2. The top-k retrieved text chunks with their similarity distances
3. An instruction to summarise/reorder by relevance

This is the **RAG paradigm** — the LLM acts as a reasoning layer *on top of* retrieved factual content, rather than relying solely on parametric (baked-in) knowledge. This dramatically reduces hallucination and makes answers traceable to source documents.

---

#### 4.1.10 `Embedd_user_question()` (Lines 575–603)

At query time, the user's question must be embedded into the **same vector space** as the document chunks:

```
User question (string)
        │
        ▼
EmbeddingApiRunnable.invoke([user_question])
        │
        ▼
numpy array of shape (1, embedding_dim)
        │
        ▼
Used as query vector in FAISS.search()
```

The critical principle: **both documents and queries must use the same embedding model** (BGE-M3) so that semantic similarity comparisons are meaningful.

---

#### 4.1.11 `handle_userinput()` — End-to-End Query Handler (Lines 613–736)

This is the orchestrating function called when the user submits a question. Its full flow:

```
User submits question
        │
        ├─ Guard: Is conversation loaded? → Error if not
        │
        ├─ Truncate question to 70 words (safety limit)
        │
        ├─ Append user message to chat_history
        │
        ├─ Count total tokens (question + history)
        │
        ├─ IF tokens < 512 (normal path):
        │       Embedd_user_question() → query_embedding (numpy array)
        │       Set index.nprobe = 8 (FAISS search parameter)
        │       Loop over all loaded FAISS indexes:
        │           index.search(query_embedding, k=5)
        │           Collect (text, distance) pairs
        │       Sort all results by distance (ascending)
        │       Take top 5 results
        │       get_conversation_chain_faiss() → LLM response
        │
        ├─ ELSE (token budget exceeded):
        │       truncate_chat_history_() → remove old messages
        │       Repeat same embedding + FAISS + LLM steps
        │
        └─ display_chat_history() → render chat bubbles
```

**The `nprobe = 8` setting:**

For approximate FAISS indexes (like `IndexIVFFlat`), `nprobe` controls how many inverted-list clusters to search. For the exact `IndexFlatL2` used here, this parameter has no effect but is set defensively for future compatibility.

---

#### 4.1.12 `main()` — Streamlit Application Entry Point (Lines 782–906)

The `main()` function builds the Streamlit user interface:

**Page Header:**
```python
st.set_page_config(page_title="AI ChatBot", page_icon="🤖")
st.write(css, unsafe_allow_html=True)   # Inject CSS from htmlTemplates.py
st.header("AI ChatBot 🤖")
```

**Sidebar — Database Selection:**
```python
available_dbs = get_available_dbs()
sel = st.selectbox("Select the Database you want to query:", available_dbs)
if st.button("Choose"):
    init_db(sel)   # Initialise DB (creates table if needed)
```

**Sidebar — PDF Upload & Processing:**
```python
pdf_docs = st.file_uploader("Upload your PDFs...", accept_multiple_files=True)
if st.button("Process"):
    for pdf in pdf_docs:
        save_uploaded_file(pdf, file_path)
        if check_if_present(DB_name, pdf.name):
            st.error("Already in DB")
            continue
        pdf_text = get_pdf_text(file_path)
        text_chunks = get_text_chunks(pdf_text)
        index, text = get_vectorstore(text_chunks)
        save_analysis_to_db(pdf.name, analysis, text, index, DB_name)
```

**Sidebar — Select Existing Manuals:**
```python
sel = st.text_input("Select the documents you want to query:")
if st.button("Select"):
    analysis_i, analysis_t = Load_selected_analysis_from_db(vectorize(sel), DB_name)
    st.session_state.conversation = list(analysis_i)
    st.session_state.text = list(analysis_t)
```

**Main Area — Chat Input:**
```python
with st.form(key='my_form'):
    user_question = st.text_input("Ask a question about your documents:")
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    handle_userinput(user_question)
```

---

### 4.2 `Machine_A.py` — Security & Key Management

This module implements **RSA-2048 asymmetric encryption** to protect API keys. The design follows a **public-key cryptography** pattern:

```
Machine B (key generation environment)
  │
  ├── generate_keys() → RSA-2048 keypair
  │       private_key.pem → kept secret on Machine A
  │       public_key.pem  → distributed to whoever needs to encrypt
  │
  └── API keys are encrypted with the public key
      (encrypted ciphertext stored in .env file)

Machine A (runtime environment — ChatBox_complete.py)
  │
  ├── load_private_key() → reads private_key.pem from ./key/
  │
  └── decrypt_message(ciphertext, private_key)
          Base64-decode ciphertext
          RSA-OAEP decrypt with SHA-256
          Return plaintext API key string
```

**Why RSA-OAEP?**

OAEP (Optimal Asymmetric Encryption Padding) is the modern, secure padding scheme for RSA encryption. It prevents chosen-ciphertext attacks and adds randomness (salt) so the same plaintext encrypts to different ciphertexts each time. SHA-256 is used as the hash function within the padding scheme.

**Rich progress bar:**

The decryption function uses the `rich` library to display a spinner/progress bar during decryption — a user experience enhancement to show that decryption is happening.

---

### 4.3 `htmlTemplates.py` — UI Chat Templates

This small but important file defines the visual appearance of the chat interface using **HTML and CSS embedded as Python strings**:

#### CSS (lines 1–26)

```css
.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
}
.chat-message.user  { background-color: #2b313e }   /* Dark navy */
.chat-message.bot   { background-color: #475063 }   /* Slightly lighter */
.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;    /* Circular avatar */
    object-fit: cover;
}
.chat-message .message {
    width: 80%;
    color: #fff;           /* White text */
}
```

The layout uses **CSS Flexbox** (`display: flex`) to position the avatar and message side by side.

#### User Template (lines 28–35)

Renders a user message bubble with an icon fetched from icons8.com. The placeholder `{{MSG}}` is replaced at runtime:

```python
st.write(user_template.replace("{{MSG}}", user_message), unsafe_allow_html=True)
```

#### Bot Template (lines 37–44)

Renders the AI response with a **Siemens logo** as the bot avatar — indicating the institutional context of the project. The Siemens branding aligns with the deployment environment for which the RAG system was intended.

---

## 5. Data & Process Flow — Step by Step

### 5.1 First-Time PDF Processing (Ingestion Pipeline)

```
Step 1: User selects a database from the sidebar dropdown
        → get_available_dbs() scans for *.db files
        → init_db(name) creates the database if needed

Step 2: User uploads one or more PDF files
        → save_uploaded_file() writes the file to ./Analysed_PDFs/

Step 3: Duplicate check
        → check_if_present(DB_name, pdf.name)
        → SQL query: SELECT filename WHERE filename = ?
        → If exists → skip with error message

Step 4: PDF partitioning
        → get_pdf_text(file_path)
        → partition_pdf() with hi_res strategy
        → Returns list of Element objects (NarrativeText, Title, Table, etc.)

Step 5: Chunking
        → get_text_chunks(elements)
        → chunk_by_title() groups by document section
        → max 3000 characters per chunk, soft limit 2000

Step 6: Embedding
        → get_vectorstore(text_chunks)
        → For each chunk: extract .to_dict()['text']
        → POST to embedding API with model bge-m3
        → Returns list of float vectors (one per chunk)
        → All vectors → numpy array

Step 7: FAISS index creation
        → IndexFlatL2(d) where d = embedding dimension
        → index.add(embeddings)
        → index.is_trained check (always True for Flat index)

Step 8: Persistence
        → save_analysis_to_db()
        → Serialize FAISS: faiss.serialize_index() → bytes
        → Compress text: gzip.compress(json.dumps(texts))
        → INSERT OR REPLACE into SQLite table
```

### 5.2 Loading Existing Documents (Retrieval from DB)

```
Step 1: User types document name(s) in "Select Manuals" text field
        Example: "Manual_A, Manual_B" (comma-separated)

Step 2: vectorize(sel) splits string by comma
        → ['Manual_A', ' Manual_B']

Step 3: Load_selected_analysis_from_db() queries SQLite:
        SELECT filename, chunked_text, vectorstore
        FROM pdf_analysis
        WHERE filename LIKE '%Manual_A%' OR filename LIKE '%Manual_B%'

Step 4: For each result row:
        → Deserialize FAISS: np.frombuffer(bytes, dtype=uint8) → faiss.deserialize_index()
        → Decompress text: gzip.decompress() → json.loads() → list of strings

Step 5: Store in session state:
        → st.session_state.conversation = [faiss_index1, faiss_index2, ...]
        → st.session_state.text = [text_chunk1, text_chunk2, ...]
```

### 5.3 Answering a User Question (Query Pipeline)

```
Step 1: User types question in the text box and presses Submit
        → handle_userinput(user_question)

Step 2: Question truncation
        → Maximum 70 words enforced

Step 3: Token budget check
        → count_tokens(question) + sum(count_tokens(msg) for msg in history)
        → If total > 512 → truncate_chat_history_() removes oldest messages

Step 4: Question embedding
        → Embedd_user_question(user_question)
        → Same BGE-M3 API → returns vector of shape (1, d)
        → Must match same space as document embeddings

Step 5: FAISS search across all loaded indexes
        → For each index in st.session_state.conversation:
            distances, idx_array = index.search(query_embedding, k=5)
        → Collect all (text, distance) pairs from all indexes

Step 6: Rank and select
        → sorted(all_responses, key=lambda x: x['distance'])
        → Top 5 results = most semantically similar chunks

Step 7: LLM call
        → get_conversation_chain_faiss(user_question, top_k_responses)
        → Constructs prompt with question + ranked chunks
        → POST to Mistral-7B-Instruct API
        → Returns generated text response

Step 8: Display
        → st.session_state.chat_history updated
        → display_chat_history() renders all messages via htmlTemplates.py
```

---

## 6. Key Technologies Explained

### 6.1 FAISS (Facebook AI Similarity Search)

FAISS is an open-source library developed by Meta AI Research for efficient **nearest-neighbour search** in high-dimensional vector spaces. In this project:

- **Index type:** `IndexFlatL2` — brute-force exact search using L2 distance
- **Dimensionality:** Determined by the BGE-M3 embedding model output
- **Operations used:** `index.add(vectors)`, `index.search(query, k)`
- **Storage:** Serialised to binary bytes via `faiss.serialize_index()` / `faiss.deserialize_index()`

FAISS is critical because traditional SQL databases cannot efficiently search across hundreds of hundreds-dimensional float vectors — they have no concept of semantic similarity.

### 6.2 Retrieval-Augmented Generation (RAG)

RAG is an AI architecture that combines:

1. **Retrieval:** Find relevant documents/chunks using vector search
2. **Augmentation:** Inject retrieved content into the LLM prompt as context
3. **Generation:** LLM generates a response grounded in the retrieved content

**Advantages over pure LLM:**
- Reduces hallucination by grounding answers in real documents
- No need to fine-tune the LLM on proprietary documents
- Traceable and updateable — add new documents without retraining
- Cost-efficient — only relevant chunks (not full documents) are processed by the LLM

### 6.3 Sentence Embeddings (BGE-M3)

An embedding model converts text into a vector (list of floating-point numbers) that captures the **semantic meaning** of the text. Similar sentences produce vectors that are close together in the high-dimensional space.

Example:
- "What is the maximum operating temperature?" → vector [0.12, -0.34, 0.89, ...]
- "Max temp threshold for operation" → vector [0.11, -0.33, 0.91, ...] (very close!)
- "The weather today is sunny" → vector [-0.72, 0.54, -0.12, ...] (far away)

### 6.4 Streamlit

Streamlit is a Python framework for building interactive web applications without HTML/JavaScript. Key concepts:

- `st.session_state` — Persists data across user interactions (like a server-side session)
- `st.sidebar` — Creates a sidebar panel
- `st.form` — Groups inputs with a single submit action
- `st.write(..., unsafe_allow_html=True)` — Renders raw HTML (used for chat templates)

### 6.5 SQLite + Binary Storage

SQLite is used as a **local, file-based relational database**. The project stores:

- **TEXT** fields for filenames and analysis descriptions
- **BLOB** fields for binary data (compressed text, serialised FAISS indexes)

The `INSERT OR REPLACE` SQL command (also called UPSERT) ensures that re-processing the same PDF updates the stored analysis rather than creating duplicates.

---

## 7. Database Design

### Table: `pdf_analysis`

```sql
CREATE TABLE IF NOT EXISTS pdf_analysis (
    filename    TEXT PRIMARY KEY,    -- PDF filename, enforces uniqueness
    analysis    TEXT,                -- Placeholder description text
    chunked_text BLOB,               -- gzip-compressed JSON list of text strings
    vectorstore  BLOB                -- Serialised FAISS binary index
);
```

### Entity Relationship

```
[pdf_analysis]
  filename (PK)   → one unique record per PDF
  analysis        → human-readable identifier (currently stub)
  chunked_text    → compressed text for retrieval & display
  vectorstore     → FAISS index for semantic search
```

### Storage Efficiency

| Data | Raw Size (example) | Stored Size |
|---|---|---|
| 10-page PDF text chunks | ~50 KB JSON | ~12 KB (gzip) |
| FAISS index for 50 chunks | ~200 KB | ~200 KB (binary, no compression) |
| Total per document | ~250 KB | ~212 KB |

---

## 8. Security Architecture

The project implements a **split-key security model** to protect external API credentials:

```
                 ┌──────────────────────┐
                 │   Key Generation     │
                 │   (one time only)    │
                 │                      │
                 │  Machine_A.generate_ │
                 │  keys()              │
                 │                      │
                 │  RSA-2048 keypair    │
                 │  ├─ private_key.pem  │
                 │  └─ public_key.pem   │
                 └──────────────────────┘
                          │
          ┌───────────────┴──────────────────┐
          ▼                                   ▼
  private_key.pem                    public_key.pem
  (stays on machine)         (shared with administrator)
          │                                   │
          │                         Administrator encrypts
          │                         API key with public key
          │                                   │
          │                         ciphertext stored in .env:
          │                         API_KEY=<base64_encrypted_bytes>
          │
          └─── At runtime: Machine_A.decrypt_message(ciphertext, private_key)
                           → plaintext API key used in API calls
```

**Security properties:**
- The plaintext API key never exists in a configuration file
- Even if `.env` is leaked, the ciphertext is useless without `private_key.pem`
- RSA-OAEP-SHA256 provides IND-CCA2 security (industry standard)

---

## 9. API Integration

The system uses **two separate external APIs**:

### 9.1 Embedding API

| Property | Value |
|---|---|
| Environment variable | `API_EMBEDDING` |
| Auth variable | `API_KEY_Embedding` |
| Model | `bge-m3` |
| Input | List of text strings |
| Output | List of float vectors (one per input) |
| Used by | `EmbeddingApiRunnable.invoke_e()` |
| Called during | Document ingestion + user question processing |

### 9.2 LLM API

| Property | Value |
|---|---|
| Environment variable | `API_URL` |
| Auth variable | `API_KEY` |
| Model | `mistral-7b-instruct` |
| Input | Structured prompt string |
| Output | Generated text string |
| Used by | `LLMApiRunnable.invoke()` |
| Called during | Every user question |

Both APIs follow the **OpenAI-compatible REST API convention** (`/v1/chat/completions`, `choices[0].message.content`), allowing easy model substitution in the future.

---

## 10. User Interface Walkthrough

When the user opens the application in their browser (e.g., `http://localhost:8501`), they see:

### Main Area
- **Header:** "AI ChatBot 🤖"
- **Question input form:** Text box labelled "Ask a question about your documents:" with a Submit button
- **Chat history display:** Scrollable conversation with colour-coded bubbles:
  - Dark navy (#2b313e) = user messages, person icon
  - Steel blue (#475063) = bot messages, Siemens logo icon

### Left Sidebar

**Section 1 — Select Database**
- Dropdown listing all `.db` files found in the working directory
- "Choose" button to activate the selected database

**Section 2 — Your Documents**
- Multi-file PDF uploader
- "Process" button: runs the full ingestion pipeline for each uploaded PDF
  - Checks for duplicates
  - Partitions, chunks, embeds, indexes, saves to DB

**Section 3 — Select Manuals**
- Text input for comma-separated document names to load from DB
- "Select" button: retrieves FAISS indexes and text from DB and loads into session state

---

## 11. Important Design Choices & Trade-offs

| Decision | Choice Made | Alternative | Rationale |
|---|---|---|---|
| Vector Index Type | `IndexFlatL2` (exact) | `IndexIVFFlat` (approximate) | Exact search ensures highest recall; doc sets are small enough |
| Embedding Model | BGE-M3 | OpenAI ada-002, sentence-transformers | Multilingual support; no vendor lock-in; high benchmark scores |
| LLM | Mistral-7B-Instruct | GPT-4, Llama3 | Open-weight; cost-efficient; good instruction following |
| Chunking Strategy | `chunk_by_title` + custom `categorize()` | Fixed-length character splitting | Semantic coherence; sections are preserved as units |
| Storage | SQLite + BLOB | File system / PostgreSQL | Simple; no server required; portable; self-contained |
| UI Framework | Streamlit | Flask+React, Gradio | Rapid prototyping; Python-native; minimal boilerplate |
| API Key Security | RSA-2048 asymmetric encryption | Plain `.env` (no encryption) | Prevents credential exposure if `.env` is accidentally committed |
| Temperature | 0.1 | 0.7–1.0 | Factual, consistent answers preferred over creative variation |
| Token Budget | 512 tokens | Higher window | Controls API cost; prevents context overflow in older models |

---

## 12. Potential Extensions & Improvements

1. **Multi-modal support:** Extend `get_pdf_text()` to extract images from PDFs and use a vision-enabled LLM (like GPT-4V) to answer questions about charts and diagrams.

2. **Approximate nearest-neighbour search:** For very large document collections (thousands of PDFs), replace `IndexFlatL2` with `IndexIVFFlat` or `IndexHNSWFlat` for sub-linear search complexity.

3. **Re-ranking:** After FAISS retrieval, apply a cross-encoder re-ranker to more precisely score the relevance of each chunk before passing to the LLM.

4. **Streaming responses:** Use Server-Sent Events (SSE) to stream the LLM response token-by-token in real time, improving perceived responsiveness.

5. **Source citation:** Display which document and chunk each piece of information came from, giving the user full traceability.

6. **User authentication:** Add login/session management so different users maintain separate chat histories and document sets.

7. **Multi-language support:** BGE-M3 already supports multilingual embeddings — extend the prompt engineering to handle responses in the user's language.

8. **Evaluation framework:** Implement RAGAS (RAG Assessment) metrics — faithfulness, answer relevance, context precision, context recall — to objectively measure system quality.

---

## 13. Glossary of Technical Terms

| Term | Definition |
|---|---|
| **API** | Application Programming Interface — a defined way for software systems to communicate |
| **BLOB** | Binary Large Object — raw binary data stored in a database field |
| **BGE-M3** | BAAI General Embedding — a multilingual, high-quality text embedding model |
| **Chunk** | A segment of a document, sized to fit within an LLM's context window |
| **Embedding** | A dense numerical vector representing the semantic meaning of a text |
| **FAISS** | Facebook AI Similarity Search — library for efficient vector nearest-neighbour search |
| **Flat Index** | A FAISS index that performs exact brute-force search over all stored vectors |
| **gzip** | A compression algorithm — reduces data size by eliminating redundancy |
| **IndexFlatL2** | A FAISS index that computes exact L2 (Euclidean) distances to all vectors |
| **L2 Distance** | Euclidean distance — the straight-line distance between two points in n-dimensional space |
| **LLM** | Large Language Model — a neural network trained on large text datasets (e.g., Mistral, GPT) |
| **Mistral-7B** | A 7-billion-parameter open-weight language model with strong instruction-following capabilities |
| **OAEP** | Optimal Asymmetric Encryption Padding — a secure RSA padding scheme |
| **Poppler** | A C++ PDF rendering library needed for high-resolution PDF parsing |
| **RAG** | Retrieval-Augmented Generation — combining vector retrieval with LLM generation |
| **RSA** | Rivest–Shamir–Adleman — an asymmetric encryption algorithm using a public/private keypair |
| **Serialisation** | Converting an in-memory object (e.g., FAISS index) to a byte stream for storage |
| **Session State** | Streamlit's mechanism for persisting variables across user interactions |
| **Streamlit** | A Python library for building interactive web apps with minimal code |
| **Temperature** | An LLM parameter controlling randomness (0 = deterministic, 1 = very creative) |
| **Tiktoken** | OpenAI's tokenizer library for counting tokens in text |
| **Token** | The atomic unit processed by an LLM — roughly ¾ of a word on average |
| **Truncation** | Cutting text or history to stay within a token budget |
| **Unstructured** | A Python library that parses PDFs and other documents into structured element objects |
| **UPSERT** | A database operation that inserts a new row or updates it if it already exists |
| **Vector Store** | A data structure that stores and enables search over embedding vectors |

---

*This document was produced as part of the AI Chatbot Thesis Project. All code was written and designed by the student. The system demonstrates applied knowledge of NLP, information retrieval, database engineering, cryptography, and modern AI system architecture.*
