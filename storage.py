#!/usr/bin/env python3
"""
SUPERHERO — STORAGE SEEMA (HARD CAP) + EK-FOLDER HISAB.

Pakke niyam (Hy ka design):
- Superhero apne aap manmaani jagah NAHI khayega. Uske apne data
  (memory, skills, gyaan-yaad, diary, logs — sab) ki KUL SEEMA
  default 5 GB hai.
- Seema SIRF Hy badha sakta hai (app setting / uske aadesh se).
  Superhero khud apni seema KABHI nahi badha sakta — is file me aisa
  koi raasta hi nahi hai; cap sirf padhi jati hai.
- Seema ke paas/bhar jane par woh RUK kar saaf Hinglish me Hy ko
  batata hai — chupchaap kuch delete nahi karta, chupchaap badhta
  bhi nahi.
- App me hamesha dikhta hai: kitni jagah istemal / seema kitni hai.
- EK FOLDER: uska saara data usi ek folder ke andar hai; model bhi
  usi folder ke 'models' hisse me rehta hai (start files OLLAMA_MODELS
  wahi rakhti hain), taaki folder copy = poora Superhero kahin bhi.
"""

import os

DEFAULT_CAP_GB = 5.0
GB = 1024 ** 3


def _dir_bytes(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for fn in files:
            try:
                total += os.path.getsize(os.path.join(root, fn))
            except OSError:
                continue
    return total


def data_used_bytes(base):
    """Superhero ka apna data: memory/ + data/ (program files nahi)."""
    return _dir_bytes(os.path.join(base, "memory")) + _dir_bytes(os.path.join(base, "data"))


def models_bytes(base):
    return _dir_bytes(os.path.join(base, "models"))


def cap_bytes(settings):
    try:
        gb = float((settings or {}).get("storage_cap_gb", DEFAULT_CAP_GB))
    except (TypeError, ValueError):
        gb = DEFAULT_CAP_GB
    return max(0.05, gb) * GB  # seema kam se kam 50 MB — galti se 0 na ho


def status(base, settings):
    used = data_used_bytes(base)
    cap = cap_bytes(settings)
    pct = (used / cap * 100) if cap else 100.0
    return {"used": used, "cap": cap, "pct": round(pct, 2),
            "models": models_bytes(base),
            "near": pct >= 90 and pct < 100, "full": pct >= 100}


def fmt(n):
    if n >= GB:
        return f"{n / GB:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / (1024 ** 2):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{int(n)} B"


def full_message(st):
    return ("📦 Jagah bhar gayi hai — meri apni jagah (yaad, skills, gyaan, diary) "
            f"{fmt(st['used'])} / {fmt(st['cap'])} ho gayi hai. Mai yahi ruk gaya hoon — "
            "na kuch chupchaap hataunga, na seema se aage badhunga.\n"
            "Tum chaaho to:\n"
            "• Seema badhao: bolo “seema badhao: 10 GB” (seema sirf tum badha sakte ho), ya\n"
            "• Kuch purana hatao: jaise “skill hatao: <naam>”.")


def near_message(st):
    return (f"📦 Ek baat — meri jagah {fmt(st['used'])} / {fmt(st['cap'])} "
            f"({st['pct']:.0f}%) ho gayi hai, seema ke paas hoon. Bhar jane par mai ruk kar bata dunga.")
