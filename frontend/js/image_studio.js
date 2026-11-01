/**
 * NEXORA AI - Image Studio Controller
 * Supports Text-to-Image (Flux.1), Preset Styles, Aspect Ratios, Batch Multi-Image Generation,
 * Regenerate Flow with Parameter Tuning, and Fullscreen Zoomable Image Preview
 */

class NexoraImageStudio {
    constructor() {
        this.promptInput = document.getElementById("img-studio-prompt");
        this.negativeInput = document.getElementById("img-studio-negative");
        this.generateBtn = document.getElementById("img-studio-generate-btn");
        this.styleCards = document.querySelectorAll(".style-option-card");
        this.ratioPills = document.querySelectorAll(".ratio-pill:not(.img-qty-pill)");
        this.quantityPills = document.querySelectorAll(".img-qty-pill");
        this.galleryContainer = document.getElementById("img-studio-results-grid");
        this.loadingOverlay = document.getElementById("img-studio-loading");
        
        this.selectedStyle = "photorealistic";
        this.selectedRatio = "1:1";
        this.selectedQuantity = 1;
        this.isGenerating = false;
        this.imagesHistory = [];

        this.init();
    }

    init() {
        // Style selection
        this.styleCards.forEach((card) => {
            card.addEventListener("click", () => {
                this.styleCards.forEach((c) => c.classList.remove("active"));
                card.classList.add("active");
                this.selectedStyle = card.getAttribute("data-style") || "photorealistic";
            });
        });

        // Aspect ratio selection
        this.ratioPills.forEach((pill) => {
            pill.addEventListener("click", () => {
                this.ratioPills.forEach((p) => p.classList.remove("active"));
                pill.classList.add("active");
                this.selectedRatio = pill.getAttribute("data-ratio") || "1:1";
            });
        });

        // Quantity selection
        this.quantityPills.forEach((pill) => {
            pill.addEventListener("click", () => {
                this.quantityPills.forEach((p) => p.classList.remove("active"));
                pill.classList.add("active");
                this.selectedQuantity = parseInt(pill.getAttribute("data-qty") || "1");
            });
        });

        // Generate button
        if (this.generateBtn) {
            this.generateBtn.addEventListener("click", () => this.handleGenerate());
        }

        // Enter key in prompt input
        if (this.promptInput) {
            this.promptInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this.handleGenerate();
                }
            });
        }

        this.loadRecentImages();
    }

    async loadRecentImages() {
        if (!this.galleryContainer) return;
        try {
            const res = await fetch("http://127.0.0.1:8000/api/media?media_type=image");
            if (!res.ok) return;
            const items = await res.json();
            this.galleryContainer.innerHTML = "";
            this.imagesHistory = [];
            items.forEach(data => {
                if (data.media_type && data.media_type !== "image") return;
                this.appendGeneratedImage({
                    ...data,
                    image_url: data.file_url
                });
            });
        } catch (e) {
            console.warn("Could not load recent images:", e);
        }
    }

    async handleGenerate() {
        if (this.isGenerating) return;
        const prompt = this.promptInput ? this.promptInput.value.trim() : "";
        if (!prompt) {
            if (window.nexoraApp) window.nexoraApp.showToast("Please enter an image description prompt.", "warning");
            return;
        }

        const negativePrompt = this.negativeInput ? this.negativeInput.value.trim() : null;

        this.isGenerating = true;
        this.setLoading(true);

        // Update 3D Robot to processing state
        if (window.nexoraRobotInstance) {
            const qtyText = this.selectedQuantity > 1 ? `${this.selectedQuantity} variations of` : "";
            window.nexoraRobotInstance.setState("processing", `Synthesizing ${qtyText} ${this.selectedStyle} image...`);
        }

        try {
            const endpoint = this.selectedQuantity > 1 
                ? "http://127.0.0.1:8000/api/image/generate-batch" 
                : "http://127.0.0.1:8000/api/image/generate";

            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: prompt,
                    style: this.selectedStyle,
                    aspect_ratio: this.selectedRatio,
                    quantity: this.selectedQuantity,
                    negative_prompt: negativePrompt
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Server responded with ${res.status}`);
            }

            const data = await res.json();
            if (Array.isArray(data)) {
                data.forEach(item => this.appendGeneratedImage(item));
            } else {
                this.appendGeneratedImage(data);
            }

            if (window.nexoraApp) {
                const successMsg = this.selectedQuantity > 1 
                    ? `Generated ${data.length} artwork variations!` 
                    : "Image generated successfully!";
                window.nexoraApp.showToast(successMsg, "success");
            }

            // Robot celebrates completed generation
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("greeting", "Your artwork has been generated!");
                setTimeout(() => window.nexoraRobotInstance.setState("idle"), 3000);
            }

        } catch (error) {
            console.error("Image generation error:", error);
            if (window.nexoraApp) {
                window.nexoraApp.showToast(`Generation failed: ${error.message}`, "error");
            }
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("idle");
            }
        } finally {
            this.isGenerating = false;
            this.setLoading(false);
        }
    }

    setLoading(loading) {
        if (this.generateBtn) {
            this.generateBtn.disabled = loading;
            this.generateBtn.innerHTML = loading
                ? `<span class="spinner"></span> Synthesizing ${this.selectedQuantity > 1 ? this.selectedQuantity + ' Artworks' : 'Art'}...`
                : `<span>✨ Generate Artwork</span>`;
        }
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = loading ? "flex" : "none";
        }
    }

    appendGeneratedImage(data) {
        if (!this.galleryContainer) return;

        const card = document.createElement("div");
        card.className = "image-card animate-in";

        const fullImageUrl = data.image_url.startsWith("http")
            ? data.image_url
            : `http://127.0.0.1:8000${data.image_url}`;

        this.imagesHistory.unshift({
            id: data.id,
            url: fullImageUrl,
            prompt: data.prompt,
            style: data.style,
            aspect_ratio: data.aspect_ratio
        });

        const safePrompt = (data.prompt || 'nexora_artwork').replace(/'/g, "\\'").replace(/"/g, '&quot;');

        card.innerHTML = `
            <div class="image-wrapper">
                <img src="${fullImageUrl}" alt="${safePrompt}" loading="lazy" style="cursor: pointer;" onclick="window.nexoraImageStudio.previewImage('${fullImageUrl}', '${safePrompt}')" />
                <div class="image-overlay-actions">
                    <button type="button" class="overlay-btn download-btn" title="Download Artwork" onclick="window.downloadMediaFile('${fullImageUrl}', '${safePrompt.slice(0, 30)}.png')">⬇️</button>
                    <button type="button" class="overlay-btn regen-btn" title="Regenerate with modifications" onclick="window.nexoraImageStudio.regenerateImage('${safePrompt}', '${data.style}', '${data.aspect_ratio}')">🔄</button>
                    <button type="button" class="overlay-btn reuse-btn" title="Send to Chat" onclick="window.nexoraImageStudio.sendToChat('${fullImageUrl}', '${safePrompt}')">💬</button>
                    <button type="button" class="overlay-btn copy-btn" title="Copy Prompt" onclick="window.nexoraImageStudio.copyPrompt('${safePrompt}')">📋</button>
                </div>
            </div>
            <div class="image-card-info">
                <p class="img-prompt-text" title="${safePrompt}">${safePrompt}</p>
                <div class="img-meta-row">
                    <span class="img-style-tag">${data.style}</span>
                    <span class="img-ratio-tag">${data.aspect_ratio}</span>
                </div>
            </div>
        `;

        this.galleryContainer.prepend(card);
    }

    previewImage(imageUrl, prompt) {
        if (window.nexoraGallery && typeof window.nexoraGallery.openPreview === "function") {
            // Find existing id or create ad-hoc preview
            const match = this.imagesHistory.find(i => i.url === imageUrl);
            if (match && match.id && window.nexoraGallery.itemsMap.has(match.id)) {
                window.nexoraGallery.openPreview(match.id);
                return;
            }
        }
        window.open(imageUrl, "_blank");
    }

    sendToChat(imageUrl, prompt) {
        if (window.nexoraApp) {
            window.nexoraApp.switchView("chat-studio");
        }
        if (window.nexoraChat) {
            window.nexoraChat.addStagedAttachment({
                name: "generated_image.png",
                type: "image",
                url: imageUrl
            });
            const chatInput = document.getElementById("chat-input");
            if (chatInput) {
                chatInput.value = `Analyze and describe this generated image: "${prompt}"`;
                chatInput.focus();
            }
        }
    }

    regenerateImage(prompt, style, ratio) {
        if (this.promptInput) {
            this.promptInput.value = prompt;
            this.promptInput.focus();
        }
        this.selectedStyle = style || "photorealistic";
        this.selectedRatio = ratio || "1:1";

        // Update active UI pills
        this.styleCards.forEach(c => {
            if (c.getAttribute("data-style") === this.selectedStyle) c.classList.add("active");
            else c.classList.remove("active");
        });
        this.ratioPills.forEach(p => {
            if (p.getAttribute("data-ratio") === this.selectedRatio) p.classList.add("active");
            else p.classList.remove("active");
        });

        if (window.nexoraApp) {
            window.nexoraApp.showToast("Parameters loaded for regeneration. Adjust or click Generate.", "info");
        }
    }

    copyPrompt(prompt) {
        navigator.clipboard.writeText(prompt);
        if (window.nexoraApp) {
            window.nexoraApp.showToast("Prompt copied to clipboard!", "info");
        }
    }
}

window.NexoraImageStudio = NexoraImageStudio;
