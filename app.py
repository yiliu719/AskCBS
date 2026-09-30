"""AskCBS -- a question-answering assistant for Columbia Business School students."""

import streamlit as st

from askcbs.knowledge import build_corpus
from askcbs.llm import BUSY_MESSAGE, build_system_prompt, stream_answer
from askcbs.logging_ import log_question, looks_unanswered

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
      .askcbs-caption {
        color: var(--cbs-slate);
        font-size: 0.75rem;
        opacity: 0.8;
        margin: 0.35rem 0 0 0;
      }
      .askcbs-note {
        color: var(--cbs-slate);
        font-size: 0.8rem;
        line-height: 1.5;
        border-left: 2px solid var(--cbs-blue);
        padding-left: 0.7rem;
        margin-top: 2rem;
      }

      /* Hide Streamlit chrome. The header itself stays so the sidebar toggle works. */
      #MainMenu,
      [data-testid="stMainMenu"],
      [data-testid="stAppDeployButton"],
      [data-testid="stDecoration"],
      footer {
        display: none !important;
      }

      /* Answer typography. */
      [data-testid="stChatMessage"] p,
      [data-testid="stChatMessage"] li {
        line-height: 1.6;
      }
      [data-testid="stChatMessage"] ul,
      [data-testid="stChatMessage"] ol {
        margin: 0.35rem 0 0.6rem 0;
      }
      [data-testid="stChatMessage"] li {
        margin-bottom: 0.3rem;
      }

      /* Starter questions as cards. */
      .st-key-starters button {
        background: #FFFFFF;
        border: 1px solid #E6E1D8;
        border-radius: 0.8rem;
        min-height: 4.2rem;
        padding: 0.75rem 1rem;
        justify-content: flex-start;
        text-align: left;
        color: var(--cbs-navy);
        box-shadow: 0 1px 2px rgba(27, 58, 92, 0.05);
        transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
      }
      .st-key-starters button > div,
      .st-key-starters button > div > span {
        justify-content: flex-start;
      }
      .st-key-starters button [data-testid="stMarkdownContainer"],
      .st-key-starters button p {
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
        text-align: left;
        font-size: 0.9rem;
        line-height: 1.4;
      }
      .st-key-starters button:hover {
        border-color: var(--cbs-blue);
        box-shadow: 0 4px 12px rgba(27, 58, 92, 0.10);
        transform: translateY(-1px);
        color: var(--cbs-navy);
      }

      /* Phones: Streamlit pins chat apps to the bottom, so a tall empty state pushes the
         title off-screen. Tighten spacing until the whole thing fits. */
      @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] {
          padding-top: 4rem;
        }
        .askcbs-sub {
          font-size: 0.9rem;
          margin-bottom: 1rem;
        }
        .askcbs-note {
          margin-top: 1.25rem;
        }
        .st-key-starters,
        .st-key-starters [data-testid="stHorizontalBlock"] {
          gap: 0.5rem;
        }
        .st-key-starters button {
          min-height: 0;
          padding: 0.6rem 0.9rem;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# Simple letter marks, not school logos: navy for AskCBS, Columbia blue for the user.
ASSISTANT_AVATAR = (
    '<svg viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#1B3A5C"/>'
    '<text x="16" y="21.5" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" '
    'font-size="15" font-weight="700" fill="#A5CDEA">A</text></svg>'
)
USER_AVATAR = (
    '<svg viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="#A5CDEA"/>'
    '<circle cx="16" cy="12.5" r="5" fill="#1B3A5C"/>'
    '<path d="M6.5 26c1.6-4.6 5.3-7 9.5-7s7.9 2.4 9.5 7" fill="#1B3A5C"/></svg>'
)
AVATARS = {"assistant": ASSISTANT_AVATAR, "user": USER_AVATAR}
# Sidebar copy for the two knowledge files. Kept separate from the labels in
# askcbs/knowledge.py, which also go to the model as document names.
SIDEBAR_SOURCES = (
    (
        "Campus & New York",
        "Buildings and microwaves, CBS systems, traditions, the evening shuttle, "
        "subway, housing, and health services.",
    ),
    (
        "Clubs & recruiting",
        "The full club directory, plus recruiting timelines and tips by industry, "
        "from investment banking to sports business.",
    ),
)
SOURCE_CAPTION = '<p class="askcbs-caption">From the ExBo Survival Guide</p>'


@st.cache_resource(show_spinner=False)
def get_system_prompt() -> str:
    """Assemble the corpus once per server process, not once per message."""
    return build_system_prompt(build_corpus())


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
    for title, description in SIDEBAR_SOURCES:
        st.markdown(f"**{title}**")
        st.caption(description)
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

# Read the question before drawing anything, so the starters vanish on the same run the
# first question arrives. The chat input is pinned to the bottom regardless of order.
question = st.chat_input("Ask about campus, clubs, or recruiting")
if "pending" in st.session_state:
    question = st.session_state.pop("pending")

# Suggested questions, shown only on an empty conversation.
if not st.session_state.messages and not question:
    st.caption("Try asking:")
    with st.container(key="starters"):
        for row in (STARTERS[:2], STARTERS[2:]):
            columns = st.columns(2)
            for column, starter in zip(columns, row):
                if column.button(starter, width="stretch"):
                    st.session_state.pending = starter
                    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=AVATARS[message["role"]]):
        st.markdown(message["content"])
        if message.get("sourced"):
            st.markdown(SOURCE_CAPTION, unsafe_allow_html=True)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    over_limit = st.session_state.questions_asked >= SESSION_QUESTION_LIMIT
    sourced = False
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        if over_limit:
            answer = LIMIT_MESSAGE
            st.markdown(answer)
        else:
            st.session_state.questions_asked += 1
            try:
                answer = st.write_stream(
                    stream_answer(get_system_prompt(), st.session_state.messages)
                )
                sourced = answer != BUSY_MESSAGE and not looks_unanswered(answer)
            except Exception as error:  # noqa: BLE001 -- surface any API failure to the user
                answer = (
                    "That request didn't go through. Try again in a moment, and if it "
                    f"keeps failing let whoever runs this know.\n\n`{error}`"
                )
                st.markdown(answer)
        if sourced:
            st.markdown(SOURCE_CAPTION, unsafe_allow_html=True)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sourced": sourced}
    )
    if not over_limit:
        log_question(question, answer)

st.markdown(
    '<p class="askcbs-note">AskCBS answers only from the ExBo Survival Guide. It will '
    "tell you when something isn\u2019t covered rather than guess. For anything "
    "time-sensitive \u2014 recruiting deadlines, room bookings, appointments \u2014 "
    "confirm with the CMC or your Peer Advisors.</p>",
    unsafe_allow_html=True,
)
