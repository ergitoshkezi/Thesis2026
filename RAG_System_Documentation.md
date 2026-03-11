# RAG-Based AI Chatbot — Thesis Technical Documentation

**Author:** [Your Name]  
**Project:** AI ChatBot — Retrieval-Augmented Generation (RAG) System  
**Stack:** Python · Streamlit · FAISS · BGE-M3 Embeddings · Mistral-7B LLM · SQLite · RSA Encryption  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [File-by-File Breakdown](#3-file-by-file-breakdown)
   - 3.1 [ChatBox_complete.py — Core RAG Engine](#31-chatbox_completepy--core-rag-engine)
   - 3.2 [Machine_A.py — Secure Key Management & Decryption](#32-machine_apy--secure-key-management--decryption)
   - 3.3 [htmlTemplates.py — Chat UI Templates](#33-htmltemplatespy--chat-ui-templates)
4. [End-to-End Data Flow](#4-end-to-end-data-flow)
5. [Component Deep-Dives](#5-component-deep-dives)
   - 5.1 [PDF Ingestion & Intelligent Chunking](#51-pdf-ingestion--intelligent-chunking)
   - 5.2 [Embedding Generation — EmbeddingApiRunnable](#52-embedding-generation--embeddingapirunnable)
   - 5.3 [FAISS Vector Store](#53-faiss-vector-store)
   - 5.4 [Persistent Storage — SQLite Database Layer](#54-persistent-storage--sqlite-database-layer)
   - 5.5 [Query Pipeline — Retrieval & Generation](#55-query-pipeline--retrieval--generation)
   - 5.6 [Token Budget Management](#56-token-budget-management)
   - 5.7 [RSA Encryption for API Key Security](#57-rsa-encryption-for-api-key-security)
   - 5.8 [UI Layer — Streamlit + Custom HTML/CSS](#58-ui-layer--streamlit--custom-htmlcss)
6. [Security Design](#6-security-design)
7. [Design Decisions & Trade-offs](#7-design-decisions--trade-offs)
8. [Limitations & Future Work](#8-limitations--future-work)
9. [Dependency Map](#9-dependency-map)

---

## 1. Project Overview

This project implements a **Retrieval-Augmented Generation (RAG)** chatbot designed to allow users to interactively ask questions about the content of their own PDF documents. Instead of relying purely on a language model's pre-trained knowledge, the system:

1. **Ingests** one or more PDFs and extracts their textual (and tabular) content using high-resolution layout analysis.
2. **Chunks** the text into semantically coherent segments, respecting document section boundaries.
3. **Embeds** each chunk using the `BGE-M3` multilingual embedding model, converting text into dense numerical vectors.
4. **Stores** these vectors in a FAISS (Facebook AI Similarity Search) index, persisted to a SQLite database for reuse across sessions.
5. **Retrieves** the most relevant chunks at query time by comparing the user's embedded question against stored vectors.
6. **Generates** a fluent, contextualised answer using the `Mistral-7B-Instruct` LLM, prompted with the retrieved chunks.

The entire system is served through a **Streamlit** web application, secured with **RSA asymmetric encryption** to protect sensitive API keys at rest.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Streamlit UI                                 │
│  ┌──────────────┐  ┌───────────────────┐  ┌────────────────────────┐   │
│  │  DB Selector │  │  PDF Uploader     │  │  Manual Selector       │   │
│  │  (Sidebar)   │  │  + Process button │  │  (query existing DB)   │   │
│  └──────────────┘  └───────────────────┘  └────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │           RAG Pipeline                   │
              │  ┌─────────────────────────────────────┐ │
              │  │  1. PDF Partition (hi-res + tables) │ │
              │  │     partition_pdf() → elements      │ │
              │  └──────────────────┬──────────────────┘ │
              │  ┌──────────────────▼──────────────────┐ │
              │  │  2. Chunking                        │ │
              │  │     chunk_by_title() → chunks       │ │
              │  └──────────────────┬──────────────────┘ │
              │  ┌──────────────────▼──────────────────┐ │
              │  │  3. Embedding (BGE-M3 via REST API) │ │
              │  │     EmbeddingApiRunnable.invoke_e() │ │
              │  └──────────────────┬──────────────────┘ │
              │  ┌──────────────────▼──────────────────┐ │
              │  │  4. FAISS IndexFlatL2               │ │
              │  │     Built from embedding matrix     │ │
              │  └──────────────────┬──────────────────┘ │
              │  ┌──────────────────▼──────────────────┐ │
              │  │  5. SQLite Persistence              │ │
              │  │     FAISS bytes + gzip text stored  │ │
              │  └─────────────────────────────────────┘ │
              └─────────────────────────────────────────-─┘

              ┌──────────────────────────────────────────┐
              │           Query Pipeline                  │
              │  User Question                           │
              │       │                                  │
              │       ▼                                  │
              │  Token budget check (tiktoken cl100k)    │
              │       │                                  │
              │       ▼                                  │
              │  Embed question (BGE-M3)                 │
              │       │                                  │
              │       ▼                                  │
              │  FAISS.search(k=5) across all indexes    │
              │       │                                  │
              │       ▼                                  │
              │  Sort by L2 distance, select top-5       │
              │       │                                  │
              │       ▼                                  │
              │  LLM prompt construction                 │
              │       │                                  │
              │       ▼                                  │
              │  Mistral-7B-Instruct (via REST API)      │
              │       │                                  │
              │       ▼                                  │
              │  Chat history append + UI render         │
              └──────────────────────────────────────────┘

              ┌──────────────────────────────────────────┐
              │         Security Layer (Machine_A)        │
              │  RSA-2048 private key (local)            │
              │  API keys encrypted with public key      │
              │  Decrypted at runtime for each call      │
              └──────────────────────────────────────────┘
```

---

## 3. File-by-File Breakdown

### 3.1 `ChatBox_complete.py` — Core RAG Engine

This is the main application file (~906 lines). It owns the complete RAG pipeline and the Streamlit UI. Below is a summary of every function and class defined within it.

---

#### Imports & Initial Setup (Lines 1–24)

```python
import streamlit as st
from unstructured.chunking.title import chunk_by_title
from htmlTemplates import css, bot_template, user_template
from flask import Flask
import os, sqlite3, requests, glob, json, gzip, numpy as np, faiss, tiktoken
import Machine_A
from dotenv import load_dotenv
```

- **`streamlit`** — Serves the entire web UI declaratively.
- **`unstructured`** — Library for intelligent document parsing; handles PDFs with mixed layouts (text, images, tables).
- **`faiss`** — Facebook's vector similarity search library; used in flat L2 mode for exact nearest-neighbour search.
- **`tiktoken`** — OpenAI's tokenizer; used here with the `cl100k_base` encoding (GPT-4 family tokenizer) to count tokens precisely and enforce budget limits.
- **`Machine_A`** — Custom RSA decryption module (see §3.2).
- **`dotenv`** — Loads sensitive environment variables from `.env` file.
- A **Poppler** binary path is injected into `PATH` so that `unstructured` can render PDF pages to images for its high-resolution parser.
- A **Flask app** object is instantiated (though not started as a separate server); the `UPLOAD_FOLDER` (`./Analysed_PDFs`) is created on disk if it doesn't exist.

---

#### `save_uploaded_file(uploaded_file, save_path)` — Lines 27–30

```python
def save_uploaded_file(uploaded_file, save_path):
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
```

**Purpose:** Writes a Streamlit `UploadedFile` object (which holds data in memory) to disk under `./Analysed_PDFs/`. This is necessary because `partition_pdf()` requires a real filesystem path, not an in-memory buffer.

**Design Note:** `uploaded_file.getbuffer()` returns the raw bytes of the uploaded file; writing them in binary mode ensures no corruption of the PDF binary format.

---

#### `get_available_dbs()` — Lines 43–46

```python
def get_available_dbs():
    db_files = glob.glob('*.db')
    return [os.path.splitext(db_file)[0] for db_file in db_files]
```

**Purpose:** Scans the current working directory for all SQLite `.db` files and returns their names (without extension). This feeds the sidebar dropdown that lets the user select which knowledge base to work with.

**Design Note:** The glob pattern `*.db` is intentionally simple — it means databases must live in the same directory as the script. This keeps the design stateless and portable within a single project folder.

---

#### `does_DB_exists(DB)` — Lines 50–61

**Purpose:** Checks whether a database matching a partial name exists in the current directory using `glob.glob(f'*{DB}*.db')`. Returns the first match or `None`. Used for user feedback; not called in the main processing flow.

---

#### `init_db(DB)` — Lines 65–84

```python
def init_db(DB):
    conn = sqlite3.connect(f'{DB}.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdf_analysis (
        id INTEGER PRIMARY KEY,
        filename TEXT UNIQUE,
        analysis TEXT,
        chunked_text BLOB,
        vectorstore BLOB
    )''')
    conn.commit()
    conn.close()
    return f'{DB}.db'
```

**Purpose:** Creates (or connects to) a SQLite database file named `{DB}.db` and ensures the `pdf_analysis` table exists. The schema stores:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-incremented row ID |
| `filename` | TEXT UNIQUE | Original PDF filename; prevents duplicate ingestion |
| `analysis` | TEXT | Placeholder analysis string (reserved for future use) |
| `chunked_text` | BLOB | gzip-compressed JSON array of the text chunks |
| `vectorstore` | BLOB | Raw serialised FAISS index bytes |

**Design Note:** SQLite is chosen for its zero-configuration character — no separate database server is needed, which makes the thesis prototype easy to run on any machine.

---

#### `analyze_pdf(file_path)` — Lines 89–91

A placeholder function that returns a simple string `"Analysis results for <path>"`. This field in the database is reserved for future expansion (e.g., a high-level summary generated by an LLM).

---

#### `save_analysis_to_db(filename, analysis, text, faiss_index, DB)` — Lines 97–132

This function serialises and persists all artefacts of processing a single PDF to SQLite:

**Step 1 — Serialise FAISS index:**
```python
faiss_index_bytes = faiss.serialize_index(faiss_index)
```
`faiss.serialize_index` converts the in-memory FAISS index (containing all embedding vectors) into a contiguous byte array (`numpy.ndarray` of `uint8`). This byte representation preserves the full index including its type metadata, making it fully reconstructible.

**Step 2 — Compress text chunks:**
```python
text_json = json.dumps(text)
compressed_text = gzip.compress(text_json.encode('utf-8'))
```
The list of text strings is first serialised to a JSON string (ensuring Python list → portable format), then compressed with gzip. This is important because for a 100-page document, the raw text chunks can easily be several hundred KB.

**Step 3 — Upsert to SQLite:**
```python
cursor.execute('''
    INSERT OR REPLACE INTO pdf_analysis (filename, analysis, chunked_text, vectorstore)
    VALUES (?, ?, ?, ?)
''', (filename, analysis, compressed_text, sqlite3.Binary(faiss_index_bytes)))
```
`INSERT OR REPLACE` means re-processing the same PDF will overwrite the previous data. `sqlite3.Binary()` wraps the FAISS bytes to signal to the SQLite driver that this is a binary blob rather than text.

---

#### `load_analysis_from_db(filename, DB)` — Lines 139–169

Retrieves and reconstructs the FAISS index for a single file by filename. Used internally; the more general multi-file loader (`Load_selected_analysis_from_db`) is used in the main pipeline.

**Deserialization:**
```python
faiss_index = faiss.deserialize_index(faiss_index_bytes)
```
Handles `memoryview` → `bytes` conversion (SQLite sometimes returns BLOBs as `memoryview` objects rather than raw `bytes`).

---

#### `Load_selected_analysis_from_db(sel, DB)` — Lines 174–248

The primary retrieval function. Accepts either a single string or a list of strings and builds a dynamic SQL query with `LIKE` matching:

```python
placeholders = ['filename LIKE ?' for _ in search_terms]
query_conditions = ' OR '.join(placeholders)
params = [f'%{term}%' for term in search_terms]
```

This allows partial-name matching — e.g., searching for `"manual"` will find any file whose name contains "manual". This is user-friendly since users don't need to remember exact filenames.

For each matched row:
1. **FAISS index** is reconstructed via `np.frombuffer` + `faiss.deserialize_index`.
2. **Text chunks** are decompressed via `gzip.decompress` + `json.loads`.

Returns a tuple `(faiss_indexes, retrieved_text_chunks)` — a list of FAISS index objects (one per matched PDF) and the aggregated text chunks. This multi-index design allows querying across several PDFs simultaneously.

---

#### `get_pdf_text(filepath)` — Lines 270–276

```python
def get_pdf_text(filepath):
    elements = partition_pdf(filepath,
                              strategy="hi_res",
                              infer_table_structure=True)
    return elements
```

Uses `unstructured`'s `partition_pdf` with two key settings:

- **`strategy="hi_res"`**: Renders each PDF page as an image (requires Poppler) and applies an OCR/layout analysis pipeline. This is computationally expensive but correctly handles multi-column layouts, scanned documents, and embedded images with text.
- **`infer_table_structure=True`**: Attempts to detect tabular regions and returns them as `Table` elements with structured cell content, rather than garbled flowing text.

Returns a list of `unstructured` `Element` objects, each carrying both text content and metadata (page number, coordinates, element type like `Title`, `NarrativeText`, `Table`, `ListItem`, etc.).

---

#### `get_text_chunks(elements)` — Lines 280–285

```python
def get_text_chunks(elements):
    chunks = chunk_by_title(
        elements, max_characters=3000,
        new_after_n_chars=2000,
        multipage_sections=False)
    return chunks
```

Applies `unstructured`'s title-aware chunking strategy:

- **`max_characters=3000`**: A single chunk will never exceed 3000 characters.
- **`new_after_n_chars=2000`**: A new chunk begins after 2000 characters even without a title boundary, preventing overly long sections.
- **`multipage_sections=False`**: Each chunk is constrained to a single page, preventing semantic crossings between PDF pages (important when page boundaries correspond to topic boundaries, e.g., in technical manuals).

**Why title-based chunking?** Section titles are semantic anchors. Grouping content under its title means each chunk contains topically coherent information, which directly improves retrieval quality since the chunk content aligns with what a user is likely to query.

---

#### `categorize(elements)` — Lines 291–320

An alternative, custom chunking function (used by the now-deprecated `get_pdf_text0`). It iterates element by element and:

- Identifies tables and formats them with `convert_table_to_text()` (tab → pipe formatting for readability).
- Groups elements into chunks, breaking at `Title` boundaries (when an element is followed by a `Title`).
- Inserts a sentinel string `"ERGI"` at each section break (a custom marker for debugging/inspection).
- Writes all chunks to `Output_Chunk.txt` for offline inspection.

This function demonstrates a manual implementation of what `chunk_by_title` does automatically, and shows the evolution of the chunking strategy during development.

---

#### `EmbeddingApiRunnable` Class — Lines 337–389

This class abstracts the REST API call to the BGE-M3 embedding service.

```python
class EmbeddingApiRunnable:
    def __init__(self, api_url, api_key): ...
    def invoke_e(self, texts): ...         # core method
    def invoke(self, texts): ...           # alias for invoke_e
    def embed_documents(self, texts): ... # LangChain-compatible interface
    def __call__(self, texts): ...        # makes instance callable directly
```

**`invoke_e(texts)`** constructs and sends a POST request:

```python
payload = {
    "model": "bge-m3",
    "input": texts  # list of strings
}
response = requests.post(self.api_url, headers=headers, json=payload)
embeddings = [item['embedding'] for item in response_json['data']]
```

**BGE-M3** is a state-of-the-art multilingual embedding model from BAAI (Beijing Academy of AI). It produces dense vectors of dimension 1024 and is designed for retrieval tasks, supporting 100+ languages. It is ideal for technical documentation which may mix languages or contain domain-specific terminology.

The response validation checks:
- HTTP 200 status.
- Presence of `'data'` key in JSON.
- Each embedding is a proper Python list (not a float or None).

The multiple interface methods (`invoke`, `embed_documents`, `__call__`) make this class compatible with both direct calls and LangChain's embedding interface convention, ensuring forward compatibility if the system is later integrated into a LangChain pipeline.

---

#### `get_vectorstore(text_chunks)` — Lines 397–441

Builds the FAISS index from a list of `unstructured` chunk objects:

**Step 1 — Decrypt API key:**
```python
api_key_e = Machine_A.decrypt_message(os.getenv('API_KEY_Embedding'), Machine_A.load_private_key())
```
The API key is stored encrypted in `.env`. It is decrypted at runtime using the local RSA private key (see §3.2 and §6).

**Step 2 — Extract text strings:**
```python
texts = [chunk.to_dict()['text'] for chunk in text_chunks]
```

**Step 3 — Batch embed:**
```python
embeddings = embedding_runnable(texts)
embeddings = np.array(embeddings)  # shape: (n_chunks, 1024)
d = embeddings.shape[1]            # d = 1024
```

**Step 4 — Build FAISS index:**
```python
index = faiss.IndexFlatL2(d)
index.add(embeddings)
```

`IndexFlatL2` performs **exhaustive** nearest-neighbour search using L2 (Euclidean) distance. It stores all vectors in memory and compares the query against every stored vector at search time. While slower than approximate indexes (like `IndexIVFFlat` or `IndexIVFPQ`, which are commented out), it provides **exact** results — critical for a thesis prototype where correctness is more important than millisecond latency.

The commented alternatives in the code show that the author evaluated:
- **`IndexIVFFlat`**: Clusters vectors into `nlist` cells (inverted file index). Only searches nearby cells at query time. Fast but approximate.
- **`IndexIVFPQ`**: Compresses vectors using Product Quantization on top of IVF. Extreme memory savings but more approximate.

Returns `(index, texts)` — the FAISS index and the parallel list of text strings (required for result lookup since FAISS only stores vectors, not the original text).

---

#### `count_tokens(text)` — Lines 527–529

```python
def count_tokens(text):
    return len(tokenizer.encode(text))
```

Uses the `cl100k_base` tiktoken tokenizer (the same tokenizer used by GPT-4 and text-embedding-ada-002) to count tokens precisely. This is used to enforce the 512-token context budget for the chat history passed to the LLM.

Note: an earlier naive implementation (lines 452–454) simply counted whitespace-split words. The tokenizer-based version is significantly more accurate because many words tokenize to 2+ tokens (especially in technical or non-English text).

---

#### `truncate_chat_history_(history)` — Lines 461–467

```python
def truncate_chat_history_(history):
    while sum(count_tokens(message['content']) for message in history) > 512:
        history.pop(0)
    return history
```

Iteratively removes the **oldest** messages from the chat history until the total token count is under 512. This is a FIFO (First-In, First-Out) eviction strategy — it preserves recent context at the cost of old context. This prevents the accumulated chat history from overwhelming the LLM's context window.

---

#### `LLMApiRunnable` Class — Lines 477–521

Abstracts calls to the Mistral-7B-Instruct LLM REST endpoint.

```python
payload = {
    "model": "mistral-7b-instruct",
    "temperature": temperature,     # default 0.1
    "max_tokens": max_tokens,       # default 1024
    "messages": [{"role": "user", "content": messages}]
}
```

**Mistral-7B-Instruct** is a 7-billion-parameter open-weight instruction-tuned LLM from Mistral AI. It is efficient enough to serve via REST API at acceptable latencies while being capable enough to perform summarisation, reasoning, and answer synthesis from provided context.

Key settings:
- **`temperature=0.1`**: Very low temperature produces highly deterministic, factual outputs. This is appropriate for a document Q&A system where consistency and accuracy matter more than creativity.
- **`max_tokens=1024`**: Caps the response length to prevent excessively long answers.

---

#### `get_conversation_chain_faiss(query, faiss_results)` — Lines 536–568

Constructs the full RAG prompt and calls the LLM:

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

**Prompt structure analysis:**
1. The user's raw question is provided as context.
2. The top-k retrieved chunks are presented, each with their L2 distance score. Providing the distance gives the LLM meta-information about retrieval confidence.
3. The instruction asks the LLM to synthesise and reorder — not to hallucinate, but to work purely from the provided evidence.

The response is appended to `st.session_state.chat_history` with `role: 'Siemens'` (identifying the bot's persona in the UI).

---

#### `Embedd_user_question(user_question)` — Lines 575–603

Embeds the user's query using the same BGE-M3 model used during ingestion. This is critical — **embedding model consistency** is required for meaningful similarity search: if the documents were embedded with model A and the query is embedded with model B, the vector spaces won't be aligned and search results will be meaningless.

Returns a 2D NumPy array of shape `(1, 1024)` ready for `faiss_index.search()`.

---

#### `handle_userinput(user_question)` — Lines 613–736

This is the central orchestration function called when the user submits a question. Full logic:

```
1. Guard: if no FAISS index loaded → show error
2. Truncate question to 70 words if too long
3. Append question to chat_history
4. Count total tokens (question + history)
5. IF tokens < 512:
     embed question → FAISS search (k=5) across all loaded indexes
     → collect & sort all results by L2 distance
     → call LLM with top-5 results
   ELSE:
     truncate chat_history → THEN embed → FAISS search → call LLM
6. Display updated chat history
```

**Multi-index search:** The `st.session_state.conversation` can hold a list of FAISS indexes (one per PDF). The code iterates over all of them, collecting up to `k=5` results from each, then globally sorts all results by L2 distance and selects the overall best 5 — enabling effective cross-document retrieval.

**nprobe setting:**
```python
for i in st.session_state.conversation:
    i.nprobe = 8
```
`nprobe` is a parameter for IVF-type indexes (how many cells to probe during search). For `IndexFlatL2`, this setting has no effect but is set preemptively to maintain compatibility if the index type is later upgraded.

---

#### `display_chat_history()` — Lines 754–762

Renders the chat history using the HTML templates from `htmlTemplates.py`:
- User messages → rendered with `user_template` (dark background `#2b313e`, user avatar icon).
- Bot messages → rendered with `bot_template` (slightly lighter `#475063`, Siemens logo).

`st.write(..., unsafe_allow_html=True)` renders raw HTML inside Streamlit, bypassing its default markdown renderer.

---

#### `check_if_present(DB_name, pdf)` — Lines 767–776

```python
cursor.execute(f'SELECT filename FROM pdf_analysis WHERE filename = "{pdf}"')
result = cursor.fetchall()
return bool(result)
```

Checks if a PDF has already been processed and stored in the database before ingestion. Prevents duplicate embeddings (which would waste compute and inflate the index) and duplicate rows.

---

#### `main()` — Lines 782–906

The Streamlit entry point, structured around sidebars and the main content area:

**Main area:**
- Page config (title, robot emoji icon).
- Injects custom CSS.
- Text input form + Submit button → `handle_userinput()`.

**Sidebar 1 — Database Selection:**
- Dropdown of all `.db` files found in the working directory.
- "Choose" button → `init_db()` to ensure the table exists.

**Sidebar 2 — PDF Upload & Processing:**
- Multi-PDF uploader.
- "Process" button → for each PDF:
  1. Save to disk.
  2. Check if already in DB (`check_if_present`).
  3. Extract text (`get_pdf_text`).
  4. Chunk (`get_text_chunks`).
  5. Embed + build FAISS index (`get_vectorstore`).
  6. Store in session state.
  7. Persist to SQLite (`save_analysis_to_db`).

**Sidebar 3 — Manual Selection:**
- Text input to specify document name(s), comma-separated (`vectorize()` splits on commas).
- "Select" button → loads existing embeddings from DB (`Load_selected_analysis_from_db`), restores FAISS indexes + text into session state.

---

### 3.2 `Machine_A.py` — Secure Key Management & Decryption

This module implements the **Machine A** side of an asymmetric RSA key infrastructure for securing API credentials.

#### `generate_keys()` — Lines 11–35

```python
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
```

Generates a **2048-bit RSA key pair**:
- **Private key** → saved to `./key/private_key.pem` (PKCS8, no passphrase). This key **never leaves Machine A**.
- **Public key** → saved to `./key/public_key.pem` (SubjectPublicKeyInfo PEM format). This is the shareable key, distributed to whoever needs to encrypt secrets for this machine.

`public_exponent=65537` is the standard RSA public exponent (Fermat number `F4`), universally used in modern RSA implementations for its balance of security and computational efficiency.

#### `load_private_key()` — Lines 37–39

```python
def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)
```

Loads the private key from disk at runtime. This is called lazily (only when a decryption is needed), ensuring the key material is kept in memory for the shortest possible time.

#### `decrypt_message(ciphertext, private_key)` — Lines 41–53

```python
decrypted_text = private_key.decrypt(
    base64.b64decode(ciphertext),
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
```

Decrypts a base64-encoded RSA ciphertext using **OAEP padding** (Optimal Asymmetric Encryption Padding) with SHA-256:

- **Why OAEP?** OAEP is probabilistic (each encryption of the same plaintext produces a different ciphertext) and provides semantic security against chosen-ciphertext attacks (CCA2-secure). It is the modern standard; older PKCS#1 v1.5 padding is vulnerable to Bleichenbacher attacks.
- **SHA-256** is used for both the mask generation function (MGF1) and the hash algorithm, providing 128-bit security.
- The ciphertext is stored **base64-encoded** in the `.env` file, making it safe to store as an ASCII string in a plain-text environment file.

A `rich` progress spinner is shown during decryption (cosmetic, since RSA 2048-bit decryption is essentially instantaneous on modern hardware).

#### `main()` — Lines 55–72

Entry point for key generation. Checks if `private_key.pem` already exists; if not, generates a new key pair. This ensures keys are generated once and never overwritten accidentally.

---

### 3.3 `htmlTemplates.py` — Chat UI Templates

Defines three Python string constants injected into the Streamlit app via `st.write(..., unsafe_allow_html=True)`.

#### `css` — Lines 1–26

Custom CSS styles for the chat interface:

```css
.chat-message { padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex }
.chat-message.user { background-color: #2b313e }   /* dark navy for user */
.chat-message.bot  { background-color: #475063 }   /* lighter slate for bot */
.chat-message .avatar { width: 20% }
.chat-message .avatar img { max-width: 78px; max-height: 78px; border-radius: 50%; object-fit: cover }
.chat-message .message { width: 80%; padding: 0 1.5rem; color: #fff }
```

A dark-themed chat UI with circular avatars (20% width) and message text (80% width) side-by-side — a standard chat bubble layout.

#### `user_template` — Lines 28–35

```html
<div class="chat-message user">
    <div class="avatar">
        <img src="https://img.icons8.com/?size=100&id=13042&format=png&color=000000">
    </div>
    <div class="message">{{MSG}}</div>
</div>
```

The `{{MSG}}` placeholder is replaced at runtime by `user_template.replace("{{MSG}}", user_message)`. The avatar is a generic person icon from Icons8.

#### `bot_template` — Lines 37–44

Identical structure to `user_template`, but uses the **Siemens logo** as the bot's avatar image, establishing the chatbot's corporate identity. This directly connects the thesis project to its intended deployment context within a Siemens environment.

---

## 4. End-to-End Data Flow

### Ingestion Flow (New PDF)

```
User uploads PDF via Streamlit
         │
         ▼
save_uploaded_file() → ./Analysed_PDFs/{name}.pdf
         │
         ▼
check_if_present() → if already in DB, skip
         │
         ▼
get_pdf_text() → partition_pdf(strategy="hi_res", infer_table_structure=True)
       → List of unstructured Elements [Title, NarrativeText, Table, ...]
         │
         ▼
get_text_chunks() → chunk_by_title(max_characters=3000, new_after_n_chars=2000)
       → List of Chunk objects (each with .text and .metadata)
         │
         ▼
get_vectorstore()
   ├─ Decrypt API key (Machine_A.decrypt_message)
   ├─ Extract text strings from chunks
   ├─ POST /embeddings → BGE-M3 API → List of 1024-dim vectors
   ├─ np.array(embeddings) → shape (n_chunks, 1024)
   ├─ faiss.IndexFlatL2(1024)
   ├─ index.add(embeddings)
   └─ return (index, texts)
         │
         ▼
st.session_state.conversation = index
st.session_state.text = texts
         │
         ▼
save_analysis_to_db()
   ├─ faiss.serialize_index(index) → bytes
   ├─ json.dumps(texts) → gzip.compress → bytes
   └─ INSERT OR REPLACE INTO pdf_analysis (filename, analysis, chunked_text, vectorstore)
```

### Query Flow (User Question)

```
User types question + clicks Submit
         │
         ▼
handle_userinput(user_question)
   ├─ Guard: session state must have conversation
   ├─ Truncate question to 70 words if needed
   ├─ Append {'role': 'user', 'content': question} to chat_history
   ├─ count_tokens(question) + count_tokens(all history)
   │
   ├─ IF total_tokens < 512: proceed directly
   │   ELSE: truncate_chat_history_() then proceed
   │
   ▼
Embedd_user_question(question)
   ├─ Decrypt API key
   ├─ POST /embeddings → BGE-M3 API → 1024-dim vector
   └─ return np.array([[...]]) shape (1, 1024)
         │
         ▼
FAISS search across all indexes in st.session_state.conversation:
   for index in conversation:
       distances, indices = index.search(query_embedding, k=5)
       → collect (text, distance) pairs
   → sort all pairs by distance (ascending = most similar first)
   → keep top_k_responses[:5]
         │
         ▼
get_conversation_chain_faiss(question, top_k_responses)
   ├─ Decrypt LLM API key
   ├─ Build prompt: question + top-5 chunks with distances
   ├─ POST to Mistral-7B-Instruct API (temperature=0.1, max_tokens=1024)
   ├─ Extract response text
   └─ Append {'role': 'Siemens', 'content': response} to chat_history
         │
         ▼
display_chat_history()
   → render user messages with user_template HTML
   → render bot messages with bot_template HTML
```

---

## 5. Component Deep-Dives

### 5.1 PDF Ingestion & Intelligent Chunking

**`partition_pdf` with `hi_res` strategy** processes PDFs as follows internally:
1. Calls `pdf2image` (which depends on **Poppler**) to rasterise each page at high DPI.
2. Runs a layout detection model to identify regions (text blocks, tables, images, page numbers, headers/footers).
3. Applies OCR (if needed) to image-based text.
4. Returns a list of typed `Element` objects with associated metadata.

The result is a structured representation that is far richer than a simple text extraction — it preserves the semantic role of each piece of content.

**Title-based chunking** then groups elements hierarchically: a chunk starts at a `Title` element and includes all subsequent non-title elements until the next `Title` (or the max character limit is reached). This mirrors how humans naturally segment documents and produces chunks that are contextually self-contained.

**Table handling** is noteworthy: tables are detected as `Table` elements with their cell content. The `convert_table_to_text` function reformats them using pipe (`|`) delimiters, making them readable as prose when embedded — this is important because embedding models process text, and a garbled tab-separated table would produce a poor-quality embedding.

### 5.2 Embedding Generation — EmbeddingApiRunnable

**BGE-M3** (BAAI General Embedding, version M3) produces **dense retrieval embeddings** of dimensionality **1024**. Key properties:
- Multilingual (100+ languages), suitable for technical documents in German, English, or mixed.
- Optimised for **symmetric retrieval** — both the documents and queries use the same embedding space.
- Outperforms older models like `text-embedding-ada-002` on many retrieval benchmarks.

The API follows the **OpenAI embeddings API** format (`/v1/embeddings`, `model` field, `data[].embedding` response), making it interchangeable.

### 5.3 FAISS Vector Store

`faiss.IndexFlatL2` implements exact nearest-neighbour search:

- **Storage**: All `n` vectors of dimension `d=1024` are stored as a flat matrix of `float32` values in memory. For 500 chunks × 1024 dimensions × 4 bytes = ~2 MB, which is trivially small.
- **Search complexity**: O(n·d) per query — every stored vector is compared to the query. This is "exact" in the sense that it always finds the true nearest neighbours.
- **Serialization**: `faiss.serialize_index` encodes the complete index (type, parameters, all stored vectors) to a byte array. `faiss.deserialize_index` reconstructs it perfectly, enabling lossless persistence to SQLite.

**L2 distance** (Euclidean distance squared) is computed as:
```
d(q, v) = Σ (q_i - v_i)²
```
Smaller distance = more similar. The top-5 retrievals with the lowest L2 distances are the most relevant chunks.

### 5.4 Persistent Storage — SQLite Database Layer

The SQLite schema provides a complete key-value store mapping PDF filenames to their processed artefacts:

```
pdf_analysis
├── filename     → TEXT (primary key, lookup by name)
├── analysis     → TEXT (future: LLM summary of the document)
├── chunked_text → BLOB (gzip-compressed JSON list of text strings)
└── vectorstore  → BLOB (raw serialised FAISS index)
```

**Compression rationale:** JSON text chunks for a 100-page document might be 500 KB; gzip typically achieves 60–80% compression on English text, bringing this down to ~100–200 KB. This substantially reduces database file size and SQLite read/write times.

**Multiple databases:** The system supports multiple `.db` files (one per project, manual set, or department). The user selects which database to work with from a dropdown, making this a **multi-tenant** knowledge base system at a simple level.

### 5.5 Query Pipeline — Retrieval & Generation

The RAG query pipeline implements the classic **Dense Passage Retrieval + Reader** architecture:

1. **Retrieval stage**: The query is embedded into the same vector space as the document chunks. FAISS finds the k=5 most similar chunks by L2 distance.
2. **Reader stage**: The LLM receives a structured prompt containing both the query and the top-5 retrieved passages and generates a synthesised answer.

The key insight is that the LLM does **not** need to "know" the answer from its training data — it reads the answer from the retrieved context. This makes the system **factually grounded** in the provided documents and reduces hallucination.

**Cross-document retrieval**: When multiple FAISS indexes exist in the session (i.e., several PDFs were selected via "Select Manuals"), the search is performed against all indexes. Results from all indexes are pooled and globally re-ranked by distance, so the final top-5 always contain the most relevant chunks regardless of which document they came from.

### 5.6 Token Budget Management

**Why 512 tokens?** This is a conservative budget for the combined query + history to ensure the retrieved context and LLM response both fit within the model's context window without truncation. Mistral-7B has a 32K token context window, but the prompt template (with retrieved chunks at potentially 3000 chars each × 5 = ~3750 tokens for chunks alone) means keeping the user query + history concise.

**Tiktoken cl100k_base** is used for precise counting. This is the tokenizer for GPT-4 and text-embedding-ada-002, and it closely approximates how Mistral's SentencePiece tokenizer counts tokens for English/German technical text.

**Truncation strategy**: FIFO eviction removes oldest messages first. This is the simplest strategy; more sophisticated systems might use importance scoring or summarisation of old turns.

### 5.7 RSA Encryption for API Key Security

The workflow for secure key usage:

```
[Setup time, on Machine A]:
Machine_A.main() → generate_keys()
→ private_key.pem (secret, stays on Machine A)
→ public_key.pem (shared with whoever sets up the .env)

[Provisioning time]:
Someone with the public key encrypts the real API key:
   ciphertext = RSA_encrypt(api_key, public_key)
   ciphertext_b64 = base64.b64encode(ciphertext)
→ placed in .env as: API_KEY=<ciphertext_b64>

[Runtime]:
Machine_A.load_private_key() → private_key (from disk)
Machine_A.decrypt_message(os.getenv('API_KEY'), private_key) → real_api_key
→ used once for the API request → discarded
```

**Security properties:**
- API keys are **never stored in plaintext** on disk.
- Even if `.env` is committed to version control accidentally, the keys remain protected (RSA-2048 + OAEP is computationally infeasible to break).
- The private key never leaves the machine; so even if the ciphertext is intercepted, it cannot be decrypted without the local private key.
- API keys are held in memory only for the duration of a single request.

### 5.8 UI Layer — Streamlit + Custom HTML/CSS

Streamlit provides the web framework. The custom `htmlTemplates.py` overrides Streamlit's default markdown rendering for chat messages with hand-crafted HTML/CSS that provides:

- **Dark theme** with dual shades distinguishing user (`#2b313e`) from bot (`#475063`).
- **Circular avatar images** using `border-radius: 50%` and `object-fit: cover`.
- **Flex layout** for avatar + message pairs.
- **Brand identity**: The Siemens logo avatar establishes the corporate context of the prototype.

The `{{MSG}}` template substitution is a minimal hand-rolled templating system — deliberately simple since only one variable is needed per message.

---

## 6. Security Design

| Aspect | Implementation |
|---|---|
| API key storage | RSA-2048/OAEP encrypted, base64-encoded in `.env` |
| Private key storage | PEM file on local disk, no passphrase (Machine A only) |
| Key generation | `cryptography` library (`hazmat.primitives`) - industry standard |
| Padding scheme | OAEP with MGF1-SHA256 — CCA2-secure |
| In-transit | HTTPS (assumed from API URL; enforced by requests library) |
| At-rest (DB) | SQLite on local filesystem; FAISS blobs are not encrypted |
| Duplicate protection | `INSERT OR REPLACE` + `check_if_present()` guard |

**Threat model covered:** An attacker who gains read access to the `.env` file cannot retrieve the API keys without also stealing the `private_key.pem`. An attacker who steals only the private key cannot retrieve the API keys without the corresponding `.env`.

**Gaps/future work:** The SQLite database and FAISS blobs are not encrypted at rest. Sensitive document content is stored in plaintext (gzip-compressed) in the database. For a production deployment handling confidential documents, database encryption (e.g., SQLCipher) should be considered.

---

## 7. Design Decisions & Trade-offs

| Decision | Choice Made | Alternative / Trade-off |
|---|---|---|
| Vector search | FAISS IndexFlatL2 (exact) | IVFFlat/IVFPQ would be faster but approximate — chosen precision over speed |
| Embedding model | BGE-M3 (1024-dim, multilingual) | ada-002 would be simpler but OpenAI-dependent; BGE-M3 is self-hostable |
| LLM | Mistral-7B-Instruct (REST API) | GPT-4 would be more capable but proprietary/expensive; Mistral is open-weight |
| PDF parser | unstructured (hi_res) | PyPDF2/pdfminer would be faster but miss tables/layouts |
| Chunking | chunk_by_title (semantic) | Fixed-size chunking would be simpler but semantically arbitrary |
| Persistence | SQLite | A vector DB like Chroma/Qdrant would be more scalable but adds dependencies |
| UI | Streamlit | Django/Flask would be more flexible but require more frontend work |
| Security | RSA-2048 + custom Machine_A | Standard secret management (HashiCorp Vault, AWS Secrets Manager) would be enterprise-grade |
| Chat memory | Simple list with FIFO truncation | LangChain Memory modules offer more sophisticated strategies |

---

## 8. Limitations & Future Work

1. **Single-machine deployment**: The RSA key infrastructure ties the application to one machine. A proper secrets manager would support distributed deployment.
2. **No re-ranking**: Results are ranked purely by L2 distance (embedding similarity). A cross-encoder re-ranker (like BGE-Reranker) would improve precision by scoring (query, chunk) pairs together.
3. **No query expansion**: The user's query is embedded as-is. Techniques like HyDE (Hypothetical Document Embeddings) or query reformulation could improve recall.
4. **FAISS index not updated incrementally**: Adding a new document creates a separate FAISS index. A merged index or a proper vector DB would enable unified search.
5. **No source citation**: The UI shows the LLM's answer but does not display which PDF pages the information came from. Adding page/section attribution would improve trustworthiness.
6. **Table embeddings**: Tables are converted to pipe-delimited text before embedding. Dedicated table embedding models or structured retrieval would handle tabular data better.
7. **No authentication**: The Streamlit app has no login mechanism. Any user on the network can access all documents.
8. **Flask app is imported but not used**: The Flask import creates an app object but never starts a server. This is dead code, likely from an earlier architecture where a separate REST API layer was planned.

---

## 9. Dependency Map

```
ChatBox_complete.py
├── streamlit              → Web UI framework
├── unstructured           → PDF ingestion & element-based chunking
│   ├── partition_pdf      → hi-res PDF parsing (requires Poppler)
│   └── chunk_by_title     → semantic chunking strategy
├── faiss                  → Vector similarity search (CPU version)
├── numpy                  → Numerical array operations for embeddings
├── tiktoken               → Token counting (cl100k_base encoder)
├── sqlite3                → Persistent storage (stdlib)
├── gzip                   → Text compression (stdlib)
├── json                   → Serialisation (stdlib)
├── requests               → REST API HTTP calls
├── python-dotenv          → .env file loading
├── flask                  → (imported, not actively used)
├── Machine_A              → RSA decryption for API keys
│   └── cryptography       → RSA key ops (OAEP/MGF1/SHA256)
│       └── rich           → Progress spinner UI
└── htmlTemplates          → Custom HTML/CSS chat templates

External APIs:
├── BGE-M3 Embedding API   → env: API_EMBEDDING, API_KEY_Embedding (encrypted)
└── Mistral-7B-Instruct    → env: API_URL, API_KEY (encrypted)

External tools:
└── Poppler                → PDF rasterisation for hi-res parsing
    └── path: poppler-25.11.0/Library/bin (added to PATH at runtime)
```

---

*Documentation generated for thesis project: AI ChatBot — RAG System*  
*Date: March 2026*
