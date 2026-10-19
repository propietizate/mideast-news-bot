import os
import re
import html
import json
import time
import hashlib
import logging
import unicodedata
from calendar import timegm
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests

import ai
from config import FEEDS, CORE, EXCLUDE, CATEGORIES

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Config from environment ───────────────────────────────────────────────────
DRY_RUN          = os.getenv("DRY_RUN") == "1"      # imprime en vez de enviar
RUN_ONCE         = os.getenv("RUN_ONCE") == "1"     # un ciclo + resumen y termina
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
POLL_INTERVAL    = int(os.getenv("POLL_INTERVAL_MINUTES", "30")) * 60
DIGEST_HOURS     = sorted(int(h) for h in os.getenv("DIGEST_HOURS", "8,14,20").split(","))
TZ               = ZoneInfo(os.getenv("TZ_NAME", "America/Santiago"))
MAX_AGE_HOURS    = int(os.getenv("MAX_AGE_HOURS", "24"))
STATE_FILE       = Path(os.getenv("STATE_FILE", "/data/state.json"))
SUMMARY_CHARS    = 180
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

if not DRY_RUN and not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
    raise SystemExit("Faltan TELEGRAM_TOKEN / TELEGRAM_CHAT_ID")

# ── Keyword matching ──────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))

def compile_terms(terms):
    if not terms:
        return None
    parts = []
    for t in terms:
        t = normalize(t)
        parts.append(rf"\b{re.escape(t[:-1])}\w*" if t.endswith("*") else rf"\b{re.escape(t)}\b")
    return re.compile("|".join(parts))

CORE_RE    = compile_terms(CORE)
EXCLUDE_RE = compile_terms(EXCLUDE)
CAT_RES    = [(name, compile_terms(terms)) for name, terms in CATEGORIES]
LOCAL_CL_RE = compile_terms(["santiago", "providencia", "nunoa", "las condes", "concepcion",
                             "temuco", "antofagasta", "iquique", "boric", "kast"])
CHILE = CATEGORIES[0][0]

def categorize(title: str, text: str, feed: dict) -> str:
    if feed.get("cl") and LOCAL_CL_RE.search(text):
        return CHILE
    # Primero por titular; el resumen solo desempata si el titular no calza con nada
    for haystack in (title, text):
        for name, rx in CAT_RES:
            if rx is not None and rx.search(haystack):
                return name
    return CATEGORIES[-1][0]

# ── State ─────────────────────────────────────────────────────────────────────
def load_state() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            log.exception("State file corrupto, se parte de cero")
    return {"seen": [], "pending": [], "last_slot": ""}

def save_state(state: dict):
    state["seen"] = state["seen"][-20000:]  # lista ordenada: se descartan las más antiguas
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

# ── Feeds ─────────────────────────────────────────────────────────────────────
def clean(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()

def entry_time(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return timegm(parsed) if parsed else None

def to_item(entry, feed: dict):
    title = clean(entry.get("title", ""))
    link = entry.get("link", "")
    if not title or not link:
        return None
    source = feed["name"]
    summary = clean(entry.get("summary", "") or entry.get("description", ""))
    if "news.google.com" in feed["url"]:
        # Google News: "Titular - Medio"; el summary solo repite el titular
        source = entry.get("source", {}).get("title") or source
        title = re.sub(rf"\s+-\s+{re.escape(source)}$", "", title)
        summary = ""
    text = normalize(f"{title} {summary}")
    if not CORE_RE.search(text) or (EXCLUDE_RE and EXCLUDE_RE.search(text)):
        return None
    if len(summary) > SUMMARY_CHARS:
        summary = summary[:SUMMARY_CHARS].rsplit(" ", 1)[0] + "…"
    return {
        "title": title, "link": link, "source": source, "summary": summary,
        "category": categorize(normalize(title), text, feed), "ts": entry_time(entry) or time.time(),
    }

def title_key(title: str) -> str:
    return "t:" + re.sub(r"[^a-z0-9]", "", normalize(title))[:80]

def poll_once(state: dict) -> int:
    seen = set(state["seen"])
    cutoff = time.time() - MAX_AGE_HOURS * 3600
    new_count = 0
    for feed in FEEDS:
        try:
            r = requests.get(feed["url"], headers={"User-Agent": UA}, timeout=20)
            r.raise_for_status()
            entries = feedparser.parse(r.content).entries
        except Exception as e:
            log.error(f"Error polling {feed['name']}: {e}")
            continue
        added = 0
        for entry in entries:
            key = getattr(entry, "id", None) or entry.get("link", "") or entry.get("title", "")
            eid = hashlib.md5(key.encode()).hexdigest()
            if eid in seen:
                continue
            seen.add(eid)
            state["seen"].append(eid)
            ts = entry_time(entry)
            if ts and ts < cutoff:
                continue
            item = to_item(entry, feed)
            if not item:
                continue
            tkey = title_key(item["title"])  # misma nota en otro feed
            if tkey in seen:
                continue
            seen.add(tkey)
            state["seen"].append(tkey)
            state["pending"].append(item)
            added += 1
        new_count += added
        log.info(f"{feed['name']}: {len(entries)} entradas, {added} relevantes")
    log.info(f"Poll complete — {new_count} notas nuevas, {len(state['pending'])} pendientes.")
    return new_count

# ── Telegram ──────────────────────────────────────────────────────────────────
def send_telegram(message: str):
    if DRY_RUN:
        print(message + "\n" + "─" * 40)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    for _ in range(3):
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 429:
                time.sleep(r.json().get("parameters", {}).get("retry_after", 5))
                continue
            r.raise_for_status()
            return
        except Exception as e:
            log.error(f"Telegram send error: {e}")
            time.sleep(3)

def format_item(item: dict) -> str:
    e = lambda s: html.escape(s, quote=False)
    line = f"• <b>{e(item['title'])}</b>"
    if item["summary"]:
        line += f"\n{e(item['summary'])}"
    line += f"\n<a href=\"{html.escape(item['link'])}\">{e(item['source'])}</a>"
    return line

def format_story(title: str, summary: str, items: list) -> str:
    e = lambda s: html.escape(s, quote=False)
    links = " · ".join(f"<a href=\"{html.escape(i['link'])}\">{e(i['source'])}</a>" for i in items)
    return f"• <b>{e(title)}</b>\n{e(summary)}\n{links}"

def build_blocks(items: list, label: str) -> list:
    order = [name for name, _ in CATEGORIES]
    stories = ai.curate(items)
    if stories:
        stories.sort(key=lambda s: order.index(s[0]))  # sort estable: mantiene la relevancia de Claude
        blocks = [f"🗞️ <b>Resumen Medio Oriente — {label}</b>\n{len(stories)} noticias de {len(items)} notas"]
        rows = [(s[0], format_story(*s[1:])) for s in stories]
    else:
        items.sort(key=lambda i: (order.index(i["category"]) if i["category"] in order else 99, -i["ts"]))
        blocks = [f"🗞️ <b>Resumen Medio Oriente — {label}</b>\n{len(items)} notas"]
        rows = [(i["category"], format_item(i)) for i in items]
    current = None
    for category, text in rows:
        if category != current:
            current = category
            blocks.append(f"\n<b>{current}</b>")
        blocks.append(text)
    return blocks

def send_digest(state: dict, label: str):
    items = state["pending"]
    if not items:
        log.info("Sin notas pendientes, no se envía resumen.")
        return
    blocks = build_blocks(items, label)

    # Telegram corta en 4096 caracteres: se arma por bloques
    msg = ""
    for block in blocks:
        if len(msg) + len(block) + 2 > 4000:
            send_telegram(msg)
            time.sleep(1)
            msg = ""
        msg += block + "\n\n"
    if msg.strip():
        send_telegram(msg)
    state["pending"] = []
    log.info(f"Resumen enviado: {len(items)} notas.")

# ── Scheduling ────────────────────────────────────────────────────────────────
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

def current_slot(now: datetime):
    past = [h for h in DIGEST_HOURS if h <= now.hour]
    if past:
        return now.strftime("%Y-%m-%d") + f" {past[-1]:02d}", past[-1]
    return "", None  # antes del primer horario del día

def label_for(now: datetime, hour: int) -> str:
    return f"{DIAS[now.weekday()]} {now.strftime('%d-%m')} {hour:02d}:00"

def main():
    log.info("🚀 Middle East News Bot starting...")
    state = load_state()

    if RUN_ONCE:
        poll_once(state)
        now = datetime.now(TZ)
        send_digest(state, label_for(now, now.hour))
        save_state(state)
        return

    now = datetime.now(TZ)
    if not state["last_slot"]:
        # Primer arranque: no mandar resumen inmediato, esperar el próximo horario
        state["last_slot"] = current_slot(now)[0] or "init"
    send_telegram(
        "🤖 <b>Middle East News Bot activo</b>\n\n"
        f"{len(FEEDS)} fuentes, revisión cada {POLL_INTERVAL // 60} min.\n"
        f"Resúmenes a las {', '.join(f'{h:02d}:00' for h in DIGEST_HOURS)} (hora de Chile)."
    )

    while True:
        poll_once(state)
        now = datetime.now(TZ)
        slot, hour = current_slot(now)
        if slot and slot != state["last_slot"]:
            send_digest(state, label_for(now, hour))
            state["last_slot"] = slot
        save_state(state)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
