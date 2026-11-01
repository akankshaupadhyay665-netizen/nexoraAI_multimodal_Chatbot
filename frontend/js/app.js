/**
 * NEXORA AI - Main Application Coordinator
 * Handles Navigation, Views, Sidebar, Conversations, Modals, Theme and Toasts
 */

class NexoraApp {
    constructor() {
        this.currentView = "chat-studio";
        this.isSidebarCollapsed = false;
        this.allConversations = [];

        this.initTheme();
        this.initNavigation();
        this.initFeatureCards();
        this.initModals();
        this.initHistorySearch();
        this.loadConversations();
        this.loadModelsInfo();
    }

    initTheme() {
        const savedTheme = localStorage.getItem("nexora_theme") || "dark";
        this.setTheme(savedTheme);

        const themeToggleBtn = document.getElementById("theme-toggle-btn");
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener("click", () => {
                const current = document.body.getAttribute("data-theme") || "dark";
                const nextTheme = current === "dark" ? "light" : "dark";
                this.setTheme(nextTheme);
            });
        }
    }

    setTheme(theme) {
        document.body.setAttribute("data-theme", theme);
        localStorage.setItem("nexora_theme", theme);

        const themeIcon = document.getElementById("theme-toggle-icon");
        if (themeIcon) {
            themeIcon.textContent = theme === "dark" ? "☀️" : "🌙";
        }
    }

    initNavigation() {
        // Sidebar toggle
        const toggleBtn = document.getElementById("sidebar-toggle-btn");
        const sidebar = document.getElementById("main-sidebar");
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener("click", () => {
                sidebar.classList.toggle("collapsed");
                this.isSidebarCollapsed = sidebar.classList.contains("collapsed");
                // Notify 3D Robot to resize smoothly
                if (window.nexoraRobotInstance) {
                    setTimeout(() => window.nexoraRobotInstance.onWindowResize(), 300);
                }
            });
        }

        // Nav Links
        const navLinks = document.querySelectorAll(".nav-link[data-view]");
        navLinks.forEach((link) => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                const view = link.getAttribute("data-view");
                this.switchView(view);
            });
        });

        // New Chat button
        const newChatBtn = document.getElementById("new-chat-btn");
        if (newChatBtn) {
            newChatBtn.addEventListener("click", () => this.startNewChat());
        }
    }

    switchView(viewName) {
        this.currentView = viewName;

        // Update active nav link
        document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
        const activeLink = document.querySelector(`.nav-link[data-view="${viewName}"]`);
        if (activeLink) activeLink.classList.add("active");

        // Hide all views
        document.querySelectorAll(".app-view").forEach((v) => v.style.display = "none");

        // Show target view with flex display
        const targetView = document.getElementById(`view-${viewName}`);
        if (targetView) {
            targetView.style.display = "flex";
        }

        // Load specific view data
        if (viewName === "media-gallery" && window.nexoraGallery) {
            window.nexoraGallery.loadMedia();
        } else if (viewName === "explore-models") {
            this.loadModelsInfo();
        } else if (viewName === "reports" && window.nexoraReports) {
            window.nexoraReports.loadReports();
        } else if (viewName === "video-studio" && window.nexoraVideoStudio) {
            window.nexoraVideoStudio.loadRecentVideos();
        } else if (viewName === "image-studio" && window.nexoraImageStudio) {
            window.nexoraImageStudio.loadRecentImages();
        }

        // Trigger 3D robot resize
        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.onWindowResize();
            if (viewName === "image-studio") {
                window.nexoraRobotInstance.setState("idle", "Welcome to Image Studio! Describe any image you can imagine.");
            } else if (viewName === "video-studio") {
                window.nexoraRobotInstance.setState("idle", "Video Studio active. Let's create cinematic AI motion.");
            } else if (viewName === "reports") {
                window.nexoraRobotInstance.setState("idle", "Analytics & Reports. Here is your live platform usage.");
            } else if (viewName === "chat-studio") {
                window.nexoraRobotInstance.setState("idle", "How can I help you today?");
            }
        }
    }

    initFeatureCards() {
        const featureCards = document.querySelectorAll(".feature-card");
        featureCards.forEach((card) => {
            card.addEventListener("click", () => {
                const action = card.getAttribute("data-action");
                this.handleFeatureCardAction(action);
            });
        });
    }

    handleFeatureCardAction(action) {
        this.switchView("chat-studio");
        const chatInput = document.getElementById("chat-input");

        switch (action) {
            case "ask-anything":
                if (chatInput) {
                    chatInput.value = "Explain the fundamental principles of quantum computing in simple terms.";
                    chatInput.focus();
                }
                break;
            case "analyze-image":
                const fileInputImg = document.getElementById("universal-file-input");
                if (fileInputImg) {
                    fileInputImg.setAttribute("accept", "image/*");
                    fileInputImg.click();
                }
                break;
            case "chat-pdf":
                const fileInputPdf = document.getElementById("universal-file-input");
                if (fileInputPdf) {
                    fileInputPdf.setAttribute("accept", ".pdf,.docx,.txt,.csv");
                    fileInputPdf.click();
                }
                break;
            case "generate-image":
                this.switchView("image-studio");
                break;
            case "create-video":
                this.switchView("video-studio");
                break;
            case "write-code":
                if (chatInput) {
                    chatInput.value = "Write a complete Python FastAPI backend with SQLite database and JWT authentication.";
                    chatInput.focus();
                }
                break;
            case "analyze-audio":
                const fileInputAud = document.getElementById("universal-file-input");
                if (fileInputAud) {
                    fileInputAud.setAttribute("accept", "audio/*");
                    fileInputAud.click();
                }
                break;
            case "summarize-documents":
                const fileInputDoc = document.getElementById("universal-file-input");
                if (fileInputDoc) {
                    fileInputDoc.setAttribute("accept", ".pdf,.docx,.txt");
                    fileInputDoc.click();
                }
                break;
            default:
                break;
        }
    }

    initHistorySearch() {
        const searchInput = document.getElementById("history-search-input");
        if (searchInput) {
            searchInput.addEventListener("input", (e) => {
                const q = e.target.value.toLowerCase().trim();
                this.filterConversationsList(q);
            });
        }
    }

    filterConversationsList(query) {
        const listContainer = document.getElementById("chat-history-list");
        if (!listContainer) return;

        const filtered = query
            ? this.allConversations.filter(c => c.title.toLowerCase().includes(query))
            : this.allConversations;

        this.renderConversations(filtered);
    }

    async loadConversations() {
        try {
            const res = await fetch("http://127.0.0.1:8000/api/conversations");
            if (!res.ok) return;

            this.allConversations = await res.json();
            const searchInput = document.getElementById("history-search-input");
            const q = searchInput ? searchInput.value.toLowerCase().trim() : "";
            this.filterConversationsList(q);

        } catch (e) {
            console.warn("Could not load conversations:", e);
        }
    }

    renderConversations(convs) {
        const listContainer = document.getElementById("chat-history-list");
        if (!listContainer) return;

        listContainer.innerHTML = "";

        if (convs.length === 0) {
            listContainer.innerHTML = `<div class="history-empty">No conversations found</div>`;
            return;
        }

        convs.forEach((c) => {
            const item = document.createElement("div");
            item.className = "history-item";
            if (window.nexoraChat && window.nexoraChat.currentConversationId === c.id) {
                item.classList.add("active");
            }

            item.innerHTML = `
                <span class="history-icon">💬</span>
                <span class="history-title" title="${c.title}">${c.title}</span>
                <div class="history-item-actions">
                    <button class="action-mini-btn rename-btn" title="Rename" onclick="event.stopPropagation(); window.nexoraApp.renameConversation('${c.id}', '${c.title.replace(/'/g, "\\'")}')">✏️</button>
                    <button class="action-mini-btn delete-btn" title="Delete" onclick="event.stopPropagation(); window.nexoraApp.deleteConversation('${c.id}')">🗑️</button>
                </div>
            `;

            item.addEventListener("click", () => this.selectConversation(c.id));
            listContainer.appendChild(item);
        });
    }

    async selectConversation(id) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/conversations/${id}`);
            if (!res.ok) return;

            const conv = await res.json();
            if (window.nexoraChat) {
                window.nexoraChat.clearMessages();
                window.nexoraChat.currentConversationId = conv.id;

                if (conv.messages && conv.messages.length > 0) {
                    if (window.nexoraChat.emptyState) {
                        window.nexoraChat.emptyState.style.display = "none";
                    }
                    conv.messages.forEach((m) => {
                        let attachments = [];
                        if (m.attachments) {
                            try { attachments = JSON.parse(m.attachments); } catch (e) {}
                        }
                        window.nexoraChat.appendMessage({
                            id: m.id,
                            role: m.role,
                            content: m.content,
                            attachments: attachments,
                            created_at: m.created_at
                        });
                    });
                }
            }

            this.switchView("chat-studio");
            this.loadConversations();
        } catch (e) {
            this.showToast("Failed to load conversation", "error");
        }
    }

    async startNewChat() {
        const modelToUse = (window.nexoraChat && window.nexoraChat.currentModel) || "gemini-2.5-flash";

        try {
            // Create a genuine new conversation in SQLite database
            const res = await fetch("http://127.0.0.1:8000/api/conversations", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: "New Conversation",
                    model_used: modelToUse
                })
            });

            if (res.ok) {
                const newConv = await res.json();
                if (window.nexoraChat) {
                    window.nexoraChat.clearMessages();
                    window.nexoraChat.currentConversationId = newConv.id;
                }
                this.showToast("Created new conversation", "info");
            }
        } catch (e) {
            console.warn("Offline new chat creation fallback:", e);
            if (window.nexoraChat) {
                window.nexoraChat.clearMessages();
                window.nexoraChat.currentConversationId = null;
            }
        }

        this.switchView("chat-studio");
        this.loadConversations();

        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("greeting", "New conversation started. What shall we explore?");
            setTimeout(() => window.nexoraRobotInstance.setState("idle"), 2500);
        }
    }

    async renameConversation(id, currentTitle) {
        const newTitle = prompt("Enter a new title for this conversation:", currentTitle);
        if (!newTitle || newTitle.trim() === "" || newTitle === currentTitle) return;

        try {
            const res = await fetch(`http://127.0.0.1:8000/api/conversations/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle.trim() })
            });

            if (res.ok) {
                this.showToast("Conversation renamed", "success");
                this.loadConversations();
            } else {
                throw new Error("Server rejected update");
            }
        } catch (e) {
            this.showToast("Rename failed: " + e.message, "error");
        }
    }

    async deleteConversation(id) {
        if (!confirm("Are you sure you want to delete this conversation?")) return;
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/conversations/${id}`, { method: "DELETE" });
            if (res.ok) {
                this.showToast("Conversation deleted", "info");
                if (window.nexoraChat && window.nexoraChat.currentConversationId === id) {
                    this.startNewChat();
                } else {
                    this.loadConversations();
                }
            }
        } catch (e) {
            this.showToast("Failed to delete conversation", "error");
        }
    }

    async clearAllHistory() {
        if (!confirm("Are you sure you want to delete ALL conversation history? This cannot be undone.")) return;
        try {
            const res = await fetch("http://127.0.0.1:8000/api/conversations", { method: "DELETE" });
            if (res.ok) {
                this.showToast("All conversations cleared", "info");
                this.startNewChat();
            }
        } catch (e) {
            this.showToast("Failed to clear history", "error");
        }
    }

    async loadModelsInfo() {
        const container = document.getElementById("models-grid-container");
        if (!container) return;

        try {
            const res = await fetch("http://127.0.0.1:8000/api/models");
            if (!res.ok) return;

            const models = await res.json();
            container.innerHTML = "";

            models.forEach((m) => {
                const card = document.createElement("div");
                card.className = "model-card animate-in";

                const capsHtml = m.capabilities.map((c) => `<span class="cap-tag">${c}</span>`).join("");
                const statusPill = m.is_configured
                    ? `<span class="badge badge-success">Configured / Ready</span>`
                    : `<span class="badge badge-warning">Needs API Key</span>`;

                card.innerHTML = `
                    <div class="model-header">
                        <div>
                            <span class="model-provider">${m.provider}</span>
                            <h3 class="model-name">${m.name}</h3>
                        </div>
                        ${statusPill}
                    </div>
                    <p class="model-desc">${m.description}</p>
                    <div class="model-caps-row">
                        ${capsHtml}
                    </div>
                `;

                container.appendChild(card);
            });
        } catch (e) {
            console.warn("Could not load models:", e);
        }
    }

    initModals() {
        // Settings modal triggers
        const settingsLink = document.getElementById("nav-settings-btn");
        const settingsModal = document.getElementById("settings-modal");
        const closeSettings = document.getElementById("close-settings-btn");
        const saveSettingsBtn = document.getElementById("save-settings-btn");
        const testConnBtn = document.getElementById("test-connection-btn");
        const resetSettingsBtn = document.getElementById("reset-settings-btn");

        if (settingsLink && settingsModal) {
            settingsLink.addEventListener("click", () => {
                settingsModal.classList.add("open");
                this.loadCurrentSettings();
            });
        }

        if (closeSettings && settingsModal) {
            closeSettings.addEventListener("click", () => settingsModal.classList.remove("open"));
        }

        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener("click", () => this.saveSettings());
        }

        if (testConnBtn) {
            testConnBtn.addEventListener("click", () => this.testGeminiConnection());
        }

        if (resetSettingsBtn) {
            resetSettingsBtn.addEventListener("click", () => {
                const g = document.getElementById("setting-gemini-key");
                const h = document.getElementById("setting-hf-key");
                if (g) g.value = "";
                if (h) h.value = "";
                this.showToast("Settings inputs reset", "info");
            });
        }

        // Help Modal triggers
        const helpLink = document.getElementById("nav-help-btn");
        const helpModal = document.getElementById("help-modal");
        const closeHelp = document.getElementById("close-help-btn");

        if (helpLink && helpModal) {
            helpLink.addEventListener("click", () => helpModal.classList.add("open"));
        }
        if (closeHelp && helpModal) {
            closeHelp.addEventListener("click", () => helpModal.classList.remove("open"));
        }

        // Close modals on clicking outside backdrop
        [settingsModal, helpModal].forEach((modal) => {
            if (modal) {
                modal.addEventListener("click", (e) => {
                    if (e.target === modal) modal.classList.remove("open");
                });
            }
        });

        // Close on Escape key press
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                document.querySelectorAll(".modal-backdrop.open").forEach(m => m.classList.remove("open"));
            }
        });

        // Clear history button in settings
        const clearHistoryBtn = document.getElementById("clear-all-history-btn");
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener("click", () => this.clearAllHistory());
        }
    }

    async loadCurrentSettings() {
        try {
            const res = await fetch("http://127.0.0.1:8000/api/settings");
            if (!res.ok) return;
            const data = await res.json();

            const geminiStatus = document.getElementById("gemini-status-indicator");
            if (geminiStatus) {
                geminiStatus.textContent = data.gemini_configured ? "Connected & Active" : "Not configured (Local Fallback Mode)";
                geminiStatus.className = data.gemini_configured ? "text-success" : "text-warning";
            }
        } catch (e) {}
    }

    async testGeminiConnection() {
        const testBtn = document.getElementById("test-connection-btn");
        if (testBtn) {
            testBtn.disabled = true;
            testBtn.textContent = "Testing...";
        }

        try {
            const res = await fetch("http://127.0.0.1:8000/api/settings/test-connection", { method: "POST" });
            const data = await res.json();

            if (data.success) {
                this.showToast(data.message, "success");
            } else {
                this.showToast(data.message, "warning");
            }
        } catch (e) {
            this.showToast("Test request failed: " + e.message, "error");
        } finally {
            if (testBtn) {
                testBtn.disabled = false;
                testBtn.textContent = "⚡ Test Connection";
            }
        }
    }

    async saveSettings() {
        const geminiInput = document.getElementById("setting-gemini-key");
        const hfInput = document.getElementById("setting-hf-key");

        const payload = {};
        if (geminiInput) payload.gemini_api_key = geminiInput.value.trim();
        if (hfInput) payload.huggingface_api_key = hfInput.value.trim();

        try {
            const res = await fetch("http://127.0.0.1:8000/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                this.showToast("Settings saved successfully!", "success");
                document.getElementById("settings-modal").classList.remove("open");
                this.loadModelsInfo();
                this.loadCurrentSettings();
            }
        } catch (e) {
            this.showToast("Error saving settings: " + e.message, "error");
        }
    }

    showToast(message, type = "info") {
        const container = document.getElementById("toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `toast toast-${type} animate-in`;
        toast.innerHTML = `
            <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
            <span class="toast-msg">${message}</span>
        `;

        container.appendChild(toast);
        setTimeout(() => {
            toast.classList.add("fade-out");
            setTimeout(() => toast.remove(), 400);
        }, 3500);
    }
}

/**
 * Universal Nexora AI Media Downloader
 * Downloads images, videos, and uploaded documents natively to the user's computer.
 * Circumvents browser cross-origin download blocking via same-origin Blob conversion.
 */
window.downloadMediaFile = async function(urlOrId, defaultName = "nexora_media_file") {
    if (window.event) {
        try {
            window.event.preventDefault();
            window.event.stopPropagation();
        } catch (e) {}
    }

    if (!urlOrId) {
        if (window.nexoraApp) window.nexoraApp.showToast("No file target specified for download.", "warning");
        return;
    }

    if (window.nexoraApp) {
        window.nexoraApp.showToast("Starting download...", "info");
    }

    try {
        let downloadEndpoint = urlOrId;
        const isUrl = urlOrId.startsWith("http://") || urlOrId.startsWith("https://") || urlOrId.startsWith("/");

        if (!isUrl) {
            // Assume it's a database ID or job ID
            downloadEndpoint = `http://127.0.0.1:8000/api/media/${encodeURIComponent(urlOrId)}/download`;
        } else if (urlOrId.includes("/storage/")) {
            // Extract filename from storage path
            const parts = urlOrId.split("/");
            const rawFilename = parts[parts.length - 1].split("?")[0];
            downloadEndpoint = `http://127.0.0.1:8000/api/media/download/file?filename=${encodeURIComponent(rawFilename)}`;
        } else if (!urlOrId.startsWith("http")) {
            downloadEndpoint = `http://127.0.0.1:8000${urlOrId}`;
        }

        // Fetch file data
        let res = await fetch(downloadEndpoint);
        if (!res.ok) {
            // Fallback attempt: if direct download endpoint 404'd, try direct storage file fetch
            if (isUrl) {
                const directUrl = urlOrId.startsWith("http") ? urlOrId : `http://127.0.0.1:8000${urlOrId}`;
                res = await fetch(directUrl);
            }
            if (!res.ok) {
                throw new Error(`Server returned HTTP ${res.status}`);
            }
        }

        // Determine filename
        let targetFilename = defaultName;
        const disposition = res.headers.get("content-disposition");
        if (disposition && disposition.includes("filename=")) {
            const match = disposition.match(/filename=["']?([^"';]+)["']?/i);
            if (match && match[1]) {
                targetFilename = match[1].trim();
            }
        } else if (isUrl) {
            const extracted = urlOrId.split("/").pop().split("?")[0];
            if (extracted && extracted.includes(".")) {
                targetFilename = extracted;
            }
        }

        // Create browser-native Blob and same-origin Object URL
        const blob = await res.blob();
        const objectUrl = window.URL.createObjectURL(blob);

        const tempLink = document.createElement("a");
        tempLink.style.display = "none";
        tempLink.href = objectUrl;
        tempLink.setAttribute("download", targetFilename);
        document.body.appendChild(tempLink);
        tempLink.click();

        setTimeout(() => {
            try {
                document.body.removeChild(tempLink);
                window.URL.revokeObjectURL(objectUrl);
            } catch (e) {}
        }, 3000);

        if (window.nexoraApp) {
            window.nexoraApp.showToast(`Saved to computer: ${targetFilename}`, "success");
        }
    } catch (err) {
        console.error("Error in downloadMediaFile:", err);
        // Fallback: try direct browser download trigger
        try {
            const fallbackLink = document.createElement("a");
            fallbackLink.style.display = "none";
            let fallbackUrl = urlOrId;
            if (urlOrId.includes("/storage/")) {
                const fname = urlOrId.split("/").pop().split("?")[0];
                fallbackUrl = `http://127.0.0.1:8000/api/media/download/file?filename=${encodeURIComponent(fname)}`;
            } else if (!urlOrId.startsWith("http") && !urlOrId.startsWith("/")) {
                fallbackUrl = `http://127.0.0.1:8000/api/media/${encodeURIComponent(urlOrId)}/download`;
            }
            fallbackLink.href = fallbackUrl;
            fallbackLink.setAttribute("download", defaultName);
            fallbackLink.setAttribute("target", "_blank");
            document.body.appendChild(fallbackLink);
            fallbackLink.click();
            setTimeout(() => document.body.removeChild(fallbackLink), 1500);
            if (window.nexoraApp) window.nexoraApp.showToast("Download triggered", "info");
        } catch (e2) {
            if (window.nexoraApp) window.nexoraApp.showToast(`Download failed: ${err.message}`, "error");
        }
    }
};

// Global Startup
window.addEventListener("DOMContentLoaded", () => {
    window.nexoraApp = new NexoraApp();
    window.nexoraChat = new NexoraChat();
    window.nexoraMultimodal = new NexoraMultimodal();
    window.nexoraVoice = new NexoraVoice();
    window.nexoraImageStudio = new NexoraImageStudio();
    window.nexoraVideoStudio = new NexoraVideoStudio();
    window.nexoraGallery = new NexoraGallery();
    window.nexoraReports = new NexoraReports();

    // Initialize 3D Robot
    if (window.initNexoraRobot) {
        window.initNexoraRobot("robot-canvas-container");
    }
    setTimeout(() => {
        if (!window.nexoraRobotInstance && window.initNexoraRobot) {
            window.initNexoraRobot("robot-canvas-container");
        } else if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.onWindowResize();
        }
    }, 250);
});
