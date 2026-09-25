/**
 * BreachSpillover — Production OSINT Engine & Cybersecurity UI Controller
 * Authentic multi-source threat intelligence with live public account enumeration
 */

let currentEmail = "test@gmail.com";
let auditMode = true; // Request forensic data from backend
let isDeclassified = true; // Default: UNLOCKED / DECLASSIFIED (safe feature disabled by user request)
let networkInstance = null;
let currentInvestigationData = null;
let isPhysicsEnabled = true;
let isHierarchicalView = false;

/* ==========================================================================
   Retro 8-Bit Chiptune Audio Synthesizer (Web Audio API)
   Authentic DMG-01 GameBoy / Pokémon Style Sound FX
   Instant (< 2ms) Response on User Interaction (PointerDown / Touch / Click)
   ========================================================================== */
class RetroSoundEngine {
    constructor() {
        this.ctx = null;
        this.enabled = localStorage.getItem("breachspillover_sfx") !== "false";
        this.volume = 0.09;
        this.sampleVolume = 0.35;
        this._buffers = {};
        this._loading = {};
        this._unlocked = false;
        this._lastTactileTime = 0;

        // Sound cues to pre-decode in memory
        this._manifest = {
            click: "/static/sounds/Clickingsound.mp3",
            search: "/static/sounds/Searchingsound.mp3",
            error: "/static/sounds/Errorsound.mp3",
            export: "/static/sounds/Exportbuttonsound.mp3"
        };
    }

    _getCtx() {
        if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioCtx();
        }
        return this.ctx;
    }

    init() {
        const ctx = this._getCtx();
        if (ctx && ctx.state === "suspended") {
            ctx.resume().catch(() => {});
        }
        if (!this._unlocked) {
            this._unlocked = true;
            this.preloadBuffers();
        }
    }

    preloadBuffers() {
        const ctx = this._getCtx();
        if (!ctx) return;
        Object.entries(this._manifest).forEach(([key, url]) => {
            if (this._buffers[key] || this._loading[key]) return;
            this._loading[key] = true;
            fetch(url)
                .then(r => {
                    if (!r.ok) throw new Error("HTTP error " + r.status);
                    return r.arrayBuffer();
                })
                .then(ab => ctx.decodeAudioData(ab))
                .then(audioBuffer => {
                    let startOffset = 0;
                    try {
                        const data = audioBuffer.getChannelData(0);
                        const threshold = 0.005;
                        for (let i = 0; i < data.length; i++) {
                            if (Math.abs(data[i]) > threshold) {
                                startOffset = Math.max(0, (i - 16) / audioBuffer.sampleRate);
                                break;
                            }
                        }
                    } catch (e) {}
                    this._buffers[key] = { buffer: audioBuffer, startOffset: startOffset };
                    this._loading[key] = false;
                })
                .catch(() => {
                    this._loading[key] = false;
                });
        });
    }

    playSample(key, fallbackFn) {
        if (!this.enabled) return;
        this.init();
        const ctx = this._getCtx();
        if (!ctx) return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});

        const item = this._buffers[key];
        if (item && item.buffer) {
            try {
                const now = ctx.currentTime;
                const source = ctx.createBufferSource();
                const gain = ctx.createGain();
                source.buffer = item.buffer;
                gain.gain.setValueAtTime(this.sampleVolume, now);
                source.connect(gain);
                gain.connect(ctx.destination);
                source.start(now, item.startOffset || 0);
                return;
            } catch (e) {}
        }

        if (typeof fallbackFn === "function") {
            fallbackFn();
        }
    }

    // Classic Pokémon Menu A-Button Select (quick square blip) - Instant < 1ms
    playSelect() {
        if (!this.enabled) return;
        this.init();
        const ctx = this._getCtx();
        if (!ctx) return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});
        try {
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "square";
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.exponentialRampToValueAtTime(1320, now + 0.042);
            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.048);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.048);
        } catch (e) {}
    }

    // Primary Click Sound: Immediate Web Audio playback
    playClick() {
        this.playSelect();
    }

    // Classic Pokémon Victory / Level-Up / Target Found Fanfare
    playVictory() {
        if (!this.enabled) return;
        this.init();
        const ctx = this._getCtx();
        if (!ctx) return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});
        try {
            const now = ctx.currentTime;
            const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98];
            const stepTime = 0.065;
            notes.forEach((freq, idx) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = "square";
                osc.frequency.setValueAtTime(freq, now + idx * stepTime);
                gain.gain.setValueAtTime(this.volume, now + idx * stepTime);
                gain.gain.exponentialRampToValueAtTime(0.001, now + (idx + 1) * stepTime);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now + idx * stepTime);
                osc.stop(now + (idx + 1) * stepTime);
            });
        } catch (e) {}
    }

    // Classic Pokémon Wild Encounter / Threat Siren
    playAlert() {
        if (!this.enabled) return;
        this.init();
        const ctx = this._getCtx();
        if (!ctx) return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});
        try {
            const now = ctx.currentTime;
            const tones = [440, 660, 440, 880];
            const stepTime = 0.08;
            tones.forEach((freq, idx) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(freq, now + idx * stepTime);
                gain.gain.setValueAtTime(this.volume * 0.9, now + idx * stepTime);
                gain.gain.exponentialRampToValueAtTime(0.001, now + (idx + 1) * stepTime);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now + idx * stepTime);
                osc.stop(now + (idx + 1) * stepTime);
            });
        } catch (e) {}
    }

    // Node Inspect / Drawer Open Sound
    playInspect() {
        if (!this.enabled) return;
        this.init();
        const ctx = this._getCtx();
        if (!ctx) return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});
        try {
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "triangle";
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.06);
            gain.gain.setValueAtTime(this.volume, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.07);
        } catch (e) {}
    }

    // 8-bit Error Buzz
    playErrorBuzz() {
        if (!this.enabled) return;
        this.init();
        const ctx = this._getCtx();
        if (!ctx) return;
        if (ctx.state === "suspended") ctx.resume().catch(() => {});
        try {
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(140, now);
            osc.frequency.setValueAtTime(110, now + 0.07);
            gain.gain.setValueAtTime(this.volume * 0.8, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.18);
        } catch (e) {}
    }

    toggle() {
        return window.toggleSoundEffects();
    }

    updateButtonUI() {
        const on = localStorage.getItem("breachspillover_sfx") !== "false";
        this.enabled = on;
        const btn = document.getElementById("btn-sfx-toggle");
        const text = document.getElementById("sfx-toggle-text");
        const icon = document.getElementById("sfx-toggle-icon");
        if (btn) btn.classList.toggle("active", on);
        if (text) text.innerText = on ? "SOUND: ON" : "SOUND: MUTED";
        if (icon) {
            icon.innerHTML = on ? `
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                </svg>
            ` : `
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <line x1="23" y1="9" x2="17" y2="15"></line>
                    <line x1="17" y1="9" x2="23" y2="15"></line>
                </svg>
            `;
        }
    }
}
const sfx = new RetroSoundEngine();
window.sfx = sfx;

/* ==========================================================================
   SoundManager — Zero-latency audio router & Web Audio API sample player
   ========================================================================== */
const SoundManager = {
    _lastPlayed: {},

    _enabled() {
        try {
            return localStorage.getItem("breachspillover_sfx") !== "false";
        } catch (e) {
            return true;
        }
    },

    toggle() {
        return window.toggleSoundEffects();
    },

    updateButtonUI() {
        if (window.sfx) window.sfx.updateButtonUI();
    },

    play(key) {
        if (!this._enabled() || !window.sfx) return;
        const now = Date.now();

        if (key === "click") {
            // Deduplicate if immediate pointerdown tactile sound already fired for this interaction
            if (now - (window.sfx._lastTactileTime || 0) < 100) return;
            window.sfx._lastTactileTime = now;
            window.sfx.playClick();
            return;
        }

        // Throttle longer sound triggers
        if (now - (this._lastPlayed[key] || 0) < 120) return;
        this._lastPlayed[key] = now;

        if (key === "search") {
            window.sfx.playSample("search", () => window.sfx.playAlert());
        } else if (key === "error") {
            window.sfx.playSample("error", () => window.sfx.playErrorBuzz());
        } else if (key === "export") {
            window.sfx.playSample("export", () => window.sfx.playSelect());
        } else {
            window.sfx.playSample(key, () => window.sfx.playSelect());
        }
    }
};
window.SoundManager = SoundManager;
function playSound(key) { SoundManager.play(key); }
window.playSound = playSound;

window.toggleSoundEffects = function() {
    let current = true;
    try {
        current = localStorage.getItem("breachspillover_sfx") !== "false";
    } catch(e) {}
    const next = !current;
    try {
        localStorage.setItem("breachspillover_sfx", next ? "true" : "false");
        localStorage.setItem("breachspillover_ui_sounds", next ? "true" : "false");
    } catch(e) {}
    if (window.sfx) {
        window.sfx.enabled = next;
        window.sfx.updateButtonUI();
        if (next) {
            window.sfx.init();
            window.sfx.playSelect();
        }
    }
    if (window.SoundManager) {
        window.SoundManager.updateButtonUI();
    }
    if (typeof showToast === "function") {
        showToast(next ? "Sound Effects ENABLED [ACTIVE]" : "Sound Effects MUTED", next ? "success" : "info");
    }
    return next;
};

// Immediate Tactile Click Feedback on pointerdown (0ms physical press response)
window.addEventListener("pointerdown", (e) => {
    if (!window.sfx) return;
    window.sfx.init();

    const target = e.target;
    if (!target) return;

    // Check if target or parent is an interactive UI element
    const interactive = target.closest(
        'button, .tab-btn, .btn-pivot-filter, .btn-cat-filter, .btn-action-tool, ' +
        '.btn-tool, .btn-primary, .btn-secondary, .finding-card-clickable, ' +
        '.copilot-chip, .copilot-tab-btn, .btn-mini-unlock, .tool-launcher-card, ' +
        '.btn-modal-close, .btn-close-drawer, .breach-row, #ai-copilot-floating-btn, ' +
        '[onclick], [role="button"]'
    );

    if (interactive && !interactive.disabled) {
        window.sfx._lastTactileTime = Date.now();
        window.sfx.playClick();
    }
}, { passive: true, capture: true });

// Preload buffers on initial DOM readiness or first touch
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        if (window.sfx) window.sfx.init();
    });
} else {
    if (window.sfx) window.sfx.init();
}

/* ==========================================================================
   Dual Theme Color Palettes & Engine Controllers (Sleek Rounded Box Nodes)
   ========================================================================== */
const BOX_PROPS = {
    shape: "box",
    shapeProperties: { borderRadius: 6 },
    margin: { top: 8, bottom: 8, left: 12, right: 12 },
    borderWidth: 1.5,
    borderWidthSelected: 2.5
};

const DARK_GRAPH_GROUPS = {
    identity: { ...BOX_PROPS, color: { background: "#0c1729", border: "#38bdf8", highlight: { border: "#7dd3fc", background: "#132544" } }, font: { color: "#f8fafc", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2.5 },
    employee: { ...BOX_PROPS, color: { background: "#0c1729", border: "#38bdf8", highlight: { border: "#7dd3fc", background: "#132544" } }, font: { color: "#f8fafc", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2.5 },
    clean: { ...BOX_PROPS, color: { background: "#062319", border: "#10b981", highlight: { border: "#34d399", background: "#0c3b2b" } }, font: { color: "#6ee7b7", face: "JetBrains Mono" } },
    hub_breaches: { ...BOX_PROPS, color: { background: "#220e15", border: "#f43f5e", highlight: { border: "#ffffff", background: "#381724" } }, font: { color: "#fecdd3", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_git: { ...BOX_PROPS, color: { background: "#0a192f", border: "#38bdf8", highlight: { border: "#ffffff", background: "#132f4c" } }, font: { color: "#bae6fd", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_accounts: { ...BOX_PROPS, color: { background: "#1a102e", border: "#c084fc", highlight: { border: "#ffffff", background: "#2b1c47" } }, font: { color: "#e9d5ff", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_telecom: { ...BOX_PROPS, color: { background: "#051f1f", border: "#22d3ee", highlight: { border: "#ffffff", background: "#0a2e2e" } }, font: { color: "#a5f3fc", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_geo: { ...BOX_PROPS, color: { background: "#072115", border: "#34d399", highlight: { border: "#ffffff", background: "#0d3121" } }, font: { color: "#a7f3d0", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_semantic: { ...BOX_PROPS, color: { background: "#1c1427", border: "#a855f7", highlight: { border: "#ffffff", background: "#2e1b4a" } }, font: { color: "#f3e8ff", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    leak: { ...BOX_PROPS, color: { background: "#191209", border: "#f59e0b", highlight: { border: "#fde047", background: "#271b0c" } }, font: { color: "#f8fafc", face: "JetBrains Mono" } },
    leak_overflow: { ...BOX_PROPS, color: { background: "#0f172a", border: "#38bdf8", highlight: { border: "#7dd3fc", background: "#1e293b" } }, font: { color: "#bae6fd", face: "JetBrains Mono" } },
    breach: { ...BOX_PROPS, color: { background: "#220e15", border: "#f43f5e", highlight: { border: "#fda4af", background: "#381724" } }, font: { color: "#fda4af", face: "JetBrains Mono" } },
    stealer: { ...BOX_PROPS, color: { background: "#260e18", border: "#e11d48", highlight: { border: "#fecdd3", background: "#3f1426" } }, font: { color: "#fecdd3", face: "JetBrains Mono" } },
    credential: { ...BOX_PROPS, color: { background: "#2d0b0b", border: "#ef4444", highlight: { border: "#fca5a5", background: "#451212" } }, font: { color: "#fca5a5", face: "JetBrains Mono" } },
    credentials: { ...BOX_PROPS, color: { background: "#2d0b0b", border: "#ef4444", highlight: { border: "#fca5a5", background: "#451212" } }, font: { color: "#fca5a5", face: "JetBrains Mono" } },
    physical: { ...BOX_PROPS, color: { background: "#064e3b", border: "#10b981", highlight: { border: "#6ee7b7", background: "#0a664e" } }, font: { color: "#6ee7b7", face: "JetBrains Mono" } },
    relative: { ...BOX_PROPS, color: { background: "#3b1778", border: "#8b5cf6", highlight: { border: "#c4b5fd", background: "#4c1d95" } }, font: { color: "#c4b5fd", face: "JetBrains Mono" } },
    relatives: { ...BOX_PROPS, color: { background: "#3b1778", border: "#8b5cf6", highlight: { border: "#c4b5fd", background: "#4c1d95" } }, font: { color: "#c4b5fd", face: "JetBrains Mono" } },
    pivot: { ...BOX_PROPS, color: { background: "#082f49", border: "#0ea5e9", highlight: { border: "#7dd3fc", background: "#0c3d5e" } }, font: { color: "#7dd3fc", face: "JetBrains Mono" } },
    pivots: { ...BOX_PROPS, color: { background: "#082f49", border: "#0ea5e9", highlight: { border: "#7dd3fc", background: "#0c3d5e" } }, font: { color: "#7dd3fc", face: "JetBrains Mono" } },
    pivot_account: { ...BOX_PROPS, color: { background: "#082f49", border: "#0ea5e9", highlight: { border: "#7dd3fc", background: "#0c3d5e" } }, font: { color: "#7dd3fc", face: "JetBrains Mono" } },
    pivot_semantic: { ...BOX_PROPS, color: { background: "#082f49", border: "#0ea5e9", highlight: { border: "#7dd3fc", background: "#0c3d5e" } }, font: { color: "#7dd3fc", face: "JetBrains Mono" } },
    domain: { ...BOX_PROPS, color: { background: "#1e1b4b", border: "#8b5cf6", highlight: { border: "#a78bfa", background: "#2a2663" } }, font: { color: "#a78bfa", face: "JetBrains Mono" } },
    subdomain: { ...BOX_PROPS, color: { background: "#1e1b4b", border: "#8b5cf6", highlight: { border: "#a78bfa", background: "#2a2663" } }, font: { color: "#a78bfa", face: "JetBrains Mono" } },
    correlated_identity: { ...BOX_PROPS, color: { background: "#300a12", border: "#f43f5e", highlight: { border: "#fda4af", background: "#42101b" } }, font: { color: "#fecdd3", face: "JetBrains Mono" } }
};

const LIGHT_GRAPH_GROUPS = {
    identity: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2.5 },
    employee: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2.5 },
    clean: { ...BOX_PROPS, color: { background: "#D1FAE5", border: "#059669", highlight: { border: "#065F46", background: "#A7F3D0" } }, font: { color: "#065F46", face: "JetBrains Mono" } },
    hub_breaches: { ...BOX_PROPS, color: { background: "#FFE4E6", border: "#E11D48", highlight: { border: "#9F1239", background: "#FECDD3" } }, font: { color: "#9F1239", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_git: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_accounts: { ...BOX_PROPS, color: { background: "#F3E8FF", border: "#9333EA", highlight: { border: "#6B21A8", background: "#E9D5FF" } }, font: { color: "#6B21A8", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_telecom: { ...BOX_PROPS, color: { background: "#CFFAFE", border: "#0891B2", highlight: { border: "#155E75", background: "#A5F3FC" } }, font: { color: "#155E75", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_geo: { ...BOX_PROPS, color: { background: "#D1FAE5", border: "#059669", highlight: { border: "#065F46", background: "#A7F3D0" } }, font: { color: "#065F46", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    hub_semantic: { ...BOX_PROPS, color: { background: "#F5F3FF", border: "#7C3AED", highlight: { border: "#4C1D95", background: "#DDD6FE" } }, font: { color: "#4C1D95", face: "JetBrains Mono", size: 11, bold: true }, borderWidth: 2 },
    leak: { ...BOX_PROPS, color: { background: "#FEF3C7", border: "#D97706", highlight: { border: "#B45309", background: "#FDE68A" } }, font: { color: "#92400E", face: "JetBrains Mono" } },
    leak_overflow: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono" } },
    breach: { ...BOX_PROPS, color: { background: "#FFE4E6", border: "#E11D48", highlight: { border: "#9F1239", background: "#FECDD3" } }, font: { color: "#9F1239", face: "JetBrains Mono" } },
    stealer: { ...BOX_PROPS, color: { background: "#FFE4E6", border: "#BE123C", highlight: { border: "#881337", background: "#FECDD3" } }, font: { color: "#881337", face: "JetBrains Mono" } },
    credential: { ...BOX_PROPS, color: { background: "#FEE2E2", border: "#DC2626", highlight: { border: "#991B1B", background: "#FECACA" } }, font: { color: "#991B1B", face: "JetBrains Mono" } },
    credentials: { ...BOX_PROPS, color: { background: "#FEE2E2", border: "#DC2626", highlight: { border: "#991B1B", background: "#FECACA" } }, font: { color: "#991B1B", face: "JetBrains Mono" } },
    physical: { ...BOX_PROPS, color: { background: "#D1FAE5", border: "#059669", highlight: { border: "#065F46", background: "#A7F3D0" } }, font: { color: "#065F46", face: "JetBrains Mono" } },
    relative: { ...BOX_PROPS, color: { background: "#EDE9FE", border: "#7C3AED", highlight: { border: "#5B21B6", background: "#DDD6FE" } }, font: { color: "#5B21B6", face: "JetBrains Mono" } },
    relatives: { ...BOX_PROPS, color: { background: "#EDE9FE", border: "#7C3AED", highlight: { border: "#5B21B6", background: "#DDD6FE" } }, font: { color: "#5B21B6", face: "JetBrains Mono" } },
    pivot: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono" } },
    pivots: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono" } },
    pivot_account: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono" } },
    pivot_semantic: { ...BOX_PROPS, color: { background: "#E0F2FE", border: "#0284C7", highlight: { border: "#0369A1", background: "#BAE6FD" } }, font: { color: "#0369A1", face: "JetBrains Mono" } },
    domain: { ...BOX_PROPS, color: { background: "#EDE9FE", border: "#7C3AED", highlight: { border: "#5B21B6", background: "#DDD6FE" } }, font: { color: "#5B21B6", face: "JetBrains Mono" } },
    subdomain: { ...BOX_PROPS, color: { background: "#EDE9FE", border: "#7C3AED", highlight: { border: "#5B21B6", background: "#DDD6FE" } }, font: { color: "#5B21B6", face: "JetBrains Mono" } },
    correlated_identity: { ...BOX_PROPS, color: { background: "#FFE4E6", border: "#E11D48", highlight: { border: "#9F1239", background: "#FECDD3" } }, font: { color: "#9F1239", face: "JetBrains Mono" } }
};

function isCurrentThemeLight() {
    return document.documentElement.classList.contains("light");
}

function getMapTileUrl(isLight) {
    return isLight 
        ? "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
}

function updateMapTheme(isLight) {
    if (window.geoMap && window.currentTileLayer) {
        try {
            window.geoMap.removeLayer(window.currentTileLayer);
            window.currentTileLayer = L.tileLayer(getMapTileUrl(isLight), {
                attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                subdomains: 'abcd',
                maxZoom: 20
            }).addTo(window.geoMap);
        } catch(e) {
            console.warn("Error updating map tile theme:", e);
        }
    }
}

function initTheme() {
    const saved = localStorage.getItem("breachspillover_theme");
    const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    const theme = saved || (prefersLight ? "light" : "dark");
    setTheme(theme, false);
    if (window.sfx) window.sfx.updateButtonUI();
}

function toggleTheme() {
    const next = isCurrentThemeLight() ? "dark" : "light";
    setTheme(next, true);
    showToast(`Switched to ${next.toUpperCase()} mode`, "info");
}

function setTheme(theme, persist = true) {
    const isLight = (theme === "light");
    const root = document.documentElement;
    
    if (isLight) {
        root.classList.remove("dark");
        root.classList.add("light");
        root.setAttribute("data-theme", "light");
    } else {
        root.classList.add("dark");
        root.classList.remove("light");
        root.setAttribute("data-theme", "dark");
    }

    if (persist) {
        try {
            localStorage.setItem("breachspillover_theme", theme);
        } catch (e) {}
    }

    // Update Header Button UI
    const btnText = document.getElementById("theme-toggle-text");
    const btnIcon = document.getElementById("theme-toggle-icon");
    if (btnText) {
        btnText.innerText = isLight ? "DARK" : "LIGHT";
    }
    if (btnIcon) {
        btnIcon.innerHTML = isLight
            ? `<svg class="theme-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
               </svg>`
            : `<svg class="theme-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
               </svg>`;
    }

    // Dynamically update active Vis.js network graph if mounted
    if (networkInstance) {
        try {
            networkInstance.setOptions({
                nodes: {
                    shadow: {
                        enabled: true,
                        color: isLight ? "rgba(15, 23, 42, 0.12)" : "rgba(0,0,0,0.5)",
                        size: 6,
                        x: 2,
                        y: 2
                    }
                },
                groups: isLight ? LIGHT_GRAPH_GROUPS : DARK_GRAPH_GROUPS,
                edges: {
                    color: isLight ? { color: "#94a3b8", highlight: "#0284c7", hover: "#0284c7" } : { color: "#384259", highlight: "#7dd3fc", hover: "#7dd3fc" }
                }
            });
        } catch(e) {
            console.warn("Network theme update error:", e);
        }
    }

    // Adapt Leaflet Map tile layer if mounted
    updateMapTheme(isLight);
}
window.initTheme = initTheme;
window.toggleTheme = toggleTheme;
window.setTheme = setTheme;
window.isCurrentThemeLight = isCurrentThemeLight;

/**
 * Platform string normalization helper
 * Ensures "Twitter / X", "x: @user", "twitter" uniformly resolve to "twitter"
 */
function normalizePlatform(platStr) {
    if (!platStr) return "";
    let s = platStr.toLowerCase().trim();
    if (s.includes("twitter") || s === "x" || s.startsWith("x:") || s.includes("twitter / x")) return "twitter";
    if (s.includes("spotify")) return "spotify";
    if (s.includes("github")) return "github";
    if (s.includes("gitlab")) return "gitlab";
    if (s.includes("chess")) return "chess.com";
    if (s.includes("steam")) return "steam";
    if (s.includes("roblox")) return "roblox";
    if (s.includes("reddit")) return "reddit";
    if (s.includes("gravatar")) return "gravatar";
    if (s.includes("telegram")) return "telegram";
    return s.split(":")[0].trim();
}

/**
 * Clean SVG micro-icons utility (Linear/Datadog aesthetic, eliminates platform emojis)
 */
function getUiIcon(name, extraClass = "") {
    const cls = extraClass || "w-3.5 h-3.5 inline-block align-middle";
    const icons = {
        globe: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>`,
        lock: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`,
        unlock: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg>`,
        search: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`,
        bolt: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>`,
        key: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-1.5 1.5L14 9l-1.5-1.5-2 2L12 11l-3 3-2-2-4 4a5 5 0 0 0 7 7l4-4-2-2 3-3 1.5 1.5 2-2L19 7.5 22 4.5 21 2z"></path></svg>`,
        shield: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`,
        shieldCheck: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><polyline points="9 12 11 14 15 10"></polyline></svg>`,
        user: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`,
        users: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`,
        mail: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>`,
        building: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="9" y1="22" x2="9" y2="22.01"></line><line x1="15" y1="22" x2="15" y2="22.01"></line><line x1="9" y1="6" x2="9" y2="6.01"></line><line x1="15" y1="6" x2="15" y2="6.01"></line><line x1="9" y1="10" x2="9" y2="10.01"></line><line x1="15" y1="10" x2="15" y2="10.01"></line><line x1="9" y1="14" x2="9" y2="14.01"></line><line x1="15" y1="14" x2="15" y2="14.01"></line><line x1="9" y1="18" x2="9" y2="18.01"></line><line x1="15" y1="18" x2="15" y2="18.01"></line></svg>`,
        mapPin: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`,
        cpu: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>`,
        settings: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
        check: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
        cross: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
        external: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`,
        copy: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`,
        refresh: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`,
        alert: `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
        github: `<svg class="${cls}" viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"></path></svg>`,
        facebook: `<svg class="${cls}" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>`,
        linkedin: `<svg class="${cls}" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>`
    };
    return icons[name] || "";
}


/**
 * Auto-detect input type (Email, Domain, Phone E.164, Hash MD5/SHA)
 */
function updateSearchInputTypeBadge() {
    const input = document.getElementById("search-input");
    const badge = document.getElementById("search-type-badge");
    if (!input || !badge) return;

    const val = input.value.trim();
    if (!val) {
        badge.className = "search-type-badge font-mono";
        badge.innerText = "[STANDBY: AUTO-DETECT]";
        return;
    }

    // 1. Hash detection: MD5 (32 hex), SHA-1 (40 hex), SHA-256 (64 hex)
    if (/^[a-fA-F0-9]{32}$/.test(val)) {
        badge.className = "search-type-badge type-hash font-mono";
        badge.innerText = "[HASH: MD5]";
        return;
    }
    if (/^[a-fA-F0-9]{40}$/.test(val)) {
        badge.className = "search-type-badge type-hash font-mono";
        badge.innerText = "[HASH: SHA-1]";
        return;
    }
    if (/^[a-fA-F0-9]{64}$/.test(val)) {
        badge.className = "search-type-badge type-hash font-mono";
        badge.innerText = "[HASH: SHA-256]";
        return;
    }

    // 2. Phone detection (starts with + or contains 7+ digits, no @, no letters)
    if (/^\+?[0-9\s\-\(\)\.]{7,22}$/.test(val) && (val.match(/\d/g) || []).length >= 7 && !/[a-zA-Z]/.test(val)) {
        badge.className = "search-type-badge type-phone font-mono";
        badge.innerText = "[TELECOM: E.164]";
        return;
    }

    // 3. Email detection
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
        badge.className = "search-type-badge type-email font-mono";
        badge.innerText = "[EMAIL TARGET]";
        return;
    }

    // 4. Domain detection (contains dot without @, or starts with @)
    if ((!val.includes("@") && val.includes(".")) || (val.startsWith("@") && val.includes("."))) {
        badge.className = "search-type-badge type-domain font-mono";
        badge.innerText = "[DOMAIN RECON]";
        return;
    }

    badge.className = "search-type-badge font-mono";
    badge.innerText = "[TARGET ID]";
}
window.updateSearchInputTypeBadge = updateSearchInputTypeBadge;

/**
 * Dense Summary Metrics Banner Calculation & Rendering
 */
function renderSummaryMetrics(data) {
    const banner = document.getElementById("summary-metrics-banner");
    if (!banner || !data) return;
    banner.style.display = "none";

    const leaks = data.leaks || [];
    const creds = data.credentials || [];
    const pivots = data.pivots || [];
    const footprints = data.physical_footprints || [];
    const relatives = data.relatives || [];

    // Calculate unique exposed IPs from leak artifacts and network pivots
    const ipsSet = new Set();
    leaks.forEach(l => {
        if (l.ip_address) ipsSet.add(l.ip_address);
        if (Array.isArray(l.exposed_data)) {
            l.exposed_data.forEach(d => {
                if (typeof d === "string" && (d.toLowerCase().includes("ip") || /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(d))) {
                    ipsSet.add(d);
                }
            });
        }
    });

    const breachesCount = leaks.length;
    const credsCount = creds.length;
    const ipsCount = ipsSet.size;
    const piiCount = footprints.length + relatives.length + pivots.filter(p => p.pivot_type === "PHONE" || p.pivot_type === "LOCATION" || p.pivot_type === "NATIONAL_ID").length;

    const breachesEl = document.getElementById("metric-breaches-count");
    const breachesBadge = document.getElementById("metric-breaches-badge");
    const passwordsEl = document.getElementById("metric-passwords-count");
    const ipsEl = document.getElementById("metric-ips-count");
    const piiEl = document.getElementById("metric-pii-count");

    if (breachesEl) {
        breachesEl.innerText = breachesCount;
        breachesEl.className = "metric-number " + (breachesCount > 0 ? "crit" : "safe");
    }
    if (breachesBadge) {
        const sev = data.spillover_score?.level || (breachesCount > 0 ? "CRITICAL" : "CLEAN");
        breachesBadge.innerText = sev;
        breachesBadge.className = "metric-subtag mono " + (breachesCount > 0 ? "text-red-400 border-red-900/50" : "text-emerald-400 border-emerald-900/50");
    }
    if (passwordsEl) {
        passwordsEl.innerText = credsCount;
        passwordsEl.className = "metric-number " + (credsCount > 0 ? "crit" : "safe");
    }
    if (ipsEl) {
        ipsEl.innerText = ipsCount;
    }
    if (piiEl) {
        piiEl.innerText = piiCount;
    }
}
window.renderSummaryMetrics = renderSummaryMetrics;

/**
 * Copy Formatted Incident Report
 */
function copyInvestigationReport() {
    if (!currentInvestigationData) {
        showToast("No active investigation to copy.", "warning");
        return;
    }
    const d = currentInvestigationData;
    const emp = d.employee || {};
    const score = d.spillover_score || {};
    const leaks = d.leaks || [];
    const creds = d.credentials || [];

    let report = `======================================================================\n`;
    report += `BREACHSPILLOVER // EXECUTIVE INCIDENT DOSSIER\n`;
    report += `======================================================================\n`;
    report += `Target Identifier : ${emp.full_name || 'N/A'} <${emp.corporate_email || currentEmail}>\n`;
    report += `Spillover Score   : ${score.score || 0}/100 [SEVERITY: ${score.level || 'CLEAN'}]\n`;
    report += `Audit Timestamp   : ${new Date().toISOString()}\n`;
    report += `Total Breaches    : ${leaks.length}\n`;
    report += `Compromised Creds : ${creds.length}\n\n`;

    report += `--- VERIFIED COMPROMISE DISCLOSURES ---\n`;
    if (leaks.length === 0) {
        report += `Zero verified breaches found across darknet threat corpora.\n`;
    } else {
        leaks.forEach((l, i) => {
            report += `[#${i+1}] ${l.leak_name || 'Unknown Incident'} (Date: ${l.breach_date || 'N/A'}, Type: ${l.leak_type || 'LEAK'})\n`;
            if (l.exposed_data && l.exposed_data.length) {
                report += `     Exposed Attributes: ${l.exposed_data.join(', ')}\n`;
            }
        });
    }

    report += `\n--- MITIGATION & REMEDIATION DIRECTIVES ---\n`;
    report += `1. Mandatory password reset on corporate SSO and primary webmail.\n`;
    report += `2. Enforce FIDO2 / WebAuthn hardware token authentication.\n`;
    report += `3. Invalidate active browser session cookies and OAuth third-party tokens.\n`;
    report += `======================================================================\n`;

    navigator.clipboard.writeText(report).then(() => {
        showActionTooltip("Incident Report Copied");
        showToast("Incident report copied to clipboard.", "success");
    }).catch(() => {
        showToast("Unable to copy to clipboard.", "error");
    });
}
window.copyInvestigationReport = copyInvestigationReport;

/**
 * Export Forensic JSON
 */
function exportInvestigationJSON() {
    if (!currentInvestigationData) {
        showToast("No active investigation to export.", "warning");
        return;
    }
    const payload = JSON.stringify(currentInvestigationData, null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const targetSlug = (currentEmail || "target").replace(/[^a-zA-Z0-9]/g, "_");
    a.href = url;
    a.download = `breach_intel_${targetSlug}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showActionTooltip("JSON Exported");
    showToast("Forensic JSON exported successfully.", "success");
}
window.exportInvestigationJSON = exportInvestigationJSON;

/**
 * Export Executive PDF Report
 */
function exportInvestigationPDF() {
    if (!currentInvestigationData) {
        showToast("No active investigation to export.", "warning");
        return;
    }
    
    showToast("Generating Executive PDF Report...", "info");
    
    // We will clone the target-exposure-card and the results-findings-grid to generate a clean PDF
    const bentoCard = document.getElementById("target-exposure-card");
    if (!bentoCard) return;

    // Create a temporary container for the PDF content
    const printContainer = document.createElement("div");
    printContainer.style.padding = "20px";
    printContainer.style.backgroundColor = "#0E1117";
    printContainer.style.color = "#E2E8F0";
    printContainer.style.fontFamily = "Geist, sans-serif";
    
    // Add header
    const header = document.createElement("div");
    header.innerHTML = `
        <h1 style="color: #EF4444; margin-bottom: 5px; font-family: monospace; font-size: 24px;">BREACH SPILLOVER // EXECUTIVE BRIEF</h1>
        <div style="font-family: monospace; font-size: 12px; color: #94A3B8; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #334155;">
            CONFIDENTIAL DIGITAL EXPOSURE REPORT - ${new Date().toISOString()}
        </div>
    `;
    printContainer.appendChild(header);
    
    // Clone bento card content
    const clonedCard = bentoCard.cloneNode(true);
    // Remove inline styles that might break print
    clonedCard.style.display = "block";
    clonedCard.style.border = "none";
    clonedCard.style.boxShadow = "none";
    
    printContainer.appendChild(clonedCard);

    const targetSlug = (currentEmail || "target").replace(/[^a-zA-Z0-9]/g, "_");
    
    const opt = {
        margin:       10,
        filename:     `executive_brief_${targetSlug}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, logging: false },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // Use html2pdf
    html2pdf().set(opt).from(printContainer).save().then(() => {
        showActionTooltip("PDF Exported");
        showToast("Executive PDF Report generated successfully.", "success");
    });
}
window.exportInvestigationPDF = exportInvestigationPDF;

/**
 * Export Comprehensive Forensic CSV Ledger
 */
function exportInvestigationCSV() {
    if (!currentInvestigationData) {
        showToast("No active investigation to export.", "warning");
        return;
    }
    if (window.sfx) window.sfx.playSelect();

    const d = currentInvestigationData;
    const emp = d.employee || {};
    const leaks = d.leaks || [];
    const creds = d.credentials || [];
    const pivots = d.pivots || [];
    const foot = d.footprints || [];

    const escapeCsv = (str) => {
        if (str === null || str === undefined) return '""';
        const val = String(str).replace(/"/g, '""');
        return `"${val}"`;
    };

    let csv = [];
    csv.push(["BREACH SPILLOVER - CYBER THREAT FORENSIC AUDIT LEDGER"]);
    csv.push([`Export Timestamp: ${new Date().toISOString()}`]);
    csv.push([]);
    
    // Target Overview
    csv.push(["=== TARGET PROFILE ==="]);
    csv.push(["Target Name", "Target Email", "Risk Score", "Risk Tier", "Total Leaks", "Credentials", "Verified Pivots"]);
    csv.push([
        escapeCsv(emp.full_name || "N/A"),
        escapeCsv(emp.corporate_email || currentEmail),
        escapeCsv(d.risk_score || 0),
        escapeCsv(d.severity || "CLEAN"),
        escapeCsv(leaks.length),
        escapeCsv(creds.length),
        escapeCsv(pivots.length)
    ]);
    csv.push([]);

    // Leaks
    csv.push(["=== EXFILTRATED BREACHES & STEALER LOGS ==="]);
    csv.push(["Incident Name", "Breach Date", "Category / Type", "Severity", "Compromised Domain", "Threat Actor Source"]);
    leaks.forEach(l => {
        csv.push([
            escapeCsv(l.leak_name),
            escapeCsv(l.breach_date || "N/A"),
            escapeCsv(l.leak_type || "BREACH"),
            escapeCsv(l.severity || "HIGH"),
            escapeCsv(l.compromised_domain || "N/A"),
            escapeCsv(l.threat_actor_source || "Dark Web Repository")
        ]);
    });
    csv.push([]);

    // Credentials
    csv.push(["=== COMPROMISED CREDENTIALS & HASHES ==="]);
    csv.push(["Username / Identity", "Plaintext Password", "Password Hash", "Pattern Complexity", "Compromised Domain", "Corporate Match"]);
    creds.forEach(c => {
        csv.push([
            escapeCsv(c.username_or_email),
            escapeCsv(c.plaintext_password || "[HASH ONLY]"),
            escapeCsv(c.password_hash || "N/A"),
            escapeCsv(c.password_pattern || "N/A"),
            escapeCsv(c.domain_compromised || "N/A"),
            escapeCsv(c.is_corporate_password_match ? "CRITICAL MATCH" : "NO")
        ]);
    });
    csv.push([]);

    // Pivots
    csv.push(["=== VERIFIED OSINT PROFILES & PIVOTS ==="]);
    csv.push(["Pivot Type", "Pivot Value", "Confidence Score", "Status", "Context / Provenance Note"]);
    pivots.forEach(p => {
        csv.push([
            escapeCsv(p.pivot_type),
            escapeCsv(p.pivot_value),
            escapeCsv(p.confidence_score || 1.0),
            escapeCsv(p.confidence_score >= 0.85 ? "VERIFIED" : "SUSPECTED"),
            escapeCsv(p.context_note || "Public Enumeration")
        ]);
    });
    csv.push([]);

    // Geospatial Footprints
    csv.push(["=== GEOSPATIAL & RESIDENTIAL FOOTPRINTS ==="]);
    csv.push(["IP Address", "City", "Country", "ISP / Organization", "Latitude", "Longitude"]);
    foot.forEach(f => {
        csv.push([
            escapeCsv(f.ip_address || "N/A"),
            escapeCsv(f.city || "N/A"),
            escapeCsv(f.country || "N/A"),
            escapeCsv(f.isp || "N/A"),
            escapeCsv(f.latitude || "N/A"),
            escapeCsv(f.longitude || "N/A")
        ]);
    });

    const csvContent = csv.map(row => row.join(",")).join("\r\n");
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const targetSlug = (currentEmail || "target").replace(/[^a-zA-Z0-9]/g, "_");
    a.href = url;
    a.download = `breach_investigation_${targetSlug}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showActionTooltip("CSV Exported");
    showToast("Forensic CSV Ledger exported successfully.", "success");
}
window.exportInvestigationCSV = exportInvestigationCSV;

/**
 * Export Microsoft Word Compatible (.doc) Executive Dossier
 */
function exportInvestigationDOC() {
    if (!currentInvestigationData) {
        showToast("No active investigation to export.", "warning");
        return;
    }
    if (window.sfx) window.sfx.playSelect();

    const d = currentInvestigationData;
    const emp = d.employee || {};
    const leaks = d.leaks || [];
    const creds = d.credentials || [];
    const pivots = d.pivots || [];
    const targetSlug = (currentEmail || "target").replace(/[^a-zA-Z0-9]/g, "_");

    const htmlContent = `
        <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
        <head>
            <meta charset='utf-8'>
            <title>BreachSpillover Forensic Report</title>
            <style>
                body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; margin: 40px; color: #1e293b; line-height: 1.5; }
                h1 { color: #dc2626; font-size: 24pt; border-bottom: 2pt solid #dc2626; padding-bottom: 6px; }
                h2 { color: #0284c7; font-size: 16pt; margin-top: 24px; border-bottom: 1pt solid #cbd5e1; padding-bottom: 4px; }
                .confidential { background-color: #fee2e2; color: #991b1b; padding: 8px 12px; font-weight: bold; border-left: 4pt solid #dc2626; margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 20px; font-size: 10pt; }
                th { background-color: #0f172a; color: #f8fafc; text-align: left; padding: 8px; border: 1pt solid #334155; }
                td { padding: 8px; border: 1pt solid #cbd5e1; vertical-align: top; }
                tr:nth-child(even) td { background-color: #f8fafc; }
                .badge-crit { background: #fee2e2; color: #b91c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px; }
                .mono { font-family: 'Consolas', 'Courier New', monospace; font-size: 9.5pt; }
                .footer { margin-top: 40px; font-size: 8pt; color: #64748b; border-top: 1pt solid #cbd5e1; padding-top: 8px; }
            </style>
        </head>
        <body>
            <div class="confidential">RESTRICTED // CYBER THREAT INTELLIGENCE DOSSIER // CONFIDENTIAL</div>
            <h1>BREACH SPILLOVER &mdash; EXECUTIVE REPORT</h1>
            <p><strong>Investigation Target:</strong> ${escapeHtml(emp.full_name || currentEmail)} &lt;${escapeHtml(emp.corporate_email || currentEmail)}&gt;<br>
            <strong>Generated At:</strong> ${new Date().toUTCString()}<br>
            <strong>Overall Risk Exposure Score:</strong> <span class="badge-crit">${d.risk_score || 0} / 100 &mdash; ${d.severity || "EVALUATED"}</span></p>

            <h2>1. Target Profile Telemetry</h2>
            <table>
                <tr><th>Attribute</th><th>Value</th><th>Classification</th></tr>
                <tr><td>Full Name</td><td>${escapeHtml(emp.full_name || "N/A")}</td><td>Verified Target</td></tr>
                <tr><td>Primary Email</td><td class="mono">${escapeHtml(emp.corporate_email || currentEmail)}</td><td>Primary Identifier</td></tr>
                <tr><td>Role / Title</td><td>${escapeHtml(emp.job_title || "Individual / Target User")}</td><td>Identity Profile</td></tr>
                <tr><td>Department / Organization</td><td>${escapeHtml(emp.department || "Public Web")}</td><td>Affiliation</td></tr>
            </table>

            <h2>2. Exfiltrated Breaches & Stealer Logs (${leaks.length} Incidents)</h2>
            <table>
                <tr><th>Incident</th><th>Date</th><th>Type</th><th>Severity</th><th>Compromised Domain</th></tr>
                ${leaks.map(l => `
                    <tr>
                        <td><strong>${escapeHtml(l.leak_name)}</strong></td>
                        <td>${escapeHtml(l.breach_date || "N/A")}</td>
                        <td>${escapeHtml(l.leak_type || "BREACH")}</td>
                        <td><span class="badge-crit">${escapeHtml(l.severity || "HIGH")}</span></td>
                        <td class="mono">${escapeHtml(l.compromised_domain || "N/A")}</td>
                    </tr>
                `).join("")}
            </table>

            <h2>3. Compromised Credentials & Password Hashes (${creds.length} Records)</h2>
            <table>
                <tr><th>Identity</th><th>Password / Dump Content</th><th>Hash</th><th>Domain</th><th>Corporate Match</th></tr>
                ${creds.map(c => `
                    <tr>
                        <td class="mono">${escapeHtml(c.username_or_email)}</td>
                        <td class="mono">${escapeHtml(c.plaintext_password || "[HASH STORED]")}</td>
                        <td class="mono" style="word-break: break-all;">${escapeHtml(c.password_hash || "N/A")}</td>
                        <td>${escapeHtml(c.domain_compromised || "N/A")}</td>
                        <td>${c.is_corporate_password_match ? "<strong style='color:red;'>CRITICAL MATCH</strong>" : "None"}</td>
                    </tr>
                `).join("")}
            </table>

            <h2>4. Corroborated OSINT Footprints & Accounts (${pivots.length} Entities)</h2>
            <table>
                <tr><th>Type</th><th>Platform / Handle / Value</th><th>Status</th><th>Context Details</th></tr>
                ${pivots.map(p => `
                    <tr>
                        <td>${escapeHtml(p.pivot_type)}</td>
                        <td class="mono"><strong>${escapeHtml(p.pivot_value)}</strong></td>
                        <td>${p.confidence_score >= 0.85 ? "VERIFIED" : "SUSPECTED"}</td>
                        <td>${escapeHtml(p.context_note || "Public OSINT Verification")}</td>
                    </tr>
                `).join("")}
            </table>

            <div class="footer">
                Report generated automatically by BreachSpillover CTI Platform &bull; ${new Date().toISOString()} &bull; Strictly for authorized forensic evaluation.
            </div>
        </body>
        </html>
    `;

    const blob = new Blob(['\ufeff', htmlContent], {
        type: 'application/msword'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `breach_dossier_${targetSlug}.doc`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showActionTooltip("Word DOC Exported");
    showToast("Executive Word Dossier (.doc) exported successfully.", "success");
}
window.exportInvestigationDOC = exportInvestigationDOC;

/* ==========================================================================
   DEFENSIVE EXPOSURE REPORT
   Purpose: "What exposure associated with this email can an authorized user
   see from the application's legitimate breach and public OSINT sources?"
   NOT a dossier. The model is built by ACTIVELY ALLOWLISTING non-sensitive
   fields — it never copies currentInvestigationData, so credentials,
   addresses, coordinates, relatives, phone numbers and social-engineering
   scores can never leak into an export even if added upstream later.
   ========================================================================== */
const EXPOSURE_REPORT_VERSION = "1.0";

function buildExposureReport(data, wmnResults) {
    data = data || {};
    const emp = data.employee || {};
    const nowIso = new Date().toISOString();
    const sources = [];
    const seenSources = new Set();
    const addSource = (name, type, url) => {
        if (!name) return;
        const dedupe = `${name}|${url || ""}`;
        if (seenSources.has(dedupe)) return;
        seenSources.add(dedupe);
        const s = { name: String(name), type: type || "unknown" };
        if (url) s.url = String(url);
        sources.push(s);
    };

    // --- Breach exposure: category-level breach metadata only (no cred values) ---
    const breachExposure = (Array.isArray(data.leaks) ? data.leaks : []).map(l => {
        const exposed = Array.isArray(l.exposed_data)
            ? l.exposed_data.filter(x => typeof x === "string")
            : [];
        const provenance = l.threat_actor_source || null;
        if (provenance) addSource(provenance, "breach-source", null);
        return {
            name: l.leak_name || "Unknown Breach",
            date: l.breach_date || null,
            type: l.leak_type || null,
            severity: l.severity || null,
            exposedDataTypes: exposed,
            source: provenance,
            description: typeof l.description === "string" ? l.description : null
        };
    });

    // --- Public account presence: only confirmed WhatsMyName matches ---
    const matches = (wmnResults && Array.isArray(wmnResults.matches)) ? wmnResults.matches : [];
    const publicAccounts = matches.map(m => {
        if (m.url) addSource(m.platform || "WhatsMyName", "public-account", m.url);
        return {
            platform: m.platform || "Unknown",
            category: m.category || null,
            exists: true,
            profileUrl: m.url || null,
            confidence: typeof m.confidence_score === "number" ? m.confidence_score : null,
            source: "WhatsMyName"
        };
    });

    // --- Subject: investigation identifier(s) only, no discovered PII ---
    const subject = { email: emp.corporate_email || currentEmail || null };
    if (wmnResults && wmnResults.handle) subject.handle = String(wmnResults.handle);

    return {
        subject,
        breachExposure,
        publicAccounts,
        sources,
        metadata: {
            generatedAt: nowIso,
            reportVersion: EXPOSURE_REPORT_VERSION,
            application: "BreachSpillover",
            queryIdentifier: subject.email,
            scope: "defensive-exposure-only",
            breachCount: breachExposure.length,
            publicAccountCount: publicAccounts.length
        }
    };
}
window.buildExposureReport = buildExposureReport;

function exposureReportToMarkdown(report) {
    const lines = [];
    lines.push(`# Defensive Exposure Report`);
    lines.push("");
    lines.push(`**Subject:** ${report.subject.email || "N/A"}` + (report.subject.handle ? ` (handle: ${report.subject.handle})` : ""));
    lines.push(`**Generated:** ${report.metadata.generatedAt}`);
    lines.push(`**Report version:** ${report.metadata.reportVersion} · **Scope:** ${report.metadata.scope}`);
    lines.push("");
    lines.push(`## Breach Exposure (${report.breachExposure.length})`);
    if (!report.breachExposure.length) {
        lines.push("_No breach exposure returned by the application's legitimate sources._");
    } else {
        report.breachExposure.forEach(b => {
            lines.push(`- **${b.name}**` + (b.date ? ` — ${b.date}` : "") + (b.type ? ` [${b.type}]` : "") + (b.severity ? ` (${b.severity})` : ""));
            if (b.exposedDataTypes.length) lines.push(`  - Exposed data categories: ${b.exposedDataTypes.join(", ")}`);
            if (b.source) lines.push(`  - Source: ${b.source}`);
        });
    }
    lines.push("");
    lines.push(`## Public Account Presence (${report.publicAccounts.length})`);
    if (!report.publicAccounts.length) {
        lines.push("_No public accounts confirmed (run a WhatsMyName scan to enrich)._");
    } else {
        report.publicAccounts.forEach(a => {
            lines.push(`- **${a.platform}**` + (a.category ? ` [${a.category}]` : "") + (a.profileUrl ? ` — ${a.profileUrl}` : ""));
        });
    }
    lines.push("");
    lines.push(`## Sources (${report.sources.length})`);
    if (!report.sources.length) {
        lines.push("_None recorded._");
    } else {
        report.sources.forEach(s => lines.push(`- ${s.name} (${s.type})` + (s.url ? ` — ${s.url}` : "")));
    }
    lines.push("");
    lines.push(`---`);
    lines.push(`_Defensive exposure summary. Excludes credentials, residential/geolocation data, phone numbers, and relatives by design._`);
    return lines.join("\n");
}

function sanitizeFilenamePart(str) {
    return String(str || "target")
        .replace(/[^a-zA-Z0-9._-]/g, "_")   // strip path/traversal/unsafe chars
        .replace(/_+/g, "_")
        .replace(/^[._]+|[._]+$/g, "")
        .slice(0, 60) || "target";
}

function downloadBlob(content, mime, filename) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function exportExposureReport(format) {
    playSound("click");
    if (!currentInvestigationData) {
        showToast("No active investigation to export.", "warning");
        return;
    }
    try {
        const report = buildExposureReport(currentInvestigationData, currentWMNResults);
        if (!report.breachExposure.length && !report.publicAccounts.length) {
            showToast("No exposure findings available to export yet.", "warning");
            return;
        }
        const datePart = new Date().toISOString().slice(0, 10);
        const slug = sanitizeFilenamePart(report.subject.email);
        if (format === "md") {
            downloadBlob(exposureReportToMarkdown(report), "text/markdown;charset=utf-8", `exposure_report_${slug}_${datePart}.md`);
        } else {
            downloadBlob(JSON.stringify(report, null, 2), "application/json", `exposure_report_${slug}_${datePart}.json`);
        }
        showActionTooltip("Exposure Report Exported");
        showToast(`Defensive exposure report exported (${(format === "md" ? "Markdown" : "JSON")}).`, "success");
        playSound("export");
    } catch (err) {
        console.error("Exposure export failed:", err);
        showToast("Exposure report export failed: " + (err.message || err), "error");
    }
}
window.exportExposureReport = exportExposureReport;

/**
 * Action Tooltip Notification Helper
 */
function showActionTooltip(text) {
    const tooltip = document.getElementById("summary-action-tooltip");
    if (!tooltip) return;
    tooltip.innerText = text;
    tooltip.classList.add("show");
    setTimeout(() => {
        tooltip.classList.remove("show");
    }, 2200);
}
window.showActionTooltip = showActionTooltip;

/**
 * Toggle Expandable Breach Drawer Accordion
 */
function toggleBreachDrawer(drawerId) {
    const drawer = document.getElementById("drawer-" + drawerId);
    const row = document.getElementById("row-" + drawerId);
    const btn = document.getElementById("btn-expand-" + drawerId);
    if (!drawer) return;
    const isHidden = drawer.style.display === "none";
    drawer.style.display = isHidden ? "table-row" : "none";
    if (row) {
        if (isHidden) row.classList.add("expanded");
        else row.classList.remove("expanded");
    }
    if (btn) {
        btn.innerText = isHidden ? "[CLOSE ▴]" : "[INSPECT ▾]";
    }
}
window.toggleBreachDrawer = toggleBreachDrawer;

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    initTheme();
    SoundManager.updateButtonUI();
    setupEventListeners();
    updateSearchInputTypeBadge();
    await loadGlobalStats();
    initStandbyState();
    updateDeclassifyStatusBadge();
    await checkServerAIStatus();
    const bridge = await checkBridgeStatus();
    if (!bridge || !bridge.authenticated) {
        openBridgeModal("startup");
    }
}

function setupEventListeners() {
    // Search input Enter key & dynamic detection
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                triggerSearch();
            }
        });
        searchInput.addEventListener("input", updateSearchInputTypeBadge);
        searchInput.addEventListener("focus", updateSearchInputTypeBadge);
    }

    // Global keyboard shortcut: Cmd+K / Ctrl+K
    document.addEventListener("keydown", (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            const sInput = document.getElementById("search-input");
            if (sInput) {
                sInput.focus();
                sInput.select();
            }
        }
    });

    // Search form submission
    const searchForm = document.getElementById("search-form");
    if (searchForm) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            triggerSearch();
        });
    }

    // Modal close on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeDeclassifyModal();
            closeBatchModal();
            closeDomainReconModal();
            closeAISettingsModal();
            if (typeof closeCombolistModal === "function") closeCombolistModal();
            if (typeof closeReversePhoneModal === "function") closeReversePhoneModal();
            if (typeof closeImageCorrelationModal === "function") closeImageCorrelationModal();
        }
    });

    // Evidence Tabs Navigation
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            playSound("click");
            tabBtns.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add("active");
            }
            if (targetId === "tab-physical" && window.geoMap) {
                setTimeout(() => window.geoMap.invalidateSize(), 50);
            }
            if (targetId === "tab-ai" && currentInvestigationData) {
                renderAITab(currentInvestigationData);
            }
            if (targetId === "tab-wmn" && currentInvestigationData) {
                renderWMNTab(currentInvestigationData);
            }
            if (targetId === "tab-pastes" && currentInvestigationData) {
                renderPastesTab(currentInvestigationData);
            }
            if (targetId === "tab-images" && currentInvestigationData) {
                renderImageCorrelationTab(currentInvestigationData);
            }
            if (targetId === "tab-telecom" && currentInvestigationData) {
                renderTelecomTab(currentInvestigationData);
            }
        });
    });

    // Graph Controls
    const btnFit = document.getElementById("btn-graph-fit");
    if (btnFit) {
        btnFit.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            if (networkInstance) networkInstance.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        });
    }

    const btnZoomIn = document.getElementById("btn-graph-zoomin");
    if (btnZoomIn) {
        btnZoomIn.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            if (networkInstance) {
                const scale = networkInstance.getScale() * 1.3;
                networkInstance.moveTo({ scale: scale, animation: { duration: 200 } });
            }
        });
    }

    const btnZoomOut = document.getElementById("btn-graph-zoomout");
    if (btnZoomOut) {
        btnZoomOut.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            if (networkInstance) {
                const scale = networkInstance.getScale() * 0.75;
                networkInstance.moveTo({ scale: scale, animation: { duration: 200 } });
            }
        });
    }

    const btnTidy = document.getElementById("btn-graph-tidy");
    if (btnTidy) {
        btnTidy.addEventListener("click", () => {
            tidyGraphConcentric();
        });
    }

    const btnLayout = document.getElementById("btn-graph-layout");
    if (btnLayout) {
        btnLayout.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            isHierarchicalView = !isHierarchicalView;
            btnLayout.innerHTML = isHierarchicalView ? "[ORGANIC_VIEW]" : "[TREE_VIEW]";
            showToast(isHierarchicalView ? "Switched to hierarchical attack flow." : "Switched to organic physics layout.", "info");
            if (currentInvestigationData && currentInvestigationData.graph) {
                renderGraph(currentInvestigationData.graph);
            }
        });
    }

    const btnPhysics = document.getElementById("btn-graph-physics");
    if (btnPhysics) {
        btnPhysics.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            isPhysicsEnabled = !isPhysicsEnabled;
            btnPhysics.innerHTML = isPhysicsEnabled ? "[PHYSICS: ON]" : "[PHYSICS: OFF]";
            if (networkInstance) {
                networkInstance.setOptions({ physics: { enabled: isPhysicsEnabled } });
            }
        });
    }

    // Fullscreen Toggle for Spillover Graph
    const btnFullscreen = document.getElementById("btn-graph-fullscreen");
    const graphPanel = document.querySelector(".graph-panel");

    function updateFullscreenUI(isFullscreen) {
        if (btnFullscreen) {
            btnFullscreen.innerHTML = isFullscreen ? "[EXIT FULLSCREEN]" : "[FULLSCREEN]";
            btnFullscreen.setAttribute("title", isFullscreen ? "Exit Fullscreen View (Esc)" : "Toggle Fullscreen Graph View (Esc to exit)");
            btnFullscreen.style.color = isFullscreen ? "#f43f5e" : "#38bdf8";
            btnFullscreen.style.borderColor = isFullscreen ? "rgba(244, 63, 94, 0.4)" : "rgba(56, 189, 248, 0.4)";
        }
        if (graphPanel) {
            graphPanel.classList.toggle("graph-panel-fullscreen", isFullscreen);
        }
        if (networkInstance) {
            setTimeout(() => {
                networkInstance.setSize("100%", "100%");
                networkInstance.fit({ animation: { duration: 300, easingFunction: "easeInOutQuad" } });
            }, 80);
        }
    }

    if (btnFullscreen && graphPanel) {
        btnFullscreen.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            const isCurrentlyFullscreen = graphPanel.classList.contains("graph-panel-fullscreen") || document.fullscreenElement === graphPanel;
            if (!isCurrentlyFullscreen) {
                if (graphPanel.requestFullscreen) {
                    graphPanel.requestFullscreen().then(() => {
                        updateFullscreenUI(true);
                    }).catch(() => {
                        updateFullscreenUI(true);
                    });
                } else {
                    updateFullscreenUI(true);
                }
            } else {
                if (document.fullscreenElement) {
                    document.exitFullscreen().catch(() => {});
                }
                updateFullscreenUI(false);
            }
        });

        document.addEventListener("fullscreenchange", () => {
            const isNative = document.fullscreenElement === graphPanel;
            if (!isNative && graphPanel.classList.contains("graph-panel-fullscreen")) {
                updateFullscreenUI(false);
            }
        });

        window.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && graphPanel.classList.contains("graph-panel-fullscreen")) {
                if (document.fullscreenElement) {
                    document.exitFullscreen().catch(() => {});
                }
                updateFullscreenUI(false);
            }
        });
    }

    // Close Inspector Drawer
    const btnCloseInspector = document.getElementById("close-inspector");
    if (btnCloseInspector) {
        btnCloseInspector.addEventListener("click", () => {
            if (window.sfx) window.sfx.playSelect();
            const drawer = document.getElementById("node-inspector");
            if (drawer) drawer.style.display = "none";
        });
    }
}

// Deep Dive Reconnaissance Anchors Toggle
function toggleExtraIntelFields() {
    const checkbox = document.getElementById("toggle-extra-intel");
    const panel = document.getElementById("extra-intel-panel");
    if (panel && checkbox) {
        panel.style.display = checkbox.checked ? "block" : "none";
        if (checkbox.checked) {
            const nameInput = document.getElementById("anchor-name");
            if (nameInput) nameInput.focus();
        }
    }
}
window.toggleExtraIntelFields = toggleExtraIntelFields;

// Security Declassification Passcode Handlers (Disabled - Unlocked Mode Active)
function openDeclassifyModal() {}
window.openDeclassifyModal = openDeclassifyModal;

function closeDeclassifyModal() {}
window.closeDeclassifyModal = closeDeclassifyModal;

function handleModalBackdropClick(e) {}
window.handleModalBackdropClick = handleModalBackdropClick;

function togglePasscodeVisibility() {}
window.togglePasscodeVisibility = togglePasscodeVisibility;

async function submitDeclassifyPasscode() {}
window.submitDeclassifyPasscode = submitDeclassifyPasscode;

function handleDeclassifyToggle() {}
window.handleDeclassifyToggle = handleDeclassifyToggle;

function relockIntel() {}
window.relockIntel = relockIntel;

function updateDeclassifyStatusBadge() {}
window.updateDeclassifyStatusBadge = updateDeclassifyStatusBadge;

function handleFindingCardClick(cardType) {
    const tabMap = {
        creds: "tab-creds",
        address: "tab-physical",
        phone: "tab-pivots",
        relative: "tab-physical",
        pivots: "tab-pivots",
        workplace: "tab-pivots"
    };
    const targetTab = tabMap[cardType];
    if (targetTab) {
        const btn = document.querySelector(`.tab-btn[data-tab="${targetTab}"]`);
        if (btn) btn.click();
        if (cardType === "workplace") {
            setTimeout(() => {
                if (typeof window.filterPivotCategory === "function") {
                    window.filterPivotCategory("business");
                }
            }, 60);
        } else if (cardType === "phone") {
            setTimeout(() => {
                if (typeof window.filterPivotCategory === "function") {
                    window.filterPivotCategory("identity");
                }
            }, 60);
        }
    }
}
window.handleFindingCardClick = handleFindingCardClick;

/**
 * Clean standby state on initial load
 */
function initStandbyState() {
    const cleanBox = document.getElementById("clean-status-box");
    const targetCard = document.getElementById("target-exposure-card");
    const warningBox = document.getElementById("domain-warning-box");
    const standbyBox = document.getElementById("standby-status-box");
    const summaryBanner = document.getElementById("summary-metrics-banner");

    if (cleanBox) cleanBox.style.display = "none";
    if (targetCard) targetCard.style.display = "none";
    if (warningBox) warningBox.style.display = "none";
    if (standbyBox) standbyBox.style.display = "flex";
    if (summaryBanner) summaryBanner.style.display = "none";

    const tabIds = [
        "tab-leaks-content", 
        "tab-creds-content", 
        "tab-pivots-content", 
        "tab-suspected-content",
        "tab-physical-content", 
        "tab-provenance-content", 
        "tab-playbook-content",
        "tab-remediations-content",
        "tab-timeline-content"
    ];
    tabIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = `<div class="empty-tab-notice mono">[STANDBY] Awaiting target query submission.</div>`;
    });

    const suspectedCountBadge = document.getElementById("count-suspected");
    if (suspectedCountBadge) {
        suspectedCountBadge.innerText = "0";
    }

    const networkGraph = document.getElementById("network-graph");
    if (networkGraph) {
        networkGraph.innerHTML = `
            <div class="graph-standby-placeholder">
                <div class="standby-glyph">⬡</div>
                <div class="standby-title">Identity Exposure Graph Standby</div>
                <div class="standby-desc">Enter any email address above or click the example target to correlate multi-source attack chains.</div>
            </div>
        `;
    }
}

/**
 * Load the example target incident
 */
function loadExampleTarget(email) {
    const targetEmail = email || "test@gmail.com";
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.value = targetEmail;
        updateSearchInputTypeBadge();
    }
    currentEmail = targetEmail;
    routeInvestigationWithBridgeCheck(targetEmail);
    showToast(`Loaded live OSINT specimen: ${targetEmail}`, "info");
}
window.loadExampleTarget = loadExampleTarget;
window.loadDemoProfile = () => loadExampleTarget("test@gmail.com");

/**
 * Handle manual user search
 */
function triggerSearch() {
    const searchInput = document.getElementById("search-input");
    const rawVal = searchInput ? searchInput.value.trim() : "";
    if (!rawVal) {
        showToast("Please enter an email address, domain, phone, or hash.", "warning");
        if (searchInput) searchInput.focus();
        return;
    }
    playSound("click");

    // Check if input is a cryptographic hash (MD5, SHA-1, SHA-256)
    if (/^[a-fA-F0-9]{32}$|^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$/.test(rawVal)) {
        showToast(`Resolving cryptographic hash [${rawVal.substring(0, 8)}...]`, "info");
        fetch(`/api/hash/resolve?hash=${encodeURIComponent(rawVal)}`)
            .then(r => r.json())
            .then(data => {
                if (data.resolved && data.plaintext) {
                    showToast(`Cracked: ${data.plaintext} (${data.source || 'Rainbow Table'})`, "success");
                    const drawer = document.getElementById("node-inspector");
                    const titleEl = document.getElementById("inspector-node-title");
                    const bodyEl = document.getElementById("inspector-node-body");
                    if (drawer && bodyEl) {
                        if (titleEl) titleEl.innerText = "Hash Cracked: " + (data.algorithm || "MD5");
                        bodyEl.innerHTML = `
                            <div style="padding: 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; margin-bottom: 0.8rem;">
                                <div style="color: var(--accent-emerald); font-weight: 700; font-size: 0.8rem;">RAINBOW TABLE RESOLUTION: SUCCESS</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: var(--t-primary); margin-top: 0.4rem; font-family: monospace;">${escapeHtml(data.plaintext)}</div>
                                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.4rem;">Hash: <span class="mono">${escapeHtml(rawVal)}</span></div>
                                <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 0.2rem;">Source: ${escapeHtml(data.source || 'Rainbow Table')} | Time: ${data.crack_time_seconds || 0.01}s</div>
                            </div>
                            <button type="button" class="btn-primary w-full py-2 px-3 text-xs mono" style="background: linear-gradient(135deg, #0284c7, #38bdf8); color: #04131f; font-weight: 700; border: none; cursor: pointer; border-radius: 4px;" onclick="pivotOnEntity('CREDENTIAL', '${escapeHtml(data.plaintext)}')">
                                [SEARCH TARGETS USING THIS PASSWORD]
                            </button>
                        `;
                        drawer.style.display = "flex";
                    }
                } else {
                    showToast(data.reason || "Hash not found in public tables.", "info");
                }
            })
            .catch(err => showToast("Hash resolution error: " + err.message, "error"));
        return;
    }

    // Check if input is a phone number (E.164 / digits)
    if (/^\+?[0-9\s\-\(\)\.]{7,22}$/.test(rawVal) && (rawVal.match(/\d/g) || []).length >= 7 && !/[a-zA-Z]/.test(rawVal)) {
        showToast(`Querying telecom directory on: ${rawVal}`, "info");
        fetch(`/api/recon/telecom?query=${encodeURIComponent(rawVal)}`)
            .then(r => r.json())
            .then(res => {
                if (res.e164_formatted || res.carrier) {
                    showToast(`Telecom Line: ${res.e164_formatted || rawVal} | Carrier: ${res.carrier || 'Detected'}`, "success");
                }
            })
            .catch(() => {});
    }

    // Check if input is a domain (e.g. cybercorp.io, @cybercorp.io, spotify.com)
    if ((!rawVal.includes("@") && rawVal.includes(".")) || (rawVal.startsWith("@") && rawVal.includes("."))) {
        const domain = rawVal.replace(/^@/, "").trim();
        executeDomainRecon(domain);
        return;
    }

    // Composite query decomposition: detect combined queries like "Amir Secic 3gbxdd@gmail.com"
    const emailMatch = rawVal.match(/[\w\.-]+@[\w\.-]+\.\w+/);
    if (emailMatch) {
        const extractedEmail = emailMatch[0].toLowerCase();
        const remainder = rawVal.replace(emailMatch[0], "").replace(/[()<>,;:\[\]"']/g, " ").trim();
        if (remainder && remainder.length >= 2 && /[a-zA-Z]/.test(remainder)) {
            const anchorNameInput = document.getElementById("anchor-name");
            if (anchorNameInput && (!anchorNameInput.value || anchorNameInput.value.trim() === "")) {
                anchorNameInput.value = remainder;
                showToast(`Anchor Detected: Name [${remainder}] linked to ${extractedEmail}`, "info");
            }
        }
        currentEmail = extractedEmail;
        routeInvestigationWithBridgeCheck(currentEmail);
        return;
    }

    if (!rawVal.includes("@") && rawVal.includes(" ")) {
        const anchorNameInput = document.getElementById("anchor-name");
        if (anchorNameInput && (!anchorNameInput.value || anchorNameInput.value.trim() === "")) {
            anchorNameInput.value = rawVal;
            showToast(`Person Target: [${rawVal}] activated for onomastic & OSINT search`, "info");
        }
    }

    currentEmail = rawVal;
    routeInvestigationWithBridgeCheck(currentEmail);
}

function closeDomainReconModal() {
    const modal = document.getElementById("domain-recon-modal");
    if (modal) modal.style.display = "none";
}

function handleDomainModalBackdropClick(event) {
    if (event.target && event.target.id === "domain-recon-modal") {
        closeDomainReconModal();
    }
}

window.closeDomainReconModal = closeDomainReconModal;
window.handleDomainModalBackdropClick = handleDomainModalBackdropClick;
window.executeDomainRecon = executeDomainRecon;

async function executeDomainRecon(domain) {
    const modal = document.getElementById("domain-recon-modal");
    const titleEl = document.getElementById("domain-modal-title");
    const bodyEl = document.getElementById("domain-modal-body");

    if (modal) modal.style.display = "flex";
    if (titleEl) titleEl.innerHTML = `<span class="flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-sky-400")} Corporate Reconnaissance: ${escapeHtml(domain)}</span>`;
    if (bodyEl) {
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 2.5rem 1rem;">
                <div class="stats-dot" style="display: inline-block; width: 14px; height: 14px; margin-bottom: 0.8rem;"></div>
                <div class="mono" style="font-size: 0.95rem; color: #38bdf8;">Executing EmploLeaks Corporate Attack Surface Scan...</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.4rem;">Querying Certificate Transparency (crt.sh), external login gateways, and employee breach exposures.</div>
            </div>
        `;
    }

    try {
        const res = await fetch(`/api/domain/recon?domain=${encodeURIComponent(domain)}`);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Domain reconnaissance failed.");
        }

        const data = await res.json();
        const r = data.organization_risk || {};
        const infra = data.infrastructure || {};
        const subs = data.subdomains || [];
        const emps = data.employees || [];

        const riskBadgeClass = r.level === "CRITICAL" ? "badge-critical" : (r.level === "HIGH" ? "badge-high" : (r.level === "MEDIUM" ? "badge-neutral" : "badge-clean"));

        let mxStr = (infra.mx_servers || []).join(", ") || "No MX records found";
        let spoofBadge = infra.spoofable 
            ? `<span class="badge-pill badge-critical">VULNERABLE TO SPOOFING (DMARC ${escapeHtml(infra.dmarc_policy || 'NONE')})</span>` 
            : `<span class="badge-pill badge-clean">PROTECTED (DMARC ${escapeHtml(infra.dmarc_policy || 'ENFORCED')})</span>`;

        let subRows = "";
        if (subs.length === 0) {
            subRows = `<tr><td colspan="3" style="text-align: center; color: #94a3b8; padding: 1rem;">No external login gateways discovered via Certificate Transparency.</td></tr>`;
        } else {
            subs.forEach(s => {
                const isHigh = s.risk_level === "HIGH";
                const catBadge = `<span class="badge-pill ${isHigh ? 'badge-critical' : 'badge-neutral'}">${escapeHtml(s.category)}</span>`;
                subRows += `
                    <tr>
                        <td class="mono" style="font-weight: 600;">
                            <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: none;">
                                ${escapeHtml(s.subdomain)} ↗
                            </a>
                        </td>
                        <td>${catBadge}</td>
                        <td style="font-size: 0.78rem; color: #94a3b8;">${escapeHtml(s.description)}</td>
                    </tr>
                `;
            });
        }

        let empRows = "";
        if (emps.length === 0) {
            empRows = `<tr><td colspan="4" style="text-align: center; color: #94a3b8; padding: 1rem;">No employees currently indexed under ${escapeHtml(domain)}. Search specific email above to execute live deep-dive.</td></tr>`;
        } else {
            emps.forEach(e => {
                const hasBreach = e.creds_count > 0 || e.direct_leaks_count > 0;
                const statusBadge = hasBreach 
                    ? `<span class="badge-pill badge-critical">${e.creds_count} LEAKED CREDS</span>` 
                    : `<span class="badge-pill badge-clean">CLEAN</span>`;
                empRows += `
                    <tr>
                        <td>
                            <strong>${escapeHtml(e.full_name)}</strong>
                            <div class="mono" style="font-size: 0.75rem; color: #94a3b8;">${escapeHtml(e.corporate_email)}</div>
                        </td>
                        <td>${escapeHtml(e.job_title)} <div style="font-size: 0.72rem; color: #64748b;">${escapeHtml(e.department)}</div></td>
                        <td>${statusBadge}</td>
                        <td>
                            <button type="button" class="btn-mini-unlock" onclick="closeDomainReconModal(); loadExampleTarget('${escapeHtml(e.corporate_email)}');">
                                Deep Dive Scan &rarr;
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        const arch = data.historical_archives || {};
        const archItems = arch.items || [];
        let archRows = "";
        if (archItems.length === 0) {
            archRows = `<tr><td colspan="3" style="text-align: center; color: #94a3b8; padding: 1rem;">No historical crawl snapshots or archived endpoints found for this domain.</td></tr>`;
        } else {
            archItems.forEach(item => {
                const isSens = item.is_sensitive;
                const riskBadge = isSens
                    ? `<span class="badge-pill badge-critical">${escapeHtml(item.risk_level)}: ${escapeHtml(item.category)}</span>`
                    : `<span class="badge-pill badge-clean">ARCHIVED</span>`;
                const playUrl = item.wayback_url || item.url;
                archRows += `
                    <tr>
                        <td class="mono" style="font-size: 0.78rem; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            <a href="${escapeHtml(playUrl)}" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: none;" title="${escapeHtml(item.url)}">
                                ${escapeHtml(item.url)} ↗
                            </a>
                        </td>
                        <td>${riskBadge}</td>
                        <td style="font-size: 0.75rem; color: #94a3b8;">
                            <div>${escapeHtml(item.description)}</div>
                            <div class="mono" style="font-size: 0.7rem; color: #64748b; margin-top: 2px;">${escapeHtml(item.source)}</div>
                        </td>
                    </tr>
                `;
            });
        }

        bodyEl.innerHTML = `
            <!-- Top Risk Header Card -->
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 8px; margin-bottom: 1.2rem;">
                <div>
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        <span class="mono" style="font-size: 1.15rem; font-weight: 700; color: var(--t-primary);">${escapeHtml(domain)}</span>
                        <span class="badge-pill ${riskBadgeClass}">RISK: ${r.level}</span>
                    </div>
                    <div style="font-size: 0.82rem; color: var(--t-secondary); margin-top: 0.35rem; max-width: 680px;">
                        ${escapeHtml(r.summary)}
                    </div>
                </div>
            </div>

            <!-- Stats Grid -->
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.75rem; margin-bottom: 1.2rem;">
                <div class="evidence-card" style="margin: 0; padding: 0.8rem; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: #38bdf8;" class="mono">${data.total_subdomains}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Subdomains</div>
                </div>
                <div class="evidence-card" style="margin: 0; padding: 0.8rem; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: ${data.high_risk_portals > 0 ? '#ef4444' : '#10b981'};" class="mono">${data.high_risk_portals}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Risk Portals</div>
                </div>
                <div class="evidence-card" style="margin: 0; padding: 0.8rem; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: ${(arch.sensitive_exposures_count || 0) > 0 ? '#f59e0b' : '#10b981'};" class="mono">${arch.sensitive_exposures_count || 0}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Sensitive Paths</div>
                </div>
                <div class="evidence-card" style="margin: 0; padding: 0.8rem; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: #818cf8;" class="mono">${r.total_staff_indexed || 0}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Staff Indexed</div>
                </div>
                <div class="evidence-card" style="margin: 0; padding: 0.8rem; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: ${r.breached_staff_count > 0 ? '#f43f5e' : '#10b981'};" class="mono">${r.breached_staff_count || 0}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Breached Staff</div>
                </div>
            </div>

            <!-- Mail Infrastructure & Anti-Spoofing -->
            <div class="evidence-card" style="margin-bottom: 1.2rem; border-left: 3px solid #38bdf8;">
                <div class="evidence-header">
                    <span class="evidence-title flex items-center gap-1.5">${getUiIcon("mail", "w-3.5 h-3.5 text-sky-400")} Mail Routing &amp; Anti-Spoofing Security (DoH Analysis)</span>
                    ${spoofBadge}
                </div>
                <div class="evidence-body" style="font-size: 0.8rem; line-height: 1.6;">
                    <div><strong>Mail Provider:</strong> ${escapeHtml(infra.provider_name || 'Custom Enterprise')}</div>
                    <div><strong>MX Gateways:</strong> <span class="mono">${escapeHtml(mxStr)}</span></div>
                    <div><strong>SPF Status:</strong> <span class="mono">${escapeHtml(infra.spf_status || 'MISSING')}</span></div>
                    <div><strong>DMARC Enforcement:</strong> <span class="mono">${escapeHtml(infra.dmarc_policy || 'MISSING')}</span></div>
                </div>
            </div>

            <!-- Discovered External Gateways (Subdomains) -->
            <div class="evidence-card" style="margin-bottom: 1.2rem;">
                <div class="evidence-header">
                    <span class="evidence-title flex items-center gap-1.5">${getUiIcon("globe", "w-3.5 h-3.5 text-purple-400")} External Corporate Portals &amp; Gateways (${subs.length})</span>
                    <span class="evidence-tag" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">CERTIFICATE TRANSPARENCY</span>
                </div>
                <div style="overflow-x: auto; max-height: 240px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                                <th style="padding: 0.5rem; color: #94a3b8;">Subdomain</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Category</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Threat Vector</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${subRows}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Historical Web Archives & Exposed Endpoints -->
            <div class="evidence-card" style="margin-bottom: 1.2rem; border-left: 3px solid #f59e0b;">
                <div class="evidence-header">
                    <span class="evidence-title flex items-center gap-1.5">${getUiIcon("globe", "w-3.5 h-3.5 text-amber-400")} Historical Web Archives &amp; Endpoint Recon (${archItems.length})</span>
                    <span class="evidence-tag" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3);">${arch.sensitive_exposures_count || 0} SENSITIVE EXPOSURES</span>
                </div>
                <div style="overflow-x: auto; max-height: 240px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                                <th style="padding: 0.5rem; color: #94a3b8;">Archived Endpoint</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Classification</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Threat Analysis &amp; Source</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${archRows}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Corporate Employee Roster & Breach Risk -->
            <div class="evidence-card" style="margin-bottom: 0;">
                <div class="evidence-header">
                    <span class="evidence-title flex items-center gap-1.5">${getUiIcon("users", "w-3.5 h-3.5 text-rose-400")} Indexed Corporate Staff &amp; Compromised Accounts (${emps.length})</span>
                    <span class="evidence-tag" style="background: rgba(244, 63, 94, 0.15); color: #f43f5e;">SPILLOVER MAPPING</span>
                </div>
                <div style="overflow-x: auto; max-height: 240px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left;">
                                <th style="padding: 0.5rem; color: #94a3b8;">Employee</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Role / Dept</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Breach Exposure</th>
                                <th style="padding: 0.5rem; color: #94a3b8;">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${empRows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Domain recon error:", err);
        if (bodyEl) {
            bodyEl.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: #f87171;">
                    <div style="font-size: 1.2rem;">Domain Reconnaissance Failed</div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #94a3b8;">${escapeHtml(err.message)}</div>
                </div>
            `;
        }
        showToast(err.message, "error");
    }
}

function openBatchModal() {
    const modal = document.getElementById("batch-modal");
    if (modal) modal.style.display = "flex";
}

function closeBatchModal() {
    const modal = document.getElementById("batch-modal");
    if (modal) modal.style.display = "none";
}

function handleBatchModalBackdropClick(event) {
    if (event.target && event.target.id === "batch-modal") {
        closeBatchModal();
    }
}

function loadSampleBatch() {
    const input = document.getElementById("batch-emails-input");
    if (input) {
        input.value = "alice@cybercorp.io\nbob@cybercorp.io\ncharlie@cybercorp.io\ntest@mailinator.com\ntest@gmail.com";
    }
}

async function executeBatchAudit() {
    const input = document.getElementById("batch-emails-input");
    const container = document.getElementById("batch-results-container");
    if (!input || !container) return;

    const rawText = input.value.trim();
    if (!rawText) {
        showToast("Please enter at least one email address.", "warning");
        return;
    }

    const emails = rawText
        .split(/[\n,]+/)
        .map(e => e.trim())
        .filter(e => e.includes("@"));

    if (emails.length === 0) {
        showToast("No valid email addresses parsed.", "warning");
        return;
    }

    container.style.display = "block";
    container.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem;">
            <div class="stats-dot" style="display: inline-block; width: 14px; height: 14px; margin-bottom: 0.8rem;"></div>
            <div class="mono" style="font-size: 0.95rem; color: #818cf8;">Executing WhatBreach Batch Audit on ${emails.length} Target(s)...</div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.4rem;">Analyzing cross-identity breach spillovers, password hash collisions, and corporate threat matrix.</div>
        </div>
    `;

    try {
        const res = await fetch("/api/scan/batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ emails: emails, audit_mode: true })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Batch audit failed.");
        }

        const data = await res.json();
        const levelColor = data.collective_risk_level === "CRITICAL" ? "#ef4444" : (data.collective_risk_level === "HIGH" ? "#f97316" : (data.collective_risk_level === "MEDIUM" ? "#f59e0b" : "#10b981"));

        let sharedBreachesHtml = "";
        if (data.shared_breaches && data.shared_breaches.length > 0) {
            sharedBreachesHtml = `
                <div style="margin-bottom: 16px;">
                    <div class="mono flex items-center gap-2" style="font-size: 0.82rem; font-weight: 700; color: #f43f5e; margin-bottom: 8px;">${getUiIcon("alert", "w-4 h-4 text-rose-400")} CROSS-IDENTITY SHARED BREACH OVERLAP (LATERAL MOVEMENT ATTACK SURFACE)</div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;">
                        ${data.shared_breaches.map(sb => `
                            <div class="evidence-card" style="border-left: 3px solid #ef4444; margin: 0; padding: 10px 14px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: var(--t-primary); font-size: 0.85rem;">${escapeHtml(sb.breach_name)}</strong>
                                    <span class="badge-pill badge-critical">${sb.count} Targets Affected</span>
                                </div>
                                <div class="mono" style="font-size: 0.72rem; color: var(--t-secondary); margin-top: 6px;">
                                    ${sb.affected_emails.map(em => `<div style="margin-top: 2px;">• ${escapeHtml(em)}</div>`).join("")}
                                </div>
                            </div>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        let targetsHtml = `
            <div style="overflow-x: auto;">
                <table class="data-table mono" style="font-size: 0.78rem; width: 100%;">
                    <thead>
                        <tr>
                            <th>Target Email</th>
                            <th>Identity Name</th>
                            <th>Risk Score</th>
                            <th>Risk Level</th>
                            <th>Leaks Count</th>
                            <th>Credentials</th>
                            <th>Top Leaks</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.targets.map(t => {
                            const badgeCls = t.risk_level === "CRITICAL" ? "badge-critical" : (t.risk_level === "HIGH" ? "badge-high" : (t.risk_level === "MEDIUM" ? "badge-neutral" : "badge-clean"));
                            const dispTag = t.is_disposable ? '<span class="badge-pill badge-high" style="font-size: 0.65rem; margin-left: 4px;">BURNER</span>' : '';
                            return `
                                <tr>
                                    <td><strong>${escapeHtml(t.email)}</strong> ${dispTag}</td>
                                    <td>${escapeHtml(t.full_name || 'N/A')}</td>
                                    <td><strong style="color: ${t.risk_score > 60 ? '#ef4444' : '#38bdf8'};">${t.risk_score}/100</strong></td>
                                    <td><span class="badge-pill ${badgeCls}">${t.risk_level}</span></td>
                                    <td>${t.leaks_count}</td>
                                    <td>${t.credentials_count || 0}</td>
                                    <td><span style="color: #94a3b8;">${escapeHtml((t.top_breaches || []).slice(0, 2).join(", ") || "Clean")}</span></td>
                                    <td>
                                        <button type="button" class="btn-tool" onclick="closeBatchModal(); loadExampleTarget('${escapeHtml(t.email)}');" style="color: #38bdf8; border-color: #38bdf8; font-size: 0.7rem; padding: 2px 8px;">
                                            Inspect Graph &rarr;
                                        </button>
                                    </td>
                                </tr>
                            `;
                        }).join("")}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = `
            <!-- Top Summary Banner -->
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 8px; margin-bottom: 16px;">
                <div>
                    <div class="mono" style="font-size: 1.1rem; font-weight: 700; color: var(--t-primary);">
                        Group Risk Rating: <span style="color: ${levelColor};">${data.collective_risk_level} (${data.collective_risk_score}/100)</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                        Group average risk score: <strong>${data.average_risk_score}/100</strong> across ${data.total_targets} analyzed target(s).
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span class="badge-pill badge-info">${data.total_targets} Targets</span>
                    <span class="badge-pill ${data.compromised_targets > 0 ? 'badge-critical' : 'badge-clean'}">${data.compromised_targets} Compromised</span>
                    <span class="badge-pill badge-neutral">${data.total_leaks_detected} Total Leaks</span>
                </div>
            </div>

            ${sharedBreachesHtml}
            ${targetsHtml}
        `;
    } catch (err) {
        console.error("Batch audit error:", err);
        container.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #f87171;">
                <div style="font-size: 1.1rem;">Group Batch Audit Failed</div>
                <div style="margin-top: 0.4rem; font-size: 0.82rem; color: #94a3b8;">${escapeHtml(err.message)}</div>
            </div>
        `;
        showToast(err.message, "error");
    }
}

window.openBatchModal = openBatchModal;
window.closeBatchModal = closeBatchModal;
window.handleBatchModalBackdropClick = handleBatchModalBackdropClick;
window.loadSampleBatch = loadSampleBatch;
window.executeBatchAudit = executeBatchAudit;

/**
 * Fetch telemetry statistics for the top navigation
 */
async function loadGlobalStats() {
    try {
        const res = await fetch("/api/stats");
        if (!res.ok) return;
        const stats = await res.json();
        const statLabel = document.getElementById("stat-threat-summary");
        if (statLabel) {
            statLabel.innerText = `Threat DB: ${stats.total_leaks} Leaks Indexed (${stats.stealer_leaks} Stealers)`;
        }
    } catch (err) {
        console.warn("Could not fetch global stats:", err);
    }
}

function addReconLog(streamEl, tag, tagClass, message, startTime) {
    if (!streamEl) return;
    const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
    const row = document.createElement("div");
    row.className = "recon-log-row";
    row.innerHTML = `
        <span class="recon-log-time">${elapsed}s</span>
        <span class="recon-log-tag ${tagClass}">${tag}</span>
        <span class="recon-log-msg">${escapeHtml(message)}</span>
    `;
    streamEl.appendChild(row);
    streamEl.scrollTop = streamEl.scrollHeight;
}

/**
 * Execute investigation for a given email address with optional anchors
 */
async function executeInvestigation(email) {
    playSound("search");
    const standbyBox = document.getElementById("standby-status-box");
    if (standbyBox) standbyBox.style.display = "none";

    const scanline = document.getElementById("search-scanline");
    if (scanline) scanline.classList.add("active");

    const reconTerminal = document.getElementById("recon-terminal");
    const logStream = document.getElementById("recon-log-stream");
    const timerEl = document.getElementById("recon-timer");
    const targetTagEl = document.getElementById("recon-target-tag");
    const progTextEl = document.getElementById("recon-progress-text");
    const progBarEl = document.getElementById("recon-progress-bar");

    if (reconTerminal) {
        reconTerminal.style.display = "block";
        if (logStream) logStream.innerHTML = "";
        if (targetTagEl) targetTagEl.innerText = `TARGET: ${email}`;
        if (progBarEl) progBarEl.style.width = "10%";
        if (progTextEl) progTextEl.innerText = "Phase 1/6: Querying Global Breach Indices (XposedOrNot)...";
    }

    const startTime = performance.now();
    const timerInterval = setInterval(() => {
        if (timerEl) {
            timerEl.innerText = ((performance.now() - startTime) / 1000).toFixed(1) + "s";
        }
    }, 100);

    addReconLog(logStream, "INIT", "recon-tag-info", `Starting multi-tool OSINT super-engine reconnaissance on ${email}...`, startTime);

    const t1 = setTimeout(() => {
        if (progBarEl) progBarEl.style.width = "28%";
        if (progTextEl) progTextEl.innerText = "Phase 2/6: Holehe Engine: Probing 120+ Platform Endpoints...";
        addReconLog(logStream, "HOLEHE_PROBE", "recon-tag-probe", "Probing Spotify, Twitter/X, Office365, Snapchat, Duolingo, LastPass, Adobe...", startTime);
    }, 400);

    const t2 = setTimeout(() => {
        if (progBarEl) progBarEl.style.width = "50%";
        if (progTextEl) progTextEl.innerText = "Phase 3/6: OpenPGP Keyservers & Gravatar Profile v2...";
        addReconLog(logStream, "CRYPTO_PROFILE", "recon-tag-git", "Querying Ubuntu HKP & keys.openpgp.org keyservers. Parsing Gravatar public bio & linked accounts...", startTime);
    }, 1100);

    const t3 = setTimeout(() => {
        if (progBarEl) progBarEl.style.width = "72%";
        if (progTextEl) progTextEl.innerText = "Phase 4/6: Git Archaeology & Candidate Document Mining...";
        addReconLog(logStream, "GIT_ARCHAEOLOGY", "recon-tag-git", "Mining GitHub global commit metadata, repositories (*.github.io), and contact CV documents...", startTime);
    }, 1800);

    const t4 = setTimeout(() => {
        if (progBarEl) progBarEl.style.width = "88%";
        if (progTextEl) progTextEl.innerText = "Phase 5/6: International Telecom & WhatsMyName Cross-Checks...";
        addReconLog(logStream, "CROSS_PIVOT", "recon-tag-telecom", "Validating carrier network (E.164/libphonenumber). Probing 12 developer/social registries across handles...", startTime);
    }, 2600);

    try {
        let anchorQuery = "";
        const aName = document.getElementById("anchor-name")?.value.trim();
        const aUser = document.getElementById("anchor-username")?.value.trim();
        const aPhone = document.getElementById("anchor-phone")?.value.trim();
        const aCity = document.getElementById("anchor-city")?.value.trim();
        if (aName) anchorQuery += `&known_name=${encodeURIComponent(aName)}`;
        if (aUser) anchorQuery += `&known_username=${encodeURIComponent(aUser)}`;
        if (aPhone) anchorQuery += `&known_phone=${encodeURIComponent(aPhone)}`;
        if (aCity) anchorQuery += `&known_city=${encodeURIComponent(aCity)}`;

        const url = `/api/search?email=${encodeURIComponent(email)}&audit_mode=${auditMode}&refresh=true${anchorQuery}`;
        const res = await fetch(url);
        
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Unable to evaluate email address.");
        }

        const data = await res.json();
        currentInvestigationData = data;

        if (progBarEl) progBarEl.style.width = "100%";
        if (progTextEl) progTextEl.innerText = "Phase 6/6: Multi-Hop Intelligence Synthesized";
        addReconLog(logStream, "SYNTHESIS", "recon-tag-done", `Reconnaissance finished in ${((performance.now() - startTime) / 1000).toFixed(2)}s. Correlated forensic pivots ingested.`, startTime);

        await new Promise(r => setTimeout(r, 400));
        if (reconTerminal) reconTerminal.style.display = "none";

        // Render sections
        renderResultsView(data, email);
        renderVectorsBreakdown(data.spillover_score);
        renderEvidenceTabs(data);
        renderGraph(data.graph);
        renderAIReviewSection(data);

        // Feedback
        if (window.sfx) {
            if (data.spillover_score && data.spillover_score.score >= 50) {
                window.sfx.playAlert();
                setTimeout(() => { if (window.sfx) window.sfx.playVictory(); }, 400);
            } else {
                window.sfx.playVictory();
            }
        }

        if (data.spillover_score.score === 0) {
            showToast(`Zero compromise footprints detected for: ${email}`, "success");
        } else {
            showToast(`Analysis loaded: ${email} (${data.spillover_score.level} — ${data.spillover_score.score}/100)`, "info");
        }
    } catch (err) {
        console.error("Investigation failed:", err);
        showToast(err.message || "Investigation failed.", "error");
        if (reconTerminal) reconTerminal.style.display = "none";
        
        // --- INJECTED ERROR BOUNDARY ---
        const errContainer = document.getElementById("network-canvas");
        if (errContainer) {
            errContainer.innerHTML = `<div style="padding: 20px; color: red; font-family: monospace; z-index: 9999; position: relative; background: #222; border: 2px solid red;">
                <h3>Frontend Rendering Crash Detected</h3>
                <pre style="white-space: pre-wrap; word-break: break-all;">${err.stack || err.toString()}</pre>
            </div>`;
        }
    } finally {
        const scanline = document.getElementById("search-scanline");
        if (scanline) scanline.classList.remove("active");
        clearInterval(timerInterval);
        clearTimeout(t1);
        clearTimeout(t2);
        clearTimeout(t3);
        clearTimeout(t4);
    }
}

/**
 * Render between Clean State (0 score) and Compromised State (>0 score)
 */
function renderResultsView(data, email) {
    // Keep redundant separate banner hidden to preserve clean canonical 4 Bento finding cards
    const summaryBanner = document.getElementById("summary-metrics-banner");
    if (summaryBanner) summaryBanner.style.display = "none";

    const cleanBox = document.getElementById("clean-status-box");
    const targetCard = document.getElementById("target-exposure-card");
    const cleanEmailLabel = document.getElementById("clean-email-label");
    const warningBox = document.getElementById("domain-warning-box");
    const warningTitle = document.getElementById("domain-warning-title");
    const warningBadge = document.getElementById("domain-warning-badge");
    const warningDesc = document.getElementById("domain-warning-desc");
    const domainStatusBadge = document.getElementById("domain-status-badge");

    // 0. Check Email & Domain Verification
    const v = data.email_verification;
    if (v && !v.is_valid) {
        if (warningBox) warningBox.style.display = "flex";
        if (warningTitle) warningTitle.innerText = v.status === "NON_EXISTENT_DOMAIN" ? "Domain Does Not Exist / Dead Mail Host" : "Invalid Email Address Format";
        if (warningBadge) {
            warningBadge.className = "badge-pill badge-critical";
            warningBadge.innerText = v.status;
        }
        if (warningDesc) warningDesc.innerText = v.reason;
        if (cleanBox) cleanBox.style.display = "none";
        if (targetCard) targetCard.style.display = "none";
        showToast(v.reason, "error");
        return;
    } else if (v && v.is_disposable) {
        if (warningBox) warningBox.style.display = "flex";
        if (warningTitle) warningTitle.innerText = "Disposable / Burner Email Service Detected";
        if (warningBadge) {
            warningBadge.className = "badge-pill badge-high";
            warningBadge.innerText = "DISPOSABLE INBOX";
        }
        if (warningDesc) warningDesc.innerText = v.reason;
    } else {
        if (warningBox) warningBox.style.display = "none";
    }

    const burnerAlert = document.getElementById("burner-email-alert");
    const burnerAlertText = document.getElementById("burner-alert-text");
    const disp = data.disposable_intelligence || (v && v.is_disposable ? { is_disposable: true, details: v.reason } : null);
    if (burnerAlert) {
        if (disp && disp.is_disposable) {
            burnerAlert.style.display = "flex";
            if (burnerAlertText) burnerAlertText.innerText = disp.details || "Target domain belongs to an ephemeral throwaway burner mailbox.";
        } else {
            burnerAlert.style.display = "none";
        }
    }

    // Target Bento Forensic Ledger & 4 Findings Cards are ALWAYS displayed consistently
    if (cleanBox) cleanBox.style.display = "none";
    if (targetCard) targetCard.style.display = "block";

    // Target Meta
    const emp = data.employee || {};
    const hasRealName = emp.full_name && emp.full_name !== "Target User" && !emp.full_name.toLowerCase().startsWith("webmail");
    const targetNameEl = document.getElementById("target-name");
    const targetEmailEl = document.getElementById("target-email-display");
    const avatarEl = document.getElementById("target-avatar");

    if (targetNameEl) targetNameEl.innerText = hasRealName ? emp.full_name : (emp.corporate_email || email);
    if (targetEmailEl) targetEmailEl.innerText = emp.corporate_email || email;

    if (avatarEl) {
        if (hasRealName) {
            const initials = emp.full_name.split(" ").filter(Boolean).map(n => n[0]).join("").substring(0, 2).toUpperCase();
            avatarEl.innerText = initials || "@";
        } else {
            avatarEl.innerText = "@";
        }
    }

    // Spillover Score Calculation & Visualization (Use Natural Risk Words, No Tiers)
    const scoreVal = data.spillover_score ? (data.spillover_score.numeric_score ?? data.spillover_score.score) : 0;
    const riskLevel = (data.spillover_score && data.spillover_score.level) ? data.spillover_score.level : "LOW";
    const scoreNumEl = document.getElementById("score-number");
    const scoreNumericBadge = document.getElementById("score-numeric-badge");
    const scoreLevelLabel = document.getElementById("score-level-label");

    if (scoreNumEl) {
        scoreNumEl.innerText = riskLevel === "CLEAN" ? "CLEAN" : `${riskLevel} RISK`;
        scoreNumEl.style.color = (riskLevel === "CLEAN") ? "#10b981" : (data.spillover_score.color || "#ef4444");
        scoreNumEl.style.fontSize = "1.85rem";
    }
    if (scoreNumericBadge) {
        scoreNumericBadge.innerText = `SCORE: ${scoreVal}/100`;
    }
    if (scoreLevelLabel) {
        scoreLevelLabel.innerText = "RISK RATING";
    }

    const badgeEl = document.getElementById("severity-badge");
    if (badgeEl) {
        if (riskLevel === "CLEAN" || scoreVal === 0) {
            badgeEl.className = "badge-pill badge-clean";
            badgeEl.innerText = "AUTHENTICATED CLEAN";
            badgeEl.style.borderColor = "#10b981";
            badgeEl.style.color = "#10b981";
            badgeEl.style.background = "rgba(16, 185, 129, 0.15)";
        } else {
            badgeEl.className = `badge-pill ${data.spillover_score.badge_class || 'badge-high'}`;
            badgeEl.innerText = `${riskLevel} RISK`;
            badgeEl.style.borderColor = data.spillover_score.color || "#ef4444";
            badgeEl.style.color = data.spillover_score.color || "#ef4444";
            badgeEl.style.background = (data.spillover_score.color || "#ef4444") + "22";
        }
    }

    const domBadge = document.getElementById("domain-status-badge");
    if (domBadge) {
        const ev = data.email_verification;
        if (ev && ev.email_security) {
            const prov = ev.email_security.mail_provider || ev.provider_type || "Mail Infrastructure";
            const isSafe = ev.email_security.spoofing_risk === "PROTECTED";
            domBadge.style.display = "inline-flex";
            domBadge.className = isSafe ? "badge-pill badge-clean" : "badge-pill badge-medium";
            domBadge.innerHTML = `<span class="flex items-center gap-1">${getUiIcon('mail', 'w-3 h-3 text-sky-400')} ${escapeHtml(prov)} [SPF: ${escapeHtml(ev.email_security.spf_status || 'OK')}]</span>`;
        } else {
            domBadge.style.display = "none";
        }
    }

    // Render Bento Overview Cards (Multi-Item Finding Pillars)
    renderTargetOverview(data);
}

/**
 * 5 Key Findings Cards (Multi-Item Display)
 * Pillars: Credentials, Geolocation, Telecom, Household, Workplace & Profiles.
 */
function renderTargetOverview(data) {
    if (!data) return;

    // 1. Credentials & Hashes List
    const credsList = document.getElementById("summary-creds-list");
    const badgeCreds = document.getElementById("badge-lock-creds");
    if (credsList) {
        const creds = data.credentials || [];
        if (creds.length > 0) {
            if (badgeCreds) {
                badgeCreds.innerText = `[${creds.length} EXPOSED]`;
                badgeCreds.className = "badge-lock unlocked";
            }
            credsList.innerHTML = creds.map(c => {
                const val = c.plaintext_password || c.password_hash || "Exfiltrated Credential";
                const service = c.domain_compromised || c.leak_name || "Breach Record";
                const isHash = !c.plaintext_password && Boolean(c.password_hash);
                return `
                    <div class="finding-item-row">
                        <div class="finding-item-top">
                            <span class="finding-item-val mono" style="${isHash ? 'color: #fde047; font-size: 0.72rem;' : 'color: #f87171;'}">${escapeHtml(val)}</span>
                            <span class="finding-item-badge">${escapeHtml(service)}</span>
                        </div>
                        ${c.username_or_email ? `<div class="finding-item-sub mono text-zinc-400">User: ${escapeHtml(c.username_or_email)}</div>` : ''}
                    </div>
                `;
            }).join("");
        } else {
            if (badgeCreds) {
                badgeCreds.innerText = "[CLEAN]";
                badgeCreds.className = "badge-lock clean";
            }
            credsList.innerHTML = `<div class="finding-empty-val mono">Zero credentials exposed in indexed dumps</div>`;
        }
    }

    // 2. Geolocation & Physical Coordinates (Corroborated Municipalities & Anchors)
    const locList = document.getElementById("summary-locations-list");
    const badgeAddr = document.getElementById("badge-lock-address");
    if (locList) {
        const footprints = [];
        (data.physical_footprints || []).forEach(f => {
            const city = (f.city || "").trim();
            const country = (f.country || "").trim();
            const addr = (f.address_line || "").trim();
            const exp = (f.exposure_type || "").toUpperCase();

            // Clean badge categorization
            let badge = "RESIDENTIAL";
            if (exp.includes("ACADEMIC") || addr.toLowerCase().includes("høgskolen") || addr.toLowerCase().includes("campus") || city.toLowerCase() === "halden") {
                badge = "ACADEMIC CAMPUS";
            } else if (exp.includes("ONOMASTIC") || addr.toLowerCase().includes("onomastic") || country.toLowerCase() === "poland" || city.toLowerCase() === "poland") {
                badge = "ONOMASTIC HERITAGE";
            } else if (exp.includes("RESIDENCE") || city.toLowerCase() === "sarpsborg") {
                badge = "VERIFIED RESIDENCE";
            } else if (country.toLowerCase() === "norway") {
                badge = "NATIONAL ANCHOR";
            }

            let dispText = addr;
            if (!dispText || dispText.toLowerCase().startsWith("geographic footprint:")) {
                dispText = city && country ? `${city}, ${country}` : (city || country || "Verified Footprint");
            }

            footprints.push({
                loc: dispText,
                badge: badge,
                key: `${city.toLowerCase()}|${country.toLowerCase()}`
            });
        });

        const seen = new Set();
        const uniqueLocs = footprints.filter(item => {
            const k = item.key || item.loc.toLowerCase().trim();
            if (seen.has(k) || !k) return false;
            seen.add(k);
            return true;
        });

        if (uniqueLocs.length > 0) {
            if (badgeAddr) {
                badgeAddr.innerText = `[${uniqueLocs.length} CORROBORATED]`;
                badgeAddr.className = "badge-lock unlocked";
            }
            locList.innerHTML = uniqueLocs.map(l => `
                <div class="finding-item-row">
                    <div class="finding-item-top">
                        <span class="finding-item-val">${escapeHtml(l.loc)}</span>
                        <span class="finding-item-badge">${escapeHtml(l.badge)}</span>
                    </div>
                </div>
            `).join("");
        } else {
            if (badgeAddr) {
                badgeAddr.innerText = "[NOT DETECTED]";
                badgeAddr.className = "badge-lock clean";
            }
            locList.innerHTML = `<div class="finding-empty-val">No residential coordinates detected</div>`;
        }
    }

    // 3. Telecom & Phone Lines
    const phoneList = document.getElementById("summary-phones-list");
    const badgePhone = document.getElementById("badge-lock-phone");
    if (phoneList) {
        const phones = (data.pivots || []).filter(p => p.pivot_type === "PHONE_NUMBER" || (p.pivot_type && p.pivot_type.includes("PHONE")) || p.pivot_value.startsWith("telecom:") || p.pivot_value.startsWith("+"));
        if (phones.length > 0) {
            if (badgePhone) {
                badgePhone.innerText = `[${phones.length} TELECOM]`;
                badgePhone.className = "badge-lock unlocked";
            }
            phoneList.innerHTML = phones.map(ph => {
                const cleanVal = ph.pivot_value.replace(/^telecom:\s*/i, "");
                const cleanCtx = (ph.context_note || "Carrier Mobile Line").replace(/\[STATUS:\s*VERIFIED\]/g, "").trim();
                return `
                    <div class="finding-item-row">
                        <div class="finding-item-top">
                            <span class="finding-item-val mono" style="color: #67e8f9;">${escapeHtml(cleanVal)}</span>
                            <span class="finding-item-badge">E.164</span>
                        </div>
                        <div class="finding-item-sub mono text-zinc-400">${escapeHtml(cleanCtx)}</div>
                    </div>
                `;
            }).join("");
        } else {
            if (badgePhone) {
                badgePhone.innerText = "[NOT DETECTED]";
                badgePhone.className = "badge-lock clean";
            }
            phoneList.innerHTML = `<div class="finding-empty-val mono">No telecom lines detected</div>`;
        }
    }

    // 4. Household Cohabitants
    const relList = document.getElementById("summary-relatives-list");
    const badgeRel = document.getElementById("badge-lock-relative");
    if (relList) {
        const rels = data.relatives || [];
        if (rels.length > 0) {
            if (badgeRel) {
                badgeRel.innerText = `[${rels.length} COHABITANTS]`;
                badgeRel.className = "badge-lock unlocked";
            }
            relList.innerHTML = rels.map(r => `
                <div class="finding-item-row">
                    <div class="finding-item-top">
                        <span class="finding-item-val">${escapeHtml(r.full_name)}</span>
                        <span class="finding-item-badge">${escapeHtml(r.relationship || 'FAMILY')}</span>
                    </div>
                    ${r.contact_phone ? `<div class="finding-item-sub mono text-zinc-400">Line: ${escapeHtml(r.contact_phone)}</div>` : ''}
                </div>
            `).join("");
        } else {
            if (badgeRel) {
                badgeRel.innerText = "[CLEAR]";
                badgeRel.className = "badge-lock clean";
            }
            relList.innerHTML = `<div class="finding-empty-val">No cohabitants or family detected</div>`;
        }
    }

    // 5. Workplace & Academic Career History (STRICTLY Work & Education, Profiles in Pivots)
    const workList = document.getElementById("summary-workplace-list");
    const badgeWork = document.getElementById("badge-lock-workplace");
    if (workList) {
        const workItems = [];
        const workPivots = (data.pivots || []).filter(p => 
            p.pivot_type === "WORKPLACE" || 
            p.pivot_type === "EMPLOYER" || 
            p.pivot_type === "EDUCATION" || 
            p.pivot_type === "BUSINESS_ASSOCIATE"
        );
        workPivots.forEach(wp => {
            const pv = wp.pivot_value || "";
            if (pv.toLowerCase().includes("customs support")) return;
            
            let title = pv.replace(/^(Employer|Alma Mater|Co-partner|Workplace):\s*/i, "").trim();
            let badge = "EMPLOYER";
            const tLow = title.toLowerCase();
            if (wp.pivot_type === "EDUCATION" || tLow.includes("høgskolen") || tLow.includes("universitet") || tLow.includes("bachelor") || tLow.includes("vgs")) {
                badge = tLow.includes("bachelor") || tLow.includes("studium") ? "DEGREE" : "ACADEMIC";
            } else if (wp.pivot_type === "BUSINESS_ASSOCIATE") {
                badge = "CORPORATE";
            } else if (tLow.includes("vikar") || tLow.includes("renholder") || tLow.includes("developer")) {
                badge = "EXPERIENCE";
            }

            workItems.push({
                title: title,
                badge: badge
            });
        });

        // Deduplicate work items
        const seenWork = new Set();
        const uniqueWork = workItems.filter(item => {
            const k = item.title.toLowerCase().trim();
            if (seenWork.has(k) || !k) return false;
            seenWork.add(k);
            return true;
        });

        if (uniqueWork.length > 0) {
            if (badgeWork) {
                badgeWork.innerText = `[${uniqueWork.length} AFFILIATIONS]`;
                badgeWork.className = "badge-lock unlocked";
            }
            workList.innerHTML = uniqueWork.map(wi => `
                <div class="finding-item-row">
                    <div class="finding-item-top">
                        <span class="finding-item-val">${escapeHtml(wi.title)}</span>
                        <span class="finding-item-badge">${escapeHtml(wi.badge)}</span>
                    </div>
                </div>
            `).join("");
        } else {
            if (badgeWork) {
                badgeWork.innerText = "[NONE DETECTED]";
                badgeWork.className = "badge-lock clean";
            }
            workList.innerHTML = `<div class="finding-empty-val">No verified employment or academic affiliations detected</div>`;
        }
    }
}

/**
 * Render 5 Vector Risk Breakdown Bars
 */
function renderVectorsBreakdown(scoreData) {
    const vectors = scoreData.vectors;
    renderSingleVector("bar-stealers", "val-stealers", "sub-stealers", vectors.stealer_exposure);
    renderSingleVector("bar-creds", "val-creds", "sub-creds", vectors.credential_severity);
    renderSingleVector("bar-pivots", "val-pivots", "sub-pivots", vectors.identity_pivot);
    renderSingleVector("bar-physical", "val-physical", "sub-physical", vectors.physical_footprint);
    renderSingleVector("bar-family", "val-family", "sub-family", vectors.family_social_eng);

    const descEl = document.getElementById("score-desc");
    if (descEl) {
        if (scoreData.score === "Score 1") {
            descEl.innerText = "Clean state: no exposed credentials, stealer logs, or dangerous pivots detected.";
        } else if (scoreData.score === "Score 5") {
            descEl.innerText = "Critical: active malware logs, cleartext passwords, and exposed infrastructure.";
        } else if (scoreData.score === "Score 4") {
            descEl.innerText = "High: significant credential leakage with exposed private pivots.";
        } else if (scoreData.score === "Score 2" || scoreData.score === "Score 3") {
            descEl.innerText = "High: exfiltrated credentials and public online profile footprints detected.";
        } else {
            descEl.innerText = "Moderate: historical breach presence without active infostealer infection.";
        }
    }
}

function renderSingleVector(barId, valId, subId, vectorData) {
    const bar = document.getElementById(barId);
    const val = document.getElementById(valId);
    const sub = document.getElementById(subId);

    if (bar && vectorData) {
        let pct = 0;
        let c = "#10b981"; // default clean
        const s = vectorData.score || "";
        if (s === "CRITICAL") { pct = 100; c = "#ef4444"; }
        else if (s === "HIGH") { pct = 75; c = "#f97316"; }
        else if (s === "MEDIUM") { pct = 50; c = "#eab308"; }
        else if (s === "LOW") { pct = 25; c = "#38bdf8"; }
        else if (s === "CLEAN") { pct = 5; c = "#10b981"; }
        
        bar.style.width = `${pct}%`;
        bar.style.background = c;
    }
    if (val && vectorData) {
        val.innerText = `${vectorData.score}`;
    }
    if (sub && vectorData) {
        sub.innerText = vectorData.details;
    }
}

/**
 * Render Evidence Tabs
 */
function renderEvidenceTabs(data) {
    // 1. Malware & Leaks (Expandable Dense Table & Collapsible Drawer)
    const leaksContainer = document.getElementById("tab-leaks-content");
    if (leaksContainer) {
        leaksContainer.innerHTML = "";
        if (!data.leaks || data.leaks.length === 0) {
            leaksContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title font-mono" style="color: #34d399;">[STATUS: ZERO BREACHES DETECTED]</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">This identity does not appear in any indexed stealer dumps, public leaks, or darknet combolists.</div>
                </div>`;
        } else {
            let tableHtml = `
                <div class="breach-table-container">
                    <table class="breach-table">
                        <thead>
                            <tr>
                                <th style="width: 75px;">SEVERITY</th>
                                <th style="width: 100px;">DATE</th>
                                <th>ENTITY / THREAT SOURCE</th>
                                <th style="width: 110px;">CATEGORY</th>
                                <th>COMPROMISED FIELDS</th>
                                <th style="width: 90px; text-align: right;">PAYLOAD</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.leaks.forEach((leak, idx) => {
                const isStealer = leak.leak_type === "INFOSTEALER";
                const sevLevel = isStealer ? "CRITICAL" : "HIGH";
                const sevClass = isStealer ? "badge-critical" : "badge-high";

                const exposed = leak.exposed_data || [];
                const pillElements = exposed.map(item => {
                    const low = String(item).toLowerCase();
                    let tagClass = "data-tag";
                    if (low.includes("password") || low.includes("secret") || low.includes("credential")) tagClass += " crit";
                    else if (low.includes("address") || low.includes("card") || low.includes("financial")) tagClass += " high";
                    return `<span class="${tagClass}">${escapeHtml(item)}</span>`;
                }).join(" ");

                const circ = leak.circulation_intel;
                const circStatus = circ ? circ.circulation_status : "CLOSED_DUMP";
                const circHash = circ ? (circ.hash_type || "Cryptographic Hash") : "N/A";
                const circExploit = circ ? (circ.exploitability || "Standard") : "Elevated";

                tableHtml += `
                    <tr class="breach-row" id="row-leak-${idx}" onclick="toggleBreachDrawer('leak-${idx}')">
                        <td><span class="badge-pill ${sevClass}">${sevLevel}</span></td>
                        <td class="breach-date-cell mono">${escapeHtml(leak.breach_date || 'HISTORIC')}</td>
                        <td>
                            <div class="breach-entity-cell">${escapeHtml(leak.leak_name)}</div>
                            <div class="breach-source-sub mono">Source: ${escapeHtml(leak.threat_actor_source || 'Darknet Intelligence')}</div>
                        </td>
                        <td><span class="stealer-meta-pill mono">${escapeHtml(leak.leak_type || 'LEAK')}</span></td>
                        <td>
                            <div class="breach-tags-cell">
                                ${pillElements || '<span class="data-tag">CREDENTIALS</span>'}
                            </div>
                        </td>
                        <td class="breach-expand-cell">
                            <button type="button" class="btn-row-expand mono" id="btn-expand-leak-${idx}">[INSPECT ▾]</button>
                        </td>
                    </tr>
                    <tr class="breach-drawer-row" id="drawer-leak-${idx}" style="display: none;">
                        <td colspan="6">
                            <div class="breach-payload-drawer">
                                <div class="drawer-desc">${escapeHtml(leak.description || 'No extended description available.')}</div>
                                <div class="drawer-metadata-grid">
                                    <div class="drawer-meta-box">
                                        <span class="drawer-meta-lbl">Circulation Status</span>
                                        <span class="drawer-meta-val text-amber-400 mono">${escapeHtml(circStatus)}</span>
                                    </div>
                                    <div class="drawer-meta-box">
                                        <span class="drawer-meta-lbl">Cryptographic Hash</span>
                                        <span class="drawer-meta-val mono">${escapeHtml(circHash)}</span>
                                    </div>
                                    <div class="drawer-meta-box">
                                        <span class="drawer-meta-lbl">Exploitability</span>
                                        <span class="drawer-meta-val text-red-400 mono">${escapeHtml(circExploit)}</span>
                                    </div>
                                    ${leak.malware_family ? `
                                    <div class="drawer-meta-box">
                                        <span class="drawer-meta-lbl">Malware Family</span>
                                        <span class="drawer-meta-val text-red-400 mono">${escapeHtml(leak.malware_family)}</span>
                                    </div>` : ''}
                                    ${leak.antivirus_bypassed ? `
                                    <div class="drawer-meta-box">
                                        <span class="drawer-meta-lbl">Bypassed AV</span>
                                        <span class="drawer-meta-val text-amber-300 mono">${escapeHtml(leak.antivirus_bypassed)}</span>
                                    </div>` : ''}
                                </div>
                                <div class="drawer-payload-shell mono">
                                    <pre style="margin: 0; white-space: pre-wrap; word-break: break-all;">${escapeHtml(JSON.stringify(leak, null, 2))}</pre>
                                </div>
                                <div class="drawer-actions-row">
                                    <button type="button" class="btn-action-tool" onclick="event.stopPropagation(); copyToClipboard('${escapeHtml(JSON.stringify(leak))}', 'Breach Payload')">
                                        Copy Payload JSON
                                    </button>
                                </div>
                            </div>
                        </td>
                    </tr>
                `;
            });

            tableHtml += `
                        </tbody>
                    </table>
                </div>
            `;
            leaksContainer.innerHTML = tableHtml;
        }
    }

    // 2. Credentials
    const credsContainer = document.getElementById("tab-creds-content");
    if (credsContainer) {
        credsContainer.innerHTML = "";
        if (!data.credentials || data.credentials.length === 0) {
            credsContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title font-mono" style="color: #34d399;">[STATUS: CREDENTIALS UNCOMPROMISED]</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">No plaintext passwords or cryptographic hashes associated with this address.</div>
                </div>`;
        } else {
            data.credentials.forEach(cred => {
                const corpBadge = cred.is_corporate_password_match 
                    ? `<div class="warning-callout mono text-xs">[POLICY MATCH] Plaintext match to corporate policy! Critical account takeover risk.</div>` 
                    : "";

                let freqHtml = "";
                if (cred.global_frequency && cred.global_frequency > 0) {
                    freqHtml = `
                        <div style="margin-top: 0.35rem; font-size: 0.72rem; color: #f87171; font-family: var(--font-mono);">
                            [HIBP K-ANONYMITY] Observed across <strong>${cred.global_frequency.toLocaleString()}</strong> publicly leaked breach databases worldwide.
                        </div>
                    `;
                }

                let hashBlockHtml = "";
                if (cred.password_hash) {
                    const hi = cred.hash_intel || {};
                    const algo = hi.algorithm || "Hash";
                    const crackability = hi.crackability || "FAST CRACK EVALUATION";
                    const isInstant = crackability.includes("INSTANT") || crackability.includes("CRITICAL");
                    const algoBadgeStyle = isInstant 
                        ? "background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;" 
                        : "background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3);";

                    hashBlockHtml = `
                        <div style="margin-top: 0.45rem; padding: 8px 10px; background: var(--c-elevated); border: 1px solid var(--b-hairline); border-radius: 4px;">
                            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px; margin-bottom: 4px;">
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span class="badge-pill mono" style="${algoBadgeStyle} font-size: 0.68rem;">ALGO: ${escapeHtml(algo)}</span>
                                    <span class="badge-pill mono" style="font-size: 0.68rem; background: var(--c-surface); color: var(--t-secondary); border: 1px solid var(--b-hairline);">${escapeHtml(crackability)}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(cred.password_hash)}', 'Password Hash')">Copy Hash</button>
                                    <button type="button" class="btn-copy-mini mono" style="background: rgba(168, 85, 247, 0.15); color: #d8b4fe; border-color: rgba(168, 85, 247, 0.35);" onclick="resolveCredentialHash('${escapeHtml(cred.password_hash)}', this)">Resolve Hash</button>
                                </div>
                            </div>
                            <div>
                                <span class="code-field telemetry-val-hash mono" style="word-break: break-all; font-size: 0.74rem;">${escapeHtml(cred.password_hash)}</span>
                            </div>
                            <div class="hash-result-slot" style="display: none; margin-top: 6px;"></div>
                        </div>
                    `;
                }

                let secretHtml = `
                    <div style="margin-bottom: 0.4rem; padding: 0.4rem 0.6rem; background: var(--accent-emerald-subtle); border-left: 3px solid var(--accent-emerald); border-radius: 4px; font-size: 0.75rem; color: var(--accent-emerald);">
                        [UNMASKED INTEL] Plaintext secret exposed in clear text.
                    </div>
                    ${cred.plaintext_password ? `<div>Compromised Password: <span class="code-field mono" style="color: #f87171; font-weight: 700;">${escapeHtml(cred.plaintext_password)}</span> <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(cred.plaintext_password)}', 'Password')">Copy</button></div>` : ''}
                    ${hashBlockHtml}
                `;


                credsContainer.innerHTML += `
                    <div class="evidence-card">
                        <div class="evidence-header">
                            <span class="evidence-title">User: ${escapeHtml(cred.username_or_email)}</span>
                            <span class="evidence-tag" style="background: rgba(234, 179, 8, 0.2); color: #fde047; border: 1px solid #eab308;">${escapeHtml(cred.leak_name)}</span>
                        </div>
                        <div class="evidence-body">
                            ${secretHtml}
                            ${cred.password_pattern ? `<div style="margin-top: 0.25rem;">Pattern Analysis: <code>${escapeHtml(cred.password_pattern)}</code></div>` : ''}
                            <div style="margin-top: 0.25rem;">Target Domain: <code>${escapeHtml(cred.domain_compromised || 'N/A')}</code></div>
                            ${freqHtml}
                        </div>
                        ${corpBadge}
                    </div>
                `;
            });
        }
    }

    const targetFullName = (data.employee && data.employee.full_name) ? data.employee.full_name : "";

    // 3. Pivots & Public OSINT Footprint
    const allPivots = data.pivots || [];
    const rawSuspectedPivots = allPivots.filter(p => 
        p.pivot_type === "SUSPECTED_ACCOUNT" || 
        (p.context_note && p.context_note.includes("[STATUS: SUSPECTED]")) ||
        (p.context_note && p.context_note.includes("[PLATFORM: UNCONFIRMED]")) ||
        (p.confidence_score !== undefined && p.confidence_score < 0.85 && p.pivot_type !== "EDUCATION" && p.pivot_type !== "WORKPLACE" && p.pivot_type !== "TIMELINE" && p.pivot_type !== "TECH_STACK" && p.pivot_type !== "FLAGSHIP_PROJECT") ||
        (p.pivot_type === "PERSONA_PIVOT" && !p.pivot_value.toLowerCase().includes("esport") && !p.pivot_value.toLowerCase().includes("gamertag"))
    );
    const verifiedPivots = allPivots.filter(p => !rawSuspectedPivots.includes(p));

    // Platforms that already have a verified PUBLIC_PROFILE (e.g. GitHub: @sazeku123, Steam: @sazeku)
    const fullyResolvedPlatforms = new Set(
        verifiedPivots
            .filter(p => p.pivot_type === "PUBLIC_PROFILE")
            .map(p => normalizePlatform(p.pivot_value))
    );

    // Suppress candidate handles on platforms that already have a verified public profile
    const suspectedPivots = rawSuspectedPivots.filter(p => {
        const plat = normalizePlatform(p.pivot_value);
        return !fullyResolvedPlatforms.has(plat);
    });

    const suspectedCountBadge = document.getElementById("count-suspected");
    if (suspectedCountBadge) {
        suspectedCountBadge.innerText = suspectedPivots.length;
    }

    const pivotsContainer = document.getElementById("tab-pivots-content");
    if (pivotsContainer) {
        pivotsContainer.innerHTML = "";
        if (verifiedPivots.length === 0) {
            pivotsContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} No Correlated Private Pivots</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">No correlated personal phone numbers, secondary inboxes, or verified developer accounts confirmed.</div>
                </div>`;
        } else {
            function getPivotCategory(piv) {
                const pt = piv.pivot_type || "";
                const pv = (piv.pivot_value || "").toLowerCase();
                const ctx = (piv.context_note || "").toLowerCase();
                
                // 1. Identity & Legal (Legal Name, Target Persona, Avatars, Phone/Telecom)
                if (pt === "FULL_NAME" || pt === "PERSON_NAME" || pt === "AVATAR_CORRELATION" || pt === "PHONE_NUMBER" || pv.startsWith("telecom:") || pv.includes("+47") || pv.includes("+31") || pv.includes("+48") || pv.includes("+1")) {
                    return "identity";
                }
                // 2. Business & Corporate (Employer, KvK, Partners, Education, Career Timeline)
                if (pt === "WORKPLACE" || pt === "BUSINESS_ASSOCIATE" || pt === "EDUCATION" || pt === "TIMELINE" || pv.includes("employer:") || pv.includes("co-partner:") || pv.includes("alma mater:") || pv.includes("bachelor") || ctx.includes("kvk") || ctx.includes("chamber of commerce") || ctx.includes("drimble")) {
                    return "business";
                }
                // 3. Technical & Keys (GitHub repos, Code stacks, Flagship projects, SSH/PGP keys, subdomains)
                if (pt === "OPENPGP_KEY" || pt === "GITHUB_SSH_KEY" || pt === "TECH_STACK" || pt === "FLAGSHIP_PROJECT" || pt === "EMAIL_PERMUTATION" || pt === "SUBDOMAIN_ASSET" || pv.includes("repository") || pv.includes("ssh key") || pv.includes("pgp key") || pv.includes("core competencies") || pv.includes("flagship project")) {
                    return "technical";
                }
                // 4. Profiles & Accounts (Unified: Gaming, Esports, Steam, Chess.com, Roblox, Twitter/X, Office365, Spotify, LinkedIn, Facebook, Telegram, etc.)
                return "accounts";
            }

            const catCounts = { all: verifiedPivots.length, accounts: 0, identity: 0, business: 0, technical: 0 };
            verifiedPivots.forEach(p => {
                const cat = getPivotCategory(p);
                catCounts[cat] = (catCounts[cat] || 0) + 1;
            });

            pivotsContainer.innerHTML = `
                <div class="pivot-filter-chips">
                    <button type="button" class="btn-pivot-filter active" data-pivot-filter="all" onclick="filterPivotCategory('all')">[ALL] <span class="filter-count">(${catCounts.all})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="accounts" onclick="filterPivotCategory('accounts')">[PROFILES &amp; ACCOUNTS] <span class="filter-count">(${catCounts.accounts})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="identity" onclick="filterPivotCategory('identity')">[IDENTITY &amp; LEGAL] <span class="filter-count">(${catCounts.identity})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="business" onclick="filterPivotCategory('business')">[WORK &amp; CAREER] <span class="filter-count">(${catCounts.business})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="technical" onclick="filterPivotCategory('technical')">[TECHNICAL &amp; REPOS] <span class="filter-count">(${catCounts.technical})</span></button>
                </div>
                <div id="pivot-cards-list"></div>
            `;
            const pivotCardsList = document.getElementById("pivot-cards-list");
            const catBadgeStyles = {
                identity: "background: rgba(6, 182, 212, 0.15); color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.3);",
                business: "background: rgba(245, 158, 11, 0.15); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.3);",
                accounts: "background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);",
                social: "background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);",
                gaming: "background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);",
                technical: "background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3);"
            };
            const catBadgeLabels = {
                identity: "[IDENTITY]",
                business: "[WORK & CAREER]",
                accounts: "[PROFILES & ACCOUNTS]",
                social: "[PROFILES & ACCOUNTS]",
                gaming: "[PROFILES & ACCOUNTS]",
                technical: "[TECHNICAL & REPOS]"
            };
            function addPivotCard(html, cat, contextNote = "") {
                const bStyle = catBadgeStyles[cat] || catBadgeStyles.accounts;
                const bLabel = catBadgeLabels[cat] || "[PROFILES & ACCOUNTS]";
                const categoryPillHtml = `<span class="pivot-category-pill" style="${bStyle}">${bLabel}</span>`;
                
                // Extract any explicit tie attribution badge if present in the card HTML or contextNote
                const fullText = (contextNote || "") + " " + html;
                const tieMatch = fullText.match(/\[TIED:\s*([^\]]+)\]/);
                let tiePillHtml = "";
                if (tieMatch) {
                    tiePillHtml = `<span class="pivot-tie-pill">[TIED: ${escapeHtml(tieMatch[1])}]</span>`;
                }

                // Embed category pill and tie pill cleanly into .evidence-header alongside .evidence-tag
                let cardHtml = html;
                if (cardHtml.includes('<span class="evidence-tag"')) {
                    cardHtml = cardHtml.replace(
                        /<span class="evidence-tag"([^>]*)>(.*?)<\/span>/s,
                        `<div class="evidence-tags-group">${categoryPillHtml}${tiePillHtml}<span class="evidence-tag"$1>$2</span></div>`
                    );
                } else if (cardHtml.includes('<div class="evidence-header">')) {
                    cardHtml = cardHtml.replace(
                        '<div class="evidence-header">',
                        `<div class="evidence-header"><div class="evidence-tags-group">${categoryPillHtml}${tiePillHtml}</div>`
                    );
                }

                if (tieMatch) {
                    cardHtml = cardHtml.replace(/\[TIED:\s*[^\]]+\]/g, "");
                }

                const wrappedHtml = `
                    <div class="pivot-entry-card" data-pivot-cat="${cat}">
                        ${cardHtml}
                    </div>
                `;
                if (pivotCardsList) {
                    pivotCardsList.innerHTML += wrappedHtml;
                } else {
                    pivotsContainer.innerHTML += wrappedHtml;
                }
            }

            verifiedPivots.forEach(piv => {
                // Public OSINT Profile Cards (Gravatar, GitHub, Duolingo, Telegram, etc.)
                if (piv.pivot_type === "PUBLIC_PROFILE" || piv.pivot_type === "ACCOUNT_REGISTRATION") {
                    let linkMatch = piv.context_note ? piv.context_note.match(/\[URL:\s*(https?:\/\/[^\]]+)\]/) : null;
                    let url = linkMatch ? linkMatch[1] : null;
                    let cleanContext = piv.context_note ? piv.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*VERIFIED\]\s*/, '').trim() : "";

                    // Detect whether URL is a specific public profile or just a generic root portal
                    let isRootDomain = false;
                    if (url) {
                        try {
                            let parsedUrl = new URL(url);
                            let host = parsedUrl.hostname.toLowerCase();
                            let pathname = (parsedUrl.pathname || "").replace(/\/+$/, "");

                            // Known generic platform root domains where a bare URL (pathname === "") is only a portal
                            const genericRootPlatforms = [
                                "facebook.com", "m.facebook.com", "www.facebook.com",
                                "apple.com", "tv.apple.com",
                                "wix.com", "www.wix.com",
                                "wordpress.com", "www.wordpress.com",
                                "office365.com", "office.com", "microsoft.com",
                                "coursera.org", "www.coursera.org",
                                "hackthebox.com", "www.hackthebox.com",
                                "codecademy.com", "www.codecademy.com",
                                "pinterest.com", "www.pinterest.com",
                                "twitter.com", "x.com",
                                "linkedin.com", "www.linkedin.com"
                            ];

                            // Subdomain hosts (e.g. jordinzwaan.jouwweb.nl, user.github.io, user.carrd.co, user.wixsite.com) are genuine user sites, NOT root portals
                            let isUserSubdomain = host.includes(".jouwweb.nl") || 
                                                  host.includes(".github.io") || 
                                                  host.includes(".carrd.co") || 
                                                  host.includes(".wixsite.com") || 
                                                  host.includes(".pages.dev") || 
                                                  host.includes(".vercel.app") || 
                                                  host.includes(".netlify.app") || 
                                                  host.includes(".blogspot.com") ||
                                                  host.includes(".substack.com") ||
                                                  (piv.pivot_value && piv.pivot_value.toLowerCase().includes("portfolio"));

                            if (isUserSubdomain) {
                                isRootDomain = false;
                            } else if (genericRootPlatforms.includes(host)) {
                                isRootDomain = (!pathname || pathname === "");
                            } else {
                                isRootDomain = (!pathname || pathname === "");
                            }
                        } catch(e) {
                            isRootDomain = true;
                        }
                    }

                    // If URL is root or missing, check if handle is embedded in value or context
                    if (isRootDomain || !url) {
                        let handleMatch = piv.pivot_value.match(/@([a-zA-Z0-9_.-]+)/) || (piv.context_note && piv.context_note.match(/@([a-zA-Z0-9_.-]+)/));
                        if (handleMatch) {
                            let h = handleMatch[1];
                            let platLower = piv.pivot_value.toLowerCase();
                            if (platLower.includes("twitter") || platLower.includes("x:") || platLower.includes("x /")) {
                                url = `https://x.com/${h}`;
                                isRootDomain = false;
                            } else if (platLower.includes("github")) {
                                url = `https://github.com/${h}`;
                                isRootDomain = false;
                            } else if (platLower.includes("steam")) {
                                url = `https://steamcommunity.com/id/${h}`;
                                isRootDomain = false;
                            }
                        }
                    }

                    let isAccountPresenceOnly = (piv.pivot_type === "ACCOUNT_REGISTRATION") && ((!url) || isRootDomain);
                    let isDevProfile = piv.pivot_value.toLowerCase().includes("github") || piv.pivot_value.toLowerCase().includes("gitlab");
                    let isSteam = piv.pivot_value.toLowerCase().includes("steam");
                    let isPortfolio = piv.pivot_value.toLowerCase().includes("portfolio") || (url && url.toLowerCase().includes("jouwweb.nl"));

                    const platKey = normalizePlatform(piv.pivot_value);
                    const matchingCandidates = suspectedPivots.filter(sp => normalizePlatform(sp.pivot_value) === platKey);

                    let candidateHandlesHtml = "";
                    if (matchingCandidates.length > 0) {
                        candidateHandlesHtml = `
                            <div style="margin-top: 0.75rem; padding: 0.65rem 0.85rem; background: rgba(15, 23, 42, 0.65); border: 1px dashed rgba(245, 158, 11, 0.4); border-radius: 6px;">
                                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.45rem; flex-wrap: wrap; gap: 0.4rem;">
                                    <span style="font-size: 0.75rem; font-weight: 700; color: #fbbf24; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 0.35rem;">
                                        ${getUiIcon("search", "w-3 h-3 text-amber-400")} CANDIDATE IDENTIFIERS (${matchingCandidates.length})
                                    </span>
                                    <span style="font-size: 0.68rem; color: #94a3b8;">Platform masks username on email lookup</span>
                                </div>
                                <div style="display: flex; flex-direction: column; gap: 0.45rem;">
                                    ${matchingCandidates.map(c => {
                                        let cLink = c.context_note ? c.context_note.match(/\[URL:\s*(https?:\/\/[^\]]+)\]/) : null;
                                        let cUrl = cLink ? cLink[1] : null;
                                        let cCtx = c.context_note ? c.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*SUSPECTED\]\s*/, '').replace(/\[PLATFORM:\s*[^\]]+\]\s*/, '').trim() : "";
                                        if (cCtx.includes("Root stem derived from authenticated account login")) {
                                             cCtx = cCtx.replace("Root stem derived from authenticated account login", "Stem match:");
                                        }
                                        let cConf = Math.round((c.confidence_score || 0.6) * 100);
                                        let inspectTargetUrl = cUrl || (platKey === 'twitter' ? `https://x.com/${c.pivot_value.replace(/[^a-zA-Z0-9_]/g, '')}` : '');
                                        return `
                                            <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 4px; padding: 0.4rem 0.6rem; gap: 0.5rem; flex-wrap: wrap;">
                                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                                    <span style="color: #fbbf24; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;">${escapeHtml(c.pivot_value)}</span>
                                                    <span class="badge-pill" style="background: rgba(245, 158, 11, 0.15); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 0.65rem;">${cConf}% CONF</span>
                                                </div>
                                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                                    ${cCtx ? `<span style="font-size: 0.72rem; color: #94a3b8; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(cCtx)}</span>` : ''}
                                                    ${inspectTargetUrl ? `<a href="${escapeHtml(inspectTargetUrl)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #fbbf24; border-color: rgba(245, 158, 11, 0.4); font-size: 0.7rem; padding: 2px 6px; text-decoration: none;">Inspect &rarr;</a>` : ''}
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }

                    let isFb = piv.pivot_value.toLowerCase().includes("facebook");
                    let isLi = piv.pivot_value.toLowerCase().includes("linkedin");
                    let cardIcon = isDevProfile ? getUiIcon('github', 'w-4 h-4 text-sky-400') : (
                        isFb ? getUiIcon('facebook', 'w-4 h-4 text-blue-500') : (
                            isLi ? getUiIcon('linkedin', 'w-4 h-4 text-sky-400') : (
                                isSteam ? getUiIcon('globe', 'w-4 h-4 text-sky-400') : (
                                    isPortfolio ? getUiIcon('globe', 'w-4 h-4 text-purple-400') :
                                    getUiIcon('globe', 'w-4 h-4 text-purple-400')
                                )
                            )
                        )
                    );
                    let cardBorder = isDevProfile ? '#38bdf8' : (
                        isFb ? '#3b82f6' : (
                            isLi ? '#0ea5e9' : (
                                isSteam ? '#0284c7' : (
                                    isPortfolio ? '#a855f7' : (
                                        isAccountPresenceOnly ? '#a855f7' : '#38bdf8'
                                    )
                                )
                            )
                        )
                    );
                    let tagStyle = isDevProfile ? 'background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8;' : (
                        isFb ? 'background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3);' : (
                            isLi ? 'background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3);' : (
                                isSteam ? 'background: rgba(2, 132, 199, 0.15); color: #38bdf8; border: 1px solid rgba(2, 132, 199, 0.4);' : (
                                    isPortfolio ? 'background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);' : (
                                        isAccountPresenceOnly ? 'background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);' : 'background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);'
                                    )
                                )
                            )
                        )
                    );
                    let tagText = isDevProfile ? 'VERIFIED DEVELOPER ACCOUNT' : (
                        isFb ? 'VERIFIED FACEBOOK DOSSIER' : (
                            isLi ? 'VERIFIED LINKEDIN PROFILE' : (
                                isSteam ? 'VERIFIED STEAM PROFILE' : (
                                    isPortfolio ? 'LIVE OSINT PROFILE' : (
                                        isAccountPresenceOnly ? 'EMAIL REGISTRATION VERIFIED' : 'LIVE OSINT PROFILE'
                                    )
                                )
                            )
                        )
                    );

                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid ${cardBorder};">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${cardIcon} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="${tagStyle}">${tagText}</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Intelligence Signal:</strong> ${escapeHtml(cleanContext || (isAccountPresenceOnly ? 'Account registration confirmed on service' : 'Corroborated public footprint'))}</div>
                                ${!isAccountPresenceOnly && url ? `
                                    <div style="margin-top: 0.65rem; display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
                                        <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="btn-verified-profile-link">
                                            <span>View Verified Profile &rarr;</span>
                                            <span class="mono opacity-70 text-[11px]">${escapeHtml(url)}</span>
                                        </a>
                                        <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(url)}', 'Profile URL')">Copy URL</button>
                                    </div>
                                ` : `
                                    <div style="margin-top: 0.65rem; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap;">
                                        <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                                            <span style="font-size: 0.76rem; color: #94a3b8; display: inline-flex; align-items: center; gap: 0.35rem;">
                                                ${getUiIcon('lock', 'w-3 h-3 text-purple-400')} Registered on platform (handle masked by API)
                                            </span>
                                            ${(platKey === 'twitter' && targetFullName) ? `
                                                <a href="https://x.com/search?q=${encodeURIComponent(targetFullName)}&f=user" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none; font-size: 0.72rem; padding: 2px 8px;">
                                                    Search "${escapeHtml(targetFullName)}" on X &rarr;
                                                </a>
                                            ` : ''}
                                        </div>
                                        ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" style="color: #64748b; font-size: 0.74rem; text-decoration: underline;">Platform Portal &rarr;</a>` : ''}
                                    </div>
                                `}
                                ${candidateHandlesHtml}
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                                // Full Name / Person Identity Discovered
                if (piv.pivot_type === "FULL_NAME" || piv.pivot_type === "PERSON_NAME") {
                    const rawVal = piv.pivot_value.replace(/^Full Name:\s*/i, '').trim();
                    let cleanCtx = piv.context_note ? piv.context_note.replace(/\[STATUS:\s*VERIFIED\]\s*/g, '').trim() : '';
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #06b6d4;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-2">
                                    ${getUiIcon('user', 'w-4 h-4 text-cyan-400')}
                                    <span class="text-zinc-400 font-mono text-xs uppercase tracking-wider">Identified Target:</span>
                                    <span class="text-zinc-100 font-semibold">${escapeHtml(rawVal)}</span>
                                </span>
                                <span class="evidence-tag" style="background: rgba(6, 182, 212, 0.15); color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.3);">
                                    CONFIDENCE: ${Math.round((piv.confidence_score || 0.95) * 100)}% // VERIFIED
                                </span>
                            </div>
                            <div class="evidence-body">
                                <div style="font-size: 0.8rem; color: #94a3b8;">
                                    <strong>Source Attribution:</strong> ${escapeHtml(cleanCtx || 'Discovered via Git commit metadata and repository signatures.')}
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "OPENPGP_KEY") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #10b981;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("key", "w-4 h-4 text-emerald-400")} OpenPGP Public Key Found</span>
                                <span class="evidence-tag" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981;">KEYSERVER VERIFIED</span>
                            </div>
                            <div class="evidence-body">
                                <div class="code-field" style="color: #34d399;">${escapeHtml(piv.pivot_value)}</div>
                                <div style="margin-top: 0.3rem;"><strong>Context:</strong> ${escapeHtml(piv.context_note || '')}</div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "ALTERNATE_EMAIL") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #06b6d4;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("mail", "w-4 h-4 text-cyan-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3);">CRYPTOGRAPHIC LINK</span>
                            </div>
                            <div class="evidence-body">
                                <div style="font-size: 0.8rem; color: #94a3b8;">
                                    <strong>Context:</strong> ${escapeHtml(piv.context_note || 'Cryptographically verified inbox discovered on public PGP key.')}
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                // Semantic Career, Education & Technical Stack Cards
                if (piv.pivot_type === "EDUCATION") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #3b82f6;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-blue-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.3);">ALMA MATER</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Academic Context:</strong> ${escapeHtml(piv.context_note || '')}</div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "WORKPLACE") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #f59e0b;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-amber-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(245, 158, 11, 0.15); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.3);">EXPERIENCE</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Professional Details:</strong> ${escapeHtml(piv.context_note || '')}</div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "FLAGSHIP_PROJECT") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #a855f7;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("globe", "w-4 h-4 text-purple-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(168, 85, 247, 0.15); color: #d8b4fe; border: 1px solid rgba(168, 85, 247, 0.3);">ENGINEERING INITIATIVE</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Scope & Tech:</strong> ${escapeHtml(piv.context_note || '')}</div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "TECH_STACK") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #06b6d4;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("cpu", "w-4 h-4 text-cyan-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(6, 182, 212, 0.15); color: #a5f3fc; border: 1px solid rgba(6, 182, 212, 0.3);">TECHNICAL COMPETENCY</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Extracted Profile Stack:</strong> ${escapeHtml(piv.context_note || '')}</div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "PERSONA_PIVOT") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #c084fc;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5" style="color: #d8b4fe;">${getUiIcon("userCheck", "w-4 h-4 text-purple-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(192, 132, 252, 0.15); color: #d8b4fe; border: 1px solid rgba(192, 132, 252, 0.3);">RECURSIVE PERSONA PIVOT</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Identity Correlation:</strong> ${escapeHtml(piv.context_note || 'Harvested candidate alias.')}</div>
                                <div style="margin-top: 0.35rem; font-size: 0.75rem; color: #94a3b8;">
                                    Discovered via recursive profile inspection and probed across external networks.
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "SUBDOMAIN_ASSET") {
                    const isHigh = (piv.context_note || "").includes("Risk: HIGH");
                    const borderCol = isHigh ? "#ef4444" : "#f59e0b";
                    const tagCol = isHigh ? "rgba(239, 68, 68, 0.15)" : "rgba(245, 158, 11, 0.15)";
                    const textCol = isHigh ? "#f87171" : "#fbbf24";
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid ${borderCol};">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-amber-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: ${tagCol}; color: ${textCol}; border: 1px solid ${borderCol};">${isHigh ? 'HIGH RISK GATEWAY' : 'CORPORATE ASSET'}</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Attack Surface:</strong> ${escapeHtml(piv.context_note || 'External corporate login portal')}</div>
                                <div style="margin-top: 0.35rem; font-size: 0.75rem; color: #94a3b8;">
                                    Recon Signal: Discovered via Certificate Transparency / DNS probing.
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "EMAIL_PERMUTATION") {
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #818cf8;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon("mail", "w-4 h-4 text-indigo-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(129, 140, 248, 0.15); color: #818cf8; border: 1px solid rgba(129, 140, 248, 0.3);">CORPORATE PERMUTATIONS</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Enterprise Schemes:</strong> ${escapeHtml(piv.context_note || 'Generated corporate format patterns')}</div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                if (piv.pivot_type === "TIMELINE") {
                    return;
                }

                // Dedicated Business Associate / Partner Card
                if (piv.pivot_type === "BUSINESS_ASSOCIATE") {
                    let cleanCtx = piv.context_note ? piv.context_note.replace(/\[STATUS:\s*VERIFIED\]\s*/g, '').trim() : '';
                    let partnerName = piv.pivot_value.replace(/^(Co-Partner|Business Partner|Associate):\s*/i, '').trim();
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #f59e0b;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-2">
                                    ${getUiIcon('users', 'w-4 h-4 text-amber-400')}
                                    <span class="text-zinc-400 font-mono text-xs uppercase tracking-wider">Business Associate:</span>
                                    <span class="text-zinc-100 font-semibold">${escapeHtml(partnerName)}</span>
                                </span>
                                <span class="evidence-tag" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3);">
                                    KVK VERIFIED (${Math.round((piv.confidence_score || 0.98) * 100)}%)
                                </span>
                            </div>
                            <div class="evidence-body">
                                <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap;">
                                    <div style="font-size: 0.8rem; color: #94a3b8;">
                                        <strong>Corporate Partnership:</strong> ${escapeHtml(cleanCtx || 'Verified co-partner in corporate registry.')}
                                    </div>
                                    <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(partnerName)}', 'Partner Name')">Copy</button>
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                // Dedicated Cross-Platform Avatar Correlation Card
                if (piv.pivot_type === "AVATAR_CORRELATION") {
                    let avatarUrlMatch = piv.pivot_value.match(/(https?:\/\/[^\s]+)/) || (piv.context_note && piv.context_note.match(/(https?:\/\/[^\s]+)/));
                    let avatarUrl = avatarUrlMatch ? avatarUrlMatch[1].replace(/\]$/, '') : "";
                    let cleanCtx = piv.context_note ? piv.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*VERIFIED\]\s*/g, '').trim() : '';
                    let platformName = avatarUrl.includes("github") ? "GitHub" : (avatarUrl.includes("gravatar") ? "Gravatar" : "Public Platform");
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #8b5cf6;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-2">
                                    ${getUiIcon('user', 'w-4 h-4 text-purple-400')}
                                    <span class="text-zinc-400 font-mono text-xs uppercase tracking-wider">Avatar Identity:</span>
                                    <span class="text-zinc-100 font-semibold">${escapeHtml(platformName)} Visual Asset</span>
                                </span>
                                <span class="evidence-tag" style="background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3);">
                                    AVATAR CORRELATION (${Math.round((piv.confidence_score || 0.92) * 100)}%)
                                </span>
                            </div>
                            <div class="evidence-body">
                                <div style="display: flex; align-items: center; gap: 0.9rem; margin-top: 0.25rem;">
                                    ${avatarUrl ? `
                                        <div style="flex-shrink: 0; width: 44px; height: 44px; border-radius: 8px; overflow: hidden; border: 1px solid rgba(139, 92, 246, 0.4); background: #0f172a;">
                                            <img src="${escapeHtml(avatarUrl)}" alt="Avatar Footprint" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none'">
                                        </div>
                                    ` : ''}
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="font-size: 0.8rem; color: #94a3b8;">
                                            <strong>Visual Signal:</strong> ${escapeHtml(cleanCtx || 'Visual avatar footprint discovered on public repository.')}
                                        </div>
                                        ${avatarUrl ? `
                                            <div style="margin-top: 0.35rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                                                <a href="${escapeHtml(avatarUrl)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #a78bfa; border-color: rgba(139, 92, 246, 0.4); text-decoration: none; font-size: 0.72rem; padding: 2px 7px;">Open Image &rarr;</a>
                                                <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(avatarUrl)}', 'Avatar URL')">Copy URL</button>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                // Dedicated Telecom / Phone Number Card
                if (piv.pivot_type === "PHONE_NUMBER") {
                    let cleanCtx = piv.context_note ? piv.context_note.replace(/\[STATUS:\s*VERIFIED\]\s*/g, '').trim() : '';
                    let waMatch = piv.context_note ? piv.context_note.match(/\[Direct WhatsApp:\s*(https?:\/\/[^\]]+)\]/) : null;
                    let waUrl = waMatch ? waMatch[1] : null;
                    addPivotCard(`
                        <div class="evidence-card" style="border-left: 3px solid #10b981;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-2">
                                    <svg class="w-4 h-4 text-emerald-400 inline-block align-middle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                                    <span class="text-zinc-400 font-mono text-xs uppercase tracking-wider">Telecom Line:</span>
                                    <span class="text-zinc-100 font-semibold font-mono">${escapeHtml(piv.pivot_value)}</span>
                                </span>
                                <span class="evidence-tag" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3);">
                                    TELECOM VERIFIED (${Math.round((piv.confidence_score || 0.95) * 100)}%)
                                </span>
                            </div>
                            <div class="evidence-body">
                                <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap;">
                                    <div style="font-size: 0.8rem; color: #94a3b8;">
                                        <strong>Carrier Signal:</strong> ${escapeHtml(cleanCtx || 'Verified cellular line attributed to subject.')}
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 0.4rem;">
                                        ${waUrl ? `<a href="${escapeHtml(waUrl)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #4ade80; border-color: rgba(34, 197, 94, 0.4); text-decoration: none; font-size: 0.72rem; padding: 2px 7px;">Message WhatsApp &rarr;</a>` : ''}
                                        <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(piv.pivot_value)}', 'Phone')">Copy</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `, getPivotCategory(piv), piv.context_note);
                    return;
                }

                // General Fallback Evidence Card (with human-readable label and icon)
                let waMatch = piv.context_note ? piv.context_note.match(/\[Direct WhatsApp:\s*(https?:\/\/[^\]]+)\]/) : null;
                let waUrl = waMatch ? waMatch[1] : null;
                let humanType = (piv.pivot_type || "SIGNAL").replace(/_/g, ' ');
                let pivotValHtml = `
                    <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
                        <div class="code-field" style="color: #67e8f9; font-weight: 700; font-size: 0.95rem;">${escapeHtml(piv.pivot_value)}</div>
                        ${waUrl ? `<a href="${escapeHtml(waUrl)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #4ade80; border-color: rgba(34, 197, 94, 0.4); text-decoration: none;">Message WhatsApp &rarr;</a>` : ''}
                        <button type="button" class="btn-copy-mini mono" onclick="copyToClipboard('${escapeHtml(piv.pivot_value)}', 'Pivot')">Copy</button>
                    </div>
                `;

                addPivotCard(`
                    <div class="evidence-card" style="border-left: 3px solid #06b6d4;">
                        <div class="evidence-header">
                            <span class="evidence-title flex items-center gap-1.5">
                                ${getUiIcon("shield", "w-3.5 h-3.5 text-cyan-400")}
                                <span class="font-mono text-xs uppercase tracking-wider text-zinc-300">${escapeHtml(humanType)}</span>
                            </span>
                            <span class="evidence-tag" style="background: rgba(6, 182, 212, 0.15); color: #67e8f9; border: 1px solid rgba(6, 182, 212, 0.3);">CONFIDENCE: ${Math.round((piv.confidence_score || 0.8) * 100)}%</span>
                        </div>
                        <div class="evidence-body">
                            ${pivotValHtml}
                            <div style="margin-top: 0.4rem; font-size: 0.8rem; color: #94a3b8;"><strong>Context:</strong> ${escapeHtml(piv.context_note || '')}</div>
                        </div>
                    </div>
                `, getPivotCategory(piv), piv.context_note);
            });

            if (suspectedPivots.length > 0) {
                pivotsContainer.innerHTML += `
                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px dashed rgba(245, 158, 11, 0.3);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.8rem; flex-wrap: wrap; gap: 0.5rem;">
                            <span class="evidence-title flex items-center gap-1.5" style="color: #fbbf24; font-size: 0.88rem;">
                                ${getUiIcon("search", "w-4 h-4 text-amber-400")} CANDIDATE PROFILES &amp; SUSPECTED ALIASES (${suspectedPivots.length})
                            </span>
                            <span class="badge-pill" style="background: rgba(245, 158, 11, 0.15); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 0.68rem;">
                                CANDIDATE LEDGER
                            </span>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 0.6rem;">
                            ${suspectedPivots.map(sp => {
                                let cLink = sp.context_note ? sp.context_note.match(/\[URL:\s*(https?:\/\/[^\]]+)\]/) : null;
                                let cUrl = cLink ? cLink[1] : null;
                                let cCtx = sp.context_note ? sp.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*SUSPECTED\]\s*/, '').replace(/\[PLATFORM:\s*[^\]]+\]\s*/, '').trim() : "";
                                let cConf = Math.round((sp.confidence_score || 0.65) * 100);
                                return `
                                    <div class="evidence-card" style="border-left: 3px solid #f59e0b; margin-bottom: 0;">
                                        <div class="evidence-header">
                                            <span class="evidence-title flex items-center gap-1.5" style="color: #fbbf24;">${getUiIcon("search", "w-3.5 h-3.5 text-amber-400")} ${escapeHtml(sp.pivot_value)}</span>
                                            <span class="evidence-tag" style="background: rgba(245, 158, 11, 0.15); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 0.68rem;">${cConf}% CONF</span>
                                        </div>
                                        <div class="evidence-body">
                                            <div><strong>Analysis:</strong> ${escapeHtml(cCtx || 'Candidate account identified via handle enumeration.')}</div>
                                            ${cUrl ? `<div style="margin-top: 0.4rem;"><a href="${escapeHtml(cUrl)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #fbbf24; border-color: rgba(245, 158, 11, 0.4); text-decoration: none;">Inspect Profile &rarr;</a></div>` : ''}
                                        </div>
                                    </div>
                                `;
                            }).join("")}
                        </div>
                    </div>
                `;
            }
        }
    }

    // 3b. Suspected Candidate Accounts (Segregated Quarantine Ledger)
    const suspectedContainer = document.getElementById("tab-suspected-content");
    if (suspectedContainer) {
        suspectedContainer.innerHTML = "";
        if (suspectedPivots.length === 0) {
            suspectedContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} Clean Attribution Ledger</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">Zero speculative handles or uncorroborated candidate profiles quarantined. Every exposed account on the primary graph has satisfied deterministic multi-signal validation.</div>
                </div>`;
        } else {
            // Platforms that only have ACCOUNT_REGISTRATION (email exists, but handle is masked / unknown)
            const emailOnlyUnresolvedPlatforms = new Set(
                verifiedPivots
                    .filter(p => p.pivot_type === "ACCOUNT_REGISTRATION")
                    .map(p => normalizePlatform(p.pivot_value))
                    .filter(plat => !fullyResolvedPlatforms.has(plat))
            );

            const verifiedServiceCandidates = suspectedPivots.filter(p => 
                emailOnlyUnresolvedPlatforms.has(normalizePlatform(p.pivot_value)) || 
                (p.context_note && p.context_note.includes("[PLATFORM: VERIFIED_EMAIL]"))
            );
            const unconfirmedServiceCandidates = suspectedPivots.filter(p => !verifiedServiceCandidates.includes(p));

            suspectedContainer.innerHTML = `
                <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; padding: 12px 16px; margin-bottom: 14px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            ${getUiIcon("search", "w-4 h-4 text-amber-400")}
                            <strong style="color: #fbbf24; font-size: 0.88rem; font-family: 'JetBrains Mono', monospace;">ANALYST SUSPECTED CANDIDATES LEDGER</strong>
                        </div>
                        <span class="badge-pill" style="background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); font-family: 'JetBrains Mono', monospace;">
                            QUARANTINED FROM ATTACK GRAPH
                        </span>
                    </div>
                    <p style="font-size: 0.8rem; color: #d1d5db; margin: 8px 0 0 0; line-height: 1.45;">
                        Candidate handles investigated for the target are cataloged below. Accounts are grouped by whether the <strong>target email is confirmed registered on that platform</strong> (high-value leads) or whether the platform itself is <strong>unconfirmed</strong> (speculative alias matches).
                    </p>
                </div>
            `;

            // Section 1: Candidate Handles on Confirmed Services
            if (verifiedServiceCandidates.length > 0) {
                suspectedContainer.innerHTML += `
                    <div style="margin: 1.2rem 0 0.6rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid rgba(56, 189, 248, 0.25); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div style="display: flex; align-items: center; gap: 0.4rem;">
                            <span style="color: #38bdf8; font-weight: 700; font-size: 0.86rem; font-family: 'JetBrains Mono', monospace;">
                                CANDIDATES ON CONFIRMED EMAIL PLATFORMS (${verifiedServiceCandidates.length})
                            </span>
                        </div>
                        <span class="badge-pill" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); font-size: 0.68rem;">
                            CONFIRMED EMAIL REGISTRATION
                        </span>
                    </div>
                    <div style="font-size: 0.76rem; color: #94a3b8; margin-bottom: 0.75rem; line-height: 1.4;">
                        Target email address is confirmed registered on these services, but the platform masks the public username. These candidate handles were derived from known aliases and represent high-probability profile leads.
                    </div>
                `;

                verifiedServiceCandidates.forEach(piv => {
                    let linkMatch = piv.context_note ? piv.context_note.match(/\[URL:\s*(https?:\/\/[^\]]+)\]/) : null;
                    let url = linkMatch ? linkMatch[1] : null;
                    let cleanContext = piv.context_note ? piv.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*SUSPECTED\]\s*/, '').replace(/\[PLATFORM:\s*[^\]]+\]\s*/, '').trim() : "";
                    let confPct = Math.round((piv.confidence_score || 0.6) * 100);

                    suspectedContainer.innerHTML += `
                        <div class="evidence-card" style="border-left: 3px solid #38bdf8; margin-bottom: 0.75rem;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5" style="color: #38bdf8;">${getUiIcon("search", "w-3.5 h-3.5 text-sky-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35);">
                                    CONFIRMED SERVICE • CANDIDATE (${confPct}% CONF)
                                </span>
                            </div>
                            <div class="evidence-body">
                                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                                    <div><strong>Investigative Signal:</strong> <span style="color: var(--t-secondary);">${escapeHtml(cleanContext || 'Candidate handle probed on confirmed service.')}</span></div>
                                    <div style="font-size: 0.75rem; color: #94a3b8; display: flex; align-items: center; gap: 0.4rem;">
                                        ${getUiIcon("alert", "w-3 h-3 text-sky-400")}
                                        <span>Target email confirmed on platform; public handle requires manual profile inspection.</span>
                                    </div>
                                </div>
                                ${url ? `
                                    <div style="margin-top: 0.6rem;">
                                        <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none; font-size: 0.74rem;">
                                            Inspect Candidate Profile &rarr;
                                        </a>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                });
            }

            // Section 2: Speculative Candidates on Unconfirmed Services
            if (unconfirmedServiceCandidates.length > 0) {
                suspectedContainer.innerHTML += `
                    <div style="margin: ${verifiedServiceCandidates.length > 0 ? '1.5rem' : '1.0rem'} 0 0.6rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid rgba(245, 158, 11, 0.25); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div style="display: flex; align-items: center; gap: 0.4rem;">
                            <span style="color: #fbbf24; font-weight: 700; font-size: 0.86rem; font-family: 'JetBrains Mono', monospace;">
                                SPECULATIVE CANDIDATES ON UNCONFIRMED SERVICES (${unconfirmedServiceCandidates.length})
                            </span>
                        </div>
                        <span class="badge-pill" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); font-size: 0.68rem;">
                            UNVERIFIED SERVICE PRESENCE
                        </span>
                    </div>
                    <div style="font-size: 0.76rem; color: #94a3b8; margin-bottom: 0.75rem; line-height: 1.4;">
                        These candidate handles were matched on gaming, forum, or coding services where the target email itself was not confirmed. Held in review ledger to prevent vanity collisions.
                    </div>
                `;

                unconfirmedServiceCandidates.forEach(piv => {
                    let linkMatch = piv.context_note ? piv.context_note.match(/\[URL:\s*(https?:\/\/[^\]]+)\]/) : null;
                    let url = linkMatch ? linkMatch[1] : null;
                    let cleanContext = piv.context_note ? piv.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*SUSPECTED\]\s*/, '').replace(/\[PLATFORM:\s*[^\]]+\]\s*/, '').trim() : "";
                    let confPct = Math.round((piv.confidence_score || 0.6) * 100);

                    suspectedContainer.innerHTML += `
                        <div class="evidence-card" style="border-left: 3px solid #f59e0b; margin-bottom: 0.75rem;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5" style="color: #fbbf24;">${getUiIcon("search", "w-3.5 h-3.5 text-amber-400")} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;">
                                    SPECULATIVE (${confPct}% CONF)
                                </span>
                            </div>
                            <div class="evidence-body">
                                <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                                    <div><strong>Triage Reason:</strong> <span style="color: var(--t-secondary);">${escapeHtml(cleanContext || 'Candidate account identified via username stem matching.')}</span></div>
                                    <div style="font-size: 0.75rem; color: #94a3b8; display: flex; align-items: center; gap: 0.4rem;">
                                        ${getUiIcon("alert", "w-3 h-3 text-amber-400")}
                                        <span>Telemetry Gap: Lacks confirmed email binding on this service. Risk of unrelated vanity collision.</span>
                                    </div>
                                </div>
                                ${url ? `
                                    <div style="margin-top: 0.6rem;">
                                        <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #fbbf24; border-color: rgba(245, 158, 11, 0.4); text-decoration: none; font-size: 0.74rem;">
                                            Manual Inspection: Open Candidate Profile &rarr;
                                        </a>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                });
            }
        }
    }

    // 4. Physical Address & Relatives
    const physicalContainer = document.getElementById("tab-physical-list");
    if (physicalContainer) {
        physicalContainer.innerHTML = "";
        const hasAddr = data.physical_footprints && data.physical_footprints.length > 0;
        const hasRels = data.relatives && data.relatives.length > 0;

        if (!hasAddr && !hasRels) {
            physicalContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} Physical Footprint Protected</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">No residential home addresses or household family contacts unmasked.</div>
                </div>`;
            const mapContainerEl = document.getElementById("map-container");
            if (mapContainerEl) mapContainerEl.style.display = "none";
        } else {
            const mapContainerEl = document.getElementById("map-container");
            if (mapContainerEl) mapContainerEl.style.display = "block";
            // Initialize or update Leaflet map
            if (!window.geoMap) {
                window.geoMap = L.map('map-container').setView([0, 0], 2);
                const isLight = isCurrentThemeLight();
                window.currentTileLayer = L.tileLayer(getMapTileUrl(isLight), {
                    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                    subdomains: 'abcd',
                    maxZoom: 20
                }).addTo(window.geoMap);
            }
            
            // Clear existing markers
            if (window.geoMarkers) {
                window.geoMap.removeLayer(window.geoMarkers);
            }
            window.geoMarkers = L.layerGroup().addTo(window.geoMap);
            let bounds = L.latLngBounds();

            if (hasAddr) {
                data.physical_footprints.forEach(foot => {
                    let addrHtml = `
                        <div style="margin-bottom: 0.4rem; padding: 0.4rem 0.6rem; background: var(--accent-emerald-subtle); border-left: 3px solid var(--accent-emerald); border-radius: 4px; font-size: 0.75rem; color: var(--accent-emerald);">
                            ${getUiIcon("mapPin", "w-3 h-3 text-emerald-400 inline mr-1")} <strong>Corroborated Residential Asset</strong>
                        </div>
                        <div><strong>Record:</strong> <span class="code-field" style="color: var(--accent-emerald); font-weight: 700;">${escapeHtml(foot.address_line)}</span></div>
                        <div><strong>City & Region:</strong> ${escapeHtml(foot.city || 'N/A')}, ${escapeHtml(foot.country || 'N/A')}</div>
                    `;

                    physicalContainer.innerHTML += `
                        <div class="evidence-card" style="border-left: 3px solid #10b981;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon('mapPin', 'w-3.5 h-3.5 text-emerald-400')} ${escapeHtml(foot.city || foot.address_line)}</span>
                                <span class="evidence-tag" style="background: var(--accent-emerald-subtle); color: var(--accent-emerald); border: 1px solid var(--accent-emerald);">${escapeHtml(foot.exposure_type)}</span>
                            </div>
                            <div class="evidence-body">
                                ${addrHtml}
                            </div>
                        </div>
                    `;

                    // Add map marker
                    if (foot.latitude && foot.longitude) {
                        const marker = L.circleMarker([foot.latitude, foot.longitude], {
                            color: '#34d399',
                            fillColor: '#10b981',
                            fillOpacity: 0.5,
                            radius: 8
                        }).addTo(window.geoMarkers);
                        marker.bindPopup(`<strong>${escapeHtml(foot.city)}</strong><br>${escapeHtml(foot.address_line)}`);
                        bounds.extend([foot.latitude, foot.longitude]);
                    }
                });
            }

            if (bounds.isValid()) {
                window.geoMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
            }

            if (hasRels) {
                data.relatives.forEach(rel => {
                    let relHtml = `
                        <div style="margin-bottom: 0.4rem; padding: 0.4rem 0.6rem; background: var(--accent-emerald-subtle); border-left: 3px solid var(--accent-emerald); border-radius: 4px; font-size: 0.75rem; color: var(--accent-emerald);">
                            ${getUiIcon("users", "w-3 h-3 text-emerald-400 inline mr-1")} <strong>Family / Cohabitant Profile</strong>
                        </div>
                        <div><strong>Full Name:</strong> <span class="code-field" style="color: #f472b6; font-weight: 700;">${escapeHtml(rel.full_name)}</span></div>
                        <div><strong>Contact Email:</strong> <code>${escapeHtml(rel.contact_email || 'N/A')}</code> | <strong>Telephone:</strong> <code>${escapeHtml(rel.contact_phone || 'N/A')}</code></div>
                    `;

                    physicalContainer.innerHTML += `
                        <div class="evidence-card" style="border-left: 3px solid #ec4899;">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${getUiIcon('users', 'w-3.5 h-3.5 text-pink-400')} Household Contact: ${escapeHtml(rel.full_name)} (${escapeHtml(rel.relationship)})</span>
                                <span class="evidence-tag" style="background: rgba(236, 72, 153, 0.2); color: #f472b6; border: 1px solid #ec4899;">RELATION: ${escapeHtml(rel.relationship)}</span>
                            </div>
                            <div class="evidence-body">
                                ${relHtml}
                            </div>
                        </div>
                    `;
                });
            }
        }

        // Render International Telecom & Multi-Country Citizen Directories
        renderMultiCountryTelecomSection(data, physicalContainer);
    }

    // 5. Remediation (SOC Playbook)
    const remediationsContainer = document.getElementById("tab-remediations-content");
    if (remediationsContainer) {
        remediationsContainer.innerHTML = "";
        data.spillover_score.remediations.forEach(rem => {
            const isP0 = rem.priority.includes("P0");
            const priorityBadge = isP0 
                ? "background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;" 
                : (rem.priority.includes("INFO") ? "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;" : "background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;");

            remediationsContainer.innerHTML += `
                <div class="evidence-card" style="border-left: 3px solid ${isP0 ? '#ef4444' : '#06b6d4'};">
                    <div class="evidence-header">
                        <span class="evidence-title">${escapeHtml(rem.title)}</span>
                        <span class="evidence-tag" style="${priorityBadge}">${escapeHtml(rem.priority)}</span>
                    </div>
                    <div class="evidence-body" style="margin-bottom: 0.25rem; font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase;">
                        Vector: ${escapeHtml(rem.vector)}
                    </div>
                    <div class="evidence-body">${escapeHtml(rem.description)}</div>
                </div>
            `;
        });
    }

    // 6. Threat Provenance & Adversary Capability Matrix
    const provContainer = document.getElementById("tab-provenance-content");
    if (provContainer) {
        provContainer.innerHTML = "";
        
        // 6a. Cross-Vector Compounding Scenarios
        const scenarios = (data.spillover_score && data.spillover_score.compounding_scenarios) || [];
        if (scenarios.length > 0) {
            let scenariosHtml = `
                <div class="compounding-section">
                    <div class="compounding-section-title">
                        <span>CROSS-VECTOR COMPOUNDING ATTACK SCENARIOS</span>
                        <span class="badge-pill badge-neutral" style="font-size: 0.65rem;">ATT&CK CORRELATED</span>
                    </div>
                    <div class="compounding-grid">
            `;

            scenarios.forEach(sc => {
                const isTrig = sc.triggered;
                const trigClass = isTrig ? "triggered" : "inactive";
                const badgeClass = isTrig ? "badge-triggered" : "badge-inactive";
                const badgeText = isTrig ? `[TRIGGERED: ${sc.multiplier}x RISK]` : `[UNTRIGGERED: 1.00x]`;
                
                let mitreTagsHtml = "";
                if (sc.mitre_tactics && sc.mitre_tactics.length > 0) {
                    mitreTagsHtml = `
                        <div class="compounding-mitre-row">
                            ${sc.mitre_tactics.map(m => `<span class="mitre-tag">${escapeHtml(m)}</span>`).join("")}
                        </div>
                    `;
                }

                scenariosHtml += `
                    <div class="compounding-card ${trigClass}">
                        <div class="compounding-head">
                            <span class="compounding-title">${escapeHtml(sc.title)}</span>
                            <span class="compounding-badge ${badgeClass}">${badgeText}</span>
                        </div>
                        <div class="compounding-desc">${escapeHtml(sc.explanation)}</div>
                        ${mitreTagsHtml}
                    </div>
                `;
            });

            scenariosHtml += `</div></div>`;
            provContainer.innerHTML += scenariosHtml;
        }

        // 6b. Threat Provenance Asset Matrix
        const matrix = data.threat_provenance_matrix || [];
        if (matrix.length === 0) {
            provContainer.innerHTML += `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} No Adversary Exploitation Vectors</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">Zero sensitive PII, phone numbers, passwords, or physical address exposures were linked to this identity.</div>
                </div>`;
        } else {
            provContainer.innerHTML += `
                <div class="compounding-section-title" style="margin-top: 0.5rem;">
                    <span>EXFILTRATED ASSET PROVENANCE & ADVERSARY CAPABILITY</span>
                </div>
            `;
            matrix.forEach(item => {
                const sev = item.threat_severity || "MEDIUM";
                const sevBadge = sev === "CRITICAL"
                    ? "badge-critical"
                    : (sev === "HIGH" ? "badge-high" : "badge-medium");

                provContainer.innerHTML += `
                    <div class="threat-card">
                        <div class="threat-card-top">
                            <span class="threat-asset-name">${escapeHtml(item.asset_name)} <span style="font-size: 0.72rem; color: var(--t-muted); font-weight: normal;">(${escapeHtml(item.asset_category)})</span></span>
                            <span class="badge-pill ${sevBadge}">${escapeHtml(sev)} THREAT</span>
                        </div>
                        <div class="threat-meta-grid">
                            <div class="threat-meta-item">
                                <strong>Origin Breach / Source:</strong>
                                <span class="threat-meta-val" style="color: #38bdf8;">${escapeHtml(item.origin_incident)}</span>
                            </div>
                            <div class="threat-meta-item">
                                <strong>Exfiltration Vector:</strong>
                                <span class="threat-meta-val">${escapeHtml(item.exfiltration_method)}</span>
                            </div>
                            <div class="threat-meta-item" style="grid-column: span 2;">
                                <strong>Adversary Capability:</strong>
                                <span class="threat-meta-val" style="color: #f87171; font-weight: 600;">${escapeHtml(item.attacker_capability)}</span>
                            </div>
                        </div>
                        <div class="threat-desc-box">
                            <strong>How an Attacker Discovers / Exploits This:</strong> ${escapeHtml(item.threat_description)}
                        </div>
                        <div class="threat-remed-box">
                            <strong>Countermeasure:</strong> ${escapeHtml(item.remediation)}
                        </div>
                    </div>
                `;
            });
        }
    }

    // 7. Adversary Attack Narrative (Playbook)
    const playbookContainer = document.getElementById("tab-playbook-content");
    if (playbookContainer) {
        playbookContainer.innerHTML = "";
        const playbook = (data.spillover_score && data.spillover_score.adversary_playbook) || [];
        if (playbook.length === 0) {
            playbookContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} Identity Untargeted</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">No correlated threat data exists to construct an adversary attack progression.</div>
                </div>`;
        } else {
            let flowHtml = `<div class="playbook-flow">`;
            playbook.forEach(step => {
                const sev = step.risk_severity || "MEDIUM";
                const sevBadge = sev === "CRITICAL"
                    ? "badge-critical"
                    : (sev === "HIGH" ? "badge-high" : "badge-medium");

                const mechPills = (step.mechanisms || []).map(m => 
                    `<span class="mechanism-pill">${escapeHtml(m)}</span>`
                ).join(" ");

                const relatedGroups = (step.related_groups || []).join(",");

                flowHtml += `
                    <div class="playbook-step-card" data-groups="${escapeHtml(relatedGroups)}" onclick="highlightPlaybookStage(this)" style="cursor: pointer; transition: all 0.2s ease;">
                        <div class="playbook-step-header">
                            <div class="playbook-phase-group">
                                <div class="playbook-step-num">0${step.stage_num}</div>
                                <span class="playbook-phase-name">${escapeHtml(step.phase_name)}</span>
                            </div>
                            <span class="badge-pill ${sevBadge}">${escapeHtml(sev)}</span>
                        </div>
                        <div class="playbook-action-text">${escapeHtml(step.action)}</div>
                        <div class="playbook-details-box">
                            <div class="playbook-detail-line">
                                <span class="playbook-detail-label">Target Assets:</span>
                                <span class="playbook-detail-val mono">${escapeHtml(step.target_assets)}</span>
                            </div>
                            <div class="playbook-detail-line">
                                <span class="playbook-detail-label">Mechanisms:</span>
                                <div class="playbook-mechanisms-strip">${mechPills}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            flowHtml += `</div>`;
            playbookContainer.innerHTML = flowHtml;
        }
    }

window.highlightPlaybookStage = function(element) {
    if (!networkInstance || !currentNodesDataSet) return;

    // Reset styles
    document.querySelectorAll('.playbook-step-card').forEach(el => el.classList.remove('active-playbook-stage'));
    element.classList.add('active-playbook-stage');

    const groupsStr = element.getAttribute('data-groups') || "";
    if (!groupsStr) {
        networkInstance.unselectAll();
        return;
    }

    const targetGroups = groupsStr.split(",");
    const allNodes = currentNodesDataSet.get();
    
    const targetNodeIds = allNodes.filter(n => n.group === 'employee' || n.group === 'Target').map(n => n.id);
    
    // Playbook groups from backend are uppercase/friendly (e.g. "Location", "Phone").
    // We map them to node categories or groups.
    const nodeIdsToSelect = allNodes
        .filter(n => {
            if (n.group === 'employee' || n.group === 'Target') return true;
            
            // fuzzy match playbook groups to node labels/groups
            const groupLower = n.group ? n.group.toLowerCase() : "";
            const catLower = n.category ? n.category.toLowerCase() : "";
            const lblLower = n.label ? n.label.toLowerCase() : "";
            const pTypeLower = (n.data && n.data.pivot_type) ? n.data.pivot_type.toLowerCase() : "";
            
            return targetGroups.some(tg => {
                const tgLow = tg.trim().toLowerCase();
                if (!tgLow) return false;
                if (tgLow === "location" && (groupLower.includes("geo") || groupLower.includes("physical"))) return true;
                if (tgLow === "phone" && (lblLower.includes("phone") || pTypeLower.includes("phone"))) return true;
                if (tgLow === "email" && (lblLower.includes("email") || pTypeLower.includes("email"))) return true;
                if (tgLow === "relative" && (groupLower.includes("relative") || catLower.includes("family"))) return true;
                if (tgLow === "social" && (groupLower.includes("account") || catLower.includes("account"))) return true;
                
                return groupLower.includes(tgLow) || catLower.includes(tgLow) || lblLower.includes(tgLow);
            });
        })
        .map(n => n.id);

    if (nodeIdsToSelect.length > 0) {
        networkInstance.selectNodes(nodeIdsToSelect);
        networkInstance.fit({ nodes: nodeIdsToSelect, animation: true });
    } else {
        networkInstance.unselectAll();
    }
};

    // 8. Identity & Incident Evolution Timeline
    const timelineContainer = document.getElementById("tab-timeline-content");
    if (timelineContainer) {
        timelineContainer.innerHTML = "";
        const timelineList = data.timeline || [];
        if (timelineList.length === 0) {
            timelineContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title" style="color: #34d399;">No Chronological Milestones Detected</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">No dated career, education, repository, or breach exposure events were recovered for this target.</div>
                </div>`;
        } else {
            let timelineHtml = `
                <div class="timeline-container">
                    <div class="timeline-header-bar">
                        <span class="timeline-header-title mono">IDENTITY &amp; SECURITY INCIDENT EVOLUTION</span>
                        <span class="badge-pill badge-neutral mono">${timelineList.length} CHRONOLOGICAL MILESTONES</span>
                    </div>
                    <div class="timeline-track">
            `;

            timelineList.forEach(item => {
                const t = (item.type || "").toLowerCase();
                const isBreach = t.includes("breach") || t.includes("incident") || t.includes("exposure");
                const isEdu = t.includes("education") || t.includes("academic") || t.includes("alma");
                const isWork = t.includes("work") || t.includes("job") || t.includes("experience");
                const isProject = t.includes("project") || t.includes("engineering") || t.includes("initiative");

                let pillClass = "timeline-pill-neutral";
                let dotColor = "#94a3b8";
                let borderAccent = "#334155";
                let iconGlyph = "";

                if (isBreach) {
                    pillClass = "timeline-pill-breach";
                    dotColor = "#f43f5e";
                    borderAccent = "#ef4444";
                    iconGlyph = "";
                } else if (isEdu) {
                    pillClass = "timeline-pill-edu";
                    dotColor = "#3b82f6";
                    borderAccent = "#3b82f6";
                    iconGlyph = "";
                } else if (isWork) {
                    pillClass = "timeline-pill-work";
                    dotColor = "#f59e0b";
                    borderAccent = "#f59e0b";
                    iconGlyph = "";
                } else if (isProject) {
                    pillClass = "timeline-pill-project";
                    dotColor = "#a855f7";
                    borderAccent = "#a855f7";
                    iconGlyph = "";
                }

                timelineHtml += `
                    <div class="timeline-node" style="--node-accent: ${borderAccent};">
                        <div class="timeline-node-marker">
                            <span class="timeline-dot" style="background: ${dotColor}; box-shadow: 0 0 10px ${dotColor}80;"></span>
                        </div>
                        <div class="timeline-card" style="border-left: 3px solid ${borderAccent};">
                            <div class="timeline-card-header">
                                <div class="timeline-period-badge mono">${escapeHtml(item.period || 'Historical')}</div>
                                <span class="timeline-type-pill ${pillClass}">[${escapeHtml(item.type || 'EVENT').toUpperCase()}]</span>
                            </div>
                            <div class="timeline-card-title">${escapeHtml(item.title || '')}</div>
                            <div class="timeline-card-desc">${escapeHtml(item.description || '')}</div>
                        </div>
                    </div>
                `;
            });

            timelineHtml += `
                    </div>
                </div>
            `;
            timelineContainer.innerHTML = timelineHtml;
        }
    }

    // 9. Full Telemetry Dictionary Ledger
    renderFullTelemetry(data);

    // 10. Precision OSINT Dorking & Deep Web Dossier
    renderDorksTab(data);

    // 11. WMN Multi-Platform Account Enumeration
    renderWMNTab(data);

    // 12. Threat Dump & Paste Reconnaissance
    renderPastesTab(data);

    // 13. AI Threat Intelligence Dossier
    renderAITab(data);

    // 14. Image Correlation & Cross-Platform Avatars
    if (typeof renderImageCorrelationTab === "function") {
        renderImageCorrelationTab(data);
    }

    // 15. Reverse Phone & Telecom Intelligence
    if (typeof renderTelecomTab === "function") {
        renderTelecomTab(data);
    }
}

function renderDorksTab(data) {
    const container = document.getElementById("tab-dorks-content");
    if (!container) return;
    const dorks = data.osint_dorks || [];
    if (!dorks || dorks.length === 0) {
        container.innerHTML = `
            <div class="evidence-card" style="border-left: 3px solid #6366f1;">
                <div class="evidence-title flex items-center gap-1.5" style="color: #a5b4fc;">${getUiIcon("globe", "w-4 h-4 text-indigo-400")} OSINT Query Pivot Links</div>
                <div class="evidence-body" style="margin-top: 0.3rem;">Enter a valid target email to generate precision web dorks and leak search operators.</div>
            </div>
        `;
        return;
    }

    const isOpenWeb = (cat) => {
        const c = (cat || "").toLowerCase();
        return c.includes("open web") || c.includes("visual") || c.includes("registry") || c.includes("career") || c.includes("company") || c.includes("linkedin");
    };

    const openWebDorks = dorks.filter(d => isOpenWeb(d.category));
    const darkWebDorks = dorks.filter(d => !isOpenWeb(d.category));

    const renderCard = (d, isWeb) => {
        const c = (d.category || "").toLowerCase();
        let borderCol = "#a855f7";
        let badgeBg = "rgba(168, 85, 247, 0.15)";
        let badgeCol = "#d8b4fe";
        let btnCol = "#c084fc";
        let btnBorder = "#a855f7";
        let btnBg = "rgba(168, 85, 247, 0.08)";
        let btnLabel = "Launch Query &nearr;";

        if (c.includes("career") || c.includes("linkedin")) {
            borderCol = "#38bdf8";
            badgeBg = "rgba(56, 189, 248, 0.15)";
            badgeCol = "#38bdf8";
            btnCol = "#38bdf8";
            btnBorder = "#0284c7";
            btnBg = "rgba(2, 132, 199, 0.12)";
            btnLabel = "Open LinkedIn Dossier &nearr;";
        } else if (c.includes("visual") || c.includes("image")) {
            borderCol = "#10b981";
            badgeBg = "rgba(16, 185, 129, 0.15)";
            badgeCol = "#34d399";
            btnCol = "#34d399";
            btnBorder = "#059669";
            btnBg = "rgba(16, 185, 129, 0.12)";
            btnLabel = "Search Face Recon &nearr;";
        } else if (c.includes("registry") || c.includes("1881")) {
            borderCol = "#06b6d4";
            badgeBg = "rgba(6, 182, 212, 0.15)";
            badgeCol = "#22d3ee";
            btnCol = "#22d3ee";
            btnBorder = "#0891b2";
            btnBg = "rgba(6, 182, 212, 0.12)";
            btnLabel = "Query 1881.no Registry &nearr;";
        } else if (c.includes("company") || c.includes("proff")) {
            borderCol = "#f59e0b";
            badgeBg = "rgba(245, 158, 11, 0.15)";
            badgeCol = "#fbbf24";
            btnCol = "#fbbf24";
            btnBorder = "#d97706";
            btnBg = "rgba(245, 158, 11, 0.12)";
            btnLabel = "Search Proff.no &nearr;";
        } else if (c.includes("code")) {
            borderCol = "#38bdf8";
            badgeCol = "#7dd3fc";
        }

        return `
            <div class="evidence-card" style="border-left: 3px solid ${borderCol}; margin: 0; padding: 12px 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                    <span class="evidence-title" style="font-size: 0.9rem; color: var(--t-primary); font-weight: 600;">${escapeHtml(d.title)}</span>
                    <span class="badge-pill mono" style="font-size: 0.68rem; background: ${badgeBg}; color: ${badgeCol}; border: 1px solid ${borderCol}40;">${escapeHtml(d.category)}</span>
                </div>
                <div class="evidence-body" style="font-size: 0.78rem; color: var(--t-secondary); margin-bottom: 8px;">
                    ${escapeHtml(d.description)}
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; background: var(--c-elevated); padding: 6px 10px; border-radius: 4px; border: 1px solid var(--b-hairline);">
                    <span class="mono" style="font-size: 0.7rem; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 460px;">
                        ${escapeHtml(d.url)}
                    </span>
                    <a href="${escapeHtml(d.url)}" target="_blank" rel="noopener noreferrer" class="btn-tool" style="color: ${btnCol}; border-color: ${btnBorder}; background: ${btnBg}; text-decoration: none; padding: 5px 12px; font-size: 0.72rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                        ${btnLabel}
                    </a>
                </div>
            </div>
        `;
    };

    let html = "";

    if (openWebDorks.length > 0) {
        html += `
            <div style="margin-bottom: 12px; padding: 10px 14px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span class="mono flex items-center gap-1.5" style="font-size: 0.82rem; font-weight: 700; color: #38bdf8;">${getUiIcon("globe", "w-3.5 h-3.5 text-sky-400")} OPEN WEB IDENTITY RECONNAISSANCE</span>
                    <span class="badge-pill badge-info mono" style="background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border-color: #38bdf8;">${openWebDorks.length} DIRECT RECON VECTORS</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                    Live open-web dossiers for <strong>${escapeHtml(currentEmail)}</strong>: Google LinkedIn queries, Google Images face recognition, Norwegian public person directories (1881.no), and corporate role filings. Click any launcher to execute live in your browser.
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr; gap: 10px; margin-bottom: 20px;">
                ${openWebDorks.map(d => renderCard(d, true)).join("")}
            </div>
        `;
    }

    if (darkWebDorks.length > 0) {
        html += `
            <div style="margin-bottom: 12px; padding: 10px 14px; background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 6px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span class="mono flex items-center gap-1.5" style="font-size: 0.82rem; font-weight: 700; color: #c084fc;">${getUiIcon("search", "w-3.5 h-3.5 text-purple-400")} EXFILTRATED DATA ARCHIVES</span>
                    <span class="badge-pill badge-neutral mono" style="background: rgba(168, 85, 247, 0.2); color: #d8b4fe; border-color: #a855f7;">${darkWebDorks.length} LEAK &amp; CODE VECTORS</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                    Pre-compiled targeted search dorks scanning paste services, spreadsheet caches (.xlsx, .env), darknet dumps, and code repositories.
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr; gap: 10px;">
                ${darkWebDorks.map(d => renderCard(d, false)).join("")}
            </div>
        `;
    }

    container.innerHTML = html;
}

/**
 * WhatBreach Interactive Online Hash Cracker & Rainbow Table Resolver
 */
async function resolveCredentialHash(hashVal, btnEl) {
    if (!hashVal) return;
    const cardEl = btnEl.closest(".evidence-card");
    let resultSlot = cardEl ? cardEl.querySelector(".hash-result-slot") : null;
    if (!resultSlot) {
        resultSlot = document.createElement("div");
        resultSlot.className = "hash-result-slot";
        btnEl.parentNode.appendChild(resultSlot);
    }
    resultSlot.style.display = "block";
    resultSlot.innerHTML = `<span style="color: #c084fc; font-size: 0.72rem;">Querying public rainbow tables &amp; dictionary matrices...</span>`;
    btnEl.disabled = true;

    try {
        const resp = await fetch(`/api/hash/resolve?hash=${encodeURIComponent(hashVal)}`);
        const data = await resp.json();
        if (data.resolved && data.plaintext) {
            resultSlot.innerHTML = `
                <div style="margin-top: 6px; padding: 6px 10px; background: rgba(34, 197, 94, 0.12); border-left: 3px solid #22c55e; border-radius: 4px;">
                    <span style="color: #4ade80; font-weight: 700; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 4px;">${getUiIcon("unlock", "w-3 h-3 text-emerald-400")} PLAINTEXT RECOVERED IN ${data.crack_time_seconds || 0.01}s:</span>
                    <code style="color: var(--t-primary); font-weight: 700; background: var(--c-surface); border: 1px solid var(--b-hairline); padding: 2px 6px; border-radius: 3px; margin-left: 4px; font-size: 0.8rem;">${escapeHtml(data.plaintext)}</code>
                    <div style="font-size: 0.7rem; color: var(--accent-emerald); margin-top: 2px;">Source: ${escapeHtml(data.source || 'Rainbow Table')} (${escapeHtml(data.algorithm || 'Hash')})</div>
                </div>
            `;
            showToast("Hash successfully resolved to plaintext password!", "success");
        } else {
            const meta = data.meta || {};
            const isHardened = meta.algorithm === "bcrypt" || meta.algorithm === "Argon2";
            const borderCol = isHardened ? "#3b82f6" : "#f59e0b";
            const titleText = isHardened ? "Cryptographically Hardened" : "Offline Hashcat Required";
            resultSlot.innerHTML = `
                <div style="margin-top: 6px; padding: 6px 10px; background: var(--c-elevated); border-left: 3px solid ${borderCol}; border-radius: 4px;">
                    <span style="color: var(--t-primary); font-weight: 600; font-size: 0.75rem;">${titleText}:</span>
                    <span style="color: var(--t-secondary); font-size: 0.73rem;">${escapeHtml(data.reason || 'Not in free public tables.')}</span>
                    <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 3px;">
                        ${meta.recommendation ? escapeHtml(meta.recommendation) : ''}
                        ${meta.est_gpu_rate ? ` | GPU Rate: <span class="mono">${escapeHtml(meta.est_gpu_rate)}</span>` : ''}
                    </div>
                </div>
            `;
            showToast("Cryptographic analysis complete. See details below.", "info");
        }
    } catch (err) {
        resultSlot.innerHTML = `<span style="color: #ef4444; font-size: 0.72rem;">Lookup error: ${escapeHtml(err.message)}</span>`;
    } finally {
        btnEl.disabled = false;
    }
}


/* ==========================================================================
   WhatsMyName (WMN) Multi-Platform Handle Enumeration
   ========================================================================== */
let currentWMNResults = null;

function renderWMNTab(data) {
    const container = document.getElementById("tab-wmn-content");
    if (!container) return;

    let defaultHandle = "";
    if (data && data.employee) {
        const rawEmail = data.employee.corporate_email || "";
        defaultHandle = rawEmail.split("@")[0] || "";
    }

    container.innerHTML = `
        <div class="evidence-card" style="border-left: 3px solid #38bdf8; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div class="evidence-title flex items-center gap-1.5" style="color: #38bdf8;">
                    ${getUiIcon("user", "w-4 h-4 text-sky-400")} WhatsMyName (WMN) Account Enumeration Engine
                </div>
                <span class="mono text-xs px-2 py-0.5 rounded" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);">
                    700+ Global Platforms
                </span>
            </div>
            <div style="font-size: 0.78rem; color: var(--t-secondary); margin-bottom: 12px; line-height: 1.4;">
                Executes high-throughput concurrent handle probes across public networks, code repositories, gaming networks, and darkweb-adjacent platforms using exact signature heuristics.
            </div>

            <div style="display: grid; grid-template-columns: 2fr 1.2fr 1fr auto; gap: 8px; align-items: end; background: var(--c-surface); padding: 10px; border-radius: 6px; border: 1px solid var(--b-hairline);">
                <div>
                    <label class="mono text-xs block mb-1" style="color: var(--t-secondary);">TARGET HANDLE / ALIAS:</label>
                    <input type="text" id="wmn-input-handle" class="modal-input mono w-full text-xs" style="padding: 6px 10px; border-radius: 4px; background: var(--c-elevated); color: var(--t-primary); border: 1px solid var(--b-hairline);" value="${escapeHtml(defaultHandle)}" placeholder="e.g. jordin, alex_dev">
                </div>
                <div>
                    <label class="mono text-xs block mb-1" style="color: var(--t-secondary);">CATEGORY FILTER:</label>
                    <select id="wmn-select-cat" class="modal-input mono w-full text-xs" style="padding: 6px 10px; border-radius: 4px; background: var(--c-elevated); color: var(--t-primary); border: 1px solid var(--b-hairline);">
                        <option value="">All Categories (Standard)</option>
                        <option value="social">Social Networks</option>
                        <option value="tech">Tech &amp; Developers</option>
                        <option value="coding">Coding &amp; Git</option>
                        <option value="gaming">Gaming &amp; Esports</option>
                        <option value="music">Music &amp; Streaming</option>
                        <option value="blog">Blogs &amp; Content</option>
                    </select>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; height: 32px;">
                    <label class="mono text-xs flex items-center gap-1.5 cursor-pointer" style="color: var(--t-secondary);">
                        <input type="checkbox" id="wmn-check-prio" checked style="accent-color: #0284c7;">
                        <span>Priority Only</span>
                    </label>
                </div>
                <div>
                    <button type="button" id="btn-run-wmn" class="btn-primary mono text-xs py-2 px-3 flex items-center gap-1.5" onclick="triggerWMNScan()">
                        ${getUiIcon("search", "w-3 h-3")} Probe Platforms &rarr;
                    </button>
                </div>
            </div>
        </div>

        <div id="wmn-results-wrapper">
            ${currentWMNResults ? renderWMNResultsHTML(currentWMNResults) : `
                <div style="text-align: center; padding: 24px; border: 1px dashed var(--b-hairline); border-radius: 6px; color: var(--t-muted); font-size: 0.8rem;" class="mono">
                    Enter a target handle above and click [Probe Platforms] to start enumeration.
                </div>
            `}
        </div>
    `;
}

async function triggerWMNScan() {
    const handleInput = document.getElementById("wmn-input-handle");
    const catSelect = document.getElementById("wmn-select-cat");
    const prioCheck = document.getElementById("wmn-check-prio");
    const btn = document.getElementById("btn-run-wmn");
    const wrapper = document.getElementById("wmn-results-wrapper");

    const rawHandle = handleInput ? handleInput.value.trim() : "";
    const handle = rawHandle.replace(/^@+/, "");
    if (!handle) {
        showToast("Please enter a target handle to probe.", "warning");
        return;
    }

    const cat = catSelect ? catSelect.value : "";
    const prio = prioCheck ? prioCheck.checked : false;

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="animate-spin inline-block mr-1">[*]</span> Scanning...`;
    }
    if (wrapper) {
        wrapper.innerHTML = `
            <div style="padding: 24px; text-align: center; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #38bdf8; margin-bottom: 6px;">
                    [+] DISPATCHING CONCURRENT PROBES ACROSS PLATFORM MATRIX...
                </div>
                <div style="font-size: 0.72rem; color: var(--t-secondary);">
                    Evaluating response bodies and status signatures for handle "@${escapeHtml(handle)}"...
                </div>
            </div>
        `;
    }

    try {
        const url = `/api/recon/wmn?handle=${encodeURIComponent(handle)}&priority_only=${prio}&max_sites=60${cat ? `&category=${encodeURIComponent(cat)}` : ''}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        currentWMNResults = data;
        if (wrapper) {
            wrapper.innerHTML = renderWMNResultsHTML(data);
        }
        showToast(`WMN scan complete: ${data.matches_count} accounts confirmed across ${data.total_scanned} sites!`, "success");
    } catch (err) {
        if (wrapper) {
            wrapper.innerHTML = `<div style="color: #ef4444; padding: 12px; font-size: 0.8rem;" class="mono">[!] Error executing WMN probe: ${escapeHtml(err.message)}</div>`;
        }
        showToast(`WMN probe error: ${err.message}`, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `${getUiIcon("search", "w-3 h-3")} Probe Platforms &rarr;`;
        }
    }
}

function renderWMNResultsHTML(data) {
    const matches = data.matches || [];
    return `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding: 8px 12px; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px;">
            <div class="mono text-xs" style="color: var(--t-secondary);">
                TARGET: <strong style="color: var(--t-primary);">@${escapeHtml(data.handle)}</strong> | SCANNED: <strong style="color: var(--t-primary);">${data.total_scanned}</strong> SITES
            </div>
            <div class="mono text-xs">
                CONFIRMED MATCHES: <span class="badge-pill" style="background: rgba(16, 185, 129, 0.15); color: #34d399; font-weight: 700;">${data.matches_count} PROFILES</span>
            </div>
        </div>

        ${matches.length === 0 ? `
            <div style="padding: 20px; text-align: center; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px; font-size: 0.78rem; color: var(--t-secondary);" class="mono">
                No active profiles confirmed with handle "@${escapeHtml(data.handle)}" under selected filters.
            </div>
        ` : `
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;">
                ${matches.map(m => `
                    <div class="evidence-card" style="border-left: 3px solid #10b981; margin: 0; padding: 10px 14px; background: var(--c-surface);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                            <span class="mono text-xs font-bold" style="color: var(--t-primary);">${escapeHtml(m.platform)}</span>
                            <span class="badge-pill" style="background: rgba(16, 185, 129, 0.15); color: #34d399; font-size: 0.65rem;">
                                ${Math.round((m.confidence_score || 0.9) * 100)}% CONF
                            </span>
                        </div>
                        <div class="mono text-xs" style="color: var(--t-secondary); margin-bottom: 8px; font-size: 0.72rem;">
                            Category: ${escapeHtml(m.category || 'social')} | Latency: ${m.response_time_sec}s
                        </div>
                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                            <a href="${escapeHtml(m.url)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock text-xs mono" style="text-decoration: none; padding: 3px 8px; display: inline-flex; align-items: center; gap: 4px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.4);">
                                Inspect Profile &nearr;
                            </a>
                            <button type="button" class="btn-secondary text-xs mono py-1 px-2" style="font-size: 0.68rem;" onclick="addWMNProfileToGraph('${escapeHtml(m.platform)}', '${escapeHtml(m.url)}', '${escapeHtml(data.handle)}')">
                                + Graph Link
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `}
    `;
}

function addWMNProfileToGraph(platform, url, handle) {
    if (!currentNodesDataSet || !currentEdgesDataSet) {
        showToast("Graph canvas is not active.", "warning");
        return;
    }
    const nodeId = `wmn_${platform.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${handle}`;
    if (currentNodesDataSet.get(nodeId)) {
        showToast(`Node for ${platform} is already in the graph.`, "info");
        return;
    }

    const newNode = {
        id: nodeId,
        label: `[${platform.toUpperCase()}]\n@${handle}`,
        title: `Confirmed Profile: ${platform}\nURL: ${url}`,
        group: "pivot_account",
        data: {
            type: "PUBLIC_ACCOUNT",
            can_pivot: true,
            pivot_type: "URL",
            pivot_value: url,
            platform: platform,
            handle: handle
        }
    };

    currentNodesDataSet.add(newNode);
    rawGraphNodes.push(newNode);

    if (currentInvestigationData && currentInvestigationData.employee) {
        const empNodeId = `emp_${currentInvestigationData.employee.id}`;
        currentEdgesDataSet.add({
            from: empNodeId,
            to: nodeId,
            label: "CONFIRMED HANDLE",
            arrows: "to",
            category: "accounts"
        });
    }

    if (networkInstance) {
        networkInstance.fit({ nodes: [nodeId], animation: true });
    }
    showToast(`Added ${platform} profile to attack graph!`, "success");
}
window.addWMNProfileToGraph = addWMNProfileToGraph;
window.triggerWMNScan = triggerWMNScan;
window.renderWMNTab = renderWMNTab;


/* ==========================================================================
   Live Threat Dump & Paste Aggregator Engine
   ========================================================================== */
let currentPastesResults = null;

function renderPastesTab(data) {
    const container = document.getElementById("tab-pastes-content");
    if (!container) return;

    let defaultTarget = "";
    if (data && data.employee) {
        defaultTarget = data.employee.corporate_email || "";
    }

    container.innerHTML = `
        <div class="evidence-card" style="border-left: 3px solid #f43f5e; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div class="evidence-title flex items-center gap-1.5" style="color: #f43f5e;">
                    ${getUiIcon("alert", "w-4 h-4 text-rose-400")} Live Threat Dump &amp; Paste Reconnaissance
                </div>
                <span class="mono text-xs px-2 py-0.5 rounded" style="background: rgba(244, 63, 94, 0.15); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.3);">
                    Pastebin / JustPaste / Rentry / Gist
                </span>
            </div>
            <div style="font-size: 0.78rem; color: var(--t-secondary); margin-bottom: 12px; line-height: 1.4;">
                Monitors public paste dumps, combo-lists, stealer logs, and mirrored threat lakes for active credential exposure.
            </div>

            <div style="display: grid; grid-template-columns: 3fr 1fr auto; gap: 8px; align-items: end; background: var(--c-surface); padding: 10px; border-radius: 6px; border: 1px solid var(--b-hairline);">
                <div>
                    <label class="mono text-xs block mb-1" style="color: var(--t-secondary);">TARGET QUERY (EMAIL / DOMAIN / ALIAS / HASH):</label>
                    <input type="text" id="pastes-input-target" class="modal-input mono w-full text-xs" style="padding: 6px 10px; border-radius: 4px; background: var(--c-elevated); color: var(--t-primary); border: 1px solid var(--b-hairline);" value="${escapeHtml(defaultTarget)}" placeholder="e.g. target@example.com or domain.com">
                </div>
                <div>
                    <label class="mono text-xs block mb-1" style="color: var(--t-secondary);">MAX RESULTS:</label>
                    <select id="pastes-select-limit" class="modal-input mono w-full text-xs" style="padding: 6px 10px; border-radius: 4px; background: var(--c-elevated); color: var(--t-primary); border: 1px solid var(--b-hairline);">
                        <option value="10">10 Findings</option>
                        <option value="20" selected>20 Findings</option>
                        <option value="40">40 Findings</option>
                    </select>
                </div>
                <div>
                    <button type="button" id="btn-run-pastes" class="btn-primary mono text-xs py-2 px-3 flex items-center gap-1.5" onclick="triggerPastesScan()">
                        ${getUiIcon("search", "w-3 h-3")} Scan Pastes &rarr;
                    </button>
                </div>
            </div>
        </div>

        <div id="pastes-results-wrapper">
            ${currentPastesResults ? renderPastesResultsHTML(currentPastesResults) : `
                <div style="text-align: center; padding: 24px; border: 1px dashed var(--b-hairline); border-radius: 6px; color: var(--t-muted); font-size: 0.8rem;" class="mono">
                    Enter an identity identifier above and click [Scan Pastes] to inspect threat dumps.
                </div>
            `}
        </div>
    `;
}

async function triggerPastesScan() {
    const targetInput = document.getElementById("pastes-input-target");
    const limitSelect = document.getElementById("pastes-select-limit");
    const btn = document.getElementById("btn-run-pastes");
    const wrapper = document.getElementById("pastes-results-wrapper");

    const target = targetInput ? targetInput.value.trim() : "";
    if (!target) {
        showToast("Please enter a target email, domain, or handle.", "warning");
        return;
    }
    const limit = limitSelect ? limitSelect.value : 20;

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="animate-spin inline-block mr-1">[*]</span> Scanning...`;
    }
    if (wrapper) {
        wrapper.innerHTML = `
            <div style="padding: 24px; text-align: center; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #f43f5e; margin-bottom: 6px;">
                    [+] SCANNING REPOSITORIES, COMBO-LISTS, AND THREAT LAKES...
                </div>
                <div style="font-size: 0.72rem; color: var(--t-secondary);">
                    Executing targeted dorks against paste engines for "${escapeHtml(target)}"...
                </div>
            </div>
        `;
    }

    try {
        const resp = await fetch(`/api/recon/pastes?target=${encodeURIComponent(target)}&max_results=${limit}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        currentPastesResults = data;
        if (wrapper) {
            wrapper.innerHTML = renderPastesResultsHTML(data);
        }
        showToast(`Paste reconnaissance complete: ${data.total_found} leaks discovered (Threat Score: ${data.threat_score}/100)!`, "info");
    } catch (err) {
        if (wrapper) {
            wrapper.innerHTML = `<div style="color: #ef4444; padding: 12px; font-size: 0.8rem;" class="mono">[!] Error executing paste search: ${escapeHtml(err.message)}</div>`;
        }
        showToast(`Paste scan error: ${err.message}`, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `${getUiIcon("search", "w-3 h-3")} Scan Pastes &rarr;`;
        }
    }
}

function renderPastesResultsHTML(data) {
    const pastes = data.pastes || [];
    const isCrit = data.threat_level === "CRITICAL";
    const isHigh = data.threat_level === "HIGH";
    const badgeColor = isCrit ? "#ef4444" : (isHigh ? "#f59e0b" : "#10b981");
    const badgeBg = isCrit ? "rgba(239, 68, 68, 0.15)" : (isHigh ? "rgba(245, 158, 11, 0.15)" : "rgba(16, 185, 129, 0.15)");

    return `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding: 10px 14px; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px;">
            <div class="mono text-xs" style="color: var(--t-secondary);">
                TARGET: <strong style="color: var(--t-primary);">${escapeHtml(data.target)}</strong> | TOTAL INDEXED: <strong style="color: var(--t-primary);">${data.total_found}</strong>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="mono text-xs font-bold" style="color: var(--t-primary);">THREAT SCORE: ${data.threat_score}/100</span>
                <span class="badge-pill mono" style="background: ${badgeBg}; color: ${badgeColor}; font-weight: 700;">
                    ${data.threat_level}
                </span>
            </div>
        </div>

        ${pastes.length === 0 ? `
            <div style="padding: 20px; text-align: center; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px; font-size: 0.78rem; color: var(--t-secondary);" class="mono">
                No exposed paste dumps found for "${escapeHtml(data.target)}".
            </div>
        ` : `
            <div style="display: flex; flex-direction: column; gap: 10px;">
                ${pastes.map(p => {
                    const isDumpCrit = p.severity === "CRITICAL";
                    const sevBorder = isDumpCrit ? "#ef4444" : (p.severity === "HIGH" ? "#f59e0b" : "#38bdf8");
                    const sevColor = isDumpCrit ? "#f87171" : (p.severity === "HIGH" ? "#fbbf24" : "#7dd3fc");
                    return `
                        <div class="evidence-card" style="border-left: 3px solid ${sevBorder}; margin: 0; padding: 10px 14px; background: var(--c-surface);">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span class="mono text-xs font-bold" style="color: var(--t-primary);">${escapeHtml(p.service)}</span>
                                    <span class="badge-pill" style="font-size: 0.65rem; background: rgba(0,0,0,0.2); color: ${sevColor}; border: 1px solid ${sevBorder};">
                                        ${escapeHtml(p.severity)} LEAK
                                    </span>
                                </div>
                                <span class="mono text-xs" style="color: var(--t-muted); font-size: 0.7rem;">${escapeHtml(p.timestamp || 'Recent')}</span>
                            </div>
                            <div style="font-size: 0.76rem; font-weight: 600; color: var(--t-primary); margin-bottom: 4px;">
                                ${escapeHtml(p.title)}
                            </div>
                            <div style="background: var(--c-canvas); border: 1px solid var(--b-hairline); border-radius: 4px; padding: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--t-secondary); margin-bottom: 8px; white-space: pre-wrap; word-break: break-all;">
                                ${escapeHtml(p.snippet)}
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <a href="${escapeHtml(p.url)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock text-xs mono" style="text-decoration: none; padding: 3px 8px; display: inline-flex; align-items: center; gap: 4px; color: #f43f5e; border-color: rgba(244, 63, 94, 0.4);">
                                    View Leak Source &nearr;
                                </a>
                                <span class="mono text-xs" style="color: var(--t-muted); font-size: 0.68rem;">${escapeHtml(p.source_type || 'Public Paste')}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `}
    `;
}
window.renderPastesTab = renderPastesTab;
window.triggerPastesScan = triggerPastesScan;


/**
 * Universal Clipboard Copy Helper
 */
function copyToClipboard(text, label = "Data") {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(`Copied ${label} to clipboard`, "success");
        }).catch(() => {
            fallbackCopy(text, label);
        });
    } else {
        fallbackCopy(text, label);
    }
}
function fallbackCopy(text, label) {
    const el = document.createElement("textarea");
    el.value = text;
    document.body.appendChild(el);
    el.select();
    try {
        document.execCommand("copy");
        showToast(`Copied ${label} to clipboard`, "success");
    } catch (err) {
        showToast("Could not copy to clipboard", "warning");
    }
    document.body.removeChild(el);
}
window.copyToClipboard = copyToClipboard;

/**
 * Full Telemetry Dictionary Ledger
 * Tabular key-value view of all exfiltrated and discovered attributes
 */
function renderFullTelemetry(data) {
    const container = document.getElementById("tab-telemetry-content");
    if (!container || !data) return;

    const rows = [];
    const emp = data.employee || {};
    const email = currentEmail;

    // 1. Target Identity
    rows.push({
        category: "IDENTITY",
        catBadge: "badge-clean",
        key: "TARGET.EMAIL",
        label: "Target Primary Identifier",
        val: email,
        source: "Investigator Target Input",
        sensitive: false
    });

    if (emp.full_name) {
        rows.push({
            category: "IDENTITY",
            catBadge: "badge-clean",
            key: "IDENTITY.NAME",
            label: "Discovered Full Name",
            val: emp.full_name,
            source: "Git Archaeology / Public Profiles",
            sensitive: !isDeclassified
        });
    }

    // 2. Compromised Credentials & Hashes
    (data.credentials || []).forEach((c, idx) => {
        if (c.password_hash) {
            rows.push({
                category: "CREDENTIAL",
                catBadge: "badge-critical",
                key: `BREACH.HASH[${idx+1}]`,
                label: `Exfiltrated Cryptographic Hash (${c.domain_compromised || c.leak_name})`,
                val: c.password_hash,
                isHash: true,
                source: `${c.leak_name} Database Dump`,
                sensitive: false
            });
        }
        if (c.plaintext_password) {
            rows.push({
                category: "CREDENTIAL",
                catBadge: "badge-critical",
                key: `PLAINTEXT.PASSWORD[${idx+1}]`,
                label: `Exfiltrated Plaintext Secret (${c.domain_compromised || c.leak_name})`,
                val: c.plaintext_password,
                source: `${c.leak_name} Stealer Memory Dump`,
                sensitive: !isDeclassified
            });
        }
        if (c.password_pattern) {
            rows.push({
                category: "CREDENTIAL",
                catBadge: "badge-high",
                key: `PASSWORD.PATTERN[${idx+1}]`,
                label: "Exfiltrated Password Pattern Mask",
                val: c.password_pattern,
                source: "Forensic Hashcat Mask Analyzer",
                sensitive: false
            });
        }
    });

    // 3. Breaches & Malwares
    (data.leaks || []).forEach((leak, idx) => {
        rows.push({
            category: "BREACH",
            catBadge: leak.leak_type === "INFOSTEALER" ? "badge-critical" : "badge-high",
            key: `INCIDENT[${idx+1}].${leak.leak_type}`,
            label: `${leak.leak_name} (${leak.breach_date || 'Undated'})`,
            val: `${leak.description || 'Verified Incident'} [Threat: ${leak.threat_actor_source || 'Unknown'}]`,
            source: "XposedOrNot / Darknet Feed",
            sensitive: false
        });
    });

    // 4. Telecom & Phone Numbers
    const phonePivots = (data.pivots || []).filter(p => p.pivot_type === "PHONE_NUMBER" || p.pivot_type.includes("PHONE"));
    phonePivots.forEach((p, idx) => {
        rows.push({
            category: "TELECOM",
            catBadge: "badge-high",
            key: `TELECOM.E164[${idx+1}]`,
            label: "Validated International Telephone Line",
            val: p.pivot_value,
            source: p.context_note || "phonenumbers E.164 Engine",
            sensitive: !isDeclassified
        });
    });

    // 5. Git & Developer Archaeology
    const gitPivots = (data.pivots || []).filter(p => 
        (p.pivot_type || "").includes("GIT") || 
        (p.pivot_value || "").toLowerCase().includes("github") ||
        (p.context_note || "").toLowerCase().includes("repository")
    );
    gitPivots.forEach((gp, idx) => {
        rows.push({
            category: "GIT_DEV",
            catBadge: "badge-low",
            key: `GIT.ARTIFACT[${idx+1}]`,
            label: "Open Source Code / Portfolio Link",
            val: `${gp.pivot_value} — ${gp.context_note || ''}`,
            source: "GitHub Commit Archaeology",
            sensitive: false
        });
    });

    // 6. Public Accounts & Online Profiles (Holehe, Duolingo, etc.)
    const accountPivots = (data.pivots || []).filter(p => 
        !gitPivots.includes(p) && 
        !phonePivots.includes(p) && 
        !p.source_leak_id
    );
    accountPivots.forEach((ap, idx) => {
        const isSuspected = ap.pivot_type === "SUSPECTED_ACCOUNT" || (ap.context_note || "").includes("[STATUS: SUSPECTED]");
        rows.push({
            category: isSuspected ? "SUSPECTED_ACCOUNT" : "ACCOUNT",
            catBadge: isSuspected ? "badge-medium" : "badge-low",
            key: isSuspected ? `SUSPECTED.PROFILE[${idx+1}]` : `ACCOUNT.PROFILE[${idx+1}]`,
            label: isSuspected ? "Suspected Candidate Handle (Quarantined)" : "Active Web & Cloud Registration",
            val: `${ap.pivot_value} — ${ap.context_note || ''}`,
            source: isSuspected ? "Uncorroborated Platform Hit" : "Holehe OSINT Probe / Platform REST",
            sensitive: false
        });
    });

    // 7. Residential & Geospatial
    (data.physical_footprints || []).forEach((foot, idx) => {
        rows.push({
            category: "GEOSPATIAL",
            catBadge: "badge-high",
            key: `GEO.RESIDENTIAL[${idx+1}]`,
            label: "Physical Living / Portfolio Coordinates",
            val: `${foot.address_line}, ${foot.city || ''} (${foot.country || ''}) [Type: ${foot.exposure_type || 'Record'}]`,
            source: "Courier / Profile OSINT",
            sensitive: !isDeclassified
        });
    });

    // 8. Household Cohabitants
    (data.relatives || []).forEach((rel, idx) => {
        rows.push({
            category: "HOUSEHOLD",
            catBadge: "badge-critical",
            key: `HOUSEHOLD.COHABITANT[${idx+1}]`,
            label: `Family / Cohabitant (${rel.relationship || 'Household'})`,
            val: `${rel.full_name} [Risk: ${rel.social_engineering_risk || 'Extortion Target'}]`,
            source: "Shared Residence Correlation",
            sensitive: !isDeclassified
        });
    });

    // 9. Spillover Index & Metrics
    const sp = data.spillover_score || {};
    rows.push({
        category: "RISK_INDEX",
        catBadge: "badge-clean",
        key: "SPILLOVER.COMPOSITE_SCORE",
        label: "Deterministic 5-Vector Weighted Score",
        val: `${sp.score || 0} / 100 [Level: ${sp.level || 'CLEAN'}]`,
        source: "Deterministic Risk Calculus Engine",
        sensitive: false
    });

    window._cachedTelemetryRows = rows;

    let html = `
        <div class="telemetry-filter-shell">
            <div style="display: flex; align-items: center; gap: 0.5rem; flex: 1;">
                <span class="mono" style="font-size: 0.72rem; color: var(--t-muted);">SEARCH_DICTIONARY:</span>
                <input 
                    type="text" 
                    id="telemetry-search-box" 
                    class="telemetry-search-input mono" 
                    placeholder="Filter telemetry keys, values, or sources (e.g. bcrypt, spotify, github, phone)..." 
                    oninput="filterTelemetryTable(this.value)"
                >
            </div>
            <span class="badge-pill badge-neutral mono" id="telemetry-counter-badge">${rows.length} ATTRIBUTES INDEXED</span>
        </div>

        <div class="telemetry-table-wrapper">
            <table class="telemetry-table">
                <thead>
                    <tr>
                        <th style="width: 110px;">VECTOR</th>
                        <th style="width: 180px;">TELEMETRY KEY</th>
                        <th>DISCOVERED FORENSIC VALUE</th>
                        <th style="width: 220px;">PROVENANCE SOURCE</th>
                    </tr>
                </thead>
                <tbody id="telemetry-table-body">
    `;

    rows.forEach(r => {
        const displayVal = r.val;
        const valClass = r.isHash ? "telemetry-val-hash" : "";
        const copyBtn = `<button type="button" class="btn-copy-mini" onclick="copyToClipboard('${escapeHtml(r.val)}', '${escapeHtml(r.key)}')">Copy</button>`;

        html += `
            <tr class="telemetry-row">
                <td><span class="badge-pill ${r.catBadge}">${escapeHtml(r.category)}</span></td>
                <td><span class="telemetry-key-name">${escapeHtml(r.key)}</span></td>
                <td class="telemetry-val-cell">
                    <span class="${valClass}">${escapeHtml(displayVal)}</span>
                    ${copyBtn}
                </td>
                <td style="font-size: 0.68rem; color: var(--t-muted);">${escapeHtml(r.source)}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

function filterTelemetryTable(query) {
    const q = (query || "").toLowerCase().trim();
    const rows = window._cachedTelemetryRows || [];
    const tbody = document.getElementById("telemetry-table-body");
    const badge = document.getElementById("telemetry-counter-badge");
    if (!tbody) return;

    const filtered = rows.filter(r => 
        !q || 
        r.category.toLowerCase().includes(q) || 
        r.key.toLowerCase().includes(q) || 
        r.val.toLowerCase().includes(q) || 
        r.source.toLowerCase().includes(q)
    );

    if (badge) badge.innerText = `${filtered.length} / ${rows.length} ATTRIBUTES`;

    tbody.innerHTML = filtered.map(r => {
        const displayVal = r.val;
        const valClass = r.isHash ? "telemetry-val-hash" : "";
        const copyBtn = `<button type="button" class="btn-copy-mini" onclick="copyToClipboard('${escapeHtml(r.val)}', '${escapeHtml(r.key)}')">Copy</button>`;

        return `
            <tr class="telemetry-row">
                <td><span class="badge-pill ${r.catBadge}">${escapeHtml(r.category)}</span></td>
                <td><span class="telemetry-key-name">${escapeHtml(r.key)}</span></td>
                <td class="telemetry-val-cell">
                    <span class="${valClass}">${escapeHtml(displayVal)}</span>
                    ${copyBtn}
                </td>
                <td style="font-size: 0.68rem; color: var(--t-muted);">${escapeHtml(r.source)}</td>
            </tr>
        `;
    }).join("");
}
window.filterTelemetryTable = filterTelemetryTable;

// Global Graph State
let currentNodesDataSet = null;
let currentEdgesDataSet = null;
let rawGraphNodes = [];
let rawGraphEdges = [];
let currentCategoryFilter = "all";

function getProcessedNodes(nodeList) {
    return nodeList.map(n => {
        const nodeCopy = { ...n };
        if (!isDeclassified) {
            const grp = nodeCopy.group;
            if (grp === "credential" || grp === "credentials") {
                const h = (nodeCopy.data && nodeCopy.data.password_hash) || "";
                if (h) {
                    nodeCopy.label = `[COMPROMISED HASH]\n${h}\n[Exfiltrated Dump]`;
                } else {
                    nodeCopy.label = "[LOCKED CREDENTIAL]\n••••••••••••\n[Click to Unlock]";
                }
            } else if (grp === "pivot" || grp === "pivots") {
                const pType = (nodeCopy.data && nodeCopy.data.pivot_type) || "";
                if (pType.includes("PHONE")) {
                    nodeCopy.label = "[LOCKED TELECOM]\n+1 (•••) •••-••••\n[Click to Unlock]";
                } else if (pType.includes("EMAIL")) {
                    nodeCopy.label = "[LOCKED EMAIL]\n•••••••@••••••.•••\n[Click to Unlock]";
                }
            } else if (grp === "physical") {
                nodeCopy.label = "[LOCKED ADDRESS]\n••••••••••••••••\n[Click to Unlock]";
            } else if (grp === "relative" || grp === "relatives") {
                nodeCopy.label = "[LOCKED CONTACT]\n••••••••••••\n[Click to Unlock]";
            }
        }
        return nodeCopy;
    });
}

/**
 * Filter Graph View by Provenance Category
 */
function filterGraphCategory(category) {
    currentCategoryFilter = category;

    document.querySelectorAll(".btn-cat-filter").forEach(btn => {
        if (btn.getAttribute("data-cat") === category) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    if (!networkInstance || !rawGraphNodes.length || !currentNodesDataSet || !currentEdgesDataSet) return;

    if (category === "all") {
        currentNodesDataSet.clear();
        currentEdgesDataSet.clear();
        currentNodesDataSet.add(getProcessedNodes(rawGraphNodes));
        currentEdgesDataSet.add(rawGraphEdges);
    } else {
        const filteredNodes = rawGraphNodes.filter(n => 
            n.category === "identity" || 
            n.id === `hub_${category}` ||
            n.category === category || 
            (n.data && n.data.category === category)
        );
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredEdges = rawGraphEdges.filter(e => 
            nodeIds.has(e.from) && nodeIds.has(e.to)
        );

        currentNodesDataSet.clear();
        currentEdgesDataSet.clear();
        currentNodesDataSet.add(getProcessedNodes(filteredNodes));
        currentEdgesDataSet.add(filteredEdges);
    }

    setTimeout(() => {
        if (networkInstance) {
            networkInstance.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
        }
    }, 60);
}
window.filterGraphCategory = filterGraphCategory;

/**
 * De-clutter & Organize Graph into Concentric Orbits
 */
function tidyGraphConcentric() {
    if (!networkInstance || !currentNodesDataSet || !rawGraphNodes.length) {
        if (typeof showToast === "function") showToast("No active network graph to organize.", "warning");
        return;
    }
    if (window.sfx) window.sfx.playSelect();

    // 1. Identify Central Identity Node
    const centerNode = rawGraphNodes.find(n => n.category === "identity" || n.group === "employee" || n.id.startsWith("emp_")) || rawGraphNodes[0];
    const centerId = centerNode ? centerNode.id : null;

    // 2. Identify Hub Nodes
    const hubNodes = rawGraphNodes.filter(n => n.id.startsWith("hub_") || (n.data && n.data.type === "PROVENANCE_HUB"));
    const hubIds = new Set(hubNodes.map(h => h.id));

    // Map children connected to each hub or center
    const hubChildren = {};
    hubNodes.forEach(h => { hubChildren[h.id] = []; });
    const directChildren = [];

    // Map edges
    rawGraphEdges.forEach(e => {
        if (e.from === centerId && hubIds.has(e.to)) {
            // center to hub
        } else if (hubIds.has(e.from)) {
            if (!hubChildren[e.from]) hubChildren[e.from] = [];
            hubChildren[e.from].push(e.to);
        } else if (e.from === centerId) {
            directChildren.push(e.to);
        }
    });

    const updates = [];

    // Place Center Node at (0, 0)
    if (centerId) {
        updates.push({ id: centerId, x: 0, y: 0, fixed: true });
    }

    // Place Hubs in Ring 1 (Radius 340)
    const numHubs = hubNodes.length || 1;
    const rHub = 340;
    const rChild = 660;
    const rLeaf = 960;

    hubNodes.forEach((hub, idx) => {
        const angle = (2 * Math.PI * idx) / numHubs - Math.PI / 2;
        const hx = Math.round(rHub * Math.cos(angle));
        const hy = Math.round(rHub * Math.sin(angle));
        updates.push({ id: hub.id, x: hx, y: hy, fixed: true });

        // Place children in fan sector
        const children = hubChildren[hub.id] || [];
        const numChildren = children.length;
        if (numChildren > 0) {
            const fanAngle = Math.min(Math.PI * 0.75, (Math.PI * 2) / numHubs * 0.88);
            children.forEach((cId, cIdx) => {
                const childOffset = numChildren === 1 ? 0 : (cIdx / (numChildren - 1) - 0.5) * fanAngle;
                const childAngle = angle + childOffset;
                const cx = Math.round(rChild * Math.cos(childAngle));
                const cy = Math.round(rChild * Math.sin(childAngle));
                updates.push({ id: cId, x: cx, y: cy, fixed: true });

                // Check leaf nodes (e.g. credentials attached to leaks)
                const grandchildren = rawGraphEdges.filter(e => e.from === cId).map(e => e.to);
                const numGrand = grandchildren.length;
                if (numGrand > 0) {
                    const grandFan = 0.38;
                    grandchildren.forEach((gId, gIdx) => {
                        const grandOffset = numGrand === 1 ? 0 : (gIdx / (numGrand - 1) - 0.5) * grandFan;
                        const grandAngle = childAngle + grandOffset;
                        const gx = Math.round(rLeaf * Math.cos(grandAngle));
                        const gy = Math.round(rLeaf * Math.sin(grandAngle));
                        updates.push({ id: gId, x: gx, y: gy, fixed: true });
                    });
                }
            });
        }
    });

    // Handle direct children if any
    directChildren.forEach((dId, dIdx) => {
        const dAngle = (2 * Math.PI * dIdx) / (directChildren.length || 1);
        updates.push({
            id: dId,
            x: Math.round(480 * Math.cos(dAngle)),
            y: Math.round(480 * Math.sin(dAngle)),
            fixed: true
        });
    });

    // Apply updates
    currentNodesDataSet.update(updates);

    // Disable physics to preserve orbit geometry
    isPhysicsEnabled = false;
    const btnPhys = document.getElementById("btn-graph-physics");
    if (btnPhys) btnPhys.innerHTML = "[PHYSICS: OFF]";
    networkInstance.setOptions({ physics: { enabled: false } });

    networkInstance.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
    if (typeof showToast === "function") showToast("Graph organized in clean concentric orbits.", "success");
}
window.tidyGraphConcentric = tidyGraphConcentric;

/**
 * Render Vis.js interactive graph
 */
function renderGraph(graphData) {
    const container = document.getElementById("network-graph") || document.getElementById("network-canvas");
    if (!container || !window.vis) return;

    rawGraphNodes = graphData.nodes || [];
    rawGraphEdges = graphData.edges || [];

    const processedNodes = getProcessedNodes(rawGraphNodes);
    currentNodesDataSet = new vis.DataSet(processedNodes);
    currentEdgesDataSet = new vis.DataSet(rawGraphEdges);
    const data = { nodes: currentNodesDataSet, edges: currentEdgesDataSet };

    let layoutConfig = {};
    let physicsConfig = {};

    if (isHierarchicalView) {
        layoutConfig = {
            hierarchical: {
                enabled: true,
                direction: "LR",
                sortMethod: "directed",
                levelSeparation: 260,
                nodeSpacing: 180,
                treeSpacing: 200,
                blockShifting: true,
                edgeMinimization: true,
                parentCentralization: true
            }
        };
        physicsConfig = { enabled: false };
    } else {
        layoutConfig = { hierarchical: { enabled: false } };
        physicsConfig = {
            enabled: isPhysicsEnabled,
            solver: "forceAtlas2Based",
            forceAtlas2Based: {
                gravitationalConstant: -380, // Strong repulsion separates nodes so they don't bunch into a crowded ball!
                centralGravity: 0.003,      // Minimal central pull keeps network expanded
                springLength: 280,          // Long springs create distinct breathing room between hubs and items
                springConstant: 0.035,      // Gentle spring prevents jitter
                damping: 0.7,               // Smooth settling
                avoidOverlap: 1.0           // Strict overlap prevention ensures cards never intersect
            },
            stabilization: {
                iterations: 180,
                updateInterval: 25
            }
        };
    }

    const isLightMode = isCurrentThemeLight();
    const options = {
        interaction: {
            hover: true,
            tooltipDelay: 80,
            zoomView: true,
            dragView: true,
            navigationButtons: false,
            keyboard: false
        },
        layout: layoutConfig,
        physics: physicsConfig,
        nodes: {
            shape: "box",
            shapeProperties: { borderRadius: 6 },
            margin: { top: 8, bottom: 8, left: 12, right: 12 },
            borderWidth: 1.5,
            borderWidthSelected: 2.5,
            font: {
                face: "'JetBrains Mono', monospace",
                size: 11,
                color: isLightMode ? '#0f172a' : '#f8fafc'
            },
            shadow: {
                enabled: true,
                color: isLightMode ? 'rgba(15, 23, 42, 0.10)' : 'rgba(0,0,0,0.5)',
                size: 8,
                x: 2,
                y: 3
            }
        },
        groups: isLightMode ? LIGHT_GRAPH_GROUPS : DARK_GRAPH_GROUPS,
        edges: {
            color: isLightMode ? { color: '#94a3b8', highlight: '#0284c7', hover: '#0284c7' } : { color: '#384259', highlight: '#7dd3fc', hover: '#7dd3fc' },
            smooth: {
                type: 'cubicBezier',
                forceDirection: isHierarchicalView ? 'horizontal' : 'none',
                roundness: 0.35
            }
        }
    };

    if (networkInstance) {
        networkInstance.destroy();
        networkInstance = null;
    }

    // Clear the standby placeholder before mounting vis.js
    container.innerHTML = "";

    networkInstance = new vis.Network(container, data, options);

    // If a category was previously filtered, apply it
    if (currentCategoryFilter && currentCategoryFilter !== "all") {
        filterGraphCategory(currentCategoryFilter);
    }

    // Node click handler
    networkInstance.on("click", (params) => {
        if (params.nodes.length > 0) {
            if (window.sfx) window.sfx.playInspect();
            renderNodeInspector(params.nodes[0]);
        }
    });
}

/**
 * Slide-in Node Inspector
 */
function renderNodeInspector(nodeId) {
    const drawer = document.getElementById("node-inspector");
    const titleEl = document.getElementById("inspector-node-title");
    const bodyEl = document.getElementById("inspector-node-body");
    if (!drawer || !bodyEl || !currentInvestigationData) return;

    const node = (currentInvestigationData.graph.nodes || []).find(n => n.id === nodeId);
    if (!node) return;

    if (titleEl) titleEl.innerText = `Node: ${node.group.toUpperCase()}`;

    let html = `
        <div style="margin-bottom: 0.75rem;">
            <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Node Label:</div>
            <div style="font-weight: 600; color: var(--t-primary); white-space: pre-line; margin-top: 0.2rem;">${escapeHtml(node.label)}</div>
        </div>
        <div style="margin-bottom: 0.75rem;">
            <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Entity Classification:</div>
            <div style="margin-top: 0.2rem;"><span class="badge-pill badge-low">${escapeHtml(node.group)}</span></div>
        </div>
    `;

    const grp = node.group;
    if (grp === "credentials" || grp === "credential") {
        html += `
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Threat Context:</div>
                <div style="margin-top: 0.3rem; color: #f87171;">Exfiltrated credential or cryptographic hash record. Correlates with account takeover and password reuse attacks.</div>
            </div>
        `;
    } else if (grp === "physical") {
        html += `
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Physical Exposure:</div>
                <div style="margin-top: 0.3rem; color: #34d399;">Residential or public profile location. Potential vector for physical reconnaissance.</div>
            </div>
        `;
    } else if (grp === "relatives" || grp === "relative") {
        html += `
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Social Engineering:</div>
                <div style="margin-top: 0.3rem; color: #f472b6;">Co-habitant sharing the same residence and surname. Prime vector for spear-phishing or vishing extortion.</div>
            </div>
        `;
    } else if (grp === "pivots" || grp === "pivot") {
        html += `
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Cross-Platform Pivot:</div>
                <div style="margin-top: 0.3rem; color: #06b6d4;">Secondary identifier or public account discovered through OSINT enumeration.</div>
            </div>
        `;
    } else if (grp === "pivot_account" || (node.data && (node.data.type === "PUBLIC_ACCOUNT" || node.data.category === "accounts"))) {
        const platKey = normalizePlatform(node.data?.value || node.label);
        const matchingSuspects = (currentInvestigationData.pivots || []).filter(p => 
            (p.pivot_type === "SUSPECTED_ACCOUNT" || (p.context_note && p.context_note.includes("[STATUS: SUSPECTED]"))) &&
            normalizePlatform(p.pivot_value) === platKey
        );

        html += `
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Verified Platform Identity:</div>
                <div style="margin-top: 0.3rem; padding: 0.5rem 0.7rem; background: var(--accent-emerald-subtle); border-left: 3px solid var(--accent-emerald); border-radius: 4px;">
                    <div style="color: var(--accent-emerald); font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 4px;">${getUiIcon("check", "w-3 h-3 text-emerald-400")} Confirmed Account Registration</div>
                    <div style="font-size: 0.74rem; color: var(--t-secondary); margin-top: 0.2rem;">${escapeHtml(node.data?.context || 'Target email address is confirmed registered on this platform.')}</div>
                </div>
            </div>
        `;

        if (matchingSuspects.length > 0) {
            html += `
                <div style="margin-top: 0.75rem; padding: 0.6rem 0.75rem; background: var(--c-surface); border: 1px dashed rgba(245, 158, 11, 0.4); border-radius: 6px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.45rem;">
                        <span style="color: #fbbf24; font-size: 0.75rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;">
                            ${getUiIcon("search", "w-3 h-3 text-amber-400")} CANDIDATE IDENTIFIERS (${matchingSuspects.length})
                        </span>
                        <span style="font-size: 0.68rem; color: #94a3b8;">Handle masked by API</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #94a3b8; margin-bottom: 0.5rem; line-height: 1.4;">
                        The platform confirmed the email exists, but masks public handles. These candidate handles were derived from known user aliases:
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 0.45rem;">
                        ${matchingSuspects.map(c => {
                            let cLink = c.context_note ? c.context_note.match(/\[URL:\s*(https?:\/\/[^\]]+)\]/) : null;
                            let cUrl = cLink ? cLink[1] : null;
                            let cCtx = c.context_note ? c.context_note.replace(/\[URL:\s*https?:\/\/[^\]]+\]/, '').replace(/\[STATUS:\s*SUSPECTED\]\s*/, '').replace(/\[PLATFORM:\s*[^\]]+\]\s*/, '').trim() : "";
                                        if (cCtx.includes("Root stem derived from authenticated account login")) {
                                            cCtx = cCtx.replace("Root stem derived from authenticated account login", "Stem match:");
                                        }
                            let cConf = Math.round((c.confidence_score || 0.6) * 100);
                            return `
                                <div style="background: var(--c-elevated); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 4px; padding: 0.4rem 0.6rem;">
                                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.4rem;">
                                        <strong style="color: #fbbf24; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace;">${escapeHtml(c.pivot_value)}</strong>
                                        <span class="badge-pill" style="background: rgba(245, 158, 11, 0.15); color: #fde68a; font-size: 0.65rem;">${cConf}% CONF</span>
                                    </div>
                                    <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 0.2rem;">${escapeHtml(cCtx || 'Candidate handle probe')}</div>
                                    ${cUrl ? `
                                        <div style="margin-top: 0.35rem;">
                                            <a href="${escapeHtml(cUrl)}" target="_blank" rel="noopener noreferrer" class="btn-mini-unlock" style="color: #fbbf24; border-color: rgba(245, 158, 11, 0.4); text-decoration: none; font-size: 0.68rem; padding: 2px 6px;">Inspect Profile &rarr;</a>
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        } else {
            html += `
                <div style="margin-top: 0.75rem; font-size: 0.75rem; color: #94a3b8; font-style: italic;">
                    ${getUiIcon("lock", "w-3 h-3 text-zinc-500 inline mr-1")} Public handle is not disclosed by the platform API upon email check. No candidate aliases matched this platform.
                </div>
            `;
        }
    } else if (grp === "hub_accounts") {
        const allPivs = currentInvestigationData.pivots || [];
        const suspPivs = allPivs.filter(p => p.pivot_type === "SUSPECTED_ACCOUNT" || (p.context_note && p.context_note.includes("[STATUS: SUSPECTED]")));
        const verPivs = allPivs.filter(p => !suspPivs.includes(p) && (p.pivot_type === "PUBLIC_PROFILE" || p.pivot_type === "ACCOUNT_REGISTRATION"));

        html += `
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">Accounts Hub Architecture:</div>
                <div style="margin-top: 0.3rem; color: var(--t-secondary); font-size: 0.78rem;">
                    Correlates verified identity endpoints with candidate handle investigations.
                </div>
                <div style="margin-top: 0.6rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 110px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 4px; padding: 0.5rem; text-align: center;">
                        <div style="color: #34d399; font-size: 1.1rem; font-weight: 700;">${verPivs.length}</div>
                        <div style="color: #94a3b8; font-size: 0.68rem; text-transform: uppercase;">Verified Services</div>
                    </div>
                    <div style="flex: 1; min-width: 110px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 4px; padding: 0.5rem; text-align: center;">
                        <div style="color: #fbbf24; font-size: 1.1rem; font-weight: 700;">${suspPivs.length}</div>
                        <div style="color: #94a3b8; font-size: 0.68rem; text-transform: uppercase;">Suspected Candidates</div>
                    </div>
                </div>
            </div>
        `;
    }

    if (grp === "correlated_identity" || (node.data && node.data.type === "CORRELATED_IDENTITY")) {
        html += `
            <div style="margin-top: 0.75rem; padding: 0.6rem 0.75rem; background: rgba(239, 68, 68, 0.12); border-left: 3px solid #ef4444; border-radius: 4px;">
                <div style="color: #f87171; font-weight: 700; font-size: 0.78rem; display: flex; align-items: center; gap: 4px;">
                    ${getUiIcon("alert", "w-3 h-3 text-rose-400")} LATERAL REUSE / CROSS-TARGET CORRELATION
                </div>
                <div style="font-size: 0.73rem; color: #e2e8f0; margin-top: 0.25rem; line-height: 1.4;">
                    Identified correlation in enterprise threat repository (${escapeHtml(node.data?.correlation_type || 'Shared Credentials/Residence')}).
                    This identity shares exfiltrated credentials, identical password hashes, or residential coordinates with the investigated target.
                </div>
            </div>
        `;
    }

    // Determine pivotability
    let pivotType = node.data?.pivot_type || "";
    let pivotValue = node.data?.pivot_value || "";

    if (!pivotValue) {
        if (node.data?.password_hash) {
            pivotType = "HASH";
            pivotValue = node.data.password_hash;
        } else if (node.data?.email) {
            pivotType = "EMAIL";
            pivotValue = node.data.email;
        } else if (node.data?.raw_value) {
            pivotType = node.data.pivot_type || "ENTITY";
            pivotValue = node.data.raw_value;
        } else if (node.data?.value) {
            pivotType = node.data.pivot_type || "ENTITY";
            pivotValue = node.data.value;
        }
    }

    html += `
        <div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid var(--border-subtle); display: flex; flex-direction: column; gap: 8px;">
            ${(pivotValue && (pivotType || node.data?.can_pivot)) ? `
                <button type="button" class="btn-primary w-full py-2 px-3 text-xs mono" style="background: linear-gradient(135deg, #0284c7, #38bdf8); color: #04131f; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 0 14px rgba(56, 189, 248, 0.35); border: none; cursor: pointer; border-radius: 4px;" onclick="pivotOnEntity('${escapeHtml(pivotType)}', '${escapeHtml(pivotValue)}')">
                    [PIVOT ON THIS ENTITY: ${escapeHtml(pivotType || 'INVESTIGATE')}]
                </button>
            ` : ''}
            <button type="button" class="btn-primary w-full py-2 px-3 text-xs mono" style="background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 0 14px rgba(16, 185, 129, 0.35); border: none; cursor: pointer; border-radius: 4px;" onclick="expandGraphFromNode('${escapeHtml(nodeId)}', '${escapeHtml(pivotType)}', '${escapeHtml(pivotValue)}')">
                [EXPAND GRAPH FROM NODE (+)]
            </button>
        </div>
    `;

    bodyEl.innerHTML = html;
    drawer.style.display = "flex";
}

/**
 * Click-to-Pivot Dynamic Graph Expansion & Investigation
 */
function pivotOnEntity(pivotType, pivotValue) {
    if (!pivotValue) return;
    const cleanVal = pivotValue.trim();
    showToast(`Pivoting investigation on ${pivotType}: ${cleanVal}`, "info");

    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.value = cleanVal;
    }

    if (pivotType === "HASH") {
        fetch(`/api/hash/resolve?hash=${encodeURIComponent(cleanVal)}`)
            .then(r => r.json())
            .then(data => {
                if (data.resolved && data.plaintext) {
                    showToast(`Cracked: ${data.plaintext} via ${data.source || 'Rainbow Table'}`, "success");
                    const bodyEl = document.getElementById("inspector-node-body");
                    if (bodyEl) {
                        const crackHtml = `
                            <div style="margin-top: 0.75rem; padding: 0.7rem; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 6px;">
                                <div style="color: #34d399; font-weight: 700; font-size: 0.82rem;">[RESOLVED PLAINTEXT PASSWORD]</div>
                                <div style="font-size: 1.1rem; font-weight: 700; color: var(--t-primary); margin-top: 0.3rem; font-family: 'JetBrains Mono', monospace;">${escapeHtml(data.plaintext)}</div>
                                <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 0.3rem;">Algorithm: ${escapeHtml(data.algorithm || 'MD5')} | Source: ${escapeHtml(data.source || 'Rainbow Table')}</div>
                            </div>
                        `;
                        bodyEl.insertAdjacentHTML("beforeend", crackHtml);
                    }
                } else {
                    showToast(data.reason || "Hash not resolved in public tables.", "warning");
                }
            })
            .catch(err => showToast("Hash resolution error: " + err.message, "error"));
        return;
    }

    if (pivotType === "DOMAIN") {
        executeDomainRecon(cleanVal);
        return;
    }

    if (pivotType === "PHONE") {
        fetch(`/api/recon/telecom?query=${encodeURIComponent(cleanVal)}`)
            .then(r => r.json())
            .then(res => {
                if (res.e164_formatted || res.carrier) {
                    showToast(`Telecom: ${res.e164_formatted || cleanVal} | Carrier: ${res.carrier || 'Detected'}`, "success");
                }
            })
            .catch(() => {});
        return;
    }

    // Default: EMAIL, USERNAME, or IDENTITY
    currentEmail = cleanVal;
    executeInvestigation(currentEmail);
}

/**
 * In-Place Multi-Hop Vis.js Graph Expansion
 */
async function expandGraphFromNode(nodeId, pivotType, pivotValue) {
    if (!currentNodesDataSet || !currentEdgesDataSet) {
        showToast("Network graph is not initialized.", "warning");
        return;
    }
    showToast(`Expanding multi-hop links from ${nodeId}...`, "info");
    const existingIds = currentNodesDataSet.getIds();

    try {
        const resp = await fetch("/api/graph/pivot-expand", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                node_id: nodeId,
                pivot_type: pivotType || "",
                pivot_value: pivotValue || "",
                current_node_ids: existingIds,
                audit_mode: isDeclassified
            })
        });
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }
        const data = await resp.json();
        const newNodes = data.new_nodes || [];
        const newEdges = data.new_edges || [];

        if (newNodes.length === 0) {
            showToast("No further lateral correlations or unlinked nodes discovered for this entity.", "warning");
            return;
        }

        const processed = getProcessedNodes(newNodes);
        currentNodesDataSet.add(processed);
        currentEdgesDataSet.add(newEdges);

        rawGraphNodes.push(...newNodes);
        rawGraphEdges.push(...newEdges);

        if (currentInvestigationData && currentInvestigationData.graph) {
            currentInvestigationData.graph.nodes = currentInvestigationData.graph.nodes || [];
            currentInvestigationData.graph.edges = currentInvestigationData.graph.edges || [];
            currentInvestigationData.graph.nodes.push(...newNodes);
            currentInvestigationData.graph.edges.push(...newEdges);
        }

        const focusIds = [nodeId, ...newNodes.map(n => n.id)];
        if (networkInstance) {
            networkInstance.fit({
                nodes: focusIds,
                animation: { duration: 700, easingFunction: 'easeInOutQuad' }
            });
        }

        showToast(`Graph expanded: +${newNodes.length} lateral entities connected!`, "success");

        const bodyEl = document.getElementById("inspector-node-body");
        if (bodyEl) {
            const expBadge = `
                <div style="margin-top: 0.6rem; padding: 0.4rem 0.6rem; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 4px; font-size: 0.72rem; color: #34d399; font-family: 'JetBrains Mono', monospace;">
                    [+] Attached ${newNodes.length} lateral hops to canvas
                </div>
            `;
            bodyEl.insertAdjacentHTML("beforeend", expBadge);
        }
    } catch (err) {
        showToast(`Graph expansion error: ${err.message}`, "error");
    }
}
window.expandGraphFromNode = expandGraphFromNode;

/**
 * Functions & Forensic Tools Hub Modal Controllers
 */
function openToolsModal() {
    playSound("click");
    const modal = document.getElementById("tools-modal");
    if (modal) modal.style.display = "flex";
}
window.openToolsModal = openToolsModal;

function closeToolsModal() {
    playSound("click");
    const modal = document.getElementById("tools-modal");
    if (modal) modal.style.display = "none";
}
window.closeToolsModal = closeToolsModal;

function handleToolsModalBackdropClick(event) {
    if (event.target && event.target.id === "tools-modal") {
        closeToolsModal();
    }
}
window.handleToolsModalBackdropClick = handleToolsModalBackdropClick;

function launchTool(toolName) {
    playSound("click");
    closeToolsModal();
    if (toolName === "combolist" && typeof openCombolistModal === "function") {
        openCombolistModal();
    } else if (toolName === "phone" && typeof openReversePhoneModal === "function") {
        openReversePhoneModal();
    } else if (toolName === "image" && typeof openImageCorrelationModal === "function") {
        openImageCorrelationModal();
    } else if (toolName === "batch" && typeof openBatchModal === "function") {
        openBatchModal();
    }
}
window.launchTool = launchTool;

/**
 * Combolist Ingestion Modal Controllers
 */
function openCombolistModal() {
    playSound("click");
    const modal = document.getElementById("combolist-modal");
    if (modal) modal.style.display = "flex";
}

function closeCombolistModal() {
    playSound("click");
    const modal = document.getElementById("combolist-modal");
    if (modal) modal.style.display = "none";
}

function handleCombolistModalBackdropClick(event) {
    if (event.target && event.target.id === "combolist-modal") {
        closeCombolistModal();
    }
}

function loadSampleCombolist() {
    const nameInput = document.getElementById("combolist-leak-name");
    const dateInput = document.getElementById("combolist-breach-date");
    const textarea = document.getElementById("combolist-textarea");

    if (nameInput) nameInput.value = "Nexus Data Broker Exfiltration 2024";
    if (dateInput) dateInput.value = "2024-03-15";
    if (textarea) {
        textarea.value = [
            "victim.user1@cybercorp.io:Spring2024!#",
            "alex.morgan@cybercorp.io:Summer2023!#",
            "marcus.vance@cybercorp.io:SecretCorpPass99",
            "jordan.dev@techhub.net:jordan:DevOps2024$$",
            "sarah.jenkins@gmail.com:SarahJ2022!#",
            "sec_analyst@cybercorp.io:P@ssw0rd2024!"
        ].join("\\n");
    }
}

function submitCombolistImport() {
    const nameInput = document.getElementById("combolist-leak-name");
    const dateInput = document.getElementById("combolist-breach-date");
    const textarea = document.getElementById("combolist-textarea");
    const statusEl = document.getElementById("combolist-status");
    const submitBtn = document.getElementById("btn-submit-combolist");

    const rawText = textarea ? textarea.value.trim() : "";
    const leakName = nameInput && nameInput.value.trim() ? nameInput.value.trim() : "Custom Ingested Leak";
    const breachDate = dateInput ? dateInput.value : "";

    if (!rawText) {
        showToast("Please provide combolist lines to ingest.", "warning");
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Ingesting...";
    }

    if (statusEl) {
        statusEl.style.display = "block";
        statusEl.style.background = "rgba(14, 165, 233, 0.1)";
        statusEl.style.border = "1px solid rgba(14, 165, 233, 0.3)";
        statusEl.style.color = "#38bdf8";
        statusEl.innerText = "Processing records and generating cryptographic hashes...";
    }

    fetch("/api/breach/import-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            raw_text: rawText,
            leak_name: leakName,
            leak_type: "DATABASE_LEAK",
            breach_date: breachDate || null,
            source: "Web UI Ingestion"
        })
    })
    .then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
    })
    .then(res => {
        if (statusEl) {
            statusEl.style.background = "rgba(16, 185, 129, 0.15)";
            statusEl.style.border = "1px solid rgba(16, 185, 129, 0.4)";
            statusEl.style.color = "#34d399";
            statusEl.innerHTML = `
                <strong>[+] Ingestion Succeeded!</strong><br>
                Records Ingested: <strong>${res.total_records || 0}</strong><br>
                Unique Identities Linked: <strong>${res.unique_emails || 0}</strong><br>
                Hashes / Plaintexts Created: <strong>${(res.total_hashes || 0) + (res.total_plains || 0)}</strong><br>
                Time: <strong>${res.elapsed_sec || 0}s</strong>
            `;
        }
        showToast(`Ingested ${res.total_records || 0} records across ${res.unique_emails || 0} targets!`, "success");
        fetchThreatStats();
        fetchEmployees();
    })
    .catch(err => {
        if (statusEl) {
            statusEl.style.background = "rgba(239, 68, 68, 0.15)";
            statusEl.style.border = "1px solid rgba(239, 68, 68, 0.4)";
            statusEl.style.color = "#f87171";
            statusEl.innerText = "Ingestion error: " + err.message;
        }
        showToast("Ingestion failed: " + err.message, "error");
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = "Ingest & Correlate →";
        }
    });
}

window.openCombolistModal = openCombolistModal;
window.closeCombolistModal = closeCombolistModal;
window.handleCombolistModalBackdropClick = handleCombolistModalBackdropClick;
window.loadSampleCombolist = loadSampleCombolist;
window.submitCombolistImport = submitCombolistImport;
window.pivotOnEntity = pivotOnEntity;

/**
 * Toast notifications
 */
function showToast(message, type = "info") {
    if (type === "error") playSound("error");
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const iconMap = {
        "success": getUiIcon("check", "w-3.5 h-3.5 text-emerald-400 inline mr-1.5"),
        "info": getUiIcon("alert", "w-3.5 h-3.5 text-sky-400 inline mr-1.5"),
        "warning": getUiIcon("alert", "w-3.5 h-3.5 text-amber-400 inline mr-1.5"),
        "error": getUiIcon("cross", "w-3.5 h-3.5 text-rose-400 inline mr-1.5")
    };

    toast.innerHTML = `${iconMap[type] || ''} <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(6px)";
        setTimeout(() => toast.remove(), 250);
    }, 3200);
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* =========================================================================
 * 12. FREE AI THREAT INTELLIGENCE ENGINE & COPILOT (GROQ LLAMA 3.3 & GEMINI)
 * ========================================================================= */
const AI_KEY_STORAGE = "breachspillover_ai_key";
const AI_PROVIDER_STORAGE = "breachspillover_ai_provider";
let currentAIDossier = null;
let currentAICopilotHistory = [];
let serverAIConfig = null;

async function checkServerAIStatus() {
    try {
        const resp = await fetch("/api/ai/status");
        if (resp.ok) {
            serverAIConfig = await resp.json();
            updateAIHeaderStatus();
        }
    } catch (e) {
        console.warn("Could not query /api/ai/status:", e);
    }
}

function getAIKey() {
    return localStorage.getItem(AI_KEY_STORAGE) || "";
}

function getAIProvider() {
    return localStorage.getItem(AI_PROVIDER_STORAGE) || (serverAIConfig && serverAIConfig.provider ? serverAIConfig.provider : "groq");
}

function updateAIHeaderStatus() {
    const btn = document.getElementById("btn-ai-settings");
    const icon = document.getElementById("ai-status-icon");
    const text = document.getElementById("ai-status-text");
    if (!btn || !text) return;

    const key = getAIKey();
    const prov = getAIProvider();

    if (key) {
        text.innerText = `AI: ${prov.toUpperCase()} ACTIVE`;
        btn.style.borderColor = "#a855f7";
        btn.style.color = "#c084fc";
        btn.style.background = "rgba(168, 85, 247, 0.16)";
        if (icon) icon.innerHTML = getUiIcon("bolt", "w-3 h-3 text-purple-400 inline mr-1.5");
    } else if (serverAIConfig && serverAIConfig.has_key) {
        text.innerText = `AI: ${serverAIConfig.provider.toUpperCase()} ACTIVE (.env)`;
        btn.style.borderColor = "#a855f7";
        btn.style.color = "#c084fc";
        btn.style.background = "rgba(168, 85, 247, 0.16)";
        if (icon) icon.innerHTML = getUiIcon("bolt", "w-3 h-3 text-purple-400 inline mr-1.5");
    } else {
        text.innerText = "AI ENGINE: OFFLINE [ADD KEY]";
        btn.style.borderColor = "#475569";
        btn.style.color = "#94a3b8";
        btn.style.background = "rgba(30, 41, 59, 0.4)";
        if (icon) icon.innerHTML = getUiIcon("settings", "w-3 h-3 text-zinc-400 inline mr-1.5");
    }
}

function openAISettingsModal() {
    const modal = document.getElementById("ai-settings-modal");
    if (!modal) return;

    const provSelect = document.getElementById("ai-provider-select");
    const keyInput = document.getElementById("ai-api-key-input");
    const statusDiv = document.getElementById("ai-test-status");

    if (provSelect) provSelect.value = getAIProvider();
    if (keyInput) keyInput.value = getAIKey();

    if (statusDiv) {
        if (!getAIKey() && serverAIConfig && serverAIConfig.has_key) {
            statusDiv.style.display = "block";
            statusDiv.style.background = "rgba(16, 185, 129, 0.08)";
            statusDiv.style.color = "#6ee7b7";
            statusDiv.style.border = "1px solid rgba(16, 185, 129, 0.25)";
            statusDiv.innerHTML = `<div class="flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span> <span>Key loaded from .env: <code>${escapeHtml(serverAIConfig.masked_key)}</code> (${escapeHtml(serverAIConfig.provider.toUpperCase())} / ${escapeHtml(serverAIConfig.model)})</span></div>`;
        } else {
            statusDiv.style.display = "none";
        }
    }

    onAIProviderChanged();
    modal.style.display = "flex";
}

function closeAISettingsModal() {
    const modal = document.getElementById("ai-settings-modal");
    if (modal) modal.style.display = "none";
}

function handleAISettingsBackdropClick(e) {
    if (e.target.id === "ai-settings-modal") {
        closeAISettingsModal();
    }
}

function onAIProviderChanged() {
    const prov = document.getElementById("ai-provider-select")?.value || "groq";
    const link = document.getElementById("ai-get-key-link");
    const input = document.getElementById("ai-api-key-input");

    if (prov === "gemini") {
        if (link) {
            link.href = "https://aistudio.google.com/app/apikey";
            link.innerHTML = "Get Gemini Key &nearr;";
        }
        if (input) input.placeholder = "AIzaSy...";
    } else {
        if (link) {
            link.href = "https://console.groq.com/keys";
            link.innerHTML = "Get Groq Key &nearr;";
        }
        if (input) input.placeholder = "gsk_...";
    }
}

function toggleAIKeyVisibility() {
    const input = document.getElementById("ai-api-key-input");
    if (input) {
        input.type = input.type === "password" ? "text" : "password";
    }
}

function saveAISettings() {
    const prov = document.getElementById("ai-provider-select")?.value || "groq";
    const key = (document.getElementById("ai-api-key-input")?.value || "").trim();

    localStorage.setItem(AI_PROVIDER_STORAGE, prov);
    if (key) {
        localStorage.setItem(AI_KEY_STORAGE, key);
        showToast(`AI Provider set to ${prov.toUpperCase()} with active key.`, "success");
    } else {
        localStorage.removeItem(AI_KEY_STORAGE);
        showToast("Switched to offline deterministic AI fallback.", "info");
    }

    updateAIHeaderStatus();
    closeAISettingsModal();

    // Invalidate cached dossier so next generation uses new key
    currentAIDossier = null;
    if (currentInvestigationData) {
        renderAITab(currentInvestigationData, true);
    }
}

function clearAIKey() {
    localStorage.removeItem(AI_KEY_STORAGE);
    const keyInput = document.getElementById("ai-api-key-input");
    if (keyInput) keyInput.value = "";
    updateAIHeaderStatus();
    showToast("AI Key cleared. Switched to offline deterministic fallback.", "info");
}

async function testAIKeyConnection() {
    const prov = document.getElementById("ai-provider-select")?.value || "groq";
    const inputKey = (document.getElementById("ai-api-key-input")?.value || "").trim();
    const key = inputKey || (serverAIConfig && serverAIConfig.has_key ? "" : "");
    const statusDiv = document.getElementById("ai-test-status");
    const btn = document.getElementById("btn-ai-test");

    if (!inputKey && (!serverAIConfig || !serverAIConfig.has_key)) {
        showToast("Please paste an API key to test.", "warning");
        return;
    }

    if (btn) btn.disabled = true;
    if (statusDiv) {
        statusDiv.style.display = "block";
        statusDiv.style.background = "rgba(99, 102, 241, 0.12)";
        statusDiv.style.color = "#c7d2fe";
        statusDiv.style.border = "1px solid rgba(99, 102, 241, 0.3)";
        statusDiv.innerText = "Probing API endpoint and measuring round-trip latency...";
    }

    try {
        const resp = await fetch("/api/ai/test-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: key, provider: prov })
        });
        const res = await resp.json();

        if (res.success) {
            statusDiv.style.background = "rgba(16, 185, 129, 0.12)";
            statusDiv.style.color = "#6ee7b7";
            statusDiv.style.border = "1px solid rgba(16, 185, 129, 0.3)";
            statusDiv.innerHTML = `<div class="flex items-center gap-2 text-emerald-400"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span> <span>Connection Verified: <strong>${escapeHtml(res.provider.toUpperCase())}</strong> • Latency: <strong>${res.latency_seconds || 0.3}s</strong></span></div>`;
        } else {
            statusDiv.style.background = "rgba(239, 68, 68, 0.12)";
            statusDiv.style.color = "#fca5a5";
            statusDiv.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            statusDiv.innerHTML = `<div class="flex items-center gap-2 text-rose-400"><span class="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block"></span> <span>Test Failed: ${escapeHtml(res.error || 'Invalid API Key')}</span></div>`;
        }
    } catch (e) {
        if (statusDiv) {
            statusDiv.style.background = "rgba(239, 68, 68, 0.12)";
            statusDiv.style.color = "#fca5a5";
            statusDiv.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            statusDiv.innerText = `Network error: ${e.message}`;
        }
    } finally {
        if (btn) btn.disabled = false;
    }
}

/* ==========================================================================
   AI Forensic Copilot: Side Drawer, Executive Dossier & Interactive Chat
   ========================================================================== */

let copilotChatHistory = [];

window.toggleAICopilotDrawer = function() {
    playSound("click");
    const drawer = document.getElementById("ai-copilot-drawer");
    const backdrop = document.getElementById("ai-copilot-backdrop");
    const badge = document.getElementById("copilot-unread-badge");
    if (!drawer) return;
    const isOpen = drawer.classList.contains("open");
    if (isOpen) {
        drawer.classList.remove("open");
        if (backdrop) backdrop.classList.remove("active");
    } else {
        drawer.classList.add("open");
        if (backdrop) backdrop.classList.add("active");
        if (badge) badge.style.display = "none";
    }
};

window.openAICopilotDrawer = function() {
    playSound("click");
    const drawer = document.getElementById("ai-copilot-drawer");
    const backdrop = document.getElementById("ai-copilot-backdrop");
    const badge = document.getElementById("copilot-unread-badge");
    if (drawer) drawer.classList.add("open");
    if (backdrop) backdrop.classList.add("active");
    if (badge) badge.style.display = "none";
};

window.closeAICopilotDrawer = function() {
    playSound("click");
    const drawer = document.getElementById("ai-copilot-drawer");
    const backdrop = document.getElementById("ai-copilot-backdrop");
    if (drawer) drawer.classList.remove("open");
    if (backdrop) backdrop.classList.remove("active");
};

window.switchCopilotTab = function(tabName) {
    playSound("click");
    const btnDossier = document.getElementById("copilot-tab-btn-dossier");
    const btnChat = document.getElementById("copilot-tab-btn-chat");
    const panelDossier = document.getElementById("copilot-panel-dossier");
    const panelChat = document.getElementById("copilot-panel-chat");

    if (tabName === "dossier") {
        if (btnDossier) btnDossier.classList.add("active");
        if (btnChat) btnChat.classList.remove("active");
        if (panelDossier) panelDossier.classList.add("active");
        if (panelChat) panelChat.classList.remove("active");
    } else {
        if (btnChat) btnChat.classList.add("active");
        if (btnDossier) btnDossier.classList.remove("active");
        if (panelChat) panelChat.classList.add("active");
        if (panelDossier) panelDossier.classList.remove("active");
        const input = document.getElementById("copilot-chat-input");
        if (input) setTimeout(() => input.focus(), 150);
    }
};

async function renderAIReviewSection(data, forceRefresh = false) {
    const container = document.getElementById("copilot-dossier-content") || document.getElementById("ai-review-body");
    const engineLabelEl = document.getElementById("copilot-engine-label");
    const unreadBadge = document.getElementById("copilot-unread-badge");
    const drawer = document.getElementById("ai-copilot-drawer");

    if (!data) return;

    if (currentAIDossier && !forceRefresh) {
        renderAIDossierContent(currentAIDossier, data);
        return;
    }

    // Show loading state in dossier panel
    if (container) {
        container.innerHTML = `
            <div style="padding: 28px 16px; text-align: center; background: rgba(168, 85, 247, 0.05); border: 1px solid rgba(168, 85, 247, 0.2); border-radius: 8px;">
                <div style="margin-bottom: 12px; display: inline-block;">
                    <div class="stats-dot" style="width: 14px; height: 14px; background: #a855f7; box-shadow: 0 0 14px #a855f7;"></div>
                </div>
                <div style="font-size: 0.92rem; font-weight: 700; color: var(--t-primary); font-family: 'JetBrains Mono', monospace;">
                    Synthesizing AI Forensic Dossier...
                </div>
                <div style="font-size: 0.76rem; color: #94a3b8; margin-top: 8px; line-height: 1.45;">
                    Connecting to ${getAIProvider().toUpperCase()} (Llama 3.3 / Gemini) • Evaluating multi-vector breach correlations
                </div>
            </div>
        `;
    }

    try {
        const resp = await fetch("/api/ai/dossier", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: currentEmail,
                api_key: getAIKey(),
                provider: getAIProvider(),
                scan_data: data,
                force_refresh: forceRefresh
            })
        });
        const dossier = await resp.json();
        currentAIDossier = dossier;
        renderAIDossierContent(dossier, data);

        if (unreadBadge && (!drawer || !drawer.classList.contains("open"))) {
            unreadBadge.style.display = "inline-block";
        }
    } catch (e) {
        if (container) {
            container.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #ef4444;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #f87171;">
                        ${getUiIcon("alert", "w-4 h-4 text-rose-400")} AI Dossier Generation Error
                    </div>
                    <div class="evidence-body" style="margin-top: 0.4rem; color: var(--t-secondary); overflow-wrap: anywhere; word-break: break-word;">
                        ${escapeHtml(e.message)}
                    </div>
                    <div style="margin-top: 12px;">
                        <button type="button" class="btn-copilot-tool btn-copilot-purple" onclick="renderAIReviewSection(currentInvestigationData, true)">
                            Retry Generation &rarr;
                        </button>
                    </div>
                </div>
            `;
        }
    }
}
window.renderAIReviewSection = renderAIReviewSection;

function renderAITab(data, forceRefresh = false) {
    return renderAIReviewSection(data, forceRefresh);
}
window.renderAITab = renderAITab;

window.reanalyzeCurrentAI = function() {
    playSound("click");
    renderAIReviewSection(currentInvestigationData, true);
};

function renderAIDossierContent(dossier, scanData) {
    const container = document.getElementById("copilot-dossier-content") || document.getElementById("ai-review-body");
    if (!container) return;

    const isLiveAI = dossier.is_ai_generated;
    const provider = (dossier.provider || getAIProvider()).toUpperCase();
    const engineLabel = dossier.engine_label || (isLiveAI ? `${provider} (${dossier.model || 'LLM'})` : 'Deterministic CTI Heuristic Synthesizer (Offline)');
    const notice = dossier.notice;

    const engineLabelEl = document.getElementById("copilot-engine-label");
    if (engineLabelEl) engineLabelEl.innerText = engineLabel;

    const personas = dossier.persona_analysis || dossier.persona_disambiguation || [];
    const attackSim = dossier.adversary_attack_simulation || {};
    const remediations = dossier.prioritized_remediations || [];

    // Parse verdict: never let long sentence explanation blowout pill badge
    const rawVerdict = (dossier.threat_level_verdict || "").trim();
    let verdictPill = "THREAT EVALUATED";
    let verdictExplanation = "";
    if (rawVerdict.length > 25) {
        verdictPill = rawVerdict.split(" ")[0].toUpperCase() + " RISK";
        verdictExplanation = rawVerdict;
    } else if (rawVerdict.length > 0) {
        verdictPill = rawVerdict.toUpperCase();
    }

    let noticeHtml = "";
    if (notice) {
        noticeHtml = `
            <div style="margin-bottom: 12px; padding: 10px 12px; background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; border-radius: 4px; display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                <span style="font-size: 0.74rem; color: #fde68a; overflow-wrap: anywhere; word-break: break-word;">[INFO] ${escapeHtml(notice)}</span>
                <button type="button" class="btn-copilot-tool" onclick="openAISettingsModal()" style="color: #fbbf24; border-color: #f59e0b; font-size: 0.68rem; padding: 2px 6px; white-space: nowrap;">
                    Configure Key &rarr;
                </button>
            </div>
        `;
    }

    container.innerHTML = `
        <!-- Assessment Overview Card -->
        <div style="margin-bottom: 12px; padding: 12px 14px; background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 6px; min-width: 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <span class="badge-pill mono" style="background: rgba(168, 85, 247, 0.2); color: #d8b4fe; border-color: #a855f7; font-size: 0.68rem;">
                        ${escapeHtml(engineLabel)}
                    </span>
                    <span class="badge-pill mono" style="background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border-color: #38bdf8; font-size: 0.68rem;">
                        ${escapeHtml(verdictPill)}
                    </span>
                </div>
            </div>
            ${verdictExplanation ? `
                <div style="margin-top: 10px; font-size: 0.78rem; color: #e0f2fe; line-height: 1.5; overflow-wrap: anywhere; word-break: break-word; background: rgba(56, 189, 248, 0.05); padding: 8px 10px; border-radius: 4px; border-left: 2px solid #38bdf8;">
                    ${escapeHtml(verdictExplanation)}
                </div>
            ` : ''}
        </div>

        ${noticeHtml}

        <!-- 1. Executive Threat Summary -->
        <div class="evidence-card" style="border-left: 3px solid #a855f7; margin-bottom: 12px;">
            <div class="evidence-title" style="color: #d8b4fe; font-size: 0.88rem;">
                EXECUTIVE FORENSIC SYNTHESIS
            </div>
            <div class="evidence-body" style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--t-primary); line-height: 1.55; white-space: pre-line; overflow-wrap: anywhere; word-break: break-word;">
                ${escapeHtml(dossier.executive_summary || 'No summary available.')}
            </div>
        </div>

        <!-- 2. Candidate Persona Attribution -->
        <div class="evidence-card" style="border-left: 3px solid #38bdf8; margin-bottom: 12px;">
            <div class="evidence-title" style="color: #7dd3fc; font-size: 0.88rem; margin-bottom: 6px;">
                IDENTITY &amp; CANDIDATE ATTRIBUTION
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${personas.length > 0 ? personas.map(p => {
                    const status = (p.status || "").toUpperCase();
                    let badgeStyle = "background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981;";
                    if (status.includes("SUSPECTED")) badgeStyle = "background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b;";
                    if (status.includes("COLLISION") || status.includes("UNLIKELY")) badgeStyle = "background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444;";

                    const pct = Math.round((parseFloat(p.probability_score || 0.8)) * 100);
                    return `
                        <div style="background: var(--c-elevated); border: 1px solid var(--b-hairline); border-radius: 6px; padding: 8px 10px; min-width: 0;">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; flex-wrap: wrap; gap: 4px;">
                                <span class="mono" style="font-weight: 700; color: var(--t-primary); font-size: 0.78rem;">${escapeHtml(p.platform)}: ${escapeHtml(p.handle_or_identifier)}</span>
                                <span class="badge-pill mono" style="${badgeStyle} font-size: 0.62rem;">${pct}% CONF</span>
                            </div>
                            <div style="font-size: 0.72rem; color: #94a3b8; line-height: 1.4; overflow-wrap: anywhere; word-break: break-word;">
                                ${escapeHtml(p.reasoning || '')}
                            </div>
                        </div>
                    `;
                }).join("") : `<div style="font-size: 0.75rem; color: #94a3b8;">No unverified persona collisions indexed. Accounts are confirmed via direct email binding.</div>`}
            </div>
        </div>

        <!-- 3. Adversary Attack Simulation -->
        <div class="evidence-card" style="border-left: 3px solid #f43f5e; margin-bottom: 12px;">
            <div class="evidence-title" style="color: #fda4af; font-size: 0.88rem; margin-bottom: 8px;">
                ADVERSARY ATTACK SIMULATION
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="background: rgba(244, 63, 94, 0.06); border: 1px solid rgba(244, 63, 94, 0.2); border-radius: 6px; padding: 8px 12px; min-width: 0;">
                    <div class="mono" style="font-size: 0.74rem; font-weight: 700; color: #fb7185; margin-bottom: 4px;">
                        Target Spear-Phishing Pretext:
                    </div>
                    <div style="font-size: 0.76rem; color: var(--t-secondary); line-height: 1.45; overflow-wrap: anywhere; word-break: break-word;">
                        ${escapeHtml(attackSim.spear_phishing_pretext || 'Pretext evaluation pending.')}
                    </div>
                </div>

                <div style="background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 6px; padding: 8px 12px; min-width: 0;">
                    <div class="mono" style="font-size: 0.74rem; font-weight: 700; color: #fbbf24; margin-bottom: 4px;">
                        Credential-Stuffing Blast Radius:
                    </div>
                    <div style="font-size: 0.76rem; color: var(--t-secondary); line-height: 1.45; overflow-wrap: anywhere; word-break: break-word;">
                        ${escapeHtml(attackSim.credential_stuffing_blast_radius || 'Blast radius evaluation pending.')}
                    </div>
                </div>
            </div>
        </div>

        <!-- 4. Prioritized Remediations -->
        <div class="evidence-card" style="border-left: 3px solid #10b981; margin-bottom: 8px;">
            <div class="evidence-title" style="color: #6ee7b7; font-size: 0.88rem; margin-bottom: 8px;">
                PRIORITIZED DEFENSIVE MITIGATIONS
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
                ${remediations.map((rem, idx) => `
                    <div style="display: flex; align-items: flex-start; gap: 8px; font-size: 0.76rem; color: var(--t-secondary); line-height: 1.45; overflow-wrap: anywhere; word-break: break-word;">
                        <span class="mono" style="color: #34d399; font-weight: 700; flex-shrink: 0;">[0${idx+1}]</span>
                        <span>${escapeHtml(rem)}</span>
                    </div>
                `).join("")}
            </div>
        </div>
    `;
}

/* ==========================================================================
   Interactive Investigator Copilot Chat
   ========================================================================== */

async function sendCopilotMessage(userText) {
    const text = (userText || "").trim();
    if (!text) return;

    const chatContainer = document.getElementById("copilot-chat-messages");
    const inputEl = document.getElementById("copilot-chat-input");
    const sendBtn = document.getElementById("btn-copilot-send");

    if (inputEl) inputEl.value = "";

    // Append User Message bubble
    if (chatContainer) {
        const userBubble = document.createElement("div");
        userBubble.className = "chat-bubble chat-user";
        userBubble.innerHTML = `
            <div class="chat-bubble-author">INVESTIGATOR</div>
            <div class="chat-bubble-body">${escapeHtml(text)}</div>
        `;
        chatContainer.appendChild(userBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    copilotChatHistory.push({ role: "user", content: text });
    playSound("click");

    // Loading indicator bubble
    let loadingBubble = null;
    if (chatContainer) {
        loadingBubble = document.createElement("div");
        loadingBubble.className = "chat-bubble chat-ai";
        loadingBubble.innerHTML = `
            <div class="chat-bubble-author">AI AGENT</div>
            <div class="chat-bubble-body" style="display: flex; align-items: center; gap: 8px;">
                <span class="status-btn-icon" style="background: #a855f7; box-shadow: 0 0 6px #a855f7;"></span>
                <span>Thinking & synthesizing exposure response...</span>
            </div>
        `;
        chatContainer.appendChild(loadingBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    if (sendBtn) sendBtn.disabled = true;

    try {
        const targetEmail = currentEmail || (currentInvestigationData && currentInvestigationData.employee ? currentInvestigationData.employee.corporate_email : "");
        const resp = await fetch("/api/ai/copilot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                email: targetEmail,
                scan_data: currentInvestigationData,
                history: copilotChatHistory.slice(-6),
                api_key: getAIKey(),
                provider: getAIProvider()
            })
        });

        const resData = await resp.json();
        const rawReply = resData.reply || resData.response || resData.answer || resData.message || (typeof resData === "string" ? resData : "Threat copilot evaluation complete.");
        
        copilotChatHistory.push({ role: "assistant", content: rawReply });

        if (loadingBubble) {
            // Format bold markdown
            const formatted = escapeHtml(rawReply)
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>');
            loadingBubble.innerHTML = `
                <div class="chat-bubble-author">AI AGENT</div>
                <div class="chat-bubble-body" style="white-space: pre-wrap; line-height: 1.55;">${formatted}</div>
            `;
        }
        playSound("click");
    } catch (err) {
        if (loadingBubble) {
            loadingBubble.innerHTML = `
                <div class="chat-bubble-author" style="color: #f87171;">AI AGENT [ERROR]</div>
                <div class="chat-bubble-body" style="color: #fca5a5;">${escapeHtml(err.message || "Failed to reach AI copilot.")}</div>
            `;
        }
    } finally {
        if (sendBtn) sendBtn.disabled = false;
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}
window.sendCopilotMessage = sendCopilotMessage;

window.handleCopilotSubmit = function(e) {
    if (e) e.preventDefault();
    const input = document.getElementById("copilot-chat-input");
    if (input && input.value) {
        sendCopilotMessage(input.value);
    }
};

window.askCopilotPrompt = function(promptText) {
    switchCopilotTab('chat');
    sendCopilotMessage(promptText);
};

// Backward-compatibility aliases
window.submitCopilotChat = function() {
    const input = document.getElementById("copilot-chat-input") || document.getElementById("copilot-input");
    if (input && input.value) {
        sendCopilotMessage(input.value);
    }
};

window.sendCopilotPrompt = function(promptText) {
    askCopilotPrompt(promptText);
};

/**
 * Multi-Country Telecom & Civil Directory Router UI Component
 */
function renderMultiCountryTelecomSection(data, container) {
    if (!container) return;

    let detectedPhone = "";
    let detectedName = data.employee?.full_name || "";
    if (detectedName === "Target User" || detectedName.startsWith("webmail")) {
        detectedName = "";
    }

    if (data.relatives) {
        for (const r of data.relatives) {
            if (r.contact_phone && !detectedPhone) {
                detectedPhone = r.contact_phone;
            }
        }
    }
    if (data.pivots) {
        for (const p of data.pivots) {
            if (p.pivot_type === "PHONE" && !detectedPhone) {
                detectedPhone = p.pivot_value;
            }
        }
    }

    const queryTarget = detectedPhone || detectedName || (currentEmail ? currentEmail.split("@")[0] : "");
    const isNorwegian = (data.physical_footprints || []).some(f => (f.country || "").toLowerCase().includes("norway")) || detectedPhone.startsWith("+47");
    const isPolish = detectedPhone.startsWith("+48") || (currentEmail || "").endsWith(".pl");
    const isSwedish = detectedPhone.startsWith("+46") || (currentEmail || "").endsWith(".se");
    const isDanish = detectedPhone.startsWith("+45") || (currentEmail || "").endsWith(".dk");
    const isUS = detectedPhone.startsWith("+1");
    const isUK = detectedPhone.startsWith("+44") || (currentEmail || "").endsWith(".uk");
    const isGerman = detectedPhone.startsWith("+49") || (currentEmail || "").endsWith(".de");

    let initialCountry = "GLOBAL";
    if (isNorwegian) initialCountry = "NO";
    else if (isPolish) initialCountry = "PL";
    else if (isSwedish) initialCountry = "SE";
    else if (isDanish) initialCountry = "DK";
    else if (isUS) initialCountry = "US";
    else if (isUK) initialCountry = "GB";
    else if (isGerman) initialCountry = "DE";

    const sectionEl = document.createElement("div");
    sectionEl.className = "evidence-card";
    sectionEl.style.cssText = "border-left: 3px solid #38bdf8; margin-top: 16px; background: rgba(15, 23, 42, 0.7);";
    sectionEl.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
            <div class="evidence-title" style="color: #7dd3fc; font-size: 0.92rem; display: flex; align-items: center; gap: 6px;">
                <span class="flex items-center gap-1.5">${getUiIcon("globe", "w-4 h-4 text-sky-400")} CIVIL DIRECTORY &amp; TELECOM ROUTER</span>
            </div>
            <span class="badge-pill mono" style="font-size: 0.68rem; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);">
                ${isDeclassified ? 'RAW QUERIES UNLOCKED' : 'PROTECTED MODE'}
            </span>
        </div>
        <div style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 12px; line-height: 1.5;">
            Beyond Norway's 1881: Query authoritative public citizen directories, telephone white pages, and reverse caller ID across Europe, North America, and globally.
        </div>

        <!-- Country Switcher Tabs -->
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;" id="telecom-country-tabs">
            <button type="button" class="btn-tool ${initialCountry === 'NO' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('NO', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[NO] Norway (1881/GuleSider)</button>
            <button type="button" class="btn-tool ${initialCountry === 'SE' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('SE', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[SE] Sweden (Hitta/Ratsit)</button>
            <button type="button" class="btn-tool ${initialCountry === 'DK' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('DK', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[DK] Denmark (Krak)</button>
            <button type="button" class="btn-tool ${initialCountry === 'PL' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('PL', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[PL] Poland (Infonumer/Panorama)</button>
            <button type="button" class="btn-tool ${initialCountry === 'US' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('US', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[US] USA (NumLookup/TruePeople)</button>
            <button type="button" class="btn-tool ${initialCountry === 'GB' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('GB', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[GB] UK (WhoCalled/192)</button>
            <button type="button" class="btn-tool ${initialCountry === 'DE' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('DE', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[DE] Germany (DasTelefonbuch)</button>
            <button type="button" class="btn-tool ${initialCountry === 'GLOBAL' ? 'active-country-btn' : ''}" onclick="switchTelecomCountry('GLOBAL', '${escapeHtml(queryTarget)}', event)" style="font-size: 0.72rem; padding: 4px 8px;">[GLOBAL] International (Sync.me)</button>
        </div>

        <!-- Custom query input row -->
        <div style="display: flex; gap: 8px; margin-bottom: 12px;">
            <input type="text" id="telecom-custom-query" value="${escapeHtml(queryTarget)}" placeholder="Enter phone number (+48..., +47..., +1...) or citizen name" class="terminal-input" style="flex: 1; padding: 6px 10px; font-size: 0.8rem; background: var(--c-input); border: 1px solid var(--b-subtle); border-radius: 4px; color: var(--t-primary);">
            <button type="button" class="btn-tool" onclick="executeTelecomLookup()" style="color: #38bdf8; border-color: #0284c7; padding: 6px 14px; font-size: 0.78rem;">
                Dispatch Query &rarr;
            </button>
        </div>

        <!-- Directory Launchers Container -->
        <div id="telecom-directory-results" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;">
        </div>
    `;

    container.appendChild(sectionEl);
    switchTelecomCountry(initialCountry, queryTarget, null);
}

async function switchTelecomCountry(iso, query, ev) {
    const input = document.getElementById("telecom-custom-query");
    const activeQuery = input ? input.value.trim() : (query || "");
    const container = document.getElementById("telecom-directory-results");
    if (!container) return;

    // Highlight active country tab
    document.querySelectorAll("#telecom-country-tabs .btn-tool").forEach(btn => {
        btn.style.background = "";
        btn.style.color = "";
        btn.style.borderColor = "";
    });
    if (ev && ev.target && ev.target.classList.contains("btn-tool")) {
        ev.target.style.background = "rgba(56, 189, 248, 0.2)";
        ev.target.style.color = "#38bdf8";
        ev.target.style.borderColor = "#38bdf8";
    }

    container.innerHTML = `<div style="grid-column: 1 / -1; padding: 12px; color: #94a3b8; font-size: 0.78rem;">Fetching national directory endpoints for ${escapeHtml(iso)}...</div>`;

    try {
        const resp = await fetch(`/api/recon/telecom?query=${encodeURIComponent(activeQuery || "target")}&country=${encodeURIComponent(iso)}`);
        const data = await resp.json();
        renderTelecomDirectoryResults(data, container);
    } catch (e) {
        container.innerHTML = `<div style="grid-column: 1 / -1; color: #f87171; font-size: 0.78rem;">Error loading directory endpoints: ${escapeHtml(e.message)}</div>`;
    }
}

function renderTelecomDirectoryResults(data, container) {
    if (!container) return;
    const dirs = data.directories || [];
    const prof = data.telecom_profile || {};

    let html = "";
    if (prof.is_valid && prof.e164) {
        html += `
            <div style="grid-column: 1 / -1; padding: 8px 12px; background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; border-radius: 4px; font-size: 0.78rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;">
                <div>
                    <strong style="color: var(--t-primary);">E.164 Identity:</strong> <code style="color: #38bdf8;">${escapeHtml(prof.e164)}</code> | 
                    <strong>Line Type:</strong> <span style="color: var(--t-secondary);">${escapeHtml(prof.line_type)}</span> | 
                    <strong>Country:</strong> <span style="color: #a7f3d0;">${escapeHtml(prof.country_name)} (${escapeHtml(prof.iso)})</span>
                </div>
            </div>
        `;
    }

    dirs.slice(0, 8).forEach(d => {
        html += `
            <div class="evidence-card" style="margin: 0; padding: 10px 12px; background: var(--c-elevated); border: 1px solid var(--b-hairline); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 700; font-size: 0.82rem; color: var(--t-primary);">${escapeHtml(d.name)}</span>
                        <span class="mono" style="font-size: 0.65rem; padding: 2px 6px; background: var(--c-surface); color: var(--t-secondary); border: 1px solid var(--b-hairline); border-radius: 3px;">${escapeHtml(d.badge)}</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8; line-height: 1.4; margin-bottom: 8px;">
                        ${escapeHtml(d.description)}
                    </div>
                </div>
                <div>
                    <a href="${escapeHtml(d.url)}" target="_blank" rel="noopener noreferrer" class="btn-tool" style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.7rem; padding: 3px 10px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none;">
                        Launch Registry &nearr;
                    </a>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

window.renderMultiCountryTelecomSection = renderMultiCountryTelecomSection;
window.switchTelecomCountry = switchTelecomCountry;
window.executeTelecomLookup = function() {
    const input = document.getElementById("telecom-custom-query");
    const q = input ? input.value.trim() : "";
    switchTelecomCountry("GLOBAL", q, null);
};

/* ==========================================================================
   Reverse Phone Number Intelligence Engine & Modal Controllers
   ========================================================================== */

function openReversePhoneModal(presetPhone = "") {
    if (window.sfx) window.sfx.playSelect();
    const modal = document.getElementById("reverse-phone-modal");
    const input = document.getElementById("modal-phone-input");
    if (modal) modal.style.display = "flex";
    if (input) {
        if (presetPhone) {
            input.value = presetPhone;
            executeModalReversePhoneSearch();
        } else if (!input.value.trim() && currentInvestigationData) {
            const emp = currentInvestigationData.employee || {};
            const p = emp.phone_number || emp.phone || "";
            if (p) {
                input.value = p;
                executeModalReversePhoneSearch();
            }
        }
        input.focus();
    }
}

function closeReversePhoneModal() {
    const modal = document.getElementById("reverse-phone-modal");
    if (modal) modal.style.display = "none";
}

function handleReversePhoneModalBackdropClick(event) {
    if (event.target && event.target.id === "reverse-phone-modal") {
        closeReversePhoneModal();
    }
}

function setModalPhonePreset(val) {
    const input = document.getElementById("modal-phone-input");
    if (input) input.value = val;
    executeModalReversePhoneSearch();
}

async function executeModalReversePhoneSearch() {
    const input = document.getElementById("modal-phone-input");
    const status = document.getElementById("modal-phone-status");
    const results = document.getElementById("modal-phone-results");
    if (!input) return;

    const query = input.value.trim();
    if (!query) {
        if (status) {
            status.style.display = "block";
            status.style.background = "rgba(239, 68, 68, 0.1)";
            status.style.color = "#f87171";
            status.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            status.innerText = "Please enter a target phone number.";
        }
        return;
    }

    if (status) {
        status.style.display = "block";
        status.style.background = "rgba(16, 185, 129, 0.08)";
        status.style.color = "#34d399";
        status.style.border = "1px solid rgba(16, 185, 129, 0.3)";
        status.innerText = `Analyzing telecom carrier, E.164 normalization, and national registries for ${query}...`;
    }
    if (results) {
        results.style.display = "none";
        results.innerHTML = "";
    }

    try {
        const resp = await fetch(`/api/recon/reverse-phone?phone=${encodeURIComponent(query)}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || "Lookup request failed");
        }
        const data = await resp.json();
        if (status) status.style.display = "none";
        if (results) {
            results.style.display = "block";
            renderReversePhoneDossier(data, results);
        }
    } catch (e) {
        if (status) {
            status.style.display = "block";
            status.style.background = "rgba(239, 68, 68, 0.1)";
            status.style.color = "#f87171";
            status.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            status.innerText = `Error: ${e.message}`;
        }
    }
}

function renderReversePhoneDossier(d, container) {
    if (!container || !d) return;

    const safeE164 = escapeHtml(d.e164 || d.raw_query || "");
    const safeCarrier = escapeHtml(d.carrier || "Standard Cellular Network");
    const safeType = escapeHtml(d.line_type || "Mobile / Cellular");
    const safeCountry = escapeHtml(d.country || "International");
    const safeIso = escapeHtml(d.country_iso || "GLOBAL");
    const safeGeo = escapeHtml(d.geographic_location || safeCountry);
    const msgs = d.messaging_shortcuts || {};
    const dirs = d.directories || [];
    const correlations = d.database_correlations || [];

    let html = `
        <div style="background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px; padding: 14px; margin-top: 10px;">
            <!-- Header Grid: Identity & Telecom Matrix -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--b-hairline);">
                <div>
                    <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider">E.164 IDENTITY</div>
                    <div class="mono text-base font-bold text-emerald-400">${safeE164}</div>
                    <div class="mono text-[11px] text-zinc-400">${escapeHtml(d.international_format || safeE164)}</div>
                </div>
                <div>
                    <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider">LINE TYPE</div>
                    <div class="mono text-sm font-semibold text-zinc-200">${safeType}</div>
                    <div class="mono text-[11px] text-zinc-400">Validity: ${d.is_valid ? '<span class="text-emerald-400 font-bold">VERIFIED VALID</span>' : '<span class="text-amber-400">UNCONFIRMED</span>'}</div>
                </div>
                <div>
                    <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider">CARRIER / NETWORK</div>
                    <div class="mono text-sm font-semibold text-sky-400">${safeCarrier}</div>
                    <div class="mono text-[11px] text-zinc-400">${safeGeo}</div>
                </div>
                <div>
                    <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider">JURISDICTION</div>
                    <div class="mono text-sm font-semibold text-zinc-200">${safeCountry} [${safeIso}]</div>
                    <div class="mono text-[11px] text-zinc-400">Dialing Prefix: ${escapeHtml(d.country_prefix || "")}</div>
                </div>
            </div>

            <!-- Direct Messaging Links -->
            <div style="margin-bottom: 14px;">
                <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider mb-2">DIRECT MESSAGING &amp; CHAT PLATFORM ACTIONS:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                    ${msgs.whatsapp ? `
                        <a href="${escapeHtml(msgs.whatsapp)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1.5 px-3" style="color: #22c55e; border-color: rgba(34, 197, 94, 0.4); text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                            <span>WhatsApp wa.me</span> &nearr;
                        </a>
                    ` : ''}
                    ${msgs.telegram ? `
                        <a href="${escapeHtml(msgs.telegram)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1.5 px-3" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                            <span>Telegram Direct</span> &nearr;
                        </a>
                    ` : ''}
                    ${msgs.viber ? `
                        <a href="${escapeHtml(msgs.viber)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1.5 px-3" style="color: #a855f7; border-color: rgba(168, 85, 247, 0.4); text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                            <span>Viber Chat</span> &nearr;
                        </a>
                    ` : ''}
                    <button type="button" class="btn-tool text-xs py-1.5 px-3" onclick="navigator.clipboard.writeText('${safeE164}'); showToast('E.164 copied to clipboard', 'success');">
                        Copy E.164
                    </button>
                </div>
            </div>
    `;

    // Database correlations
    if (correlations.length > 0) {
        html += `
            <div style="margin-bottom: 14px; background: rgba(244, 63, 94, 0.06); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: 6px; padding: 10px 12px;">
                <div class="mono text-xs font-bold text-rose-400 mb-1.5 uppercase">LOCAL DATABASE CORRELATION MATCHES (${correlations.length}):</div>
                <div style="display: flex; flex-direction: column; gap: 6px;">
        `;
        correlations.forEach(c => {
            html += `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;" class="mono">
                    <span style="color: var(--t-primary); font-weight: 600;">${escapeHtml(c.full_name || 'Unknown')} (${escapeHtml(c.corporate_email || '')})</span>
                    <button type="button" class="btn-tool text-[10px] py-0.5 px-2" onclick="closeReversePhoneModal(); loadExampleTarget('${escapeHtml(c.corporate_email)}')">Inspect Target &rarr;</button>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    // Authoritative National Directories
    if (dirs.length > 0) {
        html += `
            <div>
                <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider mb-2">AUTHORITATIVE NATIONAL DIRECTORIES &amp; CALLER ID DISPATCHERS:</div>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px;">
        `;
        dirs.forEach(d => {
            html += `
                <div class="evidence-card" style="margin: 0; padding: 10px 12px; background: var(--c-elevated); border: 1px solid var(--b-hairline); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span class="mono font-bold text-xs" style="color: var(--t-primary);">${escapeHtml(d.name)}</span>
                            <span class="mono text-[10px] px-1 py-0.5 rounded" style="background: var(--c-surface); border: 1px solid var(--b-hairline); color: var(--t-secondary);">${escapeHtml(d.badge)}</span>
                        </div>
                        <div style="font-size: 0.72rem; color: #94a3b8; line-height: 1.4; margin-bottom: 8px;">
                            ${escapeHtml(d.description)}
                        </div>
                    </div>
                    <div>
                        <a href="${escapeHtml(d.url)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[11px] py-1 px-2.5" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">
                            Launch Directory &nearr;
                        </a>
                    </div>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    html += `</div>`;
    container.innerHTML = html;
}

function renderTelecomTab(data) {
    const container = document.getElementById("tab-telecom-content");
    if (!container) return;

    const emp = (data && data.employee) ? data.employee : {};
    const pivots = (data && data.pivots) ? data.pivots : [];
    const directPhone = emp.phone_number || emp.phone || "";
    
    // Extract any phone numbers from pivots
    const phonePivots = pivots.filter(p => p.pivot_type === "PHONE" || p.pivot_type === "PHONE_NUMBER");
    const uniquePhones = new Set();
    if (directPhone) uniquePhones.add(directPhone);
    phonePivots.forEach(p => {
        if (p.pivot_value) uniquePhones.add(p.pivot_value);
    });

    const phoneList = Array.from(uniquePhones);

    let html = `
        <div class="evidence-card" style="border-left: 3px solid #10b981; margin-bottom: 14px; background: rgba(16, 185, 129, 0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div class="evidence-title flex items-center gap-1.5" style="color: #34d399; font-size: 0.95rem;">
                    ${getUiIcon("globe", "w-4 h-4 text-emerald-400")} REVERSE PHONE NUMBER &amp; TELECOM INTELLIGENCE
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span class="badge-pill mono" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3);">
                        ${phoneList.length} TELECOM VECTOR${phoneList.length === 1 ? '' : 'S'}
                    </span>
                    <button type="button" class="btn-tool" onclick="openReversePhoneModal()" style="color: #34d399; border-color: rgba(16, 185, 129, 0.4); font-size: 0.72rem; padding: 3px 8px;">
                        [OPEN REVERSE LOOKUP TOOL]
                    </button>
                </div>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; line-height: 1.5; margin-bottom: 12px;">
                E.164 normalization, carrier identification, line type classification (Mobile / Landline / VoIP), direct messaging platform pivots (WhatsApp, Telegram), and dispatch to authoritative national citizen directories.
            </div>

            <!-- Ad-hoc Reverse Phone Search Form -->
            <div style="display: flex; gap: 8px; background: var(--c-elevated); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--b-hairline); align-items: center; margin-bottom: 10px;">
                <span class="mono text-[11px] text-zinc-400" style="white-space: nowrap;">LOOKUP PHONE:</span>
                <input type="text" id="tab-custom-phone-input" placeholder="e.g. +4791234567, 0701234567, +31612345678, +14155552671" class="terminal-input" style="flex: 1; padding: 5px 8px; font-size: 0.78rem; background: var(--c-input); border: 1px solid var(--b-subtle); border-radius: 4px; color: var(--t-primary);" onkeydown="if(event.key==='Enter') executeTabReversePhoneSearch()">
                <button type="button" class="btn-tool" onclick="executeTabReversePhoneSearch()" style="color: #10b981; border-color: #059669; font-size: 0.74rem; padding: 5px 10px;">
                    Analyze Telecom &rarr;
                </button>
            </div>
            <div id="tab-reverse-phone-status" style="display: none; padding: 6px 10px; border-radius: 4px; font-size: 0.75rem; margin-bottom: 8px;" class="mono"></div>
            <div id="tab-reverse-phone-results" style="display: none; margin-bottom: 12px;"></div>
        </div>
    `;

    // Detected Target Phones Section
    if (phoneList.length > 0) {
        html += `
            <div style="margin-bottom: 16px;">
                <div class="mono text-xs font-bold text-slate-800 dark:text-zinc-200 uppercase tracking-wide mb-2">
                    IDENTIFIED TARGET PHONE VECTORS (${phoneList.length}):
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px;">
        `;

        phoneList.forEach(ph => {
            const safePhone = escapeHtml(ph);
            html += `
                <div class="evidence-card" style="margin: 0; padding: 12px; background: var(--c-elevated); border: 1px solid var(--b-hairline); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <span class="mono font-bold text-sm text-emerald-400">${safePhone}</span>
                            <span class="badge-pill mono" style="font-size: 0.65rem; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3);">
                                TARGET PHONE
                            </span>
                        </div>
                        <div class="mono text-[11px] text-zinc-400 mb-3">
                            Associated with target ${escapeHtml(emp.full_name || currentEmail)}
                        </div>
                    </div>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        <button type="button" class="btn-tool text-[10px] py-1 px-2.5" onclick="executeTabReversePhoneDirect('${safePhone}')" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4);">
                            Full Reverse Scan &rarr;
                        </button>
                        <button type="button" class="btn-tool text-[10px] py-1 px-2.5" onclick="openReversePhoneModal('${safePhone}')">
                            Open Modal
                        </button>
                    </div>
                </div>
            `;
        });

        html += `</div></div>`;
    }

    container.innerHTML = html;

    // Embed Multi-Country National Telecom Router
    const subContainer = document.createElement("div");
    subContainer.id = "tab-telecom-router-box";
    container.appendChild(subContainer);

    renderMultiCountryTelecomSection(data, subContainer);
}

async function executeTabReversePhoneSearch() {
    const input = document.getElementById("tab-custom-phone-input");
    const status = document.getElementById("tab-reverse-phone-status");
    const results = document.getElementById("tab-reverse-phone-results");
    if (!input) return;

    const query = input.value.trim();
    if (!query) {
        if (status) {
            status.style.display = "block";
            status.style.background = "rgba(239, 68, 68, 0.1)";
            status.style.color = "#f87171";
            status.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            status.innerText = "Please enter a target phone number.";
        }
        return;
    }

    if (status) {
        status.style.display = "block";
        status.style.background = "rgba(16, 185, 129, 0.08)";
        status.style.color = "#34d399";
        status.style.border = "1px solid rgba(16, 185, 129, 0.3)";
        status.innerText = `Analyzing telecom carrier, E.164 normalization, and national registries for ${query}...`;
    }
    if (results) {
        results.style.display = "none";
        results.innerHTML = "";
    }

    try {
        const resp = await fetch(`/api/recon/reverse-phone?phone=${encodeURIComponent(query)}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || "Lookup request failed");
        }
        const data = await resp.json();
        if (status) status.style.display = "none";
        if (results) {
            results.style.display = "block";
            renderReversePhoneDossier(data, results);
        }
    } catch (e) {
        if (status) {
            status.style.display = "block";
            status.style.background = "rgba(239, 68, 68, 0.1)";
            status.style.color = "#f87171";
            status.style.border = "1px solid rgba(239, 68, 68, 0.3)";
            status.innerText = `Error: ${e.message}`;
        }
    }
}

function executeTabReversePhoneDirect(phone) {
    const input = document.getElementById("tab-custom-phone-input");
    if (input) input.value = phone;
    executeTabReversePhoneSearch();
}

window.openReversePhoneModal = openReversePhoneModal;
window.closeReversePhoneModal = closeReversePhoneModal;
window.handleReversePhoneModalBackdropClick = handleReversePhoneModalBackdropClick;
window.setModalPhonePreset = setModalPhonePreset;
window.executeModalReversePhoneSearch = executeModalReversePhoneSearch;
window.renderReversePhoneDossier = renderReversePhoneDossier;
window.renderTelecomTab = renderTelecomTab;
window.executeTabReversePhoneSearch = executeTabReversePhoneSearch;
window.executeTabReversePhoneDirect = executeTabReversePhoneDirect;

/* ==========================================================================
   Image Correlation & Reverse Visual Search Engine Controllers
   ========================================================================== */

function openImageCorrelationModal() {
    if (window.sfx) window.sfx.playSelect();
    const modal = document.getElementById("image-correlation-modal");
    if (!modal) return;
    modal.style.display = "flex";

    // Populate harvested avatars in modal
    const grid = document.getElementById("modal-avatars-grid");
    const countBadge = document.getElementById("modal-avatar-count");
    const images = (currentInvestigationData && currentInvestigationData.images) ? currentInvestigationData.images : [];

    if (countBadge) {
        countBadge.innerText = `${images.length} AVATAR${images.length === 1 ? '' : 'S'}`;
    }

    if (grid) {
        if (images.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; padding: 20px; text-align: center; color: #94a3b8; font-size: 0.8rem;" class="mono">
                    No avatars harvested for current target identity. Paste an image URL above to generate 1-click reverse search queries.
                </div>
            `;
        } else {
            let html = "";
            images.forEach(img => {
                const imgUrl = img.image_url || img.thumbnail_url || "";
                const safeUrl = escapeHtml(imgUrl);
                const platform = escapeHtml(img.platform || "Web Asset");
                const label = escapeHtml(img.label || img.source || "Target Avatar");
                const revLinks = img.reverse_search_links || {};

                html += `
                    <div style="background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px; padding: 10px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span class="mono text-xs font-bold text-purple-400">${platform}</span>
                                <span class="mono text-[10px] px-1 py-0.5 rounded" style="background: var(--c-canvas); border: 1px solid var(--b-hairline); color: var(--t-secondary);">${escapeHtml(img.badge || "PUBLIC")}</span>
                            </div>
                            <div style="text-align: center; margin-bottom: 8px; background: var(--c-canvas); border-radius: 4px; padding: 6px;">
                                <img src="${safeUrl}" alt="${platform}" style="max-height: 120px; max-width: 100%; border-radius: 4px; object-fit: contain; margin: 0 auto; display: block;" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'80\\' height=\\'80\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'%2364748b\\' stroke-width=\\'1.5\\'%3E%3Crect x=\\'3\\' y=\\'3\\' width=\\'18\\' height=\\'18\\' rx=\\'2\\'/%3E%3Ccircle cx=\\'8.5\\' cy=\\'8.5\\' r=\\'1.5\\'/%3E%3Cpolyline points=\\'21 15 16 10 5 21\\'/%3E%3C/svg%3E';">
                            </div>
                            <div class="mono text-[11px] font-semibold text-zinc-300 mb-1" style="word-break: break-all;">${label}</div>
                        </div>
                        <div>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px;">
                                ${revLinks.google_lens ? `<a href="${escapeHtml(revLinks.google_lens)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #38bdf8; text-decoration: none;">Lens &nearr;</a>` : ''}
                                ${revLinks.yandex_images ? `<a href="${escapeHtml(revLinks.yandex_images)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #fb923c; text-decoration: none;">Yandex &nearr;</a>` : ''}
                                ${revLinks.tineye ? `<a href="${escapeHtml(revLinks.tineye)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #34d399; text-decoration: none;">TinEye &nearr;</a>` : ''}
                                ${revLinks.bing_visual ? `<a href="${escapeHtml(revLinks.bing_visual)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #818cf8; text-decoration: none;">Bing &nearr;</a>` : ''}
                                ${revLinks.pimeyes ? `<a href="${escapeHtml(revLinks.pimeyes)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #f43f5e; text-decoration: none;">PimEyes &nearr;</a>` : ''}
                            </div>
                            <div style="display: flex; gap: 4px; border-top: 1px solid var(--b-hairline); padding-top: 6px;">
                                <button type="button" class="btn-tool text-[10px] flex-1 py-1" onclick="setupModalVisualCompare('A', '${safeUrl}', '${platform} - ${label}')">[COMPARE A]</button>
                                <button type="button" class="btn-tool text-[10px] flex-1 py-1" onclick="setupModalVisualCompare('B', '${safeUrl}', '${platform} - ${label}')">[COMPARE B]</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            grid.innerHTML = html;
        }
    }
}

function closeImageCorrelationModal() {
    const modal = document.getElementById("image-correlation-modal");
    if (modal) modal.style.display = "none";
}

function handleImageCorrelationModalBackdropClick(event) {
    if (event.target && event.target.id === "image-correlation-modal") {
        closeImageCorrelationModal();
    }
}

async function executeCustomImageReverseSearch() {
    const input = document.getElementById("modal-custom-img-input");
    const linksContainer = document.getElementById("modal-custom-img-links");
    if (!input || !linksContainer) return;

    const url = input.value.trim();
    if (!url) {
        showToast("Please enter an image URL.", "warning");
        return;
    }

    linksContainer.style.display = "flex";
    linksContainer.innerHTML = `<span class="mono text-xs text-purple-400">Generating query links for visual search engines...</span>`;

    try {
        const resp = await fetch("/api/recon/reverse-image-urls", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_url: url })
        });
        const data = await resp.json();
        const links = data.reverse_search_links || {};

        let html = "";
        if (links.google_lens) html += `<a href="${escapeHtml(links.google_lens)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none;">Google Lens &nearr;</a>`;
        if (links.yandex_images) html += `<a href="${escapeHtml(links.yandex_images)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #fb923c; border-color: rgba(251, 146, 60, 0.4); text-decoration: none;">Yandex Visual &nearr;</a>`;
        if (links.tineye) html += `<a href="${escapeHtml(links.tineye)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #34d399; border-color: rgba(52, 211, 153, 0.4); text-decoration: none;">TinEye &nearr;</a>`;
        if (links.bing_visual) html += `<a href="${escapeHtml(links.bing_visual)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #818cf8; border-color: rgba(129, 140, 248, 0.4); text-decoration: none;">Bing Visual &nearr;</a>`;
        if (links.pimeyes) html += `<a href="${escapeHtml(links.pimeyes)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #f43f5e; border-color: rgba(244, 63, 94, 0.4); text-decoration: none;">PimEyes &nearr;</a>`;

        linksContainer.innerHTML = html;
    } catch (e) {
        linksContainer.innerHTML = `<span class="mono text-xs text-rose-400">Error: ${escapeHtml(e.message)}</span>`;
    }
}

function setupModalVisualCompare(slot, imgUrl, label) {
    const sec = document.getElementById("modal-comparison-section");
    if (sec) sec.style.display = "block";

    if (slot === "A") {
        const imgA = document.getElementById("compare-img-a");
        const metaA = document.getElementById("compare-meta-a");
        if (imgA) imgA.src = imgUrl;
        if (metaA) metaA.innerText = label;
        showToast("Set as Base Image A", "info");
    } else {
        const imgB = document.getElementById("compare-img-b");
        const metaB = document.getElementById("compare-meta-b");
        if (imgB) imgB.src = imgUrl;
        if (metaB) metaB.innerText = label;
        showToast("Set as Candidate Image B", "info");
    }
}

function renderImageCorrelationTab(data) {
    const container = document.getElementById("tab-images-content");
    if (!container) return;

    const images = (data && data.images) ? data.images : [];
    const emp = (data && data.employee) ? data.employee : {};
    const email = emp.corporate_email || currentEmail || "";
    const name = emp.full_name || "";

    let html = `
        <div class="evidence-card" style="border-left: 3px solid #a855f7; margin-bottom: 14px; background: rgba(168, 85, 247, 0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div class="evidence-title flex items-center gap-1.5" style="color: #c084fc; font-size: 0.95rem;">
                    ${getUiIcon("user", "w-4 h-4 text-purple-400")} VISUAL IDENTITY &amp; AVATAR HARVESTING
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span class="badge-pill mono" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);">
                        ${images.length} HARVESTED AVATAR${images.length === 1 ? '' : 'S'}
                    </span>
                    <button type="button" class="btn-tool" onclick="openImageCorrelationModal()" style="color: #c084fc; border-color: rgba(168, 85, 247, 0.4); font-size: 0.72rem; padding: 3px 8px;">
                        [OPEN VISUAL WORKSPACE]
                    </button>
                </div>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; line-height: 1.5; margin-bottom: 12px;">
                Automated multi-platform avatar discovery across Gravatar (MD5 hash), GitHub Developer avatars, Duolingo, and verified web profiles. Launch 1-click reverse visual lookups across Google Lens, Yandex, TinEye, Bing Visual, and PimEyes.
            </div>

            <!-- Ad-hoc Reverse Lookup Bar -->
            <div style="display: flex; gap: 8px; background: var(--c-elevated); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--b-hairline); align-items: center; margin-bottom: 10px;">
                <span class="mono text-[11px] text-zinc-400" style="white-space: nowrap;">QUICK REVERSE LOOKUP:</span>
                <input type="text" id="tab-custom-img-input" placeholder="Paste any image URL (https://.../avatar.jpg)" class="terminal-input" style="flex: 1; padding: 5px 8px; font-size: 0.78rem; background: var(--c-input); border: 1px solid var(--b-subtle); border-radius: 4px; color: var(--t-primary);" onkeydown="if(event.key==='Enter') executeTabCustomImageReverseSearch()">
                <button type="button" class="btn-tool" onclick="executeTabCustomImageReverseSearch()" style="color: #a855f7; border-color: #9333ea; font-size: 0.74rem; padding: 5px 10px;">
                    Search Engines &rarr;
                </button>
            </div>
            <div id="tab-custom-img-engines" style="display: none; margin-bottom: 10px; flex-wrap: wrap; gap: 6px;"></div>
        </div>
    `;

    if (images.length === 0) {
        html += `
            <div class="evidence-card" style="border-left: 3px solid #64748b; padding: 20px; text-align: center;">
                <div class="mono text-xs text-zinc-400 mb-2">No public avatars automatically discovered for ${escapeHtml(email || 'target')}</div>
                <div class="text-xs text-zinc-500 mb-3">Target may use customized privacy settings or non-standard image hosts. Paste an image URL above to correlate manually, or re-run image probe.</div>
                <button type="button" class="btn-tool" onclick="refreshTargetImages('${escapeHtml(email)}', '${escapeHtml(name)}')" style="color: #38bdf8; border-color: #0284c7; font-size: 0.75rem; padding: 4px 12px; margin: 0 auto; display: inline-block;">
                    Re-Probe Image Profiles
                </button>
            </div>
        `;
    } else {
        html += `
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-bottom: 16px;">
        `;

        images.forEach((img) => {
            const revLinks = img.reverse_search_links || {};
            const imgUrl = img.image_url || img.thumbnail_url || "";
            const safeUrl = escapeHtml(imgUrl);
            const platform = escapeHtml(img.platform || "Web Asset");
            const label = escapeHtml(img.label || img.source || "Target Avatar");
            const badge = escapeHtml(img.badge || "PUBLIC");

            html += `
                <div class="evidence-card" style="margin: 0; padding: 12px; background: var(--c-elevated); border: 1px solid var(--b-hairline); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                            <span class="mono font-bold text-xs" style="color: #c084fc;">${platform}</span>
                            <span class="mono text-[10px] px-1.5 py-0.5 rounded" style="background: var(--c-surface); border: 1px solid var(--b-hairline); color: var(--t-secondary);">${badge}</span>
                        </div>
                        <div style="text-align: center; margin-bottom: 10px; background: var(--c-canvas); border-radius: 6px; padding: 8px; border: 1px solid var(--b-hairline);">
                            <img src="${safeUrl}" alt="${platform}" style="max-height: 140px; max-width: 100%; border-radius: 4px; object-fit: contain; margin: 0 auto; display: block;" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'80\\' height=\\'80\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'%2364748b\\' stroke-width=\\'1.5\\'%3E%3Crect x=\\'3\\' y=\\'3\\' width=\\'18\\' height=\\'18\\' rx=\\'2\\'/%3E%3Ccircle cx=\\'8.5\\' cy=\\'8.5\\' r=\\'1.5\\'/%3E%3Cpolyline points=\\'21 15 16 10 5 21\\'/%3E%3C/svg%3E';">
                        </div>
                        <div class="mono text-xs font-semibold text-zinc-300 dark:text-zinc-200" style="margin-bottom: 4px; word-break: break-all;">
                            ${label}
                        </div>
                        <div class="mono text-[11px] text-zinc-500 mb-3" style="word-break: break-all;">
                            ${escapeHtml(img.profile_url || imgUrl)}
                        </div>
                    </div>

                    <div>
                        <!-- Reverse Visual Pivot Links -->
                        <div style="margin-bottom: 8px;">
                            <div class="mono text-[10px] text-zinc-500 uppercase tracking-wider mb-1.5">REVERSE VISUAL ENGINES:</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                                ${revLinks.google_lens ? `<a href="${escapeHtml(revLinks.google_lens)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none;">Lens &nearr;</a>` : ''}
                                ${revLinks.yandex_images ? `<a href="${escapeHtml(revLinks.yandex_images)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #fb923c; border-color: rgba(251, 146, 60, 0.4); text-decoration: none;">Yandex &nearr;</a>` : ''}
                                ${revLinks.tineye ? `<a href="${escapeHtml(revLinks.tineye)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #34d399; border-color: rgba(52, 211, 153, 0.4); text-decoration: none;">TinEye &nearr;</a>` : ''}
                                ${revLinks.bing_visual ? `<a href="${escapeHtml(revLinks.bing_visual)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #818cf8; border-color: rgba(129, 140, 248, 0.4); text-decoration: none;">Bing &nearr;</a>` : ''}
                                ${revLinks.pimeyes ? `<a href="${escapeHtml(revLinks.pimeyes)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-[10px] py-0.5 px-2" style="color: #f43f5e; border-color: rgba(244, 63, 94, 0.4); text-decoration: none;">PimEyes &nearr;</a>` : ''}
                            </div>
                        </div>

                        <!-- Comparator Staging Buttons -->
                        <div style="display: flex; gap: 6px; border-top: 1px solid var(--b-hairline); padding-top: 8px;">
                            <button type="button" class="btn-tool text-[10px] flex-1 py-1" onclick="stageCompareImage('A', '${safeUrl}', '${platform} - ${label}')">
                                [SET AS BASE A]
                            </button>
                            <button type="button" class="btn-tool text-[10px] flex-1 py-1" onclick="stageCompareImage('B', '${safeUrl}', '${platform} - ${label}')">
                                [SET AS CANDIDATE B]
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div>`;

        // Side-by-side Visual Comparison Area inside tab
        html += `
            <div id="tab-visual-comparator" style="display: none; background: var(--c-surface); border: 1px solid var(--b-hairline); border-radius: 6px; padding: 14px; margin-top: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span class="mono text-xs font-bold text-purple-400 uppercase tracking-wide">SIDE-BY-SIDE VISUAL COMPARISON INSPECTOR:</span>
                    <button type="button" class="btn-tool text-[10px] py-0.5 px-2" onclick="clearTabComparator()">Reset Inspector</button>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                    <div style="border: 1px solid var(--b-hairline); border-radius: 6px; padding: 12px; text-align: center; background: var(--c-canvas);">
                        <div class="mono text-[11px] text-zinc-400 mb-2 font-bold">[IMAGE A // BASE IDENTITY]</div>
                        <img id="tab-cmp-img-a" src="" alt="Base Avatar" style="max-height: 200px; max-width: 100%; border-radius: 4px; margin: 0 auto; display: block; object-fit: contain;">
                        <div id="tab-cmp-label-a" class="mono text-xs text-zinc-300 mt-2 font-medium"></div>
                    </div>
                    <div style="border: 1px solid var(--b-hairline); border-radius: 6px; padding: 12px; text-align: center; background: var(--c-canvas);">
                        <div class="mono text-[11px] text-zinc-400 mb-2 font-bold">[IMAGE B // CORRELATED IDENTITY]</div>
                        <img id="tab-cmp-img-b" src="" alt="Correlated Avatar" style="max-height: 200px; max-width: 100%; border-radius: 4px; margin: 0 auto; display: block; object-fit: contain;">
                        <div id="tab-cmp-label-b" class="mono text-xs text-zinc-300 mt-2 font-medium"></div>
                    </div>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

async function executeTabCustomImageReverseSearch() {
    const input = document.getElementById("tab-custom-img-input");
    const container = document.getElementById("tab-custom-img-engines");
    if (!input || !container) return;

    const url = input.value.trim();
    if (!url) {
        showToast("Please enter an image URL.", "warning");
        return;
    }

    container.style.display = "flex";
    container.innerHTML = `<span class="mono text-xs text-purple-400">Generating visual engine links...</span>`;

    try {
        const resp = await fetch("/api/recon/reverse-image-urls", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_url: url })
        });
        const data = await resp.json();
        const links = data.reverse_search_links || {};

        let html = "";
        if (links.google_lens) html += `<a href="${escapeHtml(links.google_lens)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); text-decoration: none;">Google Lens &nearr;</a>`;
        if (links.yandex_images) html += `<a href="${escapeHtml(links.yandex_images)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #fb923c; border-color: rgba(251, 146, 60, 0.4); text-decoration: none;">Yandex Visual &nearr;</a>`;
        if (links.tineye) html += `<a href="${escapeHtml(links.tineye)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #34d399; border-color: rgba(52, 211, 153, 0.4); text-decoration: none;">TinEye &nearr;</a>`;
        if (links.bing_visual) html += `<a href="${escapeHtml(links.bing_visual)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #818cf8; border-color: rgba(129, 140, 248, 0.4); text-decoration: none;">Bing Visual &nearr;</a>`;
        if (links.pimeyes) html += `<a href="${escapeHtml(links.pimeyes)}" target="_blank" rel="noopener noreferrer" class="btn-tool text-xs py-1 px-3" style="color: #f43f5e; border-color: rgba(244, 63, 94, 0.4); text-decoration: none;">PimEyes &nearr;</a>`;

        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<span class="mono text-xs text-rose-400">Error: ${escapeHtml(e.message)}</span>`;
    }
}

function stageCompareImage(slot, url, label) {
    const comparator = document.getElementById("tab-visual-comparator");
    if (comparator) comparator.style.display = "block";

    if (slot === "A") {
        const img = document.getElementById("tab-cmp-img-a");
        const lbl = document.getElementById("tab-cmp-label-a");
        if (img) img.src = url;
        if (lbl) lbl.innerText = label;
        showToast("Set as Base Image A", "info");
    } else {
        const img = document.getElementById("tab-cmp-img-b");
        const lbl = document.getElementById("tab-cmp-label-b");
        if (img) img.src = url;
        if (lbl) lbl.innerText = label;
        showToast("Set as Candidate Image B", "info");
    }

    if (comparator) {
        comparator.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
}

function clearTabComparator() {
    const comparator = document.getElementById("tab-visual-comparator");
    if (comparator) comparator.style.display = "none";
    const imgA = document.getElementById("tab-cmp-img-a");
    const imgB = document.getElementById("tab-cmp-img-b");
    const lblA = document.getElementById("tab-cmp-label-a");
    const lblB = document.getElementById("tab-cmp-label-b");
    if (imgA) imgA.src = "";
    if (imgB) imgB.src = "";
    if (lblA) lblA.innerText = "";
    if (lblB) lblB.innerText = "";
}

async function refreshTargetImages(email, name) {
    showToast("Re-probing public avatar profiles...", "info");
    try {
        const resp = await fetch(`/api/recon/images?email=${encodeURIComponent(email)}&name=${encodeURIComponent(name)}`);
        const data = await resp.json();
        if (currentInvestigationData) {
            currentInvestigationData.images = data.images || [];
        }
        renderImageCorrelationTab({
            images: data.images || [],
            employee: { corporate_email: email, full_name: name }
        });
        showToast(`Discovered ${data.count || 0} avatar profiles`, "success");
    } catch (e) {
        showToast(`Error probing avatars: ${e.message}`, "error");
    }
}

window.openImageCorrelationModal = openImageCorrelationModal;
window.closeImageCorrelationModal = closeImageCorrelationModal;
window.handleImageCorrelationModalBackdropClick = handleImageCorrelationModalBackdropClick;
window.executeCustomImageReverseSearch = executeCustomImageReverseSearch;
window.setupModalVisualCompare = setupModalVisualCompare;
window.renderImageCorrelationTab = renderImageCorrelationTab;
window.executeTabCustomImageReverseSearch = executeTabCustomImageReverseSearch;
window.stageCompareImage = stageCompareImage;
window.clearTabComparator = clearTabComparator;
window.refreshTargetImages = refreshTargetImages;




window.filterPivotCategory = function(selectedCat) {
    document.querySelectorAll(".btn-pivot-filter").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-pivot-filter") === selectedCat);
    });
    document.querySelectorAll("#pivot-cards-list .pivot-entry-card").forEach(el => {
        const itemCat = el.getAttribute("data-pivot-cat");
        const matches = (selectedCat === "all") || 
                        (itemCat === selectedCat) || 
                        (selectedCat === "accounts" && (itemCat === "social" || itemCat === "gaming")) ||
                        ((selectedCat === "social" || selectedCat === "gaming") && itemCat === "accounts");
        if (matches) {
            el.style.display = "block";
        } else {
            el.style.display = "none";
        }
    });
    if (window.SoundManager) window.SoundManager.play("click");
};

/* ==========================================================================
 * 14. LINKEDIN INVESTIGATOR RECON BRIDGE (ZERO-CONFIG LOCAL AUTHENTICATION)
 * ========================================================================== */
let bridgeStatusData = null;
let bridgePollInterval = null;
let pendingInvestigationTarget = null;
let bridgeModalReason = "startup";

function routeInvestigationWithBridgeCheck(target) {
    if (!bridgeStatusData || !bridgeStatusData.authenticated) {
        openBridgeModal("scan_intercept", target);
        return;
    }
    executeInvestigation(target);
}

async function checkBridgeStatus(manualToast = false) {
    try {
        const resp = await fetch("/api/bridge/status");
        if (resp.ok) {
            bridgeStatusData = await resp.json();
            updateBridgeUI(bridgeStatusData, manualToast);
            return bridgeStatusData;
        }
    } catch (e) {
        console.warn("Could not query /api/bridge/status:", e);
        if (manualToast) {
            showToast("Failed to connect to bridge API: " + e.message, "error");
        }
    }
    return null;
}

function updateBridgeUI(status, manualToast = false) {
    if (!status) return;

    const modalBadge = document.getElementById("bridge-modal-status-badge");
    const detectedBrowser = document.getElementById("bridge-detected-browser");
    const noticeBox = document.getElementById("bridge-account-notice-box");
    const noticeTitle = document.getElementById("bridge-account-notice-title");
    const noticeDesc = document.getElementById("bridge-account-notice-desc");
    const launchBtn = document.getElementById("btn-launch-bridge-login");
    const launchBtnText = document.getElementById("btn-launch-bridge-text");

    if (detectedBrowser && status.browser_path) {
        const pLower = status.browser_path.toLowerCase();
        const name = pLower.includes("edge") ? "Microsoft Edge" : (pLower.includes("chrome") ? "Google Chrome" : "System Chromium");
        detectedBrowser.innerText = name;
    }

    // Google Sign-In or Registration Notice Detection
    if (noticeBox) {
        if (status.notice) {
            noticeBox.style.display = "block";
            if (noticeTitle) {
                noticeTitle.innerText = status.account_issue === "not_registered"
                    ? "Google Account Not Registered on LinkedIn"
                    : "Browser Verification Notice";
            }
            if (noticeDesc) {
                noticeDesc.innerText = status.notice;
            }
        } else {
            noticeBox.style.display = "none";
        }
    }

    if (status.authenticated) {
        if (modalBadge) {
            modalBadge.className = "font-mono text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-950 text-emerald-400 border border-emerald-800";
            modalBadge.innerText = "AUTHENTICATED & READY";
        }
        if (launchBtnText) {
            launchBtnText.innerText = "✓ LinkedIn Session Connected & Active";
        }
        if (noticeBox) {
            noticeBox.style.display = "none";
        }
        stopBridgePolling();
        if (manualToast) {
            showToast("LinkedIn Bridge authenticated! Automated scraping enabled.", "success");
        }
    } else {
        if (modalBadge) {
            modalBadge.className = "font-mono text-[10px] px-2 py-0.5 rounded font-bold bg-amber-950 text-amber-400 border border-amber-800";
            modalBadge.innerText = "NOT CONNECTED";
        }
        if (launchBtnText) {
            launchBtnText.innerText = "Log In Now (Sign in with Google or Password) →";
        }
    }
}

function openBridgeModal(reason = "startup", target = null) {
    const modal = document.getElementById("bridge-settings-modal");
    if (!modal) return;

    bridgeModalReason = reason;
    if (target) {
        pendingInvestigationTarget = target;
    }

    const badgeEl = document.getElementById("bridge-modal-alert-badge");
    const titleEl = document.getElementById("bridge-modal-title");
    const subtitleEl = document.getElementById("bridge-modal-subtitle");
    const headingEl = document.getElementById("bridge-modal-warning-heading");
    const textEl = document.getElementById("bridge-modal-warning-text");
    const proceedBtn = document.getElementById("btn-proceed-inaccurate");

    if (reason === "scan_intercept") {
        if (badgeEl) badgeEl.innerText = "[SCAN PAUSED: SESSION REQUIRED]";
        if (titleEl) titleEl.innerText = "Target Scan Intercepted: Inaccurate Results Warning";
        if (subtitleEl) subtitleEl.innerText = `Investigation of target "${target || ''}" paused`;
        if (headingEl) headingEl.innerText = "High Risk of Inaccurate & Missing Attribution";
        if (textEl) {
            textEl.innerHTML = `You are attempting to investigate <strong>${escapeHtml(target || '')}</strong> without an active LinkedIn session. Without it, current employer verification, job titles, and LinkedIn profile matching will be completely omitted or highly inaccurate. Do you want to log in now for 100% full intelligence?`;
        }
        if (proceedBtn) {
            proceedBtn.innerHTML = `<span>Proceed With Inaccurate Results Anyway &times;</span>`;
        }
    } else {
        if (badgeEl) badgeEl.innerText = "[SESSION REQUIRED]";
        if (titleEl) titleEl.innerText = "LinkedIn Reconnaissance Session Required";
        if (subtitleEl) subtitleEl.innerText = "Critical local browser capability for employer attribution & profile discovery";
        if (headingEl) headingEl.innerText = "Why is this required?";
        if (textEl) {
            textEl.innerHTML = `BreachSpillover uses a local browser session to automatically extract employer affiliations, job titles, and career footprints without paid API keys. <strong>If you do not log in, investigation results will be far more inaccurate</strong> and professional pivots will be missed.`;
        }
        if (proceedBtn) {
            proceedBtn.innerHTML = `<span>Proceed Without Login (Inaccurate Results) &times;</span>`;
        }
    }

    modal.style.display = "flex";
    checkBridgeStatus(false);
    if (window.SoundManager) window.SoundManager.play("alert");
}

function closeBridgeModal() {
    const modal = document.getElementById("bridge-settings-modal");
    if (modal) modal.style.display = "none";
    stopBridgePolling();
    if (window.SoundManager) window.SoundManager.play("click");
}

function chooseProceedWithoutLogin() {
    closeBridgeModal();
    showToast("⚠️ Proceeding in DEGRADED mode: Results will be far more inaccurate without LinkedIn.", "warning");
    if (pendingInvestigationTarget) {
        const t = pendingInvestigationTarget;
        pendingInvestigationTarget = null;
        executeInvestigation(t);
    }
}

function closeBridgeModalWithWarning() {
    chooseProceedWithoutLogin();
}

function handleBridgeBackdropClick(e) {
    if (e.target.id === "bridge-settings-modal") {
        chooseProceedWithoutLogin();
    }
}

async function startBridgeLoginFlow() {
    const pollingStatus = document.getElementById("bridge-login-polling-status");
    const launchBtn = document.getElementById("btn-launch-bridge-login");
    const noticeBox = document.getElementById("bridge-account-notice-box");

    if (noticeBox) noticeBox.style.display = "none";
    if (pollingStatus) {
        pollingStatus.style.display = "block";
        pollingStatus.innerHTML = `<span class="inline-block animate-spin mr-1">&#9696;</span> Launching dedicated local browser window...`;
    }
    if (launchBtn) launchBtn.disabled = true;

    try {
        const resp = await fetch("/api/bridge/login", { method: "POST" });
        const res = await resp.json();
        if (res.success) {
            showToast("Browser window opened! Log in with LinkedIn or Sign in with Google.", "info");
            if (pollingStatus) {
                pollingStatus.innerHTML = `<span class="inline-block animate-spin mr-1">&#9696;</span> Browser active. Sign in with Google or your credentials in the opened window...`;
            }
            startBridgePolling();
        } else {
            showToast("Error launching browser: " + (res.error || "Unknown error"), "error");
            if (pollingStatus) {
                pollingStatus.innerText = "Failed: " + (res.error || "Could not launch browser");
            }
        }
    } catch (e) {
        showToast("Error communicating with bridge: " + e.message, "error");
        if (pollingStatus) {
            pollingStatus.innerText = "Error: " + e.message;
        }
    } finally {
        if (launchBtn) launchBtn.disabled = false;
    }
}

function startBridgePolling() {
    stopBridgePolling();
    bridgePollInterval = setInterval(async () => {
        try {
            const resp = await fetch("/api/bridge/status");
            if (resp.ok) {
                const data = await resp.json();
                updateBridgeUI(data, false);
                if (data.authenticated) {
                    stopBridgePolling();
                    showToast("LinkedIn Bridge Connected! Automated career scraping is active.", "success");
                    if (window.SoundManager) window.SoundManager.play("victory");
                    setTimeout(() => {
                        closeBridgeModal();
                        if (pendingInvestigationTarget) {
                            const t = pendingInvestigationTarget;
                            pendingInvestigationTarget = null;
                            executeInvestigation(t);
                        }
                    }, 1200);
                }
            }
        } catch (e) {}
    }, 2000);
}

function stopBridgePolling() {
    if (bridgePollInterval) {
        clearInterval(bridgePollInterval);
        bridgePollInterval = null;
    }
}

function toggleManualCookieSection() {
    const sec = document.getElementById("manual-cookie-section");
    const caret = document.getElementById("manual-cookie-caret");
    if (!sec) return;
    const isHidden = sec.style.display === "none";
    sec.style.display = isHidden ? "block" : "none";
    if (caret) caret.innerHTML = isHidden ? "&uarr;" : "&darr;";
}

async function saveManualCookie() {
    const input = document.getElementById("manual-li-at-input");
    if (!input) return;
    const val = input.value.trim();
    try {
        const resp = await fetch("/api/bridge/cookie", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cookie: val })
        });
        const res = await resp.json();
        if (res.success) {
            showToast(res.message, "success");
            input.value = "";
            const st = await checkBridgeStatus(false);
            if (st && st.authenticated) {
                setTimeout(() => {
                    closeBridgeModal();
                    if (pendingInvestigationTarget) {
                        const t = pendingInvestigationTarget;
                        pendingInvestigationTarget = null;
                        executeInvestigation(t);
                    }
                }, 1000);
            }
        } else {
            showToast(res.detail || "Error saving cookie", "error");
        }
    } catch (e) {
        showToast("Network error: " + e.message, "error");
    }
}

window.routeInvestigationWithBridgeCheck = routeInvestigationWithBridgeCheck;
window.checkBridgeStatus = checkBridgeStatus;
window.updateBridgeUI = updateBridgeUI;
window.openBridgeModal = openBridgeModal;
window.closeBridgeModal = closeBridgeModal;
window.chooseProceedWithoutLogin = chooseProceedWithoutLogin;
window.closeBridgeModalWithWarning = closeBridgeModalWithWarning;
window.handleBridgeBackdropClick = handleBridgeBackdropClick;
window.startBridgeLoginFlow = startBridgeLoginFlow;
window.toggleManualCookieSection = toggleManualCookieSection;
window.saveManualCookie = saveManualCookie;

