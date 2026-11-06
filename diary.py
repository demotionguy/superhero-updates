#!/usr/bin/env python3
"""
SUPERHERO — SEEKHNE KI DIARY.

Superhero ne kab, kya seekha — sab ek jagah, tareekh ke hisaab se,
hamesha ke liye. स्त्रोत (sab uski apni memory ke andar):
- memory/self_learned.jsonl  -> khud seekhe tathya (tareekh ke saath)
- memory/skills/*/skill.json -> seekhi skills (learned_on)
- memory/learned_tasks.json  -> seekhe hue kaam (learned_on)
- memory/learning_log.jsonl  -> practice/dohraai aur khaas seekh-ghatnayein
Diary sirf PADHTI hai — kuch mitati ya badalti nahi (never-forget).
"""

import json
import os
from datetime import date


def _read_jsonl(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
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


def log_event(memory_root, kind, text):
    """Ek seekh-ghatna learning log me hamesha ke liye jodo."""
    try:
        with open(os.path.join(memory_root, "learning_log.jsonl"),
                  "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": str(date.today()), "kind": kind,
                                "text": text}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def build_diary(memory_root):
    """Tareekh -> [ {kind, text} ] — nayi tareekh pehle."""
    days = {}

    def add(day, kind, text):
        if day and text:
            days.setdefault(str(day), []).append({"kind": kind, "text": text})

    for rec in _read_jsonl(os.path.join(memory_root, "self_learned.jsonl")):
        add(rec.get("date"), "tathya", f"Khud seekha: {rec.get('fact', '')}")
    for rec in _read_jsonl(os.path.join(memory_root, "learning_log.jsonl")):
        add(rec.get("date"), rec.get("kind", "seekh"), rec.get("text", ""))

    skills_root = os.path.join(memory_root, "skills")
    if os.path.isdir(skills_root):
        for slug in sorted(os.listdir(skills_root)):
            try:
                with open(os.path.join(skills_root, slug, "skill.json"),
                          "r", encoding="utf-8") as f:
                    meta = json.load(f)
                add(meta.get("learned_on"), "skill",
                    f"Skill seekhi: {meta.get('name', slug)}"
                    f" (istemal {meta.get('uses', 0)} baar, dohraai {meta.get('practised', 0)} baar)")
            except (OSError, json.JSONDecodeError):
                continue
    try:
        with open(os.path.join(memory_root, "learned_tasks.json"),
                  "r", encoding="utf-8") as f:
            for t in json.load(f).get("tasks", []):
                add(t.get("learned_on"), "kaam",
                    f"Kaam seekha: {t.get('name', '')}")
    except (OSError, json.JSONDecodeError):
        pass
    return dict(sorted(days.items(), reverse=True))


def diary_text(memory_root, max_days=7, max_items_per_day=6):
    """App me dikhane layak saaf text roop."""
    days = build_diary(memory_root)
    if not days:
        return "Abhi diary khaali hai — Superhero jaise-jaise seekhega, sab yahan dikhega."
    lines = []
    for day in list(days)[:max_days]:
        lines.append(f"📅 {day}")
        for item in days[day][:max_items_per_day]:
            lines.append(f"• {item['text']}")
    return "\n".join(lines)
