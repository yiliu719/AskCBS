"""AskCBS -- a question-answering assistant for Columbia Business School students."""

import streamlit as st

from askcbs.knowledge import build_corpus, corpus_stats
from askcbs.llm import build_system_prompt, stream_answer
from askcbs.logging_ import log_question

st.set_page_config(
    page_title="AskCBS",
    page_icon="\U0001F4CD",
    layout="centered",
)

# Columbia Business School's own palette: Columbia blue on deep navy. Grounding the
# look in the school's colors rather than a generic chat theme.
st.markdown(
    """
    <style>
      :root {
        --cbs-navy: #1B3A5C;
        --cbs-blue: #A5CDEA;
        --cbs-slate: #4A6274;
      }
      .askcbs-mast {
        border-bottom: 3px solid var(--cbs-blue);
        padding-bottom: 0.6rem;
        margin-bottom: 0.4rem;
      }
      .askcbs-mast h1 {
        color: var(--cbs-navy);
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
      }
      .askcbs-sub {
        color: var(--cbs-slate);
        font-size: 0.95rem;
        margin: 0.5rem 0 1.4rem 0;
        line-height: 1.5;
      }
      .askcbs-note {
        color: var(--cbs-slate);
        font-size: 0.8rem;
        line-height: 1.5;
        border-left: 2px solid var(--cbs-blue);
        padding-left: 0.7rem;
        margin-top: 2rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_system_prompt() -> str:
    """Assemble the corpus once per server process, not once per message."""
    return build_system_prompt(build_corpus())


@st.cache_data(show_spinner=False)
def get_stats() -> dict[str, int]:
    return corpus_stats()


st.markdown(
    '<div class="askcbs-mast"><h1>AskCBS</h1></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="askcbs-sub">Answers about campus, New York, clubs, and recruiting '
    "\u2014 drawn from the ExBo Survival Guide.</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("What AskCBS knows")
    for label, words in get_stats().items():
        st.caption(f"{label} \u00b7 {words:,} words")
    st.divider()
    st.caption(
        "Built on the student-written ExBo Survival Guide (Fall 2026), which is "
        "not an official CBS document. Confirm deadlines and contacts before you "
        "rely on them."
    )
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# Soft per-session cap to stay inside Gemini's free-tier rate limits. A refresh starts a
# new session; that's acceptable for a free tool.
SESSION_QUESTION_LIMIT = 20
LIMIT_MESSAGE = "You've hit the AskCBS limit for this session. Refresh later to ask more."

STARTERS = [
    "Where are the microwaves on campus?",
    "How do I get between Manhattanville and Morningside at night?",
    "What's the timeline for tech recruiting?",
    "When does investment banking recruiting start?",
]

if "messages" not in st.session_state:
    st.session_state.messages = []
# Tracked separately from messages so "Clear conversation" doesn't reset the cap.
if "questions_asked" not in st.session_state:
    st.session_state.questions_asked = 0

# Suggested questions, shown only on an empty conversation.
if not st.session_state.messages:
    st.caption("Try asking:")
    columns = st.columns(2)
    for index, starter in enumerate(STARTERS):
        if columns[index % 2].button(starter, use_container_width=True):
            st.session_state.pending = starter
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about campus, clubs, recruiting, or NYC")
if "pending" in st.session_state:
    question = st.session_state.pop("pending")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    over_limit = st.session_state.questions_asked >= SESSION_QUESTION_LIMIT
    with st.chat_message("assistant"):
        if over_limit:
            answer = LIMIT_MESSAGE
            st.markdown(answer)
        else:
            st.session_state.questions_asked += 1
            try:
                answer = st.write_stream(
                    stream_answer(get_system_prompt(), st.session_state.messages)
                )
            except Exception as error:  # noqa: BLE001 -- surface any API failure to the user
                answer = (
                    "That request didn't go through. Try again in a moment, and if it "
                    f"keeps failing let whoever runs this know.\n\n`{error}`"
                )
                st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    if not over_limit:
        log_question(question, answer)

st.markdown(
    '<p class="askcbs-note">AskCBS answers only from the guides above. It will '
    "tell you when something isn\u2019t covered rather than guess. For anything "
    "time-sensitive \u2014 recruiting deadlines, room bookings, appointments \u2014 "
    "confirm with the CMC or your Peer Advisors.</p>",
    unsafe_allow_html=True,
)
