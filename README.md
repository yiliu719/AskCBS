# AskCBS

A question-answering assistant for Columbia Business School MBA students. It answers
the practical questions that are annoying to look up: where the microwaves are, how to
get between Manhattanville and Morningside at night, when investment banking recruiting
starts, and how tech recruiting timelines work.

**Live demo:** _(add your Streamlit Cloud URL here after deploying)_

---

## What it does

AskCBS reads two knowledge files and answers only from them:

| Source | Covers |
|---|---|
| `knowledge/campus_facts.md` | Buildings and floors, microwave locations, CBS hardware, system logins, traditions, the evening shuttle, subway, housing, groceries, gym, health services |
| `knowledge/recruiting_clubs.md` | Full club directory plus recruiting timelines and advice from 24 professional clubs |

Both come from the student-written ExBo Survival Guide (Fall 2026), which is not an
official CBS document. The app says so and flags time-sensitive details for
confirmation.

## How it works

```
Question
   │
   ▼
System prompt  ──  both knowledge files, in full (~9k tokens)
   │
   ▼
Gemini 3.5 Flash-Lite  ──  answers only from the provided documents
   │
   ▼
Streamed answer  +  question logged to questions.csv
```

There is deliberately **no vector database**. At ~5,000 words the entire corpus fits in
the context window, so retrieval would add moving parts and a new failure mode (retrieving
the wrong chunk) without improving answers. `askcbs/knowledge.py` is the seam where a
retrieval step would go if the corpus grows past roughly 40,000 words.

The system prompt in `askcbs/llm.py` is the most important file in the project. It is what
keeps the bot from inventing a shuttle schedule. Grounding instructions, scope limits, and
the rule to defer rather than guess all live there.

## Project structure

```
AskCBS/
├── app.py                      # Streamlit chat UI
├── requirements.txt
├── askcbs/
│   ├── knowledge.py            # Loads and assembles the corpus
│   ├── llm.py                  # System prompt + Gemini API call
│   └── logging_.py             # Logs questions and flags coverage gaps
├── knowledge/
│   ├── campus_facts.md
│   └── recruiting_clubs.md
└── .streamlit/
    └── secrets.toml.example
```

## Running locally

```bash
git clone https://github.com/<you>/AskCBS.git
cd AskCBS
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# add your Gemini API key (free at aistudio.google.com/apikey) to that file

streamlit run app.py
```

## Deploying

1. Push to GitHub.
2. At [share.streamlit.io](https://share.streamlit.io), create a new app pointing at
   `app.py` on `main`.
3. Under **Settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   ```
   Without this the app starts but every question fails.

## Updating the knowledge base

Edit the markdown files in `knowledge/` and redeploy. No re-indexing, no migration.
Shuttle schedules and recruiting deadlines change, and a tool students stop trusting is
worse than no tool, so someone needs to own this each year.

## The feedback loop

Every question is logged to `questions.csv` with a flag for whether the corpus could
answer it. After a week of real use, the unanswered rows tell you what to add next.

Note that Streamlit Community Cloud has an ephemeral filesystem — the log resets on
restart or redeploy. That's fine for an early read on usage. For durable logs, replace
`_append` in `askcbs/logging_.py` with a write to a Google Sheet or Supabase table.

## Limitations

- Only knows what's in `knowledge/`. It will say so rather than guess.
- The ExBo Survival Guide is student-written and not an official CBS document.
- Dates and contacts shift during the year; confirm anything time-sensitive.
- No CMC people directory — for Advisors, Coaches, Fellows, or EIRs, use 12twenty.
- Runs on Gemini's free tier; under heavy use it may ask you to try again in a minute.
- On the free tier, Google may use the questions you ask to improve its products. Don't
  include anything personal or confidential.
- Not a substitute for the CMC, Peer Advisors, or the Office of Student Affairs.

## License

MIT
