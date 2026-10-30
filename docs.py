"""Read any uploaded file into text and/or images for Amani, and flag file-level fraud tricks.

extract(name, data) -> {
    "text": str,                     # text found in the file (may be empty)
    "images": [(bytes, mime)],       # pictures to send to the model (photos, scanned PDF pages)
    "alerts": [code, ...],           # dangerous_file | pdf_active | hidden_link | truncated | unsupported
    "kind": str,                     # short label for debugging
}
"""

import email
import logging
import html
import io
import re
import zipfile
from email import policy
from urllib.parse import urlparse

logging.getLogger("pypdf").setLevel(logging.ERROR)
MAX_CHARS = 15000
MAX_PAGES_AS_IMAGES = 3

DANGEROUS = {"apk", "exe", "msi", "bat", "cmd", "com", "scr", "js", "vbs", "jar", "ps1", "sh",
             "docm", "xlsm", "pptm", "dotm", "dmg", "pkg", "iso", "lnk", "hta", "app"}
IMAGE_MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
CONVERT_IMAGES = {"gif", "bmp", "tif", "tiff", "heic", "heif"}
TEXT_LIKE = {"txt", "csv", "md", "json", "xml", "log", "tsv", "srt", "vcf", "ics"}

_TAG = re.compile(r"<[^>]+>")
_ANCHOR = re.compile(r"<a\b[^>]*href\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
_DOMAIN_IN_TEXT = re.compile(r"(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,})", re.I)


def _host(url: str) -> str:
    host = urlparse(url if "://" in url else "http://" + url).hostname or ""
    return host.lower().removeprefix("www.")


def _defang(text: str) -> str:
    return text.replace("://", "[:]//").replace(".", "[.]")


def _html_to_text(raw: str, alerts: list) -> str:
    """Strip HTML, but keep each link's real address and flag links whose visible text lies.
    A lying label is defanged so later checks never mistake it for the real destination."""
    links = []

    def check(m):
        href, label = m.group(1), m.group(2)
        label_text = html.unescape(_TAG.sub("", label)).strip()
        shown = _DOMAIN_IN_TEXT.search(label_text)
        real = _host(href) if href.lower().startswith(("http", "www")) else ""
        if shown and real and _host(shown.group(0)) != real and not real.endswith("." + _host(shown.group(0))):
            alerts.append("hidden_link")
            label_text = _defang(label_text)
            links.append(f"shown as '{label_text}' but really goes to: {href}")
            return f" [link shown as '{label_text}' but really goes to {href}] "
        if real:
            links.append(f"'{label_text}' goes to: {href}")
        return f" {label_text} "

    raw = _ANCHOR.sub(check, raw)
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", raw)
    text = html.unescape(_TAG.sub(" ", raw))
    if links:
        text += "\n\nLinks in this document:\n" + "\n".join(links)
    return text


def _xml_text(xml: str) -> str:
    xml = re.sub(r"</(?:w:p|a:p|text:p|text:h|row)>|<w:br/>|<w:tab/>", "\n", xml)
    xml = re.sub(r"</(?:si|c|table:table-cell)>", " | ", xml)
    return html.unescape(_TAG.sub("", xml))


def _office_text(data: bytes, ext: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        if ext in ("docx", "dotx"):
            parts = [n for n in names if re.match(r"word/(document|header\d*|footer\d*|footnotes)\.xml$", n)]
        elif ext in ("pptx", "potx"):
            parts = sorted(n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n))
        elif ext in ("xlsx", "xltx"):
            parts = [n for n in names if n == "xl/sharedStrings.xml" or re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
        else:  # odt, ods, odp
            parts = [n for n in names if n == "content.xml"]
        return "\n".join(_xml_text(z.read(n).decode("utf-8", "replace")) for n in parts)


def _pdf(data: bytes, out: dict):
    if re.search(rb"/JavaScript|/JS\s|/Launch|/EmbeddedFile|/OpenAction\s*<<[^>]*/JS", data):
        out["alerts"].append("pdf_active")
    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:30])
    except Exception:  # noqa: BLE001
        pass
    out["text"] = text
    if len(text.strip()) < 80:  # scanned PDF: send page pictures instead
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(data)
            for i in range(min(len(pdf), MAX_PAGES_AS_IMAGES)):
                img = pdf[i].render(scale=2).to_pil()
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="JPEG", quality=85)
                out["images"].append((buf.getvalue(), "image/jpeg"))
            pdf.close()
            out["kind"] = "pdf (scanned)"
        except Exception:  # noqa: BLE001
            if not text.strip():
                out["alerts"].append("unsupported")


def _convert_image(data: bytes, ext: str):
    if ext in ("heic", "heif"):
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except Exception:  # noqa: BLE001
            return None
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.seek(0)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=88)
        return buf.getvalue()
    except Exception:  # noqa: BLE001
        return None


def _email(data: bytes, out: dict):
    msg = email.message_from_bytes(data, policy=policy.default)
    head = f"From: {msg.get('From', '')}\nReply-To: {msg.get('Reply-To', '')}\nSubject: {msg.get('Subject', '')}\n\n"
    body = ""
    for part in msg.walk():
        ctype = part.get_content_type()
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename() or ""
        if filename:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            head += f"Attachment: {filename}\n"
            if ext in DANGEROUS:
                out["alerts"].append("dangerous_file")
            continue
        try:
            content = part.get_content()
        except Exception:  # noqa: BLE001
            continue
        if ctype == "text/plain":
            body += str(content) + "\n"
        elif ctype == "text/html":
            body += _html_to_text(str(content), out["alerts"]) + "\n"
    out["text"] = head + body


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16", "cp1256", "latin-1"):
        try:
            text = data.decode(enc)
            if enc == "utf-16" and not data[:2] in (b"\xff\xfe", b"\xfe\xff"):
                continue
            return text
        except Exception:  # noqa: BLE001
            continue
    return data.decode("utf-8", "replace")


def extract(name: str, data: bytes, mime: str = "") -> dict:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    out = {"text": "", "images": [], "alerts": [], "kind": ext or mime or "unknown"}

    if ext in DANGEROUS:
        out["alerts"].append("dangerous_file")
        out["text"] = (f"(The person received a file named '{name}'. This type of file can install or run programs. "
                       "It was NOT opened.)")
        return out
    try:
        if ext in IMAGE_MIME:
            out["images"].append((data, IMAGE_MIME[ext]))
        elif ext in CONVERT_IMAGES or mime.startswith("image/"):
            jpg = _convert_image(data, ext)
            if jpg:
                out["images"].append((jpg, "image/jpeg"))
            else:
                out["alerts"].append("unsupported")
        elif ext == "pdf" or data[:5] == b"%PDF-":
            _pdf(data, out)
        elif ext in ("docx", "dotx", "pptx", "potx", "xlsx", "xltx", "odt", "ods", "odp"):
            out["text"] = _office_text(data, ext)
        elif ext in ("eml", "mht", "mhtml"):
            _email(data, out)
        elif ext in ("html", "htm"):
            out["text"] = _html_to_text(_decode(data), out["alerts"])
        elif ext == "rtf":
            raw = _decode(data)
            raw = re.sub(r"\\'[0-9a-f]{2}|\\[a-z]+-?\d* ?|[{}]", " ", raw)
            out["text"] = raw
        elif ext in TEXT_LIKE or not ext:
            out["text"] = _decode(data)
        else:
            text = _decode(data)
            printable = sum(ch.isprintable() or ch in "\n\r\t" for ch in text[:2000]) / max(1, len(text[:2000]))
            if printable > 0.9:
                out["text"] = text
            else:
                out["alerts"].append("unsupported")
    except Exception:  # noqa: BLE001
        out["alerts"].append("unsupported")

    out["text"] = re.sub(r"[ \t]+", " ", out["text"])
    out["text"] = re.sub(r"\n\s*\n+", "\n\n", out["text"]).strip()
    if len(out["text"]) > MAX_CHARS:
        out["text"] = out["text"][:MAX_CHARS]
        out["alerts"].append("truncated")
    out["alerts"] = list(dict.fromkeys(out["alerts"]))
    return out


# What each alert means for the model (English; the model explains it in the user's language).
ALERT_SIGNALS = {
    "dangerous_file": "SERIOUS the file is a type that can install or run programs (app, program, or macro file). It was not opened. This is a common scam trick.",
    "pdf_active": "SERIOUS the PDF contains hidden code, auto-actions, or attached files. Normal contracts do not need this.",
    "hidden_link": "SERIOUS a link shows one website address but really goes to a different one. This is a common phishing trick.",
}
