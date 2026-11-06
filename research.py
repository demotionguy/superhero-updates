#!/usr/bin/env python3
"""
SUPERHERO — KHUD RESEARCH + GYAAN YAAD.

Gyaani aadmi wala tareeka (poora internet store karna mumkin nahi):
  PADHO -> khaas baatein APNE SHABDON me gyaan-yaad me note karo ->
  dobara kaam aane par pehle WAHI YAAD dekho -> na mile to phir padho.

- Gyaan-yaad: memory/knowledge.jsonl — vishay, apne shabdon ke notes,
  kahan se padha (sources), tareekh. Diary me dikhta hai.
- Research: Hy vishay de to Superhero pehle khojta hai, 1-2 pate padhta
  hai (SIRF PADHNA — internet par kuch bhejna/upload karna kabhi nahi),
  samajh kar apne shabdon me natija/notes banata hai (copy-paste nahi).
- Khud skill banana: research se behtar tareeka mile to use apni skill
  ki shakl me likh kar rakh leta hai ("khud ki banayi" nishaan ke saath).
- Nayi rachna: research ke notes ek rachna-file (memory/creations/)
  bankar bhi rehte hain — notes/plan/khaaka wahi hain.
- SEEMA: Ye sab Creator Suraksha Lock aur permission lock ke ADHEEN
  hai. Internet sirf tab, jab Hy ne kaha ho (research ka aadesh khud
  Hy ki ijaazat hai — sirf padhne ke liye). Bina ijaazat na file
  khulti hai, na internet par kuch jata hai (sawal ke alawa).
"""

import json
import os
import re
import urllib.request
from datetime import date

KNOWLEDGE = "knowledge.jsonl"
MAX_PAGE_CHARS = 12000


def _kpath(memory_root):
    return os.path.join(memory_root, KNOWLEDGE)


def add_knowledge(memory_root, topic, note, sources, field=None):
    rec = {"date": str(date.today()), "topic": topic.strip()[:120],
           "note": note.strip()[:4000], "sources": sources[:4]}
    if field:
        rec["field"] = field
    with open(_kpath(memory_root), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def all_knowledge(memory_root):
    out = []
    try:
        with open(_kpath(memory_root), "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        pass
    return out


_STOP = set("hai hoon ka ki ke ko se me mein par aur ya to bhi nahi kya "
            "the a an is are i you my me it this that karo kar bare baare".split())


def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", str(text).lower())
            if len(w) > 2 and w not in _STOP}


def find_knowledge(memory_root, query, limit=3):
    """Gyaan-yaad me is vishay ki purani seekh dhoondho."""
    words = _words(query)
    if not words:
        return []
    scored = []
    for rec in all_knowledge(memory_root):
        hay = (rec.get("topic", "") + " " + rec.get("note", "")).lower()
        score = sum(1 for w in words if w in hay)
        # vishay se seedha milan sabse bhaari
        if words & _words(rec.get("topic", "")):
            score += 3
        if score >= 3:
            scored.append((score, rec))
    scored.sort(key=lambda x: -x[0])
    return [rec for _s, rec in scored[:limit]]


def fetch_page_text(url, limit=MAX_PAGE_CHARS):
    """Ek pate ka sirf dikhne wala text — SIRF PADHNA. Kuch bhejna nahi."""
    req = urllib.request.Request(url, headers={"User-Agent": "Superhero-Research/1"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read(600_000).decode("utf-8", "replace")
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()[:limit]


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:40] or "research"


def save_creation(memory_root, topic, note):
    folder = os.path.join(memory_root, "creations")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{date.today()}-{_slug(topic)}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Research: {topic}\n({date.today()} — Superhero ne khud padh kar, apne shabdon me)\n\n{note}\n")
    return path


def research(topic, brain, memory_root, search_fn, diary_log=None, make_skill_fn=None, field=None):
    """Poora research pravah. brain(text)->jawab, search_fn(topic)->khoj text.
    Return: (jawab_text, from_memory_bool)"""
    topic = topic.strip()
    # 1) PEHLE GYAAN-YAAD
    old = find_knowledge(memory_root, topic)
    if old:
        parts = [f"📚 Ye vishay meri gyaan-yaad me pehle se hai ({old[0]['date']} ko padha tha) — dobara padhne ki zaroorat nahi:"]
        for rec in old:
            parts.append(f"• {rec['topic']}: {rec['note'][:600]}")
        return "\n".join(parts), True

    # 2) PADHO (sirf padhna)
    khoj = search_fn(topic)
    urls = re.findall(r"https?://[^\s)]+", khoj)[:2]
    pages = []
    for u in urls:
        try:
            pages.append(fetch_page_text(u))
        except Exception:
            continue
    material = (khoj[:3000] + "\n\n" + "\n\n".join(pages))[:16000]
    if not material.strip():
        return "Is vishay par abhi kuch padh nahi paya — internet ya pata dekh kar phir koshish karna.", False

    # 3) SAMAJH KAR APNE SHABDON ME NOTES (copy-paste nahi)
    prompt = (f"Neeche '{topic}' par padhi hui jaankari hai. Ise samajh kar APNE SHABDON me "
              "5-8 khaas baatein (har baat 1-2 line) likho — copy-paste bilkul nahi. "
              "Agar isme koi code/tareeka mile to sirf wahi apne shabdon me samjhao jiska "
              "license istemal ki ijaazat de — code ki nakal bilkul nahi. "
              "Uske baad agar isse koi kaam ka TAREEKA (skill) banta ho to ant me "
              "'---SKILL---' likh kar skill ka naam aur uske kadam apne shabdon me do; "
              f"na banta ho to woh hissa chhod do.\n\nJAANKARI:\n{material}")
    raw = brain([{"role": "user", "content": prompt}]).strip()

    skill_part = ""
    notes = raw
    if "---SKILL---" in raw:
        notes, skill_part = raw.split("---SKILL---", 1)
        notes, skill_part = notes.strip(), skill_part.strip()

    # 4) GYAAN-YAAD + RACHNA + DIARY
    rec = add_knowledge(memory_root, topic, notes, urls, field=field)
    save_creation(memory_root, topic, notes)
    if diary_log:
        diary_log("research", f"Research kiya: {topic} — gyaan-yaad me {len(notes)} akshar ke notes rakhe.")

    out = [f"🔍 Research ho gaya: {topic}\n(Apne shabdon me — gyaan-yaad me rakh liya hai, agli baar yaad se milega.)\n", notes]

    # 5) KHUD SKILL BANANA (research ke tareeke se)
    if skill_part and make_skill_fn:
        m = re.search(r"(.{3,60})", skill_part)
        if m:
            name = m.group(1).strip(" :—-")
            ok, msg = make_skill_fn(name, "# " + name + "\n(ye skill Superhero ne khud research se banayi hai)\n\n" + skill_part)
            if ok:
                out.append(f"\n🛠️ Is research se maine khud ek skill bhi bana li hai: “{name}” — Skills list me dikhegi, Hy chahe to hata sakta hai.")
                if diary_log:
                    diary_log("skill", f"Khud skill banayi (research se): {name}")
    return "\n".join(out), False
