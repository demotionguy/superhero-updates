#!/usr/bin/env python3
"""
SUPERHERO — FIELD PACKS + ROZ KA SEEKH-LAKSHYA.

Hy ke "skill" ka matlab bade kshetra hain (Doctor, Engineer, Developer...).
Ek din me poora profession seekhna mumkin NAHI — isliye design ye hai:

- Har FIELD ke andar topics ka ek NAKSHA (index) hota hai: buniyaad se
  gehraai ki ore kram me lage topics.
- ROZ KA LAKSHYA: har din 15-20 naye chhote topics gyaan-yaad me —
  roz thoda, har field dheere-dheere gehra. Diary/Fields me ginati
  dikhti hai: "Aaj ki seekh: X / 15-20".
- Seekhna = padhna + apne shabdon me note (research.py wala tareeka).
  Internet SIRF tab, jab Hy ne roz-seekhna chalu kiya ho (uska diya
  hua sthaayi aadesh, kabhi bhi band ho sakta hai), aur sirf padhne ko.
- KAAM KE SAMAY PAHUNCH, STORE NAHI: bada kaam aaye to pehle
  gyaan-yaad/skills, phir zaroorat par usi samay padhkar istemal.
  GitHub/code par LICENSE ki seema lazmi — sirf ijaazat wala istemal.
- Sab kuch Creator Suraksha Lock + permission lock ke neeche hai.
"""

import json
import os
from datetime import date

FIELDS_FILE = "fields.json"
TARGET_MIN = 15
TARGET_MAX = 20

# Hy ke pehle teen bade kshetra — har ek ka buniyaad->gehraai naksha.
# (Doctor pack sirf GYAN hai — ilaaj ki salah dena iska kaam nahi.)
SEED_FIELDS = {
    "Doctor": [
        "sharir ki buniyaadi banawat", "dil aur khoon ka daura", "saans tantra",
        "paachan tantra", "dimaag aur nas tantra", "haddi aur manspeshi tantra",
        "rog-pratirodhak shakti", "aam sankraman kaise failte hain", "bukhaar ke kaaran",
        "diabetes ki samajh", "blood pressure ki samajh", "poshan ke siddhant",
        "vaccine kaise kaam karti hai", "prathmik upchaar (first aid)", "CPR ki buniyaad",
        "dawaaiyon ki aam shreniyaan", "lab report padhne ki samajh", "neend aur swasthya",
    ],
    "Engineer": [
        "map-jokh aur ikaiyaan", "bal aur dabav", "bijli ki buniyaad (voltage-current)",
        "circuit ki samajh", "machine aur gear", "motor kaise ghumti hai",
        "thermodynamics ki buniyaad", "material ki taakat", "bhawan-pul par bojh",
        "sensor kya hota hai", "signal aur data", "urja ke roop aur badlav",
        "technical drawing padhna", "map aur scale ki samajh", "suraksha gunank (safety factor)",
        "saral robotics ki samajh",
    ],
    "Developer": [
        "computer kaise kaam karta hai", "code kya hota hai", "variable aur data type",
        "shartein aur loop", "function kya hai", "data structure ki buniyaad",
        "file aur folder system", "internet kaise chalta hai (HTTP)", "website ke hisse (HTML-CSS-JS)",
        "Python ki buniyaad", "database kya hai", "API kya hai", "Git aur version control",
        "bug dhoondhna aur theek karna", "testing ki samajh", "open source license ki samajh",
        "password aur hash (suraksha ki buniyaad)", "app publish kaise hoti hai",
    ],
}


def _fpath(memory_root):
    return os.path.join(memory_root, FIELDS_FILE)


def load_fields(memory_root):
    try:
        with open(_fpath(memory_root), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("fields"):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    data = {"fields": {name: {"topics": list(topics), "learned": {}}
                       for name, topics in SEED_FIELDS.items()}}
    save_fields(memory_root, data)
    return data


def save_fields(memory_root, data):
    tmp = _fpath(memory_root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _fpath(memory_root))


def add_field(memory_root, name, topics=None):
    data = load_fields(memory_root)
    name = name.strip()[:60]
    if name in data["fields"]:
        return False, f"Field “{name}” pehle se hai."
    data["fields"][name] = {"topics": list(topics or []), "learned": {}}
    save_fields(memory_root, data)
    return True, f"Naya field jud gaya: “{name}” ({len(topics or [])} topics ke naksh ke saath)."


def set_topics(memory_root, field, topics):
    data = load_fields(memory_root)
    if field not in data["fields"]:
        return False, f"Field “{field}” mila nahi."
    data["fields"][field]["topics"] = [t.strip() for t in topics if t.strip()]
    save_fields(memory_root, data)
    return True, f"“{field}” ka naksha taiyaar: {len(data['fields'][field]['topics'])} topics."


def progress(memory_root):
    """Har field: kul topics, kitne seekhe, kitne baki."""
    data = load_fields(memory_root)
    out = []
    for name, pack in data["fields"].items():
        topics = pack.get("topics", [])
        learned = pack.get("learned", {})
        done = [t for t in topics if t in learned]
        out.append({"field": name, "total": len(topics), "learned": len(done),
                    "remaining": len(topics) - len(done),
                    "next_topic": next((t for t in topics if t not in learned), None)})
    return out


def todays_count(memory_root, knowledge_list, skills_list=None):
    """Aaj gyaan-yaad me kitne naye topics jude (+ nayi skills)."""
    today = str(date.today())
    n = sum(1 for k in knowledge_list if k.get("date") == today)
    if skills_list:
        n += sum(1 for s in skills_list if s.get("learned_on") == today)
    return n


def _next_topics(memory_root, want):
    """Sab fields se bari-bari agle anseekhe topics (round-robin)."""
    data = load_fields(memory_root)
    picks = []
    names = list(data["fields"].keys())
    idx = {n: 0 for n in names}
    topics_of = {n: data["fields"][n].get("topics", []) for n in names}
    learned_of = {n: data["fields"][n].get("learned", {}) for n in names}
    while len(picks) < want:
        progressed = False
        for n in names:
            while idx[n] < len(topics_of[n]) and topics_of[n][idx[n]] in learned_of[n]:
                idx[n] += 1
            if idx[n] < len(topics_of[n]):
                picks.append((n, topics_of[n][idx[n]]))
                idx[n] += 1
                progressed = True
                if len(picks) >= want:
                    break
        if not progressed:
            break
    return picks


def run_daily_cycle(memory_root, brain, search_fn, research_fn, diary_log=None,
                    count_now=0, target_min=TARGET_MIN, target_max=TARGET_MAX):
    """Roz ka seekh-cycle: lakshya tak field-topics padh + note karo.
    research_fn(topic, field=...) -> (text, from_memory). Internet ka
    istemal is function ke bahar ke gate (Hy ka chalu/band) se hota hai."""
    need = max(0, min(target_max, target_min) - count_now)
    if need == 0:
        return {"learned_now": 0, "total_today": count_now,
                "msg": f"Aaj ka lakshya pehle se pura hai ({count_now}/{target_min}-{target_max})."}
    picks = _next_topics(memory_root, need)
    if not picks:
        return {"learned_now": 0, "total_today": count_now,
                "msg": "Saare fields ke saare topics seekhe ja chuke hain — naya field ya naye topics jodo."}
    data = load_fields(memory_root)
    done = 0
    for field, topic in picks:
        try:
            _txt, from_mem = research_fn(f"{field}: {topic}", field=field)
        except Exception:
            continue
        data["fields"][field]["learned"][topic] = str(date.today())
        done += 1
    if done:
        save_fields(memory_root, data)
    total = count_now + done
    if diary_log:
        diary_log("seekh", f"Aaj ki seekh: {done} naye field-topics seekhe — kul aaj {total} / lakshya {target_min}-{target_max}.")
    return {"learned_now": done, "total_today": total,
            "msg": f"Is chakkar me {done} naye topics seekhe. Aaj kul: {total} / {target_min}-{target_max}."}
