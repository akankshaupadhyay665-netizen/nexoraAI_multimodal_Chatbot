"""
Nexora AI - Document Service & Text Extraction Tests
"""
import tempfile
from pathlib import Path
from backend.services.document_service import document_service

def test_chunk_text():
    """Verify document chunking divides large text properly"""
    sample_text = "Word " * 600  # ~3000 chars
    chunks = document_service.chunk_text(sample_text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 3
    assert all(len(c) <= 1000 for c in chunks)

def test_quick_summary():
    """Verify structured bullet summarization"""
    text = (
        "Artificial Intelligence is transforming modern industries.\n"
        "Machine Learning models learn patterns directly from datasets.\n"
        "Computer Vision enables machines to interpret visual inputs.\n"
        "Natural Language Processing enables conversational agents."
    )
    summary = document_service.generate_quick_summary(text, max_points=3)
    assert "•" in summary
    assert "Artificial Intelligence" in summary

def test_text_file_extraction():
    """Verify extraction from text file"""
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as f:
        f.write("Line 1: Nexora AI platform.\nLine 2: Multimodal generative intelligence.")
        f_path = f.name

    try:
        res = document_service.extract_text_from_file(f_path, "text/plain")
        assert "Nexora AI platform" in res["text"]
        assert res["metadata"]["word_count"] > 5
    finally:
        Path(f_path).unlink(missing_ok=True)

