import re
from typing import Optional, Dict, Any, List

def is_audit_active(audit_mode: Any = True) -> bool:
    return bool(audit_mode)

def mask_email(email: Optional[str], audit_mode: bool = True) -> str:
    if not email:
        return ""
    if is_audit_active(audit_mode):
        return email
    email = email.strip()
    if "@" not in email:
        return mask_text(email, audit_mode=False)
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "*"
    else:
        # Handle compound names like alice.smith -> a***e.s***h
        if "." in local_part:
            parts = local_part.split(".")
            masked_parts = []
            for p in parts:
                if len(p) <= 2:
                    masked_parts.append(p[0] + "*")
                else:
                    masked_parts.append(p[0] + "*" * (len(p) - 2) + p[-1])
            masked_local = ".".join(masked_parts)
        else:
            masked_local = local_part[0] + "*" * (len(local_part) - 2) + local_part[-1]
    return f"{masked_local}@{domain}"

def mask_name(name: Optional[str], audit_mode: bool = True) -> str:
    if not name:
        return ""
    if is_audit_active(audit_mode):
        return name
    parts = name.strip().split()
    masked_parts = []
    for part in parts:
        if len(part) <= 2:
            masked_parts.append(part[0] + "*")
        else:
            masked_parts.append(part[0] + "*" * (len(part) - 2) + part[-1])
    return " ".join(masked_parts)

def mask_password(password: Optional[str], audit_mode: bool = True) -> str:
    if not password:
        return ""
    if is_audit_active(audit_mode):
        return password
    pwd = str(password)
    # Detect trailing year / digits or special characters to preserve pattern context (e.g. S*****2024!)
    match = re.search(r'([0-9!@#$%^&*()_+\-=\[\]{};:\'",.<>?]+)$', pwd)
    if match and match.start() > 1:
        prefix = pwd[:match.start()]
        suffix = match.group(1)
        masked_prefix = prefix[0] + "*" * (len(prefix) - 1)
        return masked_prefix + suffix
    
    if len(pwd) <= 3:
        return pwd[0] + "*" * (len(pwd) - 1)
    return pwd[0] + "*" * (len(pwd) - 2) + pwd[-1]

def mask_phone(phone: Optional[str], audit_mode: bool = True) -> str:
    if not phone:
        return ""
    if is_audit_active(audit_mode):
        return phone
    # Keep country code if present, mask middle digits
    cleaned = phone.strip()
    if len(cleaned) < 6:
        return cleaned[:2] + "****"
    # Mask central digits while preserving spacing and last 2 digits
    # Example: "+48 601 234 567" -> "+48 60* *** *67"
    digits = [c for c in cleaned if c.isdigit()]
    if len(digits) >= 6:
        keep_start = 3
        keep_end = 2
        masked_digits_count = len(digits) - keep_start - keep_end
        out = []
        d_idx = 0
        for c in cleaned:
            if c.isdigit():
                if d_idx < keep_start or d_idx >= (len(digits) - keep_end):
                    out.append(c)
                else:
                    out.append("*")
                d_idx += 1
            else:
                out.append(c)
        return "".join(out)
    return cleaned[:3] + "****" + cleaned[-2:]

def mask_address(address: Optional[str], audit_mode: bool = True) -> str:
    if not address:
        return ""
    if is_audit_active(audit_mode):
        return address
    # Example: "ul. Mokotowska 45 m. 12" -> "ul. M*********a **/**"
    words = address.strip().split()
    masked_words = []
    for w in words:
        if w.lower() in ["ul.", "al.", "pl.", "os.", "st.", "ave.", "street", "road", "m."]:
            masked_words.append(w)
        elif re.match(r'^\d+([/\-a-zA-Z\d]*)$', w):
            masked_words.append("*" * len(w))
        elif len(w) > 2:
            masked_words.append(w[0] + "*" * (len(w) - 2) + w[-1])
        else:
            masked_words.append("*" * len(w))
    return " ".join(masked_words)

def mask_city(city: Optional[str], audit_mode: bool = True) -> str:
    if not city:
        return ""
    if is_audit_active(audit_mode):
        return city
    c = city.strip()
    if len(c) <= 3:
        return c[0] + "**"
    return c[0] + "*" * (len(c) - 2) + c[-1]

def mask_text(text: Optional[str], audit_mode: bool = True) -> str:
    if not text:
        return ""
    if is_audit_active(audit_mode):
        return text
    t = text.strip()
    if len(t) <= 3:
        return t[0] + "*"
    return t[0] + "*" * (len(t) - 2) + t[-1]

def mask_pivot_value(pivot_type: str, pivot_value: str, audit_mode: bool = True) -> str:
    if is_audit_active(audit_mode):
        return pivot_value
    ptype = pivot_type.upper()
    if "EMAIL" in ptype:
        return mask_email(pivot_value, audit_mode=False)
    elif "PHONE" in ptype:
        return mask_phone(pivot_value, audit_mode=False)
    elif "IP" in ptype:
        parts = pivot_value.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.**"
        return mask_text(pivot_value, audit_mode=False)
    elif "HWID" in ptype or "MACHINE" in ptype:
        if "-" in pivot_value:
            parts = pivot_value.split("-")
            return parts[0] + "-******" + parts[-1][-1:]
        return mask_text(pivot_value, audit_mode=False)
    return mask_text(pivot_value, audit_mode=False)

