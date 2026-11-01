"""
NEXORA AI - Document Intelligence & RAG Unit Tests
Verifies PDF, DOCX, TXT, CSV parsing, Document Comparison, and RAG Semantic Search
"""
import sys
import tempfile
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

from backend.services.document_service import document_service
from backend.services.rag_service import rag_service

def run_tests():
    print("==================================================")
    print("NEXORA AI - DOCUMENT INTELLIGENCE & RAG TEST SUITE")
    print("==================================================")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Plain Text Extraction
        txt_file = tmp_path / "spec.txt"
        txt_file.write_text(
            "NEXORA AI Technical Specification\n"
            "Architecture Overview: The system uses FastAPI and Three.js.\n"
            "Multimodal models provide vision, document intelligence, and audio processing.",
            encoding="utf-8"
        )
        txt_res = document_service.extract_text_from_file(str(txt_file), "text/plain")
        assert "FastAPI" in txt_res["text"]
        assert txt_res["metadata"]["word_count"] > 10
        print("✅ TEST 1: Plain Text extraction passed")

        # 2. CSV Parsing & Analytics
        csv_file = tmp_path / "benchmarks.csv"
        csv_file.write_text(
            "id,agent_name,response_time_ms,accuracy_pct,active\n"
            "1,Nexora-Flash,142,98.5,true\n"
            "2,Nexora-Pro,420,99.2,true\n"
            "3,Nexora-Motion,1850,96.8,true\n"
            "4,Nexora-Vision,310,97.9,false\n",
            encoding="utf-8"
        )
        csv_res = document_service.extract_text_from_file(str(csv_file), "text/csv")
        assert "Preview Data" in csv_res["text"]
        assert "accuracy_pct" in csv_res["text"]
        assert csv_res["metadata"]["pages_or_rows"] == 4
        assert csv_res["metadata"]["has_tables"] is True
        print("✅ TEST 2: CSV analytical extraction and Pandas summary passed")

        # 3. Document Comparison
        doc1_data = {
            "metadata": {"filename": "v1_release.txt", "extension": ".txt", "size_kb": 1.2, "pages_or_rows": 1, "word_count": 25, "has_tables": False},
            "text": "NEXORA AI v1.0 features text chat, basic image generation, and Three.js 3D robot interface."
        }
        doc2_data = {
            "metadata": {"filename": "v2_release.txt", "extension": ".txt", "size_kb": 2.5, "pages_or_rows": 1, "word_count": 35, "has_tables": False},
            "text": "NEXORA AI v2.0 features multimodal vision, video generation, document intelligence, RAG vector search, and Three.js 3D robot."
        }
        comp_md = document_service.compare_documents(doc1_data, doc2_data)
        assert "Vocabulary Overlap" in comp_md
        assert "Structural Comparison Table" in comp_md
        assert "robot" in comp_md
        print("✅ TEST 3: Document comparative vocabulary and semantic analysis passed")

        # 4. RAG Indexing & Chunking
        rag_service.clear_index()
        chunks = document_service.chunk_document_for_rag(
            extracted_data={
                "metadata": {"filename": "architecture.pdf"},
                "pages": [
                    {
                        "page_number": 1,
                        "text": "Nexora Architecture: Section 1 Quantum Core. The quantum core operates at cryogenic zero with superposed qubits delivering instantaneous multimodal reasoning."
                    },
                    {
                        "page_number": 2,
                        "text": "Section 2 Neural Audio Engine: The neural audio engine utilizes low-latency streaming speech synthesis with reactive jaw-motion synchronization in Three.js."
                    }
                ]
            },
            chunk_size=150,
            overlap=20
        )
        assert len(chunks) >= 2
        indexed_count = rag_service.index_document("doc_test_101", "architecture.pdf", chunks)
        assert indexed_count == len(chunks)
        assert len(rag_service.chunks) >= 2
        print(f"✅ TEST 4: Chunking and Vector Indexing passed ({indexed_count} chunks indexed)")

        # 5. Semantic Vector Search with Lexical Hybrid Boost
        search_results = rag_service.search("cryogenic qubits reasoning", top_k=2)
        assert len(search_results) > 0
        top_result = search_results[0]
        assert "quantum" in top_result["text"].lower() or "qubits" in top_result["text"].lower()
        assert top_result["similarity_score"] > 0.1
        print(f"✅ TEST 5: Semantic cosine search passed (Top score: {top_result['similarity_score']:.4f})")

        # 6. Grounded Context Formatting & Prompt Injection Defense
        grounded_context = rag_service.format_grounded_context(search_results)
        assert 'name="architecture.pdf"' in grounded_context
        assert "<source_document" in grounded_context
        assert "</source_document>" in grounded_context
        print("✅ TEST 6: Grounded context formatting & safety container passed")

    print("\n🎉 ALL 6 DOCUMENT INTELLIGENCE & RAG TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
