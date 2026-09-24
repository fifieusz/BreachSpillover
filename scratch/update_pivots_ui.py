import re

with open('frontend/static/js/app.v17.js', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = """    const pivotsContainer = document.getElementById("tab-pivots-content");
    if (pivotsContainer) {
        pivotsContainer.innerHTML = "";
        if (verifiedPivots.length === 0) {
            pivotsContainer.innerHTML = `
                <div class="evidence-card" style="border-left: 3px solid #10b981;">
                    <div class="evidence-title flex items-center gap-1.5" style="color: #34d399;">${getUiIcon("shieldCheck", "w-4 h-4 text-emerald-400")} No Correlated Private Pivots</div>
                    <div class="evidence-body" style="margin-top: 0.3rem;">No correlated personal phone numbers, secondary inboxes, or verified developer accounts confirmed.</div>
                </div>`;
        } else {
            verifiedPivots.forEach(piv => {"""

new_block = """    const pivotsContainer = document.getElementById("tab-pivots-content");
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
                if (pt === "FULL_NAME" || pt === "PERSON_NAME" || pt === "AVATAR_CORRELATION") return "identity";
                if (pt === "WORKPLACE" || pt === "BUSINESS_ASSOCIATE" || pt === "SUBDOMAIN_ASSET") return "business";
                if (pt === "PERSONA_PIVOT" || pt === "ROBLOX_PROFILE" || pv.includes("steam") || pv.includes("chess") || pv.includes("esports") || pv.includes("brawlhalla") || pv.includes("fortnite") || pv.includes("twitch") || pv.includes("gamertag")) return "gaming";
                if (pt === "OPENPGP_KEY" || pt === "GITHUB_SSH_KEY" || pt === "TECH_STACK" || pt === "FLAGSHIP_PROJECT" || pt === "EMAIL_PERMUTATION" || pv.includes("repository") || pv.includes("git repository")) return "technical";
                return "social";
            }

            const catCounts = { all: verifiedPivots.length, identity: 0, business: 0, social: 0, gaming: 0, technical: 0 };
            verifiedPivots.forEach(p => {
                const cat = getPivotCategory(p);
                catCounts[cat] = (catCounts[cat] || 0) + 1;
            });

            pivotsContainer.innerHTML = `
                <div class="pivot-filter-chips">
                    <button type="button" class="btn-pivot-filter active" data-pivot-filter="all" onclick="filterPivotCategory('all')">[ALL] <span class="filter-count">(${catCounts.all})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="identity" onclick="filterPivotCategory('identity')">[IDENTITY &amp; LEGAL] <span class="filter-count">(${catCounts.identity})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="business" onclick="filterPivotCategory('business')">[BUSINESS &amp; CORP] <span class="filter-count">(${catCounts.business})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="social" onclick="filterPivotCategory('social')">[ACCOUNTS &amp; SOCIAL] <span class="filter-count">(${catCounts.social})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="gaming" onclick="filterPivotCategory('gaming')">[GAMING &amp; ESPORTS] <span class="filter-count">(${catCounts.gaming})</span></button>
                    <button type="button" class="btn-pivot-filter" data-pivot-filter="technical" onclick="filterPivotCategory('technical')">[TECHNICAL &amp; KEYS] <span class="filter-count">(${catCounts.technical})</span></button>
                </div>
                <div id="pivot-cards-list"></div>
            `;
            const pivotCardsList = document.getElementById("pivot-cards-list");
            function addPivotCard(html, cat) {
                if (pivotCardsList) {
                    pivotCardsList.innerHTML += `<div class="pivot-entry-card" data-pivot-cat="${cat}">${html}</div>`;
                } else {
                    pivotsContainer.innerHTML += html;
                }
            }

            verifiedPivots.forEach(piv => {"""

assert old_block in code, "old_block not found in code"
code = code.replace(old_block, new_block, 1)

# Now replace pivotsContainer.innerHTML += inside verifiedPivots with addPivotCard
start_idx = code.find(new_block) + len(new_block)
end_str = '            });\n\n            if (suspectedPivots.length > 0) {'
end_idx = code.find(end_str, start_idx)
assert end_idx != -1, "end_str not found"

sub = code[start_idx:end_idx]
sub_mod = sub.replace('pivotsContainer.innerHTML += `', 'addPivotCard(`')
sub_mod = sub_mod.replace('`;\n                    return;', '`, getPivotCategory(piv));\n                    return;')
sub_mod = sub_mod.replace('`;\n            });', '`, getPivotCategory(piv));\n            });')

code = code[:start_idx] + sub_mod + code[end_idx:]

if 'window.filterPivotCategory =' not in code:
    code += """

window.filterPivotCategory = function(selectedCat) {
    document.querySelectorAll(".btn-pivot-filter").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-pivot-filter") === selectedCat);
    });
    document.querySelectorAll("#pivot-cards-list .pivot-entry-card").forEach(el => {
        if (selectedCat === "all" || el.getAttribute("data-pivot-cat") === selectedCat) {
            el.style.display = "block";
        } else {
            el.style.display = "none";
        }
    });
    if (window.SoundManager) window.SoundManager.play("click");
};
"""

with open('frontend/static/js/app.v17.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("SUCCESS: app.v17.js updated successfully!")
