/**
 * NEXORA AI - Chat System & Conversational Stream Engine
 */

/**
 * Global Video Timestamp Seeking Engine
 * Supports YouTube IFrame API PostMessage and HTML5 Video currentTime
 */
window.seekAnyVideo = function(timeStr) {
    if (!timeStr) return;
    const parts = timeStr.split(":").map(Number);
    let seconds = 0;
    if (parts.length === 2) {
        seconds = parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
        seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
    }

    // 1. Seek YouTube iframes via official postMessage API
    const ytIframes = document.querySelectorAll("iframe[src*='youtube']");
    if (ytIframes.length > 0) {
        ytIframes.forEach(iframe => {
            if (iframe.contentWindow) {
                iframe.contentWindow.postMessage(JSON.stringify({
                    event: 'command',
                    func: 'seekTo',
                    args: [seconds, true]
                }), '*');
                iframe.contentWindow.postMessage(JSON.stringify({
                    event: 'command',
                    func: 'playVideo',
                    args: []
                }), '*');
            }
        });
        if (window.nexoraApp) window.nexoraApp.showToast(`Jumped YouTube video to ${timeStr}`, "info");
        return;
    }

    // 2. Seek standard HTML5 video elements
    const videos = document.querySelectorAll("video");
    if (videos.length > 0) {
        const lastVid = videos[videos.length - 1];
        lastVid.currentTime = seconds;
        lastVid.play().catch(() => {});
        if (window.nexoraApp) window.nexoraApp.showToast(`Jumped video to ${timeStr}`, "info");
    }
};

class NexoraChat {
    constructor() {
        this.currentConversationId = null;
        this.currentModel = "gemini-flash-lite-latest";
        this.isGenerating = false;
        this.abortController = null;
        this.stagedAttachments = [];

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.messagesContainer = document.getElementById("chat-messages");
        this.chatInput = document.getElementById("chat-input");
        this.sendBtn = document.getElementById("send-btn");
        this.stopBtn = document.getElementById("stop-btn");
        this.modelSelector = document.getElementById("model-selector");
        this.emptyState = document.getElementById("empty-chat-state");
        this.attachmentPreviewBar = document.getElementById("attachment-preview-bar");
    }

    bindEvents() {
        if (this.sendBtn) {
            this.sendBtn.addEventListener("click", () => this.handleSendMessage());
        }

        if (this.stopBtn) {
            this.stopBtn.addEventListener("click", () => this.stopGeneration());
        }

        if (this.chatInput) {
            this.chatInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });

            // Auto-resize textarea
            this.chatInput.addEventListener("input", () => {
                this.chatInput.style.height = "auto";
                this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 180) + "px";
            });

            // Auto-detect pasted media and website URLs
            this.chatInput.addEventListener("paste", async (e) => {
                const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                if (pastedText && (pastedText.trim().startsWith("http://") || pastedText.trim().startsWith("https://"))) {
                    const cleanUrl = pastedText.trim();
                    try {
                        const res = await fetch("http://127.0.0.1:8000/api/media/url-info", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ url: cleanUrl })
                        });
                        if (res.ok) {
                            const info = await res.json();
                            if (info && info.success) {
                                this.addStagedAttachment({
                                    id: `url_${Date.now()}`,
                                    name: info.title || cleanUrl,
                                    type: info.type,
                                    url: cleanUrl,
                                    embed_url: info.embed_url,
                                    thumbnail: info.thumbnail_url || info.image,
                                    has_transcript: info.has_transcript,
                                    transcript_text: info.transcript_text,
                                    transcript_segments: info.transcript_segments
                                });
                                if (window.nexoraApp) {
                                    window.nexoraApp.showToast(`Loaded ${info.type.toUpperCase()}: ${info.title || cleanUrl}`, "info");
                                }
                            }
                        }
                    } catch (err) {
                        console.warn("URL auto-detection error:", err);
                    }
                }
            });
        }

        if (this.modelSelector) {
            this.modelSelector.addEventListener("change", (e) => {
                this.currentModel = e.target.value;
                const badge = document.getElementById("active-model-badge");
                if (badge) badge.textContent = e.target.options[e.target.selectedIndex].text;
            });
        }
    }

    async handleSendMessage(customPrompt = null, attachmentsOverride = null) {
        if (this.isGenerating) return;

        const text = customPrompt || (this.chatInput ? this.chatInput.value.trim() : "");
        const attachments = attachmentsOverride || [...this.stagedAttachments];

        if (!text && attachments.length === 0) return;

        // Reset input field and clear attachments
        if (this.chatInput && !customPrompt) {
            this.chatInput.value = "";
            this.chatInput.style.height = "auto";
        }
        this.clearStagedAttachments();

        // Hide empty welcome banner once chat starts
        if (this.emptyState) {
            this.emptyState.style.display = "none";
        }

        // Render user message bubble
        this.appendMessage({
            role: "user",
            content: text,
            attachments: attachments,
            created_at: new Date().toISOString()
        });

        // Set Robot state to thinking
        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("thinking");
        }

        // Toggle Buttons
        this.isGenerating = true;
        this.toggleButtons(true);

        // Pre-render assistant message bubble
        const assistantMsgEl = this.appendMessage({
            role: "assistant",
            content: "",
            status: "generating",
            created_at: new Date().toISOString()
        });

        const contentEl = assistantMsgEl.querySelector(".msg-content");
        contentEl.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;

        try {
            this.abortController = new AbortController();

            const res = await fetch("http://127.0.0.1:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    message: text,
                    model: this.currentModel,
                    attachments: attachments
                }),
                signal: this.abortController.signal
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Server responded with ${res.status}`);
            }

            const data = await res.json();
            this.currentConversationId = data.conversation_id;

            // Render Markdown response with syntax highlighting
            this.renderMessageContent(contentEl, data.assistant_message.content);

            // Handle attachments and action controls returned by assistant
            let attachmentsList = data.assistant_message.attachments;
            if (typeof attachmentsList === "string") {
                try { attachmentsList = JSON.parse(attachmentsList); } catch(e) { attachmentsList = []; }
            }
            attachmentsList = attachmentsList || [];

            const bubble = assistantMsgEl.querySelector(".chat-bubble");
            if (attachmentsList.length > 0 && bubble) {
                const existingAtt = bubble.querySelector(".msg-attachments-container");
                if (!existingAtt) {
                    const temp = document.createElement("div");
                    temp.innerHTML = this.buildAttachmentsHtml(attachmentsList);
                    if (temp.firstElementChild) {
                        bubble.insertBefore(temp.firstElementChild, contentEl);
                    }
                }
            }

            // Check for Video or Image in response
            const renderedVideos = contentEl.querySelectorAll("video");
            const renderedImgs = contentEl.querySelectorAll("img");
            
            const videoAtt = attachmentsList.find(a => a.type === "video");
            const imageAtt = attachmentsList.find(a => a.type === "image");

            let vidUrl = "";
            let vidName = "nexora_generated_video.mp4";
            if (videoAtt && videoAtt.url) {
                vidUrl = videoAtt.url.startsWith("http") ? videoAtt.url : "http://127.0.0.1:8000" + videoAtt.url;
                vidName = videoAtt.name || vidName;
            } else if (renderedVideos.length > 0) {
                vidUrl = renderedVideos[0].src;
            } else {
                for (const img of renderedImgs) {
                    const src = (img.src || "").toLowerCase();
                    if (src.endsWith(".mp4") || src.endsWith(".webm") || src.includes("/generated_videos/")) {
                        vidUrl = img.src;
                        vidName = "nexora_generated_video.mp4";
                        break;
                    }
                }
            }

            let imgUrl = "";
            let imgName = "nexora_generated_artwork.png";
            if (!vidUrl) {
                if (imageAtt && imageAtt.url) {
                    imgUrl = imageAtt.url.startsWith("http") ? imageAtt.url : "http://127.0.0.1:8000" + imageAtt.url;
                    imgName = imageAtt.name || imgName;
                } else if (renderedImgs.length > 0) {
                    imgUrl = renderedImgs[0].src;
                }
            }

            if (vidUrl) {
                let actionsContainer = bubble.querySelector(".generated-media-actions");
                if (!actionsContainer) {
                    actionsContainer = document.createElement("div");
                    actionsContainer.className = "generated-media-actions";
                    actionsContainer.style.cssText = "display: flex; gap: 8px; margin-top: 12px; margin-bottom: 8px; flex-wrap: wrap;";
                    actionsContainer.innerHTML = `
                        <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${vidUrl}', '${vidName}')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            📥 Download Video
                        </button>
                        <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            🔄 Regenerate
                        </button>
                        <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('video-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            🎬 Open in Video Studio
                        </button>
                    `;
                    const footer = bubble.querySelector(".msg-footer");
                    if (footer) {
                        bubble.insertBefore(actionsContainer, footer);
                    } else {
                        bubble.appendChild(actionsContainer);
                    }
                }
            } else if (imgUrl) {
                let actionsContainer = bubble.querySelector(".generated-media-actions");
                if (!actionsContainer) {
                    actionsContainer = document.createElement("div");
                    actionsContainer.className = "generated-media-actions";
                    actionsContainer.style.cssText = "display: flex; gap: 8px; margin-top: 12px; margin-bottom: 8px; flex-wrap: wrap;";
                    actionsContainer.innerHTML = `
                        <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${imgUrl}', '${imgName}')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            📥 Download Image
                        </button>
                        <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            🔄 Regenerate
                        </button>
                        <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('image-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            🎨 Open in Studio
                        </button>
                    `;
                    const footer = bubble.querySelector(".msg-footer");
                    if (footer) {
                        bubble.insertBefore(actionsContainer, footer);
                    } else {
                        bubble.appendChild(actionsContainer);
                    }
                }
            }

            // Update conversation list in sidebar
            if (window.nexoraApp) {
                window.nexoraApp.loadConversations();
            }

            // Set robot state to speaking or idle
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("speaking");
                setTimeout(() => {
                    if (window.nexoraRobotInstance.state === "speaking") {
                        window.nexoraRobotInstance.setState("idle");
                    }
                }, 3500);
            }

            // Speak response if voice auto-speak is enabled
            if (window.nexoraVoice && window.nexoraVoice.autoSpeak) {
                window.nexoraVoice.speak(data.assistant_message.content);
            }

        } catch (error) {
            if (error.name === "AbortError") {
                contentEl.innerHTML += `<p class="generation-stopped"><em>[Generation stopped by user]</em></p>`;
            } else {
                contentEl.innerHTML = `
                    <div class="msg-error">
                        <i class="icon-alert">⚠️</i>
                        <div>
                            <strong>Error generating response</strong>
                            <p>${error.message}</p>
                        </div>
                    </div>
                `;
            }
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("idle");
            }
        } finally {
            this.isGenerating = false;
            this.toggleButtons(false);
            this.scrollToBottom();
        }
    }

    stopGeneration() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.isGenerating = false;
        this.toggleButtons(false);
        if (window.nexoraRobotInstance) {
            window.nexoraRobotInstance.setState("idle");
        }
    }

    toggleButtons(generating) {
        if (this.sendBtn) this.sendBtn.style.display = generating ? "none" : "flex";
        if (this.stopBtn) this.stopBtn.style.display = generating ? "flex" : "none";
    }

    buildAttachmentsHtml(attachmentsList) {
        if (!attachmentsList || attachmentsList.length === 0) return "";
        let attachmentsHtml = `<div class="msg-attachments-container">`;
        for (const att of attachmentsList) {
            const fullUrl = att.url.startsWith("http") ? att.url : "http://127.0.0.1:8000" + att.url;
            if (att.type === "image") {
                attachmentsHtml += `
                    <div class="msg-attachment-item image-attachment">
                        <img src="${fullUrl}" alt="${att.name}" onclick="window.open(this.src, '_blank')" style="border-radius: var(--radius-md); max-width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.5); cursor: pointer;" />
                    </div>
                `;
            } else if (att.type === "youtube") {
                const videoId = att.video_id || "";
                const embedUrl = att.embed_url || `https://www.youtube-nocookie.com/embed/${videoId}?enablejsapi=1&rel=0`;
                attachmentsHtml += `
                    <div class="msg-attachment-item youtube-attachment-card" style="margin: 12px 0; max-width: 680px; width: 100%; border: 1px solid rgba(255,50,50,0.3); border-radius: var(--radius-md); overflow: hidden; background: rgba(20,20,25,0.7); box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; background: #000;">
                            <iframe 
                                id="yt-frame-${videoId}"
                                src="${embedUrl}" 
                                title="${att.name}" 
                                frameborder="0" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                allowfullscreen 
                                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;">
                            </iframe>
                        </div>
                        <div style="padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
                            <div>
                                <div style="font-weight: 600; font-size: 0.9rem; color: var(--text-primary);"><span style="color: #ff3333; margin-right: 4px;">▶</span> ${att.name}</div>
                                <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">${att.author || 'YouTube'} • ${att.has_transcript ? 'Captions Available (Click timestamps to seek)' : 'Web Stream'}</div>
                            </div>
                            <a href="${att.url}" target="_blank" rel="noopener noreferrer" class="btn-action-pill" style="text-decoration: none; font-size: 0.75rem; padding: 4px 10px; background: rgba(255,0,0,0.15); border: 1px solid rgba(255,0,0,0.4); color: #ff5555; border-radius: var(--radius-full); white-space: nowrap;">
                                Open on YouTube ↗
                            </a>
                        </div>
                    </div>
                `;
            } else if (att.type === "direct_video") {
                attachmentsHtml += `
                    <div class="msg-attachment-item direct-video-card" style="margin: 12px 0; max-width: 680px; width: 100%; border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden; background: #000; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                        <video src="${fullUrl}" controls playsinline style="width: 100%; max-height: 440px; display: block;"></video>
                        <div style="padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03);">
                            <span style="font-size: 0.82rem; font-weight: 600; color: var(--text-primary);">🎬 ${att.name || 'Direct Video Stream'}</span>
                            <a href="${fullUrl}" target="_blank" download class="btn-action-pill" style="text-decoration: none; font-size: 0.75rem; padding: 4px 10px; background: rgba(0,242,254,0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full);">
                                ⬇️ Download Video
                            </a>
                        </div>
                    </div>
                `;
            } else if (att.type === "vimeo") {
                attachmentsHtml += `
                    <div class="msg-attachment-item vimeo-card" style="margin: 12px 0; max-width: 680px; width: 100%; border: 1px solid rgba(0,173,239,0.3); border-radius: var(--radius-md); overflow: hidden; background: #000;">
                        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
                            <iframe src="${att.embed_url}" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen style="position: absolute; top:0; left:0; width:100%; height:100%;"></iframe>
                        </div>
                        <div style="padding: 8px 14px; font-size: 0.85rem; font-weight: 600; color: var(--text-primary); background: rgba(255,255,255,0.03);">
                            <span style="color: #00adef;">▶</span> ${att.name}
                        </div>
                    </div>
                `;
            } else if (att.type === "webpage") {
                let host = "";
                try { host = new URL(att.url).hostname; } catch(e) { host = "Website"; }
                attachmentsHtml += `
                    <div class="msg-attachment-item webpage-card" style="margin: 12px 0; max-width: 580px; width: 100%; border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden; background: rgba(255,255,255,0.03); box-shadow: 0 4px 20px rgba(0,0,0,0.4); text-align: left;">
                        ${att.image ? `<div style="width: 100%; height: 160px; overflow: hidden; background: #111;"><img src="${att.image}" alt="Preview" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.parentElement.style.display='none'"/></div>` : ''}
                        <div style="padding: 12px 14px;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                ${att.favicon ? `<img src="${att.favicon}" style="width: 16px; height: 16px; border-radius: 2px;" onerror="this.style.display='none'"/>` : '🌐'}
                                <span style="font-size: 0.75rem; color: var(--accent-cyan); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">${host}</span>
                            </div>
                            <a href="${att.url}" target="_blank" rel="noopener noreferrer" style="font-weight: 600; font-size: 0.95rem; color: var(--text-primary); text-decoration: none; display: block; margin-bottom: 6px; line-height: 1.3;">${att.name || att.url}</a>
                            ${att.description ? `<p style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${att.description}</p>` : ''}
                        </div>
                    </div>
                `;
            } else if (att.type === "video") {
                attachmentsHtml += `
                    <div class="msg-attachment-item video-attachment">
                        <video src="${fullUrl}" controls autoplay loop muted playsinline style="border-radius: var(--radius-md); max-width: 100%; width: 100%; max-width: 680px;"></video>
                    </div>
                `;
            } else {
                attachmentsHtml += `
                    <div class="msg-attachment-item doc-attachment">
                        <span class="file-icon">📄</span>
                        <span class="file-name">${att.name}</span>
                    </div>
                `;
            }
        }
        attachmentsHtml += `</div>`;
        return attachmentsHtml;
    }

    appendMessage(msg) {
        const msgWrapper = document.createElement("div");
        msgWrapper.className = `chat-bubble-row ${msg.role === "user" ? "user-row" : "assistant-row"}`;
        msgWrapper.id = `msg-${msg.id || Date.now()}`;

        let attachmentsList = msg.attachments;
        if (typeof attachmentsList === "string") {
            try { attachmentsList = JSON.parse(attachmentsList); } catch(e) { attachmentsList = []; }
        }
        attachmentsList = attachmentsList || [];

        let attachmentsHtml = this.buildAttachmentsHtml(attachmentsList);
        let imageActionsHtml = "";

        const vidAtt = attachmentsList.find(a => a.type === "video");
        const imgAtt = attachmentsList.find(a => a.type === "image");
        if (vidAtt) {
            const fullUrl = vidAtt.url.startsWith("http") ? vidAtt.url : "http://127.0.0.1:8000" + vidAtt.url;
            imageActionsHtml = `
                <div class="generated-media-actions" style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                    <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${fullUrl}', '${(vidAtt.name || 'nexora_video').replace(/'/g, "\\'")}.mp4')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                        📥 Download Video
                    </button>
                    <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                        🔄 Regenerate
                    </button>
                    <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('video-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                        🎬 Open in Video Studio
                    </button>
                </div>
            `;
        } else if (imgAtt) {
            const fullUrl = imgAtt.url.startsWith("http") ? imgAtt.url : "http://127.0.0.1:8000" + imgAtt.url;
            imageActionsHtml = `
                <div class="generated-media-actions" style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                    <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${fullUrl}', '${(imgAtt.name || 'nexora_artwork').replace(/'/g, "\\'")}.png')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                        📥 Download Image
                    </button>
                    <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                        🔄 Regenerate
                    </button>
                    <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('image-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                        🎨 Open in Studio
                    </button>
                </div>
            `;
        }

        if (!imageActionsHtml && msg.role === "assistant" && msg.content) {
            // Check for video tag or storage video URL
            const vidMatch = msg.content.match(/<video[^>]*src=["'](.*?)["']/i) || msg.content.match(/\/storage\/generated_videos\/[^\s"')]+/);
            if (vidMatch) {
                let rawUrl = vidMatch[1] || vidMatch[0];
                const fullUrl = rawUrl.startsWith("http") ? rawUrl : "http://127.0.0.1:8000" + rawUrl;
                imageActionsHtml = `
                    <div class="generated-media-actions" style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                        <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${fullUrl}', 'nexora_video.mp4')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            📥 Download Video
                        </button>
                        <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            🔄 Regenerate
                        </button>
                        <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('video-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                            🎬 Open in Video Studio
                        </button>
                    </div>
                `;
            } else if (msg.content.includes("![")) {
                const match = msg.content.match(/!\[(.*?)\]\((.*?)\)/);
                if (match) {
                    const imgAlt = match[1] || 'nexora_media';
                    let rawUrl = match[2];
                    const fullUrl = rawUrl.startsWith("http") ? rawUrl : "http://127.0.0.1:8000" + rawUrl;
                    const isVideoUrl = rawUrl.toLowerCase().endsWith(".mp4") || rawUrl.toLowerCase().endsWith(".webm") || rawUrl.includes("/generated_videos/");
                    
                    if (isVideoUrl) {
                        imageActionsHtml = `
                            <div class="generated-media-actions" style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                                <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${fullUrl}', 'nexora_video.mp4')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                                    📥 Download Video
                                </button>
                                <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                                    🔄 Regenerate
                                </button>
                                <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('video-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                                    🎬 Open in Video Studio
                                </button>
                            </div>
                        `;
                    } else {
                        imageActionsHtml = `
                            <div class="generated-media-actions" style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                                <button type="button" class="btn-action-pill" onclick="window.downloadMediaFile('${fullUrl}', '${imgAlt.replace(/'/g, "\\'")}.png')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(0, 242, 254, 0.15); border: 1px solid var(--accent-cyan); color: var(--accent-cyan); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                                    📥 Download Image
                                </button>
                                <button type="button" class="btn-action-pill" onclick="window.nexoraChat.regeneratePrompt()" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(168, 85, 247, 0.15); border: 1px solid var(--accent-purple); color: var(--accent-purple); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                                    🔄 Regenerate
                                </button>
                                <button type="button" class="btn-action-pill" onclick="window.nexoraApp.switchView('image-studio')" style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: var(--radius-full); font-size: 0.8rem; font-weight: 600; cursor: pointer;">
                                    🎨 Open in Studio
                                </button>
                            </div>
                        `;
                    }
                }
            }
        }

        const avatar = msg.role === "user" 
            ? `<div class="chat-avatar user-avatar">U</div>`
            : `<div class="chat-avatar robot-avatar">⚡</div>`;

        msgWrapper.innerHTML = `
            ${msg.role !== "user" ? avatar : ""}
            <div class="chat-bubble ${msg.role}">
                ${attachmentsHtml}
                <div class="msg-content"></div>
                ${imageActionsHtml}
                <div class="msg-footer">
                    <span class="msg-time">${new Date(msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <div class="msg-actions">
                        <button class="msg-action-btn copy-btn" title="Copy text" onclick="window.nexoraChat.copyText(this)">📋</button>
                        ${msg.role === "assistant" ? `
                            <button class="msg-action-btn regen-btn" title="Regenerate response" onclick="window.nexoraChat.regeneratePrompt()">🔄</button>
                            <button class="msg-action-btn speak-btn" title="Speak aloud" onclick="window.nexoraChat.speakMessage(this)">🔊</button>
                        ` : `
                            <button class="msg-action-btn edit-btn" title="Edit prompt" onclick="window.nexoraChat.editPrompt(this)">✏️</button>
                        `}
                    </div>
                </div>
            </div>
            ${msg.role === "user" ? avatar : ""}
        `;

        this.messagesContainer.appendChild(msgWrapper);
        const contentEl = msgWrapper.querySelector(".msg-content");
        if (msg.content) {
            this.renderMessageContent(contentEl, msg.content);
        }

        this.scrollToBottom();
        return msgWrapper;
    }

    regeneratePrompt() {
        const userBubbles = document.querySelectorAll(".chat-bubble-row.user-row");
        if (userBubbles.length > 0) {
            const lastUserText = userBubbles[userBubbles.length - 1].querySelector(".msg-content").innerText.trim();
            if (lastUserText) {
                this.handleSendMessage(lastUserText);
            }
        }
    }

    editPrompt(btn) {
        const bubble = btn.closest(".chat-bubble");
        if (!bubble) return;
        const content = bubble.querySelector(".msg-content").innerText.trim();
        const chatInput = document.getElementById("chat-input");
        if (chatInput) {
            chatInput.value = content;
            chatInput.focus();
            chatInput.style.height = "auto";
            chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + "px";
        }
    }

    renderMessageContent(targetEl, text) {
        if (window.marked) {
            targetEl.innerHTML = window.marked.parse(text);
        } else {
            targetEl.textContent = text;
        }

        // Parse [MM:SS] or [HH:MM:SS] timestamps and transform into interactive video seek links
        try {
            const rawHtml = targetEl.innerHTML;
            const linkedHtml = rawHtml.replace(
                /(?:\[|\()(\d{1,2}:\d{2}(?::\d{2})?)(?:\]|\))/g,
                '<a href="javascript:void(0)" class="timestamp-link" onclick="window.seekAnyVideo(\'$1\')" style="color: var(--accent-cyan); font-weight: 600; text-decoration: none; background: rgba(0,242,254,0.12); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(0,242,254,0.3); margin: 0 2px; cursor: pointer;" title="Jump video to $1">⏱️ $1</a>'
            );
            targetEl.innerHTML = linkedHtml;
        } catch (e) {}

        // Fix markdown image URLs: if an image src is actually a video or in generated_videos, replace with <video>
        targetEl.querySelectorAll("img").forEach((img) => {
            const rawSrc = img.getAttribute("src") || "";
            const lowerSrc = rawSrc.toLowerCase();
            const isVideo = lowerSrc.endsWith(".mp4") || lowerSrc.endsWith(".webm") || lowerSrc.includes("/generated_videos/");
            const resolvedSrc = rawSrc.startsWith("/storage/") ? ("http://127.0.0.1:8000" + rawSrc) : rawSrc;

            if (isVideo) {
                const vid = document.createElement("video");
                vid.src = resolvedSrc;
                vid.controls = true;
                vid.autoplay = true;
                vid.loop = true;
                vid.muted = true;
                vid.playsInline = true;
                vid.style.width = "100%";
                vid.style.maxWidth = "680px";
                vid.style.borderRadius = "var(--radius-md)";
                vid.style.boxShadow = "0 8px 30px rgba(0,0,0,0.55)";
                vid.style.marginTop = "10px";
                vid.style.marginBottom = "10px";
                vid.style.display = "block";
                if (img.parentNode) {
                    img.parentNode.replaceChild(vid, img);
                }
                return;
            }

            if (rawSrc.startsWith("/storage/")) {
                img.src = resolvedSrc;
            }
            img.style.maxWidth = "100%";
            img.style.borderRadius = "var(--radius-md)";
            img.style.boxShadow = "0 8px 30px rgba(0,0,0,0.55)";
            img.style.marginTop = "10px";
            img.style.marginBottom = "10px";
            img.style.cursor = "pointer";
            img.onclick = () => window.open(img.src, "_blank");
        });

        // Fix video URLs to point to backend storage if relative
        targetEl.querySelectorAll("video").forEach((vid) => {
            const src = vid.getAttribute("src") || vid.src || "";
            if (src && src.startsWith("/storage/")) {
                vid.src = "http://127.0.0.1:8000" + src;
            }
            // Check any <source> children
            vid.querySelectorAll("source").forEach((s) => {
                const sSrc = s.getAttribute("src") || "";
                if (sSrc.startsWith("/storage/")) {
                    s.src = "http://127.0.0.1:8000" + sSrc;
                }
            });

            vid.style.width = "100%";
            vid.style.maxWidth = "680px";
            vid.style.borderRadius = "var(--radius-md)";
            vid.style.boxShadow = "0 8px 30px rgba(0,0,0,0.55)";
            vid.style.marginTop = "10px";
            vid.style.marginBottom = "10px";
            vid.style.display = "block";

            // Initialize Hls.js for direct .m3u8 video streams
            if (window.Hls && Hls.isSupported() && ((src && src.includes(".m3u8")) || vid.innerHTML.includes(".m3u8"))) {
                try {
                    const hls = new Hls();
                    hls.loadSource(src);
                    hls.attachMedia(vid);
                } catch (e) {
                    console.warn("HLS stream attachment:", e);
                }
            }
        });

        // Intercept any media download links rendered in markdown
        targetEl.querySelectorAll("a").forEach((link) => {
            const href = link.getAttribute("href") || "";
            if (href.includes("/storage/") || link.hasAttribute("download") || href.includes("/download")) {
                link.onclick = (e) => {
                    e.preventDefault();
                    const fname = link.getAttribute("download") || href.split("/").pop().split("?")[0] || "nexora_media";
                    window.downloadMediaFile(href, fname);
                };
            }
        });

        // Apply syntax highlighting to code blocks
        if (window.hljs) {
            targetEl.querySelectorAll("pre code").forEach((block) => {
                window.hljs.highlightElement(block);

                // Add copy button to code block header
                const pre = block.parentElement;
                if (!pre.querySelector(".code-copy-btn")) {
                    const btn = document.createElement("button");
                    btn.className = "code-copy-btn";
                    btn.textContent = "Copy";
                    btn.onclick = () => {
                        navigator.clipboard.writeText(block.innerText);
                        btn.textContent = "Copied!";
                        setTimeout(() => btn.textContent = "Copy", 2000);
                    };
                    pre.appendChild(btn);
                }
            });
        }
    }

    copyText(btn) {
        const bubble = btn.closest(".chat-bubble");
        const content = bubble.querySelector(".msg-content").innerText;
        navigator.clipboard.writeText(content);
        btn.textContent = "✓";
        setTimeout(() => btn.textContent = "📋", 2000);
    }

    speakMessage(btn) {
        const bubble = btn.closest(".chat-bubble");
        const content = bubble.querySelector(".msg-content").innerText;
        if (window.nexoraVoice) {
            window.nexoraVoice.speak(content);
        }
    }

    addStagedAttachment(att) {
        this.stagedAttachments.push(att);
        this.renderAttachmentPreviews();
    }

    clearStagedAttachments() {
        this.stagedAttachments = [];
        this.renderAttachmentPreviews();
    }

    removeStagedAttachment(index) {
        this.stagedAttachments.splice(index, 1);
        this.renderAttachmentPreviews();
    }

    renderAttachmentPreviews() {
        if (!this.attachmentPreviewBar) return;
        this.attachmentPreviewBar.innerHTML = "";

        if (this.stagedAttachments.length === 0) {
            this.attachmentPreviewBar.style.display = "none";
            return;
        }

        this.attachmentPreviewBar.style.display = "flex";
        this.stagedAttachments.forEach((att, idx) => {
            const pill = document.createElement("div");
            pill.className = "attachment-pill";
            const fullUrl = att.url && att.url.startsWith("http") ? att.url : (att.url ? "http://127.0.0.1:8000" + att.url : "");
            let iconOrThumb = `<span class="pill-type">${(att.type || 'file').toUpperCase()}</span>`;
            if (att.type === "image" && (fullUrl || att.thumbnail)) {
                const src = fullUrl || att.thumbnail;
                iconOrThumb = `<img src="${src}" style="width: 22px; height: 22px; border-radius: 4px; object-fit: cover; margin-right: 6px;" onerror="this.style.display='none'"/>`;
            } else if (att.type === "youtube") {
                iconOrThumb = `<span style="color: #ff3333; margin-right: 6px; font-size: 1rem;">▶</span><span class="pill-type" style="background: rgba(255,0,0,0.2); color: #ff5555;">YOUTUBE</span>`;
            } else if (att.type === "direct_video" || att.type === "video") {
                iconOrThumb = `<span class="pill-type" style="background: rgba(0,242,254,0.2); color: var(--accent-cyan);">VIDEO</span>`;
            } else if (att.type === "webpage") {
                iconOrThumb = `<span class="pill-type" style="background: rgba(168,85,247,0.2); color: var(--accent-purple);">WEB</span>`;
            }
            pill.innerHTML = `
                ${iconOrThumb}
                <span class="pill-name">${att.name || att.url}</span>
                <button class="pill-remove" onclick="window.nexoraChat.removeStagedAttachment(${idx})">×</button>
            `;
            this.attachmentPreviewBar.appendChild(pill);
        });
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    clearMessages() {
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = "";
        }
        if (this.emptyState) {
            this.emptyState.style.display = "flex";
        }
        this.currentConversationId = null;
    }
}

window.NexoraChat = NexoraChat;

