# NEXORA AI

> **"One Intelligence. Infinite Possibilities."**

Nexora AI is a commercial-grade, multi-model generative AI platform designed for local Windows execution. Featuring a modern dark-themed glassmorphic UI, an interactive real-time 3D WebGL humanoid robot assistant, persistent SQLite database, and FastAPI backend, Nexora AI unifies conversational reasoning, multi-image computer vision, document intelligence with RAG semantic search, batch image generation, cinematic video synthesis (text-to-video & image-to-video), audio transcription, and two-way voice communication into a single cohesive application.

---

## 🌟 Key Features

### 1. Interactive 3D Humanoid Robot Assistant (Three.js WebGL)
- Mounted prominently on the right side of the interface (~38% viewport width).
- PBR metallic armor, glowing cyan/purple LED ocular visor, and pulsating chest arc reactor.
- **6 Dynamic States**:
  - `idle`: Gentle floating levitation and breathing mesh animation.
  - `thinking`: Contemplative head tilt, magenta ocular glow, and orbiting data rings.
  - `listening`: Forward posture, electric cyan pulse, and audio waveform indicator.
  - `speaking`: Rhythmic jaw amplitude oscillation, head nodding, and chest arc reactor pulsation synchronized with speech synthesis.
  - `greeting`: Welcoming right-hand waving gesture and visor blink.
  - `processing`: High-speed dual holographic neon energy rings.
- **Interactive Parallax**: Head and torso track mouse cursor movement smoothly across the screen.

### 2. Document Intelligence & RAG Knowledge Base
- **Multi-Format Ingestion**: Ingests PDF, Word DOCX, CSV, and plain text/code files.
- **PDF Page-Wise Extraction**: Preserves exact page delimiters (`--- [Page X] ---`) for precise source citation.
- **Scanned PDF Detection**: Identifies image-only or low-text PDFs (`< 25 chars/page`) and recommends OCR.
- **DOCX Parsing with Tables**: Converts Word headings and XML tables into structured Markdown tables.
- **CSV Data Analytics**: Computes column schemas, null values, numerical metrics (min, mean, max), and renders a 10-row preview grid.
- **Document Comparison**: Automated structural comparison and Jaccard vocabulary overlap analysis between two documents.
- **RAG Vector Search**: In-memory dense continuous vector embedding using character 3-gram and word frequency hashing. Features hybrid cosine similarity with exact keyword boost.
- **Prompt Injection Defense**: Retrieved knowledge chunks are isolated inside strict `<source_document>` XML boundaries with explicit citations.

### 3. Advanced Vision & Image Understanding
- Multi-image drag-and-drop and attachment staging.
- Native binary image transmission (`types.Part.from_bytes`) to Gemini Vision models for high-resolution scene analysis, OCR, and diagram comprehension.

### 4. AI Image Studio
- Text-to-image synthesis powered by **Flux.1**.
- **Multi-Image Batch Variations**: Generate 1, 2, 3, or 4 distinct image variations simultaneously.
- 10 curated style presets (Photorealistic, Cinematic, Anime, 3D Octane, Studio Photography, etc.) and aspect ratio presets (1:1, 16:9, 9:16, 4:3).
- Direct browser downloads via dedicated backend endpoints (`/api/media/{id}/download`).

### 5. AI Video Studio
- **Text-to-Video & Image-to-Video**: Synthesizes animated cinematic camera pans, zooms, and atmospheric motion.
- **Reference Image Keyframe Input**: Upload or paste an image URL to animate directly from an existing visual.
- **Asynchronous Job Pipeline**: Real-time progress bar tracking (0% → 100%) and status polling.
- **Dual-Codec Video Playback**: Generates both H.264 MP4 and WebM VP8 with dual `<source>` tags for universal HTML5 browser playback.

### 6. Voice Assistant & Audio Understanding
- Ingestion and transcription of audio files (WAV, MP3, M4A, WEBM, OGG) with executive summary and key topic extraction.
- In-browser speech synthesis with persistent Voice Volume slider (`#setting-voice-volume`), Playback rate selector, and Voice Timbre selection.
- Speech playback synchronized with the 3D robot's speaking animation.

### 7. Generated Media Gallery & Persistent Database
- Relational schema via SQLAlchemy: Conversations, Messages, Uploaded Files, Generated Media, and Video Jobs persist across sessions in `nexora.db`.
- Interactive preview modal with full-resolution display and instant local downloads.

### 8. YouTube, Web Media & Interactive Video Playback Intelligence
- **YouTube Video Integration**: Official responsive YouTube IFrame Player embed (`enablejsapi=1`), extracting title, creator, thumbnail, and timed caption transcripts via `youtube-transcript-api`.
- **Interactive Timestamp Navigation**: Clickable timestamp markers (e.g. `[01:45]` or `⏱️ 00:52`) in conversation that dynamically seek and play the embedded YouTube player or native HTML5 video player to exact scenes.
- **Universal Video Playback**: Supports direct `.mp4`, `.webm`, `.m3u8` HLS live streams (via Hls.js), and Vimeo embeds with full responsive controls.
- **Open Graph Webpage Previews**: Automatically extracts rich Open Graph cards (title, summary description, social card image, and high-res favicon) with text scraping for question-answering.
- **Enterprise SSRF Security**: Automatic IP validation blocks loopback (`127.0.0.0/8`, `localhost`), private LAN (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), and cloud metadata IP ranges (`169.254.169.254`).

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Vanilla JavaScript (ES6+), HTML5, CSS3 Glassmorphism, Three.js (WebGL), Hls.js, Marked.js, Highlight.js |
| **Backend** | Python 3.14+, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic, HTTPX, BeautifulSoup4, youtube-transcript-api |
| **AI / Multimodal** | Google Gemini (`google-genai` SDK), Flux.1, Nexora Motion Engine (FFmpeg AVC/VP8) |
| **Document AI** | PyPDF, python-docx, pandas, NumPy |
| **Computer Vision** | OpenCV (`opencv-python`), Pillow, imageio-ffmpeg |
| **Testing** | Playwright (Chromium / Edge), Requests, Pytest |

---

## 🚀 Quick Start Guide

### 1. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Add your free Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Launch Nexora AI
Start both the backend and frontend services:

**Terminal 1 (Backend API):**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 (Frontend Client):**
```bash
python serve_frontend.py
```

Open your browser and navigate to:
- **Frontend App**: `http://127.0.0.1:5500`
- **Interactive API Documentation (Swagger)**: `http://127.0.0.1:8000/docs`

---

## 🧪 Running Automated Tests

Nexora AI includes a comprehensive 3-tier automated test suite:

### Tier 1: Document Intelligence & RAG Tests
```bash
python -m tests.test_document_intelligence
```
*Validates PDF page extraction, CSV pandas analytics, document comparison, RAG chunking, vector embeddings, and prompt-injection safety containers.*

### Tier 2: Multimodal Integration Tests
```bash
python -m tests.test_multimodal_features
```
*Validates backend health, model catalog, multi-image batch generation, video studio async jobs, and binary downloads.*

### Tier 3: Browser E2E Acceptance Tests (Playwright)
```bash
python -m tests.test_final_acceptance
```
*Launches an automated browser session validating the 3D robot, Image Studio batch selector, Video Studio image-to-video input, voice sliders, and live chat.*

---

## 📄 Documentation Reports

- [`IMPLEMENTATION_REPORT.md`](file:///c:/Users/Hp/OneDrive/Desktop/chatbot/IMPLEMENTATION_REPORT.md): Complete engineering report of all multimodal features.
- [`FEATURE_AUDIT_REPORT.md`](file:///c:/Users/Hp/OneDrive/Desktop/chatbot/FEATURE_AUDIT_REPORT.md): Matrix of all protected and enhanced components.
- [`DOCUMENT_INTELLIGENCE_REPORT.md`](file:///c:/Users/Hp/OneDrive/Desktop/chatbot/DOCUMENT_INTELLIGENCE_REPORT.md): Architectural report on document extraction and RAG.
- [`TEST_REPORT.md`](file:///c:/Users/Hp/OneDrive/Desktop/chatbot/TEST_REPORT.md): Automated verification logs and test outcomes.
- [`CHANGELOG.md`](file:///c:/Users/Hp/OneDrive/Desktop/chatbot/CHANGELOG.md): Detailed release notes for v2.5 Multimodal Master.
