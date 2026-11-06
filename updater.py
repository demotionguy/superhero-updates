#!/usr/bin/env python3
"""
SUPERHERO — self-update system (v3).

Pakke niyam (Hy ke, 6 Nov):
- Update SIRF Hy ke aadesh par hota hai. Ye module apne man se kabhi
  kuch download ya change NAHI karta — sirf tab kaam karta hai jab Hy
  app me "Update dekho" / "Update lagao" button khud dabaye.
- Update me SIRF code/UI files badalti hain (neeche ALLOWED_FILES).
  memory/ folder ko ye module KABHI haath nahi lagata — us raaste ki
  har file-name yahan pehle se band (blocked) hai.
- Har badlav se pehle purani files ka backup (.update-backup/) banta
  hai; kuch gadbad ho to purana version wapas aa sakta hai.
- Koi paid service nahi, koi account/token nahi — sirf ek saade
  manifest (version.json) ko ek fixed pate (URL) se padhna hai.
"""

import hashlib
import json
import os
import shutil
import urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE, "version.txt")
CONFIG_FILE = os.path.join(BASE, "update_config.json")
STAGING_DIR = os.path.join(BASE, ".update-staging")
BACKUP_ROOT = os.path.join(BASE, ".update-backup")

# Sirf ye files update se badal sakti hain. Is list ke bahar ki koi bhi
# file — khaaskar memory/, chats/, update_config.json — kabhi nahi badlegi.
ALLOWED_FILES = {
    "superhero.py",
    "superhero_app.py",
    "superhero_web.py",
    "apna_dimaag.py",
    "APNA-DIMAAG.md",
    "skills.py",
    "SKILLS-SYSTEM.md",
    "diary.py",
    "tasks.py",
    "CREATOR-LOCK.md",
    "research.py",
    "RESEARCH.md",
    "fields.py",
    "FIELDS.md",
    "storage.py",
    "PORTABLE.md",
    "Superhero-App.bat",
    "updater.py",
    "version.txt",
    "IDENTITY.md",
    "FEATURES.md",
    "UPDATE-SYSTEM.md",
    "START-HERE.md",
    "CONTROL.md",
    "Superhero-Start-Karo.bat",
    "Superhero-App.bat",
    "Ollama-Lagao.bat",
    "Dimaag-Lagao.bat",
    "Desktop-Shortcut-Banao.bat",
    "delete-superhero.bat",
    "superhero-logo.png",
    "superhero-logo-128.png",
    "superhero.ico",
}

# In shabdon wala koi bhi path update me aaye to turant inkaar.
BLOCKED_WORDS = ("memory", "chat", "diary", "permission", "config")


def current_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() or "0.0.0"
    except OSError:
        return "0.0.0"


def manifest_url():
    """Fixed update-pata update_config.json se. Khali ho to None."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            url = (json.load(f).get("manifest_url") or "").strip()
            return url or None
    except (OSError, json.JSONDecodeError):
        return None


def _version_tuple(text):
    out = []
    for part in str(text).strip().split("."):
        digits = "".join(c for c in part if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)


SAFE_EXTS = {".py", ".md", ".txt", ".bat", ".png", ".ico"}
NEVER_FILES = {"update_config.json", "password.hash"}


def _safe_name(name):
    """Saaf file-name chalegi — path/folder/memory sab band.
    Whitelist ke alawa aage ke NAYE module (.py/.md adi, sirf app ke
    root me, surakshit ext wale) bhi chalenge, taaki naya feature
    purane updater par atke nahi. Memory/data/config kabhi nahi."""
    base = os.path.basename(str(name).replace("\\", "/"))
    if base != name:
        return None
    lowered = base.lower()
    if lowered in NEVER_FILES:
        return None
    if base in ALLOWED_FILES:
        return base  # Muse ki pakki whitelist — blocked-shabd is par nahi lagte
    if any(w in lowered for w in BLOCKED_WORDS):
        return None
    stem, dot, ext = base.rpartition(".")
    if dot and ("." + ext.lower()) in SAFE_EXTS and stem.replace("_", "").replace("-", "").isalnum():
        return base
    return None


def _fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Superhero-Updater/3"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


BRIDGE_VERSION = "3.1.1"  # pul wala version: sirf updater badalta hai
_chosen_url = {"url": None}


def _candidate_urls():
    """Aadesh-kram: aam pata; pul (bridge) par ho to pehle poora wala pata."""
    url = manifest_url()
    urls = [url] if url else []
    if url and current_version() == BRIDGE_VERSION and url.rsplit("/", 1)[-1] == "version.json":
        urls.insert(0, url[: -len("version.json")] + "version-full.json")
    return urls


def check_update():
    """Manifest padh kar batao: naya update hai ya nahi. Kuch badalta NAHI hai.

    Return dict:
      status: "no_address" | "unreachable" | "up_to_date" | "available" | "bad_manifest"
      version / notes: available ho to naye version ki jaankari
      message: Hy ko dikhane layak saaf Hinglish sandesh
    """
    urls = _candidate_urls()
    if not urls:
        return {"status": "no_address",
                "message": "Update-pata abhi set nahi hai — Muse ko bolo, woh set karega."}
    manifest = None
    for cand in urls:
        try:
            manifest = json.loads(_fetch(cand).decode("utf-8"))
            _chosen_url["url"] = cand
            break
        except Exception:
            continue
    if manifest is None:
        return {"status": "unreachable",
                "message": ("Update-pata abhi khul nahi raha. Iska matlab aksar ye hai ki "
                            "pata abhi live nahi hua, ya internet band hai. Muse ko bolo — "
                            "koi gadbad nahi hui, kuch badla bhi nahi.")}
    new_version = str(manifest.get("version", "")).strip()
    files = manifest.get("files") or []
    if not new_version or not isinstance(files, list) or not files:
        return {"status": "bad_manifest",
                "message": "Update-pate par jaankari aadhi hai — update nahi lagaya. Muse ko bolo."}
    if _version_tuple(new_version) <= _version_tuple(current_version()):
        return {"status": "up_to_date", "version": new_version,
                "message": f"Tum sabse naye version par ho (v{current_version()}). Koi update nahi hai."}
    return {"status": "available", "version": new_version,
            "notes": str(manifest.get("notes", "")).strip(),
            "message": (f"Naya update uplabdh hai (Hy ke aadesh se) — v{new_version}. "
                        "Lagana ya na lagana tumhare haath me hai.")}


def apply_update(progress=None):
    """Naya version lagao — sirf whitelist code files, backup ke saath.

    Memory ko haath nahi lagta. Beech me gadbad ho to purani files
    backup se wapas aa jati hain aur version purana hi rehta hai.
    Return: (ok: bool, message: str)
    """
    def say(msg):
        if progress:
            progress(msg)

    info = check_update()
    if info["status"] != "available":
        return False, info["message"]
    url = _chosen_url.get("url") or manifest_url()
    manifest = json.loads(_fetch(url).decode("utf-8"))
    base_url = url.rsplit("/", 1)[0] + "/"

    names = []
    for entry in manifest.get("files", []):
        name = _safe_name(entry.get("path", "") if isinstance(entry, dict) else "")
        if name is None:
            return False, ("Update me ek aisi file aayi jo badalna mana hai — "
                           "poora update rok diya, kuch nahi badla. Muse ko bolo.")
        names.append((name, entry))

    # 1) Pehle sab staging me lao aur hash jaancho — asal files abhi surakshit.
    shutil.rmtree(STAGING_DIR, ignore_errors=True)
    os.makedirs(STAGING_DIR, exist_ok=True)
    try:
        for name, entry in names:
            say(f"Update file aa rahi hai: {name}")
            rel = str(entry.get("url") or name)
            if rel.startswith("http://") or rel.startswith("https://"):
                # Poora URL ho to woh usi update-pate ke neeche ka hona chahiye.
                if not rel.startswith(base_url):
                    return False, "Update file ka pata update-pate se bahar ka hai — rok diya."
                file_url = rel
            else:
                # Sirf saaf file-name chalega — koi folder/path nahi.
                if _safe_name(rel) is None:
                    return False, "Update file ka naam saaf nahi hai — rok diya."
                file_url = base_url + rel
            data = _fetch(file_url)
            want = str(entry.get("sha256", "")).strip().lower()
            if want and hashlib.sha256(data).hexdigest() != want:
                return False, f"{name} ki jaanch (hash) fail — update rok diya, kuch nahi badla."
            with open(os.path.join(STAGING_DIR, name), "wb") as f:
                f.write(data)
    except Exception as e:
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        return False, f"Update download pura nahi hua ({e}) — kuch nahi badla, dobara koshish kar sakte ho."

    # 2) Backup banao, phir files badlo. version.txt SABSE AAKHIR me badlega.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = os.path.join(BACKUP_ROOT, stamp)
    os.makedirs(backup_dir, exist_ok=True)
    ordered = sorted(names, key=lambda t: 1 if t[0] == "version.txt" else 0)
    changed = []
    try:
        for name, _entry in ordered:
            target = os.path.join(BASE, name)
            if os.path.isfile(target):
                shutil.copy2(target, os.path.join(backup_dir, name))
            if name == "version.txt":
                with open(target, "w", encoding="utf-8") as f:
                    f.write(str(manifest["version"]).strip() + "\n")
            else:
                shutil.copy2(os.path.join(STAGING_DIR, name), target)
            changed.append(name)
            say(f"Lag gaya: {name}")
    except Exception as e:
        # Rollback: jo badla, backup se wapas.
        for name in changed:
            old = os.path.join(backup_dir, name)
            if os.path.isfile(old):
                shutil.copy2(old, os.path.join(BASE, name))
        return False, f"Update lagate waqt gadbad hui ({e}) — purana version wapas la diya hai, sab surakshit hai."
    finally:
        shutil.rmtree(STAGING_DIR, ignore_errors=True)

    return True, (f"Update lag gaya — ab tum v{manifest['version']} par ho. "
                  "Apni yaadein (memory) bilkul surakshit hain, unhe haath nahi laga. "
                  "Ab app ko ek baar band karke dobara kholo.")
