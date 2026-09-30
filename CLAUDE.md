# CLAUDE.md — AskCBS

Context for Claude Code working in this repo.

## What this is

A question-answering assistant for Columbia Business School MBA students. It answers
practical campus, NYC, club, and recruiting questions — where the microwaves are, how to
get between Manhattanville and Morningside at night, when tech recruiting kicks off.

Built as a portfolio artifact demonstrating product scoping and shipping speed, alongside
FloodBeta (which demonstrates technical/analytical depth). Same stack philosophy: simple,
free tier, deployable in days.

## Stack

- **Language:** Python 3.11+
- **Frontend:** Streamlit
- **Model:** Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) via the Gemini API, free tier
- **Deployment:** Streamlit Community Cloud
- **Key libraries:** `streamlit`, `google-genai`

## Project structure

```
AskCBS/
├── CLAUDE.md               # This file
├── README.md               # Product-facing readme
├── requirements.txt
├── .gitignore
├── app.py                  # Streamlit chat UI
├── askcbs/
│   ├── __init__.py
│   ├── knowledge.py        # Loads and assembles the corpus
│   ├── llm.py              # System prompt + Gemini API call
│   └── logging_.py         # Question logging, coverage gap detection
├── knowledge/
│   ├── campus_facts.md     # ExBo Survival Guide: campus + NYC
│   └── recruiting_clubs.md # ExBo Survival Guide: clubs + recruiting playbooks
└── .streamlit/
    └── secrets.toml.example
```

## Core architectural decision: no vector database

The entire corpus is ~5,000 words (~9k tokens) and is passed in full in the system
prompt on every request. This is deliberate.

Retrieval would add moving parts and a new failure mode — retrieving the wrong chunk —
without improving answers at this corpus size. **Do not add a vector store, embeddings,
or a chunking step unless the corpus grows past roughly 40,000 words.**

`askcbs/knowledge.py` is the seam where a retrieval step would go if that day comes.
`build_corpus()` returns a single string; swapping it for `retrieve(query)` would be the
only change needed upstream.

The system prompt is passed as Gemini's `system_instruction` and is identical on every
request. The free tier has no per-token bill, so there's no explicit caching; the
constraint that matters is the free-tier rate limit. `stream_answer()` catches a 429 and
yields a friendly "AskCBS is busy" message instead of raising. Keep that when editing
`llm.py`.

## The system prompt is the most important file

`askcbs/llm.py` contains `SYSTEM_TEMPLATE`. It is what stops the bot from confidently
inventing a shuttle schedule. When editing it, preserve these behaviors:

1. **Answer only from the documents.** Defer to CMC / Peer Advisors / the club when the
   corpus doesn't cover something. Never guess a room number, date, deadline, or email.
2. **Be brief.** Most questions are lookups deserving two sentences.
3. **Name only the people the corpus names** — the CMC contacts and faculty listed in the
   club recruiting playbooks. There is no people directory anymore; if nobody relevant is
   listed, defer to the CMC or 12twenty rather than producing a name.
4. **Flag time-sensitive info** for confirmation. Both sources are student-written.
5. **Stay in scope.** Not a career coach, academic advisor, or counselor. Personal or
   academic difficulty → Office of Student Affairs, Columbia Health (212-854-7426),
   counseling drop-in hours.

## Knowledge base provenance

- `campus_facts.md` and `recruiting_clubs.md` — extracted from the **ExBo Survival Guide,
  Fall 2026** (84-page Canva deck, student-written, explicitly *not* an official CBS
  document). Dates and contacts shift year to year.
Updating the knowledge base means editing markdown and redeploying. No re-indexing, no
migration. Someone needs to own this annually or the tool decays and students stop
trusting it.

## Feedback loop

Every question is logged to `questions.csv` with an `answered` flag set by crude phrase
matching in `looks_unanswered()`. The `no` rows are the coverage gaps to fill next.

**Known limitation:** Streamlit Community Cloud has an ephemeral filesystem, so the log
wipes on restart/redeploy. For durable logs, replace the file write in `log_question()`
with a Google Sheet or Supabase write. Worth doing before sharing the link widely, since
usage data is the actual point.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # add API key
streamlit run app.py
```

`.streamlit/secrets.toml` and `questions.csv` are gitignored. Never commit an API key.

## Deployment

Streamlit Community Cloud, pointed at `app.py` on `main`. `GEMINI_API_KEY` must be set
under Settings → Secrets or every question fails at runtime (the app itself still boots).

Consider a GitHub Actions keep-alive workflow pinging the app every 10 minutes to prevent
Community Cloud from sleeping it — same pattern used in FloodBeta.

## Cost guardrail

This project must run on Gemini's free tier only.

- The Google Cloud project behind `GEMINI_API_KEY` must never have billing enabled.
- Never suggest enabling billing to raise rate limits.
- If rate limits become a problem, the options are a smaller model, a lower
  `SESSION_QUESTION_LIMIT` in `app.py`, or switching providers. That's Yi's call, not
  something to change unprompted.

## Scope discipline

v1 is CBS-specific: campus, clubs, recruiting. Resist scope creep into a
general NYC assistant or a full campus super-app. A sharp narrow tool that works beats a
broad one that's mediocre.

Deferred, in rough priority order:
- Durable question logging (Google Sheet / Supabase)
- Answer-quality evals against a fixed question set
- Source attribution in answers (which document a fact came from)
- Splitting campus wayfinding vs. recruiting into separate modes — only if usage data
  shows people want that

## Conventions

- Commit messages are written by the repo owner, not delegated.
- Solo project; commits go directly to `main`.
- Keep dependencies minimal and Streamlit Community Cloud compatible.
