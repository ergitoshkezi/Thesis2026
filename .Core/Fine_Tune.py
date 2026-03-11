"""
PDF → Unstructured → Chunked JSONL for LLM Fine-Tuning

Dependencies:
    pip install unstructured[pdf] tqdm

Folder Structure:
    data/
      ├── pdfs/
      │     ├── file1.pdf
      │     ├── file2.pdf
      └── processed/
            ├── file1.jsonl
            ├── file2.jsonl
"""

import os
import json
from tqdm import tqdm

from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

# Add Poppler bin folder to PATH so pdf2image can find it
poppler_bin_path = r"C:\Users\z004rnva\ALT\Definitve_Project\AI_Chatbot\poppler-25.11.0\Library\bin"
os.environ["PATH"] += os.pathsep + poppler_bin_path
# =========================
# CONFIG
# =========================

PDF_DIR = "data/pdfs"
OUTPUT_DIR = r"C:\Users\z004rnva\ALT\Definitve_Project\AI_Chatbot\.Core\data\processed"

MAX_CHARACTERS = 3000
NEW_AFTER_N_CHARS = 2000
MIN_TEXT_LENGTH = 200

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# CORE FUNCTIONS
# =========================

def parse_pdf(pdf_path):
    """
    Extract structured elements from PDF using Unstructured
    """
    return partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        infer_table_structure=True,
        ocr_languages="eng"
    )


def chunk_elements(elements):
    """
    Chunk elements using title-aware segmentation
    """
    return chunk_by_title(
        elements,
        max_characters=MAX_CHARACTERS,
        new_after_n_chars=NEW_AFTER_N_CHARS,
        multipage_sections=False
    )


def normalize_text(text: str) -> str:
    """
    Clean text for training
    """
    text = text.replace("\n\n", "\n")
    return text.strip()


def write_jsonl(chunks, pdf_name, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            text = normalize_text(chunk.text)

            if len(text) < MIN_TEXT_LENGTH:
                continue

            record = {
                "id": f"{pdf_name}_chunk_{i}",
                "source": pdf_name,
                "text": text,
                "metadata": {
                    "title": getattr(chunk.metadata, "title", None),
                    "page_number": getattr(chunk.metadata, "page_number", None),
                    "section_depth": getattr(chunk.metadata, "section_depth", None),
                    "category": chunk.category
                }
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")

# =========================
# PIPELINE
# =========================

def process_all_pdfs():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDFs found.")
        return

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        output_file = pdf_file.replace(".pdf", ".jsonl")
        output_path = os.path.join(OUTPUT_DIR, output_file)

        if os.path.exists(output_path):
            print(f"Skipping {pdf_file} (already processed)")
            continue

        try:
            elements = parse_pdf(pdf_path)
            chunks = chunk_elements(elements)
            write_jsonl(chunks, pdf_file, output_path)
            print(f"Processed {pdf_file}")

        except Exception as e:
            print(f"Failed {pdf_file}: {e}")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    process_all_pdfs()
