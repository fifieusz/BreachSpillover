from typing import List, Dict, Any, Optional
from backend.masking import (
    mask_email, mask_name, mask_password, mask_phone,
    mask_address, mask_city, mask_pivot_value
)

EDGE_FONT = {
    "color": "#94a3b8",
    "size": 10,
    "face": "'JetBrains Mono', monospace",
    "background": "#08090b",
    "strokeWidth": 0,
    "align": "horizontal"
}

EDGE_COLOR = {
    "color": "#272e3f",
    "highlight": "#10b981",
    "hover": "#10b981"
}

HUB_STYLES = {
    "breaches": {
        "bg": "#220e15",
        "border": "#f43f5e",
        "highlight_bg": "#381724",
        "text": "#fecdd3",
        "edge_color": "#f43f5e"
    },
    "git": {
        "bg": "#0a192f",
        "border": "#38bdf8",
        "highlight_bg": "#132f4c",
        "text": "#bae6fd",
        "edge_color": "#38bdf8"
    },
    "accounts": {
        "bg": "#1a102e",
        "border": "#c084fc",
        "highlight_bg": "#2b1c47",
        "text": "#e9d5ff",
        "edge_color": "#c084fc"
    },
    "telecom": {
        "bg": "#051f1f",
        "border": "#22d3ee",
        "highlight_bg": "#0a2e2e",
        "text": "#a5f3fc",
        "edge_color": "#22d3ee"
    },
    "geo": {
        "bg": "#072115",
        "border": "#34d399",
        "highlight_bg": "#0d3121",
        "text": "#a7f3d0",
        "edge_color": "#34d399"
    },
    "semantic": {
        "bg": "#1c1427",
        "border": "#a855f7",
        "highlight_bg": "#2e1b4a",
        "text": "#f3e8ff",
        "edge_color": "#a855f7"
    }
}

def build_identity_graph(
    employee: Dict[str, Any],
    leaks: List[Dict[str, Any]],
    credentials: List[Dict[str, Any]],
    pivots: List[Dict[str, Any]],
    footprints: List[Dict[str, Any]],
    relatives: List[Dict[str, Any]],
    audit_mode: bool = True,
    cross_correlations: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Transforms relational exposure data into Vis.js compatible graph nodes and edges.
    Categorizes the attack graph into 5 Provenance Hubs:
      1. hub_breaches: Exfiltrated Breaches & Stealers
      2. hub_git: Developer & Git Archaeology (GitHub, commits, portfolios)
      3. hub_accounts: Real Web & Cloud Registrations (Holehe / OSINT probes)
      4. hub_telecom: International Telecom Profiling (E.164, Carriers)
      5. hub_geo: Physical & Residential Geospatial Coordinates
    """
    nodes = []
    edges = []
    emp_id = employee["id"]

    # 1. Central Identity Node
    emp_masked_name = mask_name(employee["full_name"], audit_mode)
    emp_masked_email = mask_email(employee["corporate_email"], audit_mode)
    emp_node_id = f"emp_{emp_id}"
    
    is_personal = employee.get("job_title") == "Personal Account" or any(
        employee.get("corporate_email", "").endswith(d) for d in [
            "@gmail.com", "@yahoo.com", "@outlook.com", "@hotmail.com", "@proton.me", "@protonmail.com", "@icloud.com"
        ]
    )
    has_real_name = bool(
        emp_masked_name 
        and emp_masked_name.strip() 
        and emp_masked_name != "Target User" 
        and not emp_masked_name.lower().startswith("webmail")
    )
    if has_real_name:
        center_label = f"[TARGET IDENTITY]\n{emp_masked_name}\n{emp_masked_email}"
    elif is_personal:
        center_label = f"[TARGET IDENTITY]\n{emp_masked_email}\nPersonal Webmail Profile"
    else:
        center_label = f"[TARGET IDENTITY]\n{emp_masked_name}\n{emp_masked_email}"
    
    target_title_text = f"Target: {emp_masked_name} ({emp_masked_email})" if has_real_name else f"Target: {emp_masked_email}"
    nodes.append({
        "id": emp_node_id,
        "label": center_label,
        "title": f"{target_title_text}\nRole: {employee.get('job_title', 'Individual User')}\nVIP: {employee.get('vip_level', 'Standard')}",
        "group": "employee",
        "category": "identity",
        "color": {
            "background": "#0c1322",
            "border": "#38bdf8",
            "highlight": {"background": "#13213c", "border": "#7dd3fc"}
        },
        "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 11, "bold": True},
        "shape": "box",
        "margin": 12,
        "borderWidth": 2,
        "data": {
            "type": "TARGET_IDENTITY",
            "name": emp_masked_name,
            "email": emp_masked_email,
            "role": employee.get("job_title", "Identity Profile"),
            "category": "identity",
            "audit_mode": audit_mode,
            "can_pivot": True,
            "pivot_type": "EMAIL",
            "pivot_value": employee.get("corporate_email")
        }
    })

    # If completely clean (no leaks at all)
    if not leaks and not credentials and not pivots:
        clean_node_id = f"clean_{emp_id}"
        nodes.append({
            "id": clean_node_id,
            "label": "[POSTURE: UNCOMPROMISED]\nZero Exposures Detected\nIdentity Verified Clean",
            "title": "This identity does not appear in any known infostealer malware logs or database breaches.",
            "group": "clean",
            "category": "clean",
            "color": {
                "background": "#062319",
                "border": "#10b981",
                "highlight": {"background": "#083324", "border": "#34d399"}
            },
            "font": {"color": "#6ee7b7", "face": "'JetBrains Mono', monospace", "size": 11, "bold": True},
            "shape": "box",
            "margin": 12,
            "borderWidth": 1.5,
            "data": {
                "type": "CLEAN_IDENTITY",
                "status": "UNCOMPROMISED",
                "category": "clean",
                "details": "No breach footprints found in threat intelligence repository."
            }
        })
        edges.append({
            "from": emp_node_id,
            "to": clean_node_id,
            "label": "POSTURE",
            "color": {"color": "#10b981", "highlight": "#34d399"},
            "arrows": "to",
            "width": 1.5,
            "font": EDGE_FONT,
            "category": "clean"
        })
        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    # =========================================================================
    # PARTITION PIVOTS INTO DISTINCT PROVENANCE BRANCHES
    # =========================================================================
    max_graph_leaks = 15
    displayed_leaks = leaks[:max_graph_leaks] if len(leaks) > max_graph_leaks else leaks
    displayed_leak_ids = {leak["id"] for leak in displayed_leaks}

    leak_pivots = []
    git_pivots = []
    account_pivots = []
    suspected_pivots = []
    telecom_pivots = []
    semantic_pivots = []

    for piv in pivots:
        s_leak = piv.get("source_leak_id")
        p_type = str(piv.get("pivot_type", "")).upper()
        p_val = str(piv.get("pivot_value", "")).lower()
        c_note = str(piv.get("context_note", "")).lower()

        # 1. Leak-associated pivots
        if s_leak and s_leak in displayed_leak_ids:
            leak_pivots.append(piv)
        # 2. Telecom pivots
        elif "PHONE" in p_type or "TELECOM" in p_type or "mobile" in c_note or "carrier" in c_note:
            telecom_pivots.append(piv)
        # 3. Semantic Career, Education, Co-Partners & Tech Competency pivots
        elif p_type in ["EDUCATION", "WORKPLACE", "BUSINESS_ASSOCIATE", "FLAGSHIP_PROJECT", "TECH_STACK", "CRYPTO_KEY", "PACKAGE_REGISTRY", "FULL_NAME", "NAME"]:
            semantic_pivots.append(piv)
        elif p_type == "PERSONA_PIVOT":
            account_pivots.append(piv)
        elif p_type == "TIMELINE":
            continue
        # 4. Suspected / Uncorroborated Accounts (held in review ledger)
        elif p_type == "SUSPECTED_ACCOUNT" or float(piv.get("confidence_score") or 0.85) < 0.85:
            suspected_pivots.append(piv)
        # 5. Developer & Git Archaeology / Infrastructure pivots
        elif (
            "GIT" in p_type or "GITHUB" in p_type or "GITLAB" in p_type 
            or "github" in p_val or "gitlab" in p_val or "commit" in c_note 
            or "developer repository" in c_note or ".github.io" in p_val
            or "OPENPGP" in p_type or "pgp" in p_val or "DOMAIN_INFRASTRUCTURE" in p_type
            or "SUBDOMAIN" in p_type or "PERMUTATION" in p_type or "DISPOSABLE" in p_type
        ):
            git_pivots.append(piv)
        # 6. Verified Web & Cloud Service Accounts (Holehe, Gravatar, Corroborated Handles)
        else:
            account_pivots.append(piv)

    # =========================================================================
    # HUB 1: EXFILTRATED BREACHES & STEALER LOGS
    # =========================================================================
    if displayed_leaks or credentials or leak_pivots:
        hub_breaches_id = "hub_breaches"
        style = HUB_STYLES["breaches"]
        nodes.append({
            "id": hub_breaches_id,
            "label": f"[PROVENANCE HUB: BREACHES]\nThreat Intelligence Ledger\n{len(leaks)} Verified Incidents",
            "title": "Categorical Hub: Exfiltrated dark web dumps, threat actor leaks, and active infostealer C2 logs.",
            "group": "hub_breaches",
            "category": "breaches",
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": style["highlight_bg"], "border": "#ffffff"}
            },
            "font": {"color": style["text"], "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
            "shape": "box",
            "margin": 10,
            "borderWidth": 2,
            "data": {"type": "PROVENANCE_HUB", "category": "breaches"}
        })
        edges.append({
            "from": emp_node_id,
            "to": hub_breaches_id,
            "label": "VIA THREAT DUMPS",
            "color": {"color": style["edge_color"], "highlight": "#ffffff"},
            "arrows": "to",
            "width": 2.5,
            "font": EDGE_FONT,
            "category": "breaches"
        })

        for leak in displayed_leaks:
            leak_node_id = f"leak_{leak['id']}"
            is_stealer = str(leak["leak_type"]).upper() == "INFOSTEALER"
            leak_header = "[INFOSTEALER MALWARE]" if is_stealer else "[DATABASE BREACH]"
            bg_color = "#180c10" if is_stealer else "#191209"
            border_color = "#f43f5e" if is_stealer else "#f59e0b"

            nodes.append({
                "id": leak_node_id,
                "label": f"{leak_header}\n{leak['leak_name']}\nDate: {leak.get('breach_date', 'N/A')}",
                "title": f"Incident: {leak['leak_name']}\nSeverity: {leak.get('severity', 'HIGH')}\nType: {leak.get('leak_type', 'BREACH')}",
                "group": "leak",
                "category": "breaches",
                "color": {
                    "background": bg_color,
                    "border": border_color,
                    "highlight": {"background": "#261118" if is_stealer else "#271b0c", "border": "#ffffff"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "DATA_BREACH",
                    "name": leak["leak_name"],
                    "leak_type": leak.get("leak_type", "BREACH"),
                    "breach_date": leak.get("breach_date", "N/A"),
                    "severity": leak.get("severity", "HIGH"),
                    "description": leak.get("description", ""),
                    "threat_source": leak.get("threat_actor_source", "Unknown"),
                    "category": "breaches"
                }
            })

            # Edge: Hub -> Leak
            edges.append({
                "from": hub_breaches_id,
                "to": leak_node_id,
                "label": "EXPOSED IN",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 2,
                "font": EDGE_FONT,
                "category": "breaches"
            })

        # Summary node for additional overflow leaks
        if len(leaks) > max_graph_leaks:
            overflow_count = len(leaks) - max_graph_leaks
            overflow_node_id = f"leak_overflow_{emp_id}"
            nodes.append({
                "id": overflow_node_id,
                "label": f"[+{overflow_count} VERIFIED BREACHES]\n{len(leaks)} Total Leaks Indexed\nDetailed in Evidence Ledger",
                "title": f"{overflow_count} additional verified breaches indexed. Inspect the Evidence Ledger for full catalog.",
                "group": "leak_overflow",
                "category": "breaches",
                "color": {
                    "background": "#0f172a",
                    "border": "#38bdf8",
                    "highlight": {"background": "#1e293b", "border": "#7dd3fc"}
                },
                "font": {"color": "#bae6fd", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "AGGREGATED_BREACHES",
                    "overflow_count": overflow_count,
                    "total_leaks": len(leaks),
                    "category": "breaches"
                }
            })
            edges.append({
                "from": hub_breaches_id,
                "to": overflow_node_id,
                "label": f"+{overflow_count} BREACHES",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "breaches"
            })

        # Credential Nodes
        displayed_credentials = [c for c in credentials if c.get("leak_id") in displayed_leak_ids][:15]
        for cred in displayed_credentials:
            cred_node_id = f"cred_{cred['id']}"
            leak_ref_id = f"leak_{cred['leak_id']}"
            masked_pwd = mask_password(cred.get("plaintext_password"), audit_mode)
            is_corp = bool(cred.get("is_corporate_password_match"))

            pwd_hash = cred.get("password_hash") or ""
            cred_label = f"[COMPROMISED PASSWORD]\nPassword: {masked_pwd}" if masked_pwd else (f"[PASSWORD HASH]\n{pwd_hash}" if pwd_hash else "[CREDENTIAL EXFILTRATED]")
            if cred.get("domain_compromised"):
                cred_label += f"\nDomain: {cred['domain_compromised']}"
            if is_corp:
                cred_label += "\n[CORPORATE MATCH: CRITICAL]"

            nodes.append({
                "id": cred_node_id,
                "label": cred_label,
                "title": f"Domain: {cred.get('domain_compromised')}\nPattern: {cred.get('password_pattern')}",
                "group": "credential",
                "category": "breaches",
                "color": {
                    "background": "#181308",
                    "border": "#f59e0b",
                    "highlight": {"background": "#241c0a", "border": "#fde047"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "STOLEN_CREDENTIAL",
                    "username_or_email": mask_email(cred.get("username_or_email"), audit_mode),
                    "password": masked_pwd,
                    "password_hash": pwd_hash,
                    "pattern": cred.get("password_pattern"),
                    "is_corporate_match": is_corp,
                    "compromised_domain": cred.get("domain_compromised"),
                    "leak_name": cred.get("leak_name"),
                    "category": "breaches",
                    "can_pivot": bool(pwd_hash or cred.get("plaintext_password") or cred.get("username_or_email")),
                    "pivot_type": "HASH" if pwd_hash else ("EMAIL" if "@" in str(cred.get("username_or_email") or "") else "CREDENTIAL"),
                    "pivot_value": pwd_hash or cred.get("username_or_email") or cred.get("plaintext_password")
                }
            })

            edges.append({
                "from": leak_ref_id,
                "to": cred_node_id,
                "label": "EXFILTRATED",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "breaches"
            })

        # Leak-associated pivots (secondary logins, infection hostnames, breach-phone correlations)
        for lp in leak_pivots[:8]:
            pivot_node_id = f"pivot_{lp['id']}"
            masked_val = mask_pivot_value(lp["pivot_type"], lp["pivot_value"], audit_mode)
            leak_ref_id = f"leak_{lp['source_leak_id']}"

            p_type = lp["pivot_type"].upper()
            icon = "[SECONDARY LOGIN]" if "LOGIN" in p_type else ("[INFECTION HOST]" if "INFECTION" in p_type else f"[{lp['pivot_type']}]")

            nodes.append({
                "id": pivot_node_id,
                "label": f"{icon}\n{masked_val}",
                "title": f"Type: {lp['pivot_type']}\nContext: {lp.get('context_note', '')}",
                "group": "pivot",
                "category": "breaches",
                "color": {
                    "background": "#081614",
                    "border": "#10b981",
                    "highlight": {"background": "#0d2623", "border": "#34d399"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "IDENTITY_PIVOT",
                    "pivot_type": lp["pivot_type"],
                    "value": masked_val,
                    "raw_value": lp.get("pivot_value"),
                    "confidence": lp.get("confidence_score", 1.0),
                    "context_note": lp.get("context_note"),
                    "category": "breaches",
                    "can_pivot": True,
                    "pivot_type": "PHONE" if "PHONE" in str(lp.get("pivot_type", "")).upper() else ("EMAIL" if "@" in str(lp.get("pivot_value", "")) else "USERNAME"),
                    "pivot_value": lp.get("pivot_value")
                }
            })

            edges.append({
                "from": leak_ref_id,
                "to": pivot_node_id,
                "label": "CORRELATED PIVOT",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "breaches"
            })

    # =========================================================================
    # HUB 2: DEVELOPER & GIT ARCHAEOLOGY
    # =========================================================================
    if git_pivots:
        hub_git_id = "hub_git"
        style = HUB_STYLES["git"]
        nodes.append({
            "id": hub_git_id,
            "label": f"[PROVENANCE HUB: DEVELOPER]\nGit Commit Archaeology\n{len(git_pivots)} Public Code Artifacts",
            "title": "Categorical Hub: Open source developer intelligence, public repositories, and author commit logs.",
            "group": "hub_git",
            "category": "git",
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": style["highlight_bg"], "border": "#ffffff"}
            },
            "font": {"color": style["text"], "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
            "shape": "box",
            "margin": 10,
            "borderWidth": 2,
            "data": {"type": "PROVENANCE_HUB", "category": "git"}
        })
        edges.append({
            "from": emp_node_id,
            "to": hub_git_id,
            "label": "VIA GITHUB / GIT LOGS",
            "color": {"color": style["edge_color"], "highlight": "#ffffff"},
            "arrows": "to",
            "width": 2.5,
            "font": EDGE_FONT,
            "category": "git"
        })

        for gp in git_pivots[:12]:
            p_node_id = f"pivot_{gp['id']}"
            p_val = gp["pivot_value"]
            c_note = str(gp.get("context_note", ""))
            conf = float(gp.get("confidence_score") or 0.95)
            conf_pct = int(round(conf * 100))

            is_portfolio = ".github.io" in p_val.lower()
            is_collaborator = "collaborator" in c_note.lower() or "workspace" in c_note.lower()
            is_ssh_key = "ssh" in p_val.lower() or "ssh" in str(gp.get("pivot_type", "")).lower()

            is_subdomain = "SUBDOMAIN" in str(gp.get("pivot_type", "")).upper() or "gateway:" in p_val.lower()
            is_permutation = "PERMUTATION" in str(gp.get("pivot_type", "")).upper()
            is_gitlab = "gitlab" in p_val.lower()
            is_disposable = "DISPOSABLE" in str(gp.get("pivot_type", "")).upper() or "burner" in p_val.lower()

            if is_disposable:
                label_head = "[DISPOSABLE BURNER]"
                edge_label = "EVASION ALERT"
                border_col = "#f59e0b"
                bg_col = "#2e1005"
            elif is_subdomain:
                label_head = "[CORPORATE GATEWAY]"
                edge_label = "EXPOSED PORTAL"
                border_col = "#ef4444"
                bg_col = "#200b0f"
            elif is_permutation:
                label_head = "[EMAIL PERMUTATIONS]"
                edge_label = "CORP SCHEME"
                border_col = "#818cf8"
                bg_col = "#15162c"
            elif is_gitlab:
                label_head = "[GITLAB REPOSITORY]"
                edge_label = "CODE REPO"
                border_col = "#f97316"
                bg_col = "#241208"
            elif is_ssh_key:
                label_head = "[GITHUB SSH KEY]"
                edge_label = "CRYPTO KEY"
                border_col = "#06b6d4"
                bg_col = "#041b24"
            elif is_collaborator:
                label_head = "[COLLABORATOR WORKSPACE]"
                edge_label = "CONTRIBUTOR"
                border_col = "#64748b"
                bg_col = "#0f172a"
            elif is_portfolio:
                label_head = "[DEVELOPER PORTFOLIO]"
                edge_label = "AUTHOR"
                border_col = "#38bdf8"
                bg_col = "#0c1f33"
            elif "github: @" in p_val.lower() or "github: " in p_val.lower():
                label_head = "[GITHUB DEVELOPER ACCOUNT]"
                edge_label = "DEV ACCOUNT"
                border_col = "#38bdf8"
                bg_col = "#0a1f33"
            else:
                label_head = "[OWNED REPOSITORY]"
                edge_label = "AUTHOR"
                border_col = "#38bdf8"
                bg_col = "#0c1f33"

            conf_tier = "VERIFIED" if conf >= 0.95 else ("HIGH" if conf >= 0.80 else "MEDIUM")
            label_head_with_conf = f"{label_head} • {conf_pct}% CONF"

            nodes.append({
                "id": p_node_id,
                "label": f"{label_head_with_conf}\n{p_val}",
                "title": f"Git Artifact: {p_val}\nConfidence: {conf_pct}% ({conf_tier})\nContext: {c_note}",
                "group": "pivot_git",
                "category": "git",
                "color": {
                    "background": bg_col,
                    "border": border_col,
                    "highlight": {"background": "#16385c", "border": "#7dd3fc"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 2 if conf >= 0.85 else 1.5,
                "data": {
                    "type": "GIT_ARTIFACT",
                    "value": p_val,
                    "confidence": conf,
                    "confidence_tier": conf_tier,
                    "context": c_note,
                    "category": "git",
                    "is_collaborator": is_collaborator,
                    "can_pivot": True,
                    "pivot_type": "DOMAIN" if is_subdomain else ("EMAIL" if "@" in p_val else "USERNAME"),
                    "pivot_value": p_val.replace("GitHub: @", "").replace("GitHub: ", "").strip()
                }
            })

            edges.append({
                "from": hub_git_id,
                "to": p_node_id,
                "label": edge_label,
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "git"
            })

        # Summary node for overflow git artifacts
        if len(git_pivots) > 12:
            git_overflow_count = len(git_pivots) - 12
            git_overflow_node_id = f"git_overflow_{emp_id}"
            nodes.append({
                "id": git_overflow_node_id,
                "label": f"[+{git_overflow_count} CODE ARTIFACTS]\n{len(git_pivots)} Repositories & Artifacts\nDetailed in Evidence Ledger",
                "title": f"{git_overflow_count} additional developer artifacts indexed. Inspect the Evidence Ledger for full catalog.",
                "group": "git_overflow",
                "category": "git",
                "color": {
                    "background": "#0f172a",
                    "border": "#38bdf8",
                    "highlight": {"background": "#1e293b", "border": "#7dd3fc"}
                },
                "font": {"color": "#bae6fd", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "AGGREGATED_GIT",
                    "overflow_count": git_overflow_count,
                    "total_git": len(git_pivots),
                    "category": "git"
                }
            })
            edges.append({
                "from": hub_git_id,
                "to": git_overflow_node_id,
                "label": f"+{git_overflow_count} ARTIFACTS",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "git"
            })

    # =========================================================================
    # HUB 3: PUBLIC WEB & CLOUD SERVICE ACCOUNTS
    # =========================================================================
    if account_pivots:
        hub_acc_id = "hub_accounts"
        style = HUB_STYLES["accounts"]
        hub_acc_text = f"[PROVENANCE HUB: ACCOUNTS]\nOnline Service Footprint\n{len(account_pivots)} Verified Platforms"
        if suspected_pivots:
            hub_acc_text += f"\n({len(suspected_pivots)} in Suspected Ledger)"
        nodes.append({
            "id": hub_acc_id,
            "label": hub_acc_text,
            "title": f"Categorical Hub: {len(account_pivots)} verified accounts corroborated via open endpoints. ({len(suspected_pivots)} unverified candidates in review ledger)",
            "group": "hub_accounts",
            "category": "accounts",
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": style["highlight_bg"], "border": "#ffffff"}
            },
            "font": {"color": style["text"], "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
            "shape": "box",
            "margin": 10,
            "borderWidth": 2,
            "data": {"type": "PROVENANCE_HUB", "category": "accounts"}
        })
        edges.append({
            "from": emp_node_id,
            "to": hub_acc_id,
            "label": "VIA OSINT PROBES",
            "color": {"color": style["edge_color"], "highlight": "#ffffff"},
            "arrows": "to",
            "width": 2.5,
            "font": EDGE_FONT,
            "category": "accounts"
        })

        for ap in account_pivots[:12]:
            p_node_id = f"pivot_{ap['id']}"
            p_val = ap["pivot_value"]
            c_note = str(ap.get("context_note", ""))
            conf = float(ap.get("confidence_score") or 0.85)
            conf_pct = int(round(conf * 100))

            p_val_low = p_val.lower()
            if "steam" in p_val_low:
                cat_tag = "PROFILE: STEAM"
                acc_border = "#0284c7"
                acc_bg = "#071724"
            elif "roblox" in p_val_low:
                cat_tag = "PROFILE: ROBLOX"
                acc_border = "#e11d48"
                acc_bg = "#240a10"
            elif "chess" in p_val_low:
                cat_tag = "PROFILE: CHESS.COM"
                acc_border = "#65a30d"
                acc_bg = "#111f07"
            elif "spotify" in p_val_low:
                cat_tag = "STREAMING: SPOTIFY"
                acc_border = "#10b981"
                acc_bg = "#072016"
            elif "twitter" in p_val_low or " x: @" in p_val_low:
                cat_tag = "SOCIAL: TWITTER/X"
                acc_border = "#38bdf8"
                acc_bg = "#0a1926"
            elif "reddit" in p_val_low:
                cat_tag = "COMMUNITY: REDDIT"
                acc_border = "#f97316"
                acc_bg = "#241006"
            elif "telegram" in p_val_low:
                cat_tag = "MESSAGING: TELEGRAM"
                acc_border = "#0ea5e9"
                acc_bg = "#061826"
            elif "dockerhub" in p_val_low:
                cat_tag = "REGISTRY: DOCKERHUB"
                acc_border = "#0284c7"
                acc_bg = "#051624"
            elif "hackerrank" in p_val_low:
                cat_tag = "CODING: HACKERRANK"
                acc_border = "#10b981"
                acc_bg = "#072016"
            elif "keybase" in p_val_low:
                cat_tag = "IDENTITY: KEYBASE"
                acc_border = "#f59e0b"
                acc_bg = "#261a06"
            elif "gravatar" in p_val_low:
                cat_tag = "AVATAR: GRAVATAR"
                acc_border = "#a855f7"
                acc_bg = "#1f102e"
            elif "persona_pivot" in p_val_low or "discovered alias" in p_val_low:
                cat_tag = "RECURSIVE ALIAS"
                acc_border = "#c084fc"
                acc_bg = "#220930"
            elif "gamertag" in p_val_low or "brawlhalla" in p_val_low or "esports" in p_val_low:
                cat_tag = "PROFILE: ESPORTS"
                acc_border = "#f59e0b"
                acc_bg = "#261a06"
            else:
                cat_tag = "REGISTERED ACCOUNT"
                acc_border = "#c084fc"
                acc_bg = "#19102b"

            plat_stem = p_val.split(":")[0].strip().lower().replace(" / x", "").replace("x", "twitter")
            matching_suspects = [
                sp for sp in suspected_pivots
                if plat_stem in sp.get("pivot_value", "").split(":")[0].strip().lower().replace(" / x", "").replace("x", "twitter")
            ]

            if matching_suspects:
                acc_label = f"[{cat_tag}] • {conf_pct}% CONF\n{p_val}\n[CANDIDATES: {len(matching_suspects)}]"
            else:
                acc_label = f"[{cat_tag}] • {conf_pct}% CONF\n{p_val}"

            conf_tier = "VERIFIED" if conf >= 0.95 else ("HIGH" if conf >= 0.80 else "MEDIUM")

            tooltip_str = f"Service: {p_val}\nConfidence: {conf_pct}% ({conf_tier})\nDetails: {c_note}"
            if matching_suspects:
                tooltip_str += f"\n\n[CANDIDATE IDENTIFIERS ({len(matching_suspects)})]:\n" + "\n".join([f"• {sp.get('pivot_value')}" for sp in matching_suspects])

            nodes.append({
                "id": p_node_id,
                "label": acc_label,
                "title": tooltip_str,
                "group": "pivot_account",
                "category": "accounts",
                "color": {
                    "background": acc_bg,
                    "border": acc_border,
                    "highlight": {"background": "#2a1b47", "border": "#e9d5ff"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 2 if conf >= 0.85 else 1.5,
                "data": {
                    "type": "PUBLIC_ACCOUNT",
                    "value": p_val,
                    "confidence": conf,
                    "confidence_tier": conf_tier,
                    "context": c_note,
                    "category": "accounts",
                    "candidate_handles": [sp.get("pivot_value") for sp in matching_suspects],
                    "candidate_count": len(matching_suspects),
                    "can_pivot": True,
                    "pivot_type": "USERNAME",
                    "pivot_value": p_val.split(":")[-1].strip().lstrip("@")
                }
            })

            conf_word = "VERY HIGH" if conf >= 0.95 else "HIGH" if conf >= 0.85 else "MEDIUM" if conf >= 0.65 else "LOW"
            edge_label = f"CONFIDENCE: {conf_word}"
            edges.append({
                "from": hub_acc_id,
                "to": p_node_id,
                "label": edge_label,
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "accounts"
            })

        # Summary node for additional overflow accounts
        if len(account_pivots) > 12:
            acc_overflow_count = len(account_pivots) - 12
            acc_overflow_node_id = f"acc_overflow_{emp_id}"
            nodes.append({
                "id": acc_overflow_node_id,
                "label": f"[+{acc_overflow_count} ACTIVE ACCOUNTS]\n{len(account_pivots)} Accounts Verified\nDetailed in Evidence Ledger",
                "title": f"{acc_overflow_count} additional registered accounts verified. Inspect the Evidence Ledger for full catalog.",
                "group": "account_overflow",
                "category": "accounts",
                "color": {
                    "background": "#1e1b4b",
                    "border": "#a855f7",
                    "highlight": {"background": "#2e1065", "border": "#c084fc"}
                },
                "font": {"color": "#e9d5ff", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "AGGREGATED_ACCOUNTS",
                    "overflow_count": acc_overflow_count,
                    "total_accounts": len(account_pivots),
                    "category": "accounts"
                }
            })
            edges.append({
                "from": hub_acc_id,
                "to": acc_overflow_node_id,
                "label": f"+{acc_overflow_count} ACCOUNTS",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "accounts"
            })

        # Render candidate/suspected accounts connected to Accounts Hub with distinct quarantined styling
        # Deduplicate by platform so we never render duplicate candidate nodes for the same platform (e.g. Roblox)
        seen_suspected_plats = set()
        deduped_suspected = []
        for sp in suspected_pivots:
            sp_plat = sp.get("pivot_value", "").split(":")[0].strip().lower()
            if sp_plat not in seen_suspected_plats:
                seen_suspected_plats.add(sp_plat)
                deduped_suspected.append(sp)

        for sp in deduped_suspected[:6]:
            sp_node_id = f"suspected_{sp['id']}"
            sp_val = sp["pivot_value"]
            sp_note = str(sp.get("context_note", ""))
            sp_conf = float(sp.get("confidence_score") or 0.65)
            sp_conf_pct = int(round(sp_conf * 100))

            nodes.append({
                "id": sp_node_id,
                "label": f"[CANDIDATE ALIAS] • {sp_conf_pct}% CONF\n{sp_val}",
                "title": f"Candidate Profile: {sp_val}\nConfidence: {sp_conf_pct}%\nNote: {sp_note}",
                "group": "pivot_account_suspected",
                "category": "accounts",
                "color": {
                    "background": "#1c1407",
                    "border": "#f59e0b",
                    "highlight": {"background": "#2e210b", "border": "#fde047"}
                },
                "font": {"color": "#fde68a", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "borderDashes": [4, 4],
                "data": {
                    "type": "SUSPECTED_ACCOUNT",
                    "value": sp_val,
                    "confidence": sp_conf,
                    "context": sp_note,
                    "category": "accounts"
                }
            })
            edges.append({
                "from": hub_acc_id,
                "to": sp_node_id,
                "label": "SUSPECTED ALIAS",
                "color": {"color": "#f59e0b", "highlight": "#fde047"},
                "arrows": "to",
                "width": 1.5,
                "dashes": [4, 4],
                "font": EDGE_FONT,
                "category": "accounts"
            })

    # =========================================================================
    # HUB 4: TELECOM & CARRIER PROFILING
    # =========================================================================
    if telecom_pivots:
        hub_tel_id = "hub_telecom"
        style = HUB_STYLES["telecom"]
        nodes.append({
            "id": hub_tel_id,
            "label": f"[PROVENANCE HUB: TELECOM]\nCarrier & Line Profiling\n{len(telecom_pivots)} E.164 Endpoints",
            "title": "Categorical Hub: Validated telephone lines, cellular routing networks, and messaging links.",
            "group": "hub_telecom",
            "category": "telecom",
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": style["highlight_bg"], "border": "#ffffff"}
            },
            "font": {"color": style["text"], "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
            "shape": "box",
            "margin": 10,
            "borderWidth": 2,
            "data": {"type": "PROVENANCE_HUB", "category": "telecom"}
        })
        edges.append({
            "from": emp_node_id,
            "to": hub_tel_id,
            "label": "VIA TELECOM / CARRIER",
            "color": {"color": style["edge_color"], "highlight": "#ffffff"},
            "arrows": "to",
            "width": 2.5,
            "font": EDGE_FONT,
            "category": "telecom"
        })

        for tp in telecom_pivots[:5]:
            p_node_id = f"pivot_{tp['id']}"
            masked_phone = mask_pivot_value(tp["pivot_type"], tp["pivot_value"], audit_mode)
            c_note = tp.get("context_note", "")

            nodes.append({
                "id": p_node_id,
                "label": f"[MOBILE TELECOM LINE] • 100% CONF\n{masked_phone}",
                "title": f"Phone: {masked_phone}\nConfidence: 100% (VERIFIED)\nRouting: {c_note}",
                "group": "pivot",
                "category": "telecom",
                "color": {
                    "background": "#051f1f",
                    "border": "#22d3ee",
                    "highlight": {"background": "#093333", "border": "#67e8f9"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "PHONE_LINE",
                    "value": masked_phone,
                    "raw_value": tp.get("pivot_value"),
                    "context": c_note,
                    "category": "telecom",
                    "can_pivot": True,
                    "pivot_type": "PHONE",
                    "pivot_value": tp.get("pivot_value")
                }
            })

            edges.append({
                "from": hub_tel_id,
                "to": p_node_id,
                "label": "E.164 LINE",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "telecom"
            })

            # If phone was discovered via GitHub / repo CV, link directly to git hub too to show provenance
            if "github" in c_note.lower() or "repository" in c_note.lower():
                if git_pivots:
                    first_git_id = f"pivot_{git_pivots[0]['id']}"
                    edges.append({
                        "from": first_git_id,
                        "to": p_node_id,
                        "label": "MINED FROM CV/DOC",
                        "color": {"color": "#38bdf8", "highlight": "#7dd3fc"},
                        "arrows": "to",
                        "width": 1.5,
                        "font": EDGE_FONT,
                        "category": "git"
                    })

    # =========================================================================
    # HUB 5: GEOSPATIAL & RESIDENTIAL RECORDS
    # =========================================================================
    if footprints or relatives:
        hub_geo_id = "hub_geo"
        style = HUB_STYLES["geo"]
        nodes.append({
            "id": hub_geo_id,
            "label": f"[PROVENANCE HUB: GEOSPATIAL]\nResidential & Location Records\n{len(footprints)} Coordinates Mapped",
            "title": "Categorical Hub: Physical coordinates, residential living units, and household cohabitants.",
            "group": "hub_geo",
            "category": "geo",
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": style["highlight_bg"], "border": "#ffffff"}
            },
            "font": {"color": style["text"], "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
            "shape": "box",
            "margin": 10,
            "borderWidth": 2,
            "data": {"type": "PROVENANCE_HUB", "category": "geo"}
        })
        edges.append({
            "from": emp_node_id,
            "to": hub_geo_id,
            "label": "VIA RESIDENTIAL / COURIER",
            "color": {"color": style["edge_color"], "highlight": "#ffffff"},
            "arrows": "to",
            "width": 2.5,
            "font": EDGE_FONT,
            "category": "geo"
        })

        displayed_footprints = footprints[:5]
        for foot in displayed_footprints:
            foot_node_id = f"foot_{foot['id']}"
            masked_addr = mask_address(foot["address_line"], audit_mode)
            masked_c = mask_city(foot["city"], audit_mode)

            nodes.append({
                "id": foot_node_id,
                "label": f"[RESIDENTIAL RECORD]\n{masked_addr}\n{masked_c}",
                "title": f"Location: {masked_addr}, {masked_c}\nType: {foot.get('exposure_type')}",
                "group": "physical",
                "category": "geo",
                "color": {
                    "background": "#081912",
                    "border": "#34d399",
                    "highlight": {"background": "#0c271c", "border": "#6ee7b7"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "PHYSICAL_ADDRESS",
                    "address": masked_addr,
                    "city": masked_c,
                    "postal_code": foot["postal_code"],
                    "country": foot["country"],
                    "exposure_type": foot.get("exposure_type"),
                    "category": "geo",
                    "can_pivot": True,
                    "pivot_type": "LOCATION",
                    "pivot_value": foot.get("city") or foot.get("address_line")
                }
            })

            edges.append({
                "from": hub_geo_id,
                "to": foot_node_id,
                "label": "GEO LOCATION",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "geo"
            })

        # Relatives Nodes
        for rel in relatives:
            rel_node_id = f"rel_{rel['id']}"
            masked_rel_name = mask_name(rel["full_name"], audit_mode)
            source_id = f"foot_{rel['shared_address_id']}" if rel.get("shared_address_id") else hub_geo_id

            nodes.append({
                "id": rel_node_id,
                "label": f"[HOUSEHOLD CONTACT]\n{masked_rel_name} ({rel['relationship']})\nSocial Engineering Target",
                "title": f"Cohabitant: {masked_rel_name} ({rel['relationship']})\nExploitation Risk: {rel.get('social_engineering_risk')}",
                "group": "relative",
                "category": "geo",
                "color": {
                    "background": "#190d15",
                    "border": "#fb7185",
                    "highlight": {"background": "#271221", "border": "#fda4af"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 12,
                "borderWidth": 2,
                "data": {
                    "type": "HOUSEHOLD_RELATIVE",
                    "name": masked_rel_name,
                    "relationship": rel["relationship"],
                    "risk_vector": rel.get("social_engineering_risk"),
                    "category": "geo",
                    "can_pivot": True,
                    "pivot_type": "EMAIL" if rel.get("contact_email") else "NAME",
                    "pivot_value": rel.get("contact_email") or rel.get("full_name")
                }
            })

            edges.append({
                "from": source_id,
                "to": rel_node_id,
                "label": "SHARED RESIDENCE",
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 2,
                "font": EDGE_FONT,
                "category": "geo"
            })

    # =========================================================================
    # HUB 6: SEMANTIC CAREER, EDUCATION & INTEL
    # =========================================================================
    if semantic_pivots:
        hub_sem_id = "hub_semantic"
        style = HUB_STYLES.get("semantic", HUB_STYLES["accounts"])
        nodes.append({
            "id": hub_sem_id,
            "label": f"[PROVENANCE HUB: CAREER & INTEL]\nIdentity Background & Skills\n{len(semantic_pivots)} Semantic Artifacts",
            "title": "Categorical Hub: Higher education alma mater, workplace experience, flagship projects, and tech competencies.",
            "group": "hub_semantic",
            "category": "semantic",
            "color": {
                "background": style["bg"],
                "border": style["border"],
                "highlight": {"background": style["highlight_bg"], "border": "#ffffff"}
            },
            "font": {"color": style["text"], "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
            "shape": "box",
            "margin": 10,
            "borderWidth": 2,
            "data": {"type": "PROVENANCE_HUB", "category": "semantic"}
        })
        edges.append({
            "from": emp_node_id,
            "to": hub_sem_id,
            "label": "VIA SEMANTIC OSINT",
            "color": {"color": style["edge_color"], "highlight": "#ffffff"},
            "arrows": "to",
            "width": 2.5,
            "font": EDGE_FONT,
            "category": "semantic"
        })

        for sp in semantic_pivots[:12]:
            p_node_id = f"pivot_{sp['id']}"
            p_type = sp["pivot_type"]
            p_val = sp["pivot_value"]
            c_note = str(sp.get("context_note", ""))

            if p_type == "EDUCATION":
                s_label = f"[EDUCATION: ALMA MATER]\n{p_val}"
                s_border = "#3b82f6"
                s_bg = "#0f1d3a"
                edge_label = "ALMA MATER"
            elif p_type == "WORKPLACE":
                s_label = f"[EXPERIENCE: WORKPLACE]\n{p_val}"
                s_border = "#f59e0b"
                s_bg = "#261606"
                edge_label = "EMPLOYED"
            elif p_type == "BUSINESS_ASSOCIATE":
                s_label = f"[CO-PARTNER: BUSINESS]\n{p_val}"
                s_border = "#f59e0b"
                s_bg = "#261606"
                edge_label = "CO-FOUNDER"
            elif p_type == "FLAGSHIP_PROJECT":
                s_label = f"[PROJECT: FLAGSHIP]\n{p_val}"
                s_border = "#a855f7"
                s_bg = "#220e38"
                edge_label = "ENGINEERED"
            elif p_type == "TECH_STACK":
                s_label = f"[SKILLS & STACK]\n{p_val}"
                s_border = "#06b6d4"
                s_bg = "#082026"
                edge_label = "COMPETENCY"
            elif p_type == "CRYPTO_KEY":
                s_label = f"[CRYPTO: SSH KEY]\n{p_val}"
                s_border = "#10b981"
                s_bg = "#06241a"
                edge_label = "PUBLIC KEY"
            elif p_type in ["FULL_NAME", "NAME"]:
                s_label = f"[RESOLVED IDENTITY]\n{p_val}"
                s_border = "#38bdf8"
                s_bg = "#0c1f33"
                edge_label = "REAL NAME"
            else:
                s_label = f"[SEMANTIC ARTIFACT]\n{p_val}"
                s_border = "#ec4899"
                s_bg = "#260b1c"
                edge_label = "EXTRACTED"

            nodes.append({
                "id": p_node_id,
                "label": s_label,
                "title": f"Semantic Artifact: {p_val}\nDetails: {c_note}",
                "group": "pivot_semantic",
                "category": "semantic",
                "color": {
                    "background": s_bg,
                    "border": s_border,
                    "highlight": {"background": "#1e293b", "border": "#ffffff"}
                },
                "font": {"color": "#f8fafc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                "shape": "box",
                "margin": 10,
                "borderWidth": 1.5,
                "data": {
                    "type": "SEMANTIC_ARTIFACT",
                    "subtype": p_type,
                    "value": p_val,
                    "context": c_note,
                    "category": "semantic"
                }
            })

            edges.append({
                "from": hub_sem_id,
                "to": p_node_id,
                "label": edge_label,
                "color": EDGE_COLOR,
                "arrows": "to",
                "width": 1.5,
                "font": EDGE_FONT,
                "category": "semantic"
            })

    # =========================================================================
    # CROSS-TARGET CORRELATIONS (LATERAL MOVEMENT & REUSE RINGS)
    # =========================================================================
    if cross_correlations:
        seen_targets = set()

        for sc in cross_correlations.get("shared_credentials", [])[:6]:
            t_id = sc.get("target_id")
            if t_id and t_id not in seen_targets:
                seen_targets.add(t_id)
                t_node_id = f"cross_target_{t_id}"
                c_name = sc.get("full_name") or "Correlated Target"
                c_email = sc.get("corporate_email") or ""
                nodes.append({
                    "id": t_node_id,
                    "label": f"[LATERAL REUSE RING]\n{c_name}\n{c_email}",
                    "title": f"Lateral Link: Shares credentials with {c_name} ({c_email})\nLeak: {sc.get('leak_name', 'Breach')}",
                    "group": "correlated_identity",
                    "category": "breaches",
                    "color": {
                        "background": "#2c0b0e",
                        "border": "#f43f5e",
                        "highlight": {"background": "#3f1218", "border": "#fda4af"}
                    },
                    "font": {"color": "#fecdd3", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                    "shape": "box",
                    "margin": 10,
                    "borderWidth": 2,
                    "data": {
                        "type": "CORRELATED_IDENTITY",
                        "can_pivot": True,
                        "pivot_type": "EMAIL",
                        "pivot_value": c_email,
                        "name": c_name,
                        "correlation_type": "SHARED_CREDENTIAL"
                    }
                })
                edges.append({
                    "from": emp_node_id,
                    "to": t_node_id,
                    "label": "LATERAL PWD REUSE",
                    "color": {"color": "#f43f5e", "highlight": "#fda4af"},
                    "arrows": "to;from",
                    "width": 2,
                    "font": EDGE_FONT,
                    "category": "breaches"
                })

        for sa in cross_correlations.get("shared_addresses", [])[:4]:
            t_id = sa.get("target_id")
            if t_id and t_id not in seen_targets:
                seen_targets.add(t_id)
                t_node_id = f"cross_target_{t_id}"
                c_name = sa.get("full_name") or "Co-Habitant"
                c_email = sa.get("corporate_email") or ""
                nodes.append({
                    "id": t_node_id,
                    "label": f"[CO-HABITANT TARGET]\n{c_name}\n{c_email}",
                    "title": f"Physical Proximity: Shares residence with {c_name} ({c_email})\nAddress: {sa.get('address_line', '')}, {sa.get('city', '')}",
                    "group": "correlated_identity",
                    "category": "geo",
                    "color": {
                        "background": "#092419",
                        "border": "#10b981",
                        "highlight": {"background": "#0f3625", "border": "#6ee7b7"}
                    },
                    "font": {"color": "#a7f3d0", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                    "shape": "box",
                    "margin": 10,
                    "borderWidth": 2,
                    "data": {
                        "type": "CORRELATED_IDENTITY",
                        "can_pivot": True,
                        "pivot_type": "EMAIL",
                        "pivot_value": c_email,
                        "name": c_name,
                        "correlation_type": "SHARED_RESIDENCE"
                    }
                })
                edges.append({
                    "from": emp_node_id,
                    "to": t_node_id,
                    "label": "SHARED RESIDENCE",
                    "color": {"color": "#10b981", "highlight": "#6ee7b7"},
                    "arrows": "to;from",
                    "width": 1.5,
                    "font": EDGE_FONT,
                    "category": "geo"
                })

        for sp in cross_correlations.get("shared_pivots", [])[:4]:
            t_id = sp.get("target_id")
            if t_id and t_id not in seen_targets:
                seen_targets.add(t_id)
                t_node_id = f"cross_target_{t_id}"
                c_name = sp.get("full_name") or "Correlated Target"
                c_email = sp.get("corporate_email") or ""
                nodes.append({
                    "id": t_node_id,
                    "label": f"[LINKED IDENTITY]\n{c_name}\n{c_email}",
                    "title": f"Shared Identifier: {sp.get('pivot_type')} ({sp.get('pivot_value')}) linked to {c_name}",
                    "group": "correlated_identity",
                    "category": "telecom" if "PHONE" in str(sp.get("pivot_type", "")) else "identity",
                    "color": {
                        "background": "#06222b",
                        "border": "#06b6d4",
                        "highlight": {"background": "#0a3440", "border": "#67e8f9"}
                    },
                    "font": {"color": "#a5f3fc", "face": "'JetBrains Mono', monospace", "size": 10, "bold": True},
                    "shape": "box",
                    "margin": 10,
                    "borderWidth": 2,
                    "data": {
                        "type": "CORRELATED_IDENTITY",
                        "can_pivot": True,
                        "pivot_type": "EMAIL",
                        "pivot_value": c_email,
                        "name": c_name,
                        "correlation_type": "SHARED_PIVOT"
                    }
                })
                edges.append({
                    "from": emp_node_id,
                    "to": t_node_id,
                    "label": f"SHARED {sp.get('pivot_type', 'IDENTIFIER')}",
                    "color": {"color": "#06b6d4", "highlight": "#67e8f9"},
                    "arrows": "to;from",
                    "width": 1.5,
                    "font": EDGE_FONT,
                    "category": "telecom" if "PHONE" in str(sp.get("pivot_type", "")) else "identity"
                })

    def strip_ui_styles(item):
        for key in ["color", "font", "shape", "margin", "borderWidth", "borderDashes", "dashes", "width"]:
            item.pop(key, None)
        return item

    semantic_nodes = [strip_ui_styles(n) for n in nodes]
    semantic_edges = [strip_ui_styles(e) for e in edges]

    return {
        "nodes": semantic_nodes,
        "edges": semantic_edges,
        "total_nodes": len(semantic_nodes),
        "total_edges": len(semantic_edges)
    }


def build_pivot_expansion_nodes_and_edges(
    node_id: str,
    pivot_type: Optional[str] = None,
    pivot_value: Optional[str] = None,
    current_node_ids: Optional[List[str]] = None,
    audit_mode: bool = True
) -> Dict[str, Any]:
    """
    Executes multi-hop link expansion from an arbitrary selected graph node.
    Traverses SQLite credential reuse, incident leaks, infrastructure subdomains,
    and external OSINT handles to dynamically attach new branch nodes and edges in Vis.js.
    """
    from backend.database import get_connection
    from backend.wmn_engine import enumerate_handle_wmn
    from backend.dns_recon import query_certificate_transparency

    existing = set(current_node_ids or [])
    existing.add(node_id)
    
    new_nodes: List[Dict[str, Any]] = []
    new_edges: List[Dict[str, Any]] = []

    clean_val = (pivot_value or "").strip()
    p_type = (pivot_type or "").upper()
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. EXPANSION: BREACH / INCIDENT LEAK HOP
        if node_id.startswith("leak_") or node_id.startswith("breach_") or p_type in ["BREACH", "LEAK"]:
            leak_id = None
            if node_id.startswith("leak_"):
                try:
                    leak_id = int(node_id.replace("leak_", ""))
                except Exception:
                    pass
            elif node_id.startswith("breach_"):
                try:
                    leak_id = int(node_id.replace("breach_", ""))
                except Exception:
                    pass

            if not leak_id and clean_val:
                cur.execute("SELECT id FROM leaks WHERE leak_name LIKE ? LIMIT 1", (f"%{clean_val}%",))
                row = cur.fetchone()
                if row:
                    leak_id = row["id"]

            if leak_id:
                cur.execute("""
                    SELECT c.id as cred_id, c.username_or_email, c.plaintext_password, c.password_hash,
                           e.id as emp_id, e.full_name, e.corporate_email, e.job_title
                    FROM credentials c
                    LEFT JOIN employees e ON c.employee_id = e.id
                    WHERE c.leak_id = ?
                    LIMIT 8
                """, (leak_id,))
                for r in cur.fetchall():
                    target_id = f"emp_{r['emp_id']}" if r["emp_id"] else f"lateral_cred_{r['cred_id']}"
                    if target_id not in existing:
                        existing.add(target_id)
                        name_display = mask_name(r["full_name"] or "Compromised Account", audit_mode)
                        email_display = mask_email(r["username_or_email"], audit_mode)
                        
                        new_nodes.append({
                            "id": target_id,
                            "label": f"[SPILLOVER TARGET]\n{name_display}\n{email_display}",
                            "title": f"Lateral Pivot: Compromised in same leak incident.\nAccount: {email_display}",
                            "group": "correlated_identity",
                            "data": {
                                "type": "CORRELATED_IDENTITY",
                                "can_pivot": True,
                                "pivot_type": "EMAIL",
                                "pivot_value": r["username_or_email"],
                                "name": r["full_name"] or "Lateral Subject"
                            }
                        })
                        new_edges.append({
                            "from": node_id,
                            "to": target_id,
                            "label": "INCIDENT VICTIM",
                            "arrows": "to",
                            "category": "breaches"
                        })

        # 2. EXPANSION: PASSWORD / HASH LATERAL REUSE HOP
        elif p_type in ["HASH", "PASSWORD"] or node_id.startswith("cred_"):
            hash_or_pass = clean_val
            if not hash_or_pass and node_id.startswith("cred_"):
                try:
                    c_id = int(node_id.replace("cred_", ""))
                    cur.execute("SELECT plaintext_password, password_hash FROM credentials WHERE id = ?", (c_id,))
                    row = cur.fetchone()
                    if row:
                        hash_or_pass = row["password_hash"] or row["plaintext_password"]
                except Exception:
                    pass

            if hash_or_pass:
                cur.execute("""
                    SELECT c.id as cred_id, c.username_or_email, c.plaintext_password,
                           l.id as leak_id, l.leak_name, l.severity,
                           e.id as emp_id, e.full_name, e.corporate_email
                    FROM credentials c
                    JOIN leaks l ON c.leak_id = l.id
                    LEFT JOIN employees e ON c.employee_id = e.id
                    WHERE c.password_hash = ? OR c.plaintext_password = ?
                    LIMIT 8
                """, (hash_or_pass, hash_or_pass))
                for r in cur.fetchall():
                    cand_id = f"reuse_leak_{r['leak_id']}_{r['cred_id']}"
                    if cand_id not in existing:
                        existing.add(cand_id)
                        acc_masked = mask_email(r["username_or_email"], audit_mode)
                        new_nodes.append({
                            "id": cand_id,
                            "label": f"[LATERAL REUSE]\n{r['leak_name']}\n{acc_masked}",
                            "title": f"Lateral Credential Reuse: Same password found in {r['leak_name']} for {acc_masked}",
                            "group": "stealer" if "stealer" in r["leak_name"].lower() else "breach",
                            "data": {
                                "type": "BREACH",
                                "can_pivot": True,
                                "pivot_type": "EMAIL",
                                "pivot_value": r["username_or_email"],
                                "leak_name": r["leak_name"]
                            }
                        })
                        new_edges.append({
                            "from": node_id,
                            "to": cand_id,
                            "label": "IDENTICAL SECRET REUSE",
                            "arrows": "to;from",
                            "category": "breaches"
                        })

        # 3. EXPANSION: DOMAIN / INFRASTRUCTURE HOP
        elif p_type == "DOMAIN" or node_id.startswith("domain_"):
            domain = clean_val or node_id.replace("domain_", "")
            subdomains = query_certificate_transparency(domain, timeout=3.0, max_subdomains=6)
            for sub in subdomains:
                sub_id = f"sub_{sub['subdomain'].replace('.', '_')}"
                if sub_id not in existing:
                    existing.add(sub_id)
                    new_nodes.append({
                        "id": sub_id,
                        "label": f"[{sub['prefix'].upper()}]\n{sub['subdomain']}",
                        "title": f"Infrastructure Asset: {sub['category']} ({sub['subdomain']})\nIssuer: {sub.get('issuer', 'N/A')}",
                        "group": "subdomain",
                        "data": {
                            "type": "INFRASTRUCTURE",
                            "can_pivot": True,
                            "pivot_type": "DOMAIN",
                            "pivot_value": sub["subdomain"],
                            "category": sub["category"]
                        }
                    })
                    new_edges.append({
                        "from": node_id,
                        "to": sub_id,
                        "label": "DNS SUBDOMAIN",
                        "arrows": "to",
                        "category": "domain"
                    })

        # 4. EXPANSION: HANDLE / IDENTITY WMN HOP
        elif p_type in ["HANDLE", "USERNAME", "ACCOUNT"] or node_id.startswith("pivot_"):
            handle = clean_val
            if not handle and "@" in clean_val:
                handle = clean_val.split("@")[0]
            if not handle:
                handle = node_id.replace("pivot_", "").replace("acc_", "")
            
            clean_handle = handle.lstrip("@").strip()
            if clean_handle:
                wmn_res = enumerate_handle_wmn(clean_handle, max_sites=25, priority_only=True)
                for match in wmn_res.get("matches", [])[:6]:
                    wmn_node_id = f"wmn_{match['platform'].lower().replace(' ', '_')}_{clean_handle}"
                    if wmn_node_id not in existing:
                        existing.add(wmn_node_id)
                        new_nodes.append({
                            "id": wmn_node_id,
                            "label": f"[{match['platform'].upper()}]\n@{clean_handle}",
                            "title": f"Live Platform Profile: Confirmed registration on {match['platform']}\nURL: {match['url']}",
                            "group": "pivot_account",
                            "data": {
                                "type": "PUBLIC_ACCOUNT",
                                "can_pivot": True,
                                "pivot_type": "URL",
                                "pivot_value": match["url"],
                                "platform": match["platform"],
                                "handle": clean_handle
                            }
                        })
                        new_edges.append({
                            "from": node_id,
                            "to": wmn_node_id,
                            "label": "CONFIRMED PROFILE",
                            "arrows": "to",
                            "category": "accounts"
                        })

        # 5. EXPANSION: GENERAL IDENTITY / EMAIL HOP (Cross-Correlation Fallback)
        else:
            term = clean_val or node_id
            cur.execute("""
                SELECT c.id as cred_id, c.username_or_email, l.id as leak_id, l.leak_name
                FROM credentials c
                JOIN leaks l ON c.leak_id = l.id
                WHERE c.username_or_email LIKE ? OR l.leak_name LIKE ?
                LIMIT 5
            """, (f"%{term}%", f"%{term}%"))
            for r in cur.fetchall():
                gen_id = f"gen_link_{r['cred_id']}_{r['leak_id']}"
                if gen_id not in existing:
                    existing.add(gen_id)
                    new_nodes.append({
                        "id": gen_id,
                        "label": f"[SPILLOVER LINK]\n{r['leak_name']}\n{mask_email(r['username_or_email'], audit_mode)}",
                        "title": f"Incident Association: {r['leak_name']}",
                        "group": "breach",
                        "data": {
                            "type": "BREACH",
                            "can_pivot": True,
                            "pivot_type": "EMAIL",
                            "pivot_value": r["username_or_email"]
                        }
                    })
                    new_edges.append({
                        "from": node_id,
                        "to": gen_id,
                        "label": "CORRELATED LINK",
                        "arrows": "to",
                        "category": "breaches"
                    })

    except Exception as e:
        print(f"[!] Error expanding pivot node {node_id}: {e}")
    finally:
        if conn:
            conn.close()

    return {
        "node_id": node_id,
        "pivot_type": p_type,
        "pivot_value": clean_val,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "expansion_count": len(new_nodes)
    }

