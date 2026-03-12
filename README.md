# Thesis2026


# Thesis Projects — Production Branch-> Log PArser,  RAG Branch-> ChatBot 


This branch contains two independent but complementary thesis projects built during work at **Siemens**. Both tools are production-ready prototypes designed to assist engineers in working with internal data more efficiently.

---

## Projects Overview

| Project | Folder | Purpose |
|---|---|---|
| 🔍 **Log Parser** | `Log_Parser/` | Parse, visualise, and analyse Siemens transaction logs |
| 🤖 **RAG Chatbot** | `Rag/` | Ask questions about internal PDF documents using AI |

---

## 🔍 Project 1 — Log Parser

**Folder:** `Log_Parser/`

### What it does

The **Siemens Transaction Log Parser** is a desktop application that ingests raw Siemens enterprise transaction log files (CDOs, CLFs, XML) and transforms them into readable, comparable, and analysable data. Engineers can visually browse log trees, compare two log files side by side, run AI-assisted analysis, and export structured Excel overviews — all from a single GUI.

### Main Files

| File | Description |
|---|---|
| `Log_Parser_Ultimate.py` | Main GUI application (~3,677 lines) — log viewer, comparison engine, AI integration, XML/JSON pipeline |
| `Structure_Excel.py` | Batch analysis module (~656 lines) — parses logs and exports `_Overview.xlsx` |

### Key Features

- **Interactive log tree viewer** — browse transaction depths, CDO names, delta times
- **Side-by-side log comparison** — synchronised scroll, token-level diff with `[FOUND]` / `[NOT FOUND]` classification
- **AI analysis (SiemensGPT)** — Mistral-7B-Instruct via Siemens LLM API, with map-reduce summarisation over long logs
- **XML / JSON export** — async pipeline generating structured `_tree_analysis.json` with query rankings and timing percentages
- **Excel overview export** — `_Overview.xlsx` with 12 columns including gap times, CDO deltas, process IDs
- **Performance** — memory-mapped file I/O (`mmap`), pre-compiled regex, 1000-op batched UI inserts, deque-based call stack

### How to Run

```bash
# Install dependencies
pip install pandas openpyxl matplotlib chardet nltk requests lxml beautifulsoup4 colorama PyQt6

# Launch the GUI
python Log_Parser_Ultimate.py

# Run batch Excel analysis only
python Structure_Excel.py
```

### Tech Stack

`tkinter` · `PyQt6` · `pandas` · `openpyxl` · `matplotlib` · `lxml` · `BeautifulSoup` · `asyncio` · `mmap` · `Mistral-7B` (via Siemens LLM API)

---

## 🤖 Project 2 — RAG Chatbot

**Folder:** `Rag/`

### What it does

The **RAG Chatbot** is a web application that lets users upload internal PDF documents (manuals, reports, specifications) and then ask natural language questions about their content. Rather than relying on the LLM's pre-trained knowledge, the system retrieves the most relevant passages from the uploaded documents and grounds every answer in that evidence — dramatically reducing hallucination and keeping responses factually tied to the actual source material.

### Main Files

| File | Description |
|---|---|
| `ChatBox_complete.py` | Core RAG engine and Streamlit UI (~906 lines) — PDF ingestion, embedding, FAISS search, LLM generation |
| `Machine_A.py` | RSA-2048 key management and API key decryption module |
| `htmlTemplates.py` | Custom HTML/CSS chat bubble templates (dark theme, Siemens avatar) |

### Key Features

- **PDF ingestion** — high-resolution layout analysis via `unstructured` (handles tables, multi-column, scanned pages)
- **Semantic chunking** — `chunk_by_title` groups content under section headings for coherent retrieval units
- **BGE-M3 embeddings** — 1024-dimensional multilingual vectors (100+ languages, outperforms ada-002 on retrieval benchmarks)
- **FAISS vector search** — exact nearest-neighbour search (`IndexFlatL2`) across all uploaded documents simultaneously
- **SQLite persistence** — FAISS indexes and gzip-compressed text chunks stored per knowledge base; reloaded without re-processing
- **Multi-document querying** — results from all loaded PDFs are pooled and globally re-ranked by similarity score
- **Token budget management** — `tiktoken cl100k_base` enforces a 512-token FIFO history window
- **RSA-secured API keys** — keys encrypted at rest with RSA-2048/OAEP; decrypted only at runtime for each request

### How to Run

```bash
# Install dependencies
pip install streamlit unstructured faiss-cpu numpy tiktoken requests python-dotenv cryptography rich

# Generate RSA keys (first time only)
python Machine_A.py

# Launch the web app
streamlit run ChatBox_complete.py
```

Then open `http://localhost:8501` in your browser.

### Tech Stack

`Streamlit` · `unstructured` · `FAISS` · `BGE-M3` (Siemens Embedding API) · `Mistral-7B-Instruct` (Siemens LLM API) · `SQLite` · `tiktoken` · `cryptography (RSA-2048/OAEP)`

---

## Repository Structure

```
Production/                         ← you are here (branch: Production)
│
├── Log_Parser/
│   ├── Log_Parser_Ultimate.py      ← Main GUI application
│   ├── Structure_Excel.py          ← Batch Excel export module
│   └── config.json                 ← API key config (auto-generated)
│
├── Rag/
│   ├── ChatBox_complete.py         ← Core RAG engine + Streamlit UI
│   ├── Machine_A.py                ← RSA key management
│   ├── htmlTemplates.py            ← Chat UI HTML/CSS templates
│   ├── .env                        ← Encrypted API keys (DO NOT COMMIT plaintext keys)
│   ├── key/
│   │   ├── private_key.pem         ← RSA private key (NEVER share or commit)
│   │   └── public_key.pem          ← RSA public key (safe to share)
│   └── Analysed_PDFs/              ← Uploaded PDFs (auto-created at runtime)
│
└── README.md                       ← This file
```

---

## External Dependencies

Both projects call Siemens internal APIs. You will need valid credentials configured before running.

| API | Used By | Environment Variable |
|---|---|---|
| Siemens LLM API (Mistral-7B-Instruct) | Log Parser, RAG Chatbot | `API_KEY` / `DEFAULT_API_KEY` |
| Siemens Embedding API (BGE-M3) | RAG Chatbot | `API_KEY_Embedding` |

> ⚠️ API keys for the RAG Chatbot are **RSA-encrypted** and stored in `.env`. Run `python Machine_A.py` once to generate the key pair, then encrypt your keys using the generated `public_key.pem` before placing them in `.env`.

---

## Documentation

Full technical documentation for both projects is available as separate manuals:

- 📄 `Siemens_Log_Parser_Manual.html` — Log Parser technical reference
- 📄 `RAG_Chatbot_Manual.html` — RAG Chatbot technical reference

Both manuals cover system architecture, file-by-file function breakdowns, data flow diagrams, security design, and design decision rationale.

---

## Notes

- The two projects are **independent** — they do not share code or state, and can be run separately.
- Both were developed and tested on **Windows** with Python 3.10+.
- The Log Parser requires **Poppler** binaries on `PATH` for its high-resolution PDF rendering (used in the XML analysis sub-feature). The path is configured inside `Log_Parser_Ultimate.py`.
- The RAG Chatbot also requires **Poppler** for `unstructured`'s `hi_res` PDF partitioning strategy.

---

*Thesis Project — Siemens Internship · March 2026*
