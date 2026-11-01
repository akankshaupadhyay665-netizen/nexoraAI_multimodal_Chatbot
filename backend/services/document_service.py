"""
Nexora AI - Advanced Document Intelligence Service
Supports PDF, DOCX, TXT, CSV with Page-wise Extraction, Scanned Detection, Table Extraction, and Document Comparison
"""
import os
import io
import re
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from pypdf import PdfReader
from docx import Document
import pandas as pd

class DocumentService:
    @staticmethod
    def extract_text_from_file(file_path: str, mime_type: str = "") -> Dict[str, Any]:
        """
        Extracts structured, page-wise and table-aware text from documents.
        Handles PDF, DOCX, CSV, TXT, Markdown, code, and structured spreadsheets.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        ext = path.suffix.lower()
        file_size_bytes = path.stat().st_size
        metadata: Dict[str, Any] = {
            "filename": path.name,
            "extension": ext,
            "size_bytes": file_size_bytes,
            "size_kb": round(file_size_bytes / 1024, 2),
            "mime_type": mime_type,
            "pages_or_rows": 0,
            "is_scanned": False,
            "has_tables": False,
            "table_count": 0,
            "sections": []
        }

        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        # ============================================================
        # 1. PDF EXTRACTION (Page-Wise, Structure, Scanned Detection)
        # ============================================================
        if ext == ".pdf" or "pdf" in mime_type:
            try:
                reader = PdfReader(str(path))
                num_pages = len(reader.pages)
                metadata["pages_or_rows"] = num_pages

                total_chars = 0
                for i, page in enumerate(reader.pages):
                    page_num = i + 1
                    try:
                        raw_page_text = page.extract_text() or ""
                    except Exception:
                        raw_page_text = ""

                    cleaned_text = raw_page_text.strip()
                    total_chars += len(cleaned_text)

                    pages_data.append({
                        "page_number": page_num,
                        "text": cleaned_text,
                        "char_count": len(cleaned_text),
                        "word_count": len(cleaned_text.split())
                    })
                    full_text_parts.append(f"--- [Page {page_num}] ---\n{cleaned_text}")

                # Scanned PDF Detection heuristic: page count > 0 but total characters very low
                if num_pages > 0 and (total_chars / num_pages) < 25:
                    metadata["is_scanned"] = True
                    metadata["scan_notice"] = (
                        "Notice: This PDF appears to contain scanned images or rasterized pages. "
                        "Digital text extraction yielded minimal characters. OCR visual parsing recommended."
                    )

            except Exception as e:
                full_text_parts.append(f"[PDF Extraction Warning: Encrypted or non-standard format - {str(e)}]")

        # ============================================================
        # 2. DOCX EXTRACTION (Paragraphs, Headings & Tables)
        # ============================================================
        elif ext in [".docx", ".doc"] or "wordprocessing" in mime_type or "msword" in mime_type:
            try:
                doc = Document(str(path))
                metadata["pages_or_rows"] = len(doc.paragraphs)
                
                # Extract Headings and Paragraphs
                doc_sections = []
                current_heading = "General"
                current_content: List[str] = []

                for para in doc.paragraphs:
                    text = para.text.strip()
                    if not text:
                        continue
                    # Check if styled as heading
                    style_name = para.style.name.lower() if para.style else ""
                    if "heading" in style_name or (len(text) < 80 and text.isupper()):
                        if current_content:
                            doc_sections.append({"heading": current_heading, "text": "\n".join(current_content)})
                            current_content = []
                        current_heading = text
                    else:
                        current_content.append(text)

                if current_content:
                    doc_sections.append({"heading": current_heading, "text": "\n".join(current_content)})

                metadata["sections"] = [s["heading"] for s in doc_sections]

                # Format paragraphs
                for s in doc_sections:
                    full_text_parts.append(f"### {s['heading']}\n{s['text']}")

                # Extract Tables
                if doc.tables:
                    metadata["has_tables"] = True
                    metadata["table_count"] = len(doc.tables)
                    full_text_parts.append("\n#### 📊 Extracted Document Tables:")
                    for t_idx, table in enumerate(doc.tables):
                        table_rows = []
                        for row in table.rows:
                            row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                            table_rows.append(row_cells)

                        if table_rows:
                            full_text_parts.append(f"\n*Table {t_idx + 1}:*")
                            header = table_rows[0]
                            full_text_parts.append("| " + " | ".join(header) + " |")
                            full_text_parts.append("| " + " | ".join(["---"] * len(header)) + " |")
                            for r in table_rows[1:]:
                                # Pad row if needed
                                row_padded = r + [""] * (len(header) - len(r))
                                full_text_parts.append("| " + " | ".join(row_padded[:len(header)]) + " |")

            except Exception as e:
                full_text_parts.append(f"[DOCX Extraction Notice: {str(e)}]")

        # ============================================================
        # 3. CSV EXTRACTION (Pandas Analysis, Headers, Summaries & Tables)
        # ============================================================
        elif ext == ".csv" or "csv" in mime_type:
            try:
                df = pd.read_csv(str(path), encoding="utf-8", on_bad_lines="skip")
            except Exception:
                try:
                    df = pd.read_csv(str(path), encoding="latin1", on_bad_lines="skip")
                except Exception as e:
                    df = pd.DataFrame()
                    full_text_parts.append(f"[CSV Read Error: {str(e)}]")

            if not df.empty:
                rows_count, cols_count = df.shape
                metadata["pages_or_rows"] = rows_count
                metadata["has_tables"] = True
                metadata["table_count"] = 1
                metadata["columns"] = list(df.columns)

                # Generate Statistical Summary
                summary_lines = [
                    f"### 📊 Dataset Overview: `{path.name}`",
                    f"- **Total Rows**: {rows_count:,}",
                    f"- **Total Columns**: {cols_count} (`{', '.join(map(str, df.columns[:15]))}`)",
                    f"- **Memory Usage**: {round(df.memory_usage().sum() / 1024, 2)} KB\n",
                    "#### 📋 Column Schema & Data Types:"
                ]
                for col in df.columns[:20]:
                    null_count = int(df[col].isnull().sum())
                    dtype_str = str(df[col].dtype)
                    summary_lines.append(f"- **{col}**: `{dtype_str}` ({null_count} nulls)")

                # If numerical columns exist, provide statistical preview
                num_df = df.select_dtypes(include=["number"])
                if not num_df.empty:
                    summary_lines.append("\n#### 📈 Numerical Statistics (Min, Mean, Max):")
                    for col in num_df.columns[:8]:
                        col_min = round(float(num_df[col].min()), 2)
                        col_mean = round(float(num_df[col].mean()), 2)
                        col_max = round(float(num_df[col].max()), 2)
                        summary_lines.append(f"- **{col}**: Min = `{col_min}`, Mean = `{col_mean}`, Max = `{col_max}`")

                # Preview first 10 rows formatted as Markdown Table
                summary_lines.append("\n#### 🔍 Preview Data (First 10 Rows):")
                preview_df = df.head(10).fillna("")
                try:
                    headers = [str(c) for c in preview_df.columns]
                    tbl_lines = ["| " + " | ".join(headers) + " |"]
                    tbl_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    for _, row in preview_df.iterrows():
                        tbl_lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
                    summary_lines.append("\n".join(tbl_lines))
                except Exception:
                    summary_lines.append(str(preview_df))

                full_text_parts.append("\n".join(summary_lines))

        # ============================================================
        # 4. TXT / CODE / MARKDOWN EXTRACTION
        # ============================================================
        elif ext in [".txt", ".md", ".json", ".py", ".js", ".html", ".css", ".sql", ".yaml", ".yml", ".xml"] or "text" in mime_type:
            raw_content = ""
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    with open(path, "r", encoding=encoding) as f:
                        raw_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            metadata["pages_or_rows"] = len(raw_content.splitlines())
            full_text_parts.append(raw_content)

        # ============================================================
        # 5. FALLBACK BINARY / UNKNOWN
        # ============================================================
        else:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(50000)
                metadata["pages_or_rows"] = len(content.splitlines())
                full_text_parts.append(content)
            except Exception:
                full_text_parts.append("[Binary or unsupported file format]")

        final_extracted_text = "\n\n".join(full_text_parts).strip()
        metadata["char_count"] = len(final_extracted_text)
        metadata["word_count"] = len(final_extracted_text.split())

        return {
            "text": final_extracted_text,
            "metadata": metadata,
            "pages": pages_data
        }

    @staticmethod
    def chunk_document_for_rag(
        extracted_data: Dict[str, Any],
        chunk_size: int = 1000,
        overlap: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Splits extracted document text into semantic chunks while preserving
        page numbers, section references, and document metadata.
        """
        chunks: List[Dict[str, Any]] = []
        filename = extracted_data.get("metadata", {}).get("filename", "document")
        pages = extracted_data.get("pages", [])

        # If page-wise data is available (PDF)
        if pages:
            for page in pages:
                page_num = page["page_number"]
                page_text = page["text"]
                if not page_text:
                    continue

                # Split page text into overlapping windows
                start = 0
                while start < len(page_text):
                    end = start + chunk_size
                    chunk_text = page_text[start:end].strip()
                    if chunk_text:
                        chunks.append({
                            "filename": filename,
                            "page": page_num,
                            "chunk_id": f"{filename}_p{page_num}_c{len(chunks)}",
                            "text": chunk_text,
                            "char_count": len(chunk_text)
                        })
                    start += chunk_size - overlap
        else:
            # Linear chunking for DOCX, CSV, TXT
            full_text = extracted_data.get("text", "")
            start = 0
            chunk_idx = 0
            while start < len(full_text):
                end = start + chunk_size
                chunk_text = full_text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "filename": filename,
                        "page": 1,
                        "chunk_id": f"{filename}_c{chunk_idx}",
                        "text": chunk_text,
                        "char_count": len(chunk_text)
                    })
                    chunk_idx += 1
                start += chunk_size - overlap

        return chunks

    @staticmethod
    def compare_documents(doc1_data: Dict[str, Any], doc2_data: Dict[str, Any]) -> str:
        """
        Performs high-level semantic and structural comparison between two documents.
        """
        meta1 = doc1_data.get("metadata", {})
        meta2 = doc2_data.get("metadata", {})

        name1 = meta1.get("filename", "Document 1")
        name2 = meta2.get("filename", "Document 2")

        words1 = set(re.findall(r'\b[a-zA-Z]{4,}\b', doc1_data.get("text", "").lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]{4,}\b', doc2_data.get("text", "").lower()))

        shared_terms = words1.intersection(words2)
        unique_to_1 = words1 - words2
        unique_to_2 = words2 - words1

        jaccard_similarity = round((len(shared_terms) / max(1, len(words1.union(words2)))) * 100, 2)

        comparison_report = [
            f"### ⚖️ Document Comparison: `{name1}` vs `{name2}`\n",
            "#### 📊 Structural Comparison Table:",
            f"| Metric | `{name1}` | `{name2}` |",
            f"| :--- | :--- | :--- |",
            f"| **Format** | `{meta1.get('extension', 'unknown')}` | `{meta2.get('extension', 'unknown')}` |",
            f"| **File Size** | {meta1.get('size_kb', 0)} KB | {meta2.get('size_kb', 0)} KB |",
            f"| **Pages / Rows** | {meta1.get('pages_or_rows', 0)} | {meta2.get('pages_or_rows', 0)} |",
            f"| **Word Count** | {meta1.get('word_count', 0):,} words | {meta2.get('word_count', 0):,} words |",
            f"| **Has Tables** | {'Yes' if meta1.get('has_tables') else 'No'} | {'Yes' if meta2.get('has_tables') else 'No'} |\n",
            f"#### 🔍 Content Similarity Metric:",
            f"- **Vocabulary Overlap (Jaccard Index)**: **{jaccard_similarity}%**",
            f"- **Shared Core Terms ({len(shared_terms)} terms)**: `{', '.join(list(shared_terms)[:15])}`\n",
            f"#### 📌 Key Content Distinctions:",
            f"- **Distinctive to `{name1}`**: `{', '.join(list(unique_to_1)[:12])}`",
            f"- **Distinctive to `{name2}`**: `{', '.join(list(unique_to_2)[:12])}`\n",
            "> [!NOTE]\n",
            f"> *This comparative analysis was synthesized directly from the extracted text of both documents.*"
        ]

        return "\n".join(comparison_report)

document_service = DocumentService()
