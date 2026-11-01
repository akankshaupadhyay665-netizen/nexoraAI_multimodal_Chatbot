/**
 * NEXORA AI - Video Studio Controller
 * Supports Text-to-Video and Image-to-Video with Async Job Polling and MP4 Playback
 */

class NexoraVideoStudio {
    constructor() {
        this.promptInput = document.getElementById("vid-studio-prompt");
        this.styleSelect = document.getElementById("vid-studio-style");
        this.ratioSelect = document.getElementById("vid-studio-ratio");
        this.durationSelect = document.getElementById("vid-studio-duration");
        this.generateBtn = document.getElementById("vid-studio-generate-btn");
        this.jobStatusContainer = document.getElementById("vid-studio-job-status");
        this.progressBar = document.getElementById("vid-job-progress-bar");
        this.progressText = document.getElementById("vid-job-progress-text");
        this.statusBadge = document.getElementById("vid-job-status-badge");
        this.resultsGrid = document.getElementById("vid-studio-results-grid");
        this.playerContainer = document.getElementById("vid-studio-player-container");
        this.refFileInput = document.getElementById("vid-ref-file-input");
        this.refImageUrlInput = document.getElementById("vid-studio-image-url");
        this.refPreviewContainer = document.getElementById("vid-ref-preview");
        this.refPreviewImg = document.getElementById("vid-ref-preview-img");
        this.refPreviewName = document.getElementById("vid-ref-preview-name");
        this.refClearBtn = document.getElementById("vid-ref-clear-btn");

        this.activeJobId = null;
        this.pollInterval = null;

        this.init();
    }

    init() {
        if (this.generateBtn) {
            this.generateBtn.addEventListener("click", () => this.handleGenerate());
        }

        if (this.refFileInput) {
            this.refFileInput.addEventListener("change", (e) => this.handleRefImageUpload(e));
        }

        if (this.refClearBtn) {
            this.refClearBtn.addEventListener("click", () => this.clearRefImage());
        }

        this.loadRecentVideos();
    }

    async handleRefImageUpload(e) {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            if (window.nexoraApp) window.nexoraApp.showToast("Uploading reference keyframe image...", "info");
            const res = await fetch("http://127.0.0.1:8000/api/files/upload", {
                method: "POST",
                body: formData
            });

            if (!res.ok) throw new Error("Reference image upload failed");
            const data = await res.json();

            const fileUrl = data.file_url.startsWith("http") ? data.file_url : `http://127.0.0.1:8000${data.file_url}`;
            if (this.refImageUrlInput) this.refImageUrlInput.value = fileUrl;
            if (this.refPreviewImg) this.refPreviewImg.src = fileUrl;
            if (this.refPreviewName) this.refPreviewName.textContent = data.filename || file.name;
            if (this.refPreviewContainer) this.refPreviewContainer.style.display = "flex";

            if (window.nexoraApp) window.nexoraApp.showToast("Reference keyframe ready for Image-to-Video synthesis!", "success");
        } catch (err) {
            console.error("Ref image upload error:", err);
            if (window.nexoraApp) window.nexoraApp.showToast(`Upload failed: ${err.message}`, "error");
        }
    }

    clearRefImage() {
        if (this.refFileInput) this.refFileInput.value = "";
        if (this.refImageUrlInput) this.refImageUrlInput.value = "";
        if (this.refPreviewContainer) this.refPreviewContainer.style.display = "none";
        if (this.refPreviewImg) this.refPreviewImg.src = "";
        if (this.refPreviewName) this.refPreviewName.textContent = "";
    }

    async loadRecentVideos() {
        if (!this.resultsGrid) return;
        try {
            const res = await fetch("http://127.0.0.1:8000/api/media?media_type=video");
            if (!res.ok) return;
            const items = await res.json();
            this.resultsGrid.innerHTML = "";
            items.forEach(item => {
                if (item.media_type && item.media_type !== "video") return;
                const fullVideoUrl = item.file_url.startsWith("http")
                    ? item.file_url
                    : `http://127.0.0.1:8000${item.file_url}`;
                if (!fullVideoUrl.endsWith(".webm") && !fullVideoUrl.endsWith(".mp4")) return;
                const card = document.createElement("div");
                card.className = "video-result-card animate-in";
                const isWebm = fullVideoUrl.endsWith(".webm");
                const mp4Url = fullVideoUrl.endsWith(".webm") ? fullVideoUrl.replace(/\.webm$/, ".mp4") : fullVideoUrl;
                const webmUrl = fullVideoUrl.endsWith(".mp4") ? fullVideoUrl.replace(/\.mp4$/, ".webm") : fullVideoUrl;
                const ext = isWebm ? "webm" : "mp4";
                card.innerHTML = `
                    <div class="video-wrapper">
                        <video controls autoplay loop muted playsinline style="width: 100%; border-radius: var(--radius-md); background: #000;">
                            <source src="${mp4Url}" type="video/mp4">
                            <source src="${webmUrl}" type="video/webm">
                            Your browser does not support HTML5 video.
                        </video>
                    </div>
                    <div class="video-info">
                        <p class="vid-prompt-text">${item.prompt}</p>
                        <div class="vid-actions-row">
                            <span class="vid-badge">${isWebm ? 'HD Video (WebM)' : 'MP4 Video'}</span>
                            <button type="button" class="btn btn-sm btn-primary" onclick="window.downloadMediaFile('${fullVideoUrl}', 'nexora_video_${item.id.slice(0, 8)}.${ext}')">⬇️ Download Video</button>
                        </div>
                    </div>
                `;
                this.resultsGrid.appendChild(card);
            });
        } catch (e) {
            console.warn("Could not load recent videos:", e);
        }
    }

    async handleGenerate() {
        const prompt = this.promptInput ? this.promptInput.value.trim() : "";
        if (!prompt) {
            if (window.nexoraApp) window.nexoraApp.showToast("Please enter a video prompt description.", "warning");
            return;
        }

        const style = this.styleSelect ? this.styleSelect.value : "cinematic";
        const aspect_ratio = this.ratioSelect ? this.ratioSelect.value : "16:9";
        const duration = this.durationSelect ? parseInt(this.durationSelect.value) : 5;
        const imageUrl = this.refImageUrlInput ? this.refImageUrlInput.value.trim() : null;

        this.setLoading(true);

        // Update 3D Robot
        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("processing", `Synthesizing ${duration}s cinematic video sequence...`);
        }

        try {
            const res = await fetch("http://127.0.0.1:8000/api/video/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: prompt,
                    style: style,
                    aspect_ratio: aspect_ratio,
                    duration: duration,
                    image_url: imageUrl || undefined
                })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Video job submission failed");
            }

            const data = await res.json();
            this.activeJobId = data.job_id;
            this.showJobStatus(data);
            this.startPolling(data.job_id);

            if (window.nexoraApp) {
                window.nexoraApp.showToast("Video job queued. Processing in background...", "info");
            }

        } catch (error) {
            console.error("Video submission error:", error);
            if (window.nexoraApp) {
                window.nexoraApp.showToast(`Error: ${error.message}`, "error");
            }
            this.setLoading(false);
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("idle");
            }
        }
    }

    startPolling(jobId) {
        if (this.pollInterval) clearInterval(this.pollInterval);

        this.pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`http://127.0.0.1:8000/api/video/jobs/${jobId}`);
                if (!res.ok) return;

                const job = await res.json();
                this.updateJobProgress(job);

                if (job.status === "completed") {
                    clearInterval(this.pollInterval);
                    this.pollInterval = null;
                    this.onJobCompleted(job);
                } else if (job.status === "failed") {
                    clearInterval(this.pollInterval);
                    this.pollInterval = null;
                    this.onJobFailed(job);
                }
            } catch (e) {
                console.warn("Polling error:", e);
            }
        }, 1500);
    }

    updateJobProgress(job) {
        if (this.progressBar) {
            this.progressBar.style.width = `${job.progress}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = `${job.progress}% - ${job.status.toUpperCase()}`;
        }
        if (this.statusBadge) {
            this.statusBadge.textContent = job.status.toUpperCase();
            this.statusBadge.className = `status-badge badge-${job.status}`;
        }
    }

    showJobStatus(job) {
        if (this.jobStatusContainer) {
            this.jobStatusContainer.style.display = "block";
        }
        this.updateJobProgress(job);
    }

    onJobCompleted(job) {
        this.setLoading(false);
        const fullVideoUrl = job.video_url.startsWith("http")
            ? job.video_url
            : `http://127.0.0.1:8000${job.video_url}`;

        // Render completed video card
        if (this.resultsGrid) {
            const card = document.createElement("div");
            card.className = "video-result-card animate-in";
            const isWebm = fullVideoUrl.endsWith(".webm");
            const mp4Url = fullVideoUrl.endsWith(".webm") ? fullVideoUrl.replace(/\.webm$/, ".mp4") : fullVideoUrl;
            const webmUrl = fullVideoUrl.endsWith(".mp4") ? fullVideoUrl.replace(/\.mp4$/, ".webm") : fullVideoUrl;
            const ext = isWebm ? "webm" : "mp4";
            card.innerHTML = `
                <div class="video-wrapper">
                    <video controls autoplay loop muted playsinline style="width: 100%; border-radius: var(--radius-md); background: #000;">
                        <source src="${mp4Url}" type="video/mp4">
                        <source src="${webmUrl}" type="video/webm">
                        Your browser does not support HTML5 video.
                    </video>
                </div>
                <div class="video-info">
                    <p class="vid-prompt-text">${job.prompt}</p>
                    <div class="vid-actions-row">
                        <span class="vid-badge">${isWebm ? 'HD Video (WebM)' : 'MP4 Video'}</span>
                        <button type="button" class="btn btn-sm btn-primary" onclick="window.downloadMediaFile('${fullVideoUrl}', 'nexora_video_${job.job_id.slice(0, 8)}.${ext}')">⬇️ Download Video</button>
                    </div>
                </div>
            `;
            this.resultsGrid.prepend(card);
        }

        if (window.nexoraApp) {
            window.nexoraApp.showToast("Video rendered successfully!", "success");
        }

        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("greeting", "Your cinematic video is ready!");
            setTimeout(() => window.nexoraRobotInstance.setState("idle"), 3000);
        }
    }

    onJobFailed(job) {
        this.setLoading(false);
        if (window.nexoraApp) {
            window.nexoraApp.showToast(`Video rendering failed: ${job.error_message || 'Unknown error'}`, "error");
        }
        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("idle");
        }
    }

    setLoading(loading) {
        if (this.generateBtn) {
            this.generateBtn.disabled = loading;
            this.generateBtn.innerHTML = loading
                ? `<span class="spinner"></span> Synthesizing Video...`
                : `<span>🎬 Generate Video</span>`;
        }
    }
}

window.NexoraVideoStudio = NexoraVideoStudio;

