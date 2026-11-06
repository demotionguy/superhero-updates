#!/usr/bin/env python3
"""
SUPERHERO — APNA DIMAAG (uska apna seekhne wala hissa).

Sach, saaf shabdon me: base free model (Ollama/qwen) sirf BHASHA samajhne
wala hissa hai — uske weights yahan nahi badalte. Superhero ka "apna
dimaag" uske UPAR bani ye apni parat hai, jo 100% uski apni hai:

1. KHUD SEEKHNA — har baat-cheet me program Hy ki baaton se tathya
   (facts) aur seekhe hue kaam khud pehchan kar uski apni memory me
   jodta hai. Hy ko baar-baar "yaad rakho" bolna ya train karna nahi
   padta. Jo memory me gaya, woh NEVER-FORGET — kabhi nahi mita.
2. MEMORY RECALL — jawab se pehle program uski apni memory me se is
   baat se judi purani seekhi baatein dhoondh kar dimaag ko deta hai,
   taaki Superhero din-ba-din "apna" aur majboot hota jaye.
3. INTERNET (sirf Hy ki ijaazat se) — web search ka haath yahi hai.
   Bina ijaazat ye kabhi nahi chalta (bulane wali jagah pehle ijaazat
   ki jaanch karti hai). Search me sirf SAWAL bahar jata hai — Hy ki
   memory/yaadein laptop se KABHI bahar nahi jati.

Sab kuch sirf Python ki apni library se — koi API key nahi, koi paisa
nahi, koi token nahi.
"""

import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime

# ---------- 1) KHUD SEEKHNA: tathya pehchanna ----------

_FACT_PATTERNS = [
    # "yaad rakho (ki) X" — sabse pakka sanket
    (r"yaad rakho[\s,:-]*(?:ki\s+)?(.{3,200})", None),
    # "mera naam X hai"
    (r"\bmera naam\s+(.{2,60}?)\s+hai\b", "Hy ka naam: {0}"),
    # "mujhe X pasand hai / nahi pasand"
    (r"\bmujhe\s+(.{2,80}?)\s+(nahi\s+)?pasand hai\b", None),
    # "meri pasand X hai"
    (r"\bmeri pasand\s+(.{2,80}?)\s+hai\b", "Hy ki pasand: {0}"),
    # "main X me rehta hoon / X ka rehne wala hoon"
    (r"\bmain\s+(.{2,60}?)\s+(?:me|mein)\s+rehta hoon\b", "Hy rehta hai: {0}"),
    # "mera kaam X hai / mera business X hai"
    (r"\bmera (kaam|business|channel)\s+(.{2,80}?)\s+hai\b", "Hy ka {0}: {1}"),
    # "aaj se X" — nayi aadat/niyam
    (r"\baaj se\s+(.{3,120})", "Aaj se (Hy ne sikhaya): {0}"),
    # "mujhe X se allergy hai / mujhe X nahi khana" jesi sehat baatein
    (r"\bmujhe\s+(.{2,60}?)\s+se\s+allergy hai\b", "Hy ko allergy hai: {0}"),
]


def _clean(text):
    return re.sub(r"\s+", " ", str(text)).strip().strip(".")


def extract_facts(text):
    """Hy ke sandesh se sikhaane layak tathya pehchano. List of str."""
    low = " " + _clean(text).lower() + " "
    facts = []
    for pattern, template in _FACT_PATTERNS:
        for m in re.finditer(pattern, low):
            if template is None:
                if "yaad rakho" in pattern:
                    fact = _clean(m.group(1))
                else:  # pasand wala pattern
                    neg = " (nahi pasand)" if m.group(2) else " (pasand hai)"
                    fact = "Hy ko pasand: " + _clean(m.group(1)) + ("" if not m.group(2) else "")
                    if m.group(2):
                        fact = "Hy ko NAHI pasand: " + _clean(m.group(1))
                fact = _clean(fact)
            else:
                fact = template.format(*[_clean(g) for g in m.groups()])
            if 3 <= len(fact) <= 220 and fact not in facts:
                facts.append(fact)
    return facts


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def save_facts(facts, memory_md_path, log_path):
    """Naye tathya memory me jodo (jo pehle se hain, dobara nahi). Saved list wapas."""
    if not facts:
        return []
    try:
        existing = ""
        if os.path.exists(memory_md_path):
            with open(memory_md_path, "r", encoding="utf-8") as f:
                existing = f.read()
    except OSError:
        existing = ""
    existing_norm = _norm(existing)
    saved = []
    stamp = datetime.now().strftime("%Y-%m-%d")
    for fact in facts:
        if _norm(fact) and _norm(fact) in existing_norm:
            continue
        saved.append(fact)
    if saved:
        with open(memory_md_path, "a", encoding="utf-8") as f:
            for fact in saved:
                f.write(f"\n- ({stamp}) [khud seekha] {fact}")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                for fact in saved:
                    f.write(json.dumps({"date": stamp, "fact": fact},
                                       ensure_ascii=False) + "\n")
        except OSError:
            pass
    return saved


def detect_task(text):
    """Seekha hua kaam pehchano: 'kaam seekho: naam — steps' ya
    'har baar ... karna' ke saath diye gaye kadam. (name, [steps]) ya None."""
    cleaned = _clean(text)
    m = re.search(r"kaam seekho[\s:–—-]*(.+)", cleaned, re.IGNORECASE)
    if m:
        body = m.group(1)
        parts = re.split(r"\s+steps?\s*[:–—-]\s*|\s*[|]\s*", body, flags=re.IGNORECASE)
        name = _clean(parts[0]).strip("–—- ").strip()[:60]
        steps = []
        if len(parts) > 1:
            steps = [_clean(s) for s in re.split(r"\s*(?:,|;|\d+[.)])\s*", parts[1]) if _clean(s)]
        return (name, steps) if name else None
    # "har baar X karna" — ek-kadam wala seekha kaam
    m = re.search(r"\bhar baar\s+(.{5,120}?)(?:\.|$)", cleaned, re.IGNORECASE)
    if m:
        body = _clean(m.group(1))
        return (body[:60], [body])
    return None


# ---------- 2) MEMORY RECALL ----------

_STOP = set("hai hoon ka ki ke ko se me mein par aur ya to bhi nahi kya "
            "the a an is are i you my me it this that".split())


def recall(memory_text, tasks, query, limit=5):
    """Is baat se judi purani seekhi baatein memory se dhoondho."""
    words = {w for w in re.findall(r"[a-z0-9]+", query.lower())
             if len(w) > 2 and w not in _STOP}
    if not words:
        return ""
    scored = []
    for line in memory_text.splitlines():
        line = line.strip("- ").strip()
        if len(line) < 8:
            continue
        low = line.lower()
        score = sum(1 for w in words if w in low)
        if score:
            scored.append((score, line))
    for t in tasks or []:
        low = (t.get("name", "") + " " + " ".join(t.get("steps", []))).lower()
        score = sum(1 for w in words if w in low)
        if score:
            scored.append((score, f"Seekha kaam: {t.get('name','')} — "
                                    f"{'; '.join(t.get('steps', []))}"))
    scored.sort(key=lambda x: -x[0])
    picks = [line for _s, line in scored[:limit]]
    if not picks:
        return ""
    return "\n".join(f"- {p}" for p in picks)


# ---------- 3) INTERNET — sirf ijaazat par (bulane wala pehle jaanche) ----------

def web_search(query, count=5):
    """DuckDuckGo (bina key, bina paisa) se khoj. Return: mil-jaankari ka text.
    Sirf sawal bahar jata hai — memory kabhi nahi."""
    q = _clean(query)[:200]
    if not q:
        return "Sawal khaali hai."
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(q)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Superhero; Hy ka apna agent)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"Internet abhi mila nahi ({e}). Baad me phir koshish karna."
    results = []
    for m in re.finditer(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        link = html.unescape(m.group(1))
        title = re.sub(r"<[^>]+>", "", html.unescape(m.group(2))).strip()
        uddg = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("uddg")
        if uddg:
            link = uddg[0]
        if title:
            results.append(f"- {title}\n  {link}")
        if len(results) >= count:
            break
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.S)
    out = [f"Internet khoj: {q}"]
    for i, res in enumerate(results):
        snip = ""
        if i < len(snippets):
            snip = re.sub(r"<[^>]+>", "", html.unescape(snippets[i])).strip()
        out.append(res + (f"\n  {snip}" if snip else ""))
    if not results:
        return f"Internet par '{q}' ke liye kuch saaf nahi mila."
    return "\n".join(out)
