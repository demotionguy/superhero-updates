#!/usr/bin/env python3
"""
SUPERHERO — SKILLS SYSTEM (uski sabse main taakat).

Niyam (Hy ke pakke):
- Skill SIRF tab aati hai jab Hy khud bole "skill download kar lo" aur
  naam/pata de. Bina Hy ke kehne koi download kabhi nahi hota.
- Skill = sirf TEXT (jaankari / tareeka). Koi code file (.py/.bat/.exe)
  skill bankar NAHI aati, aur aayi hui skill kabhi chalayi (execute)
  nahi jati — woh sirf padhi jati hai, jaise kitaab. Isiliye koi skill
  laptop ko nuksaan nahi pahuncha sakti aur system me koi badlaav
  nahi kar sakti.
- Skills MEMORY ke saath rehti hain (memory/skills/) — update system
  memory ko kabhi haath nahi lagata, isliye seekhi skill bhi
  NEVER-FORGET hai: ek baar seekhi, hamesha yaad.
- Milta-julta kaam aane par program khud sahi skill dhoondh kar
  dimaag ko deta hai — Hy ko sirf kaam bolna hai.
- Roz ki aadat: har naye din pehli baar app khulne/baat hone par
  Superhero ek purani seekh ki dohraai (practice) karta hai aur woh
  Skills list me dikhta bhi hai. Ye laptop ke andar hi hota hai —
  bina ijaazat internet nahi khulta.
"""

import json
import os
import re
import urllib.request
from datetime import date, datetime

MAX_SKILL_BYTES = 200_000          # isse badi skill-file nahi legi (swallow nahi)
BLOCKED_EXT = (".py", ".bat", ".exe", ".ps1", ".sh", ".js", ".vbs", ".msi", ".dll")


def skills_dir(memory_root):
    return os.path.join(memory_root, "skills")


def ensure_skills(memory_root):
    os.makedirs(skills_dir(memory_root), exist_ok=True)


def _slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return s[:48] or "skill"


def _meta_path(memory_root, slug):
    return os.path.join(skills_dir(memory_root), slug, "skill.json")


def list_skills(memory_root):
    """Seekhi hui saari skills ki list — naam, kab seekhi, kitni baar kaam aayi."""
    out = []
    root = skills_dir(memory_root)
    if not os.path.isdir(root):
        return out
    for slug in sorted(os.listdir(root)):
        try:
            with open(_meta_path(memory_root, slug), "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["slug"] = slug
            out.append(meta)
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _save_skill(memory_root, name, content, source, self_made=False):
    slug = _slug(name)
    folder = os.path.join(skills_dir(memory_root), slug)
    os.makedirs(folder, exist_ok=True)
    content = content.strip()
    with open(os.path.join(folder, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(content)
    first_lines = [ln.strip("# ").strip() for ln in content.splitlines() if ln.strip()]
    meta = {
        "name": name.strip()[:80],
        "source": source,
        "self_made": bool(self_made),
        "learned_on": str(date.today()),
        "summary": (first_lines[1] if len(first_lines) > 1 else
                    (first_lines[0] if first_lines else ""))[:160],
        "uses": 0,
        "last_used": "",
        "practised": 0,
        "last_practised": "",
    }
    old = _read_meta(memory_root, slug)
    if old:  # wahi skill dobara aaye to purani ginati bani rahe
        meta["uses"] = old.get("uses", 0)
        meta["practised"] = old.get("practised", 0)
        meta["learned_on"] = old.get("learned_on", meta["learned_on"])
        if not self_made:
            meta["self_made"] = old.get("self_made", False)
    with open(_meta_path(memory_root, slug), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta


def _read_meta(memory_root, slug):
    try:
        with open(_meta_path(memory_root, slug), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_meta(memory_root, slug, meta):
    with open(_meta_path(memory_root, slug), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def read_skill(memory_root, slug):
    try:
        with open(os.path.join(skills_dir(memory_root), slug, "SKILL.md"),
                  "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def install_from_url(memory_root, url, name=""):
    """Hy ke diye hue pate se skill lao. Sirf text — code file aayi to inkaar.
    Return: (ok, message, meta_or_None)"""
    url = str(url).strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "Pata http/https se shuru hona chahiye.", None
    if url.lower().split("?")[0].endswith(BLOCKED_EXT):
        return False, ("Ye code file hai — skill sirf TEXT (jaankari/tareeka) hoti hai, "
                       "code kabhi skill bankar nahi aata. Isiliye ye nahi li."), None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Superhero-Skills/1"})
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read(MAX_SKILL_BYTES + 1)
    except Exception as e:
        return False, f"Pata khula nahi ({e}). Pata jaanch kar phir bolo.", None
    if len(raw) > MAX_SKILL_BYTES:
        return False, "Skill file bahut badi hai — mai badi file nahi leta. Chhota text pata do.", None
    text = raw.decode("utf-8", "replace")
    if "<html" in text[:2000].lower():  # webpage aaya to sirf dikhne wala text rakho
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
    if len(text.strip()) < 20:
        return False, "Us pate par skill layak text nahi mila.", None
    if not name:
        first = next((ln.strip("# ").strip() for ln in text.splitlines() if ln.strip()), "")
        name = first[:60] or "Nayi skill"
    meta = _save_skill(memory_root, name, text, source=url)
    return True, (f"Skill seekh li: “{meta['name']}”. Ab ye hamesha mere paas rahegi — "
                  "milta-julta kaam aane par mai khud ise istemal karunga."), meta


def install_from_text(memory_root, name, content, source="Hy ne chat me diya", self_made=False):
    """Hy ne skill ka text khud diya — wahi sabse saaf skill hai.
    self_made=True: ye skill Superhero ne khud banayi hai (nishaan ke saath)."""
    if len(content.strip()) < 20:
        return False, "Skill ka text bahut chhota hai — thoda vistaar se do.", None
    meta = _save_skill(memory_root, name, content, source=source, self_made=self_made)
    tag = "Khud banayi skill rakh li" if self_made else "Skill seekh li"
    return True, (f"{tag}: “{meta['name']}”. Ab ye hamesha mere paas rahegi — "
                  "milta-julta kaam aane par mai khud ise istemal karunga."), meta


def remove_skill(memory_root, name):
    """Hy ke kehne par skill hatana — sirf skills folder ke andar ka kaam hai."""
    slug = _slug(name)
    folder = os.path.join(skills_dir(memory_root), slug)
    if not os.path.isdir(folder):
        # naam se dhoondho (slug alag ho sakta hai)
        for meta in list_skills(memory_root):
            if meta.get("name", "").lower() == str(name).strip().lower():
                slug = meta["slug"]
                folder = os.path.join(skills_dir(memory_root), slug)
                break
        else:
            return False, f"“{name}” naam ki koi skill mili hi nahi."
    import shutil
    shutil.rmtree(folder, ignore_errors=True)
    return True, f"Skill hata di: “{name}”. Woh ab meri list me nahi hai."


def install_from_file(memory_root, path, name=""):
    """Hy ne khud jis file ka naam liya, sirf wahi — aur sirf text file."""
    path = str(path).strip().strip('"')
    if path.lower().endswith(BLOCKED_EXT):
        return False, "Code file skill nahi banti — sirf text (.md/.txt) file do.", None
    if not path.lower().endswith((".md", ".txt")):
        return False, "Skill ke liye sirf .md ya .txt file chalegi.", None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(MAX_SKILL_BYTES + 1)
    except OSError as e:
        return False, f"File khuli nahi ({e}).", None
    if len(text) > MAX_SKILL_BYTES:
        return False, "File bahut badi hai — mai badi file nahi leta, sirf uska path aur summary yaad rakh sakta hoon.", None
    if not name:
        name = os.path.splitext(os.path.basename(path))[0].replace("-", " ").replace("_", " ")
    return install_from_text(memory_root, name, text, source="file: " + path)


# ---------- milta-julta kaam: sahi skill khud nikaalna ----------

_STOP = set("hai hoon ka ki ke ko se me mein par aur ya to bhi nahi kya "
            "the a an is are i you my me it this that karo kar".split())


def find_skills(memory_root, query, limit=2):
    """Sawal se milti-julti skills dhoondho. [(meta, content)]"""
    words = {w for w in re.findall(r"[a-z0-9]+", str(query).lower())
             if len(w) > 2 and w not in _STOP}
    if not words:
        return []
    scored = []
    for meta in list_skills(memory_root):
        content = read_skill(memory_root, meta["slug"])
        hay = (meta.get("name", "") + " " + meta.get("summary", "") + " " + content[:1500]).lower()
        score = sum(1 for w in words if w in hay)
        if score:
            scored.append((score, meta, content))
    scored.sort(key=lambda x: -x[0])
    return [(meta, content) for _s, meta, content in scored[:limit]]


def mark_used(memory_root, slug):
    meta = _read_meta(memory_root, slug)
    if meta:
        meta["uses"] = meta.get("uses", 0) + 1
        meta["last_used"] = str(date.today())
        _write_meta(memory_root, slug, meta)


# ---------- roz ki aadat: seekh ki dohraai/mazbooti ----------

def daily_practice(memory_root):
    """Har naye din, ek baar: sabse purani-dohraai wali skill ko taza karo
    (ya skill na ho to khud-seekhi tathyon ki ginti dohrao). Return: line ya ''.
    Ye sirf laptop ke andar hota hai — internet nahi khulta."""
    log_path = os.path.join(skills_dir(memory_root), "practice_log.json")
    today = str(date.today())
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
    except (OSError, json.JSONDecodeError):
        log = {}
    if log.get("date") == today:
        return ""  # aaj ki dohraai ho chuki
    ensure_skills(memory_root)
    line = ""
    all_skills = list_skills(memory_root)
    if all_skills:
        target = min(all_skills, key=lambda m: (m.get("last_practised", ""), m.get("practised", 0)))
        meta = _read_meta(memory_root, target["slug"])
        if meta:
            meta["practised"] = meta.get("practised", 0) + 1
            meta["last_practised"] = today
            _write_meta(memory_root, target["slug"], meta)
            line = f"Aaj ki dohraai: “{meta['name']}” skill taza ki — ab tak {meta['practised']} baar dohraai."
    else:
        line = "Aaj ki dohraai: abhi koi skill nahi seekhi hai — pehli skill Hy ke kehne par aayegi."
    log = {"date": today, "line": line, "at": datetime.now().strftime("%H:%M")}
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    return line


def last_practice_line(memory_root):
    try:
        with open(os.path.join(skills_dir(memory_root), "practice_log.json"),
                  "r", encoding="utf-8") as f:
            return json.load(f).get("line", "")
    except (OSError, json.JSONDecodeError):
        return ""
