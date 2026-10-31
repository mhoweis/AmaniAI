"""Amani on Telegram. Run: python bot.py   (needs TELEGRAM_BOT_TOKEN and GEMINI_API_KEY)

How a worker uses it:
  1. Says or types what they were promised (salary, housing, fees…)   -> stored as context
  2. Sends the contract or message: photo, PDF, any file, pasted text, or a forwarded SMS
  3. Gets the verdict, Promise vs Paper, fraud checks, a voice note, and a "check this company" button
Uses long polling, so it runs from a laptop: no server or public URL needed.
"""

import html
import io
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from amani import analyze, company_background, link_findings, transcribe
from docs import ALERT_SIGNALS, extract
from ui_text import AUTO, HINT_NAMES, HINT_TO_UI, detect_script, texts

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}/"
FILE_API = f"https://api.telegram.org/file/bot{TOKEN}/"
MAX_FILE = 20 * 1024 * 1024  # Telegram bot download limit

VERDICT_ICON = {"do_not_sign": "🛑", "ask_someone_first": "⚠️", "continue_carefully": "🟡", "cannot_tell": "❓"}
CATEGORY_ICON = {"money": "💰", "rights": "⚖️", "data": "🔐", "control": "🛂", "fraud_sign": "🚩", "missing_info": "❔"}
STATUS_ICON = {"different": "❌", "not_in_document": "📝", "matches": "✅"}
LANG_BUTTONS = [AUTO, "Gulf Arabic", "Egyptian Arabic", "Levantine Arabic", "Urdu", "Hindi",
                "Indian Tamil", "Sri Lankan Tamil (Jaffna)", "Malayalam", "Bengali (Bangladesh)",
                "Tagalog", "Nepali", "English"]

BOT_TEXT = {
    "en": {"step_hint": "Tell me what you were promised (type it or send a voice note). Then send the contract or message: a photo, PDF, any file, or paste the text.",
           "noted": "🤝 Noted what you were promised:", "is_this": "Is this the contract or message to check, or what you were promised?",
           "btn_check": "✅ Check this", "btn_promise": "🤝 This is what I was promised",
           "working": "🔍 Checking… this takes about 20 seconds.", "heard": "🎤 I heard:",
           "lang_set": "Okay, I'll talk to you in:", "reset_done": "Fresh start.", "choose_lang": "Choose your language:",
           "too_big": "This file is too big. Please send a photo or a smaller file."},
    "ar": {"step_hint": "قول لي إيش وعدوك فيه (اكتب أو أرسل فويس). بعدين أرسل العقد أو الرسالة: صورة، PDF، أي ملف، أو الصق النص.",
           "noted": "🤝 سجّلت اللي وعدوك فيه:", "is_this": "هذا العقد أو الرسالة اللي تبيني أفحصها، ولا هذا اللي وعدوك فيه؟",
           "btn_check": "✅ افحص هذا", "btn_promise": "🤝 هذا اللي وعدوني فيه",
           "working": "🔍 جاري الفحص… ياخذ تقريباً 20 ثانية.", "heard": "🎤 سمعت:",
           "lang_set": "تمام، بكلمك بـ:", "reset_done": "بدينا من جديد.", "choose_lang": "اختر لغتك:",
           "too_big": "الملف كبير واجد. أرسل صورة أو ملف أصغر."},
    "hi": {"step_hint": "मुझे बताइए आपसे क्या वादा किया गया (लिखकर या वॉइस भेजकर)। फिर कॉन्ट्रैक्ट या मैसेज भेजिए: फ़ोटो, PDF, कोई भी फ़ाइल, या टेक्स्ट पेस्ट कीजिए।",
           "noted": "🤝 आपसे किया गया वादा नोट कर लिया:", "is_this": "क्या यह वह कॉन्ट्रैक्ट या मैसेज है जिसे जाँचना है, या यह वह है जो आपसे वादा किया गया?",
           "btn_check": "✅ इसे जाँचें", "btn_promise": "🤝 यह मुझसे किया गया वादा है",
           "working": "🔍 जाँच हो रही है… लगभग 20 सेकंड लगेंगे।", "heard": "🎤 मैंने सुना:",
           "lang_set": "ठीक है, मैं इस भाषा में बात करूँगी:", "reset_done": "नई शुरुआत।", "choose_lang": "अपनी भाषा चुनिए:",
           "too_big": "यह फ़ाइल बहुत बड़ी है। कृपया फ़ोटो या छोटी फ़ाइल भेजिए।"},
    "ur": {"step_hint": "مجھے بتائیں آپ سے کیا وعدہ کیا گیا (لکھ کر یا وائس بھیج کر)۔ پھر معاہدہ یا میسج بھیجیں: تصویر، PDF، کوئی بھی فائل، یا متن پیسٹ کریں۔",
           "noted": "🤝 آپ سے کیا گیا وعدہ نوٹ کر لیا:", "is_this": "کیا یہ وہ معاہدہ یا میسج ہے جسے چیک کرنا ہے، یا یہ وہ ہے جو آپ سے وعدہ کیا گیا؟",
           "btn_check": "✅ اسے چیک کریں", "btn_promise": "🤝 یہ مجھ سے کیا گیا وعدہ ہے",
           "working": "🔍 جانچ ہو رہی ہے… تقریباً 20 سیکنڈ لگیں گے۔", "heard": "🎤 میں نے سنا:",
           "lang_set": "ٹھیک ہے، میں اس زبان میں بات کروں گی:", "reset_done": "نئی شروعات۔", "choose_lang": "اپنی زبان چنیں:",
           "too_big": "یہ فائل بہت بڑی ہے۔ براہ کرم تصویر یا چھوٹی فائل بھیجیں۔"},
}
WELCOME = ("👋 Hello, I'm Amani!  ·  مرحبا، أنا أماني!  ·  ہیلو، میں امانی ہوں!  ·  नमस्ते, मैं अमानी हूँ!\n\n"
           "🛡️ I check contracts and messages before you sign, pay, or click, and compare them with what you were promised.")

# ---------- per-chat memory (in RAM only; nothing is written to disk) ----------
STATE: dict = {}
LOCK = threading.Lock()


def state(chat_id) -> dict:
    with LOCK:
        return STATE.setdefault(chat_id, {"hint": AUTO, "ctx": "", "ui": "en", "pending": "", "result": None})


def B(chat_id) -> dict:  # bot text in the chat's language
    return {**BOT_TEXT["en"], **BOT_TEXT.get(state(chat_id)["ui"], {})}


# ---------- Telegram API ----------
def call(method, files=None, **params):
    for k, v in list(params.items()):
        if isinstance(v, (dict, list)):
            params[k] = json.dumps(v, ensure_ascii=False)
    try:
        r = requests.post(API + method, data=params, files=files, timeout=70)
        res = r.json()
    except Exception as ex:  # noqa: BLE001
        print(f"❌ {method} failed: could not reach Telegram ({type(ex).__name__}: {str(ex)[:150]})")
        return {"ok": False}
    if method in ("sendMessage", "sendAudio"):
        if res.get("ok"):
            print(f"   ↩️  {method} delivered")
        else:
            print(f"❌ Telegram refused {method}: {res.get('description')}")
            if method == "sendMessage" and "parse" in str(res.get("description", "")).lower():
                params.pop("parse_mode", None)  # retry as plain text if formatting was the problem
                return requests.post(API + method, data=params, timeout=70).json()
    return res


def send(chat_id, text, buttons=None):
    params = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons:
        params["reply_markup"] = {"inline_keyboard": buttons}
    return call("sendMessage", **params)


def download(file_id) -> bytes | None:
    info = call("getFile", file_id=file_id)
    path = (info.get("result") or {}).get("file_path")
    if not path:
        return None
    return requests.get(FILE_API + path, timeout=60).content


# ---------- formatting a result for chat ----------
def e(x) -> str:
    return html.escape(str(x or ""))


def format_result(r: dict, T: dict) -> str:
    rec = r["recommendation"]
    lines = [f"{VERDICT_ICON[rec]} <b>{e(T['verdict'][rec])}</b>", f"<b>{e(r['headline'])}</b>", ""]
    promises = r.get("promise_check") or []
    if promises:
        lines.append(f"🤝 <b>{e(T['promise_title'])}</b>")
        for p in promises:
            lines.append(f"{STATUS_ICON[p['status']]} {e(T['told'])}: {e(p['promised'])}\n    ➜ {e(T['paper'])}: {e(p['document_says'] or T['status'][p['status']])}")
        lines.append("")
    alerts = [T["file_alert"][a] for a in r.get("file_alerts", []) if a in T["file_alert"]]
    alerts += [T["link_alert"][la["kind"]].format(host=la["host"].replace(".", "[.]"), brand=la["brand"])
               for la in r.get("link_alerts", [])]
    if alerts:
        lines.append(f"🛰️ <b>{e(T['code_checks'])}</b>")
        lines += [e(a) for a in alerts]
        lines.append("")
    if r["findings"]:
        lines.append(f"🔍 <b>{e(T['found'])}</b>")
        lines += [f"{CATEGORY_ICON[f['category']]} {e(f['explanation'])}" for f in r["findings"][:4]]
        lines.append("")
    lines.append(f"👣 <b>{e(T['next_step'])}:</b> {e(r['next_step'])}")
    if r["questions_to_ask"]:
        lines.append("\n".join(f"💬 {e(q)}" for q in r["questions_to_ask"]))
    if r.get("message_to_company"):
        lines.append(f"\n✉️ <b>{e(T['msg_title'])}</b>\n<code>{e(r['message_to_company'])}</code>")
    lines.append(f"\n🔒 {e(r['safety_line'])}")
    return "\n".join(lines)


def spoken(r: dict, T: dict, same: bool) -> str:
    parts = [T["verdict"][r["recommendation"]] + "." if same else "", r["headline"]]
    for p in r.get("promise_check") or []:
        if p["status"] != "matches":
            parts.append(f'{T["told"]}: {p["promised"]}. {T["paper"]}: {p["document_says"]}.' if same
                         else f'{p["promised"]}: {p["document_says"]}.')
    parts += [f["explanation"] for f in r["findings"][:3]] + [r["next_step"], r["safety_line"]]
    return " ".join(x.strip() for x in parts if x and x.strip())[:2500]


def voice_note(chat_id, r, T, lang, same):
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=spoken(r, T, same), lang=lang).write_to_fp(buf)
        call("sendAudio", chat_id=chat_id, title="Amani", performer="🔊",
             files={"audio": ("amani.mp3", buf.getvalue(), "audio/mpeg")})
    except Exception:  # noqa: BLE001
        pass  # the text result is already sent; audio is a bonus


# ---------- core actions ----------
def run_check(chat_id, document="", images=None, alerts=None, filename=""):
    st = state(chat_id)
    send(chat_id, B(chat_id)["working"])
    call("sendChatAction", chat_id=chat_id, action="typing")
    alerts = alerts or []
    r = analyze(document=document, user_context=st["ctx"],
                language_hint="" if st["hint"] == AUTO else st["hint"], images=images,
                file_signals=[ALERT_SIGNALS[a] for a in alerts if a in ALERT_SIGNALS])
    r["file_alerts"] = alerts
    r.setdefault("link_alerts", link_findings(document))
    st["result"] = r
    lang = r.get("reply_language_code", "en") if r.get("ok") else st["ui"]
    if st["hint"] == AUTO and r.get("ok") and not detect_script(st["ctx"]):
        st["ui"] = lang if lang in ("en", "ar", "hi", "ur") else st["ui"]
    T = texts(st["ui"])
    if not r.get("ok"):
        send(chat_id, f"❓ <b>{e(T['err_head'])}</b>\n{e(T['err_next'])}")
        return
    buttons = [[{"text": T["bg_button"], "callback_data": "bg"}]] if r.get("company_name") else None
    send(chat_id, format_result(r, T), buttons)
    voice_note(chat_id, r, T, lang, same=(lang == st["ui"]))


def add_promise(chat_id, text):
    st = state(chat_id)
    st["ctx"] = f"{st['ctx']} {text}".strip()
    if st["hint"] == AUTO:
        st["ui"] = detect_script(st["ctx"]) or st["ui"]
    b = B(chat_id)
    send(chat_id, f"{b['noted']}\n<i>{e(st['ctx'][-600:])}</i>\n\n{b['step_hint']}")


def run_background(chat_id):
    st = state(chat_id)
    r, T = st.get("result") or {}, texts(st["ui"])
    name = r.get("company_name")
    if not name:
        send(chat_id, e(T["bg_no_name"]))
        return
    send(chat_id, e(T["bg_working"]))
    bg = company_background(name, r.get("detected_variety") or r.get("detected_language") or "English")
    if not bg.get("ok"):
        send(chat_id, e(T["bg_failed"]))
        return
    lines = [f"🏢 <b>{e(T['bg_title'])}: {e(name)}</b>", f"<i>{e(T['bg_sub'])}</i>", ""]
    if bg["scam_reports_found"]:
        lines.append(f"🚨 <b>{e(T['bg_reports'])}</b>")
    if bg["impersonation_risk"]:
        lines.append(f"🎭 {e(T['bg_imperson'])}")
    lines.append(e(bg["summary"]) if bg["found"] else e(T["bg_none"]))
    lines += [f"⚠️ {e(w)}" for w in bg["warning_signs"]]
    if bg["official_website"]:
        lines.append(f"🌐 {e(T['bg_site'])}: {e(bg['official_website'])}")
    lines.append(f"\n{e(T['bg_sources'])}: {e(' · '.join(bg['sources']))}")
    send(chat_id, "\n".join(lines))


def language_menu(chat_id):
    T = texts(state(chat_id)["ui"])
    rows, row = [], []
    for h in LANG_BUTTONS:
        row.append({"text": T["auto"] if h == AUTO else HINT_NAMES[h], "callback_data": f"lang:{h}"})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    send(chat_id, f"🌐 {B(chat_id)['choose_lang']}", rows)


# ---------- update handlers ----------
URL_HINT = re.compile(r"https?://|www\.|\.(com|ae|xyz|top|online|site|link|info)\b", re.I)


def on_message(msg):
    chat_id = msg["chat"]["id"]
    st = state(chat_id)
    text = (msg.get("text") or "").strip()
    caption = (msg.get("caption") or "").strip()

    if text.startswith("/start"):
        send(chat_id, WELCOME)
        language_menu(chat_id)
        return
    if text.startswith("/lang"):
        language_menu(chat_id)
        return
    if text.startswith("/reset"):
        with LOCK:  # forget the conversation, keep the chosen language
            old = STATE.pop(chat_id, {})
        state(chat_id).update({"hint": old.get("hint", AUTO), "ui": old.get("ui", "en")})
        send(chat_id, f"{B(chat_id)['reset_done']} {B(chat_id)['step_hint']}")
        return

    voice = msg.get("voice") or msg.get("audio")
    if voice:
        data = download(voice["file_id"])
        heard = transcribe(data or b"", voice.get("mime_type") or "audio/ogg")
        if not heard["ok"]:
            send(chat_id, e(texts(st["ui"])["voice_failed"]))
            return
        if heard.get("language_code") in ("ar", "hi", "ur", "en") and st["hint"] == AUTO:
            st["ui"] = heard["language_code"]
        send(chat_id, f"{B(chat_id)['heard']} <i>{e(heard['transcript'])}</i>")
        add_promise(chat_id, heard["transcript"])
        return

    if caption:  # a caption on a photo/file is the person talking about it
        st["ctx"] = f"{st['ctx']} {caption}".strip()

    if msg.get("photo"):
        data = download(msg["photo"][-1]["file_id"])
        run_check(chat_id, images=[(data, "image/jpeg")] if data else None)
        return

    doc = msg.get("document")
    if doc:
        if (doc.get("file_size") or 0) > MAX_FILE:
            send(chat_id, B(chat_id)["too_big"])
            return
        name = doc.get("file_name") or "file"
        data = download(doc["file_id"]) or b""
        f = extract(name, data, doc.get("mime_type") or "")
        if not (f["text"].strip() or f["images"] or "dangerous_file" in f["alerts"]):
            send(chat_id, e(texts(st["ui"])["file_alert"]["unsupported"]))
            return
        document = f"--- {name} ---\n{f['text']}" if f["text"].strip() else ""
        run_check(chat_id, document=document, images=f["images"], alerts=f["alerts"], filename=name)
        return

    if text:
        if st["hint"] == AUTO and detect_script(text):
            st["ui"] = detect_script(text) if detect_script(text) in BOT_TEXT else st["ui"]
        forwarded = bool(msg.get("forward_origin") or msg.get("forward_date"))
        if forwarded or URL_HINT.search(text) or len(text) > 300:
            run_check(chat_id, document=text)  # looks like the contract or a scam message itself
        else:
            st["pending"] = text
            b = B(chat_id)
            send(chat_id, f"<i>{e(text)}</i>\n\n{b['is_this']}",
                 [[{"text": b["btn_check"], "callback_data": "check"}],
                  [{"text": b["btn_promise"], "callback_data": "promise"}]])


def on_callback(cb):
    chat_id = cb["message"]["chat"]["id"]
    data = cb.get("data") or ""
    call("answerCallbackQuery", callback_query_id=cb["id"])
    st = state(chat_id)
    if data.startswith("lang:"):
        hint = data[5:]
        st["hint"] = hint if hint in HINT_NAMES else AUTO
        if st["hint"] != AUTO:
            st["ui"] = HINT_TO_UI.get(st["hint"], "en")
        label = texts(st["ui"])["auto"] if st["hint"] == AUTO else HINT_NAMES[st["hint"]]
        send(chat_id, f"{B(chat_id)['lang_set']} <b>{e(label)}</b>\n\n{B(chat_id)['step_hint']}")
    elif data == "check" and st["pending"]:
        text, st["pending"] = st["pending"], ""
        run_check(chat_id, document=text)
    elif data == "promise" and st["pending"]:
        text, st["pending"] = st["pending"], ""
        add_promise(chat_id, text)
    elif data == "bg":
        run_background(chat_id)


def handle(update):
    try:
        if "message" in update:
            on_message(update["message"])
        elif "callback_query" in update:
            on_callback(update["callback_query"])
    except Exception as ex:  # noqa: BLE001  never let one chat crash the bot
        import traceback
        print("❌ Error while answering:", type(ex).__name__, str(ex)[:300])
        traceback.print_exc(limit=3)
        chat = (update.get("message") or (update.get("callback_query") or {}).get("message") or {}).get("chat", {})
        if chat.get("id"):
            T = texts(state(chat["id"])["ui"])
            send(chat["id"], f"❓ {e(T['err_head'])}\n{e(T['err_next'])}")


def main():
    if not TOKEN:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN is missing. Add a line TELEGRAM_BOT_TOKEN=... to the .env file in this folder.")
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        print("⚠️  GEMINI_API_KEY is missing from .env: the bot will answer, but every check will fail.")
    try:
        me = call("getMe")
    except requests.RequestException as ex:
        raise SystemExit(f"❌ Can't reach Telegram from this computer: {ex}")
    if not me.get("ok"):
        raise SystemExit(f"❌ Telegram rejected the token: {me.get('description')}. Copy it again from @BotFather "
                         "(the whole thing, like 123456789:ABC...), with no spaces or quotes inside.")
    # A webhook left over from another tool blocks polling; remove it (pending messages are kept).
    call("deleteWebhook", drop_pending_updates=False)
    call("setMyCommands", commands=[{"command": "start", "description": "Start / choose language"},
                                    {"command": "lang", "description": "Change language"},
                                    {"command": "reset", "description": "Start over"}])
    print(f"✅ Amani is live on Telegram: https://t.me/{me['result']['username']}   (Ctrl+C to stop)")
    print("   Waiting for messages… each one is shown below.")
    pool, offset = ThreadPoolExecutor(max_workers=4), None
    while True:
        try:
            res = requests.get(API + "getUpdates", params={"timeout": 50, "offset": offset}, timeout=60).json()
        except requests.RequestException as ex:
            print(f"⚠️  Connection problem, retrying in 3 s: {type(ex).__name__}")
            time.sleep(3)
            continue
        if not res.get("ok"):
            code, desc = res.get("error_code"), res.get("description", "")
            if code == 409:
                print("❌ Another copy of this bot is already running (another terminal, or a webhook). "
                      "Close the other terminal, then start this one again.")
            else:
                print(f"❌ Telegram error {code}: {desc}")
            time.sleep(5)
            continue
        for update in res.get("result", []):
            offset = update["update_id"] + 1
            m = update.get("message") or {}
            kind = next((k for k in ("text", "voice", "audio", "photo", "document") if k in m), "button" if "callback_query" in update else "other")
            print(f"📩 {time.strftime('%H:%M:%S')}  {kind} from chat {(m.get('chat') or {}).get('id', '')}")
            pool.submit(handle, update)  # slow checks don't block other chats


if __name__ == "__main__":
    main()
