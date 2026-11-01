/**
 * NEXORA AI - Multimodal Upload & Drag-and-Drop Controller
 */

class NexoraMultimodal {
    constructor() {
        this.fileInput = document.getElementById("universal-file-input");
        this.dropZone = document.getElementById("chat-input-wrapper");
        this.attachBtn = document.getElementById("attach-menu-btn");
        this.attachDropdown = document.getElementById("attach-dropdown");

        this.init();
    }

    init() {
        if (this.attachBtn && this.attachDropdown) {
            this.attachBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                this.attachDropdown.classList.toggle("open");
            });

            document.addEventListener("click", () => {
                this.attachDropdown.classList.remove("open");
            });
        }

        // Attach dropdown options
        const menuItems = document.querySelectorAll(".attach-menu-item");
        menuItems.forEach((item) => {
            item.addEventListener("click", (e) => {
                const acceptType = e.currentTarget.getAttribute("data-accept");
                if (this.fileInput) {
                    this.fileInput.setAttribute("accept", acceptType);
                    this.fileInput.click();
                }
            });
        });

        // File input change
        if (this.fileInput) {
            this.fileInput.addEventListener("change", async (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    const files = Array.from(e.target.files);
                    for (const f of files) {
                        await this.uploadFile(f);
                    }
                    this.fileInput.value = "";
                }
            });
        }

        // Drag and Drop
        if (this.dropZone) {
            ["dragenter", "dragover"].forEach((eventName) => {
                this.dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.dropZone.classList.add("drag-over");
                });
            });

            ["dragleave", "drop"].forEach((eventName) => {
                this.dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.dropZone.classList.remove("drag-over");
                });
            });

            this.dropZone.addEventListener("drop", async (e) => {
                const files = e.dataTransfer.files;
                if (files && files.length > 0) {
                    for (const f of Array.from(files)) {
                        await this.uploadFile(f);
                    }
                }
            });
        }
    }

    async uploadFile(file) {
        if (!file) return;

        // Feedback in robot state
        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("processing", `Analyzing file: ${file.name}`);
        }

        const formData = new FormData();
        formData.append("file", file);
        if (window.nexoraChat && window.nexoraChat.currentConversationId) {
            formData.append("conversation_id", window.nexoraChat.currentConversationId);
        }

        const toast = window.nexoraApp ? window.nexoraApp.showToast(`Uploading ${file.name}...`, "info") : null;

        try {
            const res = await fetch("http://127.0.0.1:8000/api/files/upload", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Upload failed");
            }

            const data = await res.json();
            
            // Add to chat staged attachments
            if (window.nexoraChat) {
                window.nexoraChat.addStagedAttachment({
                    id: data.id,
                    name: data.original_name,
                    type: data.file_type,
                    url: data.file_url,
                    extracted_text: data.extracted_text
                });
            }

            if (window.nexoraApp) {
                window.nexoraApp.showToast(`Loaded ${data.original_name}`, "success");
            }

            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("idle", `Ready with ${data.original_name}. What would you like to know?`);
            }

        } catch (error) {
            if (window.nexoraApp) {
                window.nexoraApp.showToast(`Upload error: ${error.message}`, "error");
            }
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("idle");
            }
        } finally {
            if (this.fileInput) this.fileInput.value = "";
        }
    }
}

window.NexoraMultimodal = NexoraMultimodal;

