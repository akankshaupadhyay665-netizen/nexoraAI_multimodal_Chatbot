# NEXORA AI — Official Changelog

All notable changes to the **NEXORA AI** platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.0] - 2026-11-01 (Multimodal Master Release)

### Added
- **Document Intelligence System**:
  - Page-wise extraction for PDF documents with page boundaries (`--- [Page X] ---`).
  - Scanned PDF detection heuristic (`is_scanned: True` when characters per page < 25).
  - Structured Word DOCX extraction converting Word XML tables to Markdown tables.
  - CSV analytical parsing via `pandas` extracting row counts, column schemas, null counts, numerical statistics (min/mean/max), and 10-row preview grid.
  - Document comparison engine (`DocumentService.compare_documents`) calculating Jaccard vocabulary overlap, shared core terms, and distinctive vocabulary.
- **RAG Knowledge Base & Semantic Search**:
  - Contextual chunking preserving `filename`, `page_number`, and unique `chunk_id`.
  - Zero-dependency local continuous dense vector representation using character 3-gram and word frequency hashing with L2 normalization.
  - Hybrid retrieval engine combining cosine similarity with exact lexical match boost.
  - Strict anti-prompt-injection security wrapper isolating retrieved context inside `<source_document>` XML containers with source citations.
  - Dedicated `/api/files/rag/search` and `/api/files/compare` endpoints.
- **Advanced Image Understanding**:
  - Multi-image selection and drag-and-drop support (`multiple` file input).
  - Direct conversion of staged images to binary parts (`types.Part.from_bytes`) for Gemini Vision processing.
  - Chart, screenshot, and diagram visual comprehension.
- **Image Studio Enhancements**:
  - Multi-image batch variations selector with 4 interactive pills (`1 Image`, `2 Variations`, `3 Variations`, `4 Variations`).
  - New batch generation endpoint `POST /api/image/generate-batch` using varied sub-seeds.
  - One-click prompt regeneration in chat and image studio.
- **Voice & Audio Controls**:
  - Ingestion and transcription of audio files (WAV, MP3, M4A, WEBM, OGG) with executive summary and key topic extraction.
  - Integrated Voice Volume slider (`#setting-voice-volume`) with persistent `localStorage` synchronization.
  - Speech playback rate selector (`#setting-voice-rate`) and voice timbre selector.
  - Auto-speak responses toggle.
- **Video Studio Image-to-Video Animation**:
  - Reference keyframe image input (`#vid-studio-image-url`) and direct file upload button (`#vid-ref-file-input`).
  - Async Image-to-Video synthesis animating camera pans and zooms from the provided reference image.
  - Dual-codec browser player support providing both `<source src="...mp4">` and `<source src="...webm">` for universal HTML5 playback compatibility.
- **3D Robot Assistant Enhancements**:
  - Realistic `speaking` animation state with jaw/mouth amplitude oscillation, subtle head nodding, and chest arc reactor light pulsation synchronized with text-to-speech output.
- **Automated Verification**:
  - `tests/test_document_intelligence.py` covering all 6 document & RAG capabilities.
  - `tests/test_multimodal_features.py` covering multi-image batch generation, video synthesis, and downloads.
  - `tests/test_final_acceptance.py` running automated live Chromium/Edge E2E verification with screenshots.

### Changed
- Updated Gemini model catalog to recommend active models: `gemini-flash-lite-latest`, `gemini-3-flash-preview`, and `gemini-pro-latest`.
- Enhanced chat video generator handler to output dual MP4 and WebM sources inside the chat bubble.

### Protected
- Preserved existing Three.js robot geometries, materials, and lighting.
- Preserved dark glassmorphic UI layout and styling.
- Preserved conversation context and database persistence.

