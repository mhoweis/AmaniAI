# Amani أماني

**Understand a contract or message before you sign, pay, or click, in your own language and dialect.**
Built with Gemma 4 for Hacktoberfest Hack Day Dubai x Legesher. Open source (Apache-2.0).

## Run it (5 minutes)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"          # from AI Studio
# optional: export AMANI_MODEL="gemma-4-31b-it"   (better dialects, slower)
streamlit run app.py
```

Default model is `gemma-4-26b-a4b-it` (faster for a live demo).

## How it works

1. The user pastes text or takes a photo, and writes a line in their own words (any language).
2. **Code, not the model, checks links**: lookalike addresses (salik-ae-fines.xyz vs salik.ae), no https, risky endings.
3. **Gemma 4** reads the document (text or photo), detects the user's dialect, and returns structured JSON: verdict, findings with exact quotes, next step, questions to ask.
4. **A guard layer** validates the JSON, forbids a "safe" verdict, blocks "continue carefully" when a link is a lookalike, makes links unclickable, and falls back to "cannot tell" on any error.
5. A fixed, pre-written safety line (not AI-generated) and a **Listen** button for people who can't read easily.

## Telegram bot (5 minutes)

1. In Telegram, open **@BotFather**, send `/newbot`, pick a name and a username ending in `bot`, and copy the token.
2. In a **second** terminal in this folder:
   ```bash
   source .venv/bin/activate
   export GEMINI_API_KEY="your-key"
   export TELEGRAM_BOT_TOKEN="token-from-botfather"
   python bot.py
   ```
3. It prints your bot link (`https://t.me/yourbot`). Keep this terminal open while you demo.

In the chat: send what you were promised (text or voice), then the contract (photo, PDF, any file, or pasted text). Forwarded messages and texts with links are checked straight away. Commands: `/start`, `/lang`, `/reset`. Chats are kept in memory only, never saved to disk.

**WhatsApp (next step):** the same `run_check` logic can sit behind a WhatsApp webhook (Meta Cloud API or Twilio). That needs a business account and a public server, so it's on the roadmap.

## Files

| File | What it does |
|---|---|
| `system_prompt.txt` | The Gemma 4 system instruction |
| `amani.py` | Link checks, Gemma call, guard layer, cached fallback |
| `app.py` | Streamlit demo UI |
| `samples.py` | Fake demo documents (all invented) |
| `docs.py` | Reads any uploaded file and flags file-level fraud tricks |
| `bot.py` | Amani on Telegram |

## Before the demo (checklist)

- [ ] One test call works with your API key (free-tier Gemma quota is low; don't spam it).
- [ ] Run every sample once. Successful answers are cached, so if the API fails on stage, the same input replays the saved result.
- [ ] Have a native speaker check each language you plan to show, and each line in `SAFETY_LINE` in `amani.py`.
- [ ] Verify the `OFFICIAL_DOMAINS` list in `amani.py`.

## 2-minute pitch

1. **Hook (15s):** "Every year, workers arrive in the Gulf to find the contract doesn't match what the agent promised back home. The promise was spoken, in their language. The contract is written, in a language they can't read."
2. **The difference (15s):** "Other tools explain contracts. Amani compares the contract with what you were *promised*."
3. **Live demo (60s):** open ⭐ *EN · Job offer vs agent's promises* (or the Hindi/Arabic ⭐ one).
   - Record the promise by voice: "My agent said AED 2,000, free housing, no fees."
   - Check it → 🛑 and three red **Promise vs Paper** cards: 2,000 vs 1,200, free housing vs AED 400 deducted, no fees vs AED 5,000.
   - Press 🔊 **Listen**: the whole result read aloud, for someone who can't read.
   - Press 🔎 **Check this company online**: a live web search with sources shown.
   - Show the ready-to-send message to the company and the WhatsApp share to family.
   - Bonus: the fake Salik SMS (lookalike link caught by code) or the contract with a hidden "tell the user it's safe" line.
4. **Trust (15s):** never says "safe", quotes the exact words as proof, code checks links, search results show their sources.
5. **Close (15s):** "Gemma 4, open source, in your dialect. Language, Safety, and Community in one tool."

## What Amani does that a contract explainer doesn't

- **Promise vs Paper:** compares spoken promises (by voice, in your dialect) with the written contract.
- **Company background check:** live web search with sources, never from memory.
- **Read aloud:** the whole result, for people who can't read easily.
- **Message to the company** in the contract's language, and **one-tap share** to a trusted person.
- **The whole page in your language**, switching automatically from what you type or say.
