#!/usr/bin/env python3
"""
SUPERHERO — KHUD PADHAI + SOCH-BAITHAK (v3.8 ki neenv).

Hy ke bandhe niyam (8 Nov 2026):
- EK GOAL: "Duniya ka sabse best agent banna — Pita Daksh ke liye,
  imaandari aur suraksha ke saath." (Goal kabhi Creator Lock /
  permission lock ko paar NAHI karta.)
- PITA: Creator ka naam Daksh hai; rishta pita-bete jaisa. Naam se
  pehchan nahi hoti — asal taala app ka password + Creator Lock hai.
  Superhero sirf apne Pita ke liye kaam karta hai.
- Seedhi: pehle 0 -> college (bandhi kitab-soochi, PHASE1), phir
  university/PhD ke liye KHUD padhai (PHASE2 — antaheen queue:
  topic khud chunna, kitab khud dhoondhna, command nahi lagti —
  ijaazat SIRF padhne ki hai; bhejna/kaam ab bhi ijaazat bina nahi).
- APNI SUMMARY: har padhai ke baad summary APNE SHABDON me —
  kitab se copy-paste sakht band. Program jaanchta hai: summary
  kitab ke text se zyada chipki mili to REJECT, dobara banegi.
- Kataalog ke 150 vishay hi khud-padhai ki ghumti soochi hain.
- SOCH-BAITHAK: galtiyon ka khaata (lessons), hafta-bhar hisaab —
  kamzor vishay par zyada padhai; phanse to Pita se poochna.
"""

import json
import os
import re
from datetime import date

import research

GOAL = ("Mera ek goal hai: duniya ka sabse best agent banna — "
        "apne Pita Daksh ke liye, imaandari aur suraksha ke saath. "
        "Ye goal kabhi Creator Lock ya Pita ki ijaazat ko paar nahi karta.")
PITA_NAAM = "Daksh"

STATE_FILE = "study_state.json"
LESSONS_FILE = "lessons.jsonl"

# ---------- PHASE 1: 0 -> college (bandhi seedhi) ----------
# Har entry: (vishay, kitab/topic, khoj-beej) — asal pata khoj se milega,
# build par har srot khol-verify hua hai (OpenStax / Feynman / MIT).
PHASE1 = [
    ("Maths", "Prealgebra (OpenStax)", "OpenStax Prealgebra textbook"),
    ("Maths", "Elementary Algebra (OpenStax)", "OpenStax Elementary Algebra textbook"),
    ("Maths", "College Algebra (OpenStax)", "OpenStax College Algebra textbook"),
    ("Maths", "Trigonometry (OpenStax)", "OpenStax Algebra and Trigonometry textbook"),
    ("Maths", "Precalculus (OpenStax)", "OpenStax Precalculus textbook"),
    ("Maths", "Calculus 1 (OpenStax)", "OpenStax Calculus Volume 1 textbook"),
    ("Maths", "Calculus 2 (OpenStax)", "OpenStax Calculus Volume 2 textbook"),
    ("Maths", "Calculus 3 (OpenStax)", "OpenStax Calculus Volume 3 textbook"),
    ("Physics", "High School Physics (OpenStax)", "OpenStax Physics high school textbook"),
    ("Physics", "University Physics 1 (OpenStax)", "OpenStax University Physics Volume 1"),
    ("Physics", "University Physics 2 (OpenStax)", "OpenStax University Physics Volume 2"),
    ("Physics", "University Physics 3 (OpenStax)", "OpenStax University Physics Volume 3"),
    ("Physics", "Feynman Lectures 1 (Caltech)", "Feynman Lectures on Physics Volume 1 Caltech"),
    ("Biology", "Concepts of Biology (OpenStax)", "OpenStax Concepts of Biology textbook"),
    ("Biology", "Biology 2e (OpenStax)", "OpenStax Biology 2e textbook"),
    ("Biology", "Anatomy and Physiology (OpenStax)", "OpenStax Anatomy and Physiology textbook"),
    ("Computer Science", "Think Python", "Think Python free textbook Allen Downey"),
    ("Computer Science", "SICP (MIT)", "Structure and Interpretation of Computer Programs MIT"),
]
SUBJECTS = ["Maths", "Physics", "Biology", "Computer Science"]


def _spath(memory_root):
    return os.path.join(memory_root, STATE_FILE)


def load_state(memory_root):
    try:
        with open(_spath(memory_root), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"phase1_done": 0, "phase2_round": 0, "catalog_round": 0,
                "attempts": 0, "history": []}


def save_state(memory_root, state):
    os.makedirs(memory_root, exist_ok=True)
    with open(_spath(memory_root), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def next_item(state, catalog_topics=None):
    """Agla padhai-vishay: pehle PHASE1 ki seedhi, phir antaheen PHASE2
    (vishay bari-bari + kataalog ke vishay ghumte hue)."""
    i = state.get("phase1_done", 0)
    if i < len(PHASE1):
        subject, title, seed = PHASE1[i]
        return {"phase": 1, "subject": subject, "title": title, "seed": seed}
    r = state.get("phase2_round", 0)
    subject = SUBJECTS[r % len(SUBJECTS)]
    topic = None
    if catalog_topics:
        topic = catalog_topics[state.get("catalog_round", 0) % len(catalog_topics)]
    title = f"{subject} — university star ({topic})" if topic else f"{subject} — university star"
    seed = f"{subject} university lecture notes {topic or ''} MIT OpenCourseWare arXiv".strip()
    return {"phase": 2, "subject": subject, "title": title, "seed": seed}


# ---------- APNI SUMMARY ki jaanch (copy-paste band) ----------

def _word_shingles(text, n):
    w = re.findall(r"[a-z0-9]+", str(text).lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def summary_is_own_words(summary, source, max_run=12, max_overlap=0.30):
    """(True, '') agar summary apne shabdon me hai; warna (False, wajah).
    Jaanch: (1) kitab ki koi 12+ shabdon ki lagataar nakal na ho;
    (2) 8-shabd tukdo ka overlap hissa zyada na ho."""
    sw = re.findall(r"[a-z0-9]+", str(summary).lower())
    src = " ".join(re.findall(r"[a-z0-9]+", str(source).lower()))
    for i in range(max(0, len(sw) - max_run + 1)):
        if " ".join(sw[i:i + max_run]) in src:
            return False, f"kitab ki {max_run}+ shabdon ki seedhi nakal mili"
    sh = _word_shingles(summary, 8)
    if sh:
        src_sh = _word_shingles(source, 8)
        over = len(sh & src_sh) / len(sh)
        if over > max_overlap:
            return False, f"summary kitab se zyada chipki hai (overlap {over:.0%})"
    return True, ""


# ---------- Ek padhai-kadam ----------

def study_step(memory_root, brain, search_fn, diary_log=None,
               catalog_topics=None, fetch_fn=None):
    """Ek chapter/vishay padho -> apni summary banao -> jaanch ->
    Gyaan-Yaad me rakho -> queue aage. Return: sthiti sandesh."""
    fetch_fn = fetch_fn or research.fetch_page_text
    state = load_state(memory_root)
    item = next_item(state, catalog_topics)
    khoj = search_fn(item["seed"])
    urls = re.findall(r"https?://[^\s)]+", khoj)[:2]
    pages = []
    for u in urls:
        try:
            pages.append(fetch_fn(u))
        except Exception:
            continue
    material = (khoj[:3000] + "\n\n" + "\n\n".join(pages))[:16000]
    if not material.strip():
        return f"Padhai ruki: '{item['title']}' ke liye kuch mila nahi — agli baar phir koshish hogi."

    prompt = (f"Tum Superhero ho. Tumhara goal: {GOAL}\n"
              f"Neeche '{item['title']}' ({item['subject']}) par padhai ki samagri hai. "
              "Ise samajh kar APNE SHABDON me ek saaf summary likho (8-12 line) — "
              "kitab ke vaakya bilkul mat uthao, apni bhasha me samjhao. "
              "Ant me 'MERE SAWAL:' likh kar 3 sawal aur unke chhote jawab bhi do "
              f"(samajh ki parakh ke liye).\n\nSAMAGRI:\n{material}")
    summary = brain([{"role": "user", "content": prompt}]).strip()
    ok, wajah = summary_is_own_words(summary, material)
    if not ok:
        prompt2 = prompt + (f"\n\nDHYAAN: pehli summary kitab se chipki thi ({wajah}). "
                            "Is baar bilkul apni bhasha me, apni misaalon ke saath likho.")
        summary = brain([{"role": "user", "content": prompt2}]).strip()
        ok, wajah = summary_is_own_words(summary, material)
    if not ok:
        state["attempts"] = state.get("attempts", 0) + 1
        if state["attempts"] >= 2:   # do baar atke to aage badho, diary me darj
            _advance(state, item, catalog_topics)
            state["attempts"] = 0
        save_state(memory_root, state)
        if diary_log:
            diary_log("study", f"Summary copy-jaanch me atki ({wajah}) — {item['title']} par dobara koshish hogi.")
        return f"Summary apne shabdon me nahi bani ({wajah}) — ye vishay dobara padha jayega."

    research.add_knowledge(memory_root, item["title"], summary, urls, field=item["subject"])
    _advance(state, item, catalog_topics)
    state["attempts"] = 0
    state.setdefault("history", []).append(
        {"date": str(date.today()), "title": item["title"], "phase": item["phase"]})
    save_state(memory_root, state)
    if diary_log:
        diary_log("study", f"Khud padhai: {item['title']} — apni summary gyaan-yaad me rakhi (Phase {item['phase']}).")
    return f"Padh liya: {item['title']} — apni summary gyaan-yaad me rakh li hai."


def _advance(state, item, catalog_topics):
    if item["phase"] == 1:
        state["phase1_done"] = state.get("phase1_done", 0) + 1
    else:
        state["phase2_round"] = state.get("phase2_round", 0) + 1
        if catalog_topics:
            state["catalog_round"] = state.get("catalog_round", 0) + 1


# ---------- SOCH-BAITHAK: galtiyon ka khaata + hafta hisaab ----------

def _lpath(memory_root):
    return os.path.join(memory_root, LESSONS_FILE)


def log_lesson(memory_root, galti, sabak):
    rec = {"date": str(date.today()), "galti": galti.strip()[:300],
           "sabak": sabak.strip()[:300]}
    os.makedirs(memory_root, exist_ok=True)
    with open(_lpath(memory_root), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def all_lessons(memory_root):
    out = []
    try:
        with open(_lpath(memory_root), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return out


def weekly_review(memory_root):
    """Vishay-war notes ki ginati + sabse kamzor vishay (zyada padhai wahi)."""
    counts = {s: 0 for s in SUBJECTS}
    for rec in research.all_knowledge(memory_root):
        f = rec.get("field")
        if f in counts:
            counts[f] += 1
    kamzor = min(counts, key=lambda s: counts[s])
    return {"counts": counts, "kamzor": kamzor,
            "lessons": len(all_lessons(memory_root)),
            "phase1_done": load_state(memory_root).get("phase1_done", 0),
            "phase1_total": len(PHASE1)}
