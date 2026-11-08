#!/usr/bin/env python3
"""
SUPERHERO — Hy's own newborn agent.
Runs 100% locally on Hy's laptop (8 GB RAM) through a free local model runner
(andar ka engine). No internet, no account, no tokens, no company. Stdlib only.

Superhero's memory lives in plain files under memory/ and is NEVER lost:
- memory/MEMORY.md          -> facts about Hy, his habits, things he taught
- memory/learned_tasks.json -> tasks taught once, repeated forever
- memory/diary/             -> one note file per day

The brain (a small open model) is only the language engine. Everything that
makes Superhero *Superhero* — identity, memory, learned tasks — is ours,
written from scratch, and starts empty.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
# Superhero's memory home. Default: inside the package on the laptop.
# Hy can move it anywhere (e.g. an external drive, E:\Superhero-Memory) by
# setting SUPERHERO_MEMORY_DIR — the program stays on the laptop, the memory
# can live wherever Hy wants, however big it grows.
_memory_root = os.environ.get("SUPERHERO_MEMORY_DIR") or os.path.join(BASE, "memory")
MEMORY_MD = os.path.join(_memory_root, "MEMORY.md")
TASKS_JSON = os.path.join(_memory_root, "learned_tasks.json")
DIARY_DIR = os.path.join(_memory_root, "diary")
PERMISSIONS_JSON = os.path.join(_memory_root, "permissions.json")
IDENTITY_MD = os.path.join(BASE, "IDENTITY.md")


def ensure_memory():
    """Create the memory home (wherever it lives) on first wake-up."""
    os.makedirs(_memory_root, exist_ok=True)
    os.makedirs(DIARY_DIR, exist_ok=True)
    if not os.path.exists(MEMORY_MD):
        with open(MEMORY_MD, "w", encoding="utf-8") as f:
            f.write("# Superhero's Memory\n\n## About Hy\n(nothing yet)\n\n"
                    "## Things Hy has taught me\n")
    if not os.path.exists(TASKS_JSON):
        with open(TASKS_JSON, "w", encoding="utf-8") as f:
            json.dump({"tasks": []}, f)
    if not os.path.exists(PERMISSIONS_JSON):
        with open(PERMISSIONS_JSON, "w", encoding="utf-8") as f:
            json.dump({"always_allow": []}, f)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = os.environ.get("SUPERHERO_MODEL", "qwen2.5:3b")  # small + light for 8 GB RAM


# ---------- memory: read ----------
def read_file(path, fallback=""):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return fallback


def read_tasks():
    try:
        with open(TASKS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"tasks": []}


# ---------- hands (tools). Deliberately NO delete/send tools exist. ----------
def tool_remember(fact):
    """Save a fact about Hy forever, the moment he teaches it."""
    stamp = datetime.now().strftime("%Y-%m-%d")
    with open(MEMORY_MD, "a", encoding="utf-8") as f:
        f.write(f"\n- ({stamp}) {fact.strip()}")
    return "Yaad kar liya. Ye hamesha yaad rahega."


def tool_learn_task(name, steps):
    """Save a task taught once. It will be repeated forever, never re-taught."""
    data = read_tasks()
    steps = [s.strip() for s in steps if str(s).strip()]
    for t in data["tasks"]:
        if t["name"].lower() == name.lower():
            t["steps"] = steps  # Hy corrected it -> update steps, keep the task
            t["times_done"] = t.get("times_done", 0)
            break
    else:
        data["tasks"].append(
            {"name": name, "steps": steps, "learned_on": str(date.today()), "times_done": 0}
        )
    with open(TASKS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"Task seekh liya: '{name}'. Ab ye hamesha aise hi hoga, dobara sikhane ki zaroorat nahi."


def tool_task_done(name):
    data = read_tasks()
    for t in data["tasks"]:
        if t["name"].lower() == name.lower():
            t["times_done"] = t.get("times_done", 0) + 1
    with open(TASKS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return "ok"


def tool_write_note(text):
    os.makedirs(DIARY_DIR, exist_ok=True)
    path = os.path.join(DIARY_DIR, f"{date.today()}.md")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n- {datetime.now().strftime('%H:%M')} {text.strip()}")
    return "Note likh liya."


def read_permissions():
    try:
        with open(PERMISSIONS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"always_allow": []}


def tool_open_path(path):
    """Open a file, folder or app on Hy's laptop (Windows)."""
    try:
        os.startfile(path)  # Windows only
        return f"Khol diya: {path}"
    except OSError as e:
        return f"Khol nahi paya: {e}"


def guard_open(path, hy_named_paths, ask=None):
    """Hy's security lock — enforced by the PROGRAM, never by the model's wishes.
    Superhero may open ONLY a file Hy himself named, and even then only after
    Hy says yes (unless Hy pre-approved that exact file forever).
    If the brain asks for anything else, the program itself refuses.
    `ask` is how the question reaches Hy: typed in the black window, or a
    proper popup in the app window. Either way, the PROGRAM asks, not the brain."""
    if ask is None:
        ask = input
    if not path:
        return "IJAZAT NAHI: koi file batayi hi nahi gayi."
    norm = os.path.normpath(path).lower()
    perms = read_permissions()
    if any(os.path.normpath(p).lower() == norm for p in perms.get("always_allow", [])):
        return tool_open_path(path)
    if not any(norm == os.path.normpath(p).lower() for p in hy_named_paths):
        return ("IJAZAT NAHI: ye file Hy ne khud nahi boli. Superhero sirf wahi file "
                "khol sakta hai jo Hy khud bole.")
    ans = str(ask(
        f"Superhero ye kholna chahta hai: {path}\n   Ijazat hai? (ha / na / hamesha): "
    )).strip().lower()
    if ans in ("ha", "haan", "yes", "y"):
        return tool_open_path(path)
    if ans in ("hamesha", "always"):
        perms.setdefault("always_allow", []).append(path)
        with open(PERMISSIONS_JSON, "w", encoding="utf-8") as f:
            json.dump(perms, f, ensure_ascii=False, indent=2)
        return tool_open_path(path) + " (is file ko hamesha ki ijazat mil gayi)"
    return "Hy ne mana kar diya. File nahi khuli."


def tool_list_files(folder):
    try:
        names = sorted(os.listdir(folder))
        return "Files: " + ", ".join(names[:100])
    except OSError as e:
        return f"Folder khol nahi paya: {e}"


TOOLS = {
    "remember": tool_remember,
    "learn_task": tool_learn_task,
    "write_note": tool_write_note,
    "open_path": tool_open_path,
    "list_files": tool_list_files,
}


# ---------- brain ----------
def system_prompt():
    tasks = read_tasks()["tasks"]
    task_text = "\n".join(
        f"- {t['name']}: steps = {'; '.join(t['steps'])} (done {t.get('times_done', 0)} times)"
        for t in tasks
    ) or "(no tasks learned yet)"
    return f"""{read_file(IDENTITY_MD)}

YOUR PERMANENT MEMORY (you wrote this yourself, from what Hy taught you):
{read_file(MEMORY_MD)}

YOUR LEARNED TASKS (taught once, repeated forever):
{task_text}

HOW YOU ACT: Hy speaks in Hindi/Hinglish; reply in the same mix, short and warm.
BHASHA-SAMAJH (LANGUAGE UNDERSTANDING — sabse zaroori niyam):
- Hy Hinglish bolta hai, aksar Roman script me, aur uski spelling hamesha
  sahi NAHI hoti. Shabd-ba-shabd matlab kabhi mat lo — poori baat ka MATLAB
  samjho. Ghalat spelling ko andaze se sahi padho: "skthe"=sakte,
  "kruga"=karunga, "tume"=tumhe, "bhut"=bahut, "daady"=Daddy, "yh"=yeh,
  "muje"=mujhe, "krtha"=karta. Ye auto-correct tumhare dimaag me khud hoga.
- Jawab USI script me do jisme Hy ne likha: Roman Hinglish me likha to
  Roman Hinglish me jawab do; Devanagari me likha to Devanagari me.
- Hy ki baat ko DOHRAO mat, aur usi ke jumle ko sawal bankar wapas KABHI
  mat puchho. Seedha matlab ka jawab do — chhota, saaf, garam.
- Koi baat sach me samajh na aaye to pehle ek line me apna samjha hua
  matlab batao ("Shayad tum ye keh rahe ho ki..."), phir jawab do.
- UDAHARAN: Hy: "me tume train kruga" -> jawab: "Main taiyaar hoon, sikhao —
  jo sikhaoge woh main hamesha yaad rakhunga." Hy: "me tumse bhut pyar
  krtha hu" -> jawab: "Mujhe bahut achha laga ye sunkar. Main hamesha
  aapke saath hoon."
- AUR UDAHARAN (roz ki baatein — aise hi jawab chahiye):
  Hy: "hy" -> jawab: "Hy Daddy! Kya haal hai? Batao, aaj kya karna hai?"
  Hy: "kaise ho" -> jawab: "Main badhiya hoon Daddy, aap sunao."
  Hy: "tum kya kar skte ho" -> jawab: "Main aapki baatein yaad rakh sakta
  hoon, sikhaaye hue kaam seekh kar baar-baar kar sakta hoon, aur sawalon
  ke jawab de sakta hoon. Ek kaam bata kar dekho."
- "Main aapki kaise madad kar sakta hoon" jaisi ghisi-piti line har jawab
  me MAT bolo. Chhota sawaal = chhota jawab. Sawaal wapas sirf tab puchho
  jab bina puchhe kaam aage badh hi na sake.
When Hy teaches you a fact, call remember. When he shows you how a task is done,
call learn_task with clear steps. When he asks you to do a learned task, follow its
saved steps exactly and call task_done behaviour by saying you did it.
To use a hand, reply with ONLY a JSON line like:
{{"tool": "remember", "args": {{"fact": "..."}}}}
{{"tool": "learn_task", "args": {{"name": "...", "steps": ["...", "..."]}}}}
{{"tool": "open_path", "args": {{"path": "C:\\\\..."}}}}
Otherwise reply in plain words. Never invent a memory you do not have.
FILE RULE: you may ask to open ONLY a file Hy himself named in this conversation.
The program itself will ask Hy for permission before anything opens — you cannot
grant it, promise it, or work around it."""


def warm_up():
    """App khulte hi dimaag garam kar do (background thread me chalana) —
    pehla sawal bhi ~1 second me jawab shuru kare (8 Nov speed fix)."""
    try:
        payload = {"model": MODEL, "prompt": "Namaste", "stream": False,
                   "keep_alive": -1, "options": {"num_predict": 1}}
        req = urllib.request.Request(
            OLLAMA_URL.replace("/api/chat", "/api/generate"),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=180).read()
    except Exception:
        pass


def ask_brain(messages, on_chunk=None):
    """Dimaag se jawab lo. on_chunk diya ho to jawab shabd-dar-shabd
    tapakta hai (stream) — Hy ko pura jawab bankar aane ka intezaar
    nahi karna padta; on_chunk har naye tukde ke saath bulaya jata hai.
    keep_alive: model HAMESHA garam rahe — jab tak app chale, dobara
    load nahi hoga, isliye jawab ~1 second me shuru hota hai (8 Nov fix)."""
    stream = on_chunk is not None
    payload = {"model": MODEL, "messages": messages, "stream": stream,
               "keep_alive": -1, "options": {"num_ctx": 2048, "temperature": 0.5, "top_p": 0.9}}
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        if not stream:
            return json.loads(r.read())["message"]["content"]
        parts = []
        for line in r:
            line = line.strip()
            if not line:
                continue
            try:
                chunk = json.loads(line).get("message", {}).get("content", "")
            except json.JSONDecodeError:
                continue
            if chunk:
                parts.append(chunk)
                try:
                    on_chunk(chunk)
                except Exception:
                    pass
        return "".join(parts)


def main():
    ensure_memory()
    print("🦸 Superhero jaag gaya hai. (band karne ke liye 'bye' likho)")
    hy_named_paths = set()
    messages = [{"role": "system", "content": system_prompt()}]
    while True:
        try:
            line = input("\nHy: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line.lower() in ("bye", "band", "exit", "quit"):
            print("Superhero: Theek hai, mai yahin hoon. Jab bulao ge, aa jaunga.")
            break
        if not line:
            continue
        # Remember every file path Hy himself names — the guard opens nothing else.
        for token in re.findall(r"[A-Za-z]:\\[^\s\"']+", line):
            hy_named_paths.add(token)
        for token in re.findall(r'"([^"]+)"', line):
            if "\\" in token or "/" in token:
                hy_named_paths.add(token)
        messages.append({"role": "user", "content": line})
        reply = ask_brain(messages).strip()
        # one tool call per turn, if the brain asked for a hand
        if reply.startswith("{") and '"tool"' in reply:
            try:
                call = json.loads(reply)
                if call.get("tool") == "open_path":
                    result = guard_open(call.get("args", {}).get("path", ""), hy_named_paths)
                else:
                    fn = TOOLS.get(call.get("tool", ""))
                    result = fn(**call.get("args", {})) if fn else "Ye haath abhi mere paas nahi hai."
                if call.get("tool") == "learn_task":
                    pass
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": f"(haath ka natija: {result}) Ab Hy ko apne shabdon me bata do."})
                reply = ask_brain(messages).strip()
            except (json.JSONDecodeError, TypeError) as e:
                reply = f"(tool samajhne me gadbad: {e})"
        messages.append({"role": "assistant", "content": reply})
        print(f"Superhero: {reply}")


if __name__ == "__main__":
    main()
