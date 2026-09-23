import re

with open(r'frontend\static\js\app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Insert getUiIcon if not present
ui_icon_helper = """
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
        github: `<svg class="${cls}" viewBox="0 0 24 24" fill="currentColor"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"></path></svg>`
    };
    return icons[name] || "";
}
"""

if "function getUiIcon" not in text:
    norm_target = '    return s.split(":")[0].trim();\n}'
    text = text.replace(norm_target, norm_target + "\n" + ui_icon_helper)

# 2. Tooltips and eye buttons
text = text.replace('showActionTooltip("✓ Incident Report Copied");', 'showActionTooltip("Incident Report Copied");')
text = text.replace('showActionTooltip("✓ JSON Exported");', 'showActionTooltip("JSON Exported");')

text = text.replace('btnEye.innerText = "👁";', 'btnEye.innerText = "SHOW";')
text = text.replace('btn.innerText = "🙈";', 'btn.innerText = "HIDE";')
text = text.replace('btn.innerText = "👁";', 'btn.innerText = "SHOW";')

# 3. Passcode modal alerts and declassify badges
text = text.replace('err.innerHTML = "<span>✕ Please enter the master authorization key.</span>";', 'err.innerHTML = "<span>Please enter the master authorization key.</span>";')
text = text.replace('showToast("🔓 Master Security Key Accepted! Raw forensic intelligence declassified.", "success");', 'showToast("Master Security Key Accepted. Raw forensic intelligence declassified.", "success");')
text = text.replace('err.innerHTML = "<span>✕ Access Denied: Invalid Security Authorization Key.</span>";', 'err.innerHTML = "<span>Access Denied: Invalid Security Authorization Key.</span>";')
text = text.replace('showToast("🔒 Sensitive intelligence re-locked into protected privacy mode.", "info");', 'showToast("Sensitive intelligence returned to protected privacy mode.", "info");')

old_declass_badge = """function updateDeclassifyStatusBadge() {
    const btn = document.getElementById("btn-declassify-toggle");
    const icon = document.getElementById("declassify-status-icon");
    const text = document.getElementById("declassify-status-text");

    if (btn && icon && text) {
        if (isDeclassified) {
            btn.className = "btn-declassify-badge unlocked";
            icon.innerText = "🔓";
            text.innerText = "RAW INTEL UNLOCKED [LOCK PII]";
        } else {
            btn.className = "btn-declassify-badge";
            icon.innerText = "🔒";
            text.innerText = "SENSITIVE INTEL LOCKED [ENTER PASSCODE]";
        }
    }
}"""

new_declass_badge = """function updateDeclassifyStatusBadge() {
    const btn = document.getElementById("btn-declassify-toggle");
    const icon = document.getElementById("declassify-status-icon");
    const text = document.getElementById("declassify-status-text");

    if (btn && icon && text) {
        if (isDeclassified) {
            btn.className = "btn-declassify-badge unlocked";
            icon.innerHTML = getUiIcon("unlock", "w-3.5 h-3.5 text-emerald-400 inline mr-1.5");
            text.innerText = "RAW INTEL UNLOCKED [LOCK PII]";
        } else {
            btn.className = "btn-declassify-badge";
            icon.innerHTML = getUiIcon("lock", "w-3.5 h-3.5 text-amber-400 inline mr-1.5");
            text.innerText = "PROTECTED MODE [ENTER PASSCODE]";
        }
    }
}"""
text = text.replace(old_declass_badge, new_declass_badge)

# 4. Corporate Recon
text = text.replace(
    'if (titleEl) titleEl.innerText = `🏢 Corporate Reconnaissance: ${domain}`;',
    'if (titleEl) titleEl.innerHTML = `<span class="flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-sky-400")} Corporate Reconnaissance: ${escapeHtml(domain)}</span>`;'
)
text = text.replace(
    '<span class="evidence-title">✉️ Mail Routing & Anti-Spoofing Security (DoH Analysis)</span>',
    '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("mail", "w-3.5 h-3.5 text-sky-400")} Mail Routing &amp; Anti-Spoofing Security (DoH Analysis)</span>'
)
text = text.replace(
    '<span class="evidence-title">🌐 External Corporate Portals & Gateways (${subs.length})</span>',
    '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("globe", "w-3.5 h-3.5 text-purple-400")} External Corporate Portals &amp; Gateways (${subs.length})</span>'
)
text = text.replace(
    '<span class="evidence-title">👥 Indexed Corporate Staff & Compromised Accounts (${emps.length})</span>',
    '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("users", "w-3.5 h-3.5 text-rose-400")} Indexed Corporate Staff &amp; Compromised Accounts (${emps.length})</span>'
)
text = text.replace('<div style="font-size: 1.2rem;">✕ Domain Reconnaissance Failed</div>', '<div style="font-size: 1.2rem;">Domain Reconnaissance Failed</div>')

# 5. Batch & Lateral Movement
text = text.replace(
    '<div class="mono" style="font-size: 0.82rem; font-weight: 700; color: #f43f5e; margin-bottom: 8px;">\n                        🚨 CROSS-IDENTITY SHARED BREACH OVERLAP (LATERAL MOVEMENT ATTACK SURFACE)\n                    </div>',
    '<div class="mono flex items-center gap-2" style="font-size: 0.82rem; font-weight: 700; color: #f43f5e; margin-bottom: 8px;">${getUiIcon("alert", "w-4 h-4 text-rose-400")} CROSS-IDENTITY SHARED BREACH OVERLAP (LATERAL MOVEMENT ATTACK SURFACE)</div>'
)
text = text.replace('<div style="font-size: 1.1rem;">✕ Group Batch Audit Failed</div>', '<div style="font-size: 1.1rem;">Group Batch Audit Failed</div>')

# 6. Domain verification badges
text = text.replace(
    'domainStatusBadge.innerText = v.is_valid ? `✓ MX Valid (${v.domain})` : "✕ Unresolvable";',
    'domainStatusBadge.innerText = v.is_valid ? `MX Valid (${v.domain})` : "Unresolvable";'
)
text = text.replace(
    "domBadge.innerHTML = `✉️ ${escapeHtml(prov)} [SPF: ${escapeHtml(ev.email_security.spf_status || 'OK')}]`;",
    "domBadge.innerHTML = `<span class=\"flex items-center gap-1\">${getUiIcon('mail', 'w-3 h-3 text-sky-400')} ${escapeHtml(prov)} [SPF: ${escapeHtml(ev.email_security.spf_status || 'OK')}]</span>`;"
)

# 7. Render Pivots Tab
text = text.replace(
    '<div class="evidence-title" style="color: #34d399;">🛡️ No Verified Private Pivots</div>',
    '<div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} No Correlated Private Pivots</div>'
)

# Replace candidate handles block in pivots tab
old_cand_box = """                                    <span style="font-size: 0.75rem; font-weight: 700; color: #fbbf24; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 0.35rem;">
                                        <span>🔎</span> PROBED CANDIDATE HANDLES FOR THIS ACCOUNT (${matchingCandidates.length})
                                    </span>
                                    <span style="font-size: 0.68rem; color: #94a3b8; font-style: italic;">Public handle masked by platform on email lookup</span>"""

new_cand_box = """                                    <span style="font-size: 0.75rem; font-weight: 700; color: #fbbf24; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 0.35rem;">
                                        ${getUiIcon("search", "w-3 h-3 text-amber-400")} CANDIDATE IDENTIFIERS (${matchingCandidates.length})
                                    </span>
                                    <span style="font-size: 0.68rem; color: #94a3b8;">Platform masks username on email lookup</span>"""
text = text.replace(old_cand_box, new_cand_box)

# Stem clean up
old_c_ctx = """let cCtx = c.context_note ? c.context_note.replace(/\\[URL:\\s*https?:\\/\\/[^\\]]+\\]/, '').replace(/\\[STATUS:\\s*SUSPECTED\\]\\s*/, '').replace(/\\[PLATFORM:\\s*[^\\]]+\\]\\s*/, '').trim() : \"\";"""
new_c_ctx = """let cCtx = c.context_note ? c.context_note.replace(/\\[URL:\\s*https?:\\/\\/[^\\]]+\\]/, '').replace(/\\[STATUS:\\s*SUSPECTED\\]\\s*/, '').replace(/\\[PLATFORM:\\s*[^\\]]+\\]\\s*/, '').trim() : \"\";
                                        if (cCtx.includes("Root stem derived from authenticated account login")) {
                                            cCtx = cCtx.replace("Root stem derived from authenticated account login", "Stem match:");
                                        }"""
text = text.replace(old_c_ctx, new_c_ctx)

# Platform card header in pivots
old_piv_card = """                    pivotsContainer.innerHTML += `
                        <div class="evidence-card" style="border-left: 3px solid ${isDevProfile ? '#38bdf8' : (isAccountPresenceOnly ? '#a855f7' : '#38bdf8')};">
                            <div class="evidence-header">
                                <span class="evidence-title">🌐 ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="${isDevProfile ? 'background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8;' : (isAccountPresenceOnly ? 'background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);' : 'background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);')}">${isDevProfile ? 'VERIFIED DEVELOPER ACCOUNT' : (isAccountPresenceOnly ? 'EMAIL REGISTRATION VERIFIED' : 'LIVE OSINT PROFILE')}</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Intelligence Signal:</strong> ${escapeHtml(cleanContext || (isAccountPresenceOnly ? 'Account registered with target email address' : 'Public profile identified via verified corroboration'))}</div>"""

new_piv_card = """                    let cardIcon = isDevProfile ? getUiIcon('github', 'w-4 h-4 text-sky-400') : getUiIcon('globe', 'w-4 h-4 text-purple-400');
                    let cardBorder = isDevProfile ? '#38bdf8' : (isAccountPresenceOnly ? '#a855f7' : '#38bdf8');
                    let tagStyle = isDevProfile ? 'background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8;' : (isAccountPresenceOnly ? 'background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);' : 'background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);');
                    let tagText = isDevProfile ? 'VERIFIED DEVELOPER ACCOUNT' : (isAccountPresenceOnly ? 'EMAIL REGISTRATION VERIFIED' : 'LIVE OSINT PROFILE');

                    pivotsContainer.innerHTML += `
                        <div class="evidence-card" style="border-left: 3px solid ${cardBorder};">
                            <div class="evidence-header">
                                <span class="evidence-title flex items-center gap-1.5">${cardIcon} ${escapeHtml(piv.pivot_value)}</span>
                                <span class="evidence-tag" style="${tagStyle}">${tagText}</span>
                            </div>
                            <div class="evidence-body">
                                <div><strong>Intelligence Signal:</strong> ${escapeHtml(cleanContext || (isAccountPresenceOnly ? 'Account registration confirmed on service' : 'Corroborated public footprint'))}</div>"""
text = text.replace(old_piv_card, new_piv_card)

# Masked lock line in pivots
old_mask_line = """                                    <div style="margin-top: 0.5rem; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap;">
                                        <span style="font-size: 0.76rem; color: #94a3b8; display: inline-flex; align-items: center; gap: 0.35rem;">
                                            <span style="color: #c084fc;">🔒</span> Public handle not disclosed by platform API
                                        </span>
                                        ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" style="color: #64748b; font-size: 0.74rem; text-decoration: underline;">Open Platform Portal &rarr;</a>` : ''}
                                    </div>"""

new_mask_line = """                                    <div style="margin-top: 0.5rem; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap;">
                                        <span style="font-size: 0.76rem; color: #94a3b8; display: inline-flex; align-items: center; gap: 0.35rem;">
                                            ${getUiIcon('lock', 'w-3 h-3 text-purple-400')} Handle obscured by platform API
                                        </span>
                                        ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" style="color: #64748b; font-size: 0.74rem; text-decoration: underline;">Platform Portal &rarr;</a>` : ''}
                                    </div>"""
text = text.replace(old_mask_line, new_mask_line)

# Dedicated FULL_NAME card before fallback
full_name_handler = """                // Full Name / Person Identity Discovered
                if (piv.pivot_type === "FULL_NAME" || piv.pivot_type === "PERSON_NAME") {
                    const rawVal = piv.pivot_value.replace(/^Full Name:\\s*/i, '').trim();
                    let cleanCtx = piv.context_note ? piv.context_note.replace(/\\[STATUS:\\s*VERIFIED\\]\\s*/g, '').trim() : '';
                    pivotsContainer.innerHTML += `
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
                    `;
                    return;
                }
"""

if 'if (piv.pivot_type === "FULL_NAME"' not in text:
    text = text.replace('if (piv.pivot_type === "OPENPGP_KEY") {', full_name_handler + '\n                if (piv.pivot_type === "OPENPGP_KEY") {')

# Other pivot cards
text = text.replace('<span class="evidence-title">🔑 OpenPGP Public Key Found</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("key", "w-4 h-4 text-emerald-400")} OpenPGP Public Key Found</span>')
text = text.replace('<span class="evidence-title">🎓 ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-blue-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('<span class="evidence-title">💼 ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-amber-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('<span class="evidence-title">🚀 ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("globe", "w-4 h-4 text-purple-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('<span class="evidence-title">⚡ ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("cpu", "w-4 h-4 text-cyan-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('<span class="evidence-title">🏢 ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("building", "w-4 h-4 text-amber-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('⚡ EmploLeaks Recon: Discovered via Certificate Transparency / DNS probing.', 'Recon Signal: Discovered via Certificate Transparency / DNS probing.')
text = text.replace('<span class="evidence-title">✉️ ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5">${getUiIcon("mail", "w-4 h-4 text-indigo-400")} ${escapeHtml(piv.pivot_value)}</span>')

text = text.replace('const labelBtn = isPhone ? "[🔒 Unlock Phone Number]" : "[🔒 Unlock Secondary Email]";', 'const labelBtn = isPhone ? "[Unlock Phone Number]" : "[Unlock Secondary Email]";')
text = text.replace('🔒 <strong>Correlated Telecom Vector (${escapeHtml(piv.pivot_type)})</strong> — Protected by Master Security Key.', '${getUiIcon("lock", "w-3 h-3 text-cyan-400 inline mr-1")} <strong>Correlated Telecom Vector (${escapeHtml(piv.pivot_type)})</strong> — Protected by Master Security Key.')
text = text.replace('💬 WhatsApp Direct &rarr;', 'Message WhatsApp &rarr;')

# 8. Suspected tab
text = text.replace('<div class="evidence-title" style="color: #34d399;">🛡️ Zero Suspected False Positives</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} Clean Attribution Ledger</div>')
text = text.replace('<span style="font-size: 1.2rem;">🔎</span>', '${getUiIcon("search", "w-4 h-4 text-amber-400")}')
text = text.replace('🎯 CANDIDATES ON CONFIRMED EMAIL PLATFORMS', 'CANDIDATES ON CONFIRMED EMAIL PLATFORMS')
text = text.replace('<span class="evidence-title" style="color: #38bdf8;">🔎 ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5" style="color: #38bdf8;">${getUiIcon("search", "w-3.5 h-3.5 text-sky-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('<span style="color: #38bdf8;">ℹ️</span>', '${getUiIcon("alert", "w-3 h-3 text-sky-400")}')
text = text.replace('🎲 SPECULATIVE CANDIDATES ON UNCONFIRMED SERVICES', 'SPECULATIVE CANDIDATES ON UNCONFIRMED SERVICES')
text = text.replace('<span class="evidence-title" style="color: #fbbf24;">🔎 ${escapeHtml(piv.pivot_value)}</span>', '<span class="evidence-title flex items-center gap-1.5" style="color: #fbbf24;">${getUiIcon("search", "w-3.5 h-3.5 text-amber-400")} ${escapeHtml(piv.pivot_value)}</span>')
text = text.replace('<span style="color: #f59e0b;">⚠️</span>', '${getUiIcon("alert", "w-3 h-3 text-amber-400")}')

# 9. Physical Footprint & Relatives
text = text.replace('<div class="evidence-title" style="color: #34d399;">🛡️ Physical Footprint Protected</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} Physical Footprint Protected</div>')
text = text.replace('🔒 <strong>Physical Location Coordinate Found</strong>', '${getUiIcon("lock", "w-3 h-3 text-emerald-400 inline mr-1")} <strong>Physical Location Coordinate Found</strong>')
text = text.replace('[🔒 Unlock Location]', '[Unlock Location]')
text = text.replace('🔓 <strong>Declassified Location Asset</strong>', '${getUiIcon("unlock", "w-3 h-3 text-emerald-400 inline mr-1")} <strong>Declassified Location Asset</strong>')
text = text.replace("<span class=\"evidence-title\">📍 ${isDeclassified", "<span class=\"evidence-title flex items-center gap-1.5\">${getUiIcon('mapPin', 'w-3.5 h-3.5 text-emerald-400')} ${isDeclassified")
text = text.replace('🔒 <strong>Household Cohabitant Identified', '${getUiIcon("lock", "w-3 h-3 text-pink-400 inline mr-1")} <strong>Household Cohabitant Identified')
text = text.replace('[🔒 Unlock Contact Name]', '[Unlock Contact Name]')
text = text.replace('🔓 <strong>Declassified Family / Cohabitant Profile</strong>', '${getUiIcon("unlock", "w-3 h-3 text-emerald-400 inline mr-1")} <strong>Declassified Family / Cohabitant Profile</strong>')
text = text.replace("<span class=\"evidence-title\">👥 Household Contact:", "<span class=\"evidence-title flex items-center gap-1.5\">${getUiIcon('users', 'w-3.5 h-3.5 text-pink-400')} Household Contact:")

# 10. Compounding and Timeline
text = text.replace('<span>⚡ CROSS-VECTOR COMPOUNDING ATTACK SCENARIOS</span>', '<span>CROSS-VECTOR COMPOUNDING ATTACK SCENARIOS</span>')
text = text.replace('<div class="evidence-title" style="color: #34d399;">🛡️ No Adversary Exploitation Vectors</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} No Adversary Exploitation Vectors</div>')
text = text.replace('<div class="evidence-title" style="color: #34d399;">🛡️ Identity Untargeted</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} Identity Untargeted</div>')

text = text.replace('let iconGlyph = "📌";', 'let iconGlyph = "";')
text = text.replace('iconGlyph = "🚨";', 'iconGlyph = "";')
text = text.replace('iconGlyph = "🎓";', 'iconGlyph = "";')
text = text.replace('iconGlyph = "💼";', 'iconGlyph = "";')
text = text.replace('iconGlyph = "🚀";', 'iconGlyph = "";')
text = text.replace("[${iconGlyph} ${escapeHtml(item.type || 'Event')}]", "[${escapeHtml(item.type || 'EVENT').toUpperCase()}]")

# 11. Dorks & Hash Resolution
text = text.replace('<div class="evidence-title" style="color: #a5b4fc;">🌐 OSINT Dorking Engine</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #a5b4fc;">${getUiIcon("globe", "w-4 h-4 text-indigo-400")} OSINT Query Pivot Links</div>')
text = text.replace('btnLabel = "🚀 Open LinkedIn Dossier &nearr;";', 'btnLabel = "Open LinkedIn Dossier &nearr;";')
text = text.replace('btnLabel = "📷 Search Face Recon &nearr;";', 'btnLabel = "Search Face Recon &nearr;";')
text = text.replace('btnLabel = "🇳🇴 Query 1881.no Registry &nearr;";', 'btnLabel = "Query 1881.no Registry &nearr;";')
text = text.replace('btnLabel = "🏢 Search Proff.no &nearr;";', 'btnLabel = "Search Proff.no &nearr;";')

text = text.replace('<span class="mono" style="font-size: 0.82rem; font-weight: 700; color: #38bdf8;">🌐 OPEN WEB IDENTITY &amp; ROSTER RECONNAISSANCE</span>', '<span class="mono flex items-center gap-1.5" style="font-size: 0.82rem; font-weight: 700; color: #38bdf8;">${getUiIcon("globe", "w-3.5 h-3.5 text-sky-400")} OPEN WEB IDENTITY RECONNAISSANCE</span>')
text = text.replace('<span class="mono" style="font-size: 0.82rem; font-weight: 700; color: #c084fc;">🕵️ EXFILTRATED DATA &amp; DARK WEB ARCHIVES</span>', '<span class="mono flex items-center gap-1.5" style="font-size: 0.82rem; font-weight: 700; color: #c084fc;">${getUiIcon("search", "w-3.5 h-3.5 text-purple-400")} EXFILTRATED DATA ARCHIVES</span>')

text = text.replace('resultSlot.innerHTML = `<span style="color: #c084fc; font-size: 0.72rem;">⏳ Querying public rainbow tables &amp; dictionary matrices...</span>`;', 'resultSlot.innerHTML = `<span style="color: #c084fc; font-size: 0.72rem;">Querying public rainbow tables &amp; dictionary matrices...</span>`;')
text = text.replace('<span style="color: #4ade80; font-weight: 700; font-size: 0.75rem;">🔓 CRACKED IN ${data.crack_time_seconds || 0.01}s:</span>', '<span style="color: #4ade80; font-weight: 700; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 4px;">${getUiIcon("unlock", "w-3 h-3 text-emerald-400")} PLAINTEXT RECOVERED IN ${data.crack_time_seconds || 0.01}s:</span>')
text = text.replace('const titleText = isHardened ? "🛡️ Cryptographically Hardened" : "⚠️ Offline Hashcat Required";', 'const titleText = isHardened ? "Cryptographically Hardened" : "Offline Hashcat Required";')

text = text.replace("📋 Copy", "Copy")
text = text.replace("🔒 Unlock", "Unlock")

# 12. Drawer & Graph
text = text.replace(
    '<div style="color: #34d399; font-weight: 600; font-size: 0.8rem;">✓ Confirmed Account Registration</div>',
    '<div style="color: #34d399; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 4px;">${getUiIcon("check", "w-3 h-3 text-emerald-400")} Confirmed Account Registration</div>'
)
text = text.replace(
    '🔎 CANDIDATE HANDLES INVESTIGATED (${matchingSuspects.length})',
    '${getUiIcon("search", "w-3 h-3 text-amber-400")} CANDIDATE IDENTIFIERS (${matchingSuspects.length})'
)
text = text.replace(
    '🔒 Public handle is not disclosed by the platform API upon email check.',
    '${getUiIcon("lock", "w-3 h-3 text-zinc-500 inline mr-1")} Public handle is not disclosed by the platform API upon email check.'
)
text = text.replace(
    '<div style="font-size: 0.75rem; color: #f87171; font-weight: 600; margin-bottom: 0.4rem;">🔒 Intel Locked in Privacy Mode</div>',
    '<div style="font-size: 0.75rem; color: #f87171; font-weight: 600; margin-bottom: 0.4rem; display: flex; align-items: center; justify-content: center; gap: 4px;">${getUiIcon("lock", "w-3 h-3 text-rose-400")} Intel Locked in Privacy Mode</div>'
)

# 13. Toast iconMap
old_toast_map = """    const iconMap = {
        "success": "✓",
        "info": "ℹ",
        "warning": "⚠",
        "error": "✕"
    };

    toast.innerHTML = `<span style="font-weight: 700;">${iconMap[type] || '•'}</span> <span>${escapeHtml(message)}</span>`;"""

new_toast_map = """    const iconMap = {
        "success": getUiIcon("check", "w-3.5 h-3.5 text-emerald-400 inline mr-1.5"),
        "info": getUiIcon("alert", "w-3.5 h-3.5 text-sky-400 inline mr-1.5"),
        "warning": getUiIcon("alert", "w-3.5 h-3.5 text-amber-400 inline mr-1.5"),
        "error": getUiIcon("cross", "w-3.5 h-3.5 text-rose-400 inline mr-1.5")
    };

    toast.innerHTML = `${iconMap[type] || ''} <span>${escapeHtml(message)}</span>`;"""
text = text.replace(old_toast_map, new_toast_map)

# 14. Header AI status
old_ai_header = """function updateAIHeaderStatus() {
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
        if (icon) icon.innerText = "⚡";
    } else if (serverAIConfig && serverAIConfig.has_key) {
        text.innerText = `AI: ${serverAIConfig.provider.toUpperCase()} ACTIVE (.env)`;
        btn.style.borderColor = "#a855f7";
        btn.style.color = "#c084fc";
        btn.style.background = "rgba(168, 85, 247, 0.16)";
        if (icon) icon.innerText = "⚡";
    } else {
        text.innerText = "AI: OFFLINE MODE [ADD KEY]";
        btn.style.borderColor = "#475569";
        btn.style.color = "#94a3b8";
        btn.style.background = "rgba(30, 41, 59, 0.4)";
        if (icon) icon.innerText = "⚙️";
    }
}"""

new_ai_header = """function updateAIHeaderStatus() {
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
}"""
text = text.replace(old_ai_header, new_ai_header)

# AI Settings modal links and status
text = text.replace('link.innerHTML = "🔑 Get a free Google Gemini key &nearr;";', 'link.innerHTML = "Get Gemini Key &nearr;";')
text = text.replace('link.innerHTML = "🔑 Get a free Groq key in 20s (No credit card) &nearr;";', 'link.innerHTML = "Get Groq Key &nearr;";')

old_ai_status_env = """            statusDiv.style.background = "rgba(16, 185, 129, 0.12)";
            statusDiv.style.color = "#6ee7b7";
            statusDiv.style.border = "1px solid rgba(16, 185, 129, 0.3)";
            statusDiv.innerHTML = `✓ Active key detected from <strong>.env</strong>: <code>${escapeHtml(serverAIConfig.masked_key)}</code><br><span style="font-size:0.75rem; color:#a7f3d0;">Engine: ${escapeHtml(serverAIConfig.provider.toUpperCase())} (${escapeHtml(serverAIConfig.model)})</span>`;"""

new_ai_status_env = """            statusDiv.style.background = "rgba(16, 185, 129, 0.08)";
            statusDiv.style.color = "#6ee7b7";
            statusDiv.style.border = "1px solid rgba(16, 185, 129, 0.25)";
            statusDiv.innerHTML = `<div class="flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span> <span>Key loaded from .env: <code>${escapeHtml(serverAIConfig.masked_key)}</code> (${escapeHtml(serverAIConfig.provider.toUpperCase())} / ${escapeHtml(serverAIConfig.model)})</span></div>`;"""
text = text.replace(old_ai_status_env, new_ai_status_env)

# Test key status
text = text.replace('statusDiv.innerText = "⏳ Probing API endpoint and measuring round-trip latency...";', 'statusDiv.innerText = "Probing API endpoint and measuring round-trip latency...";')
text = text.replace(
    "statusDiv.innerHTML = `✓ Connection Successful! Provider: <strong>${escapeHtml(res.provider.toUpperCase())}</strong> • Latency: <strong>${res.latency_seconds || 0.3}s</strong>`;",
    "statusDiv.innerHTML = `<div class=\"flex items-center gap-2 text-emerald-400\"><span class=\"w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block\"></span> <span>Connection Verified: <strong>${escapeHtml(res.provider.toUpperCase())}</strong> • Latency: <strong>${res.latency_seconds || 0.3}s</strong></span></div>`;"
)
text = text.replace(
    "statusDiv.innerHTML = `✕ Test Failed: ${escapeHtml(res.error || 'Invalid API Key')}`;",
    "statusDiv.innerHTML = `<div class=\"flex items-center gap-2 text-rose-400\"><span class=\"w-1.5 h-1.5 rounded-full bg-rose-400 inline-block\"></span> <span>Test Failed: ${escapeHtml(res.error || 'Invalid API Key')}</span></div>`;"
)
text = text.replace(
    "statusDiv.innerText = `✕ Network error testing key: ${e.message}`;",
    "statusDiv.innerText = `Network error: ${e.message}`;"
)

# 15. AI Tab & Copilot
text = text.replace('<div class="evidence-title" style="color: #d8b4fe;">🧠 AI Threat Intelligence Engine</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #d8b4fe;">${getUiIcon("cpu", "w-4 h-4 text-purple-400")} AI Threat Intelligence Engine</div>')
text = text.replace('<div style="font-size: 1.8rem; margin-bottom: 8px; display: inline-block;">⚡</div>', '<div style="margin-bottom: 10px; display: inline-block;"><div class="stats-dot" style="width: 14px; height: 14px; background: #a855f7; box-shadow: 0 0 12px #a855f7;"></div></div>')
text = text.replace('<div class="evidence-title" style="color: #f87171;">⚠️ AI Dossier Generation Error</div>', '<div class="evidence-title flex items-center gap-1.5" style="color: #f87171;">${getUiIcon("alert", "w-4 h-4 text-rose-400")} AI Dossier Generation Error</div>')

text = text.replace('<span style="font-size: 0.76rem; color: #fde68a;">ℹ️ ${escapeHtml(notice)}</span>', '<span style="font-size: 0.76rem; color: #fde68a;">[INFO] ${escapeHtml(notice)}</span>')
text = text.replace('⚡ ${escapeHtml(engineLabel)}', '${escapeHtml(engineLabel)}')
text = text.replace('⚙️ AI Settings', 'AI Settings')
text = text.replace('🔄 Re-Synthesize', 'Re-analyze')

text = text.replace('<span>🛡️</span> EXECUTIVE FORENSIC SYNTHESIS', 'EXECUTIVE FORENSIC SYNTHESIS')
text = text.replace('<span>👥</span> PERSONA &amp; CANDIDATE ACCOUNT DISAMBIGUATION', 'IDENTITY &amp; CANDIDATE ACCOUNT ATTRIBUTION')
text = text.replace('<span>🎯</span> ADVERSARY ATTACK SIMULATION (DEFENSIVE RECON)', 'ADVERSARY ATTACK SIMULATION')
text = text.replace('🎣 Target-Specific Spear-Phishing Pretext:', 'Target-Specific Spear-Phishing Pretext:')
text = text.replace('⚡ Credential-Stuffing Blast Radius:', 'Credential-Stuffing Blast Radius:')
text = text.replace('🏡 Household &amp; Social Engineering Vectors:', 'Household &amp; Social Engineering Vectors:')

text = text.replace('<span>🔑</span> CREDENTIAL REUSE &amp; MUTATION ATTACK SURFACE', 'CREDENTIAL REUSE &amp; MUTATION ATTACK SURFACE')
text = text.replace('🧩 Detected Base Pattern Scheme:', 'Detected Base Pattern Scheme:')
text = text.replace('⚡ Corporate Gateway Cross-Reuse Assessment:', 'Corporate Gateway Cross-Reuse Assessment:')
text = text.replace('🛡️ Defensive Hardening Guidance:', 'Defensive Hardening Guidance:')
text = text.replace('<span>🛡️</span> PRIORITIZED DEFENSIVE MITIGATIONS', 'PRIORITIZED DEFENSIVE MITIGATIONS')
text = text.replace('<span>🤖</span> INTERACTIVE INVESTIGATOR COPILOT', 'INTERACTIVE INVESTIGATOR COPILOT')

# Copilot prompts
text = text.replace('🎯 Highest Attack Vector?', 'Highest Attack Vector?')
text = text.replace('🇳🇴 1881.no De-listing Steps?', '1881.no De-listing Guidance')
text = text.replace('📝 Draft User Advisory', 'Draft User Advisory')
text = text.replace('🔍 Verify Candidate Accounts', 'Verify Candidate Accounts')

text = text.replace('⚡ Copilot is analyzing forensic evidence...', 'Copilot is analyzing forensic evidence...')
text = text.replace('⚠️ Network error:', '[ERROR] Network error:')

# 16. Telecom Router
text = text.replace('<span>🌍</span> MULTI-COUNTRY CIVIL DIRECTORY &amp; TELECOM ROUTER', '<span class="flex items-center gap-1.5">${getUiIcon("globe", "w-4 h-4 text-sky-400")} CIVIL DIRECTORY &amp; TELECOM ROUTER</span>')
text = text.replace('🇳🇴 Norway (1881/GuleSider)', '[NO] Norway (1881/GuleSider)')
text = text.replace('🇸🇪 Sweden (Hitta/Ratsit)', '[SE] Sweden (Hitta/Ratsit)')
text = text.replace('🇩🇰 Denmark (Krak)', '[DK] Denmark (Krak)')
text = text.replace('🇵🇱 Poland (Infonumer/Panorama)', '[PL] Poland (Infonumer/Panorama)')
text = text.replace('🇺🇸 USA (NumLookup/TruePeople)', '[US] USA (NumLookup/TruePeople)')
text = text.replace('🇬🇧 UK (WhoCalled/192)', '[GB] UK (WhoCalled/192)')
text = text.replace('🇩🇪 Germany (DasTelefonbuch)', '[DE] Germany (DasTelefonbuch)')
text = text.replace('🌐 Global (Sync.me)', '[GLOBAL] International (Sync.me)')

text = text.replace("${escapeHtml(d.flag || '🌐')} ${escapeHtml(d.name)}", "${escapeHtml(d.name)}")

with open(r'frontend\static\js\app.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied full cleanup to app.js!")
