#!/usr/bin/env python3
"""
SUPERHERO — the app window (Claude-style face, Superhero's own soul).

A clean, warm desktop window: a soft sidebar with saved chats and a
"+ Nayi Chat" button, a calm chat screen, and one simple writing box —
the same friendly face people know from modern AI apps, but the agent
inside is Hy's own Superhero: same brain, same never-forget memory,
same permission locks (all in superhero.py). Fully offline after setup.

One-time needs: Python, the free internal engine, and the small model, pulled by
the in-app brain-download button.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import scrolledtext

import superhero as core
import updater
import apna_dimaag
import diary as diary_mod
import skills as skills_mod
import study as study_mod

OLLAMA_TAGS = "http://localhost:11434/api/tags"
MODEL = core.MODEL


def find_ollama():
    """Engine ka program dhoondo — PATH me, ya Windows ke aam install sthanon par."""
    found = shutil.which("ollama")
    if found:
        return found
    candidates = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        candidates.append(os.path.join(local, "Programs", "Ollama", "ollama.exe"))
    for var in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(var, "")
        if base:
            candidates.append(os.path.join(base, "Ollama", "ollama.exe"))
    candidates.append(os.path.join(os.path.expanduser("~"), "AppData", "Local",
                                   "Programs", "Ollama", "ollama.exe"))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None

# ---------- PROGRAM KE PAKKE JAWAB (v3.8.3) ----------
# Desktop app seedha dimaag se baat karta tha — isliye salaam aur
# padhai-aadesh jaise pakke kaam chhote model ki marzi par the, aur woh
# robot wali angrezi line bol deta tha. Ab ye kaam PROGRAM sambhalta hai:
# salaam ka jawab aur khud-padhai ka aadesh model ke paas jata hi nahi.
_MEM_ROOT = os.path.dirname(core.MEMORY_MD)
_study_state = {"on": False, "stop": False}

_SALAAM = {"hy", "hii", "hiii", "hello", "helloo", "hi", "hey", "namaste",
           "namaskar", "ram ram", "good morning",
           "good afternoon", "good evening", "namaste daddy", "hello daddy"}
_HAAL = {"kaise ho", "kya haal hai", "kaisa hai", "aur batao", "kya haal",
         "kaise ho daddy", "tum kaise ho"}


def _hy_naam():
    try:
        return "Daddy" if "daddy" in core.read_file(core.MEMORY_MD).lower() else "Hy"
    except Exception:
        return "Hy"


def _run_study_bg(steps=3):
    """Khud-padhai peeche chalao (sirf padhna; aadesh hi ijaazat hai)."""
    if _study_state["on"]:
        return False
    _study_state["on"] = True
    _study_state["stop"] = False

    def _work():
        try:
            topics = None
            try:
                topics = [e.get("name", "") for e in skills_mod.CATALOG if e.get("name")]
            except Exception:
                pass
            for _ in range(steps):
                if _study_state["stop"]:
                    break
                study_mod.study_step(
                    _MEM_ROOT,
                    brain=lambda ms: core.ask_brain(
                        [{"role": "system", "content": core.system_prompt()}] + ms),
                    search_fn=apna_dimaag.web_search,
                    diary_log=lambda k, t: diary_mod.log_event(_MEM_ROOT, k, t),
                    catalog_topics=topics)
        except Exception:
            pass
        finally:
            _study_state["on"] = False

    threading.Thread(target=_work, daemon=True).start()
    return True


def program_reply(text):
    """Pakka program-jawab ho to woh, warna None (dimaag bolega)."""
    low = re.sub(r"[!.,?~*]+", " ", text.lower())
    low = re.sub(r"\s+", " ", low).strip()
    naam = _hy_naam()
    if low in _HAAL:
        return f"Main badhiya hoon {naam}, aap sunao — kya chal raha hai?"
    if low in _SALAAM:
        return f"Namaskar {naam}! Kya haal hai? Batao, aaj kya karna hai?"
    # --- khud-padhai (web wale _study_command jaisi pehchan) ---
    if any(p in low for p in ("padhai band", "padhai rok", "study band", "study rok", "padhna band")):
        _study_state["stop"] = True
        return "Padhai rok di, Daddy. Jitna padha, woh gyaan-yaad me surakshit hai — wahan se aage kabhi bhi phir shuru ho jayegi."
    if any(p in low for p in ("padhai ki pragati", "kitna padha", "kya padha", "padhai kahan tak",
                              "study progress", "kitni padhai")):
        st = study_mod.load_state(_MEM_ROOT)
        rev = study_mod.weekly_review(_MEM_ROOT)
        last = st.get("history", [])[-3:]
        last_txt = "; ".join(h.get("title", "") for h in last) or "abhi koi chapter pura nahi"
        chal = "Padhai abhi peeche chal rahi hai. " if _study_state["on"] else ""
        return (f"{chal}Pragati: 0-se-college ki seedhi me {rev['phase1_done']}/{rev['phase1_total']} "
                f"kitabein/vishay pure hue. Aakhri padhe hue: {last_txt}. "
                f"Vishay-war notes: " + ", ".join(f"{k} {v}" for k, v in rev["counts"].items()) + ".")
    start = (
        re.search(r"(study|padhai|padhna|padho)\b[^.]{0,40}\b(karo|kro|kar|shuru|chalu|chaalu)\b", low)
        or re.search(r"\b(karo|kro|shuru|chalu)\b[^.]{0,30}\b(study|padhai)\b", low)
        or "books study" in low or "book study" in low or "khud padhai" in low
        or "start studying" in low or "study books" in low
        or ("internet se" in low and ("study" in low or "padhai" in low or "padho" in low))
    )
    if start:
        st = study_mod.load_state(_MEM_ROOT)
        topics = None
        try:
            topics = [e.get("name", "") for e in skills_mod.CATALOG if e.get("name")]
        except Exception:
            pass
        nxt = study_mod.next_item(st, topics)
        if _run_study_bg(steps=3):
            diary_mod.log_event(_MEM_ROOT, "study",
                                f"Hy ke aadesh par khud-padhai shuru: {nxt['title']} se.")
            return (f"Padhai shuru kar di hai, Daddy 📚 — seedhi 0 se college tak ki bandhi kitab-soochi se chalegi, "
                    f"phir university star ki khud-padhai. Pehla vishay: {nxt['title']} ({nxt['subject']}). "
                    f"Main peeche padhta rahunga; har chapter ki summary APNE shabdon me gyaan-yaad me rahegi "
                    f"(copy-paste wali summary program khud reject kar deta hai). "
                    f"Pragati: bolo 'padhai ki pragati' — rokna ho to: 'padhai band karo'.")
        return "Padhai pehle se hi peeche chal rahi hai, Daddy — ek chapter khatm hote hi agla khud shuru ho jata hai."
    return None


# ---- the face: warm paper, soft sidebar, clay accent ----
BG = "#FAF9F5"
SIDEBAR_BG = "#F0EEE6"
INK = "#1F1E1D"
SOFT = "#6B6862"
CLAY = "#C4633C"
CARD = "#FFFFFF"
CHATS_DIR = os.path.join(os.path.dirname(core.MEMORY_MD), "chats")


def chat_path(cid):
    return os.path.join(CHATS_DIR, cid + ".json")


def load_chat(cid):
    try:
        with open(chat_path(cid), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def list_chats():
    out = []
    if os.path.isdir(CHATS_DIR):
        for name in sorted(os.listdir(CHATS_DIR), reverse=True):
            if name.endswith(".json"):
                data = load_chat(name[:-5])
                if data:
                    out.append((name[:-5], data.get("title", "Nayi chat")))
    return out


class SuperheroApp:
    def __init__(self, root):
        self.root = root
        root.title("Superhero — Hy ka apna agent")
        root.geometry("860x660")
        root.configure(bg=BG)
        try:
            root.iconbitmap(os.path.join(core.BASE, "superhero.ico"))
        except Exception:
            pass
        try:
            self.logo_img = tk.PhotoImage(file=os.path.join(core.BASE, "superhero-logo-128.png"))
        except Exception:
            self.logo_img = None

        self.history = []
        self.chat_id = None
        self.hy_named_paths = set()
        self.busy = False
        self._ask_question = None
        self._ask_answer = None
        self._ask_event = threading.Event()

        core.ensure_memory()
        os.makedirs(CHATS_DIR, exist_ok=True)
        self._build_sidebar()
        self._build_main()
        self.refresh_chat_list()
        existing = list_chats()
        if existing:
            self.open_chat(existing[0][0])
        else:
            self.new_chat()
        self.root.after(300, self.check_setup)
        self.root.after(200, self._poll_ask)

    # ---------- layout ----------
    def _build_sidebar(self):
        bar = tk.Frame(self.root, bg=SIDEBAR_BG, width=215)
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)
        title_row = tk.Frame(bar, bg=SIDEBAR_BG)
        title_row.pack(anchor="w", padx=12, pady=(12, 2))
        if self.logo_img is not None:
            tk.Label(title_row, image=self.logo_img, bg=SIDEBAR_BG).pack(side="left")
        tk.Label(title_row, text=" Superhero", font=("Georgia", 15, "bold"),
                 bg=SIDEBAR_BG, fg=INK).pack(side="left")
        tk.Label(bar, text="Hy ka apna agent • Unlimited • No Token • Offline", font=("Segoe UI", 8),
                 bg=SIDEBAR_BG, fg=SOFT).pack(anchor="w", padx=14, pady=(0, 10))
        tk.Button(bar, text="＋  Nayi Chat", command=self.new_chat, bg=CLAY, fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=5,
                  activebackground=CLAY).pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(bar, text="Purani batein", font=("Segoe UI", 9, "bold"),
                 bg=SIDEBAR_BG, fg=SOFT).pack(anchor="w", padx=14)
        self.chat_list = tk.Listbox(bar, font=("Segoe UI", 10), bg=SIDEBAR_BG, fg=INK,
                                    relief="flat", highlightthickness=0, activestyle="none",
                                    selectbackground="#E4DFD2", selectforeground=INK)
        self.chat_list.pack(fill="both", expand=True, padx=8, pady=4)
        self.chat_list.bind("<<ListboxSelect>>", self._on_pick_chat)
        self.status = tk.Label(bar, text="jaag raha hai…", font=("Segoe UI", 9),
                               bg=SIDEBAR_BG, fg=CLAY, wraplength=190, justify="left")
        self.status.pack(anchor="w", padx=14, pady=(6, 2))
        self.btn_brain = tk.Button(bar, text="🧠 Dimaag download karo", command=self.download_brain,
                                   bg=CLAY, fg="white", font=("Segoe UI", 9, "bold"),
                                   relief="flat", padx=8, pady=4)
        self.btn_install = tk.Button(bar, text="⚙️ Dimaag Lagao (ek click)", command=self.install_ollama,
                                     bg=CLAY, fg="white", font=("Segoe UI", 9, "bold"),
                                     relief="flat", padx=8, pady=4)
        self.btn_site = tk.Button(bar, text="Dimaag ki site kholo",
                                  command=lambda: webbrowser.open("https://ollama.com/download"),
                                  font=("Segoe UI", 9), relief="flat", padx=8, pady=4)
        # ---- Update (v3): sirf Hy ke dabane par; apne man se kabhi nahi ----
        self.update_status = tk.Label(bar, text=f"Version v{updater.current_version()} • update sirf tumhare kehne par",
                                      font=("Segoe UI", 8), bg=SIDEBAR_BG, fg=SOFT,
                                      wraplength=190, justify="left")
        self.update_status.pack(anchor="w", padx=14, pady=(10, 2))
        self.btn_update = tk.Button(bar, text="🔄  Update dekho", command=self.check_update_clicked,
                                    font=("Segoe UI", 9, "bold"), relief="flat", padx=8, pady=4)
        self.btn_update.pack(fill="x", padx=12, pady=(2, 4))
        self.btn_apply = tk.Button(bar, text="⬆️  Update lagao", command=self.apply_update_clicked,
                                   bg=CLAY, fg="white", font=("Segoe UI", 9, "bold"),
                                   relief="flat", padx=8, pady=4)

    def _build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        self.greeting = tk.Label(main, text="Namaskar, Hy", font=("Georgia", 22),
                                 bg=BG, fg=INK)
        self.greeting.pack(pady=(16, 0))
        tk.Label(main, text="Mai Superhero — jo sikhaoge, hamesha yaad rakhunga.",
                 font=("Segoe UI", 10), bg=BG, fg=SOFT).pack(pady=(2, 6))
        self.chat = scrolledtext.ScrolledText(main, wrap="word", state="disabled",
                                              font=("Segoe UI", 11), bg=BG, fg=INK,
                                              relief="flat", padx=16, pady=10,
                                              insertbackground=INK)
        self.chat.pack(fill="both", expand=True, padx=10)
        self.chat.tag_config("hy_name", foreground=SOFT, font=("Segoe UI", 9, "bold"))
        self.chat.tag_config("hero_name", foreground=CLAY, font=("Segoe UI", 9, "bold"))
        bottom = tk.Frame(main, bg=CARD, relief="solid", bd=1)
        bottom.pack(fill="x", padx=16, pady=(4, 14))
        self.entry = tk.Entry(bottom, font=("Segoe UI", 12), relief="flat", bg=CARD, fg=INK)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(10, 4))
        self.entry.bind("<Return>", lambda e: self.on_send())
        self.entry.focus_set()
        tk.Button(bottom, text="Bhejo ↑", command=self.on_send, bg=CLAY, fg="white",
                  font=("Segoe UI", 11, "bold"), relief="flat", padx=12, pady=4,
                  activebackground=CLAY).pack(side="right", padx=6, pady=6)

    # ---------- chats: save, open, new ----------
    def refresh_chat_list(self):
        self.chat_list.delete(0, "end")
        self._chat_ids = []
        for cid, title in list_chats():
            self.chat_list.insert("end", "  " + title)
            self._chat_ids.append(cid)

    def save_chat(self):
        if not self.chat_id:
            return
        title = "Nayi chat"
        for m in self.history:
            if m["role"] == "user":
                title = m["content"].strip().replace("\n", " ")[:30] or title
                break
        with open(chat_path(self.chat_id), "w", encoding="utf-8") as f:
            json.dump({"title": title, "messages": self.history}, f, ensure_ascii=False, indent=1)

    def open_chat(self, cid):
        data = load_chat(cid)
        if not data:
            return
        self.chat_id = cid
        self.history = data.get("messages", [])
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        for m in self.history:
            self.say("hy" if m["role"] == "user" else "hero", m["content"], store=False)
        if not self.history:
            self.say("hero", "Namaskar Hy! Kuch bولو — mai sun raha hoon.", store=False)

    def new_chat(self):
        self.save_chat()
        self.chat_id = time.strftime("%Y%m%d-%H%M%S")
        self.history = []
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self.say("hero", "Namaskar Hy! Mai Superhero hoon — tumhara apna. "
                         "Jo bologe, samjhunga; jo sikhaoge, hamesha yaad rakhunga.", store=False)
        self.save_chat()
        self.refresh_chat_list()

    def _on_pick_chat(self, _event):
        sel = self.chat_list.curselection()
        if sel and self._chat_ids:
            cid = self._chat_ids[sel[0]]
            if cid != self.chat_id:
                self.save_chat()
                self.open_chat(cid)

    # ---------- chat helpers ----------
    def say(self, who, text, store=True):
        self.chat.configure(state="normal")
        if who == "hy":
            self.chat.insert("end", "Hy\n", "hy_name")
        else:
            self.chat.insert("end", "Superhero\n", "hero_name")
        self.chat.insert("end", text + "\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    # --- streaming jawab: shabd-dar-shabd screen par (v3.7.2 tez fix) ---
    def _stream_begin(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", "Superhero\n", "hero_name")
        self.chat.insert("end", text)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _stream_add(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", text)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _stream_finish(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", "\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def set_status(self, text):
        self.status.configure(text=text)

    # ---------- setup: is the brain here? ----------
    def _tags(self):
        try:
            with urllib.request.urlopen(OLLAMA_TAGS, timeout=2) as r:
                return json.loads(r.read())
        except Exception:
            return None

    # Saaf Hinglish sandesh — raw English error kabhi nahi dikhega
    MSG_NO_OLLAMA = ("Mera dimaag is laptop par laga hi nahi hai, isliye mai abhi "
                     "soch nahi pa raha. Ghabrana nahi — bas baayein taraf wala "
                     "“Dimaag Lagao (ek click)” button ek baar dabao, sab khud ho jayega. "
                     "Uske baad app band karke dobara kholna.")
    MSG_OLLAMA_DOWN = ("Mera dimaag abhi band hai (so raha hai). Mai use khud chalane ki koshish "
                       "kar raha hoon — 10 second ruko aur phir dobara bolo. "
                       "Phir bhi na chale to app band karke Superhero-App.bat dobara chalao.")

    def _try_start_serve(self):
        """Engine program mil jaye lekin woh so raha ho to khud jaga do."""
        exe = find_ollama()
        if not exe:
            return False
        try:
            subprocess.Popen([exe, "serve"],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            return False
        # kuch seconds tak retry — server ko jaagne ka samay do
        for _ in range(10):
            time.sleep(1)
            if self._tags() is not None:
                return True
        return self._tags() is not None

    def check_setup(self):
        def work():
            tags = self._tags()
            if tags is None:
                # server band ho sakta hai — khud chalu karke dekho
                self._try_start_serve()
                tags = self._tags()
            if tags is None:
                if find_ollama() is None:
                    # Engine hi nahi hai — saaf sandesh + ek-click button
                    def show_missing():
                        self.set_status("Dimaag laga hi nahi hai — neeche wala button dabao")
                        self.btn_brain.pack_forget()
                        self.btn_install.pack(fill="x", padx=12, pady=(2, 4))
                        self.btn_site.pack(fill="x", padx=12, pady=(2, 10))
                        self.say("hero", self.MSG_NO_OLLAMA, store=False)
                    self.root.after(0, show_missing)
                else:
                    self.root.after(0, lambda: self.set_status(
                        "Dimaag so raha hai — app dobara kholo, mai khud chalu kar dunga"))
                return
            names = [m.get("name", "") for m in tags.get("models", [])]
            if any(n.split(":")[0] == MODEL.split(":")[0] for n in names):
                self.root.after(0, lambda: (self.set_status("taiyaar hai • offline"),
                                            self.btn_brain.pack_forget(),
                                            self.btn_install.pack_forget(),
                                            self.btn_site.pack_forget()))
            else:
                self.root.after(0, lambda: (self.set_status("dimaag download baki hai — neeche button dabao"),
                                            self.btn_install.pack_forget(),
                                            self.btn_brain.pack(fill="x", padx=12, pady=(2, 10))))
        threading.Thread(target=work, daemon=True).start()

    def install_ollama(self):
        """Ek click: saath wali Dimaag-Lagao.bat chalao (install + download wahi karegi)."""
        bat = os.path.join(core.BASE, "Dimaag-Lagao.bat")
        if not os.path.isfile(bat):
            bat = os.path.join(core.BASE, "Ollama-Lagao.bat")  # purana naam (compat)
        if not os.path.isfile(bat):
            self.set_status("Dimaag-Lagao.bat packet me nahi mili — Muse ko bolo")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(bat)  # noqa: S606 — Hy ke khud ke packet ki file
            else:
                subprocess.Popen(["cmd", "/c", bat])
            self.set_status("Dimaag lag raha hai — khuli hui kaali khidki khatm hone do, "
                            "phir app dobara kholo")
            self.say("hero", "Dimaag lagna shuru ho gaya hai. Jo khidki khuli hai use "
                             "khatm hone do (usme model bhi khud download hoga), "
                             "phir is app ko band karke dobara kholo.", store=False)
        except OSError as e:
            self.set_status(f"Dimaag-Lagao.bat khul nahi payi: {e}")

    def download_brain(self):
        exe = find_ollama()
        if not exe:
            self.say("hero", self.MSG_NO_OLLAMA, store=False)
            self.check_setup()
            return
        self.btn_brain.configure(state="disabled", text="Download ho raha hai…")
        self.set_status("dimaag aa raha hai… 0% — kuch minute lagenge, khidki khuli rakho")

        def work():
            ok = False
            try:
                p = subprocess.Popen([exe, "pull", MODEL], stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                last_line = ""
                for raw in p.stdout:
                    line = raw.strip()
                    if not line:
                        continue
                    # engine ki progress line se % nikalo, saaf status dikhao
                    clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line)
                    pct = re.search(r"(\d{1,3})\s*%", clean)
                    if pct:
                        msg = f"dimaag aa raha hai… {pct.group(1)}%"
                    elif "pulling" in clean.lower() or "verifying" in clean.lower() \
                            or "writing" in clean.lower() or "success" in clean.lower():
                        msg = "dimaag aa raha hai… " + clean[-60:]
                    else:
                        continue
                    if msg != last_line:
                        last_line = msg
                        self.root.after(0, lambda m=msg: self.set_status(m))
                p.wait()
                ok = p.returncode == 0
            except OSError:
                ok = False

            def finish():
                self.btn_brain.configure(state="normal", text="🧠 Dimaag download karo")
                if ok:
                    self.set_status("dimaag taiyaar hai! Ab baat kar sakte ho • offline")
                else:
                    self.set_status("download pura nahi hua — internet dekh kar button dobara dabao")
                self.check_setup()
            self.root.after(0, finish)
        threading.Thread(target=work, daemon=True).start()

    # ---------- update (sirf Hy ke aadesh par) ----------
    def _set_update_status(self, text):
        self.update_status.configure(text=text)

    def check_update_clicked(self):
        self._set_update_status("Update dekha ja raha hai…")
        self.btn_update.configure(state="disabled")

        def work():
            info = updater.check_update()

            def done():
                self.btn_update.configure(state="normal")
                if info["status"] == "available":
                    self._set_update_status(info["message"])
                    self.btn_apply.pack(fill="x", padx=12, pady=(2, 10))
                    notes = ("\n" + info.get("notes", "")) if info.get("notes") else ""
                    self.say("hero", info["message"] + notes +
                             "\nLagana ho to baayein taraf “Update lagao” dabao — "
                             "tumhari yaadein (memory) bilkul surakshit rahengi.", store=False)
                else:
                    self._set_update_status(info["message"])
                    self.btn_apply.pack_forget()
            self.root.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    def apply_update_clicked(self):
        self.btn_apply.configure(state="disabled")
        self.btn_update.configure(state="disabled")
        self._set_update_status("Update lag raha hai… khidki band mat karna")

        def work():
            ok, msg = updater.apply_update(
                progress=lambda m: self.root.after(0, lambda: self._set_update_status(m)))

            def done():
                self.btn_update.configure(state="normal")
                self.btn_apply.configure(state="normal")
                self._set_update_status(msg if ok else "Update nahi laga — " + msg)
                if ok:
                    self.btn_apply.pack_forget()
                    self._set_update_status(
                        f"Version v{updater.current_version()} • " + msg)
                self.say("hero", msg, store=False)
            self.root.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    # ---------- permission popup (the program asks; the brain cannot) ----------
    def gui_ask(self, question):
        self._ask_question = question
        self._ask_answer = None
        self._ask_event.clear()
        self._ask_event.wait(timeout=180)
        return self._ask_answer or "na"

    def _poll_ask(self):
        if self._ask_question and not self._ask_event.is_set():
            q, self._ask_question = self._ask_question, None
            win = tk.Toplevel(self.root)
            win.title("Ijazat")
            win.configure(bg=BG)
            win.geometry("430x170")
            win.transient(self.root)
            win.grab_set()
            tk.Label(win, text="🔐 " + q.split("\n")[0], wraplength=400,
                     font=("Segoe UI", 11), bg=BG, fg=INK).pack(pady=14)
            row = tk.Frame(win, bg=BG)
            row.pack()
            def done(ans):
                self._ask_answer = ans
                self._ask_event.set()
                win.destroy()
            tk.Button(row, text="Ha, kholo", command=lambda: done("ha"), bg=CLAY, fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
            tk.Button(row, text="Na", command=lambda: done("na"),
                      font=("Segoe UI", 10), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
            tk.Button(row, text="Hamesha ke liye ha", command=lambda: done("hamesha"),
                      font=("Segoe UI", 10), relief="flat", padx=10, pady=4).pack(side="left", padx=4)
        self.root.after(200, self._poll_ask)

    # ---------- talking ----------
    def on_send(self):
        text = self.entry.get().strip()
        if not text or self.busy:
            return
        self.entry.delete(0, "end")
        self.say("hy", text)
        for token in re.findall(r"[A-Za-z]:\\[^\s\"']+", text):
            self.hy_named_paths.add(token)
        for token in re.findall(r'"([^"]+)"', text):
            if "\\" in token or "/" in token:
                self.hy_named_paths.add(token)
        self.busy = True
        self.set_status("soch raha hai…")
        threading.Thread(target=self._think, args=(text,), daemon=True).start()

    def _think(self, text):
        self.history.append({"role": "user", "content": text})
        stream_state = {"shown": False}

        def make_cb():
            st = {"buf": "", "shown": False}

            def cb(delta):
                st["buf"] += delta
                s = st["buf"].lstrip()
                if st["shown"]:
                    self.root.after(0, lambda d=delta: self._stream_add(d))
                    return
                if s.startswith("{"):
                    return  # tool-call JSON screen par kabhi nahi dikhana
                if len(s) < 2:
                    return  # pehla tukda "{" ho sakta hai — pakka karke dikhao
                st["shown"] = True
                stream_state["shown"] = True
                self.root.after(0, lambda t=st["buf"]: self._stream_begin(t))

            return cb
        reply = program_reply(text)  # pakke kaam (salaam/padhai) — model se pehle (v3.8.3)
        if reply is None:
            messages = [{"role": "system", "content": core.system_prompt()}] + self.history[-12:]
            try:
                reply = core.ask_brain(messages, on_chunk=make_cb()).strip()
                if reply.startswith("{") and '"tool"' in reply:
                    call = json.loads(reply)
                    if call.get("tool") == "open_path":
                        result = core.guard_open(call.get("args", {}).get("path", ""),
                                                 self.hy_named_paths, ask=self.gui_ask)
                    else:
                        fn = core.TOOLS.get(call.get("tool", ""))
                        result = fn(**call.get("args", {})) if fn else "Ye haath abhi mere paas nahi hai."
                    self.history.append({"role": "assistant", "content": reply})
                    messages = ([{"role": "system", "content": core.system_prompt()}] + self.history[-12:]
                                + [{"role": "user", "content": f"(haath ka natija: {result}) Ab Hy ko apne shabdon me bata do."}])
                    reply = core.ask_brain(messages, on_chunk=make_cb()).strip()
            except Exception as e:
                # Raw English/Python error kabhi mat dikhao — wajah ke hisaab se saaf Hinglish
                err = str(e).lower()
                if "10061" in err or "connection" in err or "urlopen" in err or "refused" in err:
                    if find_ollama() is None:
                        reply = self.MSG_NO_OLLAMA
                    else:
                        reply = self.MSG_OLLAMA_DOWN
                        threading.Thread(target=self._try_start_serve, daemon=True).start()
                else:
                    reply = ("Abhi jawab dene me kuch gadbad ho gayi. Ek baar phir bol kar dekho — "
                             "na ho to app band karke dobara kholo.")
                self.root.after(0, self.check_setup)
        self.history.append({"role": "assistant", "content": reply})
        def done_ui():
            if stream_state["shown"]:
                self._stream_finish()
            else:
                self.say("hero", reply)
            self.set_status("taiyaar hai • offline")
            self.busy = False
            self.save_chat()
            self.refresh_chat_list()
        self.root.after(0, done_ui)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        SuperheroApp(root)
        threading.Thread(target=core.warm_up, daemon=True).start()
        root.mainloop()
    except Exception:
        # Never die silently in a black window: leave the reason in a file
        # Hy can read out, so the fault can be found and fixed.
        import traceback
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "superhero-error.txt"), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise
