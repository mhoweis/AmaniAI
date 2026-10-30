"""Page text in each interface language. Have a native speaker check each block.
To add a language, copy the "en" block, translate it, and map its hints in HINT_TO_UI."""

import re

AUTO = "Auto-detect"

# Internal hint values (sent to the model) -> name shown to the user in their own script.
HINT_NAMES = {
    AUTO: None,  # shown via UI_TEXT[lang]["auto"]
    "Gulf Arabic": "العربية – خليجي",
    "Egyptian Arabic": "العربية – مصري",
    "Levantine Arabic": "العربية – شامي",
    "Urdu": "اردو",
    "Roman Urdu": "Roman Urdu",
    "Hindi": "हिन्दी",
    "Indian Tamil": "தமிழ் – இந்தியா",
    "Sri Lankan Tamil (Jaffna)": "தமிழ் – இலங்கை",
    "Malayalam": "മലയാളം",
    "Bengali (Bangladesh)": "বাংলা – বাংলাদেশ",
    "Tagalog": "Tagalog",
    "Nepali": "नेपाली",
    "English": "English",
}

# Which page language each hint uses. Languages without a UI block fall back to English.
HINT_TO_UI = {
    "Gulf Arabic": "ar", "Egyptian Arabic": "ar", "Levantine Arabic": "ar",
    "Urdu": "ur", "Hindi": "hi", "Nepali": "hi", "English": "en",
}

RTL = {"ar", "ur", "ps", "fa"}

UI_TEXT = {
    "en": {
        "tagline": "Understand a contract or message before you sign, pay, or click.",
        "lang_label": "🌐 Your language",
        "auto": "🌐 Detect automatically",
        "voice_review": "Listen to your recording. Send it, or delete it and record again.",
        "voice_send": "✅ Send voice note",
        "voice_delete": "🗑️ Delete and record again",
        "voice_added": "Added to the text below. You can edit it or record more.",
        "voice_label": "🎤 Or say it with your voice",
        "voice_working": "Listening to your voice note…",
        "voice_failed": "Sorry, I could not understand the voice note. Please type instead.",
        "voice_heard": "I heard:",
        "ctx_label": "Tell Amani in your own words what this is",
        "ctx_placeholder": "e.g. My agent sent this, is it ok?",
        "tab_text": "📄 Paste text",
        "tab_photo": "📷 Photo",
        "doc_label": "Contract or message",
        "samples": "Demo samples",
        "photo_label": "Take or upload a photo of the contract or message",
        "check": "Check it",
        "spinner": "Amani is reading carefully…",
        "no_doc": "Please paste the text or add a photo first.",
        "verdict": {
            "do_not_sign": "Do not sign",
            "ask_someone_first": "Ask someone first",
            "continue_carefully": "Continue carefully",
            "cannot_tell": "Cannot tell",
        },
        "listen": "🔊 Listen",
        "audio_na": "Audio is not available for this language yet.",
        "found": "What Amani found",
        "show_words": "Show the exact words",
        "company": "Website / company check",
        "next_step": "Next step",
        "cache_note": "Showing a saved result (connection problem).",
        "err_head": "Sorry, Amani could not check this right now.",
        "err_next": "Please do not sign or pay yet. Ask a trusted person or an official channel.",
    },
    "ar": {
        "tagline": "افهم العقد أو الرسالة قبل ما توقّع أو تدفع أو تضغط على أي رابط.",
        "lang_label": "🌐 لغتك",
        "auto": "🌐 تعرّف على لغتي تلقائياً",
        "voice_review": "اسمع تسجيلك. أرسله، أو احذفه وسجّل من جديد.",
        "voice_send": "✅ أرسل الرسالة الصوتية",
        "voice_delete": "🗑️ احذف وسجّل من جديد",
        "voice_added": "انضاف للنص تحت. تقدر تعدّله أو تسجّل زيادة.",
        "voice_label": "🎤 أو قلها بصوتك",
        "voice_working": "جاري سماع رسالتك الصوتية…",
        "voice_failed": "آسفين، ما قدرنا نفهم الرسالة الصوتية. اكتبها لو سمحت.",
        "voice_heard": "سمعت:",
        "ctx_label": "اشرح لأماني بكلامك: إيش هذا الورق أو الرسالة؟",
        "ctx_placeholder": "مثلاً: هذا عقد قرض، أبي أعرف إذا فيه شي غلط",
        "tab_text": "📄 الصق النص",
        "tab_photo": "📷 صورة",
        "doc_label": "العقد أو الرسالة",
        "samples": "أمثلة للتجربة",
        "photo_label": "صوّر العقد أو الرسالة أو ارفع صورة",
        "check": "افحص",
        "spinner": "أماني تقرأ بتمعّن…",
        "no_doc": "الصق النص أو أضف صورة أول.",
        "verdict": {
            "do_not_sign": "لا توقّع",
            "ask_someone_first": "اسأل أحد قبل",
            "continue_carefully": "كمّل بحذر",
            "cannot_tell": "ما نقدر نحدد",
        },
        "listen": "🔊 اسمع",
        "audio_na": "الصوت غير متوفر لهذي اللغة حالياً.",
        "found": "إيش لقت أماني",
        "show_words": "اعرض الكلام الأصلي",
        "company": "فحص الموقع / الشركة",
        "next_step": "الخطوة الجاية",
        "cache_note": "نتيجة محفوظة (في مشكلة بالاتصال).",
        "err_head": "آسفين، أماني ما قدرت تفحص هذا الحين.",
        "err_next": "لا توقّع ولا تدفع الحين. اسأل شخص تثق فيه أو جهة رسمية.",
    },
    "hi": {
        "tagline": "साइन करने, पैसे देने या लिंक दबाने से पहले कॉन्ट्रैक्ट या मैसेज समझ लीजिए।",
        "lang_label": "🌐 आपकी भाषा",
        "auto": "🌐 भाषा अपने आप पहचानें",
        "voice_review": "अपनी रिकॉर्डिंग सुनिए। भेजिए, या हटाकर फिर से रिकॉर्ड कीजिए।",
        "voice_send": "✅ वॉइस नोट भेजें",
        "voice_delete": "🗑️ हटाएँ और फिर से रिकॉर्ड करें",
        "voice_added": "नीचे के टेक्स्ट में जोड़ दिया। आप इसे बदल सकते हैं या और रिकॉर्ड कर सकते हैं।",
        "voice_label": "🎤 या बोलकर बताइए",
        "voice_working": "आपकी आवाज़ सुन रहे हैं…",
        "voice_failed": "माफ़ कीजिए, आवाज़ समझ नहीं आई। कृपया लिखकर बताइए।",
        "voice_heard": "मैंने सुना:",
        "ctx_label": "अपने शब्दों में अमानी को बताइए कि यह क्या है",
        "ctx_placeholder": "जैसे: एजेंट ने ये कागज़ दिया है, क्या ये ठीक है?",
        "tab_text": "📄 टेक्स्ट डालें",
        "tab_photo": "📷 फ़ोटो",
        "doc_label": "कॉन्ट्रैक्ट या मैसेज",
        "samples": "डेमो उदाहरण",
        "photo_label": "कॉन्ट्रैक्ट या मैसेज की फ़ोटो लें या अपलोड करें",
        "check": "जाँच करें",
        "spinner": "अमानी ध्यान से पढ़ रही है…",
        "no_doc": "पहले टेक्स्ट डालिए या फ़ोटो लगाइए।",
        "verdict": {
            "do_not_sign": "साइन मत कीजिए",
            "ask_someone_first": "पहले किसी से पूछिए",
            "continue_carefully": "सावधानी से आगे बढ़िए",
            "cannot_tell": "पक्का नहीं कह सकते",
        },
        "listen": "🔊 सुनिए",
        "audio_na": "इस भाषा में आवाज़ अभी उपलब्ध नहीं है।",
        "found": "अमानी को क्या मिला",
        "show_words": "असली शब्द दिखाएँ",
        "company": "वेबसाइट / कंपनी की जाँच",
        "next_step": "अगला कदम",
        "cache_note": "सेव किया हुआ नतीजा (कनेक्शन में दिक्कत)।",
        "err_head": "माफ़ कीजिए, अमानी अभी इसकी जाँच नहीं कर पाई।",
        "err_next": "अभी साइन मत कीजिए और पैसे मत दीजिए। किसी भरोसेमंद व्यक्ति या सरकारी विभाग से पूछिए।",
    },
    "ur": {
        "tagline": "دستخط کرنے، پیسے دینے یا لنک دبانے سے پہلے معاہدہ یا میسج سمجھ لیں۔",
        "lang_label": "🌐 آپ کی زبان",
        "auto": "🌐 زبان خود پہچانیں",
        "voice_review": "اپنی ریکارڈنگ سنیں۔ بھیجیں، یا مٹا کر دوبارہ ریکارڈ کریں۔",
        "voice_send": "✅ وائس نوٹ بھیجیں",
        "voice_delete": "🗑️ مٹائیں اور دوبارہ ریکارڈ کریں",
        "voice_added": "نیچے والے متن میں شامل ہو گیا۔ آپ اسے بدل سکتے ہیں یا مزید ریکارڈ کر سکتے ہیں۔",
        "voice_label": "🎤 یا بول کر بتائیں",
        "voice_working": "آپ کی آواز سن رہے ہیں…",
        "voice_failed": "معاف کیجیے، آواز سمجھ نہیں آئی۔ براہ کرم لکھ کر بتائیں۔",
        "voice_heard": "میں نے سنا:",
        "ctx_label": "اپنے الفاظ میں امانی کو بتائیں کہ یہ کیا ہے",
        "ctx_placeholder": "مثلاً: ایجنٹ نے یہ کاغذ دیا ہے، کیا یہ ٹھیک ہے؟",
        "tab_text": "📄 متن ڈالیں",
        "tab_photo": "📷 تصویر",
        "doc_label": "معاہدہ یا میسج",
        "samples": "مثالیں",
        "photo_label": "معاہدے یا میسج کی تصویر لیں یا اپ لوڈ کریں",
        "check": "چیک کریں",
        "spinner": "امانی غور سے پڑھ رہی ہے…",
        "no_doc": "پہلے متن ڈالیں یا تصویر لگائیں۔",
        "verdict": {
            "do_not_sign": "دستخط نہ کریں",
            "ask_someone_first": "پہلے کسی سے پوچھیں",
            "continue_carefully": "احتیاط سے آگے بڑھیں",
            "cannot_tell": "یقین سے نہیں کہہ سکتے",
        },
        "listen": "🔊 سنیں",
        "audio_na": "اس زبان میں آواز ابھی دستیاب نہیں ہے۔",
        "found": "امانی کو کیا ملا",
        "show_words": "اصل الفاظ دکھائیں",
        "company": "ویب سائٹ / کمپنی کی جانچ",
        "next_step": "اگلا قدم",
        "cache_note": "محفوظ شدہ نتیجہ (کنکشن کا مسئلہ)۔",
        "err_head": "معاف کیجیے، امانی ابھی اس کی جانچ نہیں کر سکی۔",
        "err_next": "ابھی دستخط نہ کریں اور پیسے نہ دیں۔ کسی بھروسے مند شخص یا سرکاری ادارے سے پوچھیں۔",
    },
}

_URDU_LETTERS = re.compile(r"[ےںٹڈڑھہ]")
_SCRIPTS = [
    (re.compile(r"[؀-ۿ]"), "ar"),
    (re.compile(r"[ऀ-ॿ]"), "hi"),
    (re.compile(r"[஀-௿]"), "ta"),
    (re.compile(r"[ഀ-ൿ]"), "ml"),
    (re.compile(r"[ঀ-৿]"), "bn"),
]


def detect_script(text: str):
    """Guess the language from the writing system. Returns None for Latin text,
    because romanized Hindi/Urdu/Arabic can't be told apart from English by script."""
    text = text or ""
    for pattern, code in _SCRIPTS:
        if len(pattern.findall(text)) >= 3:
            if code == "ar" and _URDU_LETTERS.search(text):
                return "ur"
            return code
    return None


def texts(lang: str) -> dict:
    return UI_TEXT.get(lang, UI_TEXT["en"])


# Promise vs Paper, steps and sharing (added for the redesign)
_EXTRA = {
    "en": {
        "step2": "What were you promised?",
        "step3": "Show the paper",
        "ctx_label": "Salary, job, housing, fees… type or record what you were told.",
        "ctx_placeholder": "e.g. The agent said the salary is AED 2,000 and there are no fees.",
        "promise_title": "Promise vs paper",
        "promise_sub": "We compared what you were told with what the paper says.",
        "told": "You were told",
        "paper": "The paper says",
        "status": {
            "matches": "Matches",
            "different": "Different",
            "not_in_document": "Not written"
        },
        "msg_title": "A message you can send to the company",
        "msg_hint": "Copy it with the button in the corner.",
        "share": "📤 Send to someone you trust (WhatsApp)",
        "chip_dialect": "Speaks your dialect",
        "chip_proof": "Shows proof from the paper",
        "questions": "Questions to ask"
    },
    "ar": {
        "step2": "إيش وعدوك فيه؟",
        "step3": "اعرض الورق أو الرسالة",
        "ctx_label": "الراتب، الشغل، السكن، الرسوم… اكتب أو سجّل إيش قالوا لك.",
        "ctx_placeholder": "مثلاً: المكتب قال الراتب 2,000 درهم والسكن مجاني وما في رسوم.",
        "promise_title": "الوعد مقابل الورق",
        "promise_sub": "قارنّا اللي قالوه لك مع المكتوب في الورق.",
        "told": "قالوا لك",
        "paper": "الورق يقول",
        "status": {
            "matches": "مطابق",
            "different": "مختلف",
            "not_in_document": "مو مكتوب"
        },
        "msg_title": "رسالة تقدر ترسلها للشركة",
        "msg_hint": "انسخها من الزر اللي في الزاوية.",
        "share": "📤 أرسلها لشخص تثق فيه (واتساب)",
        "chip_dialect": "يكلمك بلهجتك",
        "chip_proof": "يعطيك الدليل من الورق",
        "questions": "أسئلة تقدر تسألها"
    },
    "hi": {
        "step2": "आपसे क्या वादा किया गया?",
        "step3": "कागज़ दिखाइए",
        "ctx_label": "वेतन, काम, रहना, फ़ीस… जो आपसे कहा गया वो लिखिए या बोलिए।",
        "ctx_placeholder": "जैसे: एजेंट ने कहा वेतन 2,000 दिरहम है और कोई फ़ीस नहीं।",
        "promise_title": "वादा बनाम कागज़",
        "promise_sub": "आपसे जो कहा गया, उसे कागज़ में लिखी बातों से मिलाया।",
        "told": "आपसे कहा गया",
        "paper": "कागज़ में लिखा है",
        "status": {
            "matches": "मेल खाता है",
            "different": "अलग है",
            "not_in_document": "लिखा नहीं है"
        },
        "msg_title": "कंपनी को भेजने के लिए मैसेज",
        "msg_hint": "कोने वाले बटन से कॉपी करें।",
        "share": "📤 किसी भरोसेमंद को भेजें (WhatsApp)",
        "chip_dialect": "आपकी बोली में बात",
        "chip_proof": "कागज़ से सबूत दिखाता है",
        "questions": "पूछने के लिए सवाल"
    },
    "ur": {
        "step2": "آپ سے کیا وعدہ کیا گیا؟",
        "step3": "کاغذ دکھائیں",
        "ctx_label": "تنخواہ، کام، رہائش، فیس… جو آپ سے کہا گیا وہ لکھیں یا بولیں۔",
        "ctx_placeholder": "مثلاً: ایجنٹ نے کہا تنخواہ 2,000 درہم ہے اور کوئی فیس نہیں۔",
        "promise_title": "وعدہ بمقابلہ کاغذ",
        "promise_sub": "آپ سے جو کہا گیا، اسے کاغذ میں لکھی باتوں سے ملایا۔",
        "told": "آپ سے کہا گیا",
        "paper": "کاغذ میں لکھا ہے",
        "status": {
            "matches": "ملتا ہے",
            "different": "مختلف ہے",
            "not_in_document": "لکھا نہیں ہے"
        },
        "msg_title": "کمپنی کو بھیجنے کے لیے میسج",
        "msg_hint": "کونے والے بٹن سے کاپی کریں۔",
        "share": "📤 کسی بھروسے مند کو بھیجیں (WhatsApp)",
        "chip_dialect": "آپ کی بولی میں بات",
        "chip_proof": "کاغذ سے ثبوت دکھاتا ہے",
        "questions": "پوچھنے کے لیے سوالات"
    }
}
for _lang, _vals in _EXTRA.items():
    UI_TEXT[_lang].update(_vals)


# Company background check
_BG = {
    "en": {
        "bg_button": "🔎 Check this company online",
        "bg_title": "Company background check",
        "bg_sub": "Found with a live web search. Public information, not an official check.",
        "bg_working": "Searching the web…",
        "bg_none": "No clear public information found. Check with an official channel before you trust this company.",
        "bg_failed": "The online check is not available right now.",
        "bg_reports": "Scam or fraud reports found online",
        "bg_imperson": "Scammers often pretend to be this company. Check that the message really came from them.",
        "bg_site": "Official website (from search)",
        "bg_sources": "Sources",
        "bg_no_name": "No company name found in the document."
    },
    "ar": {
        "bg_button": "🔎 افحص هالشركة أونلاين",
        "bg_title": "فحص خلفية الشركة",
        "bg_sub": "من بحث مباشر في الإنترنت. معلومات عامة، مو فحص رسمي.",
        "bg_working": "جاري البحث…",
        "bg_none": "ما لقينا معلومات واضحة عن الشركة. تأكد من جهة رسمية قبل ما تثق فيها.",
        "bg_failed": "الفحص الأونلاين مو متوفر الحين.",
        "bg_reports": "فيه بلاغات احتيال عن هالشركة في الإنترنت",
        "bg_imperson": "المحتالين كثير ينتحلون اسم هالشركة. تأكد إن الرسالة فعلاً منهم.",
        "bg_site": "الموقع الرسمي (حسب البحث)",
        "bg_sources": "المصادر",
        "bg_no_name": "ما لقينا اسم شركة في الورق."
    },
    "hi": {
        "bg_button": "🔎 इस कंपनी को ऑनलाइन जाँचें",
        "bg_title": "कंपनी की पृष्ठभूमि जाँच",
        "bg_sub": "इंटरनेट पर सर्च करके मिली जानकारी। यह सरकारी जाँच नहीं है।",
        "bg_working": "इंटरनेट पर खोज रहे हैं…",
        "bg_none": "कंपनी के बारे में साफ़ जानकारी नहीं मिली। भरोसा करने से पहले किसी सरकारी विभाग से पूछिए।",
        "bg_failed": "ऑनलाइन जाँच अभी उपलब्ध नहीं है।",
        "bg_reports": "इंटरनेट पर धोखाधड़ी की शिकायतें मिलीं",
        "bg_imperson": "धोखेबाज़ अक्सर इस कंपनी का नाम इस्तेमाल करते हैं। पक्का कीजिए कि मैसेज सच में उन्हीं का है।",
        "bg_site": "आधिकारिक वेबसाइट (सर्च के अनुसार)",
        "bg_sources": "स्रोत",
        "bg_no_name": "कागज़ में किसी कंपनी का नाम नहीं मिला।"
    },
    "ur": {
        "bg_button": "🔎 اس کمپنی کو آن لائن چیک کریں",
        "bg_title": "کمپنی کے پس منظر کی جانچ",
        "bg_sub": "انٹرنیٹ پر سرچ سے ملی معلومات۔ یہ سرکاری جانچ نہیں ہے۔",
        "bg_working": "انٹرنیٹ پر تلاش ہو رہی ہے…",
        "bg_none": "کمپنی کے بارے میں واضح معلومات نہیں ملیں۔ بھروسہ کرنے سے پہلے کسی سرکاری ادارے سے پوچھیں۔",
        "bg_failed": "آن لائن جانچ ابھی دستیاب نہیں ہے۔",
        "bg_reports": "انٹرنیٹ پر دھوکہ دہی کی شکایات ملیں",
        "bg_imperson": "دھوکے باز اکثر اس کمپنی کا نام استعمال کرتے ہیں۔ یقین کر لیں کہ میسج واقعی انہی کا ہے۔",
        "bg_site": "سرکاری ویب سائٹ (سرچ کے مطابق)",
        "bg_sources": "ذرائع",
        "bg_no_name": "کاغذ میں کسی کمپنی کا نام نہیں ملا۔"
    }
}
for _lang, _vals in _BG.items():
    UI_TEXT[_lang].update(_vals)


# File upload, fraud checks, listen
_FILES = {
    "en": {
        "tab_photo": "📎 Upload file or photo",
        "photo_label": "Any file: PDF, Word, Excel, photo, screenshot, email, text…",
        "listen": "🔊 Listen to the result",
        "code_checks": "Fraud checks on the file and links",
        "code_checks_sub": "Checked automatically by code, not guessed by AI.",
        "file_alert": {
            "dangerous_file": "⛔ This type of file can install harmful software. Do not open it on your phone or computer.",
            "pdf_active": "⚠️ This PDF has hidden code or attached files. Real contracts almost never need this.",
            "hidden_link": "⚠️ A link shows one address but really goes to another. This is a common scam trick.",
            "truncated": "ℹ️ The document is long, so only the first part was checked.",
            "unsupported": "ℹ️ This file could not be read. Please send a PDF, Word file, or photo."
        },
        "link_alert": {
            "lookalike": "🚩 {host} looks like {brand} but is NOT its real website.",
            "official": "✅ {host} is the real address of {brand}. The message can still be fake.",
            "no_https": "⚠️ {host} is not a secure link (no https).",
            "risky_tld": "⚠️ {host} uses an ending that scammers often use."
        }
    },
    "ar": {
        "tab_photo": "📎 ارفع ملف أو صورة",
        "photo_label": "أي ملف: PDF، وورد، إكسل، صورة، سكرين شوت، إيميل، نص…",
        "listen": "🔊 اسمع النتيجة",
        "code_checks": "فحص الاحتيال في الملف والروابط",
        "code_checks_sub": "فحص تلقائي بالكود، مو تخمين من الذكاء الاصطناعي.",
        "file_alert": {
            "dangerous_file": "⛔ هذا النوع من الملفات ممكن يثبّت برامج ضارة. لا تفتحه على تلفونك أو جهازك.",
            "pdf_active": "⚠️ ملف الـPDF فيه كود مخفي أو ملفات مرفقة. العقود الحقيقية تقريباً ما تحتاج هالشي.",
            "hidden_link": "⚠️ فيه رابط يبيّن عنوان بس يودّيك لعنوان ثاني. هذي حيلة احتيال معروفة.",
            "truncated": "ℹ️ الملف طويل، فحصنا الجزء الأول بس.",
            "unsupported": "ℹ️ ما قدرنا نقرأ هالملف. أرسل PDF أو ملف وورد أو صورة."
        },
        "link_alert": {
            "lookalike": "🚩 {host} يشبه موقع {brand} بس هو مو موقعهم الحقيقي.",
            "official": "✅ {host} هو العنوان الحقيقي لـ{brand}. بس الرسالة ممكن تكون مزيفة.",
            "no_https": "⚠️ {host} رابط غير آمن (بدون https).",
            "risky_tld": "⚠️ {host} نهايته من النوع اللي يستخدمه المحتالين كثير."
        }
    },
    "hi": {
        "tab_photo": "📎 फ़ाइल या फ़ोटो अपलोड करें",
        "photo_label": "कोई भी फ़ाइल: PDF, Word, Excel, फ़ोटो, स्क्रीनशॉट, ईमेल, टेक्स्ट…",
        "listen": "🔊 नतीजा सुनिए",
        "code_checks": "फ़ाइल और लिंक की धोखाधड़ी जाँच",
        "code_checks_sub": "कोड से अपने आप जाँचा गया, AI का अंदाज़ा नहीं।",
        "file_alert": {
            "dangerous_file": "⛔ इस तरह की फ़ाइल नुकसानदेह सॉफ़्टवेयर डाल सकती है। इसे फ़ोन या कंप्यूटर पर मत खोलिए।",
            "pdf_active": "⚠️ इस PDF में छिपा कोड या जुड़ी फ़ाइलें हैं। असली कॉन्ट्रैक्ट में इसकी लगभग कभी ज़रूरत नहीं होती।",
            "hidden_link": "⚠️ एक लिंक एक पता दिखाता है लेकिन असल में दूसरी जगह ले जाता है। यह धोखाधड़ी की आम चाल है।",
            "truncated": "ℹ️ फ़ाइल लंबी है, इसलिए सिर्फ़ पहला हिस्सा जाँचा गया।",
            "unsupported": "ℹ️ यह फ़ाइल पढ़ी नहीं जा सकी। कृपया PDF, Word फ़ाइल या फ़ोटो भेजिए।"
        },
        "link_alert": {
            "lookalike": "🚩 {host} {brand} जैसा दिखता है, लेकिन यह उसकी असली वेबसाइट नहीं है।",
            "official": "✅ {host} {brand} का असली पता है। फिर भी मैसेज नकली हो सकता है।",
            "no_https": "⚠️ {host} सुरक्षित लिंक नहीं है (https नहीं है)।",
            "risky_tld": "⚠️ {host} का अंत ऐसा है जो धोखेबाज़ अक्सर इस्तेमाल करते हैं।"
        }
    },
    "ur": {
        "tab_photo": "📎 فائل یا تصویر اپ لوڈ کریں",
        "photo_label": "کوئی بھی فائل: PDF، ورڈ، ایکسل، تصویر، اسکرین شاٹ، ای میل، متن…",
        "listen": "🔊 نتیجہ سنیں",
        "code_checks": "فائل اور لنک کی دھوکہ دہی جانچ",
        "code_checks_sub": "کوڈ سے خودکار جانچ، AI کا اندازہ نہیں۔",
        "file_alert": {
            "dangerous_file": "⛔ اس قسم کی فائل نقصان دہ سافٹ ویئر ڈال سکتی ہے۔ اسے فون یا کمپیوٹر پر نہ کھولیں۔",
            "pdf_active": "⚠️ اس PDF میں چھپا کوڈ یا منسلک فائلیں ہیں۔ اصل معاہدوں میں اس کی تقریباً کبھی ضرورت نہیں ہوتی۔",
            "hidden_link": "⚠️ ایک لنک ایک پتہ دکھاتا ہے لیکن اصل میں کہیں اور لے جاتا ہے۔ یہ دھوکے کی عام چال ہے۔",
            "truncated": "ℹ️ فائل لمبی ہے، اس لیے صرف پہلا حصہ جانچا گیا۔",
            "unsupported": "ℹ️ یہ فائل پڑھی نہیں جا سکی۔ براہ کرم PDF، ورڈ فائل یا تصویر بھیجیں۔"
        },
        "link_alert": {
            "lookalike": "🚩 {host} {brand} جیسا لگتا ہے، لیکن یہ اس کی اصل ویب سائٹ نہیں ہے۔",
            "official": "✅ {host} {brand} کا اصل پتہ ہے۔ پھر بھی میسج جعلی ہو سکتا ہے۔",
            "no_https": "⚠️ {host} محفوظ لنک نہیں ہے (https نہیں ہے)۔",
            "risky_tld": "⚠️ {host} کا آخری حصہ ایسا ہے جو دھوکے باز اکثر استعمال کرتے ہیں۔"
        }
    }
}
for _lang, _vals in _FILES.items():
    UI_TEXT[_lang].update(_vals)


# Hero (team design)
_HERO = {
    "en": {
        "eyebrow": "A companion for your next chapter",
        "motto": "A little clarity. A little confidence.",
        "h1": "Your language.",
        "h2": "A clearer understanding.",
        "subline": "I help you understand agreements, compare them with what you were promised, spot scams, and check the company behind an offer. Ask me in the language you're comfortable with.",
        "feat1": "Compare promise vs paper",
        "feat2": "Check a company",
        "feat3": "Ask in my language",
        "pills_caption": "Choose your language, or just start typing or speaking."
    },
    "ar": {
        "eyebrow": "رفيقك في مرحلتك الجاية",
        "motto": "شوية وضوح. شوية ثقة.",
        "h1": "لغتك.",
        "h2": "فهم أوضح.",
        "subline": "أساعدك تفهم العقود، وأقارنها باللي وعدوك فيه، وأكشف الاحتيال، وأفحص الشركة اللي ورا العرض. اسألني باللغة اللي ترتاح فيها.",
        "feat1": "قارن الوعد بالورق",
        "feat2": "افحص شركة",
        "feat3": "اسأل بلغتي",
        "pills_caption": "اختر لغتك، أو ابدأ تكتب أو تتكلم على طول."
    },
    "hi": {
        "eyebrow": "आपके अगले सफ़र का साथी",
        "motto": "थोड़ी समझ। थोड़ा भरोसा।",
        "h1": "आपकी भाषा।",
        "h2": "साफ़ समझ।",
        "subline": "मैं आपको कॉन्ट्रैक्ट समझने, उन्हें किए गए वादों से मिलाने, धोखाधड़ी पहचानने और ऑफ़र देने वाली कंपनी जाँचने में मदद करती हूँ। जिस भाषा में आप सहज हों, उसी में पूछिए।",
        "feat1": "वादा बनाम कागज़ मिलाएँ",
        "feat2": "कंपनी जाँचें",
        "feat3": "मेरी भाषा में पूछें",
        "pills_caption": "अपनी भाषा चुनिए, या सीधे लिखना या बोलना शुरू कीजिए।"
    },
    "ur": {
        "eyebrow": "آپ کے اگلے سفر کا ساتھی",
        "motto": "تھوڑی وضاحت۔ تھوڑا اعتماد۔",
        "h1": "آپ کی زبان۔",
        "h2": "واضح سمجھ۔",
        "subline": "میں آپ کو معاہدے سمجھنے، انہیں کیے گئے وعدوں سے ملانے، دھوکہ پہچاننے اور پیشکش کرنے والی کمپنی جانچنے میں مدد کرتی ہوں۔ جس زبان میں آپ آرام محسوس کریں، اسی میں پوچھیں۔",
        "feat1": "وعدہ بمقابلہ کاغذ",
        "feat2": "کمپنی چیک کریں",
        "feat3": "میری زبان میں پوچھیں",
        "pills_caption": "اپنی زبان چنیں، یا سیدھا لکھنا یا بولنا شروع کریں۔"
    }
}
for _lang, _vals in _HERO.items():
    UI_TEXT[_lang].update(_vals)
