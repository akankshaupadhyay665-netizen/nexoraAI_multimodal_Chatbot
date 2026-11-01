/**
 * NEXORA AI - Media Gallery Controller
 * Manages Generated Images, Generated Videos, and Uploaded Documents
 * Includes Interactive Preview Modal with Native Browser Downloads
 */

class NexoraGallery {
    constructor() {
        this.container = document.getElementById("gallery-items-grid");
        this.filterPills = document.querySelectorAll(".gallery-filter-pill");
        this.activeFilter = "all"; // 'all', 'image', 'video', 'document'
        this.itemsMap = new Map();

        this.init();
        this.initPreviewModal();
    }

    init() {
        this.filterPills.forEach((pill) => {
            pill.addEventListener("click", () => {
                this.filterPills.forEach((p) => p.classList.remove("active"));
                pill.classList.add("active");
                this.activeFilter = pill.getAttribute("data-filter") || "all";
                this.loadMedia();
            });
        });
    }

    initPreviewModal() {
        const modal = document.getElementById("media-preview-modal");
        const closeBtn = document.getElementById("close-preview-modal-btn");
        const closeAction = document.getElementById("preview-modal-close-action");

        if (closeBtn && modal) {
            closeBtn.addEventListener("click", () => modal.classList.remove("open"));
        }
        if (closeAction && modal) {
            closeAction.addEventListener("click", () => modal.classList.remove("open"));
        }
        if (modal) {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) modal.classList.remove("open");
            });
        }
    }

    openPreview(id) {
        const item = this.itemsMap.get(id);
        if (!item) return;

        const modal = document.getElementById("media-preview-modal");
        const titleEl = document.getElementById("preview-modal-title");
        const contentEl = document.getElementById("preview-modal-media-content");
        const metaEl = document.getElementById("preview-modal-meta");
        const downloadBtn = document.getElementById("preview-modal-download-btn");

        if (!modal || !contentEl) return;

        const safeTitle = item.title || "Nexora Media";
        if (titleEl) {
            titleEl.textContent = item.type === "video" ? "🎬 Video Preview" : (item.type === "image" ? "🖼️ Image Preview" : "📄 Document Preview");
        }

        if (item.type === "image") {
            contentEl.innerHTML = `<img src="${item.url}" alt="${safeTitle}" style="max-height: 500px; max-width: 100%; border-radius: var(--radius-md); object-fit: contain; box-shadow: 0 4px 20px rgba(0,0,0,0.6);" />`;
        } else if (item.type === "video") {
            const mp4Url = item.url.endsWith(".webm") ? item.url.replace(/\.webm$/, ".mp4") : item.url;
            const webmUrl = item.url.endsWith(".mp4") ? item.url.replace(/\.mp4$/, ".webm") : item.url;
            contentEl.innerHTML = `
                <video controls autoplay loop playsinline style="max-height: 500px; max-width: 100%; width: 100%; border-radius: var(--radius-md); background: #000; box-shadow: 0 4px 20px rgba(0,0,0,0.6);">
                    <source src="${mp4Url}" type="video/mp4">
                    <source src="${webmUrl}" type="video/webm">
                    Your browser does not support HTML5 video.
                </video>
            `;
        } else {
            contentEl.innerHTML = `
                <div style="padding: 40px; text-align: center;">
                    <span style="font-size: 3.5rem;">📄</span>
                    <h3 style="margin-top: 10px; color: var(--text-primary);">${safeTitle}</h3>
                </div>
            `;
        }

        const ext = item.type === "image" ? "png" : (item.type === "video" ? (item.url.endsWith(".webm") ? "webm" : "mp4") : "dat");
        const cleanName = `${safeTitle.replace(/[^a-zA-Z0-9_\-]/g, '_').slice(0, 32)}.${ext}`;

        if (metaEl) {
            metaEl.innerHTML = `
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                    <div><strong>Prompt / Title:</strong> ${safeTitle}</div>
                    <div><span class="badge badge-success">${item.provider}</span></div>
                </div>
                <div style="font-size: 0.8rem; color: var(--text-muted); display: flex; gap: 16px;">
                    <span><strong>Type:</strong> ${item.type.toUpperCase()}</span>
                    <span><strong>Created:</strong> ${new Date(item.created_at || Date.now()).toLocaleString()}</span>
                </div>
            `;
        }

        if (downloadBtn) {
            downloadBtn.onclick = () => {
                window.downloadMediaFile(item.url, cleanName);
            };
        }

        modal.classList.add("open");
    }

    async loadMedia() {
        if (!this.container) return;
        this.container.innerHTML = `<div class="gallery-loading"><span class="spinner"></span> Loading media assets...</div>`;
        this.itemsMap.clear();

        try {
            // Fetch generated media
            const mediaRes = await fetch("http://127.0.0.1:8000/api/media");
            const mediaItems = mediaRes.ok ? await mediaRes.json() : [];

            // Fetch uploaded files
            const filesRes = await fetch("http://127.0.0.1:8000/api/files");
            const uploadedFiles = filesRes.ok ? await filesRes.json() : [];

            let allItems = [];

            // Transform media items
            mediaItems.forEach((m) => {
                const item = {
                    id: m.id,
                    type: m.media_type,
                    url: m.file_url.startsWith("http") ? m.file_url : `http://127.0.0.1:8000${m.file_url}`,
                    title: m.prompt || m.filename,
                    style: m.style,
                    provider: m.provider,
                    created_at: m.created_at,
                    is_upload: false
                };
                allItems.push(item);
                this.itemsMap.set(item.id, item);
            });

            // Transform uploaded files
            uploadedFiles.forEach((f) => {
                const item = {
                    id: f.id,
                    type: f.file_type,
                    url: f.file_url.startsWith("http") ? f.file_url : `http://127.0.0.1:8000${f.file_url}`,
                    title: f.original_name,
                    style: f.mime_type,
                    provider: "User Upload",
                    created_at: new Date().toISOString(),
                    is_upload: true
                };
                allItems.push(item);
                this.itemsMap.set(item.id, item);
            });

            // Filter items
            if (this.activeFilter !== "all") {
                allItems = allItems.filter((i) => i.type === this.activeFilter);
            }

            if (allItems.length === 0) {
                this.container.innerHTML = `
                    <div class="gallery-empty-state">
                        <span class="empty-icon">📁</span>
                        <h3>No media assets found</h3>
                        <p>Generate images in the Image Studio, create videos, or upload documents to see them here.</p>
                    </div>
                `;
                return;
            }

            this.container.innerHTML = "";
            allItems.forEach((item) => {
                const card = document.createElement("div");
                card.className = "gallery-card animate-in";

                let mediaPreview = "";
                if (item.type === "image") {
                    mediaPreview = `<img src="${item.url}" alt="${item.title}" loading="lazy" style="cursor: pointer;" onclick="window.nexoraGallery.openPreview('${item.id}')" />`;
                } else if (item.type === "video") {
                    const mp4Url = item.url.endsWith(".webm") ? item.url.replace(/\.webm$/, ".mp4") : item.url;
                    const webmUrl = item.url.endsWith(".mp4") ? item.url.replace(/\.mp4$/, ".webm") : item.url;
                    mediaPreview = `
                        <video controls muted playsinline style="cursor: pointer; width: 100%; border-radius: var(--radius-sm); background: #000;">
                            <source src="${mp4Url}" type="video/mp4">
                            <source src="${webmUrl}" type="video/webm">
                        </video>
                    `;
                } else {
                    mediaPreview = `
                        <div class="doc-preview-box" style="cursor: pointer;" onclick="window.nexoraGallery.openPreview('${item.id}')">
                            <span class="doc-icon">📄</span>
                            <span class="doc-name">${item.title}</span>
                        </div>
                    `;
                }

                const formattedDate = item.created_at
                    ? new Date(item.created_at).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })
                    : "Just now";

                const safeTitle = (item.title || "artwork").replace(/"/g, "&quot;");
                const ext = item.type === 'image' ? 'png' : (item.type === 'video' ? (item.url.endsWith(".webm") ? "webm" : "mp4") : 'dat');
                const cleanName = `${(item.title || 'media').replace(/[^a-zA-Z0-9_\-]/g, '_').slice(0, 30)}.${ext}`;

                card.innerHTML = `
                    <div class="gallery-card-preview">
                        ${mediaPreview}
                    </div>
                    <div class="gallery-card-details">
                        <div class="gallery-tag-row">
                            <span class="gallery-type-tag">${item.type.toUpperCase()}</span>
                            <span class="gallery-provider-tag">${item.provider}</span>
                        </div>
                        <h4 class="gallery-item-title" title="${safeTitle}" style="cursor: pointer;" onclick="window.nexoraGallery.openPreview('${item.id}')">${safeTitle}</h4>
                        <div class="gallery-date-row" style="font-size: 0.74rem; color: var(--text-muted); margin: 3px 0 8px 0; display: flex; align-items: center; gap: 5px;">
                            <span>🕒</span> <span>${formattedDate}</span>
                        </div>
                        <div class="gallery-actions-bar">
                            <button type="button" class="btn-icon preview-btn" title="View Fullscreen & Details" onclick="window.nexoraGallery.openPreview('${item.id}')">👁️</button>
                            <button type="button" class="btn-icon download-btn" title="Download to Computer" onclick="window.downloadMediaFile('${item.url}', '${cleanName}')">⬇️</button>
                            <button type="button" class="btn-icon delete-btn" title="Delete" onclick="window.nexoraGallery.deleteItem('${item.id}', ${item.is_upload})">🗑️</button>
                        </div>
                    </div>
                `;

                this.container.appendChild(card);
            });

        } catch (error) {
            console.error("Gallery load error:", error);
            this.container.innerHTML = `<div class="gallery-error">Failed to load media: ${error.message}</div>`;
        }
    }

    async deleteItem(id, isUpload) {
        if (!confirm("Are you sure you want to delete this item?")) return;

        const endpoint = isUpload
            ? `http://127.0.0.1:8000/api/files/${id}`
            : `http://127.0.0.1:8000/api/media/${id}`;

        try {
            const res = await fetch(endpoint, { method: "DELETE" });
            if (res.ok) {
                if (window.nexoraApp) window.nexoraApp.showToast("Item deleted", "info");
                this.loadMedia();
            }
        } catch (e) {
            alert("Delete failed: " + e.message);
        }
    }
}

window.NexoraGallery = NexoraGallery;
