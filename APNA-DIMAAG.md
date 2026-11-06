# Superhero ka APNA DIMAAG — kya hai, kaise kaam karta hai (v3.2)

## Pehchan
- Superhero **kisi company ka agent nahi** hai — woh **Hy ka apna** hai.
- Andar ka free engine sirf **bhasha samajhne wala hissa**
  hai. Jaise kaan aur zubaan. Asli Superhero — uski pehchan, yaad, seekh —
  **100% uski apni** hai, bilkul khaali se shuru, sirf Hy se seekhi hui.
- Ye "apna dimaag" program ke andar bani ek parat hai (`apna_dimaag.py`).
  Imandari ki baat: base model ke andar ke weights isse nahi badalte —
  badalti aur majboot hoti hai Superhero ki **apni memory aur seekh**, jo
  asal me uski personality hai.

## Khud seekhna (Hy ko baar-baar train nahi karna padega)
Har baat-cheet me program khud:
1. **Tathya pehchanta hai** — jaise "mujhe chai pasand hai", "mera kaam X
   hai", "yaad rakho...", "aaj se..." — aur unhe usi pal Superhero ki apni
   memory (`memory/MEMORY.md`) me **[khud seekha]** nishan ke saath jod
   deta hai. Jo pehle se yaad hai, woh dobara nahi jodta.
2. **Seekhe hue kaam pehchanta hai** — "kaam seekho: ..." ya "har baar ..."
   wali baat ko seekhe kaam ki list me jod deta hai, taaki Superhero use
   bina dobara sikhaye dohra sake.
3. **Recall** — jawab dene se pehle program memory me se is baat se judi
   purani seekhi baatein dhoondh kar dimaag ko yaad dilata hai. Isiliye
   Superhero samay ke saath aur "apna" hota jayega.
4. **Never-forget** — jo memory me gaya woh kabhi nahi mita; seekh ka ek
   log bhi rehta hai (`memory/self_learned.jsonl`).

## Skills — sabse main taakat (v3.3 se)
Apne dimaag ke saath ab **Skills system** bhi jud gaya hai: Hy ke kehne par
Superhero kisi pate/text se **skill seekh** kar hamesha ke liye rakh leta
hai (memory/skills me — update bhi use nahi chhuta), milta-julta kaam aane
par khud sahi skill istemal karta hai, aur roz ek purani seekh ki dohraai
karta hai. Skill sirf text hoti hai — code kabhi nahi, chalayi kabhi nahi.
Poori baat: **SKILLS-SYSTEM.md**

## Internet — sirf Hy ki ijaazat se
- Superhero web search kar sakta hai (DuckDuckGo, bina key, bina paisa),
  par **har baar pehle Hy ki ijaazat** lagegi:
  - Hy khud bole "internet par dhoondho" — wahi ijaazat hai.
  - Ya Superhero ko bahar ki taaza jaankari chahiye ho to woh pehle
    poochhega: *"🌐 internet par dhoondhun? 'ha' bolo"* — bina "ha" ke
    search **kabhi** nahi chalegi.
- **Yaadein kabhi bahar nahi jati.** Search me sirf sawal jata hai;
  Superhero ki memory laptop ke andar hi rehti hai.

## Suraksha — purane taale wese hi
- Bina Hy ki ijaazat **koi file nahi khulti**, system me **koi badlaav
  nahi** hota. File kholne wala taala program me pehle jesa hi hai.
- Mitane/bhejne wala koi haath ab bhi nahi hai.
- **Delete switch waisa hi hai** — `delete-superhero.bat` (DELETE likhne
  par) aur Muse ke paas code-level control: Hy ke ek shabd par sab khatm.

## Unlimited • No Token
Ye sab laptop ke andar, free model se chalta hai — koi API nahi, koi key
nahi, koi token nahi, koi limit nahi. Internet sirf search ke pal lagega;
baaki sab offline.
