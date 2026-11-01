/**
 * NEXORA AI - Advanced Voice Assistant Engine
 * Synchronized with 3D Robot Speaking Animations & Web Speech API
 * Full Volume Control, Playback Speed, Custom Voice Selection & Hardware Verification
 */

class NexoraVoice {
    constructor() {
        this.recognition = null;
        this.isRecording = false;
        this.synthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.autoSpeak = localStorage.getItem("nexora_auto_speak") === "true";
        this.selectedVoice = null;
        this.volume = parseFloat(localStorage.getItem("nexora_voice_volume") || "1.0");
        this.speechRate = parseFloat(localStorage.getItem("nexora_voice_rate") || "1.0");
        this.speechPitch = 1.0;

        this.micBtn = document.getElementById("mic-btn");
        this.voiceIndicator = document.getElementById("voice-recording-indicator");

        this.initRecognition();
        this.initSynthesis();
        this.bindEvents();
        this.initVoiceControls();
    }

    initRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            console.warn("Speech Recognition API is not supported in this browser.");
            if (this.micBtn) {
                this.micBtn.title = "Speech recognition not supported in current browser. Use Google Chrome.";
            }
            return;
        }

        this.recognition = new SpeechRec();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = "en-US";

        this.recognition.onstart = () => {
            this.isRecording = true;
            if (this.micBtn) this.micBtn.classList.add("recording");
            if (this.voiceIndicator) {
                this.voiceIndicator.textContent = "Listening... Speak now";
                this.voiceIndicator.style.display = "inline";
            }

            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("listening");
            }
        };

        this.recognition.onresult = (event) => {
            let transcript = "";
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                transcript += event.results[i][0].transcript;
            }

            const chatInput = document.getElementById("chat-input");
            if (chatInput) {
                chatInput.value = transcript;
                chatInput.style.height = "auto";
                chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + "px";
                chatInput.focus();
            }
        };

        this.recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            let userMsg = "Voice recognition error: " + event.error;
            if (event.error === "not-allowed" || event.error === "permission-denied") {
                userMsg = "Microphone access was denied. Please allow microphone permissions in your browser URL bar.";
            } else if (event.error === "no-speech") {
                userMsg = "No speech detected. Please try speaking again.";
            }
            if (window.nexoraApp) {
                window.nexoraApp.showToast(userMsg, "warning");
            }
            this.stopRecording();
        };

        this.recognition.onend = () => {
            this.stopRecording();
            const chatInput = document.getElementById("chat-input");
            if (chatInput && chatInput.value.trim().length > 0) {
                chatInput.focus();
                if (window.nexoraApp) {
                    window.nexoraApp.showToast("Transcription ready. Review or edit before sending.", "info");
                }
            }
        };
    }

    initSynthesis() {
        if (!this.synthesis) return;

        const populateVoices = () => {
            const voices = this.synthesis.getVoices();
            const voiceSelect = document.getElementById("setting-voice-select");
            const savedVoiceName = localStorage.getItem("nexora_selected_voice");

            if (voiceSelect && voices.length > 0) {
                voiceSelect.innerHTML = "";
                voices.forEach((v) => {
                    const opt = document.createElement("option");
                    opt.value = v.name;
                    opt.textContent = `${v.name} (${v.lang})`;
                    if (savedVoiceName && v.name === savedVoiceName) {
                        opt.selected = true;
                        this.selectedVoice = v;
                    } else if (!savedVoiceName && (v.default || v.name.includes("Google") || v.name.includes("Natural"))) {
                        opt.selected = true;
                        this.selectedVoice = v;
                    }
                    voiceSelect.appendChild(opt);
                });
            }
        };

        populateVoices();
        if (this.synthesis.onvoiceschanged !== undefined) {
            this.synthesis.onvoiceschanged = populateVoices;
        }
    }

    initVoiceControls() {
        // Volume Slider
        const volumeInput = document.getElementById("setting-voice-volume");
        const volumeLabel = document.getElementById("setting-voice-volume-val");
        if (volumeInput) {
            volumeInput.value = this.volume;
            if (volumeLabel) volumeLabel.textContent = `${Math.round(this.volume * 100)}%`;

            volumeInput.addEventListener("input", (e) => {
                this.volume = parseFloat(e.target.value);
                localStorage.setItem("nexora_voice_volume", this.volume);
                if (volumeLabel) volumeLabel.textContent = `${Math.round(this.volume * 100)}%`;
            });
        }

        // Playback Speed Rate
        const rateSelect = document.getElementById("setting-voice-rate");
        if (rateSelect) {
            rateSelect.value = String(this.speechRate);
            rateSelect.addEventListener("change", (e) => {
                this.speechRate = parseFloat(e.target.value);
                localStorage.setItem("nexora_voice_rate", this.speechRate);
            });
        }

        // Voice Select
        const voiceSelect = document.getElementById("setting-voice-select");
        if (voiceSelect) {
            voiceSelect.addEventListener("change", (e) => {
                const voices = this.synthesis.getVoices();
                this.selectedVoice = voices.find(v => v.name === e.target.value) || null;
                if (this.selectedVoice) {
                    localStorage.setItem("nexora_selected_voice", this.selectedVoice.name);
                }
            });
        }

        // Auto-Speak Checkbox
        const autoSpeakCheck = document.getElementById("setting-voice-autospeak");
        if (autoSpeakCheck) {
            autoSpeakCheck.checked = this.autoSpeak;
            autoSpeakCheck.addEventListener("change", (e) => {
                this.autoSpeak = e.target.checked;
                localStorage.setItem("nexora_auto_speak", this.autoSpeak);
                if (window.nexoraApp) {
                    window.nexoraApp.showToast(this.autoSpeak ? "Auto-speak enabled" : "Auto-speak disabled", "info");
                }
            });
        }
    }

    bindEvents() {
        if (this.micBtn) {
            this.micBtn.addEventListener("click", () => {
                if (this.isRecording) {
                    this.stopRecording();
                } else {
                    this.startRecording();
                }
            });
        }
    }

    async startRecording() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            if (window.nexoraApp) {
                window.nexoraApp.showToast("Speech recognition is not supported in this browser. Please use Google Chrome.", "warning");
            }
            return;
        }

        // Verify microphone hardware permission
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop());
            } catch (err) {
                console.error("Microphone hardware error:", err);
                if (window.nexoraApp) {
                    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                        window.nexoraApp.showToast("Microphone permission denied. Please allow microphone access in your browser settings.", "error");
                    } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                        window.nexoraApp.showToast("No microphone found on your system.", "error");
                    } else {
                        window.nexoraApp.showToast(`Microphone error: ${err.message}`, "error");
                    }
                }
                return;
            }
        }

        try {
            this.recognition.start();
        } catch (e) {
            console.warn("Recognition start notice:", e);
        }
    }

    stopRecording() {
        this.isRecording = false;
        if (this.micBtn) this.micBtn.classList.remove("recording");
        if (this.voiceIndicator) this.voiceIndicator.style.display = "none";

        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }

        if (window.nexoraRobotInstance && window.nexoraRobotInstance.state === "listening") {
            window.nexoraRobotInstance.setState("idle");
        }
    }

    speak(text) {
        if (!this.synthesis || !text) return;

        // Clean markdown for spoken text
        const plainText = text
            .replace(/```[\s\S]*?```/g, "Code block omitted.")
            .replace(/`([^`]+)`/g, "$1")
            .replace(/[*#_~>]/g, "")
            .trim();

        this.synthesis.cancel(); // Stop any currently playing audio

        const utterance = new SpeechSynthesisUtterance(plainText);
        if (this.selectedVoice) utterance.voice = this.selectedVoice;
        utterance.volume = this.volume;
        utterance.rate = this.speechRate;
        utterance.pitch = this.speechPitch;

        utterance.onstart = () => {
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("speaking");
            }
        };

        utterance.onpause = () => {
            if (window.nexoraRobotInstance && window.nexoraRobotInstance.state === "speaking") {
                window.nexoraRobotInstance.setState("idle");
            }
        };

        utterance.onresume = () => {
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("speaking");
            }
        };

        utterance.onend = () => {
            if (window.nexoraRobotInstance && window.nexoraRobotInstance.state === "speaking") {
                window.nexoraRobotInstance.setState("idle");
            }
        };

        utterance.onerror = () => {
            if (window.nexoraRobotInstance && window.nexoraRobotInstance.state === "speaking") {
                window.nexoraRobotInstance.setState("idle");
            }
        };

        this.currentUtterance = utterance;
        this.synthesis.speak(utterance);
    }

    pauseSpeaking() {
        if (this.synthesis && this.synthesis.speaking) {
            this.synthesis.pause();
            if (window.nexoraRobotInstance && window.nexoraRobotInstance.state === "speaking") {
                window.nexoraRobotInstance.setState("idle");
            }
        }
    }

    resumeSpeaking() {
        if (this.synthesis && this.synthesis.paused) {
            this.synthesis.resume();
            if (window.nexoraRobotInstance) {
                window.nexoraRobotInstance.setState("speaking");
            }
        }
    }

    stopSpeaking() {
        if (this.synthesis) {
            this.synthesis.cancel();
        }
        if (window.nexoraRobotInstance && window.nexoraRobotInstance.state === "speaking") {
            window.nexoraRobotInstance.setState("idle");
        }
    }
}

window.NexoraVoice = NexoraVoice;
