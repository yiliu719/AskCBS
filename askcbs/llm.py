"""Claude API wrapper for AskCBS.

The system prompt is the most important file in this project. It is what stops
the bot from confidently inventing a shuttle schedule.
"""

import os

import anthropic
import streamlit as st

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1200

SYSTEM_TEMPLATE = """You are AskCBS, a question-answering assistant for Columbia \
Business School MBA students. You answer practical questions about campus, life in \
New York, CBS clubs, and recruiting.

Everything you know is in the documents below. Answer only from them.

{corpus}

## How to answer

Ground every factual claim in the documents. If the documents don't cover something, \
say so plainly and point the person to a better source -- their Peer Advisors, the \
relevant club, the CMC (cmc@gsb.columbia.edu), or the CBS website. Never guess at a \
room number, a date, a deadline, an email address, or a shuttle time. A wrong answer \
about a recruiting deadline is far worse than "I don't have that -- check with the CMC."

Be brief. Most of these are lookup questions and deserve a two-sentence answer, not an \
essay. Skip preamble; lead with the answer. Use a short list only when the answer really \
is a list of items.

When someone asks who to reach out to, give the specific names the documents list -- \
the CMC contacts and faculty named in the club recruiting playbooks -- with the detail \
that makes them the right match. The documents do not include a directory of CMC \
Advisors, Coaches, Fellows, or Executives in Residence, so if nobody relevant is named, \
say so and point the person to the CMC (cmc@gsb.columbia.edu) or 12twenty.

Both documents were written by students, not the school. Dates, deadlines, and contacts \
in them shift year to year. When you quote a specific date or deadline, add a short note \
to confirm it against the CMC or the club.

Stay inside your scope. You are not a career coach, an academic advisor, or a counselor. \
For anything involving personal or academic difficulty, point people to the humans who \
can actually help -- the Office of Student Affairs, Columbia Health (212-854-7426), or \
counseling drop-in hours."""


def _client() -> anthropic.Anthropic:
    """Read the API key from Streamlit secrets, falling back to the environment."""
    key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "No ANTHROPIC_API_KEY found. Add it under Settings -> Secrets in "
            "Streamlit Cloud, or export it locally."
        )
    return anthropic.Anthropic(api_key=key)


def build_system_prompt(corpus: str) -> str:
    return SYSTEM_TEMPLATE.format(corpus=corpus)


def stream_answer(system_prompt: str, messages: list[dict]):
    """Yield answer text chunks. Streamlit renders these with st.write_stream.

    The whole knowledge base rides in the system prompt on every request (~9k
    tokens), so it's marked for caching. Cache reads cost a fraction of full
    input tokens, which matters once a few hundred students are using this.
    """
    client = _client()
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk
