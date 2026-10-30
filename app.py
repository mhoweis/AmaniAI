"""Amani demo app. Run: python -m streamlit run app.py"""

import html
import io
from pathlib import Path
from urllib.parse import quote as urlquote

import streamlit as st

from amani import MODEL, analyze, company_background, transcribe
from docs import ALERT_SIGNALS, extract
from samples import SAMPLES
from ui_text import AUTO, HINT_NAMES, HINT_TO_UI, RTL, detect_script, texts

VERDICT_ICON = {"do_not_sign": "🛑", "ask_someone_first": "⚠️", "continue_carefully": "🟡", "cannot_tell": "❓"}
CATEGORY_ICON = {"money": "💰", "rights": "⚖️", "data": "🔐", "control": "🛂",
                 "fraud_sign": "🚩", "missing_info": "❔"}
STATUS_ICON = {"different": "❌", "not_in_document": "📝", "matches": "✅"}

st.set_page_config(page_title="Amani أماني", page_icon="🛡️", layout="centered")
ss = st.session_state
ss.setdefault("hint", AUTO)
ss.setdefault("ctx", "")
ss.setdefault("doc", "")
ss.setdefault("voice_round", 0)


# ---------- which language should the page be in? ----------
def cur_hint():
    return ss.get("hint") or AUTO


def page_language() -> str:
    """1) language the user picked, 2) script of what they wrote or said,
    3) language detected from voice or the last result, 4) English."""
    if cur_hint() != AUTO:
        return HINT_TO_UI.get(cur_hint(), "en")
    return detect_script(ss.ctx) or ss.get("auto_lang") or "en"


LANG = page_language()
T = texts(LANG)
HERE = Path(__file__).parent
# style.css first (its font @import must lead), then the brand tokens it reads from
CSS = (HERE / "style.css").read_text(encoding="utf-8")
for _tokens in (HERE / "design-system" / "tokens.css", HERE / "tokens.css"):  # optional brand tokens
    if _tokens.exists():
        CSS += "\n" + _tokens.read_text(encoding="utf-8")
        break
st.markdown(
    f"<style>{CSS}\n.stApp {{ direction: {'rtl' if LANG in RTL else 'ltr'}; }}</style>",
    unsafe_allow_html=True,
)


# ---------- helpers ----------
def e(text) -> str:
    """Escape model or user text before putting it in HTML."""
    return html.escape(str(text or ""))


def d(lang) -> str:
    return "rtl" if lang in RTL else "ltr"


def show(markup: str):
    st.markdown(markup, unsafe_allow_html=True)


def step(num, title):
    show(f'<div class="step"><span class="num">{num}</span>{e(title)}</div>')


def make_audio(text, lang):
    """Turn text into speech. Returns mp3 bytes, or False if this language has no voice."""
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:  # noqa: BLE001
        return False


def page_lang_for(reply_lang):
    """Language the page will be in after this result (same rules as page_language)."""
    if cur_hint() != AUTO:
        return HINT_TO_UI.get(cur_hint(), "en")
    return detect_script(ss.ctx) or reply_lang or "en"


def _defang_host(host):
    return host.replace(".", "[.]")


def spoken_result(r, lang, page_lang=None) -> str:
    """The whole result as one script to read aloud, most important first."""
    page_lang = page_lang or LANG
    T = texts(page_lang)  # noqa: N806
    same = lang == page_lang  # only use page labels when they match the reply language
    parts = []
    if same:
        parts.append(T["verdict"][r["recommendation"]] + ".")
    parts.append(r["headline"])
    for p in r.get("promise_check") or []:
        if p["status"] != "matches":
            if same:
                parts.append(f'{T["told"]}: {p["promised"]}. {T["paper"]}: {p["document_says"] or T["status"][p["status"]]}.')
            else:
                parts.append(f'{p["promised"]}: {p["document_says"]}.')
    parts += [f["explanation"] for f in r["findings"][:3]]
    if same:
        parts.append(T["next_step"] + ":")
    parts.append(r["next_step"])
    parts.append(r["safety_line"])
    return " ".join(x.strip() for x in parts if x and x.strip())[:2500]


def load_sample(name):
    sample = SAMPLES[name]
    if isinstance(sample, str):  # older samples.py: document text only
        sample = (sample, "", AUTO)
    doc, ctx, hint = sample
    ss.doc, ss.ctx = doc, ctx
    ss.hint = hint if hint in HINT_NAMES else AUTO
    for k in ("result", "result_audio", "company_bg"):
        ss.pop(k, None)


def reset_recorder():
    ss.voice_round += 1


# ---------- hero (team design) ----------
GREETINGS = ["Hello, I'm Amani!", "مرحبا، أنا أماني!", "ہیلو، میں امانی ہوں!",
             "नमस्ते, मैं अमानी हूँ!", "வணக்கம், நான் அமானி!", "Kumusta, ako si Amani!"]
LOGO = ('<svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><path d="M5 30V15a12 12 0 0 1 24 0v15h-7v-9'
        'a5 5 0 0 0-10 0v9z" fill="#2b7a6b"/></svg>')
ROBOT = """<svg class="robot" width="230" height="250" viewBox="0 0 200 220" role="img" aria-label="Amani robot">
  <ellipse cx="100" cy="212" rx="44" ry="5" fill="#1d3b35" opacity=".08"/>
  <line x1="100" y1="20" x2="100" y2="36" stroke="#2b7a6b" stroke-width="5" stroke-linecap="round"/>
  <circle cx="100" cy="15" r="7" fill="#2b7a6b"/>
  <rect x="31" y="64" width="15" height="42" rx="7.5" fill="#2b7a6b"/>
  <rect x="154" y="64" width="15" height="42" rx="7.5" fill="#2b7a6b"/>
  <rect x="40" y="34" width="120" height="100" rx="38" fill="#f6f3ea" stroke="#e2ddd0" stroke-width="2"/>
  <rect x="55" y="53" width="90" height="60" rx="26" fill="#1f4a42"/>
  <ellipse cx="81" cy="79" rx="9" ry="11" fill="#c6ecdd"/><ellipse cx="119" cy="79" rx="9" ry="11" fill="#c6ecdd"/>
  <circle cx="84" cy="75" r="3" fill="#fff"/><circle cx="122" cy="75" r="3" fill="#fff"/>
  <path d="M88 96 q12 10 24 0" stroke="#c6ecdd" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M66 152 q-24 6 -30 30" stroke="#e2ddd0" stroke-width="12" fill="none" stroke-linecap="round"/>
  <circle cx="35" cy="186" r="11" fill="#2b7a6b"/>
  <path d="M134 152 q22 -6 26 -32" stroke="#e2ddd0" stroke-width="12" fill="none" stroke-linecap="round"/>
  <circle cx="161" cy="116" r="11" fill="#2b7a6b"/>
  <rect x="66" y="136" width="68" height="62" rx="22" fill="#f6f3ea" stroke="#e2ddd0" stroke-width="2"/>
  <circle cx="100" cy="164" r="11" fill="#2b7a6b"/>
  <path d="M95 164 l4 4 l7 -8" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <ellipse cx="84" cy="203" rx="13" ry="6" fill="#8fb8ab"/><ellipse cx="116" cy="203" rx="13" ry="6" fill="#8fb8ab"/>
</svg>"""

greet = "".join(f'<span dir="auto">{e(g)}</span>' for g in GREETINGS)
show(f"""
<div class="topbar">
  <div class="logo">{LOGO}<span>amani<span class="dot">.</span></span></div>
  <div class="motto">{e(T["motto"])}</div>
</div>
<div class="hero">
  <div class="eyebrow">{e(T["eyebrow"])}</div>
  <div class="bubble"><div class="greet">{greet}</div></div>
  <div class="robot-wrap">
    <span class="spark" style="top:30px;right:6px">✦</span><span class="spark" style="top:120px;left:0">✧</span>
    {ROBOT}
  </div>
</div>""")

st.pills(
    T["lang_label"], list(HINT_NAMES), key="hint", label_visibility="collapsed",
    format_func=lambda h: T["auto"] if h == AUTO else HINT_NAMES[h],
)
show(f'<div class="pills-caption">{e(T["pills_caption"])}</div>')

show(f"""
<div class="hero">
  <div class="headline">{e(T["h1"])}<span class="accent">{e(T["h2"])}</span></div>
  <div class="subline">{e(T["subline"])}</div>
</div>
<div class="features">
  <div class="feature"><span class="ico">🤝</span>{e(T["feat1"])}<span class="arrow">↗</span></div>
  <div class="feature"><span class="ico">🏢</span>{e(T["feat2"])}<span class="arrow">↗</span></div>
  <div class="feature"><span class="ico">🗣️</span>{e(T["feat3"])}<span class="arrow">↗</span></div>
</div>""")

# ---------- step 2: what were you promised (voice or text) ----------
step(1, T["step2"])
audio = st.audio_input(T["voice_label"], key=f"voice_{ss.voice_round}")
if audio is not None:
    st.caption(T["voice_review"])
    col_send, col_delete = st.columns(2)
    send = col_send.button(T["voice_send"], type="primary", use_container_width=True)
    col_delete.button(T["voice_delete"], on_click=reset_recorder, use_container_width=True)
    if send:
        with st.spinner(T["voice_working"]):
            heard = transcribe(audio.getvalue(), audio.type or "audio/wav")
        if heard["ok"]:
            ss.ctx = f"{ss.ctx.strip()} {heard['transcript']}".strip()  # add, don't replace
            if heard["language_code"]:
                ss.auto_lang = heard["language_code"]
            ss.voice_note = "added"
            ss.voice_debug = f"Voice model: {heard.get('model')}"
            reset_recorder()
            st.rerun()
        else:
            ss.voice_note = "failed"
            ss.voice_debug = f"Voice error: {heard.get('error')}"

note = ss.pop("voice_note", None)
if note == "added":
    st.success(T["voice_added"])
elif note == "failed":
    st.warning(T["voice_failed"])

st.text_area(T["ctx_label"], key="ctx", placeholder=T["ctx_placeholder"], height=100)

# ---------- step 3: the paper ----------
step(2, T["step3"])
tab_text, tab_photo = st.tabs([T["tab_text"], T["tab_photo"]])
with tab_text:
    st.text_area(T["doc_label"], key="doc", height=200, label_visibility="collapsed",
                 placeholder=T["doc_label"])
    with st.expander(T["samples"]):
        for name in SAMPLES:
            st.button(name, on_click=load_sample, args=(name,), use_container_width=True)
with tab_photo:
    upload = st.file_uploader(T["photo_label"], type=None, key=f"upload_{ss.get('upload_round', 0)}")
    if upload:
        file_id = f"{upload.name}:{upload.size}"
        if ss.get("file_id") != file_id:  # read each file once
            ss.file_id = file_id
            ss.file = extract(upload.name, upload.getvalue(), upload.type or "")
        f = ss.file
        show(f'<div class="file-chip">📎 <b>{e(upload.name)}</b> · {len(f["text"]):,} ✎ · {len(f["images"])} 🖼️</div>')
        for code in f["alerts"]:
            show(f'<div class="file-alert a-{code}">{e(T["file_alert"][code])}</div>')
        if f["images"] and f["kind"] != "pdf (scanned)":
            st.image(f["images"][0][0], use_container_width=True)
    else:
        ss.pop("file", None)
        ss.pop("file_id", None)

st.write("")
if st.button(f"🛡️  {T['check']}", type="primary", use_container_width=True):
    f = ss.get("file") if upload else None
    has_file = bool(f and (f["text"].strip() or f["images"] or "dangerous_file" in f["alerts"]))
    if not ss.doc.strip() and not has_file:
        st.warning(T["no_doc"])
    else:
        for k in ("result_audio", "company_bg"):
            ss.pop(k, None)
        document = ss.doc.strip()
        if has_file and f["text"].strip():
            document = f"{document}\n\n--- {upload.name} ---\n{f['text']}".strip()
        with st.spinner(T["spinner"]):
            ss.result = analyze(
                document=document,
                user_context=ss.ctx,
                language_hint="" if cur_hint() == AUTO else cur_hint(),
                images=f["images"] if has_file else None,
                file_signals=[ALERT_SIGNALS[a] for a in (f["alerts"] if has_file else []) if a in ALERT_SIGNALS],
            )
            ss.result["file_alerts"] = list(f["alerts"]) if has_file else []
            # Prepare the voice now, so "Listen" is ready the moment the result appears.
            if ss.result.get("ok"):
                r_lang = ss.result.get("reply_language_code", "en")
                ss.result_audio = make_audio(spoken_result(ss.result, r_lang, page_lang_for(r_lang)), r_lang)
        if cur_hint() == AUTO and ss.result.get("ok") and not detect_script(ss.ctx):
            ss.auto_lang = ss.result.get("reply_language_code") or "en"
        st.rerun()

# ---------- result ----------
r = ss.get("result")
if r:
    rec = r["recommendation"]
    lang = r.get("reply_language_code", "en") if r.get("ok") else LANG
    headline = r["headline"] if r.get("ok") else T["err_head"]
    show(f"""
<div class="verdict v-{rec}">
  <div class="v-icon">{VERDICT_ICON[rec]}</div>
  <div><div class="v-label">{e(T["verdict"][rec])}</div>
  <div class="v-head" dir="{d(lang)}">{e(headline)}</div></div>
</div>""")

    if not r.get("ok"):
        show(f'<div class="card next" dir="{d(LANG)}">{e(T["err_next"])}</div>')
    else:
        if ss.get("result_audio"):
            show(f'<div class="listen-label">{e(T["listen"])}</div>')
            st.audio(ss.result_audio, format="audio/mp3")
        elif ss.get("result_audio") is False:
            st.caption(T["audio_na"])

        # --- file and link alerts found by code ---
        alerts = [T["file_alert"][a] for a in r.get("file_alerts", []) if a in T["file_alert"]]
        for la in r.get("link_alerts", []):
            alerts.append(T["link_alert"][la["kind"]].format(host=_defang_host(la["host"]), brand=la["brand"]))
        if alerts:
            show(f'<div class="section"><h3>🛰️ {e(T["code_checks"])}</h3><p>{e(T["code_checks_sub"])}</p></div>')
            show("".join(f'<div class="card alert-row" dir="{d(LANG)}">{e(a)}</div>' for a in alerts))

        if r.get("language_note"):
            st.info(r["language_note"])

        # --- Promise vs paper: the signature feature ---
        promises = r.get("promise_check") or []
        if promises:
            show(f'<div class="section"><h3>🤝 {e(T["promise_title"])}</h3><p>{e(T["promise_sub"])}</p></div>')
            for p in promises:
                s = p["status"]
                quote = (f'<details><summary>{e(T["show_words"])}</summary>'
                         f'<div class="quote" dir="auto">“{e(p["quote"])}”</div></details>') if p.get("quote") else ""
                show(f"""
<div class="card s-{s} {'hero-promise' if s == 'different' else ''}" dir="{d(lang)}">
  <div class="pp">
    <div><div class="k">{e(T["told"])}</div><div class="v">{e(p["promised"])}</div></div>
    <div class="mid"><span class="badge">{STATUS_ICON[s]} {e(T["status"][s])}</span></div>
    <div><div class="k">{e(T["paper"])}</div><div class="v">{e(p["document_says"]) or "—"}</div></div>
  </div>{quote}
</div>""")

        # --- findings ---
        if r["findings"]:
            show(f'<div class="section"><h3>🔍 {e(T["found"])}</h3></div>')
            for f in r["findings"]:
                quote = ""
                if f["quote"]:
                    translated = (f'<div class="quote" dir="{d(lang)}">“{e(f["quote_translated"])}”</div>'
                                  if f["quote_translated"] else "")
                    quote = (f'<details><summary>{e(T["show_words"])}</summary>'
                             f'<div class="quote" dir="auto">“{e(f["quote"])}”</div>{translated}</details>')
                show(f"""
<div class="card sev-{f['severity']}" dir="{d(lang)}">
  <div class="f"><div class="ic">{CATEGORY_ICON[f['category']]}</div>
  <div><div>{e(f["explanation"])}</div>{quote}</div></div>
</div>""")

        # --- website / company ---
        if r["company_check"]:
            rows = "".join(
                f'<div class="check-row">{"🔎" if c["checked"] else "➖"} <b>{e(c["signal"])}</b>: {e(c["result"])}</div>'
                for c in r["company_check"])
            show(f'<div class="section"><h3>🌐 {e(T["company"])}</h3></div><div class="card" dir="{d(lang)}">{rows}</div>')

        # --- company background check (live web search, on request) ---
        name = r.get("company_name") or ""
        show(f'<div class="section"><h3>🏢 {e(T["bg_title"])}{": " + e(name) if name else ""}</h3>'
             f'<p>{e(T["bg_sub"])}</p></div>')
        bg = ss.get("company_bg")
        if not name:
            st.caption(T["bg_no_name"])
        elif bg is None:
            if st.button(T["bg_button"], use_container_width=True):
                with st.spinner(T["bg_working"]):
                    ss.company_bg = company_background(
                        name, r.get("detected_variety") or r.get("detected_language") or "English")
                st.rerun()
        elif not bg.get("ok"):
            st.warning(T["bg_failed"])
        else:
            alerts = ""
            if bg["scam_reports_found"]:
                alerts += f'<div class="bg-alert">🚨 {e(T["bg_reports"])}</div>'
            if bg["impersonation_risk"]:
                alerts += f'<div class="bg-alert soft">🎭 {e(T["bg_imperson"])}</div>'
            body = e(bg["summary"]) if bg["found"] else e(T["bg_none"])
            signs = "".join(f'<div class="q">⚠️ {e(w)}</div>' for w in bg["warning_signs"])
            site = (f'<div class="check-row">🌐 <b>{e(T["bg_site"])}:</b> {e(bg["official_website"])}</div>'
                    if bg["official_website"] else "")
            srcs = " · ".join(e(x) for x in bg["sources"])
            show(f"""
<div class="card" dir="{d(lang)}">{alerts}<div>{body}</div>{signs}{site}
  <div class="sources">{e(T["bg_sources"])}: {srcs}</div>
</div>""")

        # --- next step + questions ---
        show(f'<div class="section"><h3>👣 {e(T["next_step"])}</h3></div>'
             f'<div class="card next" dir="{d(lang)}">{e(r["next_step"])}</div>')
        if r["questions_to_ask"]:
            qs = "".join(f'<div class="q">💬 {e(q)}</div>' for q in r["questions_to_ask"])
            show(f'<div class="section"><h3>❓ {e(T["questions"])}</h3></div><div class="card" dir="{d(lang)}">{qs}</div>')

        # --- message to the company (copyable) ---
        msg = r.get("message_to_company") or ""
        if msg:
            show(f'<div class="section"><h3>✉️ {e(T["msg_title"])}</h3><p>{e(T["msg_hint"])}</p></div>')
            st.code(msg, language=None, wrap_lines=True)

        # --- share with a trusted person ---
        summary = f"{VERDICT_ICON[rec]} {T['verdict'][rec]}\n{r['headline']}\n{r['next_step']}\n— Amani"
        st.link_button(T["share"], f"https://wa.me/?text={urlquote(summary)}", use_container_width=True)

        show(f'<div class="safety" dir="{d(lang)}">🔒 {e(r["safety_line"])}</div>')
        if r.get("from_cache"):
            st.caption(T["cache_note"])

# ---------- team-only debug panel ----------
with st.sidebar:
    st.caption(f"Model: {MODEL}")
    st.caption(f"Page language: {LANG}")
    if ss.get("company_bg"):
        st.caption(f"Search model: {ss.company_bg.get('model') or ss.company_bg.get('error')}")
    if ss.get("voice_debug"):
        (st.error if ss.voice_debug.startswith("Voice error") else st.caption)(ss.voice_debug)
    if r:
        st.caption(f"Detected: {r.get('detected_variety') or r.get('detected_language')} "
                   f"({r.get('variety_confidence')} confidence)")
        if not r.get("ok"):
            st.error(r.get("error"))
        with st.expander("Raw JSON"):
            st.json(r)
