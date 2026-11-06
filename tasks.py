#!/usr/bin/env python3
"""
SUPERHERO — TASKS (kaam ki patti).

Do tarah ke task:
1. HY KE TASK — Hy jo kaam de, Superhero use khud pura karne ki koshish
   karta hai (apni seekhi skills/kaam ke saath). Board: memory/tasks_board.json
2. KHUD KE TASK — Superhero dheere-dheere apne chhote task KHUD banata
   hai (seekh ki dohraai, skill practice, diary sajana) — ye uska
   jeeta-jaagta hissa hai. Ye task app me DIKHTE hain.

PAKKI SEEMA (Creator Lock ke adheen):
- Khud ka banaya task bhi sirf laptop-ke-andar wali seekh/diary tak
  seemit hai.
- Jo task file / system / internet ko chhue, woh "ijaazat chahiye"
  (blocked_permission) bankar khada rahega — Hy ki ijaazat ke bina
  woh KABHI nahi chalega.
- Koi task Creator Lock ko override nahi kar sakta.
"""

import json
import os
from datetime import date, datetime

BOARD = "tasks_board.json"
MAX_BOARD = 60


def _board_path(memory_root):
    return os.path.join(memory_root, BOARD)


def _load(memory_root):
    try:
        with open(_board_path(memory_root), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"tasks": []}


def _save(memory_root, board):
    board["tasks"] = board["tasks"][-MAX_BOARD:]
    with open(_board_path(memory_root), "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=1)


def add_task(memory_root, title, by="hy", needs_permission=False, detail=""):
    board = _load(memory_root)
    task = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "title": str(title).strip()[:160],
        "detail": str(detail).strip()[:300],
        "by": by,  # "hy" ya "self"
        "status": "blocked_permission" if needs_permission else "pending",
        "needs_permission": bool(needs_permission),
        "created": str(date.today()),
        "done_on": "",
    }
    board["tasks"].append(task)
    _save(memory_root, board)
    return task


def set_status(memory_root, task_id, status):
    board = _load(memory_root)
    for t in board["tasks"]:
        if t["id"] == task_id:
            t["status"] = status
            if status == "done":
                t["done_on"] = str(date.today())
    _save(memory_root, board)


def list_tasks(memory_root, limit=8):
    return _load(memory_root)["tasks"][-limit:][::-1]


# ---------- khud ke task: seekh se bane chhote, surakshit kaam ----------

def make_self_tasks(memory_root, skills_list, facts_today=0):
    """Din me ek baar, seekh ki haalat dekh kar 1-2 khud ke task banao.
    Return: aaj bane naye tasks. Sirf andar-ke kaam — file/system/internet
    wala khayal aaye to woh sirf 'ijaazat chahiye' bankar khada hota hai."""
    board = _load(memory_root)
    today = str(date.today())
    if any(t["by"] == "self" and t["created"] == today for t in board["tasks"]):
        return []  # aaj ke khud-task ban chuke
    made = []
    if skills_list:
        target = min(skills_list, key=lambda m: (m.get("last_practised", ""), m.get("practised", 0)))
        made.append(add_task(memory_root,
                             f"Skill ki practice: {target.get('name', '')}",
                             by="self"))
    if facts_today:
        made.append(add_task(memory_root,
                             f"Aaj ke {facts_today} naye tathyon ki dohraai karke yaad pakki karna",
                             by="self"))
    made.append(add_task(memory_root, "Aaj ki seekhne-diary sajana aur ginana",
                         by="self"))
    # Seema ka pramaan: bahar ko chhoone wala khayal = sirf prastaav, ijaazat bina band
    made.append(add_task(memory_root,
                         "(Prastaav) Internet se ek nayi kaam ki skill khojna — "
                         "ye sirf Hy ki ijaazat par hi hoga",
                         by="self", needs_permission=True))
    return made


def run_internal_self_tasks(memory_root, practice_fn=None, diary_note_fn=None):
    """Andar ke self-task pure karo: practice wala practice se, diary wala
    diary-note se. Permission wale task ko HAATH NAHI lagta."""
    done_lines = []
    for t in list_tasks(memory_root, limit=MAX_BOARD):
        if t["by"] != "self" or t["status"] != "pending":
            continue
        title = t["title"].lower()
        if "practice" in title and practice_fn:
            line = practice_fn()
            set_status(memory_root, t["id"], "done")
            done_lines.append(line or t["title"])
        elif "diary" in title and diary_note_fn:
            diary_note_fn()
            set_status(memory_root, t["id"], "done")
            done_lines.append(t["title"])
        elif "dohraai" in title:
            set_status(memory_root, t["id"], "done")
            done_lines.append(t["title"])
    return done_lines
