/**
 * NEXORA AI - Activity & Usage Reports Controller
 * Connects to /api/reports to render real database analytics and CSV exports
 */

class NexoraReports {
    constructor() {
        this.container = document.getElementById("reports-container");
        this.refreshBtn = document.getElementById("reports-refresh-btn");
        this.exportBtn = document.getElementById("reports-export-csv-btn");

        this.init();
    }

    init() {
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener("click", () => this.loadReports());
        }

        if (this.exportBtn) {
            this.exportBtn.addEventListener("click", () => {
                window.location.href = "http://127.0.0.1:8000/api/reports/export-csv";
            });
        }
    }

    async loadReports() {
        if (!this.container) return;
        this.setLoading(true);

        try {
            const res = await fetch("http://127.0.0.1:8000/api/reports");
            if (!res.ok) throw new Error("Failed to load reports from server");

            const data = await res.json();
            this.renderReports(data);

            if (window.nexoraApp) {
                window.nexoraApp.showToast("Activity reports refreshed", "info");
            }
        } catch (error) {
            console.error("Reports error:", error);
            if (this.container) {
                this.container.innerHTML = `<div class="msg-error"><p>Failed to load analytics: ${error.message}</p></div>`;
            }
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(loading) {
        if (this.refreshBtn) {
            this.refreshBtn.disabled = loading;
            this.refreshBtn.innerHTML = loading
                ? `<span class="spinner"></span> Refreshing...`
                : `<span>🔄 Refresh Data</span>`;
        }
    }

    renderReports(data) {
        const m = data.metrics;

        // Models distribution HTML
        let modelsHtml = "";
        if (data.models_breakdown && data.models_breakdown.length > 0) {
            modelsHtml = data.models_breakdown.map((mb) => `
                <div class="report-metric-bar-item">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.85rem;">
                        <strong>${mb.model}</strong>
                        <span>${mb.count} msgs (${mb.percentage}%)</span>
                    </div>
                    <div class="progress-bar-container" style="margin: 0 0 10px 0; height: 8px;">
                        <div class="progress-bar-fill" style="width: ${mb.percentage}%;"></div>
                    </div>
                </div>
            `).join("");
        } else {
            modelsHtml = `<p style="color: var(--text-muted); font-size: 0.88rem;">No assistant model interactions recorded yet.</p>`;
        }

        // Recent activity rows HTML
        let activityHtml = "";
        if (data.recent_activity && data.recent_activity.length > 0) {
            activityHtml = data.recent_activity.map((act) => `
                <tr>
                    <td><span class="report-act-badge badge-${act.type}">${act.event}</span></td>
                    <td style="max-width: 320px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${act.details}</td>
                    <td><code>${act.model}</code></td>
                    <td style="font-size: 0.78rem; color: var(--text-muted);">${new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td>
                </tr>
            `).join("");
        } else {
            activityHtml = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No recorded activity yet.</td></tr>`;
        }

        this.container.innerHTML = `
            <!-- Top 4 Summary Cards -->
            <div class="reports-stats-grid">
                <div class="stat-card">
                    <span class="stat-icon">💬</span>
                    <div class="stat-number">${m.total_conversations}</div>
                    <div class="stat-label">Total Conversations</div>
                    <div class="stat-sub">${m.total_messages} total messages</div>
                </div>

                <div class="stat-card">
                    <span class="stat-icon">⚡</span>
                    <div class="stat-number">${m.assistant_messages}</div>
                    <div class="stat-label">AI Generations</div>
                    <div class="stat-sub">${m.user_messages} user prompts</div>
                </div>

                <div class="stat-card">
                    <span class="stat-icon">📄</span>
                    <div class="stat-number">${m.total_uploads}</div>
                    <div class="stat-label">Files Uploaded</div>
                    <div class="stat-sub">${m.upload_storage_mb} MB stored</div>
                </div>

                <div class="stat-card">
                    <span class="stat-icon">🎨</span>
                    <div class="stat-number">${m.total_generated_images + m.total_generated_videos}</div>
                    <div class="stat-label">Media Synthesized</div>
                    <div class="stat-sub">${m.total_generated_images} images, ${m.total_generated_videos} videos</div>
                </div>
            </div>

            <!-- Two Columns: Model Breakdown & Recent Activity -->
            <div class="reports-details-grid">
                <div class="report-panel">
                    <h3 style="margin-bottom: 16px; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                        <span>🧠</span> Model & Provider Utilization
                    </h3>
                    ${modelsHtml}
                </div>

                <div class="report-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h3 style="font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                            <span>⏱️</span> Recent Activity Stream
                        </h3>
                        <span style="font-size: 0.78rem; color: var(--text-muted);">Live from SQLite</span>
                    </div>

                    <div style="overflow-x: auto;">
                        <table class="report-activity-table">
                            <thead>
                                <tr>
                                    <th>Event</th>
                                    <th>Details</th>
                                    <th>Provider</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${activityHtml}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
}

window.NexoraReports = NexoraReports;

